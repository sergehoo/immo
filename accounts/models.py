# accounts/models.py
from __future__ import annotations

import uuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models.signals import post_save
from django.dispatch import receiver

# =============== #
# Core User model #
# =============== #

class User(AbstractUser):
    CLIENT_INDIV = "client_individual"
    CLIENT_COMPANY = "client_company"
    OWNER = "owner"
    SCOUT = "scout"  # démarcheur

    ROLE_CHOICES = [
        (CLIENT_INDIV, "Client (particulier)"),
        (CLIENT_COMPANY, "Client (entreprise)"),
        (OWNER, "Propriétaire"),
        (SCOUT, "Démarcheur"),
    ]

    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default=CLIENT_INDIV)
    phone = PhoneNumberField(blank=True, null=True, help_text="Numéro de téléphone au format international")
    company_name = models.CharField(
        max_length=255, blank=True, null=True,
        help_text="Raison sociale si le compte représente une entreprise (client_company/owner)"
    )

    # Flags de confort
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.role})"


# ================== #
# Mixins & Utilities #
# ================== #

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def avatar_upload_to(instance: "UserProfile", filename: str) -> str:
    return f"avatars/{instance.user_id}/{uuid.uuid4()}-{filename}"


def doc_upload_to(instance: "KYCDocument", filename: str) -> str:
    return f"kyc/{instance.owner_user_id or instance.owner_company_id}/{instance.type}/{uuid.uuid4()}-{filename}"


# ========= #
# Address   #
# ========= #

class Address(TimeStampedModel):
    LINE_MAX = 255

    label = models.CharField(max_length=100, blank=True, help_text="Libellé: Domicile, Bureau, Siège, etc.")
    line1 = models.CharField(max_length=LINE_MAX)
    line2 = models.CharField(max_length=LINE_MAX, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=30, blank=True)
    country = CountryField(default="CI")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = "Adresse"
        verbose_name_plural = "Adresses"
        indexes = [
            models.Index(fields=["country", "city"]),
        ]

    def __str__(self):
        parts = [self.line1, self.city, str(self.country)]
        return ", ".join([p for p in parts if p])


# =============== #
# User Profile    #
# =============== #

class UserProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    national_id_number = models.CharField(
        max_length=64, blank=True, help_text="CNI/Passport…"
    )
    primary_address = models.ForeignKey(
        Address, on_delete=models.SET_NULL, null=True, blank=True, related_name="primary_for_users"
    )
    # Préférences de contact
    alt_email = models.EmailField(blank=True, null=True)
    alt_phone = PhoneNumberField(blank=True, null=True)

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateur"

    def __str__(self):
        return f"Profil({self.user})"


# ================= #
# Company / Org     #
# ================= #

class Company(TimeStampedModel):
    LANDLORD = "landlord"        # propriétaire/bailleur
    AGENCY = "agency"            # agence
    CORPORATE = "corporate"      # client entreprise
    DEVELOPER = "developer"      # promoteur
    TYPES = [
        (LANDLORD, "Propriétaire / Bailleur"),
        (AGENCY, "Agence immobilière"),
        (CORPORATE, "Client entreprise"),
        (DEVELOPER, "Promoteur immobilier"),
    ]

    name = models.CharField(max_length=255, unique=True)
    company_type = models.CharField(max_length=20, choices=TYPES)
    email = models.EmailField(blank=True, null=True)
    phone = PhoneNumberField(blank=True, null=True)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name="companies")
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)

    # Identifiants légaux
    rc_number = models.CharField("RCCM / Registre commerce", max_length=64, blank=True)
    tax_number = models.CharField("N° contribuable", max_length=64, blank=True)
    website = models.URLField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Entreprise/Société"
        verbose_name_plural = "Entreprises/Sociétés"
        indexes = [
            models.Index(fields=["company_type"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.company_type})"


class CompanyMembership(TimeStampedModel):
    ADMIN = "admin"
    STAFF = "staff"
    VIEWER = "viewer"
    ROLES = [(ADMIN, "Admin"), (STAFF, "Staff"), (VIEWER, "Viewer")]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company_memberships")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="members")
    role = models.CharField(max_length=16, choices=ROLES, default=STAFF)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Membre d'entreprise"
        verbose_name_plural = "Membres d'entreprise"
        unique_together = ("user", "company")
        constraints = [
            models.UniqueConstraint(
                fields=["user"], condition=models.Q(is_primary=True), name="unique_primary_company_per_user"
            )
        ]

    def __str__(self):
        return f"{self.user} @ {self.company} [{self.role}]"


# ===================== #
# KYC / Vérifications   #
# ===================== #

class KYCDocument(TimeStampedModel):
    ID_CARD = "id_card"
    PASSPORT = "passport"
    UTILITY_BILL = "utility_bill"
    BUSINESS_REG = "business_registration"
    DOC_TYPES = [
        (ID_CARD, "CNI / Carte d'identité"),
        (PASSPORT, "Passeport"),
        (UTILITY_BILL, "Facture (SODECI/CEI/…"),
        (BUSINESS_REG, "Registre de commerce / Attestation d'immatriculation"),
    ]

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    STATUSES = [(PENDING, "En attente"), (APPROVED, "Validé"), (REJECTED, "Rejeté")]

    # Propriétaire du document : User OU Company (Generic FK pour flexibilité)
    owner_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    owner_object_id = models.PositiveIntegerField()
    owner = GenericForeignKey("owner_content_type", "owner_object_id")

    # Raccourcis utiles (FK directs optionnels, non obligatoires)
    owner_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    owner_company = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL)

    type = models.CharField(max_length=32, choices=DOC_TYPES)
    number = models.CharField(max_length=64, blank=True)
    file = models.FileField(upload_to=doc_upload_to)
    issued_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=16, choices=STATUSES, default=PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="kyc_reviews"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Document KYC"
        verbose_name_plural = "Documents KYC"
        indexes = [
            models.Index(fields=["type", "status"]),
        ]

    def __str__(self):
        who = self.owner_company or self.owner_user or self.owner
        return f"KYC[{self.type}] - {who}"


