from django.core.management.base import BaseCommand, CommandError, CommandParser
from pathlib import Path
from .boilerplate.utils import (
    create_directory,
    create_module,
    pascal_case,
    name_module
)
from .boilerplate.boilers import (
    boil_node,
    boil_query,
    boil_input_type,
    boil_mutation,
    boil_schema,
    boil_endpoint,
    select_fields
)
from django.apps import apps
import json, jsonschema


schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "model": {
        "type": "string",
        "description": "The model to generate the schema for"
      },
      "schema_app": {
        "type": "string",
        "description": "The app to place the generated files in"
      },
      "overwrite": {
        "type": "boolean",
        "description": "Overwrite existing files",
      },
      "query": {
        "type": "boolean",
        "description": "Generate the query module",
      },
      "query_fields": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "The queryable fields to include",
      },
      "create_mutation": {
        "type": "boolean",
        "description": "Generate the create mutation module",
      },
      "create_mutation_fields": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "The mutation fields to include",
      },
      "update_mutation": {
        "type": "boolean",
        "description": "Generate the update mutation module",
      },
      "update_mutation_fields": {
        "type": "array",
        "items": {
          "type": "string"
        },
        "description": "The mutation fields to include",
      },
      "delete_mutation": {
        "type": "boolean",
        "description": "Generate the delete mutation module",
      }
    },
    "required": ["model", "schema_app"]
  }
}

defaults = {
    "overwrite": False,
    "query": True,
    "create_mutation": True,
    "update_mutation": True,
    "delete_mutation": True,
    "query_fields": ["__all__"],
    "create_mutation_fields": ["__all__"],
    "update_mutation_fields": ["__all__"],
}



