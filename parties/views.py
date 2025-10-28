from rest_framework import viewsets, filters
from .models import Party
from .serializers import PartySerializer

class PartyViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all().order_by("-id")
    serializer_class = PartySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["id"]
