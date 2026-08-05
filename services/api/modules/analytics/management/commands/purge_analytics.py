from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from modules.analytics.models import DailyAnalyticsAggregate, RawAnalyticsEvent


class Command(BaseCommand):
    help = (
        "Comando idempotente de expurgo de dados de eventos brutos de analytics "
        "brutos com mais de N horas (padrão: 24) e agregados com mais de 13 meses."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Janela em horas de retenção de eventos brutos (padrão: 24).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Exibe contagem dos registros a serem expurgados sem exclusão efetiva.",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        dry_run = options["dry_run"]

        if hours <= 0:
            self.stderr.write(self.style.ERROR("O número de horas deve ser maior que 0."))
            return

        cutoff_date = timezone.now() - timedelta(hours=hours)
        events_to_purge = RawAnalyticsEvent.objects.filter(occurred_at__lt=cutoff_date)
        count = events_to_purge.count()
        iso_cutoff = cutoff_date.isoformat()

        if dry_run:
            msg = (
                f"[PRÉVIA] {count} evento(s) com mais de {hours} horas "
                f"(< {iso_cutoff}) seriam expurgados."
            )
            self.stdout.write(self.style.WARNING(msg))
        else:
            deleted_count, _ = events_to_purge.delete()
            aggregate_cutoff = (timezone.now() - timedelta(days=396)).date()
            DailyAnalyticsAggregate.objects.filter(date__lt=aggregate_cutoff).delete()
            msg = f"[EXPURGO] Sucesso: {deleted_count} evento(s) brutos expurgados."
            self.stdout.write(self.style.SUCCESS(msg))
