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

### To-do List
### - add tile *download* funcitonality, with check of 5 digits
### - update kml/tile check to do polygons and not just the center point
### - add additional password/user option that hides input
### - change download to be able to select packages rather than downloading all?
### - figure out how to check unzipped files (long file name problem)
### - incorporate automatic unzipping (for pre-processing)
### - learn more about python GUI modules: Tkinter and pyGTK
### - switch optparse to argparse
### - update building of query string using append or join

#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import requests
import optparse
import tkMessageBox
import xml.etree.ElementTree as etree
from datetime import date
from Tkinter import *

################################################################################
class OptionParser (optparse.OptionParser):

    def check_required(self, opt):
        option = self.get_option(opt)

    # assumes the option's 'default' is set to None!
        if getattr(self.values, option.dest) is None:
            self.error('{} option not supplied'.format(option))

################################################################################

# function checks for existance of ESA kml file
def check_kml():
    if os.path.exists('S2A_OPER_GIP_TILPAR_MPC__20151209T095117'
            '_V20150622T000000_21000101T000000_B00.kml') == False:
        print '\n--------------------------------------------------------------'
        print 'Please download the ESA Sentinel-2 kml file!'
        print 'See README.md for details.'
        print '--------------------------------------------------------------\n'
        sys.exit(-1)

# function returns center coordinates of tile, if the tile exists
## this will be changed to polygon coordintes instead of points
def tile_point(tile):
    print '\n------------------------------------------------------------------'
    print 'Hold on while we check the kml for the tile\'s center point!'
    kml_file = ('S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000'
        '_21000101T000000_B00.kml')

    tree = etree.parse(kml_file)
    # get all placemarks
    placemarks = tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark')

    # initialize empty list to fill, or not
    coords = []
    # iterate through the attributes within each placemark
    for attributes in placemarks:
        for subAttribute in attributes:
            # iterate through the names of each placemark
            name = attributes.find('.//{http://www.opengis.net/kml/2.2}name')
            # if the name is the same as the defined tile, get coordinates
            if name.text == tile:
                # find the center point tag
                points = attributes.find('.//{http://www.opengis.net/kml/2.2}'
                    'Point')
                # have to go in deeper, thanks to etree
                for unit in points:
                    # save the center point values as a list
                    coords = (unit.text).split(',')
                    # ['longitude', 'latitude', 'vertical']
                    return coords
    # if list is still empty after loop, tile was not found
    if not coords:
        print 'Tile not found. Try again.'
        sys.exit(-1)

# function returns tiles incldued in a package/file
def return_tiles(uuid_element, filename):
    # create link to search for tile/granule data
    granule_link = (huburl + "odata/v1/Products"
        "('{}')/Nodes('{}')/Nodes('GRANULE')/Nodes").format(
        uuid_element, filename)

    # GET request from hub and essentially parse it
    response = session.get(granule_link, stream=True)
    granule_tree = etree.fromstring(response.content)
    # search for all entires (i.e. tiles)
    granule_entries = granule_tree.findall('{http://www.w3.org/2005/Atom}entry')

    # empty string to fill with all tiles in the file
    granules = ''

    # go through each tile appending each name to string
    for granule_entry in range(len(granule_entries)):
        # UUID element creates the path to the file
        granule_dir_name = (granule_entries[granule_entry].find(
            '{http://www.w3.org/2005/Atom}title')).text
        granule = granule_dir_name[50:55]
        granules = granules + ' ' + granule

    # print the number of tiles and their names
    print '# of Tiles: ' + str(len(granule_entries))
    print 'Tiles:' + granules

################################################################################

#------------------------------------------------------------------------------#
#                             Parse command line                               #
#------------------------------------------------------------------------------#
if len(sys.argv) == 1:
    prog = os.path.basename(sys.argv[0])
    print '\n        ' + sys.argv[0] + ' [options]'
    print '        Help: ', prog, ' --help'
    print '        or: ', prog, ' -h'
    print 'example python ' + sys.argv[0] + ' --lat 43.6 --lon 1.44\n'
    sys.exit(-1)
