# parties/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    PartyRole, Party, PartyAddress, PartyContact, PartyRelationship,
    PartyAttachment, PartyTag, PartyNote
)


# =========
# Inlines
# =========

class PartyAddressInline(admin.TabularInline):
    model = PartyAddress
    extra = 0
    autocomplete_fields = ("address",)
    fields = ("address", "address_type", "is_primary", "created_at")
    readonly_fields = ("created_at",)


class PartyContactInline(admin.TabularInline):
    model = PartyContact
    extra = 0
    fields = ("type", "label", "email", "phone", "value", "created_at")
    readonly_fields = ("created_at",)


class PartyAttachmentInline(admin.TabularInline):
    model = PartyAttachment
    extra = 0
    fields = ("title", "file", "size_bytes", "mime_type", "created_at")
    readonly_fields = ("created_at", "size_bytes", "mime_type")


class PartyNoteInline(admin.StackedInline):
    model = PartyNote
    extra = 0
    autocomplete_fields = ("author", "tags")
    fields = ("author", "content", "is_pinned", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


# =========
# Party
# =========

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    inlines = [PartyAddressInline, PartyContactInline, PartyAttachmentInline, PartyNoteInline]

    list_display = (
        "full_name", "type", "email", "phone",
        "roles_list", "user", "company",
        "created_at", "updated_at",
    )
    list_filter = ("type", "roles", "created_at", "updated_at", "is_landlord", "is_tenant", "is_agent")
    search_fields = ("full_name", "email", "phone", "user__username", "company__name")
    autocomplete_fields = ("user", "company")
    filter_horizontal = ("roles",)
    ordering = ("-created_at",)
    list_select_related = ("user", "company")

    fieldsets = (
        (None, {"fields": ("type", "full_name")}),
        (_("Liens"), {"fields": ("user", "company")}),
        (_("Contact"), {"fields": ("email", "phone")}),
        (_("Rôles"), {"fields": ("roles",)}),
        (_("Compatibilité (legacy)"), {"fields": ("is_landlord", "is_tenant", "is_agent")}),
        (_("Dates"), {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Rôles")
    def roles_list(self, obj):
        return ", ".join(r.label for r in obj.roles.all()) or "—"


# =========
# PartyRole
# =========

@admin.register(PartyRole)
class PartyRoleAdmin(admin.ModelAdmin):
    list_display = ("label", "code")
    search_fields = ("label", "code")
    ordering = ("label",)


# =================
# PartyRelationship
# =================

@admin.register(PartyRelationship)
class PartyRelationshipAdmin(admin.ModelAdmin):
    list_display = ("from_party", "relation_type", "to_party", "created_at")
    list_filter = ("relation_type", "created_at")
    search_fields = ("from_party__full_name", "to_party__full_name")
    autocomplete_fields = ("from_party", "to_party")
    ordering = ("-created_at",)


# =========
# PartyTag
# =========

@admin.register(PartyTag)
class PartyTagAdmin(admin.ModelAdmin):
    list_display = ("label", "code")
    search_fields = ("label", "code")
    ordering = ("label",)


# =========
# PartyAttachment
# =========

@admin.register(PartyAttachment)
class PartyAttachmentAdmin(admin.ModelAdmin):
    list_display = ("title", "party", "file_link", "size_bytes", "mime_type", "created_at")
    list_filter = ("mime_type", "created_at")
    search_fields = ("title", "party__full_name")
    autocomplete_fields = ("party",)
    ordering = ("-created_at",)

    @admin.display(description="Fichier")
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Télécharger</a>', obj.file.url)
        return "—"


# =========
# PartyAddress
# =========

@admin.register(PartyAddress)
class PartyAddressAdmin(admin.ModelAdmin):
    list_display = ("party", "address", "address_type", "is_primary", "created_at")
    list_filter = ("address_type", "is_primary", "created_at")
    search_fields = ("party__full_name", "address__line1", "address__city")
    autocomplete_fields = ("party", "address")
    ordering = ("-created_at",)


# =========
# PartyContact
# =========

@admin.register(PartyContact)
class PartyContactAdmin(admin.ModelAdmin):
    list_display = ("party", "type", "label", "email", "phone", "value", "created_at")
    list_filter = ("type", "created_at")
    search_fields = ("party__full_name", "email", "phone", "label")
    autocomplete_fields = ("party",)
    ordering = ("-created_at",)


# =========
# PartyNote
# =========

@admin.action(description="Épingler les notes sélectionnées")
def pin_notes(modeladmin, request, queryset):
    queryset.update(is_pinned=True)


@admin.action(description="Désépingler les notes sélectionnées")
def unpin_notes(modeladmin, request, queryset):
    queryset.update(is_pinned=False)


@admin.register(PartyNote)
class PartyNoteAdmin(admin.ModelAdmin):
    list_display = ("party", "author", "short_content", "is_pinned", "created_at", "updated_at")
    list_filter = ("is_pinned", "created_at")
    search_fields = ("party__full_name", "author__username", "content")
    autocomplete_fields = ("party", "author", "tags")
    actions = [pin_notes, unpin_notes]
    ordering = ("-created_at",)

    @admin.display(description="Extrait")
    def short_content(self, obj):
        return (obj.content[:80] + "…") if len(obj.content) > 80 else obj.content
