#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
import xml.etree.ElementTree as etree
import requests

# Start Session/Authorization in requests
session = requests.Session()
session.auth = ('s1036347', 'AT0210de0210!')

# Variables that would otherwise be handed over
uuid_element = 'c9c0bf59-936b-4f95-b516-c83363c70bd3'
filename = 'S2A_OPER_PRD_MSIL1C_PDMC_20151206T174408_R094_V20151206T111905_20151206T111905.SAFE'

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

# Given variables based off of this information from a download script
# Scene  67 of  69
# S2A_OPER_PRD_MSIL1C_PDMC_20151206T174408_R094_V20151206T111905_20151206T111905
# Date: 2015-12-06T11:19:05Z, Instrument: MSI, Mode: , Satellite: Sentinel-2, Size: 4.56 GB
# Cloud cover percentage: 28.642857142857142
# https://scihub.copernicus.eu/apihub/odata/v1/Products('c9c0bf59-936b-4f95-b516-c83363c70bd3')/$value
# https://scihub.copernicus.eu/apihub/odata/v1/Products('c9c0bf59-936b-4f95-b516-c83363c70bd3')/Nodes('S2A_OPER_PRD_MSIL1C_PDMC_20151206T174408_R094_V20151206T111905_20151206T111905.SAFE')/Nodes('GRANULE')/Nodes
