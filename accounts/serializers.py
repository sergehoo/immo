# /Users/ogahserge/Documents/terra360/accounts/serializers.py
# accounts/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import UserProfile, Address, Company, CompanyMembership, KYCDocument
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


# -------- Address
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id", "label", "line1", "line2", "city", "state", "postal_code", "country",
            "latitude", "longitude", "created_at", "updated_at",
        ]


# -------- User / Profile (lecture)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "phone", "company_name",
                  "is_email_verified", "is_phone_verified"]


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    primary_address = AddressSerializer(read_only=True)
    primary_address_id = serializers.PrimaryKeyRelatedField(
        write_only=True, queryset=Address.objects.all(), source="primary_address", allow_null=True, required=False
    )

    class Meta:
        model = UserProfile
        fields = [
            "user", "avatar", "birth_date", "national_id_number", "primary_address", "primary_address_id",
            "alt_email", "alt_phone", "created_at", "updated_at",
        ]


# -------- Register / Update
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = [
            "username", "password", "email", "phone", "role", "company_name", "first_name", "last_name"
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "company_name"]
        extra_kwargs = {"email": {"required": False}}


class ProfileUpdateSerializer(serializers.ModelSerializer):
    # permet d’uploader avatar + éditer infos
    class Meta:
        model = UserProfile
        fields = ["avatar", "birth_date", "national_id_number", "primary_address", "alt_email", "alt_phone"]


# -------- Company
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "id", "name", "company_type", "email", "phone", "address", "logo",
            "rc_number", "tax_number", "website", "is_active", "created_at", "updated_at"
        ]


class CompanyMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyMembership
        fields = ["id", "user", "company", "role", "is_primary", "created_at", "updated_at"]
        read_only_fields = ["user"]


# -------- KYC
class KYCDocumentSerializer(serializers.ModelSerializer):
    owner_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="owner_user", required=False, allow_null=True
    )
    owner_company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(), source="owner_company", required=False, allow_null=True
    )

    class Meta:
        model = KYCDocument
        fields = [
            "id", "type", "number", "file", "issued_date", "expiry_date",
            "status", "reviewed_by", "reviewed_at", "review_notes",
            "owner_user_id", "owner_company_id", "created_at", "updated_at",
        ]
        read_only_fields = ["status", "reviewed_by", "reviewed_at"]

    def create(self, validated_data):
        # lie le GenericFK à partir des raccourcis owner_user / owner_company
        owner_user = validated_data.pop("owner_user", None)
        owner_company = validated_data.pop("owner_company", None)
        if not owner_user and not owner_company:
            # Par défaut: propriétaire = request.user
            request = self.context.get("request")
            owner_user = getattr(request, "user", None)
        if owner_user:
            ct = ContentType.objects.get_for_model(User)
            obj = KYCDocument.objects.create(
                owner_content_type=ct, owner_object_id=owner_user.id, owner_user=owner_user, **validated_data
            )
        else:
            ct = ContentType.objects.get_for_model(Company)
            obj = KYCDocument.objects.create(
                owner_content_type=ct, owner_object_id=owner_company.id, owner_company=owner_company, **validated_data
            )
        return obj


class KYCReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCDocument
        fields = ["status", "review_notes"]

    def update(self, instance, validated_data):
        request = self.context["request"]
        instance.status = validated_data.get("status", instance.status)
        instance.review_notes = validated_data.get("review_notes", instance.review_notes)
        instance.reviewed_by = request.user
        from django.utils import timezone
        instance.reviewed_at = timezone.now()
        instance.save()
        return instance
