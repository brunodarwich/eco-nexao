from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from modules.analytics.models import RawAnalyticsEvent


class Command(BaseCommand):
    help = (
        "Comando idempotente de expurgo de dados de eventos brutos de analytics "
        "com mais de N dias (padrão: 90 dias) e suporte ao modo de prévia (--dry-run)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Janela em dias de retenção para expurgo de eventos brutos (padrão: 90).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Exibe contagem dos registros a serem expurgados sem exclusão efetiva.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]

        if days <= 0:
            self.stderr.write(self.style.ERROR("O número de dias deve ser maior que 0."))
            return

        cutoff_date = timezone.now() - timedelta(days=days)
        events_to_purge = RawAnalyticsEvent.objects.filter(occurred_at__lt=cutoff_date)
        count = events_to_purge.count()
        iso_cutoff = cutoff_date.isoformat()

        if dry_run:
            msg = (
                f"[PRÉVIA] {count} evento(s) com mais de {days} dias "
                f"(< {iso_cutoff}) seriam expurgados."
            )
            self.stdout.write(self.style.WARNING(msg))
        else:
            deleted_count, _ = events_to_purge.delete()
            msg = (
                f"[EXPURGO] Sucesso: {deleted_count} evento(s) com mais de {days} dias expurgados."
            )
            self.stdout.write(self.style.SUCCESS(msg))
