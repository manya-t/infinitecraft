from django.test import TestCase
from .models import Item, InputDoesNotExist, Transformation
from .views import newTransformation, randomGap
from random import choice

# Create your tests here.

class ItemsTestCase(TestCase):

    def setUp(self):
        Item(name='root1', tier=1).save()
        Item(name='root2', tier=1).save()
        Item(name='root3', tier=1).save()
    
    def make_new_random_tr(self):
        all_items = Item.objects.all()
        num_items = all_items.count()
        randNum1 = choice(range(num_items))
        randNum2 = choice(range(num_items))
        name1 = all_items[randNum1].name
        name2 = all_items[randNum2].name
        output = str(choice(range(200)))
        newTransformation(name1, name2, output)

    def test_items_unique(self):
        for i in range(100):
            self.make_new_random_tr()
        all_items = Item.objects.all()
        for item in all_items:
            num = Item.objects.filter(name=item.name).count()
            self.assertEqual(num, 1, item)
        
    def test_second_tier_higher(self):
        for i in range(100):
            self.make_new_random_tr()
        all_tr = Transformation.objects.all()
        for tr in all_tr:
            self.assertLessEqual(tr.first_input.tier, tr.second_input.tier)

    def test_simplest_tier_correct(self):
        for i in range(200):
            self.make_new_random_tr()
        all_items = Item.objects.all()
        for item in all_items:
            trs = list(item.as_output.all())
            if item.simplestWayToMake is None:
                self.assertEqual(item.tier, 1, f"\ntrs: {trs}\nitem: {item}")
            else:
                self.assertEqual(item.tier, item.simplestWayToMake.second_input.tier+1, f"\ntrs: {trs}\nitem: {item}\nsimplest: {item.simplestWayToMake}")

    def test_simplest_is_simplest(self):
        for i in range(200):
            self.make_new_random_tr()
        all_tr = Transformation.objects.all()
        for tr in all_tr:
            tr_tier = tr.second_input.tier + 1
            self.assertLessEqual(tr.output.tier, tr_tier)

    def test_gaps(self):
        message = newTransformation("root1", "root2", "next1")
        self.assertEqual(message, "New Item: next1 (2)<br>root1 (1) + root2 (1) = next1 (2)<br>root1 (1) + next1 (2) = ???<br>root2 (1) + next1 (2) = ???<br>next1 (2) + next1 (2) = ???<br>")
        message = newTransformation("next1", "root1", "next2")
        self.assertEqual(message, "New Item: next2 (3)<br>root1 (1) + next1 (2) = next2 (3)<br>root1 (1) + next2 (3) = ???<br>next1 (2) + next2 (3) = ???<br>next2 (3) + next2 (3) = ???<br>")
        gaps = Item.fetch("next1").gaps()
        self.assertEqual(gaps, "root2 (1) + next1 (2) = ???<br>next1 (2) + next1 (2) = ???<br>next1 (2) + next2 (3) = ???<br>")