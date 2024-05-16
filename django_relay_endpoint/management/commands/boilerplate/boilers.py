import textwrap
from django.apps import apps
from .utils import pascal_case, snake_case, name_class, name_module
from pathlib import Path
from typing import Literal
from django.db import models

FORM_SUFFIX = "ModelForm"
INPUT_TYPE_SUFFIX = "InputType"
CREATE_PREFIX = "Create"
UPDATE_PREFIX = "Create"
INPUT_SUFFIX = "Input"
MUTATION_SUFFIX = "Mutation"
QUERY_SUFFIX = "Query"
NODE_SUFFIX = "Node"


mutate_and_get_payload_create = """
        data = kwargs.get("data", None)
        client_mutation_id = kwargs.get("client_mutation_id", None)
        if data.get("id", None):
            raise ValidationError(_("A client must not provide an id for new resources"))

        instance = cls.create_node(info)
        cls.validate(data, instance, info)
        cls.update_instance(instance, data)
        instance.save()
        mutation_kwargs = {{
            '{return_field_name}': instance,
            'success_keyword' or "success": True,
            'client_mutation_id': client_mutation_id
        }}
        return cls(**mutation_kwargs)
"""

mutate_and_get_payload_update = """
        data = kwargs.get("data", None)
        client_mutation_id = kwargs.get("client_mutation_id", None)
        unresolved_id = data.get("id", None)
        # raise error if no id was provided
        if not unresolved_id:
            raise ValidationError(_("You must provide the id of the instance being mutated."))
        id = from_global_id(unresolved_id).id
        instance = cls.get_node(info, id)
        cls.validate(data, instance, info)
        cls.update_instance(instance, data)
        instance.save()
        mutation_kwargs = {{
            '{return_field_name}': instance,
            'success': True,
            'client_mutation_id': client_mutation_id
        }}
        return cls(**mutation_kwargs)
"""

mutate_and_get_payload_delete = """
        client_mutation_id = kwargs.get("client_mutation_id", None) 

        # use from_global_id inside mutate_and_get_payload to ensure it is similar to graphene_django.DjangoObjectType implementation
        id = from_global_id(kwargs.get("id")).id
        
        instance = cls.get_node(info, id)
        instance.delete()
        mutation_kwargs = {{
            'success': True,
            'client_mutation_id': client_mutation_id
        }}
        return cls(**mutation_kwargs)
"""


def boil_form(app_label: str, modelname: str, fields: list[str], purpose: Literal['Create', 'Update']):
    """
        Returns a content of a form module
    """

    content = textwrap.dedent(
        f"""
        from django import forms
        from {app_label}.models import {modelname}

        class {pascal_case(modelname, purpose, FORM_SUFFIX)}(forms.ModelForm):
            class Meta:
                model = {modelname}
                fields = {fields}
        """
    )
    return content


def boil_node(app_label: str, modelname: str, fields: list[str]):
    """
        Returns a content of a node module
    """

    content = textwrap.dedent(
        f"""
        from {app_label}.models import {modelname}
        from graphene import relay
        from graphene_django import DjangoObjectType

        class {name_class(modelname, suffix=NODE_SUFFIX)}(DjangoObjectType):
            class Meta:
                model = {modelname}
                fields = {fields}
                filter_fields = {{}}
                interfaces = (relay.Node, )
        """
    )
    return content


def boil_query(app_label: str, modelname: str, schema_app_dir: Path):
    """
        Returns a content of a query module
    """
    connection_field_name = snake_case(apps.get_model(
        app_label, modelname)._meta.verbose_name_plural)

    node_name = name_class(modelname, suffix=NODE_SUFFIX)

    content = textwrap.dedent(
        f"""
        from graphene import ObjectType
        from graphene_django.filter import DjangoFilterConnectionField
        from {app_label}.models import {modelname}
        from {schema_app_dir.name}.nodes.{name_module(modelname, '', NODE_SUFFIX)} import {node_name}

        class {name_class(modelname, suffix=QUERY_SUFFIX)}(ObjectType):
            {connection_field_name} = DjangoFilterConnectionField({node_name})
        """
    )
    return content


