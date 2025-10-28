from rest_framework import viewsets, filters
from .models import MaintenanceTicket
from .serializers import MaintenanceTicketSerializer

class MaintenanceTicketViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceTicket.objects.all().order_by("-id")
    serializer_class = MaintenanceTicketSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["id"]
