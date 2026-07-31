import csv
import io
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from django.contrib.gis.geos import MultiPolygon, Point, Polygon
from drf_spectacular.generators import SchemaGenerator

from modules.catalog.models import ExternalDiscoveryRun, ExternalSourceReference
from modules.imports.catalog_csv import CATALOG_COLUMNS, CatalogRelationIndex, validate_catalog_csv
from modules.imports.commit import commit_catalog_import
from modules.imports.models import CatalogImportBatch, CatalogImportDraft


def build_csv_bytes(rows: list[list[str]]) -> bytes:
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue().encode()


def get_base_row(**kwargs) -> dict[str, str]:
    row = {col: "" for col in CATALOG_COLUMNS}
    row.update(
        {
            "external_id": "test:actor:1",
            "action": "upsert",
            "record_status": "active",
            "publish_status": "draft",
            "region_slug": "santarem-alter-do-chao",
            "route_slugs": "pindobal",
            "route_role": "support",
            "actor_kind": "business",
            "category_slug": "alimentacao",
            "public_name": "Restaurante Teste WGS84",
            "short_description": "Restaurante de teste",
            "city": "Santarém",
            "state": "PA",
            "country_code": "BR",
            "latitude": "-2.4435",
            "longitude": "-54.7082",
            "source_type": "mock",
            "source_reference": "test:template",
            "verification_status": "unverified",
            "public_contact_authorized": "false",
            "media_authorized": "false",
        }
    )
    row.update(kwargs)
    return row


def default_relations(
    actor_external_ids: frozenset[str] = frozenset(),
) -> CatalogRelationIndex:
    return CatalogRelationIndex(
        region_slugs=frozenset({"santarem-alter-do-chao"}),
        category_slugs=frozenset({"alimentacao"}),
        route_keys=frozenset({("santarem-alter-do-chao", "pindobal")}),
        actor_external_ids=actor_external_ids,
    )


# --- 1. GEOGRAPHIC LIMITS WGS84 / POSTGIS ---


def test_wgs84_point_coordinates_valid_range():
    lon, lat = -54.7082, -2.4435
    pt = Point(lon, lat, srid=4326)

    assert pt.srid == 4326
    assert -180.0 <= pt.x <= 180.0
    assert -90.0 <= pt.y <= 90.0
    assert pt.x == lon
    assert pt.y == lat


def test_wgs84_csv_validation_rejects_out_of_bounds_coordinates():
    relations = default_relations()

    # Latitude out of bounds (> 90)
    invalid_lat_row = get_base_row(latitude="95.1234", external_id="test:lat_out")
    result_lat = validate_catalog_csv(
        build_csv_bytes([CATALOG_COLUMNS, [invalid_lat_row[col] for col in CATALOG_COLUMNS]]),
        relations,
    )
    assert not result_lat.valid
    assert "out_of_range" in {issue.code for issue in result_lat.issues}

    # Longitude out of bounds (< -180)
    invalid_lon_row = get_base_row(longitude="-185.5000", external_id="test:lon_out")
    result_lon = validate_catalog_csv(
        build_csv_bytes([CATALOG_COLUMNS, [invalid_lon_row[col] for col in CATALOG_COLUMNS]]),
        relations,
    )
    assert not result_lon.valid
    assert "out_of_range" in {issue.code for issue in result_lon.issues}


def test_wgs84_multipolygon_service_area_srid_4326():
    poly = Polygon(
        (
            (-54.75, -2.45),
            (-54.70, -2.45),
            (-54.70, -2.40),
            (-54.75, -2.40),
            (-54.75, -2.45),
        )
    )
    multi_poly = MultiPolygon(poly, srid=4326)

    assert multi_poly.srid == 4326
    assert len(multi_poly) == 1
    bounds = multi_poly.extent  # (xmin, ymin, xmax, ymax)
    assert -180.0 <= bounds[0] and bounds[2] <= 180.0
    assert -90.0 <= bounds[1] and bounds[3] <= 90.0


def test_external_discovery_run_coordinates_wgs84_limits():
    run = ExternalDiscoveryRun(
        provider=ExternalSourceReference.Provider.GOOGLE_PLACES,
        context_key="pindobal-preview",
        center_latitude=-2.4435,
        center_longitude=-54.7082,
        radius_meters=5000,
        included_types=["restaurant"],
        max_results=20,
        result_count=5,
    )

    assert -90 <= run.center_latitude <= 90
    assert -180 <= run.center_longitude <= 180


# --- 2. OPENAPI SCHEMA VALIDATION ---


def test_openapi_schema_builds_without_errors():
    generator = SchemaGenerator()
    schema = generator.get_schema(request=None, public=True)

    assert "openapi" in schema
    assert "paths" in schema
    assert "components" in schema
    assert schema["info"]["title"] == "ECOnexão API"


