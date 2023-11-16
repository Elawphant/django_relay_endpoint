
import graphene
from typing import List, Dict
from django.db import models
from graphql_relay.node.node import from_global_id
from django.utils.translation import gettext_lazy as _
from ..fields import GenericDjangoInputField
from ..field_conversions import MODEL_TO_FORM_FIELD, MODEL_TO_SCALAR
from ..object_types import DjangoClientIDMutation

def configure_input_object_type(
    abstract_mutation_type: DjangoClientIDMutation,
    fields: List[str] = [],
    extra_kwargs: Dict[str, dict] = {},
    ) -> graphene.InputObjectType:

    model: models.Model = abstract_mutation_type.model
    # generate an InputObjectType for our fields
    input_fields = {
    }
    for field in model._meta.get_fields():
        field_kwargs = extra_kwargs.get(field.name, {})
        if field.name != "id":
            field_kwargs['required'] = field_kwargs.get('required', not field.null and not field.blank)
        else:
            field_kwargs['required'] = field_kwargs.get('required', False)
        if field.name in fields:
            field: models.Field = field
            
            # create "add_<fieldname>" and "remove_<fieldname>" fields for hasMany relations 
            if field.is_relation:
                if field.many_to_many or field.many_to_one:
                    input_fields[f"add_{field.name}"] = graphene.List(graphene.ID, **field_kwargs)
                    remove_kwargs = {**field_kwargs}
                    remove_kwargs["required"] = False
                    input_fields[f"remove_{field.name}"] = graphene.List(graphene.ID, **remove_kwargs)
                else:
                    input_fields[field.name] = graphene.ID(**field_kwargs)
            else:
                # extend GenericDjangoInputField which casts graphene fields to form-fields for inputted data cleanup and validation
                conversion = MODEL_TO_FORM_FIELD.get(field.__class__, None) or MODEL_TO_FORM_FIELD[models.CharField] # fail silently to Charfield
                _type = MODEL_TO_SCALAR.get(field.__class__, None) or graphene.types.generic.GenericScalar

                # cast to form field
                input_field_type = type(f"", (GenericDjangoInputField,), {
                        "Meta": type("Meta", (), {
                            "form_field_class": conversion
                        })
                    })
                input_fields[field.name] = input_field_type(_type, **field_kwargs)

    # define an input object type with fields
    InputObjectType = type(f"{abstract_mutation_type.django_object_type.__name__}Input", (graphene.InputObjectType,), input_fields)
    
    return InputObjectType
