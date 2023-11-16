
from typing import Dict, Any
from django.core.exceptions import ValidationError


@classmethod
def validate(cls, data: Dict[str, Any]):
    """Performs field and non-field validation, by running the supplied validators
    Valdator args are current field value and the whole data

    Args:
        data (Dict[str, Any]): data to validate

    Raises:
        ValidationError: A validation error if validation fails.
    """
    # skip id
    fields_to_validate = [
        field for field in cls.Meta.model._meta.get_fields() if field.name != "id" and field.name != "pk"]

    # perform field validation
    field_errors = {}
    for field in fields_to_validate:
        validators = cls.Meta.field_validators.get(field.name, [])
        current_field_errors = []
        if validators:
            for validator in validators:
                try:
                    validator(data.get(field.name), data)
                except ValidationError as err:
                    field_errors.append({field.name: err})
        if current_field_errors:
            if not field_errors.get(field.name, None):
                field_errors[field.name] = current_field_errors

    # perform non-field validation
    non_field_errors = []
    for validator in cls.Meta.non_field_validators:
        try:
            validator(data)
        except ValidationError as err:
            non_field_errors.append(err)
    if field_errors or non_field_errors:
        raise ValidationError(
            {"field-errors": field_errors, "non-field-errors": non_field_errors})
