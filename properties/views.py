from rest_framework import viewsets, filters
from .models import Property
from .serializers import PropertySerializer

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all().order_by("-id")
    serializer_class = PropertySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["id"]

from rest_framework import viewsets, filters
from .models import Unit
from .serializers import UnitSerializer

class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all().order_by("-id")
    serializer_class = UnitSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["id"]

from rest_framework import viewsets, filters
from .models import Listing
from .serializers import ListingSerializer

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all().order_by("-id")
    serializer_class = ListingSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["id"]
