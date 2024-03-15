import csv
from django.core.management.base import BaseCommand, CommandError
from .add_tr import newTransformation

class Command(BaseCommand):
    help = "import csv of transformations"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)

    def handle(self, *args, **options):
        file_path = options["file_path"]
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                isReal = (row["real"]=="TRUE")
                newTransformation(row["first_input"], row["second_input"], row["output"], isReal)