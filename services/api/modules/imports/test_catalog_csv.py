import csv
import io
from pathlib import Path

from .catalog_csv import (
    CATALOG_COLUMNS,
    MAX_CSV_BYTES,
    MAX_CSV_ROWS,
    CatalogRelationIndex,
    validate_catalog_csv,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
TEMPLATE_PATH = REPOSITORY_ROOT / "spec" / "schemas" / "catalogo-template.csv"
RELATIONS = CatalogRelationIndex(
    region_slugs=frozenset({"santarem-alter-do-chao"}),
    category_slugs=frozenset({"alimentacao", "guias"}),
    route_keys=frozenset({("santarem-alter-do-chao", "pindobal")}),
)


def template_content() -> bytes:
    return TEMPLATE_PATH.read_bytes()


def rows_to_bytes(rows: list[list[str]]) -> bytes:
    output = io.StringIO(newline="")
    csv.writer(output, lineterminator="\n").writerows(rows)
    return output.getvalue().encode()


def template_rows() -> list[list[str]]:
    return list(csv.reader(io.StringIO(template_content().decode())))


def issue_codes(result) -> set[str]:
    return {issue.code for issue in result.issues}


def test_official_template_is_accepted_with_only_editorial_warnings():
    result = validate_catalog_csv(template_content(), RELATIONS)

    assert result.valid
    assert result.row_count == 2
    assert result.error_count == 0
    assert result.sha256
    assert len(result.normalized_rows) == 2
    assert {"unstructured_opening_hours"} <= issue_codes(result)


def test_rejects_header_that_differs_from_official_template():
    rows = template_rows()
    rows[0][0], rows[0][1] = rows[0][1], rows[0][0]

    result = validate_catalog_csv(rows_to_bytes(rows), RELATIONS)

    assert not result.valid
    assert result.row_count == 0
    assert issue_codes(result) == {"invalid_header"}


def test_reports_duplicate_id_invalid_types_and_relations_without_cell_values():
    rows = template_rows()
    first = dict(zip(CATALOG_COLUMNS, rows[1], strict=True))
    first["latitude"] = "91"
    first["email"] = "private-invalid-email"
    first["region_slug"] = "regiao-secreta"
    first["publish_status"] = "published"
    row = [first[column] for column in CATALOG_COLUMNS]

    result = validate_catalog_csv(rows_to_bytes([rows[0], row, row]), RELATIONS)

    assert not result.valid
    assert {
        "duplicate_external_id",
        "invalid_choice",
        "invalid_email",
        "out_of_range",
        "unknown_relation",
    } <= issue_codes(result)
    assert "private-invalid-email" not in str(result.issues)


def test_requires_media_metadata_verification_provenance_and_contact_consent():
    rows = template_rows()
    item = dict(zip(CATALOG_COLUMNS, rows[1], strict=True))
    item.update(
        {
            "publish_status": "review",
            "verification_status": "direct",
            "verified_at": "",
            "verified_by": "",
            "image_alt": "",
            "image_credit": "",
            "public_contact_authorized": "false",
            "phone_e164": "+5593999990001",
        }
    )

    result = validate_catalog_csv(
        rows_to_bytes([rows[0], [item[column] for column in CATALOG_COLUMNS]]),
        RELATIONS,
    )

    assert {
        "contact_not_authorized",
        "incomplete_media",
        "incomplete_verification",
    } <= issue_codes(result)


def test_rejects_non_utf8_and_malformed_rows():
    encoding_result = validate_catalog_csv(b"\xff\xfe", RELATIONS)
    malformed_result = validate_catalog_csv(
        (",".join(CATALOG_COLUMNS) + '\n"unterminated').encode(),
        RELATIONS,
    )

    assert issue_codes(encoding_result) == {"invalid_encoding"}
    assert "malformed_csv" in issue_codes(malformed_result)


def test_rejects_file_over_size_limit_before_parsing():
    result = validate_catalog_csv(b"x" * (MAX_CSV_BYTES + 1), RELATIONS)

    assert not result.valid
    assert result.row_count == 0
    assert issue_codes(result) == {"file_too_large"}


def test_rejects_more_than_maximum_rows_without_partial_preview():
    rows = template_rows()
    template = dict(zip(CATALOG_COLUMNS, rows[1], strict=True))
    template["opening_hours_text"] = ""
    content = [rows[0]]
    for index in range(MAX_CSV_ROWS + 1):
        item = {**template, "external_id": f"source:{index}"}
        content.append([item[column] for column in CATALOG_COLUMNS])

    result = validate_catalog_csv(rows_to_bytes(content), RELATIONS)

    assert not result.valid
    assert result.row_count == MAX_CSV_ROWS + 1
    assert "too_many_rows" in issue_codes(result)
    assert result.preview_rows == ()


def test_previews_create_update_and_archive_only_after_valid_validation():
    rows = template_rows()
    create_row = dict(zip(CATALOG_COLUMNS, rows[1], strict=True))
    create_row["external_id"] = "source:create"
    update_row = dict(zip(CATALOG_COLUMNS, rows[1], strict=True))
    update_row["external_id"] = "source:update"
    archive_row = dict(zip(CATALOG_COLUMNS, rows[1], strict=True))
    archive_row["external_id"] = "source:archive"
    archive_row["action"] = "archive"
    relations = CatalogRelationIndex(
        region_slugs=RELATIONS.region_slugs,
        category_slugs=RELATIONS.category_slugs,
        route_keys=RELATIONS.route_keys,
        actor_external_ids=frozenset({"source:update", "source:archive"}),
    )

    result = validate_catalog_csv(
        rows_to_bytes(
            [
                rows[0],
                [create_row[column] for column in CATALOG_COLUMNS],
                [update_row[column] for column in CATALOG_COLUMNS],
                [archive_row[column] for column in CATALOG_COLUMNS],
            ]
        ),
        relations,
    )

    assert result.valid
    assert [(row.line, row.external_id, row.operation) for row in result.preview_rows] == [
        (2, "source:create", "create"),
        (3, "source:update", "update"),
        (4, "source:archive", "archive"),
    ]


def test_blocks_preview_for_missing_archive_target_or_actor_outside_scope():
    rows = template_rows()
    missing = dict(zip(CATALOG_COLUMNS, rows[1], strict=True))
    missing["external_id"] = "source:missing"
    missing["action"] = "archive"
    unavailable = dict(zip(CATALOG_COLUMNS, rows[1], strict=True))
    unavailable["external_id"] = "source:outside"
    relations = CatalogRelationIndex(
        region_slugs=RELATIONS.region_slugs,
        category_slugs=RELATIONS.category_slugs,
        route_keys=RELATIONS.route_keys,
        unavailable_actor_external_ids=frozenset({"source:outside"}),
    )

    result = validate_catalog_csv(
        rows_to_bytes(
            [
                rows[0],
                [missing[column] for column in CATALOG_COLUMNS],
                [unavailable[column] for column in CATALOG_COLUMNS],
            ]
        ),
        relations,
    )

    assert not result.valid
    assert result.preview_rows == ()
    assert {"invalid_archive_target", "unknown_relation"} <= issue_codes(result)
    assert all("source:" not in issue.message for issue in result.issues)
