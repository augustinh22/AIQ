#-------------------------------------------------------------------------------
# Name:        Sentinel2 Downloader
# Purpose:     This script uses aria2 and Powershell to download Sentinel2
#              images from the Sentinel API or Scientific Data Hub.
#
# Author:      h.Augustin
#
# Created:     12.10.2016
#
#-------------------------------------------------------------------------------

#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import optparse
import tkMessageBox
import xml.etree.ElementTree as etree
from datetime import date
from Tkinter import *

import requests  # Follow PEP8 on formatting imports.

################################################################################
class OptionParser(optparse.OptionParser):

    def check_required(self, opt):
        option = self.get_option(opt)

    # Assumes the option's 'default' is set to None.
        if getattr(self.values, option.dest) is None:
            self.error('{} option not supplied'.format(option))

################################################################################

# Function checks for existance of ESA kml file.
def check_kml():
    kml_file = ('S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000'
        '_21000101T000000_B00.kml')
    if os.path.exists(kml_file) is False:
        print(
            '\n--------------------------------------------------------------'
            '\nPlease download the ESA Sentinel-2 kml file!'
            '\nSee README.md for details.'
            '\n--------------------------------------------------------------\n'
        )
        sys.exit(-1)

# Function returns center coordinates of tile, if the tile exists.
## This will be changed to polygon coordinates instead of points.
def tile_point(tile):
    print '\n------------------------------------------------------------------'
    print 'Hold on while we check the kml for the tile\'s center point!'
    kml_file = ('S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000'
        '_21000101T000000_B00.kml')

    tree = etree.parse(kml_file)
    # Get all placemarks.
    placemarks = tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark')

    # Initialize empty list to fill, or not.
    coords = []
    # Iterate through the attributes within each placemark.
    for attributes in placemarks:
        for subAttribute in attributes:
            # Iterate through the names of each placemark.
            name = attributes.find('.//{http://www.opengis.net/kml/2.2}name')
            # If the name is the same as the defined tile, get coordinates.
            if name.text == tile:
                # Find the center point tag.
                points = attributes.find('.//{http://www.opengis.net/kml/2.2}'
                    'Point')
                # Have to go in deeper, thanks to etree.
                for unit in points:
                    # Save the center point values as a list.
                    coords = (unit.text).split(',')
                    # ['longitude', 'latitude', 'vertical']
                    return coords
    # If list is still empty after loop the tile was not found,
    if not coords:
        print 'Tile not found. Try again.'
        sys.exit(-1)

# Function returns tiles incldued in a package/file.
def return_tiles(uuid_element, filename):
    # Create link to search for tile/granule data.
    granule_link = ("{}odata/v1/Products"
        "('{}')/Nodes('{}')/Nodes('GRANULE')/Nodes").format(
        huburl, uuid_element, filename)

    # Create GET request from hub and essentially parse it.
    response = session.get(granule_link, stream=True)
    granule_tree = etree.fromstring(response.content)
    # Search for all entires (i.e. tiles)
    granule_entries = granule_tree.findall('{http://www.w3.org/2005/Atom}entry')

    # Empty string to fill with all tiles in the file
    granules = ''

    # Go through each tile appending each name to string.
    for granule_entry in range(len(granule_entries)):
        # UUID element creates the path to the file.
        granule_dir_name = (granule_entries[granule_entry].find(
            '{http://www.w3.org/2005/Atom}title')).text
        granule = granule_dir_name[50:55]
        granules += ' {}'.format(granule)

    # Print the number of tiles and their names.
    print '# of Tiles: {}'.format(str(len(granule_entries)))
    print 'Tiles:{}'.format(granules)

################################################################################

#------------------------------------------------------------------------------#
#                             Parse command line                               #
#------------------------------------------------------------------------------#
if len(sys.argv) == 1:
    prog = os.path.basename(sys.argv[0])
    print('\n        {0} [options]'
        '\n        Help: {1} --help'
        '\n        or: {1} -h'
        '\nexample python {0} --lat 43.6 --lon 1.44\n').format(
        sys.argv[0], prog)
    sys.exit(-1)
