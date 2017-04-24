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
import zipfile
import optparse
import tkMessageBox
import xml.etree.ElementTree as etree
from datetime import date
import Tkinter
import ast

import requests

################################################################################
class OptionParser(optparse.OptionParser):

    def check_required(self, opt):
        option = self.get_option(opt)

        #
        # Assumes the option's 'default' is set to None.
        #
        if getattr(self.values, option.dest) is None:
            self.error('{} option not supplied'.format(option))

################################################################################

def kml_api(tile):

    '''This function returns the center point of a defined S2 tile based on an
        API developed by M. Sudmanns.'''

    #
    # Formulate request and get it.
    #
    with requests.Session() as session:

        api_request = ('http://cf000008.geo.sbg.ac.at/cgi-bin/s2-dashboard/'
                        'api.py?centroid={}').format(tile)

        try:
            r = session.get(api_request)

            #
            # Read string result as a dictionary.
            #
            result = {}
            result = r.text
            result = ast.literal_eval(result)

        except requests.exceptions.RequestException as e:  # This is the correct syntax
            print '\n\n{}\n\n'.format(e)
            result = {"status": "FAIL"}

    #
    # Extract lat, lon from API request, or get try to get from file if failed.
    #
    if result["status"] == "OK":

        print '\n------------------------------------------------------------------'
        print 'Hold on while we check the kml for the tile\'s coordinates!'

        coords = [result["data"]["x"], result["data"]["y"]]

    else:
        coords = tile_coords(options.tile, 'point')

    return coords


def check_kml():

    ''' Checks for existance of ESA kml file, and quits if not available.'''

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
    return kml_file


def tile_coords(tile, form):

    '''Returns polygon or center point coordinates for a tile from the kml.'''

    #
    # Check for kml file.
    #
    kml_file = check_kml()
    print '\n------------------------------------------------------------------'
    print 'Hold on while we check the kml for the tile\'s coordinates!'

    #
    # Create element tree of all tiles in the kml file.
    #
    tree = etree.parse(kml_file)

    #
    # Get all placemarks (i.e. tiles).
    #
    placemarks = tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
    coords = []

    #
    # Iterate through the attributes within each placemark.
    #
    for attributes in placemarks:
        for subAttribute in attributes:

            #
            # Iterate through the names of each placemark.
            #
            name = attributes.find('.//{http://www.opengis.net/kml/2.2}name')

            #
            # If the name is the same as the defined tile, get coordinates,
            # either the polygon or center point.
            #
            if name.text == tile and form == 'polygon':

                #
                # Find the polygon tag.
                #
                points = attributes.find('.//{http://www.opengis.net/kml/2.2}'
                    'Polygon')
                #
                # Access and return the tile's polygon coordinates.
                #
                for unit in points:
                    xyz = attributes.find('.//{http://www.opengis.net/kml/2.2}'
                        'coordinates').text
                    xyz = xyz.strip('\t\n\r')
                    coords = (xyz).split(' ')
                    # ['longitude,latitude,vertical', ... ]
                    point1 = coords[0].split(',')
                    point2 = coords[1].split(',')
                    point3 = coords[2].split(',')
                    point4 = coords[3].split(',')
                    point5 = coords[4].split(',')

                    return point1, point2, point3, point4, point5

                    #
                    # Assuming not empty, quit searching.
                    #
                    if coords:
                        break

            elif name.text == tile and form == 'point':
                #
                # Find the center point tag.
                #
                points = attributes.find('.//{http://www.opengis.net/kml/2.2}'
                    'Point')
                for unit in points:

                    #
                    # Save the center point values as a list.
                    #
                    coords = (unit.text).split(',')
                    # ['longitude', 'latitude', 'vertical']
                    return coords

                    #
                    # Assuming not empty, quit searching.
                    #
                    if coords:
                        break

    if not coords:
        print 'Tile not found. Try again.'
        sys.exit(-1)


