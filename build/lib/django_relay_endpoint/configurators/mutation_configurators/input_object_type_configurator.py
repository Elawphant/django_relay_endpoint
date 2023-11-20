
import graphene
from typing import List, Dict, Type
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_relay_endpoint.configurators.fields import GenericDjangoInputField
from django_relay_endpoint.configurators.field_conversions import MODEL_TO_SCALAR, configure_input_field
from graphene.types.generic import GenericScalar

def configure_input_object_type(
    model: Type[models.Model],
    conventional_name: str,
    fields: List[str] = [],
    extra_kwargs: Dict[str, dict] = {},
    ) -> Type[graphene.InputObjectType]:
    """
    Configures a graphene.InputObjectType with given fields and extra_kwargs.
    !Important, this class does not implement id. An id field must explicitly added for update and delete mutations.
    It casts all Input arguments into GenericDjangoInputField and graphene.List(graphene.ID, **field_extra_kwargs) for to-many relations. 
    This ensures that graphene scalars also behave as Django form fields.
    For to-many relations, it constructs add_<field_name> and remove_<field_name> input fields, instead of just using field_name. 
    This is a design preference to explicitly request which related resources need to be added and which ones need to be removed, 
    insteead of just setting all the related resources: the latter can be a huge list. 
    N.B. it was decided to opt out from DjangoFormMutation, because it did not correspond relay style mutation and 
    for the design choice with to-many relations 

    Args:
        model (Type[models.Model]): 
        Django model for field reference. 

        conventional_name (str):
        a conventional prefix for outputted graphene.InputObjectType

        fields (List[str], optional): 
        the list of fields. Defaults to [].

        extra_kwargs (Dict[str, dict], optional): 
        a dictionary where keys are field names and values are extra kwargs that will be passed to the fields.
        It is similar to extra_kwargs on Django Form. Defaults to {}.

    Returns:
        Type[graphene.InputObjectType]: the InputObjectType used for create and update mutation types
    """
    # generate an InputObjectType for our fields
    input_fields = {
        'model': model,
        'Meta': type("Meta", (), {
            'model': model,
        })
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
                conversion = configure_input_field(field = field.__class__, field_extra_kwargs=field_kwargs)
                _type = MODEL_TO_SCALAR.get(field.__class__, GenericScalar) # fail silently to GenericScalar

                GenericDjangoInputFieldMeta = type("Meta", (), {
                    "form_field_class": conversion
                })

                # cast to form field
                input_field_type = type(f"{field.__class__.__name__}", (GenericDjangoInputField,), {
                        "Meta": GenericDjangoInputFieldMeta
                    })
                input_fields[field.name] = input_field_type(_type, **field_kwargs)

    # define an input object type with the fields
    InputObjectType = type(f"{conventional_name}Input", (graphene.InputObjectType,), input_fields)
    
    return InputObjectType
