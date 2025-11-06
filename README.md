# Infinite Craft Analysis

Infinite Craft is a [game made by Neal Agarwal](https://neal.fun/infinite-craft/), inspired [1] by the earlier game Little Alchemy. In both, you start with the four classical elements (`Air`, `Water`, `Earth`, and `Fire`). You combine them in pairs, which creates new items: for example, `Fire` and `Wind` makes `Smoke`, and `Water` and `Water` makes `Lake`. The difference between Little Alchemy and Infinite Craft is that Little Alchemy has a finite, predefined set of combinations, and Infinite Craft is hooked up to an LLM that can add *any* two items together [2]. That's why it's... infinite. You can just keep making things.

Once you start playing this game, you quickly realize that there are some very interesting trends. Adding anything to `Lava` almost always ends up at `Volcano`, for example, and adding something to `Volcano` will usually go back to `Lava`. If you combine two items that are numbers, the result will often be their sum. Adding `Engine` to things makes a vast variety of vehicles and machines (`Tractor`, `Windmill`, `Boat`, `Train`, and so on and so forth.)

Some things are very easy to get to from the starting conditions (`Fire + Water = Steam`, `Steam + Fire = Engine`). Others are quite difficult (the simplest way I currently have of making `Daylight` places it on the 37th level). 

When I encountered this game, I realized rapidly that what I was most interested in were these *patterns*. I didn't just want to throw a bunch of elements at each other, watch them react, and then move on. I wanted to *track* it.

I also didn't want spoilers. There are wikis and discussions out there about how to build what. I've never looked at them. I wanted to discover things myself.

At first I tracked it in a spreadsheet, but this rapidly got out of hand. So I built this tool. 

[1]: I assume

[2]: Mostly. Some combinations just don't react together.

## The Database Schema

I have three tables: Item, ItemPair, and Transformation.

Item has the columns:
- id
- name
- emoji (each item in Infinite Craft comes with an emoji representation)
- timeCreated
- timeUpdated
- tier (an int representing the complexity of the item)
- isReal (whether the item is real or word salad nonsense)
- simplestWayToMake_id (foreign key for a Transformation with the output of this item)
- canCombine (whether the item is such nonsense that further experimentation with it is pointless)

ItemPair:
- id
- first_input_id (Item foreign key)
- second_input_id (Item foreign key)
- from_AB_C_id (Transformation foreign key: if A + B = C, this automatically creates pairs for A + C, B+ C, and C + C if they don't exist yet)

Transformation:
- input_pair_id (ItemPair foreign key)
- output_id (Item foreign key)
- timeCreated
- timeUpdated

## Tiers and simplest ways to make

Each item is on a tier. The first four elements are tier 1. The ten combinations of tier 1 items make the ten tier 2 items. The combinations of tier 2 and tier 1 items make tier 3 items. In general, if you create a transformation creating a new item:

`Item A (tier m) + Item B (tier n) = Item C`

where m<=n, Item C gets assigned a tier of n+1, and the new transformation is assigned as the simplest way to make it (and, for now, the only way).

If Item C already exists and has a tier k no greater than n+1, then it continues to have that tier and simplestwaytomake. However, if k *is* greater than n+1, then the tier is set to n+1 and simplestwaytomake is set to the new transformation. Furthermore, the tool then recursively goes through all the transformations that Item C is an *input* for and checks if any other items need to change tiers. It then reports all the changes.

For example:
> 🧿Artifact (7) has a new simplest way to make it and has changed from Tier 8 to Tier 7!
>
> Was: 📜History (6) + 🏛Museum (7) = 🧿Artifact (7)
>
> Now: 🎨Art (6) + 🏚Ruin (6) = 🧿Artifact (7)
> 
> 🦢Odette (8) has a new simplest way to make it and has changed from Tier 9 to Tier 8!
> 
> Was: 🦢Swan Lake (7) + 🦢Black Swan (8) = 🦢Odette (8)
> 
> Now: 🧿Artifact (7) + 🦢Swan Lake (7) = 🦢Odette (8)
> 
> The tier of Odile (9) has changed from 10 to 9
> 
> 🦢Black Swan (8) + 🦢Odette (8) = Odile (9)

## Most common outputs
One interesting aspect to analyze is one I mentioned briefly above: which inputs most commonly produce which outputs. Here is a graph of which outputs are most common from all the inputs of tier no more than 4:

![](items\templates\most_common\mostCommonOutputs_4.gv.svg)

You can see that there are clusters of meaning (the snow-related cluster, the ocean cluster, the volcano-related cluster). Most chains end in a pair of items that usually produce each other (`Tree` and `Forest`, `Pyramid` and `Sphinx`), but many also end in an item that usually produces itself (`Tsunami`, `Dragon`). At higher tiers, it is occasionally the case that an item will most frequently not produce anything at all. It is also possible for a chain to terminate in a cycle of more than two items, but this appears to be very rare, and often turns out to be temporary, collapsing into a two-cycle once more transformations are tried.



## Most productive items
Some items produce interesting outputs at far greater rates than others. We can operationalize this as: what percent of the time when an item is combined with something does this turn out to be the simplest way to make the result? Discarding those items which have been combined less than 20 times, we get:

| item                |   num_total_transformations |   num_produced_items |   percent_productive |
|:--------------------|----------------------------:|---------------------:|---------------------:|
| 🐐Yankees (8)       |                          25 |                   12 |              48      |
| 🚲Bicycle (8)       |                          27 |                   11 |              40.7407 |
| 📸Resolution (8)    |                          20 |                    8 |              40      |
| 🔝Over (10)         |                          32 |                   12 |              37.5    |
| 🥫Tin (8)           |                          20 |                    7 |              35      |
| 🍕The Godfather (8) |                          20 |                    7 |              35      |
| 🏜Rocky (6)          |                          23 |                    8 |              34.7826 |
| 🎸Country Music (7) |                          26 |                    9 |              34.6154 |
| 🚶Ways (7)          |                          41 |                   14 |              34.1463 |
| 🚗Hit and Run (8)   |                          21 |                    7 |              33.3333 |

(etc.)

There are a great many items that never produce anything new, though:

| item           |   num_total_transformations |   num_produced_items |   percent_productive |
|:---------------|----------------------------:|---------------------:|---------------------:|
| 🏺Pottery (5)  |                          76 |                    0 |                    0 |
| ❄Snowball (4)  |                          73 |                    0 |                    0 |
| 💥Big Bang (6) |                          69 |                    0 |                    0 |
| 🌿Marsh (4)    |                          64 |                    0 |                    0 |
| 🐦Firebird (5) |                          59 |                    0 |                    0 |

And some that only do so very rarely:

| item            |   num_total_transformations |   num_produced_items |   percent_productive |
|:----------------|----------------------------:|---------------------:|---------------------:|
| 🦖T-Rex (6)     |                          78 |                    1 |             1.28205  |
| 🐸Pond (4)      |                          80 |                    1 |             1.25     |
| 🐻Sasquatch (6) |                          85 |                    1 |             1.17647  |
| 🇪🇬Egypt (5)     |                          92 |                    1 |             1.08696  |
| 🌋Eruption (3)  |                         236 |                    1 |             0.423729 |

If we want to drill down into what specifically the items that are produced, we can do that:

|transformation|
|:---------------:|
😈Curse (6) + 🐐Yankees (8) = 🍺Red Sox (9)
🐐Goat (6) + 🐐Yankees (8) = 🥁Billy Martin (9)
🗽New York (6) + 🐐Yankees (8) = ⚾Baseball (9)
⚽Ball (7) + 🐐Yankees (8) = ⚾Home Run (9)
🌟Legend (7) + 🐐Yankees (8) = 🐐Babe Ruth (9)
🐐Scapegoat (7) + 🐐Yankees (8) = 💍A-Rod (9)
🏰Empire (8) + 🐐Yankees (8) = 👿Evil Empire (9)
🏆Win (8) + 🐐Yankees (8) = 💩2009 (9)
🐐Yankees (8) + 🐐Yankees (8) = ⚾World Series (9)
🐐Yankees (8) + 💍A-Rod (9) = 💉Steroids (10)
🐐Yankees (8) + 🥁Billy Martin (9) = 🔥Fired (10)
🐐Yankees (8) + 🍺Red Sox (9) = 👊Rivalry (10)