else:
    usage = 'usage: %prog [options] '
    parser = OptionParser(usage=usage)

    # authorization and directory related commands
    parser.add_option('-a', '--auth', dest='auth', action='store', \
            type='string', help='Sentinels Scientific Data Hub account and '
            'password file, if available')
    parser.add_option('-w', '--write_dir', dest='write_dir', action='store', \
            type='string', help='Path where products should be downloaded', \
            default='')
    parser.add_option('-r', dest='MaxRecords', action='store', type='int', \
            help='Maximum number of records to download (default=100)', \
            default=100)
    parser.add_option('--hub', dest='hub', action='store_true',  \
            help='Try other hubs if apihub is not working', default=None)

    # location related commands
    parser.add_option('-t', '--tile', dest='tile', action='store', \
            type='string', help='Sentinel-2 Tile number', default=None)
    parser.add_option('-l', '--location', dest='location', action='store', \
            type='string', help='Town name (pick one which is not too '
            'frequent to avoid confusions)', default=None)
    parser.add_option('--lat', dest='lat', action='store', type='float', \
            help='Latitude in decimal degrees', default=None)
    parser.add_option('--lon', dest='lon', action='store', type='float', \
            help='Longitude in decimal degrees', default=None)
    parser.add_option('--latmin', dest='latmin', action='store', type='float', \
            help='Min latitude in decimal degrees', default=None)
    parser.add_option('--latmax', dest='latmax', action='store', type='float', \
            help='Max latitude in decimal degrees', default=None)
    parser.add_option('--lonmin', dest='lonmin', action='store', type='float', \
            help='Min longitude in decimal degrees', default=None)
    parser.add_option('--lonmax', dest='lonmax', action='store', type='float', \
            help='Max longitude in decimal degrees', default=None)

    # other Sentinel file related command parameters
    parser.add_option('-s', '--sentinel', dest='sentinel', action='store', \
            type='string', help='Sentinel mission considered (e.g. S1 or S2)', \
            default='S2')
    parser.add_option('-d', '--start_date', dest='start_date', action='store', \
            type='string', help='Start date, fmt("2015-12-22")', default=None)
    parser.add_option('-f', '--end_date', dest='end_date', action='store', \
            type='string', help='End date, fmt("2015-12-23")', default=None)
    parser.add_option('-c', '--max_cloud', dest='max_cloud', action='store', \
            type='float', help='Only search for products up to a certain '
            'cloud percentage (e.g. 50 for 50%)', default=None)
    parser.add_option('-o', '--orbit', dest='orbit', action='store', \
            type='int', help='Orbit path number', default=None)

# currently unused commands that could be built into the script at a later date
    # parser.add_option('-n', '--no_download', dest='no_download', \
    #        action='store_true', help='Do not download products, just '
    #        'print aria2 command', default=False)
    # parser.add_option('-p', '--proxy_passwd', dest='proxy', \
    #        action='store', type='string', help='Proxy account and '
    #        'password file', default=None)
    # parser.add_option('--id', '--start_ingest_date', \
    #         dest='start_ingest_date', action='store', type='string', \
    #         help='start ingestion date, fmt("2015-12-22")', default=None)
    # parser.add_option('--if', '--end_ingest_date', dest='end_ingest_date', \
    #         action='store', type='string', help='end ingestion date, \
    #         fmt("2015-12-23")', default=None)

    (options, args) = parser.parse_args()

# tile query check
if options.tile != None and options.sentinel != 'S2':
    print 'The tile option (-t) can only be used for Sentinel-2!'
    sys.exit(-1)

# set data source (apihub vs dhus -- more could be added)
if options.hub == None:
    huburl = 'https://scihub.copernicus.eu/apihub/'
elif options.hub == 'dhus':
    huburl = 'https://scihub.copernicus.eu/dhus/'
# # untested
# elif options.hub == 'zamg':
#     huburl = 'https://data.sentinel.zamg.ac.at/api/'