def return_tiles(uuid_element, filename, tile=''):

    '''Function returns tiles incldued in the GRANULE folder of a product,
       including the entire file name of one desired tile, if specified. '''

    #
    # Create link to search for tile/granule data.
    #
    granule_link = ("{}odata/v1/Products"
        "('{}')/Nodes('{}')/Nodes('GRANULE')/Nodes").format(
        huburl, uuid_element, filename)

    #
    # Create GET request from hub and parse it.
    #
    response = session.get(granule_link, stream=True)
    granule_tree = etree.fromstring(response.content)

    #
    # Search for all entires (i.e. tiles)
    #
    granule_entries = granule_tree.findall('{http://www.w3.org/2005/Atom}entry')

    #
    # Empty string to fill with all tiles in the file.
    #
    granules = ''

    #
    # Go through each tile appending each name to string.
    #
    for granule_entry in range(len(granule_entries)):

        #
        # UUID element creates the path to the file.
        #
        granule_dir_name = (granule_entries[granule_entry].find(
            '{http://www.w3.org/2005/Atom}title')).text
        granule = granule_dir_name[50:55]
        granules += ' {}'.format(granule)

        #
        # If one tile is given as an optional arg, return entire tile file name.
        #
        if tile != '':
            if tile in granule_dir_name:
                granule_file = granule_dir_name
        else:
            granule_file = ''

    #
    # Return the number of granules and their names, or just the individual
    # tile file name if a specific tile was asked for.
    #
    if not granule_file:
        return(granule_entries, granules)

    else:
        return(granule_file)


def download_check(write_dir, title_element, filename):

    ''' Function checks if files have aleady been downloaded. If yes, but
       unzipped, it unzips them and deletes the zipped folder.'''

    #
    # Possible zipped folder name.
    #
    zfile = '{}.zip'.format(title_element)

    #
    # Check if file was already downloaded.
    #
    if os.path.exists(os.path.join(write_dir, title_element)):
        print '{} already exists in unzipped form!'.format(title_element)
        return True
    elif os.path.exists(os.path.join(write_dir, filename)):
        print '{} already exists in unzipped form!'.format(filename)
        return True
    elif os.path.exists(os.path.join(write_dir, zfile)):
        print '{} has already been downloaded!'.format(zfile)
        with zipfile.ZipFile(os.path.join(write_dir, zfile)) as z:
            z.extractall(u'\\\\?\\{}'.format(write_dir))
            print 'And is now unzipped.'
        os.remove(os.path.join(write_dir, zfile))
        return True
    else:
        return False


def return_header(uuid_element, filename):

    ''' Function returns name of header xml incldued in a product.'''

    #
    # Create link to search for tile/granule data.
    #
    safe_link = ("{}odata/v1/Products"
        "('{}')/Nodes('{}')/Nodes").format(
        huburl, uuid_element, filename)

    #
    # Create GET request from hub and essentially parse it.
    #
    response = session.get(safe_link, stream=True)
    safe_tree = etree.fromstring(response.content)

    #
    # Search for all entires.
    #
    safe_entries = safe_tree.findall('{http://www.w3.org/2005/Atom}entry')

    #
    # Go through each entry in the safe folder and return header xml name.
    #
    for safe_entry in range(len(safe_entries)):

        #
        # UUID element creates the path to the file.
        #
        safe_name = (safe_entries[safe_entry].find(
            '{http://www.w3.org/2005/Atom}title')).text
        if 'SAFL1C' in safe_name:
            header_xml = safe_name
            return header_xml
    if not header_xml:
        print 'Header xml could not be located!'
        # Maybe change to throw some sort of exception?

#
def make_dir(location, filename):

    ''' Creates a directory in another directory if it doesn't already exist.'''

    dir_name = '{}/{}'.format(location, filename)
    if not(os.path.exists(dir_name)):
        os.mkdir(dir_name)

    return dir_name


