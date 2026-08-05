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

    @transaction.atomic
    def handle(self, *args, **options):
        status = EditorialStatus.DRAFT
        existing_region = Region.objects.filter(slug="santarem-alter-do-chao").first()
        region_defaults = {
            "public_name": "Santarém e Alter do Chão",
            "short_description": (
                "Território demonstrativo para validar a experiência multirregional."
            ),
            "center_point": Point(-54.97478, -2.55997, srid=4326),
            "timezone": "America/Fortaleza",
        }
        if not existing_region or existing_region.status != EditorialStatus.PUBLISHED:
            region_defaults["status"] = status

        region, _ = Region.objects.update_or_create(
            slug="santarem-alter-do-chao",
            defaults=region_defaults,
        )

        existing_route = Route.objects.filter(region=region, slug="pindobal").first()
        route_defaults = {
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
        }
        if not existing_route or existing_route.editorial_status != EditorialStatus.PUBLISHED:
            route_defaults["editorial_status"] = status

        route, _ = Route.objects.update_or_create(
            region=region,
            slug="pindobal",
            defaults=route_defaults,
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

        existing_alert = Alert.objects.filter(
            region=region,
            route=route,
            stage=None,
            title="Informações demonstrativas",
        ).first()
        alert_defaults = {
            "severity": Alert.Severity.WARNING,
            "description": (
                "Horários, acesso, preços e condições ainda precisam de verificação humana."
            ),
            "alternative": "Confirme com fontes locais antes de iniciar o deslocamento.",
            "starts_at": make_aware(datetime(2026, 1, 1)),
            "ends_at": make_aware(datetime(2030, 1, 1)),
        }
        if not existing_alert or existing_alert.status != EditorialStatus.PUBLISHED:
            alert_defaults["status"] = status
        Alert.objects.update_or_create(
            region=region,
            route=route,
            stage=None,
            title="Informações demonstrativas",
            defaults=alert_defaults,
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
            existing_actor = Actor.objects.filter(external_id=definition["external_id"]).first()
            actor_defaults = {
                "actor_kind": definition["kind"],
                "category": category,
                "slug": definition["slug"],
                "public_name": definition["name"],
                "short_description": definition["description"],
                "full_description": (
                    f"{definition['description']} Não representa oferta comercial real."
                ),
                "services": ["atendimento demonstrativo"],
                "partnership_type": Actor.PartnershipType.EDITORIAL,
            }
            if not existing_actor or existing_actor.editorial_status != EditorialStatus.PUBLISHED:
                actor_defaults["editorial_status"] = status
            actor, _ = Actor.objects.update_or_create(
                external_id=definition["external_id"],
                defaults=actor_defaults,
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
                        "source_type": "legacy",
                        "source_reference": "fixture:demo-pindobal",
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

        self.stdout.write(
            self.style.SUCCESS(
                "Fixtures demonstrativos de Pindobal criados ou atualizados como rascunho; "
                "conteúdo já publicado foi preservado."
            )
        )
