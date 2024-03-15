from items.models import Transformation, Item, InputDoesNotExist
from items.views import newTransformation, checkForTransformation
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "add and modify transformations"

    def add_arguments(self, parser):
        parser.add_argument("action")
        parser.add_argument("first_input")
        parser.add_argument("second_input")
        parser.add_argument("output")
        parser.add_argument("--notReal", action="store_false")

    def handle(self, *args, **options):
        if (options["action"] == "new") or (options["action"] == "add"):
            newTransformation(options["first_input"], options["second_input"], options["output"], options["notReal"])
        elif options["action"] == "check":
            checkForTransformation(options["first_input"], options["second_input"])
        else:
            print(f"{options['action']} is not a valid action")


