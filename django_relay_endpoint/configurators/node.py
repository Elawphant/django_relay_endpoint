
import graphene
from django.db import models
from django.forms import Field
from graphene_django import DjangoObjectType
from typing import Any, List, Dict, Literal, Union, TypedDict, Callable, Type
from django.apps import apps

from django_relay_endpoint.configurators.object_type_configurator import configure_node_object_type
from django_relay_endpoint.configurators.queries_configurator import configure_queries
from django_relay_endpoint.configurators.mutation_configurators.create_mutation_configurator import configure_create_mutation
from django_relay_endpoint.configurators.mutation_configurators.update_mutation_configurator import configure_update_mutation
from django_relay_endpoint.configurators.mutation_configurators.delete_mutation_configurator import configure_delete_mutation
from django_relay_endpoint.configurators.mutation_configurators.abstract_mutation_class_configurator import configure_abstract_mutation
from django_relay_endpoint.configurators.mutation_configurators.input_object_type_configurator import configure_input_object_type
from django_relay_endpoint.configurators.object_types import DjangoClientIDMutation
from django_relay_endpoint.configurators.permissions import BasePermission
from django_filters import FilterSet, OrderingFilter
from .permissions import assert_permissions_are_valid, assert_permission_classes_are_valid


class MutationConfig(TypedDict):
    graphene_field_kwargs: Dict[str, Any]
    validators: List[Callable]
    graphene_input_field: str
    form_field: Field
    scalar_type: graphene.Scalar


class MetaKwargs(TypedDict):
    model: Union[str, Type[models.Model]]
    fields: List[str] | Literal["__all__"]
    query_root_name: str | None
    query_root_name_plural: str | None
    filter_fields: Union[Dict[str, List[str]], List[str]]
    filterset_class: Type[FilterSet]
    object_type_name: str | None
    mutation_operations: Literal["create", "update", "delete"]
    extra_kwargs: Dict[str, Dict[str, Any]]
    field_validators: Dict[str, List[Callable]]
    non_field_validators: List[Callable]
    success_keyword: str
    input_field_name: str
    return_field_name: str
    get_queryset: Callable
    permissions: List[str]
    permission_classes: List[Type[BasePermission]]


DEFAULT_META_KWARGS: MetaKwargs = {
    'model':  None,
    'fields': [],
    'query_root_name': None,
    'query_root_name_plural':  None,
    'filter_fields': {},
    'filterset_class': None,
    'mutation_operations': ["create", "update", "delete"],
    'object_type_name': None,
    'extra_kwargs': {},
    'success_keyword': None,
    'field_validators': {},
    'non_field_validators': [],
    'input_field_name': None,
    'return_field_name': None,
    "permissions": [],
    "permission_classes": []
}


