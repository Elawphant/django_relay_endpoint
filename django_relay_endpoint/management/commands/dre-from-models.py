from django.core.management.base import BaseCommand, CommandParser
from .boilerplate.boilers import validate_model, generate
from .boilerplate.utils import defaults



class Command(BaseCommand):
    help = "Generates graphene schema for given model"

    requires_migrations_checks = True

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("model", 
            type=str,
            help="The models to generate the schema for"
            )
        parser.add_argument("--in-app", '-in', 
            type=str,
            required=False, 
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
        validate_model(options)
        generate(options)
        self.stdout.write(f"Endpoint successfully created")


