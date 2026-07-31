from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from modules.imports.pindobal_inventory import (
    PindobalInventoryError,
    adapt_pindobal_inventory,
    write_pindobal_inventory_outputs,
)


class Command(BaseCommand):
    help = "Une o inventário histórico ao complemento operacional e gera rascunhos canônicos."

    def add_arguments(self, parser):
        parser.add_argument("--raw", required=True, help="CSV histórico da Secretaria de Turismo.")
        parser.add_argument("--operational", required=True, help="CSV operacional enriquecido.")
        parser.add_argument("--output-dir", required=True, help="Pasta dos arquivos adequados.")

    def handle(self, *args, **options):
        raw_path = Path(options["raw"]).resolve()
        operational_path = Path(options["operational"]).resolve()
        output_dir = Path(options["output_dir"]).resolve()
        try:
            result = adapt_pindobal_inventory(
                raw_path.read_bytes(),
                operational_path.read_bytes(),
            )
            catalog, review, summary = write_pindobal_inventory_outputs(result, output_dir)
        except (OSError, PindobalInventoryError) as error:
            raise CommandError(str(error)) from error
        self.stdout.write(
            self.style.SUCCESS(
                f"Adequação concluída: {result.summary['merged_records']} registros unidos, "
                f"{result.summary['canonical_drafts']} rascunhos canônicos e "
                f"{result.summary['quarantined_google_rows']} candidatos Google em quarentena."
            )
        )
        self.stdout.write(f"Catálogo: {catalog}")
        self.stdout.write(f"Revisão: {review}")
        self.stdout.write(f"Resumo: {summary}")
