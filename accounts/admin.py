# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    User, Address, UserProfile, Company, CompanyMembership,
    KYCDocument, BankAccount, NotificationPreference, ScoutReferral
)

admin.site.site_header = "Terra360 – Administration"
admin.site.site_title = "Terra360 Admin"
admin.site.index_title = "Gestion du patrimoine foncier & immobilier"
# ==============================
# Inlines (utiles & ergonomiques)
# ==============================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    readonly_fields = ("avatar_preview",)

    @admin.display(description="Aperçu avatar")
    def avatar_preview(self, obj):
        if obj and obj.avatar:
            return format_html('<img src="{}" style="height:60px;border-radius:8px"/>', obj.avatar.url)
        return "—"


class NotificationPreferenceInline(admin.StackedInline):
    model = NotificationPreference
    can_delete = False
    extra = 0


class CompanyMembershipInline(admin.TabularInline):
    model = CompanyMembership
    extra = 0
    autocomplete_fields = ("user",)


# =================================
# UserAdmin (custom user + inlines)
# =================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline, NotificationPreferenceInline, CompanyMembershipInline]

    # champs affichés en liste
    list_display = (
        "username", "email", "first_name", "last_name",
        "role", "phone", "is_active", "is_staff", "date_joined",
    )
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name", "phone")
    ordering = ("-date_joined",)

    # fieldsets adaptés à ton modèle
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Informations personnelles"), {"fields": ("first_name", "last_name", "email", "phone", "role", "company_name")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Vérifications"), {"fields": ("is_email_verified", "is_phone_verified")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "role", "phone", "company_name", "is_staff", "is_active"),
        }),
    )


# =========
# Address
# =========

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("label", "line1", "city", "country", "postal_code", "latitude", "longitude", "created_at")
    list_filter = ("country",)
    search_fields = ("label", "line1", "city", "state", "postal_code")
    ordering = ("-created_at",)


# =========
# Company
# =========

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    inlines = [CompanyMembershipInline]
    list_display = ("name", "company_type", "email", "phone", "is_active", "rc_number", "tax_number", "created_at")
    list_filter = ("company_type", "is_active", "created_at")
    search_fields = ("name", "email", "phone", "rc_number", "tax_number")
    autocomplete_fields = ("address",)
    readonly_fields = ("logo_preview",)

    @admin.display(description="Logo")
    def logo_preview(self, obj):
        if obj and obj.logo:
            return format_html('<img src="{}" style="height:60px;border-radius:8px"/>', obj.logo.url)
        return "—"

    fieldsets = (
        (None, {"fields": ("name", "company_type", "is_active")}),
        (_("Coordonnées"), {"fields": ("email", "phone", "address", "website")}),
        (_("Identifiants"), {"fields": ("rc_number", "tax_number")}),
        (_("Branding"), {"fields": ("logo", "logo_preview")}),
        (_("Meta"), {"fields": ("created_at", "updated_at")}),
    )
    readonly_fields = (*readonly_fields, "created_at", "updated_at")


# =================
# CompanyMembership
# =================

@admin.register(CompanyMembership)
class CompanyMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "role", "is_primary", "created_at")
    list_filter = ("role", "is_primary", "created_at")
    search_fields = ("user__username", "user__email", "company__name")
    autocomplete_fields = ("user", "company")
    ordering = ("-created_at",)


# ==========
# KYCDocument
# ==========

@admin.action(description="Marquer comme VALIDÉ")
def mark_kyc_approved(modeladmin, request, queryset):
    queryset.update(status=KYCDocument.APPROVED)

@admin.action(description="Marquer comme REJETÉ")
def mark_kyc_rejected(modeladmin, request, queryset):
    queryset.update(status=KYCDocument.REJECTED)

@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "type", "owner_display", "status", "issued_date", "expiry_date", "reviewed_by", "reviewed_at", "created_at"
    )
    list_filter = ("type", "status", "issued_date", "expiry_date", "created_at")
    search_fields = (
        "number",
        "owner_user__username", "owner_user__email",
        "owner_company__name",
    )
    autocomplete_fields = ("owner_user", "owner_company", "reviewed_by")
    actions = [mark_kyc_approved, mark_kyc_rejected]
    readonly_fields = ("owner_link",)

    def owner_display(self, obj):
        return obj.owner_company or obj.owner_user or f"{obj.owner_content_type}#{obj.owner_object_id}"
    owner_display.short_description = "Propriétaire"

    def owner_link(self, obj):
        # Affiche le type & id génériques (utile pour debug)
        return f"{obj.owner_content_type} / {obj.owner_object_id}"


# ==========
# BankAccount
# ==========

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("bank_name", "account_holder", "currency", "is_default", "owner_display", "created_at")
    list_filter = ("currency", "is_default", "created_at")
    search_fields = ("bank_name", "account_holder", "iban", "account_number", "swift_bic")
    readonly_fields = ("owner_link",)

    def owner_display(self, obj):
        return getattr(obj, "owner", None) or f"{obj.owner_content_type}#{obj.owner_object_id}"
    owner_display.short_description = "Titulaire"

    def owner_link(self, obj):
        return f"{obj.owner_content_type} / {obj.owner_object_id}"


# =========================
# NotificationPreference
# =========================

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "email_enabled", "sms_enabled", "push_enabled", "marketing_opt_in", "updated_at")
    list_filter = ("email_enabled", "sms_enabled", "push_enabled", "marketing_opt_in")
    search_fields = ("user__username", "user__email")


# =============
# ScoutReferral
# =============

@admin.action(description="Valider (status=validated)")
def mark_referral_validated(modeladmin, request, queryset):
    queryset.update(status=ScoutReferral.VALIDATED)

@admin.action(description="Convertir (status=converted)")
def mark_referral_converted(modeladmin, request, queryset):
    queryset.update(status=ScoutReferral.CONVERTED)

@admin.register(ScoutReferral)
class ScoutReferralAdmin(admin.ModelAdmin):
    list_display = ("code", "scout", "status", "invited_user", "commission_rate", "commission_currency", "created_at")
    list_filter = ("status", "commission_currency", "created_at")
    search_fields = ("code", "scout__username", "invited_user__username")
    autocomplete_fields = ("scout", "invited_user")
    actions = [mark_referral_validated, mark_referral_converted]
    ordering = ("-created_at",)