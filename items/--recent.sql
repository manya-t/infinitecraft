--recent
/* SELECT t.id, i1.name, i1.tier, i2.name, i2.tier, o.name, o.tier, o.isReal, o.id, t.timeCreated
FROM items_transformation t
JOIN items_item i1 on i1.id = t.first_input_id
JOIN items_item i2 on i2.id = t.second_input_id
JOIN items_item o on o.id = t.output_id
WHERE t.id<10
ORDER BY t.id */
 
--missing
/* SELECT i1.name, i1.tier, i2.name, i2.tier, o.name, o.tier, o.isReal
FROM
items_item i1
CROSS JOIN items_item i2
LEFT JOIN items_transformation t on 
    (t.first_input_id=i1.id and t.second_input_id = i2.id)
    OR (t.first_input_id=i2.id and t.second_input_id = i1.id)
LEFT JOIN items_item o on o.id = t.output_id
WHERE i1.tier<=3 and i2.tier<=3 and t.id is null
ORDER BY i1.tier+i2.tier, i1.tier, i2.tier, i2.id */


--recently newly made or optimized items
/* SELECT o.name, o.tier, i1.name, i1.tier, i2.name, i2.tier
FROM 
items_item AS o
JOIN items_transformation as t ON o.simplestWayToMake_id = t.id
JOIN items_item AS i1 ON i1.id = t.first_input_id
JOIN items_item AS i2 ON i2.id = t.second_input_id
WHERE o.timeUpdated>'2024-02-28 23:05:24'  and o.isReal
ORDER BY o.tier */

-- import to draw.io
/* SELECT i2.name || '->' || i1.name || '->' || o.name
FROM 
items_item AS o
JOIN items_transformation as t ON o.simplestWayToMake_id = t.id
JOIN items_item AS i1 ON i1.id = t.first_input_id
JOIN items_item AS i2 ON i2.id = t.second_input_id
WHERE 
o.timeUpdated>'2024-03-05 12:00:00' and 
o.isReal
ORDER BY o.tier */

SELECT i1.name, i1.tier, i2.name, i2.tier, t.id
from items_transformation t
join items_item i1 on t.first_input_id = i1.id
join items_item i2 on t.second_input_id = i2.id
join items_item o on o.id = t.output_id
where (i1.tier > i2.tier) or (i1.tier=i2.tier and i1.name>i2.name)
order by i1.tier, i2.tier

SELECT * from items_items