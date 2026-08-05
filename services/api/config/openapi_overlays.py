from pathlib import Path
from typing import Any

import yaml


def _overlay_path() -> Path:
    repository_root = Path(__file__).resolve().parents[3]
    return repository_root / "packages" / "contracts" / "openapi" / "design-first.yaml"


def apply_design_first_overlays(
    result: dict[str, Any], generator: Any, request: Any, public: bool
) -> dict[str, Any]:
    """Merge approved operations that intentionally precede their endpoint implementation."""
    del generator, request, public

    with _overlay_path().open(encoding="utf-8") as overlay_file:
        overlay = yaml.safe_load(overlay_file) or {}

    for path, path_item in overlay.get("paths", {}).items():
        if path in result.setdefault("paths", {}):
            raise RuntimeError(
                f"O path {path} já é gerado pelo Django; remova-o do overlay design-first."
            )
        result["paths"][path] = path_item

    schemas = result.setdefault("components", {}).setdefault("schemas", {})
    for name, schema in overlay.get("components", {}).get("schemas", {}).items():
        if name in schemas:
            raise RuntimeError(
                f"O schema {name} já é gerado pelo Django; remova-o do overlay design-first."
            )
        schemas[name] = schema

    return result
