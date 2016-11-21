#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import xml.etree.ElementTree as etree

granule = '31TC'

def tile_point(tile):
    kml_file = ('S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000'
        '_21000101T000000_B00.kml')

    tree = etree.parse(kml_file)

    placemarks = tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
    coords = []
    # cycle through the attributes within each placemark
    for attributes in placemarks:
        for subAttribute in attributes:
            name = attributes.find('.//{http://www.opengis.net/kml/2.2}name')
            if name.text == tile:
                points = attributes.find('.//{http://www.opengis.net/kml/2.2}Point')
                for unit in points:
                    coords = (unit.text).split(',')
                    # ['longitude', 'latitude', 'vertical']
                    print coords
                    return coords
                # find the center point tag
                # save the center point values as a list
    if not coords:
      print("This List is Empty")

tile_point(granule)
# options.lon = str(coords[0])
# options.lat = str(coords[1])
# geom == 'point'