def get_tile_files(uuid_element, filename, tile_file, tile_dir):

    ''' Creates structure for tile specific download (tile inside GRANULE
       folder), and fills it.'''

    #
    # Define link to tile folder in data hub.
    #
    tile_folder_link = ("{}odata/v1/Products"
        "('{}')/Nodes('{}')/Nodes('GRANULE')/Nodes('{}')/Nodes").format(
        huburl, uuid_element, filename, tile_file)

    #
    # Connect to the server and stream the metadata as a string, parsing it.
    #
    response = session.get(tile_folder_link, stream=True)
    tile_folder_tree = etree.fromstring(response.content)

    #
    # Search for all entires
    #
    tile_folder_entries = (tile_folder_tree.findall(
        '{http://www.w3.org/2005/Atom}entry'))

    #
    # Go through each entry and identify necessary information for download.
    #
    for tile_folder_entry in range(len(tile_folder_entries)):
        tile_entry_title = (tile_folder_entries[tile_folder_entry].find(
            '{http://www.w3.org/2005/Atom}title')).text
        print '\n\n\n\n\nDownloading: {}'.format(tile_entry_title)
        tile_entry_id = (tile_folder_entries[tile_folder_entry].find(
            '{http://www.w3.org/2005/Atom}id')).text

        #
        # Download xml file
        #
        if '.xml' in tile_entry_title:
            tile_xml_file = tile_entry_title
            tile_xml_link = "{}/$value".format(tile_entry_id)
            command_aria = '{} {} --dir {} {}{} "{}"'.format(wg, auth,
                tile_dir, wg_opt, tile_xml_file, tile_xml_link)
            os.system(command_aria)

        else:

            #
            # Create folder for files and go get them
            #
            inside_folder_dir = make_dir(tile_dir, tile_entry_title)
            get_inside_files(inside_folder_dir, tile_entry_id)


def get_inside_files(inside_folder_dir, tile_entry_id):

    ''' Go deeper in the element tree and download contents to the specified
       folder. This is relevant for tile specific downloads in the old file
       structure, pre-06.12.16.'''

    #
    # Get xml link and connect to server, parsing response as a string.
    #
    inside_folder_link = "{}/Nodes".format(tile_entry_id)
    resp = session.get(inside_folder_link, stream=True)
    inside_folder_tree = etree.fromstring(resp.content)

    #
    # Search for all entires
    #
    inside_folder_entries = (inside_folder_tree.findall(
        '{http://www.w3.org/2005/Atom}entry'))

    #
    # Download each entry saving in the defined directory.
    #
    for inside_folder_entry in range(len(inside_folder_entries)):
        inside_entry_title = (inside_folder_entries[inside_folder_entry].find(
            '{http://www.w3.org/2005/Atom}title')).text
        inside_entry_id = (inside_folder_entries[inside_folder_entry].find(
            '{http://www.w3.org/2005/Atom}id')).text
        inside_entry_file = inside_entry_title
        inside_entry_link = "{}/$value".format(inside_entry_id)
        command_aria = '{} {} --dir {} {}{} "{}"'.format( wg, auth,
            inside_folder_dir, wg_opt, inside_entry_file, inside_entry_link)
        os.system(command_aria)

################################################################################

#------------------------------------------------------------------------------#
#                             Parse command line                               #
#------------------------------------------------------------------------------#

#
# Create download tool help response.
#
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

    #
    # Authorization and directory related commands
    #
    parser.add_option('-a', '--auth', dest='auth', action='store',
            type='string', help='Sentinels Scientific Data Hub account and '
            'password file, if available')
    parser.add_option('-w', '--write_dir', dest='write_dir', action='store',
            type='string', help='Path where products should be downloaded',
            default='C:\\tempS2')
    parser.add_option('-r', dest='MaxRecords', action='store', type='int',
            help='Maximum number of records to download (default=100)',
            default=100)
    parser.add_option('--hub', dest='hub', action='store',
            help='Try other hubs if apihub is not working', default=None)

    #
    # Location related commands
    #
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

    #
    # Other Sentinel file related command parameters
    #
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
    # parser.add_option('--id', '--start_ingest_date',
    #         dest='start_ingest_date', action='store', type='string',
    #         help='start ingestion date, fmt("2015-12-22")', default=None)
    # parser.add_option('--if', '--end_ingest_date', dest='end_ingest_date',
    #         action='store', type='string', help='end ingestion date,
    #         fmt("2015-12-23")', default=None)

    (options, args) = parser.parse_args()


