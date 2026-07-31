import csv
import io
from pathlib import Path

import pytest

from .catalog_csv import CatalogRelationIndex, validate_catalog_csv
from .pindobal_inventory import (
    ENRICHED_COLUMNS,
    LEGACY_COLUMNS,
    PindobalInventoryError,
    adapt_pindobal_inventory,
    write_pindobal_inventory_outputs,
)


def _csv_bytes(columns, rows):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode()


def _row(*, identifier="1", page="31", title="Ponto Setur"):
    shared = {column: "" for column in LEGACY_COLUMNS}
    shared.update(
        {
            "pagina": page,
            "categoria": "mercado",
            "titulo": title,
            "coordenadas_geograficas": "-2.5, -54.9",
            "endereco": "Rua Exemplo, 10 - CEP 68060-000",
            "local": "Santarém/PA",
            "telefone": "(93) 99999-0000",
            "texto_bruto": title,
            "forma_de_acesso": "Carro",
        }
    )
    enriched = {**shared, **{column: "" for column in ENRICHED_COLUMNS if column not in shared}}
    enriched.update(
        {
            "id": identifier,
            "latitude": "-2.5",
            "longitude": "-54.9",
            "status_coord": "ok",
            "categoria_normalizada": "mercado",
            "categoria_id": "mercado",
            "dist_rota_m": "20",
            "km_rota": "4.2",
            "segmento_rota": "3",
            "ponto_projetado_rota": "[-54.9, -2.5]",
        }
    )
    return shared, enriched


def test_joins_shared_rows_and_quarantines_google_candidates():
    setur, enriched_setur = _row()
    google, enriched_google = _row(identifier="2", page="Pesquisa Google Maps 2026", title="Google")
    result = adapt_pindobal_inventory(
        _csv_bytes(LEGACY_COLUMNS, [setur, google]),
        _csv_bytes(ENRICHED_COLUMNS, [enriched_google, enriched_setur]),
    )
    assert result.summary["merged_records"] == 2
    assert result.summary["canonical_drafts"] == 1
    assert result.summary["quarantined_google_rows"] == 1
    assert result.canonical_rows[0]["external_id"] == "inventory:pindobal:1"
    assert result.canonical_rows[0]["source_type"] == "institutional"
    assert any(item.code == "google_source_quarantine" for item in result.review_items)


def test_blocks_when_shared_source_values_diverge():
    raw, enriched = _row()
    enriched["titulo"] = "Título divergente"
    with pytest.raises(PindobalInventoryError, match="fontes divergem"):
        adapt_pindobal_inventory(
            _csv_bytes(LEGACY_COLUMNS, [raw]),
            _csv_bytes(ENRICHED_COLUMNS, [enriched]),
        )


def test_current_repository_sources_reconcile_without_duplicate_inflation(tmp_path):
    repository = Path(__file__).resolve().parents[4]
    result = adapt_pindobal_inventory(
        (repository / "santarem-pindobal.csv").read_bytes(),
        (repository / "pontos_interesse.csv").read_bytes(),
    )
    assert result.summary["raw_rows"] == 195
    assert result.summary["operational_rows"] == 195
    assert result.summary["merged_records"] == 195
    assert result.summary["canonical_drafts"] == 181
    assert result.summary["quarantined_google_rows"] == 14
    assert result.summary["possible_duplicate_pairs"] == 0

    catalog_path, _, _ = write_pindobal_inventory_outputs(result, tmp_path)
    validation = validate_catalog_csv(
        catalog_path.read_bytes(),
        CatalogRelationIndex(
            region_slugs=frozenset({"santarem-alter-do-chao"}),
            category_slugs=frozenset(row["category_slug"] for row in result.canonical_rows),
            route_keys=frozenset({("santarem-alter-do-chao", "pindobal")}),
        ),
    )
    assert validation.valid, validation.issues
