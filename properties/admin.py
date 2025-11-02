# properties/admin.py
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from public_api.models import Banner
from .models import (
    Property, Unit, Listing,
    Amenity, PropertyAmenity, UnitAmenity,
    PropertyImage, UnitImage, PropertyDocument,
    FavoriteListing, VisitRequest, Valuation
)


# =========
# Inlines
# =========

class UnitInline(admin.TabularInline):
    model = Unit
    extra = 0
    fields = ("name", "bedrooms", "bathrooms", "size_m2", "is_available")
    show_change_link = True


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0
    fields = ("image", "caption", "is_primary", "ordering", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px"/>', obj.image.url)
        return "—"


class PropertyDocumentInline(admin.TabularInline):
    model = PropertyDocument
    extra = 0
    fields = ("doc_type", "title", "file", "uploaded_at")
    readonly_fields = ("uploaded_at",)


class PropertyAmenityInline(admin.TabularInline):
    model = PropertyAmenity
    extra = 0
    autocomplete_fields = ("amenity",)
    fields = ("amenity", "value")


# =========
# Property
# =========

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    inlines = [UnitInline, PropertyImageInline, PropertyDocumentInline, PropertyAmenityInline]

    list_display = (
        "title", "property_type", "city", "country",
        "owner", "owner_user", "created_at", "updated_at"
    )
    list_filter = ("property_type", "city", "country", "created_at")
    search_fields = ("title", "address", "city", "owner__full_name", "owner_user__username")
    autocomplete_fields = ("owner", "owner_user")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


# =========
# Unit & UnitImage & UnitAmenity
# =========

class UnitImageInline(admin.TabularInline):
    model = UnitImage
    extra = 0
    fields = ("image", "caption", "ordering", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:6px"/>', obj.image.url)
        return "—"


class UnitAmenityInline(admin.TabularInline):
    model = UnitAmenity
    extra = 0
    autocomplete_fields = ("amenity",)
    fields = ("amenity", "value")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    inlines = [UnitImageInline, UnitAmenityInline]
    list_display = ("__str__", "is_available", "bedrooms", "bathrooms", "size_m2")
    list_filter = ("is_available", "bedrooms", "bathrooms")
    search_fields = ("property__title", "name")
    autocomplete_fields = ("property",)
    ordering = ("property", "name")


# =========
# Listing, Favoris, Visites
# =========

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = (
        "__str__", "listing_type", "price", "currency", "is_active", "is_featured", "published_at", "views_count")
    list_filter = ("listing_type", "is_active", "is_featured", "currency", "published_at")
    search_fields = ("unit__property__title", "unit__name", "description")
    autocomplete_fields = ("unit",)
    ordering = ("-published_at",)
    readonly_fields = ("published_at", "views_count")


@admin.register(FavoriteListing)
class FavoriteListingAdmin(admin.ModelAdmin):
    list_display = ("user", "listing", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "listing__unit__property__title")
    autocomplete_fields = ("user", "listing")
    ordering = ("-created_at",)


@admin.register(VisitRequest)
class VisitRequestAdmin(admin.ModelAdmin):
    list_display = ("listing", "user", "desired_date", "status", "created_at")
    list_filter = ("status", "desired_date", "created_at")
    search_fields = ("user__username", "listing__unit__property__title")
    autocomplete_fields = ("user", "listing")
    ordering = ("-created_at",)


# =========
# Amenity
# =========

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("label", "code", "icon")
    search_fields = ("label", "code", "icon")
    ordering = ("label",)


@admin.register(PropertyAmenity)
class PropertyAmenityAdmin(admin.ModelAdmin):
    list_display = ("property", "amenity", "value")
    search_fields = ("property__title", "amenity__label")
    autocomplete_fields = ("property", "amenity")


@admin.register(UnitAmenity)
class UnitAmenityAdmin(admin.ModelAdmin):
    list_display = ("unit", "amenity", "value")
    search_fields = ("unit__property__title", "amenity__label")
    autocomplete_fields = ("unit", "amenity")


# =========
# Documents & Images
# =========

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("property", "caption", "is_primary", "ordering", "thumb")
    list_filter = ("is_primary",)
    search_fields = ("property__title", "caption")
    autocomplete_fields = ("property",)
    ordering = ("property", "ordering")

    def thumb(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:6px"/>', obj.image.url)
        return "—"

    thumb.short_description = "Aperçu"


@admin.register(UnitImage)
class UnitImageAdmin(admin.ModelAdmin):
    list_display = ("unit", "caption", "ordering", "thumb")
    search_fields = ("unit__property__title", "unit__name", "caption")
    autocomplete_fields = ("unit",)
    ordering = ("unit", "ordering")

    def thumb(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:6px"/>', obj.image.url)
        return "—"

    thumb.short_description = "Aperçu"


@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "property", "doc_type", "uploaded_at")
    list_filter = ("doc_type", "uploaded_at")
    search_fields = ("title", "property__title")
    autocomplete_fields = ("property",)
    ordering = ("-uploaded_at",)


# =========
# Valuation
# =========

@admin.register(Valuation)
class ValuationAdmin(admin.ModelAdmin):
    list_display = ("property", "value", "currency", "valued_at", "valued_by")
    list_filter = ("currency", "valued_at")
    search_fields = ("property__title", "valued_by__username")
    autocomplete_fields = ("property", "valued_by")
    ordering = ("-valued_at",)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    # Liste
    list_display = (
        "title",
        "icon",
        "is_active",
        "is_running",
        "starts_at",
        "ends_at",
        "order",  # <- suppose que OrderedActiveModel fournit 'order'
        "updated_at",  # <- idem: souvent présent (sinon supprime)
    )
    list_editable = ("is_active", "order")  # édition rapide
    list_filter = (
        "is_active",
        ("starts_at", admin.DateFieldListFilter),
        ("ends_at", admin.DateFieldListFilter),
    )
    search_fields = ("title", "subtitle", "cta", "to", "icon")
    ordering = ("order", "-starts_at", "-id")
    date_hierarchy = "starts_at"
    actions = ["activer", "desactiver", "dupliquer"]
    readonly_fields = ("preview_image", "is_running")

    # Formulaire de détail
    fieldsets = (
        ("Contenu", {
            "fields": ("title", "subtitle", "cta", "to", "icon", "image", "preview_image"),
        }),
        ("Planning & statut", {
            "fields": ("is_active", "starts_at", "ends_at", "is_running"),
        }),
        ("Ordre d’affichage", {
            "fields": ("order",),
        }),
    )

    def is_running(self, obj: Banner) -> bool:
        """
        Actif *et* dans la fenêtre temporelle courante.
        """
        if not obj.is_active:
            return False
        now = timezone.now()
        if obj.starts_at and obj.starts_at > now:
            return False
        if obj.ends_at and obj.ends_at < now:
            return False
        return True

    is_running.boolean = True
    is_running.short_description = "Actif maintenant"

    def preview_image(self, obj: Banner):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:420px;max-height:180px;border-radius:8px;object-fit:cover;border:1px solid #eee;" />',
                obj.image,
            )
        return "—"

    preview_image.short_description = "Aperçu"

    # Actions
    def activer(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} bannière(s) activée(s).")

    activer.short_description = "Activer les bannières sélectionnées"

    def desactiver(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} bannière(s) désactivée(s).")

    desactiver.short_description = "Désactiver les bannières sélectionnées"

    def dupliquer(self, request, queryset):
        count = 0
        for b in queryset:
            b.pk = None  # clone
            b.title = f"{b.title} (copie)"
            # option: rendre inactive et pousser en bas de liste
            try:
                # si 'order' existe
                max_order = Banner.objects.aggregate(m=admin.models.functions.Coalesce(
                    admin.models.Max("order"), 0
                ))["m"]
                b.order = (max_order or 0) + 1
            except Exception:
                pass
            b.is_active = False
            b.starts_at = None
            b.ends_at = None
            b.save()
            count += 1
        self.message_user(request, f"{count} bannière(s) dupliquée(s).")

    dupliquer.short_description = "Dupliquer les bannières sélectionnées"
