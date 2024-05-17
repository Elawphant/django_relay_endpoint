from django.core.management.base import BaseCommand, CommandParser
from .boilerplate.boilers import validate_model, boil_endpoint
from .boilerplate.utils import defaults



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
        parser.add_argument("models", 
            nargs="*",
            type=list[str],
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
        models = options['models']
        for model in models:
            validate_model(model)
        for model in models:
            options['model'] = model
            boil_endpoint(options)
        self.stdout.write(f"Endpoint successfully created")


