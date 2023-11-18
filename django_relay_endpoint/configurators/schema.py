import graphene
from django_relay_endpoint.configurators.node import NodeType
from typing import List, Type

class SchemaConfigurator:
    """
    A class that configures schema.
    Must be instantiated with a list of classes extending NodeType
    Call SchemaConfigurator to return a configured graphene.Schema with queries and mutations
    """

    query: Type[graphene.ObjectType]
    mutation: Type[graphene.ObjectType]

    def __init__(self, node_types: List[Type[NodeType]]) -> None:
        instantiated_types = [node_type() for node_type in node_types]
        class Query(*[node_type.configure_queries() for node_type in instantiated_types], graphene.ObjectType): pass
        class Mutation(*[node_type.configure_mutations() for node_type in instantiated_types], graphene.ObjectType): pass
        self.query = Query
        self.mutation = Mutation

    def schema(self) -> graphene.Schema:
        """
        Configures a graphene.Schema from provided types

        Returns:
            graphene.Schema: the socnfigured schema.
        """
        return graphene.Schema(
            query=self.query, 
            mutation=self.mutation
            )