else:
    usage = 'usage: %prog [options] '
    parser = OptionParser(usage=usage)

    # Authorization and directory related commands
    parser.add_option('-a', '--auth', dest='auth', action='store',
            type='string', help='Sentinels Scientific Data Hub account and '
            'password file, if available')
    parser.add_option('-w', '--write_dir', dest='write_dir', action='store',
            type='string', help='Path where products should be downloaded',
            default='')
    parser.add_option('-r', dest='MaxRecords', action='store', type='int',
            help='Maximum number of records to download (default=100)',
            default=100)
    parser.add_option('--hub', dest='hub', action='store_true',
            help='Try other hubs if apihub is not working', default=None)

    # Location related commands
    parser.add_option('-t', '--tile', dest='tile', action='store',
            type='string', help='Sentinel-2 Tile number', default=None)
    parser.add_option('-l', '--location', dest='location', action='store',
            type='string', help='Town name (pick one which is not too '
            'frequent to avoid confusions)', default=None)
    parser.add_option('--lat', dest='lat', action='store', type='float',
            help='Latitude in decimal degrees', default=None)
    parser.add_option('--lon', dest='lon', action='store', type='float',
            help='Longitude in decimal degrees', default=None)
    parser.add_option('--latmin', dest='latmin', action='store', type='float',
            help='Min latitude in decimal degrees', default=None)
    parser.add_option('--latmax', dest='latmax', action='store', type='float',
            help='Max latitude in decimal degrees', default=None)
    parser.add_option('--lonmin', dest='lonmin', action='store', type='float',
            help='Min longitude in decimal degrees', default=None)
    parser.add_option('--lonmax', dest='lonmax', action='store', type='float',
            help='Max longitude in decimal degrees', default=None)

    # Other Sentinel file related command parameters
    parser.add_option('-s', '--sentinel', dest='sentinel', action='store',
            type='string', help='Sentinel mission considered (e.g. S1 or S2)',
            default='S2')
    parser.add_option('-d', '--start_date', dest='start_date', action='store',
            type='string', help='Start date, fmt("2015-12-22")', default=None)
    parser.add_option('-f', '--end_date', dest='end_date', action='store',
            type='string', help='End date, fmt("2015-12-23")', default=None)
    parser.add_option('-c', '--max_cloud', dest='max_cloud', action='store',
            type='float', help='Only search for products up to a certain '
            'cloud percentage (e.g. 50 for 50%)', default=None)
    parser.add_option('-o', '--orbit', dest='orbit', action='store',
            type='int', help='Orbit path number', default=None)

# Currently unused commands that could be built into the script at a later date
    # parser.add_option('-n', '--no_download', dest='no_download',
    #        action='store_true', help='Do not download products, just '
    #        'print aria2 command', default=False)
    # parser.add_option('-p', '--proxy_passwd', dest='proxy',
    #        action='store', type='string', help='Proxy account and '
    #        'password file', default=None)
    # parser.add_option('--id', '--start_ingest_date',
    #         dest='start_ingest_date', action='store', type='string',
    #         help='start ingestion date, fmt("2015-12-22")', default=None)
    # parser.add_option('--if', '--end_ingest_date', dest='end_ingest_date',
    #         action='store', type='string', help='end ingestion date,
    #         fmt("2015-12-23")', default=None)

    (options, args) = parser.parse_args()

# Add tile query check.
if options.tile != None and options.sentinel != 'S2':
    print 'The tile option (-t) can only be used for Sentinel-2!'
    sys.exit(-1)

# Set data source (apihub vs dhus -- more could be added).
if options.hub is None:
    huburl = 'https://scihub.copernicus.eu/apihub/'
elif options.hub == 'dhus':
    huburl = 'https://scihub.copernicus.eu/dhus/'
