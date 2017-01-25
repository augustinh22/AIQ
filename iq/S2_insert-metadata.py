#!/usr/bin/python

import os
import sys
import datetime
import fnmatch
from osgeo import gdal, osr

import psycopg2

import iqm_db

def bailout(message):
    print message
    sys.exit()

def getDirectorylist(rootdirectory, sensortype):

    #
    # Directorypattern is the pattern that is used to search for the folder.
    # Note that currently only the beginning of the foldername is used.
    #
    directorypattern = None
    if sensortype == "Landsat-8":
        directorypattern = "LC8"

    if sensortype == "CORINE":
        directorypattern = "g100_clc"

    if sensortype == "Sentinel-2":
        directorypattern = "S2A"  # Note new structure tile names (L1C*) are previously changed in restructure.py

    #
    # directories keeps the list with the directory names
    #
    directories = []

    #
    # get all directoies in the root directory
    #
    for root, dirnames, filenames in os.walk(rootdirectory):
        for dirname in dirnames:

            #
            # If the name is qualified, append it to the directories array
            #
            if dirname.startswith(directorypattern):
                directories.append(dirname)

    #
    # Return the sorted array.
    # Note: Usually, the sorted array will sort it by date if it is in the name
    #
    return sorted(directories)

def getDates(dirname, sensortype):

    if sensortype == "Landsat-8":

        #
        # Extract year and day of year
        #
        dateinfo = dirname[9:-5]
        year = int(dateinfo[:-3])
        doy = int(dateinfo[4:])

        #
        # Convert to ANSI date
        #
        date = datetime.datetime(year, 1, 1) + datetime.timedelta(doy - 1)
        delta = date - datetime.datetime(1601, 1, 2) # somehow there is one day too much, investigate later

        #
        # Return ANSI date and date
        #
        return [str(delta.days), str(date)[0:10]]

    if sensortype == "CORINE":

        #
        # Extract year
        #
        year = int("20" + dirname[8:10])

        #
        # Convert to ANSI data
        #
        date = datetime.datetime(year, 1, 1)
        delta = date - datetime.datetime(1601, 1, 2)

        #
        # Return ANSI date and date
        #
        return [str(delta.days), str(date)[0:10]]

    if sensortype == "Sentinel-2":

        #
        # New S2 data format.
        #
        if dirname.startswith('S2AL1C_'):

            name_parts = dirname.split("_")
            datetimeinfo = name_parts[3]

        #
        # Old S2 data format.
        #
        if dirname.startswith('S2A_OPER_'):

            name_parts = dirname.split("_")
            datetimeinfo = name_parts[7]

        #
        # Extract year and day of year
        #
        dateinfo = datetimeinfo[:8]
        year = dateinfo[:4]
        month = dateinfo[4:6]
        day = dateinfo[6:]
        fmt = '%Y.%m.%d'
        s = '{}.{}.{}'.format(year, month, day)
        dt = datetime.datetime.strptime(s, fmt)
        tt = dt.timetuple()
    	doy = int(tt.tm_yday) # Extract doy
        year = int(year)

        #
        # Convert to ANSI date
        #
        date = datetime.datetime(year, 1, 1) + datetime.timedelta(doy - 1)
        delta = date - datetime.datetime(1601, 1, 2) # somehow there is one day too much, investigate later

        #
        # Return ANSI date and date
        #
        return [str(delta.days), str(date)[0:10]]

def GetExtent(gt,cols,rows):
    #
    #    from here: http://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings
    #

    ext=[]
    xarr=[0,cols]
    yarr=[0,rows]

    for px in xarr:
        for py in yarr:
            x=gt[0]+(px*gt[1])+(py*gt[2])
            y=gt[3]+(px*gt[4])+(py*gt[5])
            ext.append([x,y])
        yarr.reverse()
    return ext

