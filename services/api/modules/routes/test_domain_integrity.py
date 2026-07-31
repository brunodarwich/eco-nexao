import uuid

import pytest
from django.contrib.gis.geos import LineString, Point
from django.core.exceptions import ValidationError

from modules.catalog.models import Actor, Category, RouteActor
from modules.regions.models import Region

from .models import Alert, Route, RouteSegment, RouteStage


def region(slug: str) -> Region:
    return Region(
        id=uuid.uuid4(),
        slug=slug,
        public_name=slug,
        center_point=Point(-54.7, -2.4, srid=4326),
    )


def route(parent: Region, slug: str) -> Route:
    return Route(
        id=uuid.uuid4(),
        region=parent,
        slug=slug,
        public_name=slug,
        short_promise="Promessa",
        duration_minutes=60,
        difficulty=Route.Difficulty.EASY,
    )


def stage(parent: Route, position: int) -> RouteStage:
    return RouteStage(
        id=uuid.uuid4(),
        route=parent,
        position=position,
        public_name=f"Etapa {position}",
        point=Point(-54.7 + position / 100, -2.4, srid=4326),
        stage_type=RouteStage.StageType.STOP,
    )


def test_segment_rejects_stages_from_another_route():
    first_region = region("regiao-a")
    first_route = route(first_region, "rota-a")
    second_route = route(first_region, "rota-b")
    first_stage = stage(first_route, 1)
    foreign_stage = stage(second_route, 2)
    segment = RouteSegment(
        route=first_route,
        from_stage=first_stage,
        to_stage=foreign_stage,
        geometry=LineString(first_stage.point, foreign_stage.point, srid=4326),
        transport_mode="walk",
        distance_meters=100,
        duration_minutes=5,
    )

    with pytest.raises(ValidationError, match="mesma rota"):
        segment.clean()


def test_alert_rejects_mixed_region_route_and_stage():
    first_region = region("regiao-a")
    second_region = region("regiao-b")
    first_route = route(first_region, "rota-a")
    second_route = route(second_region, "rota-b")
    foreign_stage = stage(second_route, 1)
    alert = Alert(
        region=first_region,
        route=first_route,
        stage=foreign_stage,
        severity=Alert.Severity.WARNING,
        title="Atenção",
        description="Descrição",
        starts_at="2026-07-29T10:00:00Z",
    )

    with pytest.raises(ValidationError, match="etapa.*rota"):
        alert.clean()

    alert.route = second_route
    with pytest.raises(ValidationError, match="rota.*região"):
        alert.clean()


def test_catalog_link_rejects_stage_from_another_route():
    parent_region = region("regiao-a")
    first_route = route(parent_region, "rota-a")
    second_route = route(parent_region, "rota-b")
    foreign_stage = stage(second_route, 1)
    category = Category(id=uuid.uuid4(), slug="apoio", public_name="Apoio")
    actor = Actor(
        id=uuid.uuid4(),
        external_id="ator-1",
        actor_kind=Actor.ActorKind.SUPPORT,
        category=category,
        slug="ator-1",
        public_name="Ator 1",
        short_description="Apoio",
    )
    link = RouteActor(
        route=first_route,
        actor=actor,
        stage=foreign_stage,
        route_role=RouteActor.RouteRole.SUPPORT,
    )

    with pytest.raises(ValidationError, match="etapa.*rota"):
        link.clean()


def test_consistent_references_pass_domain_validation():
    parent_region = region("regiao-a")
    parent_route = route(parent_region, "rota-a")
    first_stage = stage(parent_route, 1)
    second_stage = stage(parent_route, 2)

    RouteSegment(
        route=parent_route,
        from_stage=first_stage,
        to_stage=second_stage,
        geometry=LineString(first_stage.point, second_stage.point, srid=4326),
        transport_mode="walk",
        distance_meters=100,
        duration_minutes=5,
    ).clean()
    Alert(
        region=parent_region,
        route=parent_route,
        stage=first_stage,
        severity=Alert.Severity.INFO,
        title="Informativo",
        description="Descrição",
        starts_at="2026-07-29T10:00:00Z",
    ).clean()
