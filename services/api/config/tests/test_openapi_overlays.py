from pathlib import Path

import pytest

from config.openapi_overlays import apply_design_first_overlays


def test_design_first_overlay_adds_approved_operation():
    schema = {"paths": {}, "components": {"schemas": {}}}

    result = apply_design_first_overlays(schema, None, None, False)

    assert "/api/v1/admin/catalog/support-points/" in result["paths"]
    assert "SupportPointCreateRequest" in result["components"]["schemas"]


def test_design_first_overlay_refuses_to_shadow_implemented_path():
    schema = {
        "paths": {"/api/v1/admin/catalog/support-points/": {"post": {}}},
        "components": {"schemas": {}},
    }

    with pytest.raises(RuntimeError, match="já é gerado pelo Django"):
        apply_design_first_overlays(schema, None, None, False)


def test_design_first_overlay_file_stays_inside_contract_package():
    overlay = Path(__file__).resolve().parents[4] / "packages/contracts/openapi/design-first.yaml"

    assert overlay.is_file()
