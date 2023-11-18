
from django.db import models
from django_relay_endpoint.configurators.object_types import DjangoClientIDMutation
import graphene
from graphene_django import DjangoObjectType
from graphene.types.generic import GenericScalar
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Callable, Type
from django_relay_endpoint.configurators.permissions import node_permission_checker, queryset_permission_checker, BasePermission

def configure_abstract_mutation(
    django_object_type: Type[DjangoObjectType],
    conventional_name: str,
    field_validators: Dict[str, List[Callable]] = {},
    non_field_validators: List[Callable] = [],
    return_field_name: str = None,
    custom_get_queryset: staticmethod = None,
    permission_classes: List[Type[BasePermission]] = [],
    permissions: List[str] = [],
    ) -> Type[DjangoClientIDMutation]:
    """
    Configures an abstract mutation from `DjangoClientIDMutation`, with all fields, validators, permissions set on NodeType,
    overwrites `get_queryset` and `get_node` methods to support permission checking and custom 'get_queryset'.

    Args:
        django_object_type (Type[DjangoObjectType]): 
        The `DjangoObjectType` configured for given model.

        conventional_name (str): 
        the conventional name prefixed for the class name.

        field_validators (Dict[str, List[Callable]], optional): 
        A dictionary of where keys are field names, and values are field validator functions. Defaults to {}.

        non_field_validators (List[Callable], optional): 
        A list of functions that do data level validation. Defaults to [].

        return_field_name (str, optional): 
        The mutation field name of the return type. If none is provided `model._meta.model_name` will be used, which is by default. Defaults to None.

        custom_get_queryset (staticmethod, optional): 
        A static method that overwrites the get_queryset classmethod. N.B. this method must be a staticmethod. Defaults to None.

        permission_classes (List[Type[BasePermission]], optional): 
        The list of permission_classes. Defaults to [].

        permissions (List[str], optional): 
        The list of permissions. Defaults to [].

    Returns:
        Type[DjangoClientIDMutation]: 
        A configured abstract type for our model that the create, update and delete mutation root fields will be configured from 
    """
    
    model: Type[models.Model] = django_object_type._meta.model
    class Meta:
        abstract=True

    # Declare a base abstract class that applies permission checkers and get_queryset overwrite 
    class AbstractDjangoClientIDMutation(DjangoClientIDMutation):
        
        class Meta:
            abstract=True

        @classmethod
        @queryset_permission_checker()
        def get_queryset(cls, queryset, info):
            # instead of overwriting the get_queryset classmethod, we inject the get_queryset staticmethod with same args as the classmethod.
            # this ensures that permission checking is not overwritten by mistake.
            if custom_get_queryset:
                return custom_get_queryset(cls, queryset, info)  
            else:
                return super().get_queryset(queryset, info)

        @classmethod
        @node_permission_checker()
        def get_node(cls, info, id):
            return super().get_node(info, id)
        


    mutation_type = type(f"{conventional_name}AbstractClientIDMutation", (AbstractDjangoClientIDMutation,), {
        "model": model,
        "django_object_type": django_object_type,
        "Meta": Meta,
        "message": graphene.String(),
        "success": graphene.Boolean(),
        "client_mutation_id": GenericScalar(),
        "field_validators": field_validators, 
        "non_field_validators": non_field_validators, 
        return_field_name or model._meta.model_name: graphene.Field(django_object_type),
        "permission_classes": permission_classes,
        "permissions": permissions
    })
    return mutation_type