def getFileinformation(file):

    #
    # This is the object with the fileinformation that should be extracted
    #
    fileinfo = {
        "extent":{
            "geo": {},
            "temp": {}
        },
        "epsg": None,
        "z_position": None
    }

    #
    # Open the file with gdal
    #
    datafile = gdal.Open(file)

    #
    # Extract the xtent in pixel
    #
    fileinfo["extent"]["geo"]["px_width"] = datafile.RasterXSize
    fileinfo["extent"]["geo"]["px_height"] = datafile.RasterYSize

    #
    # Extract the extent in coordinates
    #
    gt = datafile.GetGeoTransform()
    ext = GetExtent(gt, datafile.RasterXSize, datafile.RasterYSize)

    fileinfo["extent"]["geo"]["source_xmin"] = int(ext[0][0])
    fileinfo["extent"]["geo"]["source_xmax"] = int(ext[2][0])
    fileinfo["extent"]["geo"]["source_ymin"] = int(ext[2][1])
    fileinfo["extent"]["geo"]["source_ymax"] = int(ext[0][1])

    #
    # Extract the spatial reference System
    #
    srs = osr.SpatialReference()
    srs.ImportFromWkt(datafile.GetProjection())
    if srs.GetAttrValue("AUTHORITY", 0) != "EPSG":
        bailout("Need EPSG as SRS authority")
    fileinfo["epsg"] = srs.GetAttrValue("AUTHORITY", 1)

    #
    # Return that information for this file
    #
    return fileinfo

def getFilemetadata(rootdirectory, directorylist, sensortype, product):

    if product == "SIAM_AIQ":
        filepattern = "SIAM_stack_"
    elif product == "CORINE":
        filepattern = "g100_clc*class"
    else:
        return

    #
    # This is the extension of the file. Currently, it is set to tif
    #
    extension = "tif"

    #
    # Z-Position is the vertical position in te stack
    #
    z_pos_start = 0
    z_position = z_pos_start

    #
    # files is the array where the metadata is stored
    #
    files = []

    #
    # Walk thrugh all files in the directory
    #
    for directory in directorylist:

        #
        # Extract the dates. This is depending on the sensortype and should be included in the name
        #
        dates = getDates(directory, sensortype)

        #
        # Walk through all files in the current directory
        #
        for file in os.listdir(rootdirectory + "/" + directory):
            if fnmatch.fnmatch(file, '*' + filepattern + '*' + extension):

                #
                # If this is our main file, extract the file informion
                #
                fileinfo = getFileinformation(rootdirectory + "/" + directory + "/" + file)
                fileinfo["extent"]["temp"]["ansidate"] = dates[0]
                fileinfo["extent"]["temp"]["date"] = dates[1]
                fileinfo["z_position"] = z_position

                # TODO: Extract pixelsize automatically
                if sensortype == "Landsat-8":
                    fileinfo["filename"] = directory
                    fileinfo["pixelsize"] = 30

                if sensortype == "CORINE":
                    fileinfo["filename"] = file

                    #
                    # Override EPSG here, it is somehow not correctly detected
                    #
                    fileinfo["epsg"] = 3035
                    fileinfo["pixelsize"] = 100

                if sensortype == "Sentinel-2":
                    fileinfo["filename"] = directory
                    fileinfo["pixelsize"] = 10

                #
                # Add the fileinfo to the array
                #
                files.append(fileinfo)

                #
                # Increment the vertical positoon
                #
                z_position += 1

    #
    # Return the list with the filenames
    #
    return files

def getTempExtent(files):
    ansimin = 9999999999
    ansimax = -9999999999

    for fileinfo in files:
        ansidate = int(fileinfo["extent"]["temp"]["ansidate"])

        if ansidate < ansimin:
            ansimin = ansidate

        if ansidate > ansimax:
            ansimax = ansidate

    return {"ansimin": ansimin, "ansimax": ansimax}

