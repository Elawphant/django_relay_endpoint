from typing import Any
from django.core.management.base import BaseCommand, CommandError, CommandParser
from pathlib import Path
from .utils import (
    create_directory,
    create_module,
    pascal_case,
    snake_case
)
from .boilers import (
    boil_node,
    boil_query,
    boil_input_type,
    boil_mutation,
    boil_schema,
    boil_endpoint
)
from django.apps import apps



class DREBoil(BaseCommand):
    """
    The `DREBoilCommand` class is a Django management command that generates a graphene schema for a given model. It creates various modules for nodes, queries, input types, mutations, and the schema itself.

    Example Usage:
        python manage.py dreboil myapp.MyModel --in-app=schema_app --query --create-mutation --update-mutation --delete-mutation

    This command generates the graphene schema for the `MyModel` model in the `myapp` app. It places the generated files in the `schema_app` app. It generates the query module, create mutation module, update mutation module, and delete mutation module.

    Main functionalities:
    - Generates a node module that defines a GraphQL node for a given model.
    - Generates a query module that defines a GraphQL query for a given model.
    - Generates an input type module that defines a GraphQL input type for create, update, and delete mutations for a given model.
    - Generates a mutation module that defines create, update, and delete mutations for a given model.
    - Generates a schema module that defines the GraphQL schema.
    - Generates an endpoint module that defines the GraphQL endpoint URL.

    Methods:
    - `add_arguments(parser: CommandParser) -> None`: Adds command line arguments to the command parser.
    - `handle(*args: Any, **options: Any) -> str | None`: Executes the command logic. Generates the graphene schema based on the provided options.

    Fields:
    - `help`: A help message for the command.
    - `requires_migrations_checks`: Indicates whether the command requires migrations checks.
    - `model`: The model to generate the schema for.
    - `schema_app`: The app to place the generated files in.
    - `overwrite`: Indicates whether to overwrite existing files.
    - `query`: Indicates whether to generate the query module.
    - `query_fields`: The queryable fields to include.
    - `create_mutation`: Indicates whether to generate the create mutation module.
    - `create_mutation_fields`: The mutation fields to include for create mutations.
    - `update_mutation`: Indicates whether to generate the update mutation module.
    - `update_mutation_fields`: The mutation fields to include for update mutations.
    - `delete_mutation`: Indicates whether to generate the delete mutation module.
    """
    help = "Generates graphene schema for given model"

    requires_migrations_checks = True

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("model", type=str,
                            required=True, dest="model", help="The model to generate the schema for")
        parser.add_argument("--in-app", '-in', type=bool,
                            required=True, dest="schema_app", help="The app to place the generated files in")
        parser.add_argument("--overwrite", "-owt", type=bool,
                            required=False, default=False, dest="overwrite", help="Overwrite existing files")
        parser.add_argument("--query", "-q", type=bool,
                            required=False, default=True, dest="query", help="Generate the query module")
        parser.add_argument("--query-fields", "-qf", type=list[str],
                            required=False, default=["__all__"], dest="query_fields", help="The queryable fields to include")
        parser.add_argument("--create-mutation", "-cm", type=bool,
                            required=False, default=True, dest="create_mutation", help="Generate the create mutation module")
        parser.add_argument("--create-mutation-fields", "-cmf",
                            type=list[str], required=False, default=['__all__'], dest="create_mutation_fields", help="The mutation fields to include")
        parser.add_argument("--update-mutation", "-um", type=bool,
                            required=False, default=True, dest="update_mutation", help="Generate the update mutation module")
        parser.add_argument("--update-mutation-fields", "-umf",
                            type=list[str], required=False, default=['__all__'], dest="update_mutation_fields", help="The mutation fields to include")
        parser.add_argument("--delete-mutation", "-dm", type=bool,
                            required=False, default=True, dest="delete_mutation", help="Generate the delete mutation module")

    def handle(self, *args: Any, **options: Any) -> str | None:
        [
            model,
            schema_app,
            overwrite,
            query,
            query_fields,
            create_mutation,
            create_mutation_fields,
            update_mutation,
            update_mutation_fields,
            delete_mutation
        ] = options

        [app_label, modelname] = model.split(".")

        try:
            apps.get_app_config(app_label)
            apps.get_app_config(schema_app)
        except (LookupError, ImportError) as e:
            raise CommandError(
                f"{e}. Are you sure your INSTALLED_APPS setting is correct?"
            )
        try:
            apps.get_model(app_label, modelname)
        except LookupError as e:
            raise CommandError(e)

        schema_app_dir = Path(schema_app)

        create_directory(schema_app_dir / "nodes")
        create_directory(schema_app_dir / "queries")
        create_directory(schema_app_dir / "input_types")
        create_directory(schema_app_dir / "mutations")

        pascal_name = pascal_case(modelname)
        snake_name = snake_case(pascal_name)

        node_content = boil_node(
            pascal_name, model, query_fields)
        create_module(snake_name + "_node",
                      Path(schema_app_dir / "nodes"), node_content, overwrite)

        if query:
            query_content = boil_query(model, schema_app_dir)
            create_module(snake_name + "_query",
                          Path(schema_app_dir / "queries"), query_content, overwrite)

        mutations = {
            "create": "Create" if create_mutation else False,
            "update": "Update" if update_mutation else False,
            "delete": "Delete" if delete_mutation else False,
        }

        fields = {
            "create": create_mutation_fields,
            "update": update_mutation_fields,
            "delete": [],
        }

        for key, value in mutations.items():
            if value:
                input_type_content = boil_input_type(
                    app_label, modelname, value, fields[key])
                mutation_content = boil_mutation(
                    app_label, modelname, schema_app_dir, value)
                create_module(snake_name + f"_{key}_input_type", Path(
                    schema_app_dir / "input_types"), input_type_content, overwrite)
                create_module(snake_name + f"_{key}_mutation", Path(
                    schema_app_dir / "mutations"), mutation_content, overwrite)

        create_module("urls", schema_app_dir,
                      boil_endpoint(schema_app_dir), False)
        create_module("schema", schema_app_dir, boil_schema(), False)
