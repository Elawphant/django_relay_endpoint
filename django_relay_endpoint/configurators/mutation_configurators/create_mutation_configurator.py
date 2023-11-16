import graphene
from django.db import models
from django.utils.translation import gettext_lazy as _
from ..object_types import DjangoClientIDMutation



def configure_create_mutation(
        input_object_type: type[graphene.InputObjectType],
        abstract_mutation_type: type[DjangoClientIDMutation], 
        conventional_name: str,
        input_field_name: str = None,
        return_field_name: str = None,
        ) -> type[graphene.InputObjectType]:
    
    @classmethod
    def mutate_and_get_payload(cls, root, info, *args, **kwargs):
        model = abstract_mutation_type.model
        data = kwargs.get(input_field_name or "data", None)
        client_mutation_id = kwargs.get("client_mutation_id", None) 
        # id = data.get("id", None)
        # if id:
        #     raise Exception(_("Field 'id' should not be provided when creating new objects. Instead you can provide a 'ClientMutationId' to identify the response"))
        instance = cls.create_node()
        cls.validate(data, instance, info)
        cls.update_instance(instance, data)
        instance.save()
        mutation_kwargs = {return_field_name or model._meta.model_name: instance}
        return cls(**mutation_kwargs, success=True, client_mutation_id=client_mutation_id)
    
    Input = type("Input", (), {
        input_field_name or "data" : graphene.Field(input_object_type)
    })

    mutation = type(f'{conventional_name}CreateMutation', (abstract_mutation_type,), {
        "Input": Input,
        "mutate_and_get_payload": mutate_and_get_payload,
    })
    return mutation