# ===================== #
# Bank / Paiements      #
# ===================== #

class BankAccount(TimeStampedModel):
    """Coordonnées bancaires (User ou Company via Generic FK)."""
    owner_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    owner_object_id = models.PositiveIntegerField()
    owner = GenericForeignKey("owner_content_type", "owner_object_id")

    bank_name = models.CharField(max_length=120)
    account_holder = models.CharField(max_length=120)
    iban = models.CharField(max_length=34, blank=True)  # IBAN si dispo
    account_number = models.CharField(max_length=64, blank=True)
    swift_bic = models.CharField(max_length=11, blank=True)
    currency = models.CharField(max_length=8, default="XOF")

    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Compte bancaire"
        verbose_name_plural = "Comptes bancaires"
        indexes = [
            models.Index(fields=["bank_name", "currency"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner_content_type", "owner_object_id"],
                condition=models.Q(is_default=True),
                name="unique_default_bank_account_per_owner",
            )
        ]

    def __str__(self):
        return f"{self.bank_name} - {self.account_holder} ({self.currency})"


# =========================== #
# Préférences de notification #
# =========================== #

class NotificationPreference(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_prefs")

    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=False)

    marketing_opt_in = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Préférences de notification"
        verbose_name_plural = "Préférences de notification"

    def __str__(self):
        return f"Prefs({self.user})"


# =========================== #
# Parrainage (démarcheur)     #
# =========================== #

class ScoutReferral(TimeStampedModel):
    """Parrainage / lead créé par un démarcheur (SCOUT)."""
    NEW = "new"
    VALIDATED = "validated"
    CONVERTED = "converted"
    REJECTED = "rejected"
    STATUSES = [
        (NEW, "Nouveau"),
        (VALIDATED, "Validé"),
        (CONVERTED, "Converti"),
        (REJECTED, "Rejeté"),
    ]

    code = models.CharField(max_length=12, unique=True, help_text="Code de parrainage")
    scout = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="scout_referrals",
        limit_choices_to={"role": User.SCOUT}
    )
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="invited_by_scout",
        null=True, blank=True
    )
    status = models.CharField(max_length=16, choices=STATUSES, default=NEW)
    notes = models.TextField(blank=True)

    # KPI/commission (calcul complet géré côté billing/payments)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    commission_currency = models.CharField(max_length=8, default="XOF")

    class Meta:
        verbose_name = "Parrainage démarcheur"
        verbose_name_plural = "Parrainages démarcheurs"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"Referral[{self.code}] by {self.scout}"


# ========================== #
# Signals: create defaults   #
# ========================== #



@receiver(post_save, sender=User)
def create_profile_and_prefs(sender, instance: User, created: bool, **kwargs):
    """Créer automatiquement le profil & préférences à la création du user."""
    if created:
        UserProfile.objects.create(user=instance)
        NotificationPreference.objects.create(user=instance)