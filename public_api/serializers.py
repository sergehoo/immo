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
    unit_id = serializers.PrimaryKeyRelatedField(
        source="unit", queryset=Unit.objects.select_related("property"), write_only=True
    )

    class Meta:
        model = Listing
        fields = [
            "id", "unit", "unit_id", "listing_type", "price", "currency",
            "description", "is_active", "is_featured", "available_from",
            "published_at", "views_count",
        ]
        read_only_fields = ["published_at", "views_count"]


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


class ValuationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Valuation
        fields = ["id", "property", "valued_by", "method", "value", "currency", "valued_at", "notes"]