def getGeoExtent(files):
    source_xmin = 9999999999
    source_xmax = -9999999999
    source_ymin = 9999999999
    source_ymax = -9999999999

    px_width = -9999999999
    px_height = -9999999999

    for fileinfo in files:
        if int(fileinfo["extent"]["geo"]["source_xmin"]) < source_xmin:
            source_xmin = int(fileinfo["extent"]["geo"]["source_xmin"])

        if int(fileinfo["extent"]["geo"]["source_xmax"]) > source_xmax:
            source_xmax = int(fileinfo["extent"]["geo"]["source_xmax"])

        if int(fileinfo["extent"]["geo"]["source_ymin"]) < source_ymin:
            source_ymin = int(fileinfo["extent"]["geo"]["source_ymin"])

        if int(fileinfo["extent"]["geo"]["source_ymax"]) > source_ymax:
            source_ymax = int(fileinfo["extent"]["geo"]["source_ymax"])

        if int(fileinfo["extent"]["geo"]["px_width"]) > px_width:
            px_width = int(fileinfo["extent"]["geo"]["px_width"])

        if int(fileinfo["extent"]["geo"]["px_height"]) > px_height:
            px_height = int(fileinfo["extent"]["geo"]["px_height"])

    return {"source_xmin": source_xmin,
            "source_xmax": source_xmax,
            "source_ymin": source_ymin,
            "source_ymax": source_ymax,
            "px_width": px_width,
            "px_height": px_height}

def extractMetadata(rootdirectory, sensortype, product, tile=None):

    global debugging

    collectionCLS = None
    collectionSHP = None
    collectionMSK = None

    #
    # Determine names of collections based on sensor type.
    #
    if sensortype == "CORINE":
        datasetTitle = "CORINE"
        description = "This is the CORINE land use / land cover class layer."
        collectionCLS = "CORINE_CLS"
        collectionSHP = "CORINE_SHP"

    if sensortype == "Sentinel-2":
        datasetTitle = "S2toSIAM"
        description = ("These are data processed using SIAM, based on"
            " Copernicus Sentinel-2 satellite imagery.")
        collectionCLS = 'S2_{}_CLS'.format(tile)
        collectionMSK = 'S2_{}_MSK'.format(tile)

    metadata = {

        #
        # The name of the dataset as it should be shown in IQ
        #
        "name": datasetTitle,

        #
        # The description that should be shown in IQ
        #
        "description": description,

        #
        # Whether this dataset should only be visible for certain user (groups) in IQ. Set to false as
        # this does not have any effect currently
        #
        "protected": "false",

        #
        # Sensortype, Landsat etc
        #
        "sensor": sensortype,

        #
        # Main product. This is only used to extract metadata such as extent etc.
        #
        "product": product,

        #
        # Don't change this
        #
        "baseurl": "http://iq.zgis.at",

        #
        # This will be populated automatically
        #
        "files": None,
        "extent": {
            "temp": None,
            "geo": None
        },

        #
        # The preprocessing layers
        #
        "preprocessing" : {

            #
            # Layers
            #
            "layers": [
                {
                    "acro": "SIAM33SHRD",
                    "name": "SIAM 33",
                    "description": "This is the SIAM 33 shared spectral categories layer.",
                    "order": 0,
                    "belongs_to_collection": collectionCLS
                },
                {
                    "acro": "SIAM96",
                    "name": "SIAM 96",
                    "description": "This is the SIAM 96 spectral categories layer.",
                    "order": 1,
                    "belongs_to_collection": collectionCLS
                },
                {
                    "acro":"SIAMVEGBI",
                    "name": "SIAM vegetation binary mask",
                    "description": "This is the SIAM binary vegetation mask.",
                    "order": 0,
                    "belongs_to_collection": collectionMSK
                },
                {
                    "acro": "SIAMURBAN",
                    "name": "SIAM urban mask",
                    "description": " This is the SIAM urban area seed pixel binary mask.",
                    "order": 1,
                    "belongs_to_collection": collectionMSK
                }
            ],

            #
            # Collections
            #
            "collections": [{
                "name": collectionCLS,
                "type": "categorical",
                "complex": True
            }, {
                "name": collectionMSK,
                "type": "categorical",
                "complex": True
            }]
        }
    }

    #
    # Get the list of directories where the data is stored. This is dependent on the sensor.
    #
    directorylist = getDirectorylist(rootdirectory, metadata["sensor"])

    if debugging == True:
        print directorylist

    files = getFilemetadata(rootdirectory, directorylist, metadata["sensor"], metadata["product"])

    if debugging == True:
        print files

    metadata["files"] = files
    metadata["extent"]["temp"] = getTempExtent(files)
    metadata["extent"]["geo"] = getGeoExtent(files)
    return metadata

