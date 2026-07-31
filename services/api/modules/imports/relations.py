from django.db.models import Q

from modules.accounts.permissions import AdminRole, get_user_roles
from modules.catalog.models import Actor, Category
from modules.regions.models import Region
from modules.routes.models import Route

from .catalog_csv import CatalogRelationIndex


def catalog_relation_index_for(user) -> CatalogRelationIndex:
    if AdminRole.ADMINISTRATOR in get_user_roles(user):
        region_slugs = set(Region.objects.values_list("slug", flat=True))
    else:
        region_slugs = set(
            user.administrative_region_scopes.filter(is_active=True).values_list(
                "region__slug", flat=True
            )
        )
    category_slugs = frozenset(Category.objects.values_list("slug", flat=True))
    route_keys = frozenset(
        Route.objects.filter(region__slug__in=region_slugs).values_list("region__slug", "slug")
    )
    all_actor_external_ids = frozenset(Actor.objects.values_list("external_id", flat=True))
    actor_external_ids = frozenset(
        Actor.objects.filter(
            Q(locations__region__slug__in=region_slugs)
            | Q(route_links__route__region__slug__in=region_slugs)
        )
        .distinct()
        .values_list("external_id", flat=True)
    )
    return CatalogRelationIndex(
        frozenset(region_slugs),
        category_slugs,
        route_keys,
        actor_external_ids,
        all_actor_external_ids - actor_external_ids,
    )