#------------------------------------------------------------------------------#
#                               Create query                                   #
#------------------------------------------------------------------------------#

#
# Add tile query check.
#
if options.tile != None and options.sentinel != 'S2':
    print 'The tile option (-t) can only be used for Sentinel-2!'
    sys.exit(-1)

#
# Set data source (apihub vs dhus -- more could be added).
#
if options.hub is None:

    huburl = 'https://scihub.copernicus.eu/apihub/'

elif options.hub == 'dhus':

    huburl = 'https://scihub.copernicus.eu/dhus/'

    #
    # The dhus data hub has a limit of 10 records.
    #
    if int(options.MaxRecords) > 10:
        options.MaxRecords = '10'

# # Untested, but may be possible to add later.
# elif options.hub == 'zamg':
#     huburl = 'https://data.sentinel.zamg.ac.at/api/'

#
# Make sure write_dir is formatted properly.
#
options.write_dir = (options.write_dir).replace('/', '\\')
print '\nDirectory: {}\n'.format(options.write_dir)

#
# Build in checks for valid commands related to the spatial aspect.
#
if options.tile is None or options.tile == '?':

    if options.location is None:

        if options.lat is None or options.lon is None:

            if (options.latmin is None or options.lonmin is None
                    or options.latmax is None or options.lonmax is None):

                #
                # Explain problem and give example.
                #
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
    #
    # # Returns polygon coordinates. Quits if the tile or kml file do not exist.
    #
    # point1, point2, point3, point4, point5 = tile_coords(
    #     options.tile, 'polygon')
    #
    # # If the polygon's not square get the center coordinate...
    # if point1 != point5:
    #     # Quits if the tile doesn't exist, otherwise returns center coordinates.
    #     coords = tile_coords(options.tile, 'point')
    #     options.lon = coords[0]
    #     options.lat = coords[1]
    #     print 'Center point: {} lat, {} lon'.format(options.lat, options.lon)
    #     geom = 'point'
    # else:
    #     geom = 'tile'

    #
    # Defines lat and lon based on tile's center point.
    #
    ##
    ## Old version retrieving center point from kml file on disk
    ##
    # coords = tile_coords(options.tile, 'point')

    #
    # New method using API.
    #
    coords = kml_api(options.tile)
    options.lon = coords[0]
    options.lat = coords[1]

    print 'Center point: {} lat, {} lon'.format(options.lat, options.lon)
    geom = 'point'

#
# Create spatial parts of the query ::: point, rectangle or location name
# Beware of the quotation marks. For some reason the double quotes alone are
# not registered by the data hub, so they seem to need to be done this way.
#
if geom == 'point':

    query_geom = '(footprint:"\""Intersects({} {})"\"")'.format(
        options.lon, options.lat)

elif geom == 'rectangle':

    query_geom = ('(footprint:"\""Intersects(POLYGON(({lonmin} {latmin}, '
        '{lonmax} {latmin}, {lonmax} {latmax}, {lonmin} {latmax}, '
        '{lonmin} {latmin})))"\"")').format(latmin = options.latmin,
        latmax = options.latmax, lonmin = options.lonmin,
        lonmax = options.lonmax)

elif geom == 'location':

    query_geom = '{}'.format(options.location)

elif geom == 'tile':

    point1 = '{} {}'.format(point1[0], point1[1])
    point2 = '{} {}'.format(point2[0], point2[1])
    point3 = '{} {}'.format(point3[0], point3[1])
    point4 = '{} {}'.format(point4[0], point4[1])
    del point5
    query_geom = ('(footprint:"\""Intersects(POLYGON(({0}, {1}, {2}, {3}, {0})'
        '))"\"")').format(point1, point2, point3, point4)
    print query_geom

#
# Add orbit, if defined (default: NONE).
#
if options.orbit is None:

    query_orb = query_geom

else:

    query_orb = '({}) AND (relativeorbitnumber:{})'.format(
        query_geom, options.orbit)

#
# Add Sentinel mission.
#
if options.sentinel == 'S2':
    query_slc = '{} AND (platformname:Sentinel-2)'.format(query_orb)
