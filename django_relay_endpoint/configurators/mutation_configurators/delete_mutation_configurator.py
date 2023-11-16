
import graphene
from django.utils.translation import gettext_lazy as _
from typing import Callable
from ..object_types import DjangoClientIDMutation

def configure_delete_mutation(
        abstract_mutation_type: type[DjangoClientIDMutation], 
        conventional_name: str,
    ) ->  type[DjangoClientIDMutation]:
    
    @classmethod
    def mutate_and_get_payload(cls, root, info, *args, **kwargs):
        client_mutation_id = kwargs.get("client_mutation_id", None) 
        id = kwargs.get("id")
        instance = cls.get_node(info, id)
        instance.delete()
        return cls(success=True, client_mutation_id=client_mutation_id)
    
    class Input:
        id = graphene.ID(required=True)

    mutation = type(f'{conventional_name}DeleteMutation', (abstract_mutation_type,), {
        'Input': Input,
        'mutate_and_get_payload': mutate_and_get_payload,
    })

    return mutation
