import os

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import DatabaseError

from modules.catalog.external_discovery import record_google_places_discovery
from modules.catalog.google_places import GooglePlacesError, search_nearby

DEFAULT_TYPES = (
    "restaurant",
    "hotel",
    "hostel",
    "guest_house",
    "campground",
    "tourist_attraction",
    "supermarket",
    "pharmacy",
    "hospital",
    "gas_station",
    "police",
)


def safe_console_text(value: object, encoding: str | None) -> str:
    text = str(value)
    if not encoding:
        return text
    return text.encode(encoding, errors="replace").decode(encoding)


class Command(BaseCommand):
    help = "Consulta pontos próximos no Google Maps e registra somente Place IDs para curadoria."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--latitude", type=float, default=-2.55997)
        parser.add_argument("--longitude", type=float, default=-54.97478)
        parser.add_argument("--radius", type=float, default=10_000)
        parser.add_argument("--max-results", type=int, default=20)
        parser.add_argument("--context-key", default="pindobal")
        parser.add_argument(
            "--preview-only",
            action="store_true",
            help="Exibe a prévia sem registrar a execução e os Place IDs.",
        )
        parser.add_argument(
            "--types",
            default=",".join(DEFAULT_TYPES),
            help="Tipos da Places API separados por vírgula.",
        )

    def handle(self, *args: object, **options: object) -> None:
        api_key = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_PLACES_API_KEY", "")
        types = str(options["types"]).split(",")
        console_encoding = getattr(getattr(self.stdout, "_out", None), "encoding", None)

        try:
            candidates = search_nearby(
                api_key=api_key,
                latitude=float(options["latitude"]),
                longitude=float(options["longitude"]),
                radius_meters=float(options["radius"]),
                included_types=types,
                max_results=int(options["max_results"]),
            )
        except GooglePlacesError as error:
            raise CommandError(str(error)) from None

        if not options["preview_only"]:
            try:
                recorded = record_google_places_discovery(
                    context_key=str(options["context_key"]),
                    latitude=float(options["latitude"]),
                    longitude=float(options["longitude"]),
                    radius_meters=float(options["radius"]),
                    included_types=types,
                    max_results=int(options["max_results"]),
                    place_ids=[candidate.place_id for candidate in candidates],
                )
            except (DatabaseError, ValidationError, ValueError) as error:
                raise CommandError(
                    "A consulta foi concluída, mas as referências não puderam ser registradas."
                ) from error
        else:
            recorded = None

        self.stdout.write(
            "Prévia temporária — os campos abaixo são dados do Google Maps e não foram salvos."
        )
        self.stdout.write("Candidatos exigem verificação humana antes de virar rascunho.\n")
        if recorded:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Execução {recorded.run_id}: {recorded.reference_count} Place IDs "
                    "registrados para curadoria."
                )
            )
            self.stdout.write(
                "A apresentação offline usará somente conteúdo editorial próprio verificado.\n"
            )
        if not candidates:
            self.stdout.write("Nenhum ponto encontrado com os filtros informados.")
            return

        for index, candidate in enumerate(candidates, start=1):
            coordinates = ""
            if candidate.latitude is not None and candidate.longitude is not None:
                coordinates = f"{candidate.latitude:.6f}, {candidate.longitude:.6f}"
            display_name = safe_console_text(
                candidate.display_name or "Nome não informado", console_encoding
            )
            primary_type = safe_console_text(
                candidate.primary_type or "não informado", console_encoding
            )
            formatted_address = safe_console_text(
                candidate.formatted_address or "não informado", console_encoding
            )
            google_maps_uri = safe_console_text(
                candidate.google_maps_uri or "não informado", console_encoding
            )
            place_id = safe_console_text(candidate.place_id, console_encoding)
            self.stdout.write(f"{index}. {display_name}")
            self.stdout.write(f"   Tipo: {primary_type}")
            self.stdout.write(f"   Endereço: {formatted_address}")
            self.stdout.write(f"   Coordenadas: {coordinates or 'não informadas'}")
            self.stdout.write(f"   Google Maps: {google_maps_uri}")
            self.stdout.write(f"   Place ID: {place_id}\n")
