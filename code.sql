-- get all the well key= A01 

SELECT *
FROM wells
WHERE well_key = 'A1';


-- retrieve all the well_keys with specimen_type = 'mouse'

SELECT wells.well_key
FROM wells
JOIN specimens ON wells.specimen_id = specimens.id
WHERE specimens.type = 'mouse';