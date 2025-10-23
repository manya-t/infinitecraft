from django.db import models
from django.db.models import Count, CharField
from django.db.models.functions import Length
from pyvis.network import Network
from itertools import combinations_with_replacement
import graphviz, graphviz.backend
import tempfile
import os

CharField.register_lookup(Length, 'length')

class PyvisConstants:
    COLOR_DEFAULT = "#B2C9AB"
    COLOR_NOT_REAL = "#6c757d"
    COLOR_HIGHLIGHT = "goldenrod"

class Item(models.Model):
    name = models.TextField(unique=True)
    emoji = models.TextField(null=True)
    timeCreated = models.DateTimeField(auto_now_add=True)
    timeUpdated = models.DateTimeField(auto_now=True)
    tier = models.IntegerField()
    isReal = models.BooleanField(default=True)
    simplestWayToMake = models.ForeignKey("items.Transformation", on_delete = models.SET_NULL, related_name = "is_simplest_to_make", null=True)
    canCombine = models.BooleanField(default=True)

    def __str__(self) -> str:
        emoji_string = self.emoji if self.emoji else ""
        return f"{emoji_string}{self.name} ({self.tier})"
    
    def makes(self):
        as_first = Transformation.objects.filter(input_pair__first_input=self)
        as_second = Transformation.objects.filter(input_pair__second_input=self)
        ordered = (as_first.all() | as_second.all()).order_by(
            "input_pair__second_input__tier", 
            "input_pair__first_input__tier", 
            "input_pair__first_input__name", 
            "input_pair__second_input__name")
        return ordered

    def related(self):
        return self.makes() | self.as_output.all()   
    
    def fetch(name):
        return Item.objects.get(name=name)
    
    def gaps(self):
        if self.isReal:
            qs = self.as_first_in_pair.filter(second_input__canCombine=True) | self.as_second_in_pair.filter(first_input__canCombine=True)
        elif not self.canCombine:
            qs  = ItemPair.objects.none()
        else:
            qs = self.as_first_in_pair.filter(second_input__isReal=True) | self.as_second_in_pair.filter(first_input__isReal=True)
        return qs.filter(as_inputs__isnull=True).order_by("second_input__tier", "first_input__tier")

    def makeAllGaps(self):        
        to_check = []

        for tr in self.makes():
            if tr.output.isReal:
                pair = ItemPair.getOrMakePairFromList([self, tr.output])
                if pair.from_AB_C is None:
                    pair.from_AB_C = tr
                    pair.save()
                to_check.append(pair)

        for tr in self.as_output.all():
            if tr.output.isReal:
                pair1 = ItemPair.getOrMakePairFromList([self, tr.input_pair.first_input])
                pair2 = ItemPair.getOrMakePairFromList([self, tr.input_pair.second_input])
                for pair in [pair1, pair2]:
                    if pair.from_AB_C is None:
                        pair.from_AB_C = tr
                        pair.save()
                    to_check.append(pair)
        
        square = ItemPair.getOrMakePairFromList([self,self])
        to_check.append(square)

        result = [pair for pair in to_check if pair.as_inputs.count()==0]
        return ItemPair.dedupeAndSortPairs(result)
    
    """ def gapFrom(first, second):
        firstAndOutput = Transformation.objects.filter(first_input__name=first, output__name=second)
        secondAndOutput = Transformation.objects.filter(second_input__name=first, output__name=second)
        outputAndFirst = Transformation.objects.filter(output__name=first, first_input__name=second)
        outputAndSecond = Transformation.objects.filter(output__name=first, second_input__name=second)
        return firstAndOutput.union(secondAndOutput).union(outputAndFirst).union(outputAndSecond) """

    def recursiveMake(self, minTier=1, currentResult=[]):
        if minTier < 1:
            print("That's going to make an infinite loop.")
            return currentResult
        elif self.tier <= minTier:
            return currentResult
        else:
            simplest = self.simplestWayToMake
            if simplest not in currentResult:
                currentResult.append(simplest)
                currentResult = simplest.input_pair.first_input.recursiveMake(minTier=minTier, currentResult=currentResult)
                currentResult = simplest.input_pair.second_input.recursiveMake(minTier=minTier, currentResult=currentResult)
            return currentResult

    def mostCommonOutput(self):
        outputs_by_freq = self.makes().values("output").annotate(freq=Count("output")).order_by("-freq", "output__tier","-output__isReal")
        if outputs_by_freq.count() == 0:
            return {"output":None, "freq":0, "item":None}
        else:
            most_common = outputs_by_freq[0]
            most_common['item'] = Item.objects.get(id=most_common['output'])
            return most_common
    
    def chainGraph(self, highlight=None):
        if highlight:
            to_highlight = highlight
        else:
            most_recent = Transformation.objects.all().order_by("-timeCreated")[0]
            to_highlight = [most_recent.input_pair.first_input, most_recent.input_pair.second_input, most_recent.output]
        makes_trs = self.makes()
        pyvis = (makes_trs.count()<300)
        
        if pyvis:
            net = Network(directed=True)
        else:
            graph = graphviz.Digraph(format='svg', engine='sfdp')
            graph.attr(size="12,12")

        for tr in makes_trs:
            if tr.input_pair.first_input == self:
                other_input = tr.input_pair.second_input
            else:
                other_input = tr.input_pair.first_input
            
            color_input = PyvisConstants.COLOR_DEFAULT
            color_output = PyvisConstants.COLOR_DEFAULT
            if other_input in to_highlight:
                color_input = PyvisConstants.COLOR_HIGHLIGHT
            if tr.output in to_highlight:
                color_output = PyvisConstants.COLOR_HIGHLIGHT
            if not other_input.isReal:
                color_input = PyvisConstants.COLOR_NOT_REAL
            if not tr.output.isReal:
                color_output = PyvisConstants.COLOR_NOT_REAL

            if pyvis:
                net.add_node(other_input.id, label=str(other_input), shape="ellipse", color=color_input)
                net.add_node(tr.output.id, label=str(tr.output), shape="ellipse", color=color_output)
                net.add_edge(other_input.id, tr.output.id)
            else:
                graph.node(str(other_input.id), label=str(other_input), style="filled", fillcolor=color_input)
                graph.node(str(tr.output.id), label=str(tr.output), style="filled", fillcolor=color_output)
                graph.edge(str(other_input.id), str(tr.output.id))

        if pyvis:     
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
                temp_path = temp_file.name
            net.write_html(temp_path)
            with open(temp_path, 'r') as file:
                result = file.read()
            os.remove(temp_path)
        else:
            print("Graphviz DOT path:", graphviz.backend.GRAPHVIZ_DOT)
            print("Current PATH:", os.environ.get('PATH'))
            result = graph.pipe(format='svg').decode('utf-8')

        return result


    def name_wo_special_char(self):
        clean_name = self.name.replace("?","%3F").replace("/", "%2F").replace("\\", "%5c")
        reserved = ["CON", "PRN", "AUX", "NUL", "COM0", "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", 
                    "COM¹", "COM²", "COM³", "LPT0", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9", "LPT¹", 
                    "LPT²", "LPT³"]
        if clean_name.upper() in reserved:
            clean_name = clean_name + "-unreserved"
        return clean_name
    
    def list_by_emoji(self):
        if self.emoji is None:
            raise Exception(f"No emoji found for {self}")
        return list(Item.objects.filter(emoji=self.emoji, isReal=True).order_by("tier","name").all())
    
    def report_pairs(self, item_list):
        results = []
        for item in item_list:
            ordered_pair = ItemPair.orderItems([item,self])
            try:
                result = ItemPair.objects.get(first_input=ordered_pair[0], second_input=ordered_pair[1])
            except ItemPair.DoesNotExist:
                result = f"Pair {ordered_pair[0]} + {ordered_pair[1]} does not exist"
            results.append(result)
        return results

    def no_pair(self):
        items = Item.objects.filter(isReal=1).order_by("tier","name")
        for item in items:
            try:
                ordered = ItemPair.orderItems([item, self])
                ItemPair.objects.get(first_input=ordered[0], second_input=ordered[1])
            except:
                return item

    # to undo a tr that made a bad tier update     
    def updateTier(self):
        """
        Updates the tier of the output item if a simpler transformation is found, 
        recursively updates related transformations, and returns a list of changes made.
        """
        self.tier = 100
        all_ways_to_make =  self.as_output.all()
        self.simplestWayToMake = all_ways_to_make[0]
        changes = []

        for tr in all_ways_to_make:
            changes.extend(tr.updateTier())

        item_list = Item.objects.none()
        for tr in self.makes():
            item_list = item_list | tr.is_simplest_to_make.all()

        for i in item_list:
            changes.extend(i.updateTier())
        return changes