class Command(BaseCommand):
    """
    The Command class is a subclass of BaseCommand and represents a Django management command. It generates a graphene schema for a given model.

    Attributes:
        help (str): A string representing the help message for the command.
        requires_migrations_checks (bool): A boolean indicating whether the command requires migrations checks.

    Methods:
        add_arguments(parser: CommandParser) -> None:
            Adds command line arguments to the command parser.

        handle(*args: Any, **options: Any) -> str | None:
            Executes the command logic.

        validate_input(options):
            Validates the input options for the command.

        boil_endpoint(options):
            Generates the necessary modules for the GraphQL endpoint.

    """
    help = "Generates graphene schema for given model"

    requires_migrations_checks = True

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("model", 
            type=str, 
            help="The model to generate the schema for"
            )
        parser.add_argument("--in-app", '-in', 
            type=str,
            required=True, 
            dest="schema_app", 
            help="The app to place the generated files in"
            )
        parser.add_argument("--overwrite", "-owt", 
            type=bool,
            required=False, 
            default=defaults["overwrite"], 
            dest="overwrite", 
            help="Overwrite existing files"
            )
        parser.add_argument("--query", "-q", 
            type=bool,
            required=False, 
            default=defaults["query"], 
            dest="query", 
            help="Generate the query module"
            )
        parser.add_argument(
            "--query-fields", "-qf", 
            type=list[str],
            required=False, 
            default=defaults["query_fields"], 
            dest="query_fields",
            nargs='*',
            help="The queryable fields to include"
            )
        parser.add_argument("--create-mutation", "-cm", 
            type=bool,
            required=False, 
            default=defaults["create_mutation"], 
            dest="create_mutation", 
            help="Generate the create mutation module"
            )
        parser.add_argument(
            "--create-mutation-fields", "-cmf",
            type=list[str],
            required=False, 
            default=defaults["create_mutation_fields"], 
            dest="create_mutation_fields",
            nargs='*',
            help="The mutation fields to include"
            )
        parser.add_argument("--update-mutation", "-um", 
            type=bool,
            required=False, 
            default=defaults["update_mutation"], 
            dest="update_mutation", 
            help="Generate the update mutation module"
            )
        parser.add_argument("--update-mutation-fields", "-umf",
            type=list[str],
            required=False, 
            default=defaults["update_mutation_fields"], 
            dest="update_mutation_fields",
            nargs='*',
            help="The mutation fields to include"
            )
        parser.add_argument("--delete-mutation", "-dm", 
            type=bool,
            required=False, 
            default=defaults["delete_mutation"], 
            dest="delete_mutation", 
            help="Generate the delete mutation module"
            )
        parser.add_argument("--read", "-r", 
            type=str,
            required=False, 
            dest="file", 
            help="Read from json file"
            )
        

    def handle(self, *args, **options) -> str | None:
        if options['file']:
            if options.__len__() > 2 and options["overwrite"] is False:
                raise ValueError("Reading from file supports only file path and --overwrite arguments")
            file = open(Path(options['file']))
            try:
                json_objects = json.loads(file)
            except ValueError as e:
                raise e
            for opts in json_objects:
                self.validate_input(opts)
            for opts in json_objects:
                # give granular control with overwriting
                if options['overwrite'] and opts['overwrite'] is None:
                    opts['overwrite'] = options['overwrite']
                self.boil_endpoint(opts)
            file.close()
        else:   
            self.validate_input(options)
            self.boil_endpoint(options)


    def validate_input(self, options):
        [app_label, modelname] = model.split(".")
        schema_app = options["schema_app"]

        try:
            apps.get_app_config(app_label)
            apps.get_app_config(schema_app)
        except (LookupError, ImportError) as e:
            raise CommandError(
                f"{e}. Are you sure your INSTALLED_APPS setting is correct?"
            )
        try:
            model = apps.get_model(app_label, modelname)
        except LookupError as e:
            raise CommandError(e)

    def boil_endpoint(self, options):
        model = options["model"]

        [app_label, modelname] = model.split(".")
        schema_app = options["schema_app"]
        
        overwrite = options["overwrite"]
        query = options["query"]
        query_fields = select_fields(model, options["query_fields"]) if query else []
        create_mutation = options["create_mutation"]
        create_mutation_fields = select_fields(model, options["create_mutation_fields"]) if create_mutation else []
        update_mutation = options["update_mutation"]
        update_mutation_fields = select_fields(model, options["update_mutation_fields"]) if update_mutation else []
        delete_mutation = options["delete_mutation"]

        schema_app_dir = Path(schema_app)

        [create_directory(schema_app_dir / foldername) for foldername in ["nodes", "queries", "input_types", "mutations"]]

        pascal_name = pascal_case(modelname)

        node_content = boil_node(app_label, modelname, query_fields)
        create_module(name_module(pascal_name, '', "node"), Path(schema_app_dir / "nodes"), node_content, overwrite)

        if query:
            query_content = boil_query(app_label, modelname, schema_app_dir)
            create_module(name_module(pascal_name, '', "query"), Path(schema_app_dir / "queries"), query_content, overwrite)

        mutations = {
            "create": "Create" if create_mutation else False,
            "update": "Update" if update_mutation else False,
            "delete": "Delete" if delete_mutation else False,
        }

        fields = {
            "create": create_mutation_fields,
            "update": update_mutation_fields,
            "delete": ['id'],
        }

        for key, value in mutations.items():
            if value:
                input_type_content = boil_input_type(
                    app_label, modelname, value, fields[key])
                mutation_content = boil_mutation(
                    app_label, modelname, schema_app_dir, value)
                create_module(name_module(pascal_name, key, "input_type"), Path(schema_app_dir / "input_types"), input_type_content, overwrite)
                create_module(name_module(pascal_name, key, "mutation"), Path(schema_app_dir / "mutations"), mutation_content, overwrite)

        create_module("urls", schema_app_dir, boil_endpoint(schema_app_dir), False)
        create_module("schema", schema_app_dir, boil_schema(), False)
        self.stdout.write(f"Created modules for {model} in {schema_app_dir}")