def test_openapi_schema_catalog_and_discovery_paths_documented():
    generator = SchemaGenerator()
    schema = generator.get_schema(request=None, public=True)
    paths = schema["paths"]

    # Check Discovery Preview endpoint
    discovery_path = "/api/v1/admin/discovery/google-places/preview"
    assert discovery_path in paths
    assert "post" in paths[discovery_path]
    post_op = paths[discovery_path]["post"]
    assert post_op["operationId"] == "previewGooglePlacesCandidates"
    assert post_op["security"] == [{"cookieAuth": []}]

    # Check Import Validation endpoint
    validate_path = "/api/v1/admin/imports/validate"
    assert validate_path in paths
    assert "post" in paths[validate_path]
    assert paths[validate_path]["post"]["operationId"] == "validateCatalogCsv"

    # Check Import Commit endpoint
    commit_path = "/api/v1/admin/imports/commit"
    assert commit_path in paths
    assert "post" in paths[commit_path]
    assert paths[commit_path]["post"]["operationId"] == "commitCatalogCsv"


def test_openapi_schema_public_paths_documented():
    generator = SchemaGenerator()
    schema = generator.get_schema(request=None, public=True)
    paths = schema["paths"]

    # Region list endpoint
    assert "/api/v1/regions" in paths
    assert "get" in paths["/api/v1/regions"]

    # Public route detail endpoint
    route_detail_path = "/api/v1/regions/{region_slug}/routes/{route_slug}"
    assert route_detail_path in paths
    assert "get" in paths[route_detail_path]


# --- 3. CSV IDEMPOTENCY BY EXTERNAL_ID ---


def test_csv_validation_detects_duplicate_external_ids_in_same_file():
    relations = default_relations()

    row1 = get_base_row(external_id="actor:duplicate:1")
    row2 = get_base_row(external_id="actor:duplicate:1", public_name="Restaurante Duplicado")

    csv_data = build_csv_bytes(
        [
            CATALOG_COLUMNS,
            [row1[col] for col in CATALOG_COLUMNS],
            [row2[col] for col in CATALOG_COLUMNS],
        ]
    )

    result = validate_catalog_csv(csv_data, relations)

    assert not result.valid
    issue_codes = {issue.code for issue in result.issues}
    assert "duplicate_external_id" in issue_codes


def test_csv_validation_maps_operations_by_external_id_identity():
    relations = default_relations(
        actor_external_ids=frozenset({"actor:existing:1", "actor:to:archive"}),
    )

    create_row = get_base_row(external_id="actor:new:1")
    update_row = get_base_row(external_id="actor:existing:1")
    archive_row = get_base_row(external_id="actor:to:archive", action="archive")

    csv_data = build_csv_bytes(
        [
            CATALOG_COLUMNS,
            [create_row[col] for col in CATALOG_COLUMNS],
            [update_row[col] for col in CATALOG_COLUMNS],
            [archive_row[col] for col in CATALOG_COLUMNS],
        ]
    )

    result = validate_catalog_csv(csv_data, relations)

    assert result.valid
    operations = [(row.external_id, row.operation) for row in result.preview_rows]
    assert operations == [
        ("actor:new:1", "create"),
        ("actor:existing:1", "update"),
        ("actor:to:archive", "archive"),
    ]


def test_catalog_import_commit_idempotent_replay():
    csv_hash = "a" * 64
    idempotency_key = uuid4()
    user = SimpleNamespace(pk=42)

    existing_batch = SimpleNamespace(
        pk=uuid4(),
        sha256=csv_hash,
        idempotency_key=idempotency_key,
        created_by_id=user.pk,
    )

    batch_queryset = MagicMock()
    batch_queryset.first.return_value = existing_batch

    validation_result = SimpleNamespace(
        valid=True,
        sha256=csv_hash,
        row_count=1,
        issues=(),
        preview_rows=(SimpleNamespace(line=2, external_id="actor:new:1", operation="create"),),
        normalized_rows=({"external_id": "actor:new:1", "region_slug": "santarem-alter-do-chao"},),
    )

    with (
        patch("modules.imports.commit.validate_catalog_csv", return_value=validation_result),
        patch(
            "modules.imports.commit.CatalogImportBatch.objects.filter",
            return_value=batch_queryset,
        ) as batch_filter,
        patch("modules.imports.commit.CatalogImportDraft.objects.bulk_create") as bulk_create,
        patch("modules.imports.commit.record_audit_event") as record_audit,
    ):
        replay_result = commit_catalog_import.__wrapped__(
            content=b"header\nrow",
            original_filename="catalogo.csv",
            expected_sha256=csv_hash,
            idempotency_key=idempotency_key,
            user=user,
            relations=SimpleNamespace(),
            request_id=uuid4(),
        )

    assert replay_result.replayed is True
    assert replay_result.batch is existing_batch
    batch_filter.assert_called_once()
    bulk_create.assert_not_called()
    record_audit.assert_not_called()


def test_catalog_import_draft_db_constraints_enforce_idempotency():
    constraint_names = {c.name for c in CatalogImportDraft._meta.constraints}
    assert "import_draft_batch_line_uniq" in constraint_names
    assert "import_draft_batch_external_uniq" in constraint_names
    assert "import_draft_line_valid" in constraint_names

    batch_field = CatalogImportBatch._meta.get_field("sha256")
    assert batch_field.unique
    idem_field = CatalogImportBatch._meta.get_field("idempotency_key")
    assert idem_field.unique


def test_external_source_reference_idempotent_linking():
    constraint_names = {c.name for c in ExternalSourceReference._meta.constraints}
    assert "external_source_provider_id_uniq" in constraint_names