class InputDoesNotExist(Item.DoesNotExist):
    def __init__(self, name, *args: object) -> None:
        msg = f"Input ({name}) does not exist. Enter a transformation that fixes that and then try again."
        super().__init__(msg, *args)

class Transformation(models.Model):
    """
    Represents a transformation from a pair of input items to an output item.

    Note:
        The fields `first_input` and `second_input` are deprecated and kept for legacy support.
        Use `input_pair` instead for all new code.
    """
    # DEPRECATED: first_input and second_input are legacy fields, use input_pair instead
    first_input = models.ForeignKey(Item, on_delete = models.CASCADE, related_name = "as_first_input", null=True) 
    second_input = models.ForeignKey(Item, on_delete = models.CASCADE, related_name = "as_second_input", null=True)
    input_pair = models.ForeignKey("items.ItemPair", on_delete = models.CASCADE, related_name = "as_inputs")
    output = models.ForeignKey(Item, on_delete = models.CASCADE, related_name = "as_output")
    timeCreated = models.DateTimeField(auto_now_add=True)
    timeUpdated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("input_pair",), name="unique_transformation_inputs")
        ]

    def __str__(self) -> str:
        return f"{self.input_pair.first_input} + {self.input_pair.second_input} = {self.output}"
             
    def updateTier(self):
        changes = []

        # this SHOULD always be the second one, but just in case
        trTier = max(self.input_pair.first_input.tier, self.input_pair.second_input.tier) + 1
        output = self.output

        if trTier < output.tier:
            change = {"item_changed": output, 
                      "old_tier": output.tier,
                      "old_simplest": output.simplestWayToMake,
                      "new_tier": trTier,
                      "new_simplest": self}
            changes.append(change)
            
            output.tier = trTier
            output.simplestWayToMake = self
            output.save()

            for pair in output.as_first_in_pair.all() | output.as_second_in_pair.all():
                pair.checkOrder()
                try:
                    tr = Transformation.objects.get(input_pair=pair)
                    changes.extend(tr.updateTier())
                except (Transformation.DoesNotExist):
                    pass
        return changes

    def export(self):
        return f"{self.input_pair.second_input}->{self.input_pair.first_input}->{self.output}"
    
    def makeGapPairs(self):
        pairsToCheck = [[self.input_pair.first_input, self.output], 
                         [self.input_pair.second_input, self.output],
                         [self.output, self.output]]
        for pair_list in pairsToCheck:
            pair = ItemPair.getOrMakePairFromList(pair_list)
            if pair.from_AB_C is None:
                    pair.from_AB_C = self
                    pair.save()
        return self

    