def getThumbnail():
    # TODO generate thumbnail
    return ''

def insertPreprocessinginformation(layers):
    global db
    global debugging


    #
    # Open cursor
    #
    cur = db.cursor()

    #
    # Iterate through the layers that are provided
    #
    for layer in layers:

        #
        # Check whether the layer exists already based on the acronym.
        # This should be safe since acro is unique
        # With postgres > 9.6 it is possible to combine the two steps
        #
        sql = """SELECT exists (SELECT 1 FROM iq_preprocessing WHERE acro = %s LIMIT 1)"""
        cur.execute(sql, (layer["acro"],))
        exists = cur.fetchone()[0]

        #
        # If it does not exst, insert the new layer in the metadata database
        #
        if exists == False:
            sql = """INSERT INTO
                        iq_preprocessing (acro, name, description)
                    VALUES
                        (%s, %s, %s)"""
            cur.execute(sql, (layer["acro"], layer["name"], layer["description"]))

            if debugging == False:
                db.commit()

    #
    # Close cursor
    #
    cur.close()

def getPreprocessingids(layers):
    ids = []
    cur = db.cursor()
    for layer in layers:
        sql = """SELECT id FROM iq_preprocessing WHERE acro=%s"""
        cur.execute(sql,(layer["acro"],))
        ids.append(cur.fetchone()[0])
    cur.close()
    return ids

def insertMetadata(metadata):
    global db
    global debugging

    cur = db.cursor()

    # ---------------------------------------------------------------- #
    # IQ_preprocessing
    # ---------------------------------------------------------------- #

    #
    # Insert new informationlayers that have not been added to the
    # database yet
    #
    insertPreprocessinginformation(metadata["preprocessing"]["layers"])

    # ---------------------------------------------------------------- #
    # IQ_Sensor
    # ---------------------------------------------------------------- #

    #
    # Get the sesorid. This is used in a later step
    #
    sql = """SELECT id FROM iq_sensor WHERE name = %s"""
    cur.execute(sql, (metadata["sensor"],))
    sensorid = cur.fetchone()[0]

    # ---------------------------------------------------------------- #
    # IQ_site
    # ---------------------------------------------------------------- #

    #
    # Import the main metadata of the dataset. This is currently called iq_site and will be renamed later.
    # Then, retrieve the id. This is used in alater step
    #
    sql = """INSERT INTO
                iq_site (name,description,protected,thumbnail)
              VALUES
                (%s,%s,%s,%s)
              RETURNING id"""
    cur.execute(sql, (metadata["name"], metadata["description"], metadata["protected"], getThumbnail()))
    siteid = cur.fetchone()[0]

    #
    # Commit changes to the database
    #
    if debugging == False:
        db.commit()

    # ---------------------------------------------------------------- #
    # IQ_datasource
    # ---------------------------------------------------------------- #

    #
    # Insert datasource and retrieve id
    #
    sql = """INSERT INTO
                iq_datasource (siteid, baseurl, ansimin, ansimax, source_xmin, source_xmax, source_ymin, source_ymax, px_width, px_height)
              VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
              RETURNING id"""
    cur.execute(sql, (siteid,
                      metadata["baseurl"],
                      metadata["extent"]["temp"]["ansimin"],
                      metadata["extent"]["temp"]["ansimax"],
                      metadata["extent"]["geo"]["source_xmin"],
                      metadata["extent"]["geo"]["source_xmax"],
                      metadata["extent"]["geo"]["source_ymin"],
                      metadata["extent"]["geo"]["source_ymax"],
                      metadata["extent"]["geo"]["px_width"],
                      metadata["extent"]["geo"]["px_height"],
                      ))
    datasourceid = cur.fetchone()[0]

    #
    # Commit changes to the database
    #
    if debugging == False:
        db.commit()

    # ---------------------------------------------------------------- #
    # IQ_dataset
    # ---------------------------------------------------------------- #

    #
    # Import dataset and return the ids
    #
    sql = """INSERT INTO
                iq_dataset (datasourceid, sensorid, ansidate, date, zposition, source_xmin, source_xmax, source_ymin, source_ymax, px_width, px_height, filename, epsg, pixelsize)
              VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s) RETURNING id"""

    datasetids = []
    for file in metadata["files"]:
        cur.execute(sql, (
            datasourceid,
            sensorid,
            file["extent"]["temp"]["ansidate"],
            file["extent"]["temp"]["date"],
            file["z_position"],
            file["extent"]["geo"]["source_xmin"],
            file["extent"]["geo"]["source_xmax"],
            file["extent"]["geo"]["source_ymin"],
            file["extent"]["geo"]["source_ymax"],
            file["extent"]["geo"]["px_width"],
            file["extent"]["geo"]["px_height"],
            file["filename"],
            file["epsg"],
            file["pixelsize"]
        ))
        datasetids.append(cur.fetchone()[0])

    #
    # Commit changes to the database
    #
    if debugging == False:
        db.commit()

    # ---------------------------------------------------------------- #
    # IQ_dataset_preprocessing
    # ---------------------------------------------------------------- #

    #
    # Retrieve the preprocessing ids
    #
    preprocessingids = getPreprocessingids(metadata["preprocessing"]["layers"])

    #
    # Insert to the join table that connects the dataset with the preprocessing
    #
    sql = """INSERT INTO
                iq_dataset_preprocessing (datasetid,preprocessingid)
              VALUES
                (%s, %s)"""
    for did in datasetids:
        for pid in preprocessingids:
            cur.execute(sql, (did, pid))

    #
    # Commit changes to the database
    #
    if debugging == False:
        db.commit()

    # ---------------------------------------------------------------- #
    # IQ_collection
    # ---------------------------------------------------------------- #

    #
    # Insert into collection. The collection is the spatio-temporal stack
    #
    sql = """INSERT INTO
                iq_collection (siteid, name, datatype, scoll, complex)
             VALUES
                (%s, %s, %s, %s, %s)"""

    #
    # Scoll is the acro that is used in the query.
    # This should be designed better
    #
    scoll = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']  # omg

    for i, collection in enumerate(metadata["preprocessing"]["collections"]):
        cur.execute(sql, (siteid, collection["name"], collection["type"], scoll[i], collection["complex"]))

    #
    # Commit changes to the database
    #
    if debugging == False:
        db.commit()

    # ---------------------------------------------------------------- #
    # IQ_collection_preprocessing
    # ---------------------------------------------------------------- #

    #
    # Insert into the join table that connects the collection with the preprocessing
    #
    sql = """INSERT INTO
        iq_collection_preprocessing (collectionid,preprocessingid,layerorder)
      VALUES
        ((SELECT id FROM iq_collection WHERE name = %s),
         (SELECT id FROM iq_preprocessing WHERE acro = %s),%s)"""

    for item in metadata["preprocessing"]["layers"]:
        acro = item["acro"]
        collection = item["belongs_to_collection"]
        order = item["order"]

        cur.execute(sql, (collection, acro, order))

    #
    # Commit changes to the database
    #
    if debugging == False:
        db.commit()

    cur.close()

def deleteMetadata(coverageName):
    # TODO: Implement
    pass

