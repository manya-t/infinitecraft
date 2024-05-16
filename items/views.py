from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import F
from django.db import IntegrityError
import random
from datetime import datetime
from .models import Item, InputDoesNotExist, Transformation, ItemPair
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def index(request):
    message = ""
    if request.method == "POST":
        isReal = ("isNonsense" not in request.POST)
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
    if request.method == 'POST':
        item.name = request.POST["name"]
        item.isReal = ("isReal" in request.POST)
        item.save()   
    
    as_output = item.as_output.all()
    makes = item.makes()
    gaps = item.gaps()
    related = [tr.export() for tr in as_output | makes]
    
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
    CUTOFF = datetime(year=2024, month=3,day=16)
    items = Item.objects.filter(timeUpdated__gte=CUTOFF,isReal=True, tier__gt=1)
    data = [item.simplestWayToMake.export() for item in items]
    return render(request, "export.html", {"data" : data})

def exportSet(request):
    export = []
    if request.method == "POST":
        items = request.POST["item_list"].split(",")
        items = [s.strip() for s in items]
        outputs = Transformation.objects.filter(output__name__in=items)
        first_inputs = Transformation.objects.filter(input_pair__first_input__name__in=items)
        second_inputs = Transformation.objects.filter(input_pair__second_input__name__in=items)
        export = [tr.export() for tr in outputs | first_inputs | second_inputs]
    return render(request, "exportSet.html", {"export": export})

def newTransformation(first_input, second_input, output, isReal=1):
    message = ''
    try:   
        input_pair = ItemPair.pairFromStrings(first_input, second_input)
    except InputDoesNotExist as error:
        return error

    try:
        existing_tr = Transformation.objects.get(input_pair=input_pair)
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
            tier = max(input_pair.first_input.tier, input_pair.second_input.tier) + 1
            output = Item(name=output, tier=tier, isReal=isReal)
            output.save()
            message += f"New Item: {output}<br>"
                    
        transformation = Transformation(input_pair=input_pair, first_input=input_pair.first_input, second_input=input_pair.second_input, output=output)
        transformation.save()
        message += f"{transformation}<br>"

        if output.simplestWayToMake is None:
            output.simplestWayToMake = transformation
            output.save()
        
        message += transformation.updateTier()
        
        transformation.makeGapPairs()

        if not output.isReal:
            for pair in input_pair.first_input.gaps():
                message += str(pair)
                message +="<br>"
            message += "<br>"
            for pair in input_pair.second_input.gaps():
                message += str(pair)
                message +="<br>"
        else:
            for pair in output.gaps():
                message += str(pair)
                message +="<br>"
        
        first_most_common = input_pair.first_input.mostCommonOutput()
        second_most_common = input_pair.second_input.mostCommonOutput()
        message +="<br>"
        message += f"{input_pair.first_input} makes {first_most_common['item']} {first_most_common['freq']} times"
        message +="<br>"
        message += f"{input_pair.second_input} makes {second_most_common['item']} {second_most_common['freq']} times"
        message +="<br>"

        return message


def checkForTransformation(first_input, second_input):
    input_pair = ItemPair.pairFromStrings(first_input, second_input)
    print(input_pair)
    return input_pair.as_inputs.count() > 0
        
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
    pairs = (
        ItemPair.objects.filter(first_input__isReal=1, second_input__isReal=1, as_inputs__isnull=True)
        .annotate(tier_sum = F("first_input__tier")+F("second_input__tier"))
        .order_by("-tier_sum", "-from_AB_C__timeCreated")
    )
    return pairs[0]

            
def randomGap():
    all = Item.objects.filter(isReal=True)
    result = ''
    while len(result) == 0:
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

def populatePairs():
    all_tr = Transformation.objects.all()
    for tr in all_tr:
        pair = ItemPair(first_input=tr.first_input, second_input=tr.second_input)
        pair.save()
        tr.input_pair = pair
        tr.save()

@csrf_exempt
def addEmoji(request):
    try:
        data = json.loads(request.body)
        item = Item.objects.get(name=data.get("name"))
        item.emoji = data.get("emoji")
        item.save()
        return HttpResponse(status=201)
    except Exception as error:
        print(error)
        return HttpResponse(status=500)
    
def checkPairsOrder():
    out_of_order = ItemPair.objects.filter(first_input__tier__gte=F("second_input__tier"))
    deleted = []
    for pair in out_of_order:
        try:
            pair.checkOrder()
        except IntegrityError:
            deleted.append(pair)
            pair.delete()
    return deleted