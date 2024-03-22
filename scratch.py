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
