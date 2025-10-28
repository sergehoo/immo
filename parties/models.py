# /Users/ogahserge/Documents/terra360/parties/models.py
# parties/models.py
from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

# =======================
# Mixins / utilities
# =======================

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def attachment_upload_to(instance: "PartyAttachment", filename: str) -> str:
    return f"party/{instance.party_id}/attachments/{uuid.uuid4()}-{filename}"


# =======================
# Rôles (extensibles)
# =======================
class PartyRole(models.Model):
    """
    Catalogue des rôles possibles (landlord, tenant, agent, scout, notary, etc.)
    Permet d'étendre sans toucher au schéma de Party.
    """
    code = models.SlugField(max_length=32, unique=True)
    label = models.CharField(max_length=120)

    class Meta:
        verbose_name = "Rôle de partie"
        verbose_name_plural = "Rôles de partie"

    def __str__(self) -> str:
        return f"{self.label} ({self.code})"


# =======================
# Partie (coeur)
# =======================
class Party(TimeStampedModel):
    """
    Entité générique représentant une personne ou une entreprise impliquée
    dans les processus immobiliers (propriétaire, locataire, agent, etc.).
    """
    user = models.OneToOneField(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="party"
    )
    company = models.ForeignKey(  # si Party de type entreprise, on peut la pointer
        "accounts.Company", on_delete=models.SET_NULL, null=True, blank=True, related_name="parties"
    )

    PERSON = "person"
    COMPANY = "company"
    PARTY_TYPES = [(PERSON, "Personne"), (COMPANY, "Entreprise")]

    type = models.CharField(max_length=16, choices=PARTY_TYPES)

    full_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = PhoneNumberField(blank=True, null=True)

    # Rôles extensibles (recommandé)
    roles = models.ManyToManyField(PartyRole, blank=True, related_name="parties")

    # Flags historiques (compatibilité — préférer Party.roles à terme)
    is_landlord = models.BooleanField(default=False, help_text="Legacy: préférez les rôles via Party.roles")
    is_tenant = models.BooleanField(default=False, help_text="Legacy: préférez les rôles via Party.roles")
    is_agent = models.BooleanField(default=False, help_text="Legacy: préférez les rôles via Party.roles")

    class Meta:
        verbose_name = "Partie"
        verbose_name_plural = "Parties"
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["full_name"]),
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self) -> str:
        return self.full_name

    # Helpers pratiques
    @property
    def is_company(self) -> bool:
        return self.type == self.COMPANY

    @property
    def is_person(self) -> bool:
        return self.type == self.PERSON


# =======================
# Adresses d'une Party
# =======================
class PartyAddress(TimeStampedModel):
    """
    Lie une Party à une ou plusieurs adresses (via accounts.Address),
    avec un type fonctionnel (principal, facturation, courrier...).
    """
    PRIMARY = "primary"
    BILLING = "billing"
    MAILING = "mailing"
    WORK = "work"
    OTHER = "other"
    TYPES = [
        (PRIMARY, "Principale"),
        (BILLING, "Facturation"),
        (MAILING, "Courrier"),
        (WORK, "Professionnelle"),
        (OTHER, "Autre"),
    ]

    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="party_addresses")
    address = models.ForeignKey("accounts.Address", on_delete=models.CASCADE, related_name="party_links")
    address_type = models.CharField(max_length=16, choices=TYPES, default=PRIMARY)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Adresse de partie"
        verbose_name_plural = "Adresses de partie"
        unique_together = ("party", "address", "address_type")
        indexes = [
            models.Index(fields=["address_type"]),
            models.Index(fields=["is_primary"]),
        ]

    def __str__(self) -> str:
        return f"{self.party} → {self.address} [{self.address_type}]"


# =======================
# Contacts complémentaires
# =======================
class PartyContact(TimeStampedModel):
    EMAIL = "email"
    PHONE = "phone"
    WEBSITE = "website"
    OTHER = "other"
    TYPES = [
        (EMAIL, "Email"),
        (PHONE, "Téléphone"),
        (WEBSITE, "Site web"),
        (OTHER, "Autre"),
    ]

    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="contacts")
    type = models.CharField(max_length=16, choices=TYPES, default=PHONE)
    label = models.CharField(max_length=120, blank=True, help_text="Ex: perso, bureau, WhatsApp…")
    email = models.EmailField(blank=True, null=True)
    phone = PhoneNumberField(blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, help_text="Pour website/autres")

    class Meta:
        verbose_name = "Contact de partie"
        verbose_name_plural = "Contacts de partie"
        indexes = [models.Index(fields=["type"])]

    def __str__(self) -> str:
        return f"{self.party} – {self.type}/{self.label or '—'}"


