
from django.db import models
from django import forms
import graphene
from graphene_file_upload.scalars import Upload
from graphene.types.generic import GenericScalar  # Use this for json-field instead of graphene.JSONField which keeps the data as string
from typing import Type, Dict


MODEL_TO_FORM_FIELD = {
    models.BigIntegerField: forms.IntegerField,
    models.CharField: forms.CharField,
    models.DateField: forms.DateInput,
    models.DateTimeField: forms.DateTimeField,
    models.DecimalField: forms.DecimalField,
    models.DurationField: forms.DurationField,
    models.EmailField: forms.EmailField,
    models.FileField: forms.FileField,
    models.FilePathField: forms.FilePathField,
    models.ImageField: forms.ImageField,
    models.FloatField: forms.FloatField,
    models.IntegerField: forms.IntegerField,

    models.IPAddressField: forms.GenericIPAddressField,
    models.GenericIPAddressField: forms.GenericIPAddressField,

    models.JSONField: forms.JSONField,
    models.PositiveBigIntegerField: forms.IntegerField,
    models.PositiveIntegerField: forms.IntegerField,
    models.PositiveSmallIntegerField: forms.IntegerField,
    models.SlugField: forms.SlugField,
    models.SmallIntegerField: forms.IntegerField,
    models.TextField: forms.CharField,
    models.TimeField: forms.TimeField,
    models.URLField: forms.URLField,
    models.UUIDField: forms.UUIDField,
}

MODEL_TO_SCALAR = {
    models.BigIntegerField: graphene.BigInt,
    models.BooleanField: graphene.Boolean,
    models.CharField: graphene.String,
    models.DateField: graphene.Date,
    models.DateTimeField: graphene.DateTime,
    models.DecimalField: graphene.Float,
    models.DurationField: graphene.Int,

    models.EmailField: graphene.String,

    models.FileField: Upload,  # using graphene file upload
    models.ImageField: Upload,  # using graphene file upload
    models.FilePathField: graphene.String,

    models.FloatField: graphene.Float,

    models.IntegerField: graphene.Int,

    # implement custom scalar for IP addresses
    models.IPAddressField: graphene.String,
    models.GenericIPAddressField: graphene.String,

    models.JSONField: GenericScalar,
    models.PositiveBigIntegerField: graphene.BigInt,
    models.PositiveIntegerField: graphene.Int,
    models.PositiveSmallIntegerField: graphene.Int,
    models.SlugField: graphene.String,
    models.SmallIntegerField: graphene.Int,
    models.TextField: graphene.String,
    models.TimeField: graphene.Time,
    models.URLField: graphene.String,
    models.UUIDField: graphene.UUID,
}


def whichBooleanField(null = False):
    """
    Utility function for BooleanField conversion to BooleanField or NullBooleanField 
    """

    if null:
        return forms.NullBooleanField
    return forms.BooleanField


def configure_input_field(
        field: Type[models.Field], 
        field_extra_kwargs: Dict[str, dict] = {}, 
        ):
    """
    A utility function that maps the model field to the form field.

    Args:
        field (models.Field): a django model field
        custom_form_field_class (Type[forms.Field], optional): a custom form field class to supply custom field. Defaults to None.
        field_extra_kwargs (Dict[str, dict]): extra kwargs for the field. Used for BooleanField conversion to BooleanField or NullBooleanField
    """
    
    if issubclass(field, models.BooleanField):
        field_class = whichBooleanField(field_extra_kwargs.get("null", False))
    else:
        field_class = MODEL_TO_FORM_FIELD.get(field, None) or MODEL_TO_FORM_FIELD[models.CharField] # fail silently to Charfield
    return field_class
