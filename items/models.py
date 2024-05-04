from django.db import models

# Create your models here.
class Item(models.Model):
    name = models.TextField(unique=True)
    emoji = models.TextField(null=True)
    timeCreated = models.DateTimeField(auto_now_add=True)
    timeUpdated = models.DateTimeField(auto_now=True)
    tier = models.IntegerField()
    isReal = models.BooleanField(default=True)
    simplestWayToMake = models.ForeignKey("items.Transformation", on_delete = models.SET_NULL, related_name = "is_simplest_to_make", null=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.tier})"
    
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
                simplest.input_pair.first_input.recursiveMake(minTier=minTier, currentResult=currentResult)
                simplest.input_pair.second_input.recursiveMake(minTier=minTier, currentResult=currentResult)
            currentResult = list(set(currentResult))
            return currentResult

    
class InputDoesNotExist(Item.DoesNotExist):
    def __init__(self, name, *args: object) -> None:
        msg = f"Input ({name}) does not exist. Enter a transformation that fixes that and then try again."
        super().__init__(msg, *args)

class Transformation(models.Model):
    first_input = models.ForeignKey(Item, on_delete = models.CASCADE, related_name = "as_first_input", null=True) 
    second_input = models.ForeignKey(Item, on_delete = models.CASCADE, related_name = "as_second_input", null=True)
    input_pair = models.ForeignKey("items.ItemPair", on_delete = models.CASCADE, related_name = "as_inputs")
    output = models.ForeignKey(Item, on_delete = models.CASCADE, related_name = "as_output")
    timeCreated = models.DateTimeField(auto_now_add=True)
    timeUpdated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("first_input", "second_input"), name="unique_transformation_inputs")
        ]

    def __str__(self) -> str:
        return f"{self.input_pair.first_input} + {self.input_pair.second_input} = {self.output}"
             
    def updateTier(self):
        message = ""
        # this SHOULD always be the second one, but just in case
        trTier = max(self.input_pair.first_input.tier, self.input_pair.second_input.tier) + 1
        output = self.output

        if trTier < output.tier:

            message += f"{output.name} has a new simplest way to make it! <br>Was: {output.simplestWayToMake}<br>"
            
            output.tier = trTier
            output.simplestWayToMake = self
            output.save()

            message +=f"Now: {self}<br>"

            for pair in output.as_first_in_pair.all() | output.as_second_in_pair.all():
                pair.checkOrder()
                tr_set = pair.as_inputs.all()
                if tr_set:
                    message += tr_set[0].updateTier()

        return message

    def export(self):
        return f"{self.second_input}->{self.first_input}->{self.output}"

    
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
        except:
            output_string = "???"
        return f"{self.first_input} + {self.second_input} = {output_string}"
    
    def fetch(str1, str2):
        try:
            return ItemPair.objects.get(first_input__name=str1, second_input__name=str2)
        except:
            return ItemPair.objects.get(first_input__name=str2, second_input__name=str1)

    def pairFromStrings(first_input, second_input):
        item_list = []
        for name in [first_input, second_input]:
            try:
                item_list.append(Item.objects.get(name=name))
            except Item.DoesNotExist:
                raise InputDoesNotExist(name=name)
        pair = ItemPair.getOrMakePairFromList(item_list)
        return pair
    
    def getOrMakePairFromList(item_list):
        item_list = ItemPair.orderItems(item_list)
        try:
            pair = ItemPair.objects.get(first_input=item_list[0], second_input=item_list[1])
        except ItemPair.DoesNotExist:
            pair = ItemPair(first_input=item_list[0], second_input=item_list[1])
            pair.save()
        return pair
    
    def orderItems(item_list):
        item_list.sort(key= lambda item: item.name)
        item_list.sort(key= lambda item: item.tier)
        return item_list

    def dedupeAndSortPairs(pair_list):
        pair_list = list(set(pair_list))
        pair_list = ItemPair.sortListOfPairs(pair_list)
        return pair_list
    
    def sortListOfPairs(pair_list):
        pair_list.sort(key = lambda pair: pair.first_input.name)
        pair_list.sort(key = lambda pair: pair.second_input.name)
        pair_list.sort(key = lambda pair: pair.first_input.tier)
        pair_list.sort(key = lambda pair: pair.second_input.tier)
        return pair_list
    
    def checkOrder(self):
        ordered = ItemPair.orderItems([self.first_input, self.second_input])
        if self.first_input == ordered[0] and self.second_input == ordered[1]:
            return self
        else:
            self.first_input = ordered[0]
            self.second_input = ordered[1]
            self.save()