# =======================
# Relations entre parties
# =======================
class PartyRelationship(TimeStampedModel):
    """
    Représente un lien sémantique entre deux parties :
    - agent_of : A est l'agent de B
    - legal_rep_of : A est le représentant légal de B
    - employee_of : A est employé de B
    - family_of : A a un lien familial avec B
    """
    AGENT_OF = "agent_of"
    LEGAL_REP_OF = "legal_rep_of"
    EMPLOYEE_OF = "employee_of"
    FAMILY_OF = "family_of"
    OTHER = "other"

    TYPES = [
        (AGENT_OF, "Agent de"),
        (LEGAL_REP_OF, "Représentant légal de"),
        (EMPLOYEE_OF, "Employé de"),
        (FAMILY_OF, "Lien familial avec"),
        (OTHER, "Autre"),
    ]

    from_party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="relationships_from")
    to_party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="relationships_to")
    relation_type = models.CharField(max_length=24, choices=TYPES)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Relation entre parties"
        verbose_name_plural = "Relations entre parties"
        unique_together = ("from_party", "to_party", "relation_type")
        indexes = [models.Index(fields=["relation_type"])]

    def __str__(self) -> str:
        return f"{self.from_party} → {self.to_party} [{self.relation_type}]"


# =======================
# Pièces jointes / docs
# =======================
class PartyAttachment(TimeStampedModel):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="attachments")
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=attachment_upload_to)
    mime_type = models.CharField(max_length=120, blank=True)
    size_bytes = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Pièce jointe (Partie)"
        verbose_name_plural = "Pièces jointes (Partie)"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.party})"


# =======================
# Notes & Tags
# =======================
class PartyTag(models.Model):
    code = models.SlugField(max_length=32, unique=True)
    label = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Tag de partie"
        verbose_name_plural = "Tags de partie"

    def __str__(self) -> str:
        return self.label


class PartyNote(TimeStampedModel):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    tags = models.ManyToManyField(PartyTag, blank=True, related_name="notes")

    class Meta:
        verbose_name = "Note (Partie)"
        verbose_name_plural = "Notes (Partie)"
        indexes = [
            models.Index(fields=["is_pinned"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Note {self.party_id} – {self.created_at:%Y-%m-%d}"


# =======================
# Signals d’alignement
# =======================
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="accounts.User")
def create_or_update_party_for_user(sender, instance, created, **kwargs):
    """
    - Crée automatiquement une Party pour chaque User (si utile à ton business).
    - Met à jour le nom affiché.
    """
    if created:
        full_name = instance.get_full_name().strip() or instance.username
        p = Party.objects.create(
            user=instance,
            type=Party.PERSON,
            full_name=full_name,
            email=instance.email or "",
            phone=getattr(instance, "phone", None),
        )
        # mappage minimal des rôles user -> party (optionnel)
        # Exemple: owner -> is_landlord True
        role = getattr(instance, "role", None)
        if role == "owner":
            p.is_landlord = True
            p.save(update_fields=["is_landlord"])
    else:
        try:
            p = instance.party
            name = instance.get_full_name().strip() or instance.username
            updates = []
            if p.full_name != name:
                p.full_name = name
                updates.append("full_name")
            if instance.email and p.email != instance.email:
                p.email = instance.email
                updates.append("email")
            if hasattr(instance, "phone") and p.phone != instance.phone:
                p.phone = instance.phone
                updates.append("phone")
            if updates:
                p.save(update_fields=updates + ["updated_at"])
        except Party.DoesNotExist:
            # Si l’utilisateur n’a pas de Party (supprimée manuellement), on la recrée
            Party.objects.create(
                user=instance,
                type=Party.PERSON,
                full_name=instance.get_full_name().strip() or instance.username,
                email=instance.email or "",
                phone=getattr(instance, "phone", None),
            )


@receiver(post_save, sender="accounts.Company")
def create_or_update_party_for_company(sender, instance, created, **kwargs):
    """
    Associer une Party à chaque Company (si tu utilises accounts.Company).
    """
    if created:
        Party.objects.create(
            company=instance,
            type=Party.COMPANY,
            full_name=instance.name,
            email=instance.email or "",
            phone=getattr(instance, "phone", None),
        )
    else:
        # Mettre à jour la Party liée si elle existe
        party_qs = Party.objects.filter(company=instance)
        if party_qs.exists():
            p = party_qs.first()
            updates = []
            if p.full_name != instance.name:
                p.full_name = instance.name
                updates.append("full_name")
            if instance.email and p.email != instance.email:
                p.email = instance.email
                updates.append("email")
            if hasattr(instance, "phone") and p.phone != instance.phone:
                p.phone = instance.phone
                updates.append("phone")
            if updates:
                p.save(update_fields=updates + ["updated_at"])