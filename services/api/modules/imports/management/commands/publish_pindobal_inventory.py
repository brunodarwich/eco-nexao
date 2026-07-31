import csv
from pathlib import Path

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from modules.catalog.models import Actor, ActorLocation, Category, ContactChannel, RouteActor
from modules.core.models import EditorialStatus
from modules.imports.catalog_csv import CATALOG_COLUMNS
from modules.regions.models import Region
from modules.routes.models import Route

ALLOWED_SOURCES = {"direct", "field", "institutional", "inventory", "public_web"}
PARTNERSHIP_TYPES = {
    "sponsored": Actor.PartnershipType.SPONSORED,
    "founding": Actor.PartnershipType.PARTNER,
    "institutional": Actor.PartnershipType.EDITORIAL,
    "none": Actor.PartnershipType.EDITORIAL,
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != CATALOG_COLUMNS:
            raise CommandError("O CSV canônico possui cabeçalho inesperado.")
        rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
    if not rows:
        raise CommandError("O CSV canônico está vazio.")
    blocked = sorted({row["source_type"] for row in rows} - ALLOWED_SOURCES)
    if blocked:
        raise CommandError(f"O CSV contém fontes não publicáveis: {', '.join(blocked)}.")
    return rows


class Command(BaseCommand):
    help = "Materializa e publica explicitamente o inventário canônico de Pindobal no banco local."

    def add_arguments(self, parser):
        parser.add_argument("--csv", required=True, help="Caminho do CSV canônico validado.")
        parser.add_argument(
            "--confirm-publish-unverified",
            action="store_true",
            help="Confirma a publicação humana de registros ainda pendentes de revisão.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["confirm_publish_unverified"]:
            raise CommandError("A publicação exige --confirm-publish-unverified.")

        rows = _rows(Path(options["csv"]).resolve())
        regions = {slug: Region.objects.get(slug=slug) for slug in {r["region_slug"] for r in rows}}
        route_keys = {
            (row["region_slug"], route_slug)
            for row in rows
            for route_slug in filter(None, row["route_slugs"].split("|"))
        }
        routes = {key: Route.objects.get(region=regions[key[0]], slug=key[1]) for key in route_keys}

        imported_ids = {row["external_id"] for row in rows}
        # Mantém os fixtures recuperáveis, mas os retira da API pública sem
        # disputar locks nos vínculos já lidos pelo servidor de desenvolvimento.
        Actor.objects.filter(external_id__startswith="demo:pindobal:").update(
            editorial_status=EditorialStatus.DRAFT
        )

        location_count = 0
        for position, row in enumerate(rows, start=1):
            category, _ = Category.objects.update_or_create(
                slug=row["category_slug"],
                defaults={
                    "public_name": row["category_slug"].replace("_", " ").title(),
                    "description": "Categoria do inventário canônico de Pindobal.",
                    "is_active": True,
                },
            )
            actor_slug = (
                f"{slugify(row['public_name'])[:110]}-{row['external_id'].rsplit(':', 1)[-1]}"
            )
            services = [item.strip() for item in row["services"].split("|") if item.strip()]
            actor, _ = Actor.objects.update_or_create(
                external_id=row["external_id"],
                defaults={
                    "actor_kind": row["actor_kind"],
                    "category": category,
                    "slug": actor_slug,
                    "public_name": row["public_name"],
                    "legal_name": row["legal_name"],
                    "short_description": row["short_description"],
                    "full_description": row["full_description"] or row["short_description"],
                    "services": services,
                    "editorial_status": EditorialStatus.PUBLISHED,
                    "partnership_type": PARTNERSHIP_TYPES[row["partnership_type"]],
                },
            )
            point = None
            if row["latitude"] and row["longitude"]:
                point = Point(float(row["longitude"]), float(row["latitude"]), srid=4326)
                location_count += 1
            ActorLocation.objects.update_or_create(
                actor=actor,
                region=regions[row["region_slug"]],
                label="Localização do inventário",
                defaults={
                    "address_fields": {
                        key: row[column]
                        for key, column in (
                            ("street", "street"),
                            ("number", "address_number"),
                            ("extra", "address_extra"),
                            ("neighborhood", "neighborhood"),
                            ("city", "city"),
                            ("state", "state"),
                            ("postal_code", "postal_code"),
                            ("country_code", "country_code"),
                        )
                        if row[column]
                    },
                    "point": point,
                    "is_primary": True,
                    "public_visibility": point is not None,
                },
            )
            ContactChannel.objects.filter(actor=actor).delete()
            for route_slug in filter(None, row["route_slugs"].split("|")):
                RouteActor.objects.update_or_create(
                    route=routes[(row["region_slug"], route_slug)],
                    actor=actor,
                    stage=None,
                    route_role=row["route_role"],
                    defaults={"editorial_position": position, "is_featured": False},
                )

        Actor.objects.filter(external_id__startswith="inventory:pindobal:").exclude(
            external_id__in=imported_ids
        ).update(editorial_status=EditorialStatus.DRAFT)
        self.stdout.write(
            self.style.SUCCESS(
                f"Inventário publicado: {len(rows)} atores, {location_count} pins e "
                f"{len(route_keys)} vínculo(s) de rota processados."
            )
        )
