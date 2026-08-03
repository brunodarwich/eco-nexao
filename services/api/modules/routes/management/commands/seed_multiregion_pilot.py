"""Seed demonstrativo para o piloto multirregional — Tarefa 12.

Cria quatro rotas adicionais distribuídas em duas regiões, elevando o total
a cinco rotas publicáveis na plataforma.  Também cria uma região não pública
(status=DRAFT) que valida o isolamento sem alteração de código.

Uso:
    python manage.py seed_multiregion_pilot --publish-demo
    python manage.py seed_multiregion_pilot  # apenas rascunhos (padrão)

_Requisitos: RF-01, RF-02, RNF-06_
"""

from decimal import Decimal

from django.contrib.gis.geos import LineString, Point
from django.core.management.base import BaseCommand
from django.db import transaction

from modules.core.models import EditorialStatus
from modules.regions.models import Region
from modules.routes.models import Route, RouteSegment, RouteStage


class Command(BaseCommand):
    help = (
        "Cria quatro rotas adicionais e uma região não pública para validar "
        "o modelo multirregional do MVP ECOnexão."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--publish-demo",
            action="store_true",
            help="Publica as rotas e a segunda região no ambiente de desenvolvimento.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        pub = EditorialStatus.PUBLISHED if options["publish_demo"] else EditorialStatus.DRAFT

        # ── Região 1 (já criada pelo seed de Pindobal) ──────────────────────────
        # Apenas referenciamos para adicionar mais rotas; não recriamos a região.
        existing_region = Region.objects.filter(slug="santarem-alter-do-chao").first()
        region_defaults = {
            "public_name": "Santarém e Alter do Chão",
            "short_description": (
                "Território demonstrativo para validar a experiência multirregional."
            ),
            "center_point": Point(-54.97478, -2.55997, srid=4326),
            "timezone": "America/Fortaleza",
        }
        if not existing_region or not options["publish_demo"]:
            if not existing_region or existing_region.status != EditorialStatus.PUBLISHED:
                region_defaults["status"] = pub
                region_defaults["published_version"] = 1 if options["publish_demo"] else None

        region_tapajos, _ = Region.objects.update_or_create(
            slug="santarem-alter-do-chao",
            defaults=region_defaults,
        )

        # ── Rota 2: Orla de Alter do Chão (região 1) ───────────────────────────
        self._seed_route(
            region=region_tapajos,
            slug="orla-alter-do-chao",
            name="Orla e Praia Verde de Alter do Chão",
            promise="Caminhada à beira do Tapajós com banho nas águas cristalinas.",
            description=(
                "Roteiro demonstrativo pela Orla de Alter do Chão.  "
                "Inclui praia fluvial, mirante e feira artesanal.  "
                "Conteúdo em fase de verificação humana."
            ),
            duration=180,
            difficulty=Route.Difficulty.EASY,
            cost_min=Decimal("0.00"),
            cost_max=Decimal("60.00"),
            modes=["walk"],
            prep=(
                "Melhor visitada no período seco (agosto–novembro).  "
                "Leve protetor solar, água e repelente."
            ),
            a11y=(
                "Parte da orla tem calçamento irregular.  "
                "Confirme acesso para cadeiras de rodas com fontes locais."
            ),
            stages=[
                (1, "Feira de Artesanato", -54.95133, -2.52131, RouteStage.StageType.START, 30),
                (
                    2,
                    "Praia da Ponta do Cururu",
                    -54.95300,
                    -2.52050,
                    RouteStage.StageType.EXPERIENCE,
                    120,
                ),
                (3, "Mirante do Rio Tapajós", -54.95500, -2.52200, RouteStage.StageType.END, 30),
            ],
            pub_status=pub,
        )

        # ── Rota 3: Lago Verde (região 1) ──────────────────────────────────────
        self._seed_route(
            region=region_tapajos,
            slug="lago-verde",
            name="Lago Verde e Flutuante de Canoas",
            promise="Travessia de canoa pelo espelho d'água cercado de floresta.",
            description=(
                "Roteiro demonstrativo de canoagem pelo Lago Verde.  "
                "Ponto de observação de aves e macrofauna aquática.  "
                "Conteúdo em fase de verificação."
            ),
            duration=120,
            difficulty=Route.Difficulty.EASY,
            cost_min=Decimal("30.00"),
            cost_max=Decimal("80.00"),
            modes=["boat", "walk"],
            prep=(
                "Reserve canoa com antecedência.  "
                "Evite horários de chuva intensa.  "
                "Coletes salva-vidas são obrigatórios."
            ),
            a11y=(
                "Acesso ao embarcadouro pode ser íngreme.  "
                "Confirme disponibilidade de canoa adaptada."
            ),
            stages=[
                (
                    1,
                    "Embarcadouro de Alter do Chão",
                    -54.95100,
                    -2.52200,
                    RouteStage.StageType.START,
                    10,
                ),
                (
                    2,
                    "Centro do Lago Verde",
                    -54.94800,
                    -2.52500,
                    RouteStage.StageType.EXPERIENCE,
                    90,
                ),
                (
                    3,
                    "Retorno ao embarcadouro",
                    -54.95100,
                    -2.52200,
                    RouteStage.StageType.END,
                    10,
                ),
            ],
            pub_status=pub,
        )

        # ── Região 2: Tapajós Leste (nova região pública) ──────────────────────
        existing_leste = Region.objects.filter(slug="tapajos-leste").first()
        leste_defaults = {
            "public_name": "Tapajós Leste",
            "short_description": (
                "Segunda região demonstrativa para validar o isolamento multirregional."
            ),
            "center_point": Point(-54.70000, -2.43000, srid=4326),
            "timezone": "America/Fortaleza",
        }
        if not existing_leste or existing_leste.status != EditorialStatus.PUBLISHED:
            leste_defaults["status"] = pub
            leste_defaults["published_version"] = 1 if options["publish_demo"] else None

        region_leste, _ = Region.objects.update_or_create(
            slug="tapajos-leste",
            defaults=leste_defaults,
        )

        # ── Rota 4: Floresta Tapajônica (região 2) ─────────────────────────────
        self._seed_route(
            region=region_leste,
            slug="floresta-tapajonica",
            name="Trilha da Floresta Tapajônica",
            promise="Imersão na floresta de terra firme com guia local.",
            description=(
                "Trilha demonstrativa de 6 km em floresta densa.  "
                "Observação de fauna e flora com guia habilitado.  "
                "Conteúdo em fase de verificação."
            ),
            duration=300,
            difficulty=Route.Difficulty.MODERATE,
            cost_min=Decimal("80.00"),
            cost_max=Decimal("200.00"),
            modes=["walk"],
            prep=(
                "Obrigatório contratar guia local certificado.  "
                "Botas de borracha e calça comprida recomendadas.  "
                "Trilha disponível somente no período seco."
            ),
            a11y=("Trilha em terreno irregular — não recomendada para mobilidade reduzida."),
            stages=[
                (
                    1,
                    "Portão de entrada da reserva",
                    -54.70000,
                    -2.43000,
                    RouteStage.StageType.START,
                    15,
                ),
                (
                    2,
                    "Clareira do Juçara",
                    -54.69500,
                    -2.43500,
                    RouteStage.StageType.EXPERIENCE,
                    120,
                ),
                (
                    3,
                    "Mirante da copa das árvores",
                    -54.69000,
                    -2.44000,
                    RouteStage.StageType.EXPERIENCE,
                    60,
                ),
                (4, "Retorno ao portão", -54.70000, -2.43000, RouteStage.StageType.END, 15),
            ],
            pub_status=pub,
        )

        # ── Rota 5: Encontro das Águas (região 2) ──────────────────────────────
        self._seed_route(
            region=region_leste,
            slug="encontro-das-aguas",
            name="Encontro das Águas do Tapajós",
            promise="Passeio de barco para o encontro entre rios de cores distintas.",
            description=(
                "Roteiro demonstrativo de observação do encontro das águas.  "
                "O contraste de coloração entre afluentes é um fenômeno natural.  "
                "Conteúdo em fase de verificação."
            ),
            duration=240,
            difficulty=Route.Difficulty.EASY,
            cost_min=Decimal("60.00"),
            cost_max=Decimal("150.00"),
            modes=["boat"],
            prep=("Recomendado entre junho e novembro.  Leve proteção solar e câmera fotográfica."),
            a11y="Embarcações turísticas com acesso assistido disponíveis sob consulta.",
            stages=[
                (1, "Porto de embarque", -54.71000, -2.42000, RouteStage.StageType.START, 20),
                (
                    2,
                    "Ponto de encontro das águas",
                    -54.72000,
                    -2.41000,
                    RouteStage.StageType.EXPERIENCE,
                    90,
                ),
                (
                    3,
                    "Parada na prainha fluvial",
                    -54.71500,
                    -2.40500,
                    RouteStage.StageType.STOP,
                    60,
                ),
                (4, "Retorno ao porto", -54.71000, -2.42000, RouteStage.StageType.END, 20),
            ],
            pub_status=pub,
        )

        # ── Região 3: Região Piloto (não pública — Tarefa 12.2) ────────────────
        # status=DRAFT garante que a API pública retorna queryset vazio (404)
        # sem nenhuma alteração de código de domínio.
        Region.objects.update_or_create(
            slug="regiao-piloto-interno",
            defaults={
                "public_name": "Região Piloto Interno",
                "short_description": (
                    "Região de testes internos — nunca publicada para o público.  "
                    "Valida o isolamento sem alteração de código."
                ),
                "center_point": Point(-54.50000, -2.50000, srid=4326),
                "timezone": "America/Fortaleza",
                "status": EditorialStatus.DRAFT,
                "published_version": None,
            },
        )

        state = "publicados" if options["publish_demo"] else "criados como rascunho"
        self.stdout.write(
            self.style.SUCCESS(
                f"Piloto multirregional {state}: 4 rotas adicionais (2 regiões públicas) "
                "e 1 região não pública de teste."
            )
        )

    # ─────────────────────────────────────────────────────────────────────────
    def _seed_route(
        self,
        *,
        region: Region,
        slug: str,
        name: str,
        promise: str,
        description: str,
        duration: int,
        difficulty: str,
        cost_min: Decimal,
        cost_max: Decimal,
        modes: list,
        prep: str,
        a11y: str,
        stages: list[tuple],
        pub_status: str,
    ) -> Route:
        existing_route = Route.objects.filter(region=region, slug=slug).first()
        route_defaults = {
            "public_name": name,
            "short_promise": promise,
            "description": description,
            "duration_minutes": duration,
            "difficulty": difficulty,
            "estimated_cost_min": cost_min,
            "estimated_cost_max": cost_max,
            "transport_modes": modes,
            "preparation_content": prep,
            "accessibility_content": a11y,
            "offline_enabled": True,
        }
        if not existing_route or existing_route.editorial_status != EditorialStatus.PUBLISHED:
            route_defaults["editorial_status"] = pub_status

        route, _ = Route.objects.update_or_create(
            region=region,
            slug=slug,
            defaults=route_defaults,
        )

        stage_objs: list[RouteStage] = []
        for position, stage_name, lon, lat, stage_type, duration_min in stages:
            stage_obj, _ = RouteStage.objects.update_or_create(
                route=route,
                position=position,
                defaults={
                    "public_name": stage_name,
                    "description": f"Ponto demonstrativo — {stage_name}.",
                    "point": Point(lon, lat, srid=4326),
                    "arrival_guidance": "Valide a orientação com fonte local.",
                    "duration_minutes": duration_min,
                    "stage_type": stage_type,
                    "is_optional": False,
                },
            )
            stage_objs.append(stage_obj)

        for start, end in zip(stage_objs, stage_objs[1:], strict=False):
            RouteSegment.objects.update_or_create(
                route=route,
                from_stage=start,
                to_stage=end,
                defaults={
                    "geometry": LineString(start.point, end.point, srid=4326),
                    "transport_mode": modes[0],
                    "distance_meters": 500,
                    "duration_minutes": 15,
                    "instructions": "Trecho demonstrativo; valide o percurso no local.",
                },
            )

        return route