def boil_input_type(app_label: str, modelname: str, purpose: Literal['Create', 'Update', 'Delete'], fields=["__all__"]):
    """
        Returns a content of a input_type module
    """

    model = apps.get_model(app_label, modelname)

    input_fields = ""
    for field in model._meta.get_fields():
        if field.name in fields:
            # cast for better typing
            field: models.Field = field

            # create "add_<fieldname>" and "remove_<fieldname>" fields for hasMany relations
            if field.is_relation:
                if field.many_to_many or field.many_to_one:
                    input_fields += f"    add_{field.name} = graphene.List(graphene.ID, **Meta.extra_kwargs.get('{field.name}', {{}}))\n"
                    input_fields += f"    remove_{field.name} = graphene.List(graphene.ID, **Meta.extra_kwargs.get('{field.name}', {{}}))\n"
                else:
                    input_fields += f"    {field.name} = graphene.ID(**Meta.extra_kwargs.get('{field.name}', {{}}))\n"
            else:
                if field.name == "id":
                    # omit id for Create operations, because id is generated on server side
                    if purpose != "Create":
                        input_fields += f"    {field.name} = graphene.ID()\n"
                else:
                    # extend GenericDjangoInputField which casts graphene fields to form-fields for inputted data cleanup and validation
                    input_fields += f"    {field.name} = configured(forms.{field.__class__.__name__}, **Meta.extra_kwargs.get('{field.name}', {{}}))\n"

    content = f"""
import graphene
{'''
from django_relay_endpoint.configurators.fields import configured
from django import forms 
''' if purpose != "Delete" else ""}

class {name_class(modelname, prefix=purpose, suffix=INPUT_TYPE_SUFFIX)}(graphene.InputObjectType):
    class Meta:
        extra_kwargs = {{}}

{input_fields}
"""
    return content


def boil_mutation(app_label: str, modelname: str, schema_app_dir: Path, purpose: Literal['Create', 'Update', 'Delete']):
    """
        Returns a content of a mutation module
    """

    input_type_name = name_class(
        modelname, prefix=purpose, suffix=INPUT_TYPE_SUFFIX)
    node_name = name_class(modelname, suffix=NODE_SUFFIX)

    mutator_methods = {
        "Create": mutate_and_get_payload_create,
        "Update": mutate_and_get_payload_update,
        "Delete": mutate_and_get_payload_delete
    }

    content = f"""
import graphene
from {app_label}.models import {modelname}
from {schema_app_dir.name}.nodes.{name_module(modelname, '', 'node')} import {node_name}
from {schema_app_dir.name}.input_types.{name_module(modelname, purpose, INPUT_TYPE_SUFFIX)} import {input_type_name}
{'''
from graphql_relay.node.node import from_global_id
''' if purpose != "Create" else ""}
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_relay_endpoint.configurators.object_types import DjangoClientIDMutation

class {name_class(modelname, prefix=purpose, suffix=MUTATION_SUFFIX)}(DjangoClientIDMutation):
    model = {modelname}
    class Input:
        data = graphene.Field({input_type_name})

    {snake_case(modelname)} = graphene.Field({node_name})

    @classmethod
    def mutate_and_get_payload(cls, root, info, *args, **kwargs):
    {mutator_methods[purpose].format(return_field_name=snake_case(modelname)) if purpose != "Delete" else mutator_methods[purpose]}

    class Meta:
        input_field_name = 'data'
        return_field_name = '{modelname}'
"""
    return content


def boil_schema():
    """
        Returns a content of a schema module
    """

    return textwrap.dedent("""
    import graphene

    # Add your queries here
    class Query(graphene.ObjectType):
        pass
    
    # Add your mutations here
    class Mutation(graphene.ObjectType):
        pass
    
    # Add your subscriptions here
    class Subscription(graphene.ObjectType):
        pass
    
    schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription)

    """)

def boil_endpoint(schema_app_dir: Path):
    """
        Returns a content of a urls module
    """
    return textwrap.dedent(f"""
    from django.urls import path
    from django.views.decorators.csrf import csrf_exempt
    from graphene_django.views import GraphQLView
    from {schema_app_dir.name}.schema import schema

    urlpatterns = [
        path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
    ]
    """)


def select_fields(model: models.Model, fields:list[str]):
    condition_error = "'fields' must be string '__all__' or a list of fieldnames"
    field_error = "No such field '{name}' for model {model__class__name__}"
    if isinstance(fields, list) and len(fields) == 1 and fields[0] == '__all__':
        return [field.name for field in model._meta.get_fields()]
    elif isinstance(fields, list) and all(isinstance(field, str) for field in fields):
        model_fields = [field.name for field in model._meta.get_fields()]
        for name in fields:
            if name not in model_fields:
                raise ValueError(field_error.format(name=name, model__class__name__=model._meta.model_name))
        return fields
    else:
        raise ValueError(condition_error)