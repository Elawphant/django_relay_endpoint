

import graphene
from django.db import models
from graphql_relay.node.node import from_global_id
from graphene_django import DjangoObjectType # This import is necessary. we export it in the model for easy of use
from django.utils.translation import gettext_lazy as _


class DjangoClientIDMutation(graphene.relay.ClientIDMutation):
    """
    An abstract subclass of graphene.relay.ClientIDMutation which implements 
    `get_queryset`, `get_node`, `create_node`, `validate` and `update_instance` classmethods.
    """

    class Meta:
        abstract=True

    @classmethod
    def get_queryset(cls, queryset: models.QuerySet, info: graphene.ResolveInfo,):
        """
        A get_queryset method for ClientIDMutation to support permission classes via cls.check_permissions
        When overwriting this method, you must call super or implement check_permissions manually.
        """
        return queryset

    @classmethod
    def get_node(cls, info, id):
        """
        Returns the node by id
        """
        queryset = cls.get_queryset(cls.model.objects, info)
        instance = queryset.get(id=id) # let graphene handle the DoesNotExist
        return instance

    @classmethod
    def create_node(cls, info):
        """
        Creates an unsaved model instance and checks permissions on it. If ok, returns the instance
        """
        instance = cls.model()
        return instance


    @classmethod
    def validate(cls, data: dict, not_updated_model_instance: models.Model, info: graphene.ResolveInfo):
        """
        Performs field and non_field validation.

        Args:
            data (dict): the data to be validated
            not_updated_model_instance (models.Model): initial instance state before saving.
            info (graphene.ResolveInfo): graphene info
        """
        for field in cls.model._meta.get_fields():
            field: models.Field = field

            for validator in cls.field_validators.get(field.name, []):
                validator(data.get(field.name), not_updated_model_instance, info)
        for validator in cls.non_field_validators:
            validator(data, not_updated_model_instance, info)

    @classmethod
    def update_instance(cls, instance: models.Model, data: dict):
        """
        Sets values from data on teh instance.
        For to-many relations uses add_<field_name> and remove_<field_name> to explicitly add or remove instances on the relations.

        Args:
            instance (models.Model): Django model instance to update
            data (dict): the data

        Raises:
            model.DoesNotExist: if an for non existing model instance is provided for relations. The error includes the problematic ids.
        """
        
        model = cls.model
        for field in cls.model._meta.get_fields():

            # disregard id 
            if field.name != "id":
                # check the field type, resolve m2m and reverse foreign keys via add_<field_name> and remove_<field_name> fields
                if field.is_relation: 
                    if field.many_to_one or field.many_to_many:
                        adders = data.get(f"add_{field.name}", [])
                        removers = data.get(f"remove_{field.name}", [])
                        if adders:
                            adder_instances = model._meta.get_field(field.name).related_model.objects.filter(id__in=[from_global_id(id).id for id in adders])
                            no_such_adders_error = _(f"{field.name} with ids: {', '.join([id for id in adders if id not in [i.id for i in adder_instances]])} do not exist")
                            if not adder_instances.exists():
                                raise model.DoesNotExist(no_such_adders_error)
                            getattr(instance, field.name).add(*adder_instances)
                        if removers:
                            remover_instances = model._meta.get_field(field.name).related_model.objects.filter(id__in=[from_global_id(id).id for id in removers])
                            no_such_removers_error = _(f"{field.name} with ids: {', '.join([id for id in adders if id not in [i.id for i in adder_instances]])} do not exist")
                            if not remover_instances.exists():
                                raise model.DoesNotExist(no_such_removers_error)
                            getattr(instance, field.name).remove(*remover_instances)
                    else:
                        if data.get(field.name, None):
                            related_object = model._meta.get_field(field.name).related_model.objects.get(id=from_global_id(data.get(field.name)).id)
                            setattr(instance, field.name, related_object)
                else:
                    # check if this field is in the arguments
                    if data.get(field.name, None):
                        setattr(instance, field.name, data.get(field.name))
