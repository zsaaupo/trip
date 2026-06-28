from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """Administrator = Django's is_staff flag (SRS 2.3.2: no public admin signup)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Anyone (incl. anonymous) can read listings; only admins can write."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsOwnerOrAdmin(permissions.BasePermission):
    """A booking may only be read/modified by the customer who made it, or an admin."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.customer_id == request.user.id
