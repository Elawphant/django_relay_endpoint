import graphene
from django.core.exceptions import PermissionDenied
from typing import List, Callable, Any
from django.utils.translation import gettext_lazy as _
from graphql_relay.node.node import from_global_id
from django.db import models
from .object_types import DjangoObjectType

class BasePermission:
    """
    A base class from which all permission classes should inherit.
    """

    def has_permission(self, info):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(self, info, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True
    
    def check_permissions(self, info, obj = None):
        """
        Returns the result of has_permission and has_object_permission methods

        """
        return self.has_permission(info) and self.has_object_permission(info, obj)


class AllowAny(BasePermission):
    """
    Allow any access.
    This isn't strictly required, since you could use an empty
    permission_classes list, but it's useful because it makes the intention
    more explicit.
    """

    def has_permission(self, info):
        return True

class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, info):
        return bool(info.context.user and info.context.user.is_authenticated)

class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, info):
        return bool(info.context.user and info.context.user.is_staff)

class IsAuthenticatedOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, info):
        return bool(
            not isinstance(info.parent_type, graphene.relay.ClientIDMutation) and
            info.context.user and
            info.context.user.is_authenticated
        )
 


PERMISSION_ERROR = _("Permission denied!")
PERMISSIONS_ASSERTION_ERROR = _("Permissions must be a list of strings.")
PERMISSION_CLASS_ASSERTION_ERROR = _("You must provide a list of permission classes that extend graphene_relay_endpoint.BasePermission.")



def assert_permissions_are_valid(permissions: Any):
    if not isinstance(permissions, list):
        raise AssertionError(PERMISSIONS_ASSERTION_ERROR)
    for perm in permissions:
        if not isinstance(perm, str):
            raise AssertionError(PERMISSIONS_ASSERTION_ERROR)


def assert_permission_classes_are_valid(permission_classes: Any):
    if not isinstance(permission_classes, list):
        raise AssertionError(PERMISSION_CLASS_ASSERTION_ERROR)
    for p_cls in permission_classes:
        if not isinstance(p_cls, BasePermission):
            raise AssertionError(PERMISSION_CLASS_ASSERTION_ERROR)


def user_permission_checker(cls, info):
    permissions = cls.permissions
    # make sure of these arguments to the wrapped mutation
    user = info.context.user
    for perm in permissions:
        if isinstance(perm, str):
            perms = (perm, )
        else:
            perms = perm
        
        if not user.has_perms(perms):
            raise PermissionDenied(PERMISSION_ERROR)


def queryset_permission_checker():
    def wrapped_decorator(class_method: classmethod):
        def wrapped_get_queryset(cls: type[DjangoObjectType], queryset: models.QuerySet, info: graphene.ResolveInfo):
            user_permission_checker(cls, info)
            permission_classes = cls.permission_classes
            if permission_classes:
                if not isinstance(permission_classes, list):
                    raise AssertionError(PERMISSION_CLASS_ASSERTION_ERROR)
                for p_cls in permission_classes:
                    if not isinstance(p_cls, BasePermission):
                        raise AssertionError(PERMISSION_CLASS_ASSERTION_ERROR)
                    allowed = p_cls().has_permission(info)
                    if not allowed:
                        raise PermissionDenied(PERMISSION_ERROR)
            
            return class_method(cls, queryset, info)
        
        return wrapped_get_queryset
    return wrapped_decorator

def node_permission_checker():
    def wrapped_decorator(class_method: classmethod):
        def wrapped_get_node(cls: type[DjangoObjectType], info: graphene.ResolveInfo, id: str):
            user_permission_checker(cls, info)
            permission_classes = cls.permission_classes
            if permission_classes:
                obj = cls.Meta.model.objects.get(id=from_global_id(id).id)
                for p_cls in permission_classes:
                    allowed = p_cls().has_object_permission(info, obj)
                    if not allowed:
                        raise PermissionDenied(PERMISSION_ERROR)
            
            return class_method(cls, info, id)
        
        return wrapped_get_node
    return wrapped_decorator

