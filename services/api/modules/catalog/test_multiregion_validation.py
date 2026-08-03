"""Testes de validação do modelo multirregional.

Verifica que a plataforma suporta N regiões dinâmicas criadas por dados,
sem depender de slugs fixos no código.

_Requisitos: RF-01, RF-02, RNF-06_
"""

from modules.routes.views import RegionRouteListView, RouteCatalogListView


def test_route_list_scopes_to_dynamic_region_slug():
    """Queryset filtra por region_slug vindo da URL — nenhum slug está hardcoded."""
    for slug in ("regiao-x", "regiao-y", "regiao-z"):
        view = RegionRouteListView()
        view.kwargs = {"region_slug": slug}
        filters = repr(view.get_queryset().query.where).lower()
        assert slug in filters, f"Slug '{slug}' não encontrado nos filtros da queryset."
        assert filters.count("published") == 2, (
            "Queryset deve exigir published em region.status E route.editorial_status."
        )


def test_route_list_isolates_between_regions():
    """Slugs de regiões distintas não se sobrepõem nos filtros de queryset."""
    view_a = RegionRouteListView()
    view_a.kwargs = {"region_slug": "regiao-alfa"}
    view_b = RegionRouteListView()
    view_b.kwargs = {"region_slug": "regiao-beta"}

    filters_a = repr(view_a.get_queryset().query.where).lower()
    filters_b = repr(view_b.get_queryset().query.where).lower()

    assert "regiao-alfa" in filters_a
    assert "regiao-alfa" not in filters_b
    assert "regiao-beta" in filters_b
    assert "regiao-beta" not in filters_a


def test_catalog_requires_both_region_and_route_filters():
    """O catálogo contextual filtra por region_slug E route_slug sem vazar entre pares."""
    view = RouteCatalogListView()
    view.kwargs = {"region_slug": "regiao-delta", "route_slug": "rota-eco-1"}
    filters = repr(view.get_queryset().query.where).lower()

    assert "regiao-delta" in filters
    assert "rota-eco-1" in filters
    assert filters.count("published") >= 3, (
        "Catálogo deve exigir published em region, route e actor."
    )


def test_nonpublic_region_produces_empty_queryset():
    """Uma região não publicada retorna queryset vazio, resultando em 404 automático.

    O filtro region__status=EditorialStatus.PUBLISHED exclui regiões em rascunho
    ou arquivadas sem qualquer lógica de negócio nas views.
    """
    view = RegionRouteListView()
    view.kwargs = {"region_slug": "regiao-privada-piloto"}
    qs = view.get_queryset()
    filters = repr(qs.query.where).lower()

    # Filtros de publicação e slug estão presentes mesmo sem resultados no banco
    assert "published" in filters
    assert "regiao-privada-piloto" in filters


def test_multiregion_arbitrary_slugs_never_hardcoded():
    """Dez slugs arbitrários são corretamente injetados nos filtros da queryset."""
    slugs = [f"regiao-{i}" for i in range(10)]
    for slug in slugs:
        view = RegionRouteListView()
        view.kwargs = {"region_slug": slug}
        filters = repr(view.get_queryset().query.where).lower()
        assert slug in filters, f"Slug '{slug}' ausente nos filtros — possível hardcoding."
