
import graphene
from typing import Any
from django import forms
from django.utils.translation import gettext_lazy as _
import inspect
from django_relay_endpoint.configurators.field_conversions import MODEL_TO_SCALAR, configure_input_field
from graphene.types.generic import GenericScalar


class GenericDjangoInputField(graphene.InputField):
    """
    An abstract subclass of graphene.InputField that handles the data cleaning via django form field.
    """

    form_field: forms.Field

    class Meta:
        abstract = True
        form_field_class: type[forms.Field]

    def __init__(self, *args, **kwargs) -> None:
        if not self.Meta.form_field_class:
            raise AssertionError(
                "You must provide a form_field_class from django.forms")
        constructor_params = inspect.signature(
            self.Meta.form_field_class).parameters
        accepted_keys = constructor_params.keys()

        # get the default field configuration from models.Field
        params_from_model_field = {key: value for key,
                                   value in kwargs.items() if key in accepted_keys}
        merged_params = {**params_from_model_field}

        # overwrite with inputed kwargs
        for key, value in kwargs.items():
            if key in accepted_keys:
                merged_params[key] = value

        # instantiate a form field
        self.form_field = self.Meta.form_field_class(**merged_params)
        super().__init__(*args, **kwargs)

    def get_value(self, input) -> Any:
        """
        Does data cleaning via django form field 
        """

        return self.form_field.clean(super().get_value(input))


def configured(form_field_class: forms.Field, extra_kwargs: dict) -> None:
    conversion = configure_input_field(
        field=form_field_class, field_extra_kwargs=extra_kwargs)
    # fail silently to GenericScalar
    _type = MODEL_TO_SCALAR.get(form_field_class, GenericScalar)

    Meta = type("Meta", (), {
        "form_field_class": conversion
    })

    # cast to form field
    input_field_type = type(f"{form_field_class.__name__}InputField", (GenericDjangoInputField,), {
        "Meta": Meta
    })
    return input_field_type(_type, **extra_kwargs)