elif options.sentinel == 'S1':
    query_slc = '{} AND (platformname:Sentinel-1)'.format(query_orb)
else:
    query_slc = query_orb

#
# Add dates of capture.
#
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

#
# Add cloud cover query.
#
if options.max_cloud != None:

    query = '{} AND (cloudcoverpercentage:[0.0 TO {}])'.format(
        query_time, options.max_cloud)

else:

    query = query_time


#------------------------------------------------------------------------------#
#                   Authorize ESA API or DataHub Credentials                   #
#------------------------------------------------------------------------------#
#
# Use this part if you want to have your password and username saved in a
# textfile, with the file name as the command.
#
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

#
# Authenticate at data hub.
#
else:
    url = '{}search?q='.format(huburl)
    account = raw_input('Username: ')
    passwd = raw_input('Password: ')

    #
    # Start session/authorization using requests module.
    #
    session = requests.Session()
    session.auth = (account, passwd)


#------------------------------------------------------------------------------#
#                Prepare aria2 command line to search catalog                  #
#------------------------------------------------------------------------------#

#
# Check for existing xml query file and delete if present.
#
if os.path.exists('query_results.xml'):
    os.remove('query_results.xml')

#
# Set query variables used throughout the script.
#
url_search = '{}search?q='.format(huburl)
wg = 'aria2c --check-certificate=false'
auth = '--http-user="{}" --http-passwd="{}"'.format(account, passwd)
search_output = ' --continue -o query_results.xml'
wg_opt = ' -o '

#
# Execute command to download and save query as xml-file in the same location
# as the python script.
#
command_aria = '{} {} {} "{}{}&rows={}"'.format(
    wg, auth, search_output, url_search, query, options.MaxRecords)

print command_aria
os.system(command_aria)


#------------------------------------------------------------------------------#
#                              Parse catalog output                            #
#------------------------------------------------------------------------------#

#
# Parse the xml query file. The entry tag contains the results.
#
tree = etree.parse('query_results.xml')
entries = tree.findall('{http://www.w3.org/2005/Atom}entry')

#
# Save the number of scenes to a variable.
#
scenes = str(len(entries))

#
# Initialize variable to return total file size of results.
#
total_size = 0

for entry in range(len(entries)):

    #
    # The UUID element is the key ingredient for creating the path to the file.
    #
    uuid_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
        'id')).text
    sentinel_link = ("{}odata/v1/Products('{}')/$value").format(
        huburl, uuid_element)

    #
    # The title element contains the corresponding file name.
    #
    title_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
        'title')).text
    summary_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
        'summary')).text
    filename = (entries[entry].find('.//*[@name="filename"]')).text

    #
    # Print each entry's info.
    #
    print "\n------------------------------------------------------------------"
    print 'Scene {} of {}'.format(entry + 1, len(entries))
    print title_element
    print summary_element

    #
    # Return tile names per entry using function return_tiles if desired
    #
    if options.tile == '?' and filename.startswith('S2A_OPER_'):

        found_tiles = return_tiles(uuid_element, filename)

        #
        # Print the number of tiles and their names.
        #
        print '# of Tiles: {}'.format(str(len(found_tiles[0])))
        print 'Tiles:{}'.format(found_tiles[1])

    if options.tile == '?' and filename.startswith('S2A_MSIL1C_'):

        #
        # Print the number of tiles and their names.
        #
        print '# of Tiles: 1'
        print 'Tile: {}'.format(filename[-26:-21])

    #
    # Find cloud cover percentage.
    #
    cloud_element = (entries[entry].find('.//*[@name="cloudcoverpercentage"]')
        ).text
    print 'Cloud cover percentage: {}'.format(cloud_element)

    #
    # Print download link from the server.
    #
    print sentinel_link

    #
    # Return the file size of the entry.
    #
    size_element = (entries[entry].find('.//*[@name="size"]')).text

    #
    # Parse size to float and add to running total of size.
    #
    if 'GB' in size_element:
        size_element = size_element.replace(' GB', '')
        size_element = float(size_element)
        total_size += size_element
    elif 'MB' in size_element:
        size_element = size_element.replace(' MB', '')
        size_element = float(size_element) / 1024
        size_element = size_element
        total_size += size_element

    #
    # Check if file was already downloaded.
    #
    download_check(options.write_dir, title_element, filename)


