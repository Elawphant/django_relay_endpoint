
from django.db import models
import graphene
from typing import Dict, List, Callable, Type
from django_filters import FilterSet
from django_relay_endpoint.configurators.permissions import BasePermission
from django_relay_endpoint.configurators.object_types import DjangoObjectType
from django_relay_endpoint.configurators.permissions import queryset_permission_checker, node_permission_checker



def configure_node_object_type(
        model: Type[models.Model],
        conventional_name: str,
        fields: List[str] = [],
        filter_fields: Dict[str, list] = {},
        filterset_class: Type[FilterSet] = None,
        custom_get_queryset: Callable = None,
        permissions: List[str] = [],
        permission_classes: List[BasePermission] = [],
) -> Type[DjangoObjectType]:
    """Creates graphene Node Type from given django model class

    Per <https://docs.graphene-python.org/projects/django/en/latest/queries/>, It is strongly recommended to explicitly set all fields that should be exposed using the fields attribute
    Args:
        model (models.Model): Django Model class. Will be set for 'ObjectType.Meta.model'
        fields (List[str], optional): list of fields as defined on 'ObjectType.Meta.fields'. Defaults to [] which internally defualts to '__all__'. 

        filter_fields (dict[str, list]): a dictionary of filter configurations that will be set on "'ObjectType.Meta.filter_fields'
        filterset_class (django_filters.FilterSet): A FilterSet class for filtering instead of filter_fields
        type_props (dict[str, Union[graphene.types.scalars.Scalar, Callable]], optional): a dictionary of attributes and methods that will be merged with the type. This should be used to provide custom fields and methods
        meta_props (dict[str, Any]): a dictionary that will be merged with class Meta: Defaults to {}. Used for Meta property overwrites or custom configurations, which is normally unnecessary.
    Returns:
        __type__ (Type[DjangoObjectType]): DjangoObjectType for given Django Model
    """


    merged_meta_kwargs = {
        "model": model,
        "fields": fields,
        "interfaces": (graphene.relay.Node, ),
        "filter_fields": filter_fields or {},
    }

    if filterset_class:
        merged_meta_kwargs["filterset_class"] = filterset_class
          
    class AbstractDjangoType(DjangoObjectType):
        class Meta:
            abstract =True

        # implement the get_queryset with permission checking
        @classmethod
        @queryset_permission_checker()
        def get_queryset(cls, queryset, info):
            if custom_get_queryset:
                return custom_get_queryset(cls, queryset, info)
            else:
                return super().get_queryset(queryset, info)

        # implement get_node with permission checking
        @classmethod
        @node_permission_checker()
        def get_node(cls, info, id):
            return super().get_node(info, id) # let graphene handle the id from_global_id

    AbstractDjangoType.permission_classes = permission_classes
    AbstractDjangoType.permissions = permissions
    
    # configure the meta
    meta = type("Meta", (),  merged_meta_kwargs)

    # configure the DjangoObjectType implementation
    django_node = type(f'{conventional_name}', (AbstractDjangoType,), {
        'Meta': meta,
    })
    return django_node
