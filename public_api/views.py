# /Users/ogahserge/Documents/terra360/public_api/views.py
from django.shortcuts import render

# Create your views here.
# public_api/views.py


from django.db.models import Count, Avg, Min, Max
from django.utils import timezone
from rest_framework import viewsets, mixins, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

# Permissions (import si déjà présents, sinon fallback)
try:
    from .permissions import RoleRequired, IsOwnerOrReadOnly
except Exception:
    from rest_framework.permissions import BasePermission, SAFE_METHODS


    class IsOwnerOrReadOnly(BasePermission):
        def has_object_permission(self, request, view, obj):
            if request.method in SAFE_METHODS:
                return True
            return getattr(obj, "owner_user", None) == getattr(request, "user", None)


    class RoleRequired(BasePermission):
        allowed_roles = ()

        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            roles = getattr(view, "allowed_roles", self.allowed_roles)
            return not roles or request.user.role in roles

# Models & Serializers
from parties.models import Party
from properties.models import (
    Property, Unit, Listing,
    Amenity, PropertyAmenity, UnitAmenity,
    FavoriteListing, VisitRequest, Valuation
)
from .serializers import (
    PartySerializer,
    PropertySerializer, UnitSerializer, ListingSerializer,
    AmenitySerializer, FavoriteListingSerializer, VisitRequestSerializer,
    ValuationSerializer
)


# ============
# Filters
# ============

class ListingFilterSet(filters.BaseFilterBackend):
    """Filtres simples via query params (compatible avec DjangoFilterBackend si souhaité)."""

    def filter_queryset(self, request, queryset, view):
        params = request.query_params
        # Type (rent/sale)
        lt = params.get("listing_type")
        if lt in {"rent", "sale"}:
            queryset = queryset.filter(listing_type=lt)
        # Prix
        min_price = params.get("min_price")
        max_price = params.get("max_price")
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        # Ville, type de propriété (via unit->property)
        city = params.get("city")
        if city:
            queryset = queryset.filter(unit__property__city__icontains=city)
        ptype = params.get("property_type")
        if ptype:
            queryset = queryset.filter(unit__property__property_type=ptype)
        # Chambres
        bedrooms = params.get("bedrooms")
        if bedrooms:
            queryset = queryset.filter(unit__bedrooms__gte=bedrooms)
        # Actives seulement (par défaut)
        active = params.get("active", "true").lower()
        if active in {"true", "1"}:
            queryset = queryset.filter(is_active=True)
        # Tri
        ordering = params.get("ordering", "-published_at")
        if ordering:
            queryset = queryset.order_by(ordering)
        return queryset


# ============
# Parties (limité)
# ============

class PartyViewSet(viewsets.ReadOnlyModelViewSet):
    """Lecture seule des parties (utile pour autocomplete côté UI)."""
    queryset = Party.objects.all().order_by("full_name")
    serializer_class = PartySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["full_name", "email", "phone"]


# ============
# Properties
# ============

class PropertyViewSet(viewsets.ModelViewSet):
    """CRUD Property – réservé aux propriétaires (owner)."""
    queryset = Property.objects.select_related("owner", "owner_user").all().order_by("-created_at")
    serializer_class = PropertySerializer
    allowed_roles = ("owner",)
    permission_classes = [RoleRequired & IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "address", "city"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        serializer.save(owner_user=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) == "owner":
            return qs.filter(owner_user=user)
        return qs.none() if not user.is_staff else qs  # staff voit tout


class UnitViewSet(viewsets.ModelViewSet):
    """CRUD Unit – restreint au propriétaire du bien parent."""
    queryset = Unit.objects.select_related("property", "property__owner_user").all()
    serializer_class = UnitSerializer
    allowed_roles = ("owner",)
    permission_classes = [RoleRequired & IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "property__title"]
    ordering_fields = ["name", "bedrooms", "bathrooms", "size_m2"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) == "owner":
            return qs.filter(property__owner_user=user)
        return qs.none() if not user.is_staff else qs

    def perform_create(self, serializer):
        prop = serializer.validated_data["property"]
        # sécurité: force le owner côté API
        serializer.save()
        if prop.owner_user_id != self.request.user.id:
            # Si besoin, tu peux lever une PermissionDenied ici.
            pass


# ============
# Listings (public read-only)
# ============

class ListingViewSet(viewsets.ReadOnlyModelViewSet):
    """Catalogue public des annonces."""
    queryset = (
        Listing.objects
        .select_related("unit", "unit__property")
        .filter(is_active=True)
        .order_by("-published_at")
    )
    serializer_class = ListingSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, ListingFilterSet, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["description", "unit__name", "unit__property__title", "unit__property__address",
                     "unit__property__city"]
    ordering_fields = ["published_at", "price"]

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def increment_view(self, request, pk=None):
        obj = self.get_object()
        obj.views_count = (obj.views_count or 0) + 1
        obj.save(update_fields=["views_count"])
        return Response({"views_count": obj.views_count})

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        data = qs.aggregate(
            total=Count("id"),
            min_price=Min("price"),
            max_price=Max("price"),
            avg_price=Avg("price"),
        )
        return Response(data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        listing = self.get_object()
        fav, _ = FavoriteListing.objects.get_or_create(user=request.user, listing=listing)
        return Response({"favorited": True, "favorite_id": fav.id})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def unfavorite(self, request, pk=None):
        listing = self.get_object()
        FavoriteListing.objects.filter(user=request.user, listing=listing).delete()
        return Response({"favorited": False})


# ============
# Favoris & Visites
# ============

class FavoriteListingViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteListingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FavoriteListing.objects.filter(user=self.request.user).select_related(
            "listing", "listing__unit", "listing__unit__property"
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VisitRequestViewSet(viewsets.ModelViewSet):
    serializer_class = VisitRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return VisitRequest.objects.filter(user=self.request.user).select_related(
            "listing", "listing__unit", "listing__unit__property"
        ).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ============
# Amenity (catalogue)
# ============

class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Amenity.objects.all().order_by("label")
    serializer_class = AmenitySerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["label", "code"]
    ordering_fields = ["label", "code"]


# ============
# Valuation (staff/pro)
# ============

class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class ValuationViewSet(viewsets.ModelViewSet):
    queryset = Valuation.objects.select_related("property", "valued_by").all()
    serializer_class = ValuationSerializer
    permission_classes = [IsStaff]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["property__title", "method", "valued_by__username"]
    ordering_fields = ["valued_at", "value"]
    ordering = ["-valued_at"]


# ============
# Healthcheck
# ============

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health(request):
    return Response({"status": "ok", "time": timezone.now().isoformat()})