# build in checks for valid commands ::: spatial aspect
if options.tile == None or options.tile == '?':
    if options.location == None:
        if options.lat == None or options.lon == None:
            if (options.latmin == None or options.lonmin == None
                    or options.latmax == None or options.lonmax == None):
                # explain problem and give example
                print '\nPlease provide at least one point/rectangle/location!'
                print '\nExamples:'
                print '\tPoint: python iq_download.py --lat 47.083 --lon 12.842'
                print '\tPolygon: python iq_download.py --latmin 46 ' \
                    '--latmax 48 --lonmin 12 --lonmax 14'
                print '\tLocation: python iq_download.py -l Vienna\n'
                sys.exit(-1)
            else:
                geom = 'rectangle'
        else:
            if (options.latmin == None and options.lonmin == None
                    and options.latmax == None and options.lonmax == None):
                geom = 'point'
            else:
                print '\nPlease choose either point or rectangle, but not both!'
                print '\nExamples:'
                print '\tPoint: python iq_download.py --lat 47.083 --lon 12.842'
                print '\tPolygon: python iq_download.py --latmin 46 ' \
                    '--latmax 48 --lonmin 12 --lonmax 14\n'
                sys.exit(-1)
    else:
        if (options.latmin == None and options.lonmin == None
                and options.latmax == None and options.lonmax == None
                and options.lat == None or options.lon == None):
            geom = 'location'
        else:
            print '\nPlease choose location and coordinates, but not both!\n'
            print '\nExamples:'
            print '\tPoint: python iq_download.py --lat 47.083 --lon 12.842'
            print '\tPolygon: python iq_download.py --latmin 46 --latmax 48 ' \
                '--lonmin 12 --lonmax 14'
            print '\tLocation: python iq_download.py -l Vienna\n'
            sys.exit(-1)
else:
    # quits if kml file not there
    check_kml()
    # quits if the tile doesn't exist, otherwise returns center coordinates
    coords = tile_point(options.tile)
    options.lon = coords[0]
    options.lat = coords[1]
    print 'The center point is: ' + options.lat + ', ' + options.lon
    geom = 'point'

# create spatial parts of the query ::: point, rectangle or location name
# beware of the quotation marks!!
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

# add orbit, if defined (default: NONE)
if options.orbit == None:
    query_orb = query_geom
else:
    query_orb = '({}) AND (relativeorbitnumber:{})'.format(
        query_geom, options.orbit)

# add Sentinel mission
if options.sentinel == 'S2':
    query_slc = '{} AND (platformname:Sentinel-2)'.format(query_orb)
elif options.sentinel == 'S1':
    query_slc = '{} AND (platformname:Sentinel-1)'.format(query_orb)
else:
    query_slc = query_orb

# add dates of capture
if options.start_date != None:
    start_date = options.start_date
else:
    start_date = '2015-06-13' # Sentinel-2 launch date

if options.end_date != None:
    end_date = options.end_date
else:
    end_date = date.today().isoformat()

query_time = ('{} AND (beginPosition:[{}T00:00:00.000Z TO {}T23:59:59.999Z] '
    'AND endPosition:[{}T00:00:00.000Z TO {}T23:59:59.999Z])').format(
    query_slc, start_date, end_date, start_date, end_date)

# cloud cover query
if options.max_cloud != None:
    query = '{} AND  (cloudcoverpercentage:[0.0 TO {}])'.format(
        query_time, options.max_cloud / 100)
else:
    query = query_time

#------------------------------------------------------------------------------#
#                          Read authentification file                          #
#------------------------------------------------------------------------------#
# use this part if you want to have your password and username saved in a
# textfile, with the file name as the command
if options.auth != None:
    parser.check_required('-a')
    try:
        f = file(options.auth)
        (account,passwd) = f.readline().split(' ')
        if passwd.endswith('\n'):
            passwd=passwd[:-1]
        f.close()
    except:
        print 'Error with password file.'
        sys.exit(-2)

# authenticate at data hub
else:
    url =  huburl + 'search?q='
    account = raw_input ('Username: ')
    passwd = raw_input ('Password: ')

    # start session/authorization using requests module
    session = requests.Session()
    session.auth = (account, passwd)

