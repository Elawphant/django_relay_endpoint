
from django.db import models
from ..object_types import DjangoClientIDMutation
import graphene
from graphene_django import DjangoObjectType
from graphene.types.generic import GenericScalar
from graphql_relay.node.node import from_global_id
from django.utils.translation import gettext_lazy as _
from typing import Dict, List, Callable
from ..permissions import node_permission_checker, queryset_permission_checker

def configure_abstract_mutation(
    django_object_type: DjangoObjectType,
    conventional_name: str,
    field_validators: Dict[str, List[callable]] = {},
    non_field_validators: List[Callable] = [],
    return_field_name: str = None,
    custom_get_queryset = None,
    permission_classes = [],
    permissions = [],
    ) -> type[DjangoClientIDMutation]:
    
    model = django_object_type._meta.model
    class Meta:
        abstract=True

    class AbstractDjangoClientIDMutation(DjangoClientIDMutation):
        
        class Meta:
            abstract=True

        @classmethod
        @queryset_permission_checker()
        def get_queryset(cls, queryset, info):
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