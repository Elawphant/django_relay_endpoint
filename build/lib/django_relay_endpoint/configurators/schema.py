import graphene
from django_relay_endpoint.configurators.node import NodeType
from typing import List, Type


class NodeType(graphene.ObjectType):
    node = graphene.relay.Node.Field()

class SchemaConfigurator:
    """
    A class that configures schema.
    Must be instantiated with a list of classes extending NodeType
    Call SchemaConfigurator to return a configured graphene.Schema with queries and mutations
    """

    query: List[graphene.ObjectType]
    mutation: List[graphene.ObjectType]
    node_type: graphene.ObjectType = NodeType

    def __init__(self, node_types: List[Type[NodeType]]) -> None:
        instantiated_types = [node_type() for node_type in node_types]
        self.query = [node_type.configure_queries() for node_type in instantiated_types]
        self.mutation = [node_type.configure_mutations() for node_type in instantiated_types]

    def schema(self) -> graphene.Schema:
        """
        Configures a graphene.Schema from provided types

        Returns:
            graphene.Schema: the socnfigured schema.
        """
        class Query(*self.query, self.node_type, graphene.ObjectType): 
            node = graphene.relay.Node.Field()

            # @classmethod
            # def resolve_node(cls, root, info, id):
            #     from graphql_relay.node.node import from_global_id

            #     model, id = from_global_id(id)
            #     print(model, id)
            #     # Implement your logic to fetch the object by ID here
            #     return None

            class Meta:
                interfaces = (graphene.relay.Node,)
            
        class Mutation(*self.mutation, graphene.ObjectType): pass
        return graphene.Schema(
            query=Query, 
            mutation=Mutation
            )
