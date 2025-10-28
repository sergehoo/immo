from rest_framework import viewsets, filters
from .models import LeaseContract
from .serializers import LeaseContractSerializer

class LeaseContractViewSet(viewsets.ModelViewSet):
    queryset = LeaseContract.objects.all().order_by("-id")
    serializer_class = LeaseContractSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["id"]
