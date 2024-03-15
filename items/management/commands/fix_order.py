from django.core.management.base import BaseCommand, CommandError
from items.models import Transformation, Item

class Command(BaseCommand):
    help = "re-order transformations that are out of order"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        allTr = Transformation.objects.all()
        for tr in allTr:
            ordered = Item.orderItems([tr.first_input, tr.second_input])
            if ordered[0] != tr.first_input:
                tr.first_input = ordered[0]
                tr.second_input = ordered[1]
                tr.save()
                print(f"Switched order of {tr}")