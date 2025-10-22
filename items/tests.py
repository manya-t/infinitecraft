from django.test import TestCase, Client
from .models import Item, InputDoesNotExist, Transformation, ItemPair
from .views import newTransformation, randomGap
from random import choice
#from selenium import webdriver
#from selenium.webdriver.common.by import By
#import pathlib
#import os

# Create your tests here.

""" def file_uri(filename):
    return pathlib.Path(os.path.abspath(filename)).as_uri()

# Sets up web driver using Google chrome
driver = webdriver.Chrome() """

class ItemsTestCase(TestCase):
    def setUp(self):
        for i in range(2):
            Item(name=i, tier=1).save()
        newTransformation("1","1","2")
        newTransformation("1","2","3")
    
    def test_print(self):
        i = Item.objects.get(name="0")
        self.assertEqual(str(i), "0 (1)")

    def test_makes(self):
        i = Item.objects.get(name="1")
        tr_queryset = Transformation.objects.all()
        self.assertQuerySetEqual(i.makes(), tr_queryset)

    def test_makes_empty(self):
        i = Item.objects.get(name="0")
        self.assertQuerySetEqual(i.makes(), Transformation.objects.none())

    def test_related(self):
        pass

    def test_fetch(self):
        i = Item.objects.get(name="0")
        self.assertEqual(i, Item.fetch("0"))

    def test_gaps(self):
        item = Item.objects.get(name="3")
        gaps = [
            ItemPair.fetch("1","3"),
            ItemPair.fetch("2","3"),
            ItemPair.fetch("3","3")
            ]
        self.assertEqual(list(item.gaps()), gaps)
    
    def test_gaps_if_not_real(self):
        pass

class MiscTestCase(TestCase):
    def setUp(self):
        for i in range(2):
            Item(name=i, tier=1).save()
        newTransformation("0","1","2")

    def test_last_item(self):
        last_item = Item.objects.get(id=3)
        self.assertEqual(last_item.name,"2")
        self.assertEqual(last_item.tier,2)
    
    def test_simplest_set(self):
        last_item = Item.objects.get(id=3)
        simplest = last_item.simplestWayToMake
        correct = Transformation.objects.filter(input_pair__first_input__name="0",
                                                input_pair__second_input__name="1")[0]
        self.assertEqual(simplest,correct)
    
    def test_new_tr_return(self):
        result = newTransformation("1","2","3")
        self.assertTrue(result["success"])
        self.assertTrue(result["new_item"])
        self.assertEqual(result["changes"], [])
        self.assertEqual(result["tr"], Transformation.objects.get(id=2))

    def test_already_exists(self):
        result = newTransformation("0","1","2")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"],"This transformation already exists! 0 (1) + 1 (1) = 2 (2)")

    def test_exists_with_diff_output(self):
        result = newTransformation("0","1","3")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"],"The database says this transformation has a result of 2 and not 3, please check again.")

    def test_input1_invalid(self):
        result = newTransformation("3","1","2")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], 'Input (3) does not exist. Enter a transformation that fixes that and then try again.')

    def test_input2_invalid(self):
        result = newTransformation("0","3","2")
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], 'Input (3) does not exist. Enter a transformation that fixes that and then try again.')

    def test_second_tier_higher(self):
        pass

    def test_simplest_tier_correct(self):
        pass

    def test_index(self):
        c = Client()
        response = c.get("")
        self.assertEqual(response.status_code, 200)

    """def test_item_page(self):
        c = Client()
        response = c.get("/item/1")
        self.assertEqual(response.status_code, 200)
        response = c.get("/item/root1")
        self.assertEqual(response.status_code, 200)
    """
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
