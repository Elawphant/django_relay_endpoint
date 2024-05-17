from django.core.management.base import BaseCommand, CommandParser
from .boilerplate.boilers import validate_model, boil_endpoint
from pathlib import Path
import json, jsonschema
from .boilerplate.utils import schema


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
        parser.add_argument("--read", "-r", 
            type=str,
            required=True, 
            dest="file", 
            help="Read from json file"
            )
        

    def handle(self, *args, **options) -> str | None:
        file = open(Path(options['file']))
        print(file)
        try:
            json_schema = json.loads(file)
            jsonschema.validate(json_schema, schema)
        except ValueError as e:
            raise e
        for opts in json_schema['type_config']:
            opts['schema_app'] = json_schema['schema_app']
        for opts in json_schema['type_config']:
            validate_model(opts)
        for opts in json_schema['type_config']:
            # give granular control with overwriting
            if json_schema['overwrite'] is not None:
                opts['overwrite'] = json_schema['overwrite']
            boil_endpoint(opts)
        file.close()
        self.stdout.write(f"Endpoint successfully created")
