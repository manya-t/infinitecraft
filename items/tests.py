from django.test import TestCase, Client
from .models import Item, InputDoesNotExist, Transformation, ItemPair
from .views import newTransformation, randomGap
from random import choice
from selenium import webdriver
from selenium.webdriver.common.by import By
import pathlib
import os

# Create your tests here.

""" def file_uri(filename):
    return pathlib.Path(os.path.abspath(filename)).as_uri()

# Sets up web driver using Google chrome
driver = webdriver.Chrome() """

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
            self.assertLessEqual(tr.input_pair.first_input.tier, tr.input_pair.second_input.tier)

    def test_simplest_tier_correct(self):
        for i in range(200):
            self.make_new_random_tr()
        all_items = Item.objects.all()
        for item in all_items:
            trs = list(item.as_output.all())
            if item.simplestWayToMake is None:
                self.assertEqual(item.tier, 1, f"\ntrs: {trs}\nitem: {item}")
            else:
                self.assertEqual(item.tier, item.simplestWayToMake.input_pair.second_input.tier+1, f"\ntrs: {trs}\nitem: {item}\nsimplest: {item.simplestWayToMake}")

    def test_simplest_is_simplest(self):
        for i in range(200):
            self.make_new_random_tr()
        all_tr = Transformation.objects.all()
        for tr in all_tr:
            tr_tier = tr.input_pair.second_input.tier + 1
            self.assertLessEqual(tr.output.tier, tr_tier)

    def test_gaps(self):
        message = newTransformation("root1", "root2", "next1")
        self.assertEqual(message, "New Item: next1 (2)<br>root1 (1) + root2 (1) = next1 (2)<br>root1 (1) + next1 (2) = ???<br>root2 (1) + next1 (2) = ???<br>next1 (2) + next1 (2) = ???<br>")
        message = newTransformation("next1", "root1", "next2")
        self.assertEqual(message, "New Item: next2 (3)<br>root1 (1) + next1 (2) = next2 (3)<br>root1 (1) + next2 (3) = ???<br>next1 (2) + next2 (3) = ???<br>next2 (3) + next2 (3) = ???<br>")
        gaps = Item.fetch("next1").gaps()
        pair1 = ItemPair.pairFromStrings("root2", "next1")
        pair2 = ItemPair.pairFromStrings("next1", "next1")
        pair3 = ItemPair.pairFromStrings("next1", "next2")
        self.assertEqual(gaps, [pair1, pair2, pair3])

    def test_index(self):
        c = Client()
        response = c.get("")
        self.assertEqual(response.status_code, 200)

    def test_item_page(self):
        c = Client()
        response = c.get("/item/1")
        self.assertEqual(response.status_code, 200)
        response = c.get("/item/root1")
        self.assertEqual(response.status_code, 200)

    """ def test_input_new_tr(self):
        path = r"items\templates\index.html"
        print(file_uri(path))
        driver.get(file_uri(path))
        first_input_field = driver.find_element(By.NAME, "first_input")
        second_input_field = driver.find_element(By.NAME, "second_input")
        output_field = driver.find_element(By.NAME, "output")
        first_input_field.send_keys("root1")
        second_input_field.send_keys("root2")
        output_field.send_keys("next1")
        driver.find_element(By.ID, "submitNew").click()
        next1 = Item.objects.get(name="next1")
        tr = Transformation.objects.get(first_input__name="root1", second_input__name="root2")
        self.assertEqual(tr, next1.simplestWayToMake) """