#------------------------------------------------------------------------------#
#                            Downloader message box                            #
#------------------------------------------------------------------------------#

#
# Turn the total size of all scenes found back into text.
#
total_size = '{0:.2f} GB'.format(total_size)

#
# Create question to continue based on number of scenes found.
#
if options.tile is None or options.tile == '?':

    question_tile = 'Do you want to download all results?'

elif options.tile != None:

    question_tile = ('Do you want to download only {} tiles selected '
        'from the results?').format(options.tile)

question = ('Number of scenes found: {}'
    '\nTotal size of scenes: {}'
    '\n\n{}').format(scenes, total_size, question_tile)

#
# Hide the main window.
#
Tkinter.Tk().withdraw()

#
# Create the content of the window.
#
messagebox = tkMessageBox.askyesno('Sentinel Downloader', question)


#------------------------------------------------------------------------------#
#                                  Download.                                   #
#------------------------------------------------------------------------------#

#
# If you want to download all entries and did not search for a specific tile,
# then downloading will begin.
#
if messagebox and (options.tile is None or options.tile == '?'):

    #
   	# Download all whole scenes matching the query.
    #
    for entry in range(len(entries)):

        #
        # Create download command for the entry.
        #
        uuid_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
            'id')).text
        sentinel_link = ("{}odata/v1/Products('{}')/$value").format(
            huburl, uuid_element)
        filename = (entries[entry].find('.//*[@name="filename"]')).text
        title_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
            'title')).text
        zfile = '{}.zip'.format(title_element)

        #
        # Skip files that have already been downloaded.
        #
        check = download_check(options.write_dir, title_element, filename)
        if check is True:

            continue

        #
        # Save to defined directory (default = C:\\tempS2)
        #
        command_aria = '{} {} --dir {} {}{} "{}"'.format(wg, auth,
            options.write_dir, wg_opt, zfile, sentinel_link)

        #
        # Execute download.
        #
        os.system(command_aria)
        print 'Downloaded Scene #{}'.format(str(entry + 1))

        #
        # Unzip even if path names are really long.
        #
        with zipfile.ZipFile(os.path.join(options.write_dir, zfile)) as z:

            z.extractall(u'\\\\?\\{}'.format(options.write_dir))
            print 'Unzipped Scene # {}'.format(str(entry + 1))

        #
        # If the unzipped and zipped version exist, delete the zipped version.
        #
        if (os.path.exists(os.path.join(options.write_dir, filename))
                and os.path.exists(os.path.join(options.write_dir, zfile))):

            os.remove(os.path.join(options.write_dir, zfile))

    print '\n------------------------------------------------------------------'
    print 'Downloading complete!'
    print '------------------------------------------------------------------\n'

