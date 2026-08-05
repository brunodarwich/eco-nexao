from django.core.management.base import BaseCommand
from django.utils import timezone

from modules.catalog.models import SupportPointIdempotencyRecord


class Command(BaseCommand):
    help = "Remove registros expirados de idempotência do cadastro manual."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        queryset = SupportPointIdempotencyRecord.objects.filter(expires_at__lte=timezone.now())
        count = queryset.count()
        if not options["dry_run"]:
            queryset.delete()
        mode = "encontrados" if options["dry_run"] else "removidos"
        self.stdout.write(f"{count} registro(s) expirado(s) {mode}.")
