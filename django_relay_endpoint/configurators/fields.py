
import graphene
from typing import Any
from django import forms
from django.utils.translation import gettext_lazy as _
import inspect



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
            raise AssertionError("You must provide a form_field_class from django.forms")
        constructor_params = inspect.signature(self.Meta.form_field_class).parameters
        accepted_keys = constructor_params.keys()

        # get the default field configuration from models.Field
        params_from_model_field = {key: value for key, value in kwargs.items() if key in accepted_keys}
        merged_params = {**params_from_model_field}

        #overwrite with inputed kwargs
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

    
