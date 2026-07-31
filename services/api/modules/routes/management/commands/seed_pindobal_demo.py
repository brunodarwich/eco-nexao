from datetime import datetime, time
from decimal import Decimal

from django.contrib.gis.geos import LineString, Point
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import make_aware

from modules.catalog.models import (
    Actor,
    ActorLocation,
    Category,
    ContactChannel,
    OperatingHours,
    RouteActor,
)
from modules.core.models import EditorialStatus
from modules.regions.models import Region
from modules.routes.models import Alert, Route, RouteSegment, RouteStage


class Command(BaseCommand):
    help = "Cria fixtures idempotentes e claramente demonstrativos da rota de Pindobal."

    def add_arguments(self, parser):
        parser.add_argument(
            "--publish-demo",
            action="store_true",
            help="Publica os fixtures no ambiente de desenvolvimento configurado.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        status = EditorialStatus.PUBLISHED if options["publish_demo"] else EditorialStatus.DRAFT
        region, _ = Region.objects.update_or_create(
            slug="santarem-alter-do-chao",
            defaults={
                "public_name": "Santarém e Alter do Chão",
                "short_description": (
                    "Território demonstrativo para validar a experiência multirregional."
                ),
                "center_point": Point(-54.97478, -2.55997, srid=4326),
                "timezone": "America/Fortaleza",
                "status": status,
                "published_version": 1 if options["publish_demo"] else None,
            },
        )
        route, _ = Route.objects.update_or_create(
            region=region,
            slug="pindobal",
            defaults={
                "public_name": "Rota demonstrativa de Pindobal",
                "short_promise": "Prepare uma visita consciente com informações em validação.",
                "description": (
                    "Conteúdo demonstrativo criado para testar a jornada da ECOnexão. "
                    "Não use estas informações como orientação operacional sem confirmação local."
                ),
                "duration_minutes": 240,
                "difficulty": Route.Difficulty.EASY,
                "estimated_cost_min": Decimal("40.00"),
                "estimated_cost_max": Decimal("120.00"),
                "transport_modes": ["car", "walk"],
                "preparation_content": (
                    "Confirme previamente acesso, transporte de retorno, funcionamento dos "
                    "serviços e condições do rio. Leve água, proteção solar, repelente e "
                    "meios de pagamento alternativos. Todo este conteúdo é demonstrativo."
                ),
                "accessibility_content": (
                    "Condições de acessibilidade ainda não verificadas em campo. "
                    "Confirme diretamente antes da visita."
                ),
                "offline_enabled": True,
                "editorial_status": status,
            },
        )

        stage_definitions = [
            (
                1,
                "Chegada e orientação",
                "Ponto demonstrativo para conferir condições locais antes de seguir.",
                -54.97478,
                -2.55997,
                RouteStage.StageType.START,
                20,
            ),
            (
                2,
                "Caminho até a praia",
                "Trecho demonstrativo de deslocamento com atenção ao terreno.",
                -54.9695,
                -2.5593,
                RouteStage.StageType.STOP,
                25,
            ),
            (
                3,
                "Praia de Pindobal",
                "Área de permanência representada apenas para validação da interface.",
                -54.96111,
                -2.55833,
                RouteStage.StageType.EXPERIENCE,
                180,
            ),
        ]
        stages = []
        for (
            position,
            name,
            description,
            longitude,
            latitude,
            stage_type,
            duration,
        ) in stage_definitions:
            stage, _ = RouteStage.objects.update_or_create(
                route=route,
                position=position,
                defaults={
                    "public_name": name,
                    "description": description,
                    "point": Point(longitude, latitude, srid=4326),
                    "arrival_guidance": "Confirme a orientação com uma fonte local.",
                    "duration_minutes": duration,
                    "stage_type": stage_type,
                    "is_optional": False,
                },
            )
            stages.append(stage)

        for index, (start, end) in enumerate(
            zip(stages, stages[1:], strict=False),
            start=1,
        ):
            RouteSegment.objects.update_or_create(
                route=route,
                from_stage=start,
                to_stage=end,
                defaults={
                    "geometry": LineString(start.point, end.point, srid=4326),
                    "transport_mode": "walk" if index == 2 else "car",
                    "distance_meters": 750 if index == 1 else 1100,
                    "duration_minutes": 12 if index == 1 else 18,
                    "instructions": "Trecho demonstrativo; valide o percurso no local.",
                },
            )

        Alert.objects.update_or_create(
            region=region,
            route=route,
            stage=None,
            title="Informações demonstrativas",
            defaults={
                "severity": Alert.Severity.WARNING,
                "description": (
                    "Horários, acesso, preços e condições ainda precisam de verificação humana."
                ),
                "alternative": "Confirme com fontes locais antes de iniciar o deslocamento.",
                "starts_at": make_aware(datetime(2026, 1, 1)),
                "ends_at": make_aware(datetime(2030, 1, 1)),
                "status": status,
            },
        )

        actors = [
            {
                "external_id": "demo:pindobal:apoio",
                "category": ("apoio", "Apoio"),
                "slug": "ponto-de-apoio-demonstrativo",
                "name": "Ponto de apoio demonstrativo",
                "kind": Actor.ActorKind.SUPPORT,
                "description": "Referência fictícia para testar apoio e localização.",
                "role": RouteActor.RouteRole.SUPPORT,
                "stage": stages[0],
                "point": stages[0].point,
                "contacts": [("website", "https://example.com/econexao-apoio")],
            },
            {
                "external_id": "demo:pindobal:alimentacao",
                "category": ("alimentacao", "Alimentação"),
                "slug": "cozinha-ribeirinha-demonstrativa",
                "name": "Cozinha ribeirinha demonstrativa",
                "kind": Actor.ActorKind.BUSINESS,
                "description": "Estabelecimento fictício para validar o catálogo contextual.",
                "role": RouteActor.RouteRole.SERVICE,
                "stage": stages[2],
                "point": stages[2].point,
                "contacts": [
                    ("phone", "+5593000000000"),
                    ("whatsapp", "+5593000000000"),
                    ("website", "https://example.com/econexao-cozinha"),
                ],
            },
        ]
        for position, definition in enumerate(actors, start=1):
            category, _ = Category.objects.update_or_create(
                slug=definition["category"][0],
                defaults={
                    "public_name": definition["category"][1],
                    "description": "Categoria demonstrativa.",
                    "is_active": True,
                },
            )
            actor, _ = Actor.objects.update_or_create(
                external_id=definition["external_id"],
                defaults={
                    "actor_kind": definition["kind"],
                    "category": category,
                    "slug": definition["slug"],
                    "public_name": definition["name"],
                    "short_description": definition["description"],
                    "full_description": (
                        f"{definition['description']} Não representa oferta comercial real."
                    ),
                    "services": ["atendimento demonstrativo"],
                    "editorial_status": status,
                    "partnership_type": Actor.PartnershipType.EDITORIAL,
                },
            )
            location, _ = ActorLocation.objects.update_or_create(
                actor=actor,
                region=region,
                label="Local demonstrativo",
                defaults={
                    "address_fields": {
                        "neighborhood": "Pindobal",
                        "city": "Belterra",
                        "state": "PA",
                        "country_code": "BR",
                    },
                    "point": definition["point"],
                    "is_primary": True,
                    "public_visibility": True,
                },
            )
            OperatingHours.objects.update_or_create(
                actor_location=location,
                weekday=0,
                exception_date=None,
                defaults={
                    "opens_at": time(9, 0),
                    "closes_at": time(17, 0),
                    "is_closed": False,
                    "public_note": "Horário fictício para demonstração.",
                },
            )
            for channel_type, public_value in definition["contacts"]:
                ContactChannel.objects.update_or_create(
                    actor=actor,
                    channel_type=channel_type,
                    public_value=public_value,
                    defaults={
                        "is_public": True,
                        "authorization_reference": "fixture:demo-pindobal",
                    },
                )
            RouteActor.objects.update_or_create(
                route=route,
                actor=actor,
                stage=definition["stage"],
                route_role=definition["role"],
                defaults={
                    "editorial_position": position,
                    "is_featured": position == 1,
                    "sponsorship_label": "",
                },
            )

        state = "publicados" if options["publish_demo"] else "criados como rascunho"
        self.stdout.write(
            self.style.SUCCESS(f"Fixtures demonstrativos de Pindobal {state} com sucesso.")
        )