class NodeType:
    model: Type[models.Model]
    conventional_name: str
    django_object_type: Type[DjangoObjectType]
    input_object_type: graphene.InputObjectType
    django_abstract_mutation_type: Type[DjangoClientIDMutation]

    class Meta:
        abstract = True

    def __init_subclass__(cls) -> None:
        """
        Ensures the class is subclassed properly 

        Raises:
            AssertionError: if the class is not subclassed properly. 
            See assertion errors in the code for more details
        """
        if cls is not NodeType and not issubclass(cls, NodeType):
            raise AssertionError(
                "NodeType is intended to be used as base class for creating subclasses! ")
        if not cls.Meta.model:
            raise AssertionError(
                f"Django model or '<app_label.model_name> should be provided on {cls.__name__}.Meta.model'")
        if not cls.Meta.fields:
            raise AssertionError(
                f"You must explicitly provide the list of fields (List[str]) or Literal['__all__']")
        for key, default in DEFAULT_META_KWARGS.items():
            if not getattr(cls.Meta, key, None):
                setattr(cls.Meta, key, default)
        assert_permissions_are_valid(cls.Meta.permissions)
        assert_permission_classes_are_valid(cls.Meta.permission_classes)

    def __init__(self) -> None:
        self.__prepare_model_class__()
        self.__configure_conventional_name__()
        if self.Meta.fields == '__all__':
            fields = [field.name for field in self.model._meta.get_fields()]
        else:
            fields = self.Meta.fields
        
        self.fields = fields

        self.django_object_type = configure_node_object_type(
            model=self.model,
            conventional_name=self.conventional_name,
            fields=fields,
            filter_fields=self.Meta.filter_fields,
            filterset_class=self.Meta.filterset_class,
            custom_get_queryset=self.__class__.get_queryset if hasattr(self.__class__, 'get_queryset') else None,
            permissions=self.Meta.permissions,
            permission_classes=self.Meta.permission_classes,
        )
        self.input_object_type = configure_input_object_type(
            model=self.model,
            conventional_name=self.conventional_name, 
            fields=fields, 
            extra_kwargs=self.Meta.extra_kwargs,
        )
        self.django_abstract_mutation_type = configure_abstract_mutation(
            django_object_type=self.django_object_type,
            conventional_name=self.conventional_name,
            permissions=self.Meta.permissions,
            permission_classes=self.Meta.permission_classes
        )

        

    def __prepare_model_class__(self) -> None:
        """
        Retrieves the django model class and assigns it to self.model.
        """

        if isinstance(self.Meta.model, str):
            description = self.Meta.model.split('.')
            django_model = apps.get_model(description[0], description[1])
        elif issubclass(self.Meta.model, models.Model):
            django_model = self.Meta.model
        else:
            raise AssertionError("Django model or '<app_label.model_name> should be provided on {cls.__name__}.Meta.model'")
        self.model = django_model

    def __configure_conventional_name__(self) -> str:
        """Returns a conventional name for object type made from django model's app_label and model_name

        Returns:
            str: a prefix name made form django model's app_label and model_name
        """
        if hasattr(self.Meta, "object_type_name") and self.Meta.object_type_name:
            self.conventional_name = self.Meta.object_type_name
        else:
            self.conventional_name = f'{self.model._meta.app_label.capitalize()}{self.model._meta.model_name.capitalize()}'

    def configure_queries(self) -> Type[graphene.ObjectType]:
        """Configures the graphene query object types for single and multiple records.

        Returns:
            graphene.ObjectType: The configured grpahene query ObjectType
        """
        return configure_queries(
            django_object_type=self.django_object_type,
            conventional_name=self.conventional_name,
            query_field_name=self.Meta.query_root_name_plural,
        )

    def configure_mutations(self) -> Type[graphene.ObjectType]:
        """
        Configures mutations with "create_<model._meta.model_name>", "update_<model._meta.model_name>", "delete_<model._meta.model_name>" root fields per Meta.mutation_operations.

        Returns:
            Type[graphene.ObjectType]: A configured extended graphene.ObjectType with mutation root fields
        """
        root = {}
        if "create" in self.Meta.mutation_operations:
            
            create_mutation = configure_create_mutation(
                input_object_type=self.input_object_type,
                abstract_mutation_type=self.django_abstract_mutation_type,
                conventional_name=self.conventional_name,
                input_field_name=self.Meta.input_field_name,
                return_field_name=self.Meta.return_field_name,
                success_keyword=self.Meta.success_keyword
            )
            root[f"create_{self.model._meta.model_name}"] = create_mutation.Field()

        if "update" in self.Meta.mutation_operations:
            update_mutation = configure_update_mutation(
                input_object_type=self.input_object_type,
                abstract_mutation_type=self.django_abstract_mutation_type,
                conventional_name=self.conventional_name,
                input_field_name=self.Meta.input_field_name,
                return_field_name=self.Meta.return_field_name,
                success_keyword=self.Meta.success_keyword
            )
            root[f"update_{self.model._meta.model_name}"] = update_mutation.Field()

        if "delete" in self.Meta.mutation_operations:
            delete_mutation = configure_delete_mutation(
                abstract_mutation_type=self.django_abstract_mutation_type,
                conventional_name=self.conventional_name,
                success_keyword=self.Meta.success_keyword
                )
            root[f"delete_{self.model._meta.model_name}"] = delete_mutation.Field()

        return type(f'{self.conventional_name}Mutation', (graphene.ObjectType, ), root)
