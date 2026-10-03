from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsProvider(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_provider


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_customer


class IsOwnerOrAdmin(permissions.BasePermission):    
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj == request.user


class IsSelfOrAdmin(permissions.BasePermission):    
    def has_permission(self, request, view):
        if view.action == 'list':
            return request.user and request.user.is_authenticated and request.user.is_admin
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj == request.user


class IsProviderOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True
        
        return request.user.is_authenticated and (
            request.user.is_provider or request.user.is_admin
        )
    
    def has_object_permission(self, request, view, obj):
        if view.action in ['retrieve']:
            return True
        
        return request.user.is_admin or obj.provider == request.user


class IsServiceOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return obj.provider == request.user


class IsBookingOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_admin:
            return True
        return user == obj.customer or user == obj.provider