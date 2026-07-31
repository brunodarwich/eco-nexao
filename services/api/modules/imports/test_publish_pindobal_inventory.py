import csv

import pytest
from django.core.management.base import CommandError

from modules.imports.catalog_csv import CATALOG_COLUMNS
from modules.imports.management.commands.publish_pindobal_inventory import Command, _rows


def _write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=CATALOG_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _row(**overrides):
    row = {column: "" for column in CATALOG_COLUMNS}
    row.update(
        external_id="inventory:pindobal:1",
        source_type="institutional",
        public_name="Cozinha local",
    )
    row.update(overrides)
    return row


def test_requires_explicit_confirmation(tmp_path):
    path = tmp_path / "inventory.csv"
    _write_csv(path, [_row()])
    with pytest.raises(CommandError, match="confirm-publish-unverified"):
        Command.handle.__wrapped__(Command(), csv=path, confirm_publish_unverified=False)


def test_accepts_only_canonical_non_google_sources(tmp_path):
    path = tmp_path / "inventory.csv"
    _write_csv(path, [_row(), _row(external_id="inventory:pindobal:2", source_type="field")])
    assert len(_rows(path)) == 2

    _write_csv(path, [_row(source_type="google_maps")])
    with pytest.raises(CommandError, match="fontes não publicáveis"):
        _rows(path)
