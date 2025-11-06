from .models import Item, Transformation, ItemPair, PyvisConstants
import graphviz
import pandas as pd

def mostCommonGraph(upToTier=None, excludeNot=True):
    NOT_ID = Item.fetch("[not]").id
    if upToTier is not None:
        items = Item.objects.filter(tier__lte=upToTier)
        graph = graphviz.Digraph(f'mostCommonOutputs_{upToTier}', format='svg', engine='sfdp')
        
    else:
        items = Item.objects.all()
        graph = graphviz.Digraph('mostCommonOutputs_all', format='svg', engine='sfdp')

    edges = []

    for item in items:
        color = PyvisConstants.COLOR_DEFAULT if item.isReal else PyvisConstants.COLOR_NOT_REAL
        graph.node(str(item.id), str(item), style="filled", fillcolor=color, tooltip=str(item))
        mostCommonOutput= item.mostCommonOutput()

        if mostCommonOutput["output"] is not None:
            if mostCommonOutput["output"]==NOT_ID and excludeNot:
                continue
            if upToTier is not None and mostCommonOutput["item"].tier > upToTier:
                graph.node(str(mostCommonOutput["output"]), str(mostCommonOutput["item"]), tooltip=str(mostCommonOutput["item"]))
            edges.append((str(item.id), str(mostCommonOutput["output"]), f"{mostCommonOutput["freq"]} time(s)"))

    for edge in edges:
        graph.edge(edge[0],edge[1],label=edge[2])

    graph.render(directory= f'items/templates/most_common/', cleanup=True)
    return graph

def productivity(items=None, threshold=None):
    if items is None:
        items = Item.objects.filter(isReal=True)
    productivity_frame = pd.DataFrame(items, columns=["item"])
    productivity_frame["num_total_transformations"] = productivity_frame.apply(lambda row: row["item"].makes().count(), axis=1)
    if threshold is not None:
        productivity_frame = productivity_frame[productivity_frame["num_total_transformations"] >= threshold]
    productivity_frame["num_produced_items"] = productivity_frame.apply(lambda row: row["item"].makes_simplest().count(), axis=1)
    productivity_frame["percent_productive"] = productivity_frame["num_produced_items"] / productivity_frame["num_total_transformations"]*100
    return productivity_frame.sort_values(by="percent_productive", ascending=False)
