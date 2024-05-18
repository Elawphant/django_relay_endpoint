from django.core.management.base import BaseCommand, CommandParser
from .boilerplate.boilers import validate_model, generate
from pathlib import Path
import json, jsonschema
from .boilerplate.utils import schema, defaults, SUCCESS_MESSAGE


class Command(BaseCommand):
    """
    A class that generates graphene schema for given json file.

    Attributes:
        help (str): A description of the command's purpose.
        requires_migrations_checks (bool): Indicates whether migrations checks are required.

    Methods:
        add_arguments(parser: CommandParser) -> None:
            Adds command line arguments to the parser.

        handle(*args, **options) -> str | None:
            Handles the execution of the command.

            Args:
                *args: Variable length argument list.
                **options: Keyword arguments.

            Returns:
                str | None: The result of the command execution.
    """
    help = "Generates graphene schema for given models from json file"

    requires_migrations_checks = True

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Adds single command line argument to the parser for reading the file.

        Parameters:
            parser (CommandParser): The parser object to which the arguments will be added.

        Returns:
            None

        Raises:
            None
        """
        parser.add_argument("--read", "-r", 
            type=str,
            required=True, 
            dest="file", 
            help="Read from json file"
            )
        

    def handle(self, *args, **options) -> None:
        """
        Handles the execution of the command by validating the schema, 
        apps and models and generating the necessary modules in the provided schema_app.
        """
        file = open(Path(options['file']))
        try:
            json_schema = json.loads(file.read())
            file.close()
            jsonschema.validate(json_schema, schema)
        except (ValueError, jsonschema.ValidationError) as e:
            raise e
        type_config = json_schema.get('type_config', [])
        schema_app = json_schema.get('schema_app')
        overwrite = json_schema.get('overwrite', None)
        # Using multiple loops is intentinal, we want to configure and validate everything before generating the schema
        for opts in type_config:
            opts['schema_app'] = schema_app
        for opts in type_config:
            validate_model(opts)
            for key, value in defaults.items():
                if key != "overwrite" and opts.get(key, None) is None:
                    opts[key] = value
        for opts in type_config:
            # give granular control with overwriting
            if overwrite is not None:
                opts['overwrite'] = overwrite
            generate(opts)
        self.stdout.write(SUCCESS_MESSAGE.format(schema_app=schema_app))
