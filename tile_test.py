#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import optparse
import urllib
import urllib2
import tkMessageBox
import xml.etree.ElementTree as etree
from xml.dom import minidom
from datetime import date
from Tkinter import *

import requests

################################################################################
def return_tiles(uuid_element, filename):
    # create link to search for tile/granule data at ESA APIHub
    granule_link = ("https://scihub.copernicus.eu/apihub/odata/v1/Products"
        "('{}')/Nodes('{}')/Nodes('GRANULE')/Nodes").format(uuid_element, filename)

    # GET request from hub and essentially parse it
    response = session.get(granule_link, stream=True)
    tile_tree = etree.fromstring(response.content)
    # Search for all entires (i.e. tiles)
    tile_entries = tile_tree.findall('{http://www.w3.org/2005/Atom}entry')

    # Empty string to fill with all tiles in the file
    granules = ''

    # Go through each tile and save the tile name to the string
    for tile_entry in range(len(tile_entries)):
        # the UUID element creates the path to the file
        granule_dir_name = (tile_entries[tile_entry].find('{http://www.w3.org/2005/Atom}'
            'title')).text
        granule = granule_dir_name[50:55]
        granules = granules + ' ' + granule

    # print the number of tiles and their names
    tiles = len(tile_entries)
    print '# of Tiles: ' + str(tiles)
    print 'Tiles:' + granules

################################################################################

# Start Session/Authorization in requests
session = requests.Session()
session.auth = ('s1036347', 'AT0210de0210!')

#------------------------------------------------------------------------------#
#                              Parse catalog output                            #
#------------------------------------------------------------------------------#

# parse the xml-file ::: the entry tag contains the results
tree = etree.parse('query_results.xml')
entries = tree.findall('{http://www.w3.org/2005/Atom}entry')

# save the number of scenes to a variable
scenes = len(entries)

# initialize variable to return total size
total_size = 0

for entry in range(len(entries)):
    # the UUID element creates the path to the file
    uuid_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
        'id')).text
    sentinel_link = ("https://scihub.copernicus.eu/apihub/odata/v1/Products('"
        + uuid_element + "')/$value")

    # the title element contains the corresponding file name
    title_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
        'title')).text
    summary_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
        'summary')).text
    filename = (entries[entry].find('.//*[@name="filename"]')).text

    zipfile = title_element + '.zip'

    # Print each entry's info
    print '\n------------------------------------------------------------------'
    print 'Scene ', entry + 1, 'of ', len(entries)
    print title_element
    print summary_element

    granule_link = ("https://scihub.copernicus.eu/apihub/odata/v1/Products"
        "('{}')/Nodes('{}')/Nodes('GRANULE')/Nodes").format(uuid_element, filename)

    # GET request from hub based on session authorization (already defined)
    response = session.get(granule_link, stream=True)
    # create tree from string
    tile_tree = etree.fromstring(response.content)
    # Search for all entires (i.e. tiles)
    tile_entries = tile_tree.findall('{http://www.w3.org/2005/Atom}entry')

    # Empty string to fill with all tiles in the file
    granules = ''

    # Go through each tile and save the tile name to the string
    for tile_entry in range(len(tile_entries)):
        # the UUID element creates the path to the file
        granule_dir_name = (tile_entries[tile_entry].find('{http://www.w3.org/2005/Atom}'
            'title')).text
        granule = granule_dir_name[50:55]
        granules = granules + ' ' + granule

    # print the number of tiles and their names
    tiles = len(tile_entries)
    print '# of Tiles: ' + str(tiles)
    print 'Tiles:' + granules

    # return cloud cover
    cloud_element = (entries[entry].find('.//*[@name="cloudcoverpercentage"]')
        ).text
    print 'Cloud cover percentage: ' + cloud_element