# # Untested
# elif options.hub == 'zamg':
#     huburl = 'https://data.sentinel.zamg.ac.at/api/'

# Build in checks for valid commands related to the spatial aspect.
if options.tile is None or options.tile == '?':
    if options.location is None:
        if options.lat is None or options.lon is None:
            if (options.latmin is None or options.lonmin is None
                    or options.latmax is None or options.lonmax is None):
                # Explain problem and give example.
                print(
                    '\nPlease provide at least one point/rectangle/location!'
                    '\nExamples:'
                    '\n\tPoint: python iq_download.py --lat 47.083 --lon 12.842'
                    '\n\tPolygon: python iq_download.py --latmin 46 '
                    '--latmax 48 --lonmin 12 --lonmax 14'
                    '\n\tLocation: python iq_download.py -l Vienna\n'
                )
                sys.exit(-1)
            else:
                geom = 'rectangle'
        else:
            if (options.latmin is None and options.lonmin is None
                    and options.latmax is None and options.lonmax is None):
                geom = 'point'
            else:
                print(
                    '\nPlease choose either point or rectangle, but not both!'
                    '\nExamples:'
                    '\n\tPoint: python iq_download.py --lat 47.083 --lon 12.842'
                    '\n\tPolygon: python iq_download.py --latmin 46 '
                    '--latmax 48 --lonmin 12 --lonmax 14'
                )
                sys.exit(-1)
    else:
        if (options.latmin is None and options.lonmin is None
                and options.latmax is None and options.lonmax is None
                and options.lat is None or options.lon is None):
            geom = 'location'
        else:
            print(
                '\nPlease choose location and coordinates, but not both!\n'
                '\nExamples:'
                '\n\tPoint: python iq_download.py --lat 47.083 --lon 12.842'
                '\n\tPolygon: python iq_download.py --latmin 46 '
                '--latmax 48 --lonmin 12 --lonmax 14'
                '\n\tLocation: python iq_download.py -l Vienna\n'
            )
            sys.exit(-1)
else:
    # Quits if the kml file is not there.
    check_kml()
    # Quits if the tile doesn't exist, otherwise returns center coordinates.
    coords = tile_point(options.tile)
    options.lon = coords[0]
    options.lat = coords[1]
    print 'The center point is: {}, {}'.format(options.lat, options.lon)
    geom = 'point'

# Create spatial parts of the query ::: point, rectangle or location name
# Beware of the quotation marks. For some reason the double quotes alone are
# not registered by the data hub, so they seem to need to be done this way.
if geom == 'point':
    query_geom = '(footprint:"\""Intersects({} {})"\"")'.format(
        options.lat, options.lon)
elif geom == 'rectangle':
    query_geom = ('(footprint:"\""Intersects(POLYGON(({lonmin} {latmin}, '
        '{lonmax} {latmin}, {lonmax} {latmax}, {lonmin} {latmax}, '
        '{lonmin} {latmin})))"\"")').format(latmin = options.latmin,
        latmax = options.latmax, lonmin = options.lonmin,
        lonmax = options.lonmax)
elif geom == 'location':
    query_geom = '{}'.format(options.location)

# Add orbit, if defined (default: NONE).
if options.orbit is None:
    query_orb = query_geom
else:
    query_orb = '({}) AND (relativeorbitnumber:{})'.format(
        query_geom, options.orbit)

# Add Sentinel mission.
if options.sentinel == 'S2':
    query_slc = '{} AND (platformname:Sentinel-2)'.format(query_orb)
elif options.sentinel == 'S1':
    query_slc = '{} AND (platformname:Sentinel-1)'.format(query_orb)
else:
    query_slc = query_orb

# Add dates of capture.
if options.start_date != None:
    start_date = options.start_date
else:
    start_date = '2015-06-13'  # Sentinel-2 launch date

if options.end_date != None:
    end_date = options.end_date
else:
    end_date = date.today().isoformat()