#------------------------------------------------------------------------------#
#                Prepare aria2 command line to search catalog                  #
#------------------------------------------------------------------------------#

# check for existing xml-file, delete if present
if os.path.exists('query_results.xml'):
    os.remove('query_results.xml')

# set query variables used throughout the script
url_search = huburl + 'search?q='
wg = 'aria2c --check-certificate=false'
auth = '--http-user="{}" --http-passwd="{}"'.format(account, passwd)
search_output = ' --continue -o query_results.xml'
wg_opt = ' -o '

# execute command to download and save query as xml-file in the same location
# as the python script
command_aria = '{} {} {} "{}{}&rows={}"'.format(
    wg, auth, search_output, url_search, query, options.MaxRecords)

print command_aria
os.system(command_aria)

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
    sentinel_link = (huburl + "odata/v1/Products('" + uuid_element + "')/$value")

    # the title element contains the corresponding file name
    title_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
        'title')).text
    summary_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
        'summary')).text
    filename = (entries[entry].find('.//*[@name="filename"]')).text

    # print each entry's info
    print "\n------------------------------------------------------------------"
    print 'Scene ', entry + 1, 'of ', len(entries)
    print title_element
    print summary_element
    # return tile names per entry using function return_tiles if desired
    if options.tile == '?':
        return_tiles(uuid_element, filename)
    # find cloud cover percentage
    cloud_element = (entries[entry].find('.//*[@name="cloudcoverpercentage"]')
        ).text
    print 'Cloud cover percentage: ' + cloud_element
    print sentinel_link

    # return the size
    size_element = (entries[entry].find('.//*[@name="size"])').text
    # parse size to float and add to running total of size
    if 'GB' in size_element:
        size_element = size_element.replace(' GB', '')
        size_element = float(size_element)
        total_size += size_element
    elif 'MB' in size_element:
        size_element = size_element.replace(' MB', '')
        size_element = float(size_element) / 1024
        size_element = size_element
        total_size += size_element

    # check if file was already downloaded
    zipfile = title_element + '.zip'
    if os.path.exists(zipfile):
        print zipfile, ' has already been downloaded!',
     # do not download the product if it was already downloaded and unzipped
    if os.path.exists(title_element):
        print title_element, ' already exists in unzipped form!',

        continue

#------------------------------------------------------------------------------#
#                            Downloader message box                            #
#------------------------------------------------------------------------------#

# turn the total size of scenes found back into text
total_size = '{0:.2f}'.format(total_size) + ' GB'

# question to continue based on the number of scenes found
question = 'Number of scenes found: ' + str(scenes) + \
    '\nTotal size of scenes: ' + total_size + \
    '\n\nDo you want to download all results?'

# hide main window
root = Tk().withdraw()
# content of window
messagebox = tkMessageBox.askyesno('Sentinel Downloader', question)
if messagebox == True:
   	# download all whole scenes matching the query
    for entry in range(len(entries)):
        # create download command for the entry
        uuid_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
            'id')).text
        sentinel_link = (huburl + "odata/v1/Products('"
            + uuid_element + "')/$value")
        title_element = (entries[entry].find('{http://www.w3.org/2005/Atom}'
            'title')).text

        # if write_dir defined, save there, otherwise save to folder where
        # the python script is located
        if options.write_dir != '':
            command_aria = '{} {} --dir {} {}{} "{}"'.format(wg, auth,
                options.write_dir, wg_opt, zipfile, sentinel_link)
        else:
            command_aria = '{} {} {}{}{} "{}"'.format(wg, auth, wg_opt,
                options.write_dir, zipfile, sentinel_link)

        # execute download
        os.system(command_aria)
        print 'Downloaded Scene #' + str(entry + 1)

    print '\n------------------------------------------------------------------'
    print 'Downloading complete!'
    print '------------------------------------------------------------------\n'

else:
    print '\n------------------------------------------------------------------'
    print 'Nothing downloaded, but xml file saved!'
    print '------------------------------------------------------------------\n'
