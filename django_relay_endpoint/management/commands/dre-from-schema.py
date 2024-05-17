from django.core.management.base import BaseCommand, CommandParser
from .boilerplate.boilers import validate_model, generate
from pathlib import Path
import json, jsonschema
from .boilerplate.utils import schema, defaults


class Command(BaseCommand):
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
        try:
            json_schema = json.loads(file.read())
            file.close()
            jsonschema.validate(json_schema, schema)
        except ValueError as e:
            raise e
        for opts in json_schema['type_config']:
            opts['schema_app'] = json_schema['schema_app']
        for opts in json_schema['type_config']:
            validate_model(opts)
            for key, value in defaults.items():
                if key != "overwrite" and opts.get(key, None) is None:
                    opts[key] = value
        for opts in json_schema['type_config']:
            # give granular control with overwriting
            if json_schema['overwrite'] is not None:
                opts['overwrite'] = json_schema['overwrite']
            generate(opts)
        self.stdout.write(f"Endpoint successfully created")