query_time = ('{} AND (beginPosition:[{}T00:00:00.000Z TO {}T23:59:59.999Z] '
    'AND endPosition:[{}T00:00:00.000Z TO {}T23:59:59.999Z])').format(
    query_slc, start_date, end_date, start_date, end_date)

# Add cloud cover query.
if options.max_cloud != None:
    query = '{} AND (cloudcoverpercentage:[0.0 TO {}])'.format(
        query_time, options.max_cloud / 100)
else:
    query = query_time

#------------------------------------------------------------------------------#
#                          Read authentification file                          #
#------------------------------------------------------------------------------#
# Use this part if you want to have your password and username saved in a
# textfile, with the file name as the command.
if options.auth != None:
    parser.check_required('-a')
    try:
        f = file(options.auth)  # Should this be done with a "with" function?
        (account,passwd) = f.readline().split(' ')
        if passwd.endswith('\n'):
            passwd=passwd[:-1]
        f.close()
    except:
        print 'Error with password file.'
        sys.exit(-2)

# Authenticate at data hub.
else:
    url = '{}search?q='.format(huburl)
    account = raw_input('Username: ')
    passwd = raw_input('Password: ')

    # Start session/authorization using requests module.
    session = requests.Session()
    session.auth = (account, passwd)

#------------------------------------------------------------------------------#
#                Prepare aria2 command line to search catalog                  #
#------------------------------------------------------------------------------#

# Check for existing xml-file and delete if present.
if os.path.exists('query_results.xml'):
    os.remove('query_results.xml')

# Set query variables used throughout the script.
url_search = '{}search?q='.format(huburl)
wg = 'aria2c --check-certificate=false'
auth = '--http-user="{}" --http-passwd="{}"'.format(account, passwd)
search_output = ' --continue -o query_results.xml'
wg_opt = ' -o '

# Execute command to download and save query as xml-file in the same location
# as the python script.
command_aria = '{} {} {} "{}{}&rows={}"'.format(
    wg, auth, search_output, url_search, query, options.MaxRecords)

print command_aria
os.system(command_aria)

#------------------------------------------------------------------------------#
#                              Parse catalog output                            #
#------------------------------------------------------------------------------#

# Parse the xml-file. The entry tag contains the results.
tree = etree.parse('query_results.xml')
entries = tree.findall('{http://www.w3.org/2005/Atom}entry')

# Save the number of scenes to a variable.
scenes = str(len(entries))

# Initialize variable to return total size.
total_size = 0

for entry in range(len(entries)):
    # The UUID element is the key ingredient for creating the path to the file.
    uuid_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
        'id')).text
    sentinel_link = ("{}odata/v1/Products('{}')/$value").format(
        huburl, uuid_element)

    # The title element contains the corresponding file name.
    title_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
        'title')).text
    summary_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
        'summary')).text
    filename = (entries[entry].find('.//*[@name="filename"]')).text

    # Print each entry's info
    print "\n------------------------------------------------------------------"
    print 'Scene {} of {}'.format(entry + 1, len(entries))
    print title_element
    print summary_element
    # Return tile names per entry using function return_tiles if desired
    if options.tile == '?':
        return_tiles(uuid_element, filename)
    # Find cloud cover percentage
    cloud_element = (entries[entry].find('.//*[@name="cloudcoverpercentage"]')
        ).text
    print 'Cloud cover percentage: {}'.format(cloud_element)
    print sentinel_link

    # Return the size of the entry.
    size_element = (entries[entry].find('.//*[@name="size"]')).text
    # Parse size to float and add to running total of size.
    if 'GB' in size_element:
        size_element = size_element.replace(' GB', '')
        size_element = float(size_element)
        total_size += size_element
    elif 'MB' in size_element:
        size_element = size_element.replace(' MB', '')
        size_element = float(size_element) / 1024
        size_element = size_element
        total_size += size_element

    # Check if file was already downloaded.
    zipfile = '{}.zip'.format(title_element)
    if os.path.exists(zipfile):
        print zipfile, ' has already been downloaded!',
     # Do not download the product if it was already downloaded and unzipped.
    if os.path.exists(title_element):
        print title_element, ' already exists in unzipped form!',

        continue

