import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.gis.geos import Point
from django.conf import settings

from modules.accounts.permissions import AdminRole, role_group_name
from modules.catalog.models import Category
from modules.core.models import EditorialStatus
from modules.regions.models import Region
from modules.routes.models import Route


expected_project_ref = os.environ.get("TASK_7_4_SUPABASE_PROJECT_REF", "")
database_host = str(settings.DATABASES["default"].get("HOST", ""))
if not expected_project_ref:
    raise RuntimeError("TASK_7_4_SUPABASE_PROJECT_REF é obrigatório.")
if expected_project_ref not in database_host:
    raise RuntimeError("A conexão Django não corresponde ao projeto Supabase autorizado.")


regions = []
for slug, name, longitude in (
    ("integration-norte", "Integração Norte", -54.7),
    ("integration-sul", "Integração Sul", -54.5),
):
    region, _ = Region.objects.update_or_create(
        slug=slug,
        defaults={
            "center_point": Point(longitude, -2.4, srid=4326),
            "public_name": name,
            "published_version": 1,
            "short_description": "Região fictícia do teste integrado.",
            "status": EditorialStatus.PUBLISHED,
        },
    )
    Route.objects.update_or_create(
        region=region,
        slug="rota-integrada",
        defaults={
            "difficulty": Route.Difficulty.EASY,
            "duration_minutes": 60,
            "editorial_status": EditorialStatus.PUBLISHED,
            "public_name": f"Rota {name}",
            "short_promise": "Rota fictícia para tráfego HTTP integrado.",
        },
    )
    regions.append(region)

Category.objects.update_or_create(
    slug="apoio-integrado",
    defaults={"is_active": True, "public_name": "Apoio integrado"},
)

User = get_user_model()
administrator, _ = User.objects.update_or_create(
    username="integration_admin",
    defaults={"is_active": True, "is_staff": True},
)
administrator.set_password("integration-only-password")
administrator.save(update_fields=["password"])
group, _ = Group.objects.get_or_create(name=role_group_name(AdminRole.ADMINISTRATOR))
administrator.groups.set([group])

staff, _ = User.objects.update_or_create(
    username="integration_staff",
    defaults={"is_active": True, "is_staff": True},
)
staff.set_password("integration-only-password")
staff.save(update_fields=["password"])

print("fixtures task 7.4 prontas")
