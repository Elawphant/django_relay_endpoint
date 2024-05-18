from django.core.management.base import BaseCommand, CommandParser
from .boilerplate.boilers import validate_model, generate
from .boilerplate.utils import defaults, SUCCESS_MESSAGE



class Command(BaseCommand):
    """
    Generates graphene schema for a given model.

    This class is a Django management command that generates a graphene schema for a specified model. 
    It uses the `validate_model` and `generate` functions from the `boilers.py` module to perform the schema generation.

    Attributes:
        help (str): A brief description of the command's purpose.
        requires_migrations_checks (bool): Indicates whether the command requires migration checks.

    Methods:
        add_arguments(parser: CommandParser) -> None:
            Adds command line arguments to the command parser.

        handle(*args, **options) -> str | None:
            Executes the command's logic. Calls the `validate_model` and `generate` functions, and outputs a success message.

        validate_model(options: dict) -> None:
            Validates the specified model and its associated app configurations.

        generate(options: dict) -> None:
            Generates the graphene schema based on the specified options.

    """
    help = "Generates graphene schema for given model"

    requires_migrations_checks = True

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Adds command line arguments to the command parser.
        "model": dot-separate app_label and model class name, e.g. 'app.Model'
        "--in-app", "-in": the django app where to generate the schema models in
        "--overwrite", "-owt": whether to overwrite the modeles o not, defaults to False
        "--query", "-q": whether to generate query modules or not, defaults to True
        "--query-fields", "-qf": a list of of fields to configure, if none provided, all model fields will be configured
        "--create-mutation", "-cm": whether to generate mutation modules for creation, defaults to True
        "--create-mutation-fields", "-cmf": the list of fields to configure, if none provided, all model fields will be configured
        "--update-mutation", "-um": whether to generate mutation modules for updating, defaults to True
        "--update-mutation-fields", "-umf": the list of fields to configure, if none provided, all model fields will be configured
        "--delete-mutation", "-dm": whether to generate mutation modules for deletion, defaults to True
        """

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
            default=defaults.get("overwrite"), 
            dest="overwrite", 
            help="Overwrite existing files"
            )
        parser.add_argument("--query", "-q", 
            type=bool,
            required=False, 
            default=defaults.get("query"),
            dest="query", 
            help="Generate the query module"
            )
        parser.add_argument(
            "--query-fields", "-qf", 
            type=list[str],
            required=False, 
            default=defaults.get("query_fields"), 
            dest="query_fields",
            nargs='*',
            help="The queryable fields to include"
            )
        parser.add_argument("--create-mutation", "-cm", 
            type=bool,
            required=False, 
            default=defaults.get("create_mutation"), 
            dest="create_mutation", 
            help="Generate the create mutation module"
            )
        parser.add_argument(
            "--create-mutation-fields", "-cmf",
            type=list[str],
            required=False, 
            default=defaults.get("create_mutation_fields"), 
            dest="create_mutation_fields",
            nargs='*',
            help="The mutation fields to include"
            )
        parser.add_argument("--update-mutation", "-um", 
            type=bool,
            required=False, 
            default=defaults.get("update_mutation"), 
            dest="update_mutation", 
            help="Generate the update mutation module"
            )
        parser.add_argument("--update-mutation-fields", "-umf",
            type=list[str],
            required=False, 
            default=defaults.get("update_mutation_fields"), 
            dest="update_mutation_fields",
            nargs='*',
            help="The mutation fields to include"
            )
        parser.add_argument("--delete-mutation", "-dm", 
            type=bool,
            required=False, 
            default=defaults.get("delete_mutation"), 
            dest="delete_mutation", 
            help="Generate the delete mutation module"
            )        

    def handle(self, *args, **options) -> None:
        """
        Handles the creation of a schema for the given model
        """
        validate_model(options)
        generate(options)
        self.stdout.write(SUCCESS_MESSAGE.format(schema_app=options.get("schema_app")))


