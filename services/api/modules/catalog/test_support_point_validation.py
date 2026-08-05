from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from django.db import close_old_connections, connection
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from modules.accounts.models import AdministrativeRegionScope
from modules.accounts.permissions import AdminRole, role_group_name
from modules.audit.models import AuditEvent
from modules.core.models import EditorialStatus
from modules.regions.models import Region
from modules.routes.models import Route, RouteStage

from .admin_permissions import require_support_point_region_access
from .models import (
    Actor,
    ActorLocation,
    Category,
    ContactChannel,
    RouteActor,
    SupportPointIdempotencyRecord,
)
from .support_point_creation import SupportPointCreationConflict, create_support_point
from .support_point_duplicates import DuplicateSupportPointError
from .support_point_serializers import SupportPointCreateRequestSerializer


@pytest.fixture(autouse=True)
def authorized_region(monkeypatch):
    monkeypatch.setattr(
        "modules.catalog.support_point_relations.require_support_point_region_access",
        lambda _user, _region: None,
    )


def _boundary(west=-55.2, south=-2.8, east=-54.7, north=-2.2):
    return MultiPolygon(
        Polygon(
            (
                (west, south),
                (east, south),
                (east, north),
                (west, north),
                (west, south),
            )
        ),
        srid=4326,
    )


@pytest.fixture
def domain(db):
    region = Region.objects.create(
        slug="regiao-teste",
        public_name="Região teste",
        center_point=Point(-54.95, -2.5, srid=4326),
        boundary=_boundary(),
        status=EditorialStatus.PUBLISHED,
    )
    category = Category.objects.create(
        slug="apoio",
        public_name="Apoio",
        is_active=True,
    )
    route = Route.objects.create(
        region=region,
        slug="rota-teste",
        public_name="Rota teste",
        short_promise="Uma rota de teste",
        duration_minutes=60,
        difficulty=Route.Difficulty.EASY,
    )
    stage = RouteStage.objects.create(
        route=route,
        position=1,
        public_name="Início",
        point=Point(-54.96, -2.51, srid=4326),
        stage_type=RouteStage.StageType.START,
    )
    return {"region": region, "category": category, "route": route, "stage": stage}


def _payload(domain):
    return {
        "actor": {
            "category_id": str(domain["category"].pk),
            "public_name": "Base de apoio comunitária",
            "short_description": "Água potável e orientação local.",
            "services": ["Água potável", "Informações"],
        },
        "location": {
            "label": "Entrada principal",
            "address_fields": {
                "locality": "Comunidade exemplo",
                "administrative_area": "PA",
                "country_code": "br",
            },
            "latitude": -2.497,
            "longitude": -54.952,
            "public_visibility": True,
        },
        "contacts": [],
        "route_links": [
            {
                "route_id": str(domain["route"].pk),
                "stage_id": str(domain["stage"].pk),
                "route_role": "support",
                "editorial_position": 1,
                "is_featured": False,
                "sponsorship_label": "",
            }
        ],
    }


def _validate(payload, *, user=None):
    serializer = SupportPointCreateRequestSerializer(
        data=payload,
        context={"user": user or object()},
    )
    serializer.is_valid(raise_exception=True)
    return serializer


def _actor(domain, *, name="Ponto existente", address=None, point=None):
    actor = Actor.objects.create(
        external_id=f"test:{uuid4()}",
        actor_kind=Actor.ActorKind.SUPPORT,
        category=domain["category"],
        slug=f"ponto-{uuid4().hex[:10]}",
        public_name=name,
        short_description="Registro existente para teste.",
    )
    ActorLocation.objects.create(
        actor=actor,
        region=domain["region"],
        label="Principal",
        address_fields=address or {"locality": f"Local {uuid4()}", "country_code": "BR"},
        point=point or Point(-54.98, -2.55, srid=4326),
        is_primary=True,
    )
    return actor


@pytest.mark.django_db
def test_valid_draft_input_normalizes_country_and_allows_no_contact(domain):
    serializer = _validate(_payload(domain))

    assert serializer.validated_data["location"]["address_fields"]["country_code"] == "BR"
    assert serializer.validated_data["contacts"] == []
    assert serializer.resolved_relations.region == domain["region"]
    assert serializer.resolved_relations.point.srid == 4326


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["external_id", "slug", "actor_kind", "editorial_status"])
def test_server_controlled_and_unknown_fields_are_rejected(domain, field):
    payload = _payload(domain)
    payload["actor"][field] = "client-controlled"

    with pytest.raises(serializers.ValidationError) as error:
        _validate(payload)

    assert "unknown_field" in str(error.value.get_codes())


