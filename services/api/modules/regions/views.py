from drf_spectacular.utils import extend_schema
from rest_framework import generics

from modules.core.models import EditorialStatus

from .models import Region
from .serializers import RegionSummarySerializer


class RegionListView(generics.ListAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = RegionSummarySerializer
    queryset = Region.objects.filter(status=EditorialStatus.PUBLISHED)

    @extend_schema(
        operation_id="listPublishedRegions",
        summary="Listar regiões publicadas",
        description="Retorna somente regiões disponíveis para navegação pública.",
        tags=["Regions"],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
