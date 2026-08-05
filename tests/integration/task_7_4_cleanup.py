import os

from django.contrib.auth import get_user_model
from django.conf import settings

from modules.analytics.models import RawAnalyticsEvent
from modules.catalog.models import Actor
from modules.regions.models import Region
from modules.reports.models import PublicReport


expected_project_ref = os.environ.get("TASK_7_4_SUPABASE_PROJECT_REF", "")
database_host = str(settings.DATABASES["default"].get("HOST", ""))
if not expected_project_ref or expected_project_ref not in database_host:
    raise RuntimeError("Limpeza recusada: projeto Supabase não autorizado.")

event_ids = [value for value in os.getenv("TASK_7_4_EVENT_IDS", "").split(",") if value]
RawAnalyticsEvent.objects.filter(event_id__in=event_ids).delete()
PublicReport.objects.filter(region_slug__startswith="integration-").delete()
Actor.objects.filter(public_name="Apoio HTTP Integrado").delete()
Region.objects.filter(slug__in=("integration-norte", "integration-sul")).delete()
get_user_model().objects.filter(
    username__in=("integration_admin", "integration_staff")
).delete()
print("fixtures task 7.4 removidas")