@pytest.mark.django_db
@pytest.mark.parametrize(
    "channel_type,value",
    [
        ("phone", "93999999999"),
        ("whatsapp", "+03999999999"),
        ("email", "não-é-email"),
        ("website", "http://inseguro.example"),
        ("instagram", "https://usuario:senha@example.com/perfil"),
    ],
)
def test_invalid_contact_formats_are_rejected(domain, channel_type, value):
    payload = _payload(domain)
    payload["contacts"] = [
        {
            "channel_type": channel_type,
            "value": value,
            "is_public": True,
            "source_type": "consolidated_sheet",
            "source_reference": "planilha:linha-001",
            "verified_at": timezone.now().isoformat(),
        }
    ]

    with pytest.raises(serializers.ValidationError):
        _validate(payload)


@pytest.mark.django_db
def test_private_contact_is_rejected_until_encryption_has_its_own_spec(domain):
    payload = _payload(domain)
    payload["contacts"] = [
        {
            "channel_type": "email",
            "value": "privado@example.org",
            "is_public": False,
        }
    ]

    with pytest.raises(serializers.ValidationError) as error:
        _validate(payload)

    assert "private_contact_unsupported" in str(error.value.get_codes())


@pytest.mark.django_db
def test_public_contact_requires_provenance_and_verification(domain):
    payload = _payload(domain)
    payload["contacts"] = [
        {
            "channel_type": "email",
            "value": "apoio@example.org",
            "is_public": True,
        }
    ]

    with pytest.raises(serializers.ValidationError) as error:
        _validate(payload)

    assert "source_reference" in str(error.value.detail)
    assert "source_type" in str(error.value.detail)
    assert "verified_at" in str(error.value.detail)


@pytest.mark.django_db
def test_boundary_is_required_and_coordinates_must_be_covered(domain):
    payload = _payload(domain)
    domain["region"].boundary = None
    domain["region"].save(update_fields=["boundary"])

    with pytest.raises(serializers.ValidationError) as missing_boundary:
        _validate(payload)
    assert "region_boundary_unavailable" in str(missing_boundary.value.get_codes())

    domain["region"].boundary = _boundary()
    domain["region"].save(update_fields=["boundary"])
    payload["location"]["latitude"] = 0
    payload["location"]["longitude"] = 0
    with pytest.raises(serializers.ValidationError) as outside:
        _validate(payload)
    assert "coordinate_outside_region" in str(outside.value.get_codes())


@pytest.mark.django_db
def test_coordinate_on_region_boundary_is_accepted(domain):
    payload = _payload(domain)
    payload["location"]["longitude"] = -55.2
    payload["location"]["latitude"] = -2.5

    serializer = _validate(payload)

    assert serializer.resolved_relations.region == domain["region"]


@pytest.mark.django_db
def test_serializer_applies_real_editor_region_scope(domain, monkeypatch):
    monkeypatch.setattr(
        "modules.catalog.support_point_relations.require_support_point_region_access",
        require_support_point_region_access,
    )
    user = get_user_model().objects.create_user(
        username="editor-regional",
        is_staff=True,
    )
    editor_group, _ = Group.objects.get_or_create(name=role_group_name(AdminRole.EDITOR))
    user.groups.add(editor_group)

    with pytest.raises(PermissionDenied):
        _validate(_payload(domain), user=user)

    AdministrativeRegionScope.objects.create(user=user, region=domain["region"])
    serializer = _validate(_payload(domain), user=user)

    assert serializer.resolved_relations.region == domain["region"]


@pytest.mark.django_db
def test_routes_must_share_region_and_stage_must_belong_to_route(domain):
    other_region = Region.objects.create(
        slug="outra-regiao",
        public_name="Outra região",
        center_point=Point(-48, -1, srid=4326),
        boundary=_boundary(-48.2, -1.2, -47.8, -0.8),
    )
    other_route = Route.objects.create(
        region=other_region,
        slug="outra-rota",
        public_name="Outra rota",
        short_promise="Outra promessa",
        duration_minutes=30,
        difficulty=Route.Difficulty.EASY,
    )
    payload = _payload(domain)
    mixed_link = deepcopy(payload["route_links"][0])
    mixed_link["route_id"] = str(other_route.pk)
    mixed_link["stage_id"] = None
    payload["route_links"].append(mixed_link)

    with pytest.raises(serializers.ValidationError):
        _validate(payload)

    payload = _payload(domain)
    payload["route_links"][0]["route_id"] = str(other_route.pk)
    with pytest.raises(serializers.ValidationError):
        _validate(payload)


@pytest.mark.django_db
def test_inactive_category_and_repeated_payload_relations_are_rejected(domain):
    domain["category"].is_active = False
    domain["category"].save(update_fields=["is_active"])
    with pytest.raises(serializers.ValidationError):
        _validate(_payload(domain))

    domain["category"].is_active = True
    domain["category"].save(update_fields=["is_active"])
    payload = _payload(domain)
    payload["route_links"].append(deepcopy(payload["route_links"][0]))
    with pytest.raises(serializers.ValidationError) as repeated:
        _validate(payload)
    assert "duplicate_input" in str(repeated.value.get_codes())


