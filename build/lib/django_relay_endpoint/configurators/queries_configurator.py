
import graphene
from graphene_django.filter import DjangoFilterConnectionField
from typing import Literal
from .object_types import DjangoObjectType
from typing import Type


def configure_queries(
    django_object_type: Type[DjangoObjectType],
    conventional_name: str,
    query_field_name: str = None,
    query_field_name_plural: str = None,
    query_operations: Literal["list", "detail"] = ["list", "detail"],
    ) -> Type[graphene.ObjectType]:
    """
    Configures relay node style query object type for single and multiple records, supports filtering via django_filter 

    Returns:
    Args:
        django_object_type (DjangoObjectType): The object type top generate queries from
        conventional_name (str): A name to use for the query object type
        query_field_name (str, optional): the field name. Defaults to None. If None, lowered snake-case model._meta.verbose_name will be used
        query_field_name_plural (str, optional): _description_. Defaults to None. If None, lowered snake-case model._meta.verbose_name_plural will be used

    Returns:
        graphene.ObjectType: The created query object type
    """

    model = django_object_type._meta.model
    name = query_field_name or model._meta.verbose_name.strip().replace(' ', '_').lower()
    name_plural = query_field_name_plural or model._meta.verbose_name_plural.strip().replace(' ', '_').lower()

    
    roots = {}

    if "detail" in query_operations:
        roots[name] = graphene.relay.Node.Field(django_object_type)
    
    if "list" in query_operations:
        roots[name_plural] = DjangoFilterConnectionField(django_object_type)

    query = type(f'{conventional_name}Query', (graphene.ObjectType, ), roots)
    return query
