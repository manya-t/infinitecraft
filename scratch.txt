from items.models import Item, InputDoesNotExist, Transformation, ItemPair
from items.views import newTransformation, randomGap
i = Item.fetch('Gollum')
i.gaps()

    items_df = pd.read_sql("SELECT * FROM items_item",db_con)
    tr_df = pd.read_sql("SELECT * FROM items_transformation",db_con)
    
    html_table = tr_df.to_html(classes="table col-sm-10")

    items_with_simplest = items_df.merge(tr_df, how="left", left_on="simplestWayToMake_id", right_on="id", suffixes=("_i", "_t"))
    items_with_simplest = items_with_simplest.merge(items_df, how="left", left_on="first_input_id", right_on="id", suffixes=(None, "_first"))
    items_with_simplest = items_with_simplest.merge(items_df, how="left", left_on="second_input_id", right_on="id", suffixes=(None, "_second"))
    html_table = items_with_simplest[['name', 'tier', 'isReal', 'name_first', 'name_second']].to_html(classes="table col-sm-10")


db_con = sqlite3.connect("db.sqlite3")
    items_df = pd.read_sql("SELECT * FROM items_item",db_con)
    tr_df = pd.read_sql("SELECT * FROM items_transformation",db_con)
    items_with_simplest = items_df.merge(tr_df, how="left", left_on="simplestWayToMake_id", right_on="id", suffixes=("_i", "_t"))
    items_with_simplest = items_with_simplest.merge(items_df, how="left", left_on="first_input_id", right_on="id", suffixes=(None, "_first"))
    items_with_simplest = items_with_simplest.merge(items_df, how="left", left_on="second_input_id", right_on="id", suffixes=(None, "_second"))
    html_table = items_with_simplest[['name', 'tier', 'isReal', 'name_first', 'name_second']].to_html(classes="table col-sm-10")
    return render(request, "index.html", {"table" : html_table})


fetch("https://neal.fun/api/infinite-craft/pair?first=Mountain&second=Earth")
    .then(response => response.json())
    .then(data => {
        console.log(data);
    });

# assigning emoji from saved webpage
for key in result_dict:
         try:
             item = Item.fetch(key)
             if item.emoji is None:
                 item.emoji = result_dict[key]
                 item.save()
         except Item.DoesNotExist:
             print(f"{key} does not exist")
    

    # print items where the most common output is of a higher tier than one would expect
    for item in items:
          mostCommonOutput = item.mostCommonOutput()
          if    .tier>(item.tier+1) and mostCommonOutput["item"].tier>5:
              print(item)
              print(mostCommonOutput)
          if item.tier>5:
              break

    # print pairs or lack thereof for a single item for all items of tier<=4
     for item in items_4:
          try:
              print(ItemPair.fetch(item.name, "Ghost"))
          except:
              print(item)
     

    # print first item with most common frequency at most 1
    for item in items:
        mostCommonOutput = item.mostCommonOutput()
        if mostCommonOutput["freq"]<=1:
            i = item
            print(item)
            print(mostCommonOutput)
            break

yeti_name_list = ["Yeti", "Abominable Snowman", "Bigfoot", "Sasquatch"]
yeti_list = [Item.fetch(name) for name in yeti_name_list]
for item in yeti_list:
   print(f"{item} + {item.no_pair()}")

v = Item.fetch("Volcano")
items_4 = Item.objects.filter(isReal=True, tier__lte=4).order_by("tier","name")
volcano_list = [v]
for item in items_4:
    if item.mostCommonOutput()["item"] == v:
        volcano_list.append(item)
for item in volcano_list:
    print(f"{item} + {item.no_pair()}")