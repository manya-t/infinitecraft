from django.shortcuts import render
from django.core.paginator import Paginator
import random
from datetime import datetime
from .models import Item, InputDoesNotExist, Transformation, ItemPair

# Create your views here.
def index(request):
    message = ""
    if request.method == "POST":
        isReal = ("isNonsense" not in request.POST) or (request.POST["isNonsense"]==False)
        message = newTransformation(first_input=request.POST["first_input"], 
                          second_input=request.POST["second_input"], 
                          output=request.POST['output'], 
                          isReal=isReal)
    all_tr = Transformation.objects.all().order_by("-timeCreated")
    page = Paginator(all_tr, 50).get_page(1)
    return render(request, "index.html", {
        "page" : page,
        "message" : message})

def items(request):
    all_items = Item.objects.all().order_by("tier")
    all_items.select_related()
    return render(request, "items.html", {"items" : all_items})

def gaps(request):
    last_gap = lastGap()
    random_gap = randomGap()
    return render(request, "gaps.html", {
        "last_gap": last_gap,
        "random_gap": random_gap
    })

def item(request, id):
    item = Item.objects.get(id=id)
    as_output = item.as_output.all()
    makes = item.makes()
    gaps = item.gaps()
    related = [tr.export() for tr in as_output | makes]
    related 
    return render(request, "item.html", {
        "item": item,
        "as_output": as_output,
        "makes": makes,
        "gaps": gaps,
        "related": related
        })

def itemByName(request, name):
    return item(request, Item.fetch(name).id)

def export(request):
    #CUTOFF = datetime(year=2024, month=3,day=7)timeUpdated__gte=CUTOFF,
    items = Item.objects.filter(isReal=True, tier__gt=1)
    data = [item.simplestWayToMake.export() for item in items]
    return render(request, "export.html", {"data" : data})

def exportSet(request):
    export = []
    if request.method == "POST":
        items = request.POST["item_list"].split(",")
        items = [s.strip() for s in items]
        outputs = Transformation.objects.filter(output__name__in=items)
        first_inputs = Transformation.objects.filter(first_input__name__in=items)
        second_inputs = Transformation.objects.filter(second_input__name__in=items)
        export = [tr.export() for tr in outputs | first_inputs | second_inputs]
    return render(request, "exportSet.html", {"export": export})

def stringsToOrderedObjects(first_input, second_input):
    list = []
    for name in [first_input, second_input]:
        try:
            list.append(Item.objects.get(name=name))
        except Item.DoesNotExist:
            raise InputDoesNotExist(name=name)
    return ItemPair.orderItems(list)


def newTransformation(first_input, second_input, output, isReal=1):
    message = ''
    try:   
        inputs = stringsToOrderedObjects(first_input, second_input)
    except InputDoesNotExist as error:
        return error

    try:
        existing_tr = Transformation.objects.get(first_input=inputs[0], second_input=inputs[1])
        if existing_tr.output.name == output:
            message += f"This transformation already exists! {existing_tr}<br>"
            existing_tr.updateTier()
            return message
        else:
            message += f"The database says this transformation has a result of {existing_tr.output.name} and not {output}, please check again.<br>"
            return message
    except Transformation.DoesNotExist:

        try:
            output = Item.objects.get(name=output)
        except Item.DoesNotExist:
            tier = max(inputs[0].tier, inputs[1].tier) + 1
            output = Item(name=output, tier=tier, isReal=isReal)
            output.save()
            message += f"New Item: {output}<br>"
                    
        transformation = Transformation(first_input=inputs[0], second_input=inputs[1], output=output)
        transformation.save()
        message += f"{transformation}<br>"

        if output.simplestWayToMake is None:
            output.simplestWayToMake = transformation
            output.save()
        
        message += transformation.updateTier()
        
        if not output.isReal:
            message += inputs[0].gaps()
            message += "<br>"
            message += inputs[1].gaps()
            return message
        else:
            message += output.gaps()
            return message


def checkForTransformation(first_input, second_input):
        inputs = stringsToOrderedObjects(first_input, second_input)
        try:
            print(Transformation.objects.get(first_input=inputs[0], second_input=inputs[1]))
            return True
        except Transformation.DoesNotExist:
            print(f"Transformation {first_input}, {second_input} does not exist")
            return False
        
def capitalize(caps_specified):
        result = []
        for s in caps_specified:
            matching = Item.objects.filter(name__iexact=s)
            for item in matching:
                print(item)
                yn =input(f"Rename to {s}?")
                if yn == "Y":
                    item.name = s
                    item.save()
                    print(item)
                result.append(item)
        return result

def lastGap(tier=None):
    if tier is None:
        byTier = Item.objects.filter(isReal=1).order_by("-tier","-timeUpdated")
    else:
        byTier = Item.objects.filter(isReal=1, tier=tier).order_by("-tier","-timeUpdated")
    for i in byTier:
        gap = i.gaps()
        if gap != "":
            return(gap)
            
def randomGap():
    all = Item.objects.filter(isReal=True)
    result = ''
    while result == '':
        randNum = random.choice(range(all.count()))
        result = all[randNum].gaps()
    return result

def mergeTr(id1, id2):
    tr1 = Transformation.objects.get(id=id1)
    tr2 = Transformation.objects.get(id=id2)
    print(f"{tr1}\n{tr2}")
    if tr1.first_input != tr2.second_input or tr1.second_input!=tr2.first_input:
        print("not duplicate")
    else:
        ordered = Item.orderItems([tr1.first_input, tr1.second_input])
        if ordered[0] == tr1.first_input:
            correct = tr1
            incorrect = tr2
        else:
            correct = tr2
            incorrect = tr1
        simplest = incorrect.is_simplest_to_make.all()
        for item in simplest:
            item.simplestWayToMake = correct
            item.save()
            print(f"{item}: {item.simplestWayToMake}")
            print(incorrect.is_simplest_to_make.all())
        incorrect.delete()