@pytest.mark.django_db
def test_exact_public_contact_detects_duplicate_without_returning_contact_value(domain):
    actor = _actor(domain)
    ContactChannel.objects.create(
        actor=actor,
        channel_type=ContactChannel.ChannelType.WHATSAPP,
        public_value="+5593999999999",
        is_public=True,
        source_type=ContactChannel.SourceType.CONSOLIDATED_SHEET,
        source_reference="planilha:linha-001",
        verified_at=timezone.now(),
    )
    payload = _payload(domain)
    payload["contacts"] = [
        {
            "channel_type": "whatsapp",
            "value": "+5593999999999",
            "is_public": True,
            "source_type": "consolidated_sheet",
            "source_reference": "planilha:linha-002",
            "verified_at": timezone.now().isoformat(),
        }
    ]

    with pytest.raises(DuplicateSupportPointError) as duplicate:
        _validate(payload)

    assert duplicate.value.candidate_ids == (str(actor.pk),)
    assert "+5593999999999" not in str(duplicate.value.candidates)


@pytest.mark.django_db
def test_exact_normalized_address_detects_duplicate(domain):
    actor = _actor(
        domain,
        address={
            "locality": "  COMUNIDADE Exemplo ",
            "administrative_area": "pa",
            "country_code": "BR",
        },
    )

    with pytest.raises(DuplicateSupportPointError) as duplicate:
        _validate(_payload(domain))

    assert duplicate.value.candidate_ids == (str(actor.pk),)
    assert duplicate.value.candidates[0].signals == ("address_exact",)


@pytest.mark.django_db
def test_similar_name_within_100_meters_detects_duplicate(domain):
    actor = _actor(
        domain,
        name="Base de Apoio Comunitaria",
        address={"locality": "Outro local", "country_code": "BR"},
        point=Point(-54.9522, -2.4972, srid=4326),
    )

    with pytest.raises(DuplicateSupportPointError) as duplicate:
        _validate(_payload(domain))

    assert duplicate.value.candidate_ids == (str(actor.pk),)
    assert duplicate.value.candidates[0].signals == ("name_nearby",)


@pytest.mark.django_db
def test_proximity_alone_does_not_block_colocated_points(domain):
    _actor(
        domain,
        name="Farmácia comunitária",
        address={"locality": "Outro local", "country_code": "BR"},
        point=Point(-54.9522, -2.4972, srid=4326),
    )

    serializer = _validate(_payload(domain))

    assert serializer.is_valid()


@pytest.mark.django_db
def test_duplicate_outside_selected_region_is_not_disclosed(domain):
    other_region = Region.objects.create(
        slug="regiao-distante",
        public_name="Região distante",
        center_point=Point(-54.95, -2.5, srid=4326),
        boundary=_boundary(),
    )
    actor = Actor.objects.create(
        external_id=f"test:{uuid4()}",
        actor_kind=Actor.ActorKind.SUPPORT,
        category=domain["category"],
        slug=f"fora-{uuid4().hex[:10]}",
        public_name="Base de apoio comunitária",
        short_description="Registro fora do escopo.",
    )
    ActorLocation.objects.create(
        actor=actor,
        region=other_region,
        label="Principal",
        address_fields={"locality": "Comunidade exemplo", "country_code": "BR"},
        point=Point(-54.952, -2.497, srid=4326),
        is_primary=True,
    )

    serializer = _validate(_payload(domain))

    assert serializer.is_valid()


@pytest.mark.django_db
def test_transaction_creates_only_draft_aggregate_and_minimal_audit(domain):
    user = get_user_model().objects.create_user(username="creator", password="unused")
    serializer = _validate(_payload(domain), user=user)
    key = uuid4()

    result = create_support_point(
        user=user,
        data=serializer.validated_data,
        idempotency_key=key,
        request_id=uuid4(),
    )

    actor = Actor.objects.get(pk=result.payload["id"])
    assert actor.actor_kind == Actor.ActorKind.SUPPORT
    assert actor.editorial_status == EditorialStatus.DRAFT
    assert actor.partnership_type == Actor.PartnershipType.EDITORIAL
    assert actor.locations.get().is_primary is True
    assert RouteActor.objects.filter(actor=actor).count() == 1
    event = AuditEvent.objects.get(action=AuditEvent.Action.SUPPORT_POINT_CREATE)
    assert event.metadata["contact_count"] == 0
    assert "public_name" not in event.metadata
    assert "address" not in event.metadata