#
# If you want to download a tile that you searched for, then it will
# create the proper file structure mimicing a complete download and fill it
# with data specific to the tile you want, or, post 06.12.16, simply download
# complete matching tile packages.
#
elif messagebox and options.tile != None and options.tile != '?':

    #
    # Create download directory if not already existing (default = C:\\tempS2)
    #
    if not(os.path.exists(options.write_dir)):

            os.mkdir(options.write_dir)

    #
   	# Search through entries for matching tiles.
    #
    for entry in range(len(entries)):

        #
        # Create download command for the entry.
        #
        uuid_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
            'id')).text
        filename = (entries[entry].find('.//*[@name="filename"]')).text
        title_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
            'title')).text
        sentinel_link = ("{}odata/v1/Products('{}')/Nodes('{}')/Nodes").format(
            huburl, uuid_element, filename)

        if filename.startswith('S2A_OPER_'):

            #
            # Find tiles in entry, returning the number[0] and tile names[1]
            #
            included_tiles = return_tiles(uuid_element, filename)

        elif filename.startswith('S2A_MSIL1C_'):

            included_tiles = [filename[-26:-21], filename[-26:-21]]

        #
        # If the tile you want is in the entry, then it will create the
        # necessary file structure and fill it.
        #
        if (options.tile in included_tiles[1]
                and filename.startswith('S2A_OPER_')):

        # File structire--------------------------------------------------

            product_dir_name = make_dir(options.write_dir, filename)

            #
            # Create GRANULE directory in product directory
            #
            granule_dir = make_dir(product_dir_name, 'GRANULE')

            #
            # Create tile directory in GRANULE directory based on tile file name
            #
            tile_file = return_tiles(uuid_element, filename, options.tile)

            #
            # If tile folder already exists, then it skips downloading.
            #
            if os.path.exists(os.path.join(granule_dir, tile_file)):

                print 'Tile Folder already downloaded.'

                continue

            tile_dir = make_dir(granule_dir, tile_file)

        # Downloads--------------------------------------------------

            print 'Downloading from scene #{}'.format(str(entry + 1))

            #
            # Download the product header file after finding the name
            #
            header_file = return_header(uuid_element, filename)
            header_link = "{}('{}')/$value".format(
                sentinel_link, header_file)
            command_aria = '{} {} --dir {} {}{} "{}"'.format(wg, auth,
                product_dir_name, wg_opt, header_file, header_link)
            os.system(command_aria)

            #
            # Download INSPIRE.xml
            #
            inspire_file = 'INSPIRE.xml'
            inspire_link = "{}('{}')/$value".format(
                sentinel_link, inspire_file)
            command_aria = '{} {} --dir {} {}{} "{}"'.format(wg, auth,
                product_dir_name, wg_opt, inspire_file, inspire_link)
            os.system(command_aria)

            #
            # Download manifest.safe
            #
            manifest_file = 'manifest.safe'
            manifest_link = "{}('{}')/$value".format(
                sentinel_link, manifest_file)
            command_aria = '{} {} --dir {} {}{} "{}"'.format(wg, auth,
                product_dir_name, wg_opt, manifest_file, manifest_link)
            os.system(command_aria)

            #
            # Download tile xml file and create AUX_DATA, IMG_DATA and QI_DATA
            # folders in the tile folder and download their contents.
            #
            get_tile_files(uuid_element, filename, tile_file, tile_dir)

            print 'Downloaded tile {} from scene #{}\n'.format(
                options.tile, str(entry + 1))

        elif (options.tile in included_tiles
                and filename.startswith('S2A_MSIL1C_')):

            #
            # Create download command for the entry.
            #
            sentinel_link = ("{}odata/v1/Products('{}')/$value").format(
                huburl, uuid_element)
            zfile = '{}.zip'.format(title_element)

            #
            # Skip files that have already been downloaded.
            #
            check = download_check(options.write_dir, title_element, filename)
            if check is True:

                continue

            #
            # Save to defined directory (default = C:\\tempS2)
            #
            command_aria = '{} {} --dir {} {}{} "{}"'.format(wg, auth,
                options.write_dir, wg_opt, zfile, sentinel_link)

            #
            # Execute download.
            #
            os.system(command_aria)
            print 'Downloaded Scene #{}'.format(str(entry + 1))

            #
            # Unzip the downloaded file.
            #
            with zipfile.ZipFile(os.path.join(options.write_dir, zfile)) as z:

                z.extractall(u'\\\\?\\{}'.format(options.write_dir))
                print 'Unzipped Scene # {}'.format(str(entry + 1))

            #
            # Delete the zipped version.
            #
            if (os.path.exists(os.path.join(options.write_dir, filename))
                    and os.path.exists(os.path.join(options.write_dir, zfile))):

                os.remove(os.path.join(options.write_dir, zfile))

        else:

            print '\nTile {} not in scene #{}\n'.format(
                options.tile, str(entry + 1))

    print '\n------------------------------------------------------------------'
    print 'Downloading complete!'
    print '------------------------------------------------------------------\n'

#
# You decided not to download this time in the message box.
#
else:
    print '\n------------------------------------------------------------------'
    print 'Nothing downloaded, but xml file saved!'
    print '------------------------------------------------------------------\n'
