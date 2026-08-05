import copy

import jsonschema
import pytest

from config.openapi_validator import load_openapi_spec

PATH = "/api/v1/admin/catalog/support-points/"
EXPECTED_STATUSES = {"201", "400", "401", "403", "409", "429", "500"}
pytestmark = pytest.mark.filterwarnings(
    "ignore:jsonschema.RefResolver is deprecated:DeprecationWarning"
)


@pytest.fixture(scope="module")
def contract():
    _, preprocessed_spec = load_openapi_spec()
    return preprocessed_spec


def _validator(contract, schema):
    return jsonschema.Draft7Validator(
        schema,
        resolver=jsonschema.RefResolver.from_schema(contract),
        format_checker=jsonschema.FormatChecker(),
    )


def _request_schema(contract):
    return contract["paths"][PATH]["post"]["requestBody"]["content"]["application/json"]["schema"]


def test_support_point_operation_declares_security_headers_and_statuses(contract):
    operation = contract["paths"][PATH]["post"]

    assert operation["operationId"] == "createAdminSupportPoint"
    assert operation["security"] == [{"cookieAuth": []}]
    assert set(operation["responses"]) == EXPECTED_STATUSES

    headers = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "header"
    }
    assert headers["Idempotency-Key"]["required"] is True
    assert headers["Idempotency-Key"]["schema"]["format"] == "uuid"
    assert headers["X-CSRFToken"]["required"] is True


def test_support_point_request_accepts_precise_draft_input(contract):
    payload = {
        "actor": {
            "category_id": "2cf8aa62-c48f-4b49-a882-ecfad96a0976",
            "public_name": "Base de apoio comunitária",
            "short_description": "Água potável e orientação local.",
            "services": ["Água potável", "Informações"],
        },
        "location": {
            "label": "Entrada principal",
            "address_fields": {
                "locality": "Comunidade exemplo",
                "administrative_area": "PA",
                "country_code": "BR",
            },
            "latitude": -2.497,
            "longitude": -54.952,
            "public_visibility": True,
        },
        "contacts": [
            {
                "channel_type": "whatsapp",
                "value": "+5593999999999",
                "is_public": True,
                "source_type": "consolidated_sheet",
                "source_reference": "planilha:linha-001",
                "verified_at": "2026-08-05T12:00:00Z",
            }
        ],
        "route_links": [
            {
                "route_id": "e706d05c-9f73-4543-9d6d-dbb93d60d87e",
                "stage_id": None,
                "route_role": "support",
                "editorial_position": 1,
                "is_featured": False,
                "sponsorship_label": "",
            }
        ],
    }

    errors = list(_validator(contract, _request_schema(contract)).iter_errors(payload))
    assert errors == []

    private_contact = copy.deepcopy(payload)
    private_contact["contacts"][0]["is_public"] = False
    assert list(_validator(contract, _request_schema(contract)).iter_errors(private_contact))


@pytest.mark.parametrize(
    "forbidden_field", ["external_id", "slug", "actor_kind", "editorial_status"]
)
def test_support_point_request_rejects_server_controlled_actor_fields(contract, forbidden_field):
    payload = {
        "actor": {
            "category_id": "2cf8aa62-c48f-4b49-a882-ecfad96a0976",
            "public_name": "Base de apoio comunitária",
            "short_description": "Água potável e orientação local.",
            forbidden_field: "client-controlled",
        },
        "location": {
            "label": "Entrada principal",
            "address_fields": {"locality": "Comunidade exemplo", "country_code": "BR"},
            "latitude": -2.497,
            "longitude": -54.952,
            "public_visibility": True,
        },
        "contacts": [],
        "route_links": [
            {
                "route_id": "e706d05c-9f73-4543-9d6d-dbb93d60d87e",
                "route_role": "support",
                "editorial_position": 1,
                "is_featured": False,
                "sponsorship_label": "",
            }
        ],
    }

    assert list(_validator(contract, _request_schema(contract)).iter_errors(payload))


def test_support_point_request_rejects_invalid_coordinates_and_contact(contract):
    invalid_payload = {
        "actor": {
            "category_id": "2cf8aa62-c48f-4b49-a882-ecfad96a0976",
            "public_name": "Base de apoio comunitária",
            "short_description": "Água potável e orientação local.",
        },
        "location": {
            "label": "Entrada principal",
            "address_fields": {"locality": "Comunidade exemplo", "country_code": "BR"},
            "latitude": 91,
            "longitude": -181,
            "public_visibility": True,
        },
        "contacts": [
            {
                "channel_type": "website",
                "value": "http://inseguro.example",
                "is_public": True,
                "source_type": "consolidated_sheet",
                "source_reference": "planilha:linha-001",
                "verified_at": "2026-08-05T12:00:00Z",
            }
        ],
        "route_links": [
            {
                "route_id": "e706d05c-9f73-4543-9d6d-dbb93d60d87e",
                "route_role": "support",
                "editorial_position": 1,
                "is_featured": False,
                "sponsorship_label": "",
            }
        ],
    }

    errors = list(_validator(contract, _request_schema(contract)).iter_errors(invalid_payload))
    assert len(errors) >= 2


def test_support_point_response_is_minimized_and_fixed_to_draft(contract):
    response_schema = contract["paths"][PATH]["post"]["responses"]["201"]["content"][
        "application/json"
    ]["schema"]
    response = {
        "id": "813b2b6f-a1fc-4e79-8421-09fa03cb7e09",
        "actor_kind": "support",
        "editorial_status": "draft",
        "partnership_type": "editorial",
        "region_id": "d7a64ff8-66b1-4c72-bbb0-ae1ff5262d00",
        "location_id": "1137b5d1-97c4-481e-9f25-1bc32389422e",
        "contact_ids": [],
        "route_links": [
            {
                "id": "bf4b6a63-91ec-4a6f-94ae-0501a358dcdb",
                "route_id": "e706d05c-9f73-4543-9d6d-dbb93d60d87e",
                "stage_id": None,
            }
        ],
        "created_at": "2026-08-05T12:00:00Z",
    }

    assert list(_validator(contract, response_schema).iter_errors(response)) == []

    leaked = copy.deepcopy(response)
    leaked["coordinates"] = [-54.952, -2.497]
    assert list(_validator(contract, response_schema).iter_errors(leaked))


@pytest.mark.parametrize("status", sorted(EXPECTED_STATUSES - {"201"}))
def test_support_point_errors_use_one_minimized_envelope(contract, status):
    schema = contract["paths"][PATH]["post"]["responses"][status]["content"]["application/json"][
        "schema"
    ]
    error = {
        "code": "validation_error" if status == "400" else "request_failed",
        "message": "Não foi possível concluir a operação.",
        "field_errors": {},
        "request_id": "d6d5edb4-195f-42b6-8d64-1a14520a75c8",
    }

    assert list(_validator(contract, schema).iter_errors(error)) == []
