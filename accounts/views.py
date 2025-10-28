# /Users/ogahserge/Documents/terra360/accounts/views.py
# accounts/views.py
from rest_framework import generics, permissions, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import (
    RegisterSerializer, UserSerializer, UserUpdateSerializer, UserProfileSerializer, ProfileUpdateSerializer,
    AddressSerializer, CompanySerializer, CompanyMembershipSerializer,
    KYCDocumentSerializer, KYCReviewSerializer,
)
from .models import UserProfile, Address, Company, CompanyMembership, KYCDocument
from .permissions import IsSelf, IsOwnerUserOrReadOnly, IsStaffOrOwnerKYC

User = get_user_model()


# -------- Register
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


# -------- Me (GET) & Update (PATCH) user
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UserUpdateSerializer
        return UserSerializer


# -------- Mon profil (UserProfile)
class MyProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # pour avatar upload

    def get_object(self):
        return self.request.user.profile

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProfileUpdateSerializer
        return UserProfileSerializer


# -------- Adresses (CRUD perso)
class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerUserOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["city", "country"]

    def get_queryset(self):
        # Adresses personnelles + adresses des companies où je suis membre (lecture)
        mine = Address.objects.filter(primary_for_users__user=self.request.user)
        company_addresses = Address.objects.filter(companies__members__user=self.request.user).distinct()
        return (mine | company_addresses).distinct()

    def perform_create(self, serializer):
        # Adresse “libre” que l’utilisateur pourra lier à son profil
        self.instance = serializer.save()


# -------- Company & memberships
class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["company_type", "is_active"]
    queryset = Company.objects.all()

    @action(detail=True, methods=["post"], url_path="join")
    def join(self, request, pk=None):
        company = self.get_object()
        role = request.data.get("role", "staff")
        mem, _ = CompanyMembership.objects.get_or_create(user=request.user, company=company, defaults={"role": role})
        return Response(CompanyMembershipSerializer(mem).data)

    @action(detail=True, methods=["post"], url_path="set-primary")
    def set_primary(self, request, pk=None):
        company = self.get_object()
        CompanyMembership.objects.filter(user=request.user, is_primary=True).update(is_primary=False)
        mem, _ = CompanyMembership.objects.get_or_create(user=request.user, company=company)
        mem.is_primary = True
        mem.save()
        return Response(CompanyMembershipSerializer(mem).data)


class CompanyMembershipViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CompanyMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CompanyMembership.objects.filter(user=self.request.user).select_related("company")


# -------- KYC Docs
class KYCDocumentViewSet(viewsets.ModelViewSet):
    queryset = KYCDocument.objects.all().select_related("owner_user", "owner_company", "reviewed_by")
    permission_classes = [permissions.IsAuthenticated, IsStaffOrOwnerKYC]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = KYCDocumentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["type", "status", "owner_user", "owner_company"]

    def get_queryset(self):
        qs = super().get_queryset()
        u = self.request.user
        if u.is_staff:
            return qs
        return qs.filter(
            models.Q(owner_user=u) |
            models.Q(owner_company__members__user=u)
        ).distinct()

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def review(self, request, pk=None):
        doc = self.get_object()
        serializer = KYCReviewSerializer(doc, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(KYCDocumentSerializer(doc).data)
