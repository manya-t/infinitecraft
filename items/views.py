from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import F
from django.db import IntegrityError
import random
from datetime import datetime
from .models import Item, InputDoesNotExist, Transformation, ItemPair, PyvisConstants
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from pyvis.network import Network
import pytz

# Create your views here.
def index(request):
    all_tr = Transformation.objects.all().order_by("-timeCreated")
    page_number = request.GET.get("page")
    page = Paginator(all_tr, 50).get_page(page_number)
    message = ""
    if request.method == "POST":
        isReal = ("isNonsense" not in request.POST)
        result = newTransformation(first_input=request.POST["first_input"], 
                          second_input=request.POST["second_input"], 
                          output=request.POST['output'], 
                          isReal=isReal)
        message = result["message"]
        tr = result["tr"]
        returned_message = result["message"]        

        """ if tr.output.isReal:
            gaps = tr.output.gaps()
        else:
            gaps = tr.input_pair.first_input.gaps() | tr.input_pair.second_input.gaps() """
        
        first_most_common = tr.input_pair.first_input.mostCommonOutput()
        second_most_common = tr.input_pair.second_input.mostCommonOutput()

        following = tr.input_pair.following()
        if following is None:
            following = tr.input_pair.second_input
            
        following.chainGraph(highlight=True)
        gaps = following.gaps()
        gaps_continuing = []
        other_gaps = []
        for gap in gaps:
            if gap.following() == following or (gap.following() is None and gap.second_input == following):
                gaps_continuing.append(gap)
            else:
                other_gaps.append(gap)        

        url_path_name = following.name_wo_special_char()
    
        return render(request, "index.html", {
            "page" : page,
            "message" : message,
            "tr": tr,
            "success": result["success"],
            "gaps_continuing": gaps_continuing,
            "other_gaps": other_gaps,
            "first_most_common": first_most_common,
            "second_most_common": second_most_common,
            "following": following,
            "url_path_name": url_path_name})
    else:
        return render(request, "index.html", {
            "page" : page})

def items(request):
    page_number = request.GET.get("page")
    filter_name = request.GET.get("name")
    filter_exact = ("exact" in request.GET)
    filter_tier = request.GET.get("tier")
    filter_showNonsense = ("showNonsense" in request.GET)
    order = request.GET.get("order")
    if order is None:
        order = "tier"
    order2 = request.GET.get("order2")
    if order2 is None:
        order2 = "timeCreated"
    
    items = Item.objects.all().order_by(order, order2)
    if filter_name is not None and filter_name != "":
        if filter_exact:
            items = items.filter(name=filter_name)
        else:
            items = items.filter(name__contains=filter_name)
    if filter_tier is not None and filter_tier != "":
        items = items.filter(tier = filter_tier)
    if not filter_showNonsense:
        items = items.filter(isReal=True)
    page = Paginator(items, 50).get_page(page_number)
    return render(request, "items.html", {"page" : page})

def gaps(request):
    pairs = (
        ItemPair.objects.filter(first_input__isReal=1, second_input__isReal=1, as_inputs__isnull=True)
        .annotate(tier_sum = F("first_input__tier")+F("second_input__tier"))
        .order_by("tier_sum", "from_AB_C__timeCreated")
    )
    length = pairs.count()
    last_gap = pairs[length-1]
    gap_with_biggest_tier = pairs.order_by("second_input__tier", "from_AB_C__timeCreated")[length-1]
    first_gap = pairs[0]
    median_gap = pairs[int(length/2)]
    random_gap = pairs[random.choice(range(length))]
    gaps = [
        {"pair": first_gap, "name": "First Gap"},
        {"pair": last_gap, "name": "Last Gap"},
        {"pair": gap_with_biggest_tier, "name": "Gap with biggest tier"},
        {"pair": median_gap, "name": "Median Gap"},
        {"pair": random_gap, "name": "Random Gap"}
    ]
    times = []
    for gap in gaps:
        try:
            times.append(gap["pair"].from_AB_C.timeCreated)
        except:
            times.append(datetime(1,1,1,tzinfo=pytz.UTC))

    for i in range(len(times)):
        gap = gaps[i]
        if times[i] == min(times):
            gap['flag'] = 'earliest'
        if times[i] == max(times):
            gap['flag'] = 'latest'
        gap['following'] = gap['pair'].following()

    return render(request, "gaps.html", {
        "gaps": gaps,
        "num_gaps": length
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
    #related = [tr.export() for tr in as_output | makes]
    
    item.chainGraph(highlight=True)
    name_wo_special_char = item.name_wo_special_char()

    return render(request, "item.html", {
        "item": item,
        "as_output": as_output,
        "makes": makes,
        "gaps": gaps,
        "name_wo_special_char": name_wo_special_char
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
    try:   
        input_pair = ItemPair.pairFromStrings(first_input, second_input)
    except InputDoesNotExist as error:
        return {"success": False, "message": error}

    try:
        existing_tr = Transformation.objects.get(input_pair=input_pair)
        if existing_tr.output.name == output:
            existing_tr.updateTier()
            return {"success": False, "message": f"This transformation already exists! {existing_tr}", "tr": existing_tr}
        else:
            return {"success": False, 
                    "message": f"The database says this transformation has a result of {existing_tr.output.name} and not {output}, please check again.", 
                    "tr": existing_tr}
    except Transformation.DoesNotExist:
        message = ''
        try:
            output = Item.objects.get(name=output)
        except Item.DoesNotExist:
            tier = max(input_pair.first_input.tier, input_pair.second_input.tier) + 1
            output = Item(name=output, tier=tier, isReal=isReal)
            output.save()
            message = f"New Item: {output}"
                    
        transformation = Transformation(input_pair=input_pair, output=output)
        transformation.save()

        if output.simplestWayToMake is None:
            output.simplestWayToMake = transformation
            output.save()
        
        message += transformation.updateTier()
        
        transformation.makeGapPairs()

        return {"success": True, 
                "message": message,
                "tr": transformation}


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

def mostCommonGraph():
    nt = Network(directed=True)
    items = Item.objects.all()
    edges = []
    for item in items:
        color = PyvisConstants.COLOR_DEFAULT if item.isReal else PyvisConstants.COLOR_NOT_REAL
        nt.add_node(item.id, label=item.name, color=color, shape="ellipse")
        mostCommonOutputId = item.mostCommonOutput()["output"]
        if mostCommonOutputId is not None:
            edges.append((item.id, item.mostCommonOutput()["output"]))
    nt.add_edges(edges)
    nt.save_graph('items/templates/images/mostCommonOutputs.html')
    return