if __name__ == "__main__":

    debugging = False
    deleteCoverages = False

    db = iqm_db.getDatabaseConnection()

    if deleteCoverages == False:
        #
        # Extract the metadata
        #

        # California fire example. EPSG: 32611
            # Classes
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_EPA__20151022T184002_A001740_T11SLV_N02.04/SIAM_stack_S2_11SLV_CLS.tif', "Sentinel-2", "SIAM_AIQ", tile="11SLV")
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_MPS__20160519T184433_A004743_T11SLV_N02.02/SIAM_stack_S2_11SLV_CLS.tif', "Sentinel-2", "SIAM_AIQ", tile="11SLV")
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_MPS__20160728T183826_A005744_T11SLV_N02.04/SIAM_stack_S2_11SLV_CLS.tif', "Sentinel-2", "SIAM_AIQ", tile="11SLV")
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_MPS__20161105T183542_A007174_T11SLV_N02.04/SIAM_stack_S2_11SLV_CLS.tif', "Sentinel-2", "SIAM_AIQ", tile="11SLV")
            # Masks
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_EPA__20151022T184002_A001740_T11SLV_N02.04/SIAM_stack_S2_11SLV_MSK.tif', "Sentinel-2", "SIAM_AIQ", tile="11SLV")
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_MPS__20160519T184433_A004743_T11SLV_N02.02/SIAM_stack_S2_11SLV_MSK.tif', "Sentinel-2", "SIAM_AIQ", tile="11SLV")
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_MPS__20160728T183826_A005744_T11SLV_N02.04/SIAM_stack_S2_11SLV_MSK.tif', "Sentinel-2", "SIAM_AIQ", tile="11SLV")
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_MPS__20161105T183542_A007174_T11SLV_N02.04/SIAM_stack_S2_11SLV_MSK.tif', "Sentinel-2", "SIAM_AIQ", tile="11SLV")


        # Asyut, Egypt example. EPSG: 32636
            # Classes
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_SGS__20160110T085036_A002878_T36RUR_N02.01/SIAM_stack_2_36RUR_CLS.tif', "Sentinel-2", "SIAM_AIQ", tile="36RUR")
        # metadata = extractMetadata('C:/tempS2/S2AL1C_T36RUR_A008026_20170104T083845/SIAM_stack_S2_36RUR_CLS.tif', "Sentinel-2", "SIAM_AIQ", tile="36RUR")
            # Masks
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_SGS__20160110T085036_A002878_T36RUR_N02.01/SIAM_stack_S2_36RUR_MSK.tif', "Sentinel-2", "SIAM_AIQ", tile="36RUR")
        # metadata = extractMetadata('C:/tempS2/S2AL1C_T36RUR_A008026_20170104T083845/SIAM_stack_S2_36RUR_MSK.tif', "Sentinel-2", "SIAM_AIQ", tile="36RUR")


        # Bidi Bidi refugee camp example. EPSG: 32636
            # Classes
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_SGS__20160213T082324_A003364_T36NUJ_N02.01/SIAM_stack_S2_36NUJ_CLS.tif', "Sentinel-2", "SIAM_AIQ", tile="36NUJ")
        # metadata = extractMetadata('C:/tempS2/S2AL1C_T36NUJ_A008083_20170108T082804/SIAM_stack_S2_36NUJ_CLS.tif', "Sentinel-2", "SIAM_AIQ", tile="36NUJ")
            # Masks
        # metadata = extractMetadata('C:/tempS2/S2A_OPER_MSI_L1C_TL_SGS__20160213T082324_A003364_T36NUJ_N02.01/SIAM_stack_S2_36NUJ_MSK.tif', "Sentinel-2", "SIAM_AIQ", tile="36NUJ")
        # metadata = extractMetadata('C:/tempS2/S2AL1C_T36NUJ_A008083_20170108T082804/SIAM_stack_S2_36NUJ_MSK.tif', "Sentinel-2", "SIAM_AIQ", tile="36NUJ")


        if debugging == True:
            print metadata

        #
        # Insert the metadata
        #
        insertMetadata(metadata)
    else:

        coverageName = 'Test'
        deleteMetadata(coverageName)