@pytest.mark.django_db
def test_idempotent_replay_returns_same_result_without_new_rows_or_audit(domain):
    user = get_user_model().objects.create_user(username="replay", password="unused")
    serializer = _validate(_payload(domain), user=user)
    key = uuid4()
    arguments = {
        "user": user,
        "data": serializer.validated_data,
        "idempotency_key": key,
        "request_id": uuid4(),
    }

    first = create_support_point(**arguments)
    second = create_support_point(**arguments)

    assert second.replayed is True
    assert second.payload == first.payload
    assert Actor.objects.count() == 1
    assert SupportPointIdempotencyRecord.objects.count() == 1
    assert AuditEvent.objects.count() == 1


@pytest.mark.django_db
def test_same_idempotency_key_with_different_fingerprint_is_rejected(domain):
    user = get_user_model().objects.create_user(username="fingerprint", password="unused")
    serializer = _validate(_payload(domain), user=user)
    key = uuid4()
    create_support_point(
        user=user,
        data=serializer.validated_data,
        idempotency_key=key,
        request_id=uuid4(),
    )
    changed = deepcopy(serializer.validated_data)
    changed["actor"]["short_description"] = "Descrição editorial diferente."

    with pytest.raises(SupportPointCreationConflict) as conflict:
        create_support_point(
            user=user,
            data=changed,
            idempotency_key=key,
            request_id=uuid4(),
        )

    assert conflict.value.code == "idempotency_conflict"
    assert Actor.objects.count() == 1
    assert AuditEvent.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "target,error_message",
    [
        ("ContactChannel.objects.create", "contact unavailable"),
        ("RouteActor.objects.create", "route link unavailable"),
    ],
)
def test_suboperation_failure_rolls_back_every_row(domain, monkeypatch, target, error_message):
    user = get_user_model().objects.create_user(
        username=f"rollback-{error_message.split()[0]}", password="unused"
    )
    payload = _payload(domain)
    if target.startswith("ContactChannel"):
        payload["contacts"] = [
            {
                "channel_type": "email",
                "value": "publico@example.org",
                "is_public": True,
                "source_type": "consolidated_sheet",
                "source_reference": "planilha:linha-rollback",
                "verified_at": timezone.now().isoformat(),
            }
        ]
    serializer = _validate(payload, user=user)
    model_name, manager_name, method_name = target.split(".")
    model = {"ContactChannel": ContactChannel, "RouteActor": RouteActor}[model_name]
    monkeypatch.setattr(
        getattr(model, manager_name),
        method_name,
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError(error_message)),
    )

    with pytest.raises(RuntimeError, match=error_message):
        create_support_point(
            user=user,
            data=serializer.validated_data,
            idempotency_key=uuid4(),
            request_id=uuid4(),
        )

    assert Actor.objects.count() == 0
    assert ActorLocation.objects.count() == 0
    assert ContactChannel.objects.count() == 0
    assert RouteActor.objects.count() == 0
    assert SupportPointIdempotencyRecord.objects.count() == 0
    assert AuditEvent.objects.count() == 0


@pytest.mark.django_db
def test_audit_failure_rolls_back_every_aggregate_row(domain, monkeypatch):
    user = get_user_model().objects.create_user(username="rollback", password="unused")
    serializer = _validate(_payload(domain), user=user)
    monkeypatch.setattr(
        "modules.catalog.support_point_creation.record_audit_event",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("audit unavailable")),
    )

    with pytest.raises(RuntimeError, match="audit unavailable"):
        create_support_point(
            user=user,
            data=serializer.validated_data,
            idempotency_key=uuid4(),
            request_id=uuid4(),
        )

    assert Actor.objects.count() == 0
    assert ActorLocation.objects.count() == 0
    assert RouteActor.objects.count() == 0
    assert SupportPointIdempotencyRecord.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_concurrent_keys_serialize_duplicate_check_on_postgresql(domain):
    if connection.vendor != "postgresql":
        pytest.skip("A prova de locks exige PostgreSQL/PostGIS.")
    user = get_user_model().objects.create_user(username="concurrent", password="unused")
    serializer = _validate(_payload(domain), user=user)
    data = serializer.validated_data

    def create(key):
        close_old_connections()
        try:
            return create_support_point(
                user=user,
                data=deepcopy(data),
                idempotency_key=key,
                request_id=uuid4(),
            )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(create, uuid4()) for _ in range(2)]
        outcomes = []
        for future in futures:
            try:
                outcomes.append(future.result())
            except DuplicateSupportPointError as error:
                outcomes.append(error)

    assert sum(isinstance(item, DuplicateSupportPointError) for item in outcomes) == 1
    assert sum(not isinstance(item, DuplicateSupportPointError) for item in outcomes) == 1
    assert Actor.objects.count() == 1
    assert SupportPointIdempotencyRecord.objects.count() == 1
    assert AuditEvent.objects.count() == 1