class ItemPair(models.Model):
    first_input = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="as_first_in_pair")
    second_input = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="as_second_in_pair")
    from_AB_C = models.ForeignKey(Transformation, on_delete=models.SET_NULL, related_name="to_other_pair", null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("first_input", "second_input"), name="unique_pair")
        ]

    def __str__(self) -> str:
        try:
            output_string = self.as_inputs.get().output
        except Transformation.DoesNotExist:
            output_string = "???"
        return f"{self.first_input} + {self.second_input} = {output_string}"
    
    @staticmethod
    def fetch(str1, str2):
        try:
            return ItemPair.objects.get(first_input__name=str1, second_input__name=str2)
        except:
            return ItemPair.objects.get(first_input__name=str2, second_input__name=str1)
    @staticmethod
    def pairFromStrings(first_input, second_input):
        item_list = []
        for name in [first_input, second_input]:
            try:
                item_list.append(Item.objects.get(name=name))
            except Item.DoesNotExist:
                raise InputDoesNotExist(name=name)
        pair = ItemPair.getOrMakePairFromList(item_list)
        return pair
        return pair
    @staticmethod
    def getOrMakePairFromList(item_list):
        item_list = ItemPair.orderItems(item_list)
        try:
            pair = ItemPair.objects.get(first_input=item_list[0], second_input=item_list[1])
        except ItemPair.DoesNotExist:
            pair = ItemPair(first_input=item_list[0], second_input=item_list[1])
            pair.save()
        return pair
        return pair
    
    @staticmethod
    def orderItems(item_list):
        item_list.sort(key= lambda item: (item.tier, item.name))
        return item_list

    @staticmethod
    def dedupeAndSortPairs(pair_list):
        pair_list = list(set(pair_list))
        pair_list = ItemPair.sortListOfPairs(pair_list)
        return pair_list
    
    @staticmethod
    def sortListOfPairs(pair_list):
        pair_list.sort(key = lambda pair: (pair.second_input.tier, pair.first_input.tier, pair.second_input.name, pair.first_input.name))
        return pair_list
    
    def checkOrder(self):
        ordered = ItemPair.orderItems([self.first_input, self.second_input])
        if self.first_input == ordered[0] and self.second_input == ordered[1]:
            return self
        else:
            self.first_input = ordered[0]
            self.second_input = ordered[1]
            self.save()

    def following(self):
        if self.from_AB_C is None:
            return None
        prev_input_pair = self.from_AB_C.input_pair
        if self.first_input in [prev_input_pair.first_input, prev_input_pair.second_input]:
            return self.first_input
        elif self.second_input in [prev_input_pair.first_input, prev_input_pair.second_input]:
            return self.second_input
        else:
            return None
        
    def report_pairs(item_list):
        results = []
        for item in item_list:
            results += item.report_pairs(item_list)
        return results