#!/usr/bin/env python

import json
from pprint import pprint

ingredients = {
"config": {
"service_url": "http://localhost:8080/rasdaman/ows",
"tmp_directory": "/tmp/",
"crs_resolver": "http://localhost:8080/def/",
"default_crs": "http://localhost:8080/def/crs/EPSG/0/__insert__", # Insert EPSG
"mock": False,
"automated": False,
"subset_correction": True
},
"input": {
"coverage_id": "S2_TILE_TYPE", #Insert TILE and TYPE
"paths": [
	"/var/projects/iq4sen/rawdata/__insert__" # Insert filename
]
},
"recipe": {
"name": "time_series_irregular",
"options": {
  "time_parameter" :{
    "filename": {
    "regex": "(.*)_(\\d\\d\\d\\d\\d\\d\\d\\d)_(.*)",
    "group": "2"
    },
    "datetime_format": "YYYYMMDD"
  },
  "time_crs": "http://localhost:8080/def/crs/OGC/0/AnsiDate",
  "tiling": "ALIGNED [0:127480, 0:85900, 1]"
}
}
}

def insert_data():
    ## Do a bunch of stuff to insert the actual bits.

    return ingredients

if __name__ == '__main__':

    pprint(ingredients)

    ingredients = insert_data()

    # Save this to json file
    with open('ingredients2.json', 'w') as file:
        file.write(json.dumps(ingredients))
