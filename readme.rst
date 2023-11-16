=====
Django Graphene Endpoint
=====

"Django Graphene Endpoint" is a Django addon that automatically configures a graphql endpoint based on your models.
The addon is made for "graphene_django".

Quick start
-----------


1. Create your root fields from NodeFactory, e.g.
    from graphene_django_endpoint import NodeType
    from book.forms import BookForm
    from graphene.types.generic import GenericScalar

    class BookType(NodeType):
        # provide with your django model
        django_model_name_or_type='book.Book' # "app_name.ModelName" or ModelName
        # add fields to expose
        fields_config=['id', 'name', 'author', 'meta_info']
        # add filtering functionality
        filter_fields_config={
                'id': ('exact',),
                'name': ('iexact', 'icontains'),
                'author__id': ('exact',),
            }
        # optionally provide a custom form, if no form. If non is provided graphene_django_endpoint will create an internal one 
        model_form = BookForm
        # optionally specify custom field types for graphene. normally required for jsonfields
        field_types = {
            meta_info: GenericScalar()
        }
        # optionally list the supported mutations for current type. by default it will support all
        mutation_operations = ["create", "update", "delete", "bulk_create", "bulk_update", "bulk_delete"]

2. Declare your schema using SchemaFactory and providing your NodeTypes. e.g.
    schema = SchemaFactory([
            BookType,
            LibraryType,
            MembershipType]
        ).schema()


3. Register your schema with your urls.py, e.g.:
    from graphene_django.views import GraphQLView
    from graph_ql_api_v1.schema import schema
    from django.views.decorators.csrf import csrf_exempt
    from django.urls import path

    urlpatterns = [
        # ... other urls
        path("your_graphql_path", csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
    ]

4. Run the server and use the endpoint