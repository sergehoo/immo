# public_api/serializers.py
from __future__ import annotations
from rest_framework import serializers

# Parties
from parties.models import (
    Party, PartyRole, PartyAddress, PartyContact, PartyRelationship,
    PartyAttachment, PartyTag, PartyNote
)

# Properties
from properties.models import (
    Property, Unit, Listing, Amenity, PropertyAmenity, UnitAmenity,
    PropertyImage, UnitImage, PropertyDocument,
    FavoriteListing, VisitRequest, Valuation
)
from public_api.models import Banner, QuickAction, Category, MapTeaser


# =============== Parties ===============

class PartyRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyRole
        fields = "__all__"


class PartySerializer(serializers.ModelSerializer):
    roles = PartyRoleSerializer(many=True, read_only=True)

    class Meta:
        model = Party
        fields = [
            "id", "type", "full_name", "email", "phone",
            "is_landlord", "is_tenant", "is_agent",
            "roles", "user", "company", "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


# =============== Properties ===============

class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = "__all__"


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ["id", "image", "caption", "is_primary", "ordering"]


class UnitImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitImage
        fields = ["id", "image", "caption", "ordering"]


class PropertyDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyDocument
        fields = ["id", "doc_type", "title", "file", "uploaded_at"]


class PropertySerializer(serializers.ModelSerializer):
    images = PropertyImageSerializer(many=True, read_only=True)
    documents = PropertyDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = [
            "id", "title", "property_type", "address", "city", "country", "geom",
            "owner", "owner_user", "images", "documents",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class UnitSerializer(serializers.ModelSerializer):
    images = UnitImageSerializer(many=True, read_only=True)
    property = serializers.PrimaryKeyRelatedField(queryset=Property.objects.all())

    class Meta:
        model = Unit
        fields = [
            "id", "property", "name", "bedrooms", "bathrooms", "size_m2",
            "is_available", "images",
        ]


class ListingSerializer(serializers.ModelSerializer):
    unit = UnitSerializer(read_only=True)
    property_city = serializers.CharField(source="unit.property.city", read_only=True)
    property_district = serializers.CharField(source="unit.property.address",
                                              read_only=True)  # à adapter si tu as district
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = (
            "id", "listing_type", "price", "currency", "description",
            "is_active", "is_featured", "available_from", "published_at",
            "views_count", "unit", "property_city", "property_district",
            "cover_image",
        )

    def get_cover_image(self, obj):
        # si tu as PropertyImage ou UnitImage, renvoie la première, sinon None
        img = getattr(obj.unit, "images", None)
        if img and img.exists():
            return img.first().image.url
        return None


class FavoriteListingSerializer(serializers.ModelSerializer):
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(
        source="listing", queryset=Listing.objects.all(), write_only=True
    )

    class Meta:
        model = FavoriteListing
        fields = ["id", "listing", "listing_id", "created_at"]
        read_only_fields = ["created_at"]


class VisitRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitRequest
        fields = ["id", "user", "listing", "desired_date", "status", "notes", "created_at"]
        read_only_fields = ["created_at", "user", "status"]


# class HomeSerializer(serializers.Serializer):
#     banners = serializers.ListField(child=serializers.DictField(), allow_empty=True)
#     quick_actions = serializers.ListField(child=serializers.DictField(), allow_empty=True)
#     districts = serializers.ListField(child=serializers.DictField(), allow_empty=True)
#     categories = serializers.ListField(child=serializers.DictField(), allow_empty=True)
#     map_teaser = serializers.DictField(allow_null=True)

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ("id", "title", "subtitle", "cta", "to", "icon", "image")


class QuickActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuickAction
        fields = ("id", "icon", "label", "to", "gradient", "color")


class CategorySerializer(serializers.ModelSerializer):
    # on renvoie id = slug pour coller aux filtres du front (rent/sell/featured/new/all)
    id = serializers.CharField(source="slug")

    class Meta:
        model = Category
        fields = ("id", "label", "icon", "color")


class MapTeaserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapTeaser
        fields = ("image", "title", "subtitle", "to")


class SummarySerializer(serializers.Serializer):
    favorites_count = serializers.IntegerField()
    visit_requests_count = serializers.IntegerField()


class ValuationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Valuation
        fields = ["id", "property", "valued_by", "method", "value", "currency", "valued_at", "notes"]
