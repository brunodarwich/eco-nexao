from django.urls import path

from .views import RegionRouteListView, RouteCatalogListView, RouteDetailView

urlpatterns = [
    path(
        "regions/<slug:region_slug>/routes",
        RegionRouteListView.as_view(),
        name="region-route-list",
    ),
    path(
        "regions/<slug:region_slug>/routes/<slug:route_slug>",
        RouteDetailView.as_view(),
        name="route-detail",
    ),
    path(
        "regions/<slug:region_slug>/routes/<slug:route_slug>/catalog",
        RouteCatalogListView.as_view(),
        name="route-catalog",
    ),
]
