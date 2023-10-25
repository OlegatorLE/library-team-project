from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class IsAdminUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(
            (request.method in SAFE_METHODS and request.user)
            or (request.user and request.user.is_staff)
        )
