import graphene
from django.core.exceptions import PermissionDenied
from typing import List, Callable, Type, Union
from django.utils.translation import gettext_lazy as _
from graphql_relay.node.node import from_global_id
from django.db import models
from .object_types import DjangoObjectType, DjangoClientIDMutation

class BasePermission:
    """
    A base class from which all permission classes should inherit.
    """

    def has_permission(self, info) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True

    def has_object_permission(self, info, obj) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True
    

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

    def has_permission(self, info) -> bool:
        return bool(info.context.user and info.context.user.is_authenticated)

class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, info) -> bool:
        return bool(info.context.user and info.context.user.is_staff)

class IsAuthenticatedOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, info) -> bool:
        return bool(
            not isinstance(info.parent_type, graphene.relay.ClientIDMutation) and
            info.context.user and
            info.context.user.is_authenticated
        )
 


PERMISSION_ERROR = _("Permission denied!")
PERMISSIONS_ASSERTION_ERROR = _("Permissions must be a list of strings.")
PERMISSION_CLASS_ASSERTION_ERROR = _("You must provide a list of permission classes that extend graphene_relay_endpoint.BasePermission.")



def assert_permissions_are_valid(permissions: List[str]) -> None:
    """
    Raises assertion error if permissions is not a list of strings
    """

    if not isinstance(permissions, list) or not all(isinstance(perm, str) for perm in permissions):
        raise AssertionError(PERMISSIONS_ASSERTION_ERROR)


def assert_permission_classes_are_valid(permission_classes: List[Type[BasePermission]]) -> None:
    """
    Raises asserion error if permission classes are not a list of classes extending BasePermission
    """
    
    if not isinstance(permission_classes, list) or not all(issubclass(perm, BasePermission) for perm in permission_classes):
        raise AssertionError(PERMISSION_CLASS_ASSERTION_ERROR)


def user_permission_checker(cls: Type[Union[DjangoClientIDMutation, DjangoObjectType]], info: graphene.ResolveInfo) -> None:
    """
    Raises error if user does not have the permissions defined as strings
    Calls user.has_perms(tuple(permissions)):

    Args:
        info (graphene.ResolveInfo): the info of graphene DjangoObjectType or DjangoClientIDMutation type

    Raises:
        PermissionDenied
    """
    
    permissions = cls.permissions
    user = info.context.user
    if not user.has_perms(tuple(permissions)):
        raise PermissionDenied(PERMISSION_ERROR)


def queryset_permission_checker() -> classmethod: # this is final decorator type
    """
    A decorator designed for `DjangoClientIDMutation` and `DjangoObjectType` `get_queryset` classmethod
    The decorator has no arguments, however it returns a wrapper decorator, which takes `get_queryset` 
    classmethod and wraps it in a decorator passing the args of the `get_queryset` classmethod. 
    The decorator checks `cls.permissions` calling user_permission_checker and `has_permission` method on all `cls.permission_classes`.
    The latter raises PermissionDenied if any permission fails.

    Returns:
        decorator: a classmethod decorator for `cls.get_queryset`
    """

    def wrapped_decorator(get_queryset_method: Type[Callable[..., Type[Callable]]]) -> Type[Callable[..., Type[Callable]]]:
        def wrapped_get_queryset(cls: Type[Union[DjangoClientIDMutation, DjangoObjectType]], queryset: models.QuerySet, info: graphene.ResolveInfo) -> classmethod:
            """
            The decorator that checks the permissions calling `user_permission_checker` and all `has_permission` method on all `cls.permission_classes`

            Args:
                cls (Type[Union[DjangoClientIDMutation, DjangoObjectType]]): A class extending either DjangoClientIDMutation or DjangoObjectType
                queryset (models.QuerySet): the queryset, which is passed from get_node
                info (graphene.ResolveInfo): graphene.ResolveInfo object instance 

            Raises:
                PermissionDenied

            Returns:
                classmethod: the get_queryset classmethod
            """

            # call user_permission_checker function with cls and info
            user_permission_checker(cls, info)
            permission_classes = cls.permission_classes
            if permission_classes:
                for p_cls in permission_classes:
                    allowed = p_cls().has_permission(info)
                    if not allowed:
                        raise PermissionDenied(PERMISSION_ERROR)
            
            return get_queryset_method(cls, queryset, info)
        
        return wrapped_get_queryset
    return wrapped_decorator

def node_permission_checker() -> classmethod: # this is final decorator type
    """
    A decorator designed for DjangoClientIDMutation and DjangoObjectType get_node classmethod which does object level permission check.
    The decorator has no arguments, however it returns a wrapper decorator, which takes get_node
    classmethod and wraps it in a decorator passing the args of the get_node classmethod. 
    The decorator checks the permissions on object level calling all `the has_object_permission` on all `cls.permission_classes`.
    The latter raises `PermissionDenied` if any permission fails.


    Returns:
        decorator: a classmethod decorator for get_node
    """

    def wrapped_decorator(get_node_method: Type[Callable[..., Type[Callable]]]) -> Type[Callable[..., Type[Callable]]]:
        """
        The decorator that returns the wrapped get_node method

        Args:
            get_node_method (classmethod): the get_node classmethod of DjangoClientIDMutation or DjangoObjectType
        """

        def wrapped_get_node(cls: Type[Union[DjangoObjectType, DjangoClientIDMutation]], info: graphene.ResolveInfo, id: str) -> classmethod:
            """
            The decorator that checks the permissions on object level calling all `the has_object_permission` on all `cls.permission_classes`

            Args:
                cls (Type[Union[DjangoClientIDMutation, DjangoObjectType]]): A class extending either DjangoClientIDMutation or DjangoObjectType
                info (graphene.ResolveInfo): graphene.ResolveInfo object instance 
                id (str): the universally unique id of provided in graphene

            Raises:
                PermissionDenied

            Returns:
                classmethod: a get_node classmethod
            """

            # no need to call user_permission_checker, because the get_node and create_node methods on the class call the get_queryset method
            permission_classes = cls.permission_classes
            if permission_classes:
                obj = cls.Meta.model.objects.get(id=from_global_id(id).id)
                for p_cls in permission_classes:
                    allowed = p_cls().has_object_permission(info, obj)
                    if not allowed:
                        raise PermissionDenied(PERMISSION_ERROR)
            
            return get_node_method(cls, info, id)
        
        return wrapped_get_node
    return wrapped_decorator

