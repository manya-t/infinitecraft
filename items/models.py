from django.db import models

# Create your models here.
class Item(models.Model):
    name = models.TextField(unique=True)
    timeCreated = models.DateTimeField(auto_now_add=True)
    timeUpdated = models.DateTimeField(auto_now=True)
    tier = models.IntegerField()
    isReal = models.BooleanField(default=True)
    simplestWayToMake = models.ForeignKey("items.Transformation", on_delete = models.SET_NULL, related_name = "is_simplest_to_make", null=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.tier})"
    
    def makes(self):
        q_first = models.Q(first_input = self)
        q_second = models.Q(second_input = self)
        return Transformation.objects.filter(q_first | q_second).all().order_by(
            "second_input__tier", "first_input__tier", "first_input__name", "second_input__name")
    
    def fetch(name):
        return Item.objects.get(name=name)
    
    def sortAndCheck(unsorted):
        sorted = ItemPair.orderItems(unsorted)
        try:
            tr = Transformation.objects.get(first_input=sorted[0], second_input=sorted[1])
            return [True, tr]
        except Transformation.DoesNotExist:
            return [False, sorted]
    
    def gaps(self):        
        result = []
        for tr in self.makes().all():
            sorted_and_bool = Item.sortAndCheck([self, tr.output])
            if not sorted_and_bool[0] and tr.output.isReal:
                result.append(sorted_and_bool[1])
        for tr in self.as_output.all():
            sorted_and_bool = Item.sortAndCheck([tr.first_input, self])
            if not sorted_and_bool[0] and tr.first_input.isReal:
                result.append(sorted_and_bool[1])
            sorted_and_bool = Item.sortAndCheck([tr.second_input, self])
            if not sorted_and_bool[0] and tr.second_input.isReal:
                result.append(sorted_and_bool[1])
        sorted_and_bool = Item.sortAndCheck([self, self])
        if not sorted_and_bool[0]:
            result.append(sorted_and_bool[1])
        result.sort(key= lambda list: list[0].tier)
        result.sort(key= lambda list: list[1].tier)
        resultString = ''
        for pair in result:
            resultString += f"{pair[0]} + {pair[1]} = ???<br>"
        return resultString
    
    def gapFrom(first, second):
        firstAndOutput = Transformation.objects.filter(first_input__name=first, output__name=second)
        secondAndOutput = Transformation.objects.filter(second_input__name=first, output__name=second)
        outputAndFirst = Transformation.objects.filter(output__name=first, first_input__name=second)
        outputAndSecond = Transformation.objects.filter(output__name=first, second_input__name=second)
        return firstAndOutput.union(secondAndOutput).union(outputAndFirst).union(outputAndSecond)

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
                simplest.first_input.recursiveMake(minTier=minTier, currentResult=currentResult)
                simplest.second_input.recursiveMake(minTier=minTier, currentResult=currentResult)
            return Transformation.dedupeListOfTr(currentResult)

    
class InputDoesNotExist(Item.DoesNotExist):
    def __init__(self, name, *args: object) -> None:
        msg = f"Input ({name}) does not exist. Enter a transformation that fixes that and then try again."
        super().__init__(msg, *args)

class Transformation(models.Model):
    first_input = models.ForeignKey(Item, on_delete = models.CASCADE, related_name = "as_first_input") 
    second_input = models.ForeignKey(Item, on_delete = models.CASCADE, related_name = "as_second_input")
    output = models.ForeignKey(Item, on_delete = models.CASCADE, related_name = "as_output")
    timeCreated = models.DateTimeField(auto_now_add=True)
    timeUpdated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("first_input", "second_input"), name="unique_transformation_inputs")
        ]

    def __str__(self) -> str:
        return f"{self.first_input} + {self.second_input} = {self.output}"
             
    def updateTier(self):
        message = ""
        # this SHOULD always be the second one, but just in case
        trTier = max(self.first_input.tier,self.second_input.tier) + 1
        output = self.output

        if trTier < output.tier:

            message += f"{output.name} has a new simplest way to make it! <br>Was: {output.simplestWayToMake}<br>"
            
            output.tier = trTier
            output.simplestWayToMake = self
            output.save()

            message +=f"Now: {self}<br>"

            for t in output.makes():
                t.checkOrder()
                message += t.updateTier()

        return message
    
    def dedupeListOfTr(list):
        list.sort(key = lambda tr: tr.first_input.name)
        list.sort(key = lambda tr: tr.second_input.name)
        list.sort(key = lambda tr: tr.first_input.tier)
        list.sort(key = lambda tr: tr.second_input.tier)

        prev = list[0]
        for tr in list[1:]:
            if tr == prev:
                list.remove(tr)
            else:
                prev = tr
        return list

    def checkOrder(self):
        ordered = ItemPair.orderItems([self.first_input, self.second_input])
        if self.first_input == ordered[0] and self.second_input == ordered[1]:
            return self
        else:
            self.first_input = ordered[0]
            self.second_input = ordered[1]
            self.save()

    def export(self):
        return f"{self.second_input}->{self.first_input}->{self.output}"
    
class ItemPair(models.Model):
    first_input = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="as_first_in_pair")
    second_input = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="as_second_in_pair")
    transformation = models.ForeignKey(Transformation, on_delete=models.CASCADE, related_name="transformation", null=True)


    def pairFromStrings(first_input, second_input):
        list = []
        for name in [first_input, second_input]:
            try:
                list.append(Item.objects.get(name=name))
            except Item.DoesNotExist:
                raise InputDoesNotExist(name=name)
        ItemPair.orderItems(list)
        pair = ItemPair(first_input=list[0], second_input=list[1])
        return pair
    
    def orderItems(list):
        list.sort(key= lambda item: item.name)
        list.sort(key= lambda item: item.tier)
        return list