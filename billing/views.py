from rest_framework import viewsets, filters
from .models import RentInvoice
from .serializers import RentInvoiceSerializer


class RentInvoiceViewSet(viewsets.ModelViewSet):
    queryset = RentInvoice.objects.all().order_by("-id")
    serializer_class = RentInvoiceSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["id"]
