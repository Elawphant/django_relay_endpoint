import graphene
from .node import NodeType
from typing import List

class AutoSchema:
    query: graphene.ObjectType
    mutation: graphene.ObjectType

    def __init__(self, node_types: List[NodeType]) -> None:
        instantiated_types = [node_type() for node_type in node_types]
        class Query(*[node_type.configure_queries() for node_type in instantiated_types], graphene.ObjectType): pass
        class Mutation(*[node_type.configure_mutations() for node_type in instantiated_types], graphene.ObjectType): pass
        self.query = Query
        self.mutation = Mutation

    def schema(self):
        return graphene.Schema(
            query=self.query, 
            mutation=self.mutation
            )