#------------------------------------------------------------------------------#
#                            Downloader message box                            #
#------------------------------------------------------------------------------#

# Turn the total size of scenes found back into text.
total_size = '{0:.2f} GB'.format(total_size)

if options.tile is None:
    question_tile = 'Do you want to download all results?'
elif options.tile != None:
    question_tile = ('Do you want to download only {} tiles selected'
        'from the results?').format(options.tile)

# Create question to continue based on the number of scenes found.
question = ('Number of scenes found: {}'
    '\nTotal size of scenes: {}'
    '\n\n{}').format(scenes, total_size, question_tile)

# Hide the main window.
root = Tk().withdraw()
# Create the content of the window.
messagebox = tkMessageBox.askyesno('Sentinel Downloader', question)
if messagebox and options.tile is None:
   	# Download all whole scenes matching the query.
    for entry in range(len(entries)):
        # Create download command for the entry.
        uuid_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
            'id')).text
        sentinel_link = ("{}odata/v1/Products('{}')/$value").format(
            huburl, uuid_element)
        title_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
            'title')).text
        zipfile = '{}.zip'.format(title_element)

        # If write_dir is defined, save there, otherwise save to folder where
        # the python script is located.
        if options.write_dir != '':
            command_aria = '{} {} --dir {} {}{} "{}"'.format(wg, auth,
                options.write_dir, wg_opt, zipfile, sentinel_link)
        else:
            command_aria = '{} {} {}{}{} "{}"'.format(wg, auth, wg_opt,
                options.write_dir, zipfile, sentinel_link)

        # Execute download.
        os.system(command_aria)
        print 'Downloaded Scene #{}'.format(str(entry + 1))

    print '\n------------------------------------------------------------------'
    print 'Downloading complete!'
    print '------------------------------------------------------------------\n'
elif messagebox and options.tile != None:
   	# Download all whole scenes matching the query.
    for entry in range(len(entries)):
        # Create download command for the entry.
        uuid_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
            'id')).text
        filename = (entries[entry].find('.//*[@name="filename"]')).text
        # Create link to search for tile/granule data.
        granule_link = ("{}odata/v1/Products"
            "('{}')/Nodes('{}')/Nodes('GRANULE')/Nodes").format(
            huburl, uuid_element, filename)
        # Create GET request from hub and essentially parse it.
        response = session.get(granule_link, stream=True)
        granule_tree = etree.fromstring(response.content)
        # Search for all entires (i.e. tiles)
        granule_entries = granule_tree.findall('{http://www.w3.org/2005/Atom}entry')

        # Go through each tile appending each name to string.
        for granule_entry in range(len(granule_entries)):
            # UUID element creates the path to the file.
            granule_dir_name = (granule_entries[granule_entry].find(
                '{http://www.w3.org/2005/Atom}title')).text
            granule = granule_dir_name[50:55]
            if granule == options.tile:
                # Create product directory
                # Create tile directory
                # Download HTML
                # Download AUX_DATA
                # Download DATASTRIP
                # Download GRANULE files
                # If write_dir is defined, save there, otherwise save to folder where
                # the python script is located.
                if options.write_dir != '':
                    command_aria = '{} {} --dir {} {}{} "{}"'.format(wg, auth,
                        options.write_dir, wg_opt, zipfile, sentinel_link)
                else:
                    command_aria = '{} {} {}{}{} "{}"'.format(wg, auth, wg_opt,
                        options.write_dir, zipfile, sentinel_link)

                # Execute download.
                os.system(command_aria)
                print 'Downloaded Scene #{}'.format(str(entry + 1))
            else:
                print 'Tile not in this entry.'
else:
    print '\n------------------------------------------------------------------'
    print 'Nothing downloaded, but xml file saved!'
    print '------------------------------------------------------------------\n'
