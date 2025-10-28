# properties/models.py
from __future__ import annotations

from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.gis.db import models  # GeoDjango fields inclus

# =======================
# Core : Property / Unit / Listing
# =======================

class Property(models.Model):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    LAND = "land"
    TYPES = [(RESIDENTIAL, "Résidentiel"), (COMMERCIAL, "Commercial"), (LAND, "Terrain")]

    title = models.CharField(max_length=255)
    property_type = models.CharField(max_length=32, choices=TYPES)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=120, blank=True, null=True)
    country = models.CharField(max_length=120, default="Côte d'Ivoire")
    geom = models.PointField(geography=True, null=True, blank=True)

    owner = models.ForeignKey("parties.Party", on_delete=models.SET_NULL, null=True, blank=True, related_name="owned_properties")
    owner_user = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="user_owned_properties")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["property_type"]),
            models.Index(fields=["city"]),
        ]

    def __str__(self):
        return self.title


class Unit(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="units")
    name = models.CharField(max_length=120)
    bedrooms = models.IntegerField(default=0)
    bathrooms = models.IntegerField(default=0)
    size_m2 = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ("property", "name")
        indexes = [
            models.Index(fields=["is_available"]),
            models.Index(fields=["bedrooms", "bathrooms"]),
        ]

    def __str__(self):
        return f"{self.property} - {self.name}"


class Listing(models.Model):
    RENT = "rent"
    SALE = "sale"
    LISTING_TYPES = [(RENT, "Location"), (SALE, "Vente")]

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="listings")
    listing_type = models.CharField(max_length=16, choices=LISTING_TYPES)
    price = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=8, default="XOF")
    description = models.TextField(blank=True, null=True)

    # Options d’annonces
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    available_from = models.DateField(null=True, blank=True)
    published_at = models.DateTimeField(auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["listing_type"]),
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["published_at"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return f"{self.unit} - {self.listing_type}"


# =======================
# Catalogue d'équipements / services
# =======================

class Amenity(models.Model):
    code = models.SlugField(max_length=40, unique=True)
    label = models.CharField(max_length=120)
    icon = models.CharField(max_length=40, blank=True, help_text="Nom d’icône (libre)")

    class Meta:
        verbose_name = "Équipement"
        verbose_name_plural = "Équipements"
        ordering = ["label"]

    def __str__(self):
        return self.label


class PropertyAmenity(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="property_amenities")
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name="properties")
    value = models.CharField(max_length=120, blank=True, help_text="Ex.: 24/7, nbre places, etc.")

    class Meta:
        unique_together = ("property", "amenity")
        verbose_name = "Équipement de bien"
        verbose_name_plural = "Équipements de bien"

    def __str__(self):
        return f"{self.property} – {self.amenity}"


class UnitAmenity(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="unit_amenities")
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name="units")
    value = models.CharField(max_length=120, blank=True)

    class Meta:
        unique_together = ("unit", "amenity")
        verbose_name = "Équipement d’unité"
        verbose_name_plural = "Équipements d’unité"

    def __str__(self):
        return f"{self.unit} – {self.amenity}"


# =======================
# Médias & documents
# =======================

def property_image_upload_to(instance: "PropertyImage", filename: str) -> str:
    import uuid
    return f"properties/{instance.property_id}/images/{uuid.uuid4()}-{filename}"

def unit_image_upload_to(instance: "UnitImage", filename: str) -> str:
    import uuid
    return f"properties/{instance.unit.property_id}/units/{instance.unit_id}/images/{uuid.uuid4()}-{filename}"

def property_doc_upload_to(instance: "PropertyDocument", filename: str) -> str:
    import uuid
    return f"properties/{instance.property_id}/docs/{uuid.uuid4()}-{filename}"


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=property_image_upload_to)
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering", "id"]
        indexes = [models.Index(fields=["is_primary"])]

    def __str__(self):
        return f"Photo {self.property} ({'★' if self.is_primary else ''})"


class UnitImage(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=unit_image_upload_to)
    caption = models.CharField(max_length=200, blank=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering", "id"]

    def __str__(self):
        return f"Photo {self.unit}"


class PropertyDocument(models.Model):
    PLAN = "plan"
    TITLE = "title"
    OTHER = "other"
    TYPES = [(PLAN, "Plan"), (TITLE, "Titre/Attestation"), (OTHER, "Autre")]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=16, choices=TYPES, default=OTHER)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=property_doc_upload_to)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title} ({self.property})"


# =======================
# Favoris & Visites
# =======================

class FavoriteListing(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "listing")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} ❤ {self.listing_id}"


class VisitRequest(models.Model):
    NEW = "new"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    STATUSES = [
        (NEW, "Nouveau"),
        (CONFIRMED, "Confirmé"),
        (COMPLETED, "Réalisé"),
        (CANCELLED, "Annulé"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="visit_requests")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="visit_requests")
    desired_date = models.DateTimeField()
    status = models.CharField(max_length=16, choices=STATUSES, default=NEW)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["status", "desired_date"])]

    def __str__(self):
        return f"Visite {self.listing_id} par {self.user} ({self.status})"


# =======================
# Évaluations / Estimations
# =======================

class Valuation(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="valuations")
    valued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    method = models.CharField(max_length=120, blank=True, help_text="Méthode/Cf document")
    value = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=8, default="XOF")
    valued_at = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-valued_at"]
        indexes = [models.Index(fields=["valued_at", "value"])]

    def __str__(self):
        return f"Estimation {self.value} {self.currency} ({self.valued_at}) – {self.property}"