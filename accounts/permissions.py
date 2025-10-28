# accounts/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user

class IsOwnerUserOrReadOnly(BasePermission):
    """Pour objets liés à un user (ex: profil, adresse)."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "user", None) or getattr(obj, "owner_user", None)
        return owner == request.user

class IsStaffOrOwnerKYC(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        # propriétaire user ou membre de la company
        if obj.owner_user and obj.owner_user == request.user:
            return True
        if obj.owner_company:
            return obj.owner_company.members.filter(user=request.user).exists()
        return False