#!/usr/bin/env python

import os
import json
import fnmatch
from pprint import pprint


def initialize_template():

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
	"coverage_id": "S2_TILE_TYPE", # Insert TILE and TYPE
	"paths": [] # Append paths.
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

	return ingredients

def get_crs():
	#use gdal to get crs


def insert_crs():
	## Do this once per type of tile.

	jsonconfig = ingredients["config"]
	print jsonconfig["default_crs"]
	jsonconfig["default_crs"] = 'apple'


def insert_coverageID(tile_name, cube_type):
	## Do this once for type of tile

	coverageID = "S2_{}_{}".format(tile_name, cube_type)

	jsoninput = ingredients["input"]


def insert_paths(linux_folder, tile_path):
	## Do this for each matching tile.

	something = ''

	path = os.path.join(linux_folder, something)

	jsoninput = ingredients["input"]

	path_list = jsoninput["paths"]

	# append new path to list


def get_folders(root_folder):

	'''This function returns all of the directories (with full path) located
		directly in the input folder (i.e. root_folder).'''

	#
	# Create list for tile folder paths with one or more stacks for import.
	#
	tile_folders = []

	#
	# Set depth of next()
	#
	dir_names = 1

	#
	# Return list of tile folder paths.
	#
	for name in next(os.walk(root_folder))[dir_names]:

		tile_folders.append(os.path.join(root_folder, name))

	return tile_folders


def get_layer_paths(root_folder, cube_type):

	'''This function returns paths to all layers/stacks of a certain type
		located within the directory tree of the defined root folder.
		Currently, all such layers are created directly in each tile folder.'''

	#
	# Create list for layer/stack paths for import/load.
	#
	layer_paths = []

    for dirpath, dirnames, filenames in os.walk(folder, topdown=True):
        for filename in filenames:



def save_ingredients(root_folder, cube_type, tile_name, ingredients):

	'''This function saves a completed ingredients file to the root_folder. '''

	#
	# Creates ingredients file name and file path
	#
	json_name = 'ingredients_{}_{}.json'.format(cube_type, tile_name)

	file_path = os.path.join(root_folder, json_name)

	#
	# Writes and saves the file to disk.
	#
	with open(file_path, 'w') as file:

		file.write(json.dumps(ingredients))


if __name__ == '__main__':

	#
	# Where the tile folders are located.
	#
	root_folder = 'C:/temps2'

	#
	# The folder where the data will be for loading to the database.
	#
	linux_folder = "/var/projects/iq4sen/"

	#
	# The type of coverage for the ID (e.g. CLS, MSK, IQ4SEN)
	#
	cube_type = 'IQ4SEN'
