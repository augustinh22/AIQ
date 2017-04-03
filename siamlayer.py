#-------------------------------------------------------------------------------
# Name:        Single Layer for IQ.
# Purpose:     This script creates one layer for import into IQ based
#              on SIAM output and NoData cells.
#
# Author:      h.Augustin
#
# Created:     29.03.2017
#
#-------------------------------------------------------------------------------

#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import fnmatch
import datetime
import Tkinter
import tkMessageBox

import gdal
import numpy
import scipy.ndimage


def siam_folders(root_folder):

    '''This function creates a list of siamoutput folder paths.'''

    siamFolders = []

    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=True):
        for dirname in dirnames:
            if (dirname == 'siamoutput'
                    and fnmatch.fnmatch(dirpath, '*PROC_DATA*')):
                siamFolders.append(os.path.join(dirpath, dirname))

    return siamFolders


def siam_layer(siam_folders, stack_type, layer_endings, start_time):

    '''This function will create a layer of defined SIAM semi-concepts, saving
        it to the tile folder.'''

    for folder in siam_folders:

        #
        # Create new list of desired layers depending on stack type.
        #
        siam_layers = []

        for dirpath, dirnames, filenames in os.walk(folder, topdown=True):
            for filename in filenames:
                for layer in layer_endings:
                    if filename.endswith(layer):
                        siam_layers.append(os.path.join(dirpath, filename))
                        example = filename

        siam_layers.sort

        #
        # Generate name of layer, based on defined type.
        #
        layer_name = generate_name(folder, example, stack_type)

        #
        # Create tiff file in folder for layer.
        #
        outDs, outData = create_tif(siam_layers[0], layer_name, 1)

        #
        # Extract vegetation binary mask and clouds and ice/snow from
        # 18 semi-concepts.
        #
        for layer in siam_layers:

            img_array = None
            img_array = open_as_array(layer)

            if layer.endswith('18SpCt_r88v6.dat'):

                outData = numpy.where((img_array == 13), (2), outData)
                outData = numpy.where((img_array == 10), (3), outData)

                print '\nExtracted snow-ice and clouds from 18 granularity.'
                img_array = None

            elif layer.endswith('VegBinaryMask.dat'):

                outData = numpy.where((img_array == 1), (1), outData)

                print 'Extracted vegetation mask.'
                img_array = None

        #
        # Add '4' as placeholder for all other semi-concepts or noData.
        #
        outData = numpy.where((outData == 0), (4), outData)

        #
        # Replace noData with zeros.
        #
        outData = remove_nodata(folder, outData)

        #
        # Write outdata array.
        #
        outBand = outDs.GetRasterBand(1)
        outBand.WriteArray(outData, 0, 0)

        #
        # Flush data to disk.
        #
        outBand.FlushCache()

        #
        # Clean up.
        #
        del outData
        del outBand
        del outDs
        img = None

        time_elapsed(start_time)
        print '\nFinished layer: {}'.format(layer_name)
        print '--------------------------------'


def create_tif(layer, tiffname, num_layers):

    '''Create file to save to based on a defined layer.
        All should have the same size and resolution after SIAM processing --
        it ought not matter which one.'''

    #
    # Get layer name.
    #
    head, layername = os.path.split(layer)

    #
    # Open the first layer.
    #
    img = gdal.Open(layer, gdal.GA_ReadOnly)
    if img is None:
        print 'Could not open {}'.format(layername)
        sys.exit(1)

    #
    # Get raster georeference info.
    #
    projection = img.GetProjection()
    transform = img.GetGeoTransform()

    #
    # Establish size of raster from B02 for stacked output file.
    #
    img_rows = img.RasterYSize
    img_cols = img.RasterXSize

    #
    # Open output format driver, see gdal_translate --formats for list.
    #
    format = 'GTiff'
    driver = gdal.GetDriverByName(format)

    #
    # Test stacked band file path.
    #
    tile_folder = os.path.dirname(os.path.dirname(os.path.dirname(layer)))
    filepath = os.path.join(tile_folder, tiffname)

    #
    # Print driver for stacked layers (defined # bands, 8-bit unsigned).
    #
    num_layers = int(num_layers)

    outDs = driver.Create(filepath, img_cols, img_rows, num_layers,
        gdal.GDT_Byte)
    if outDs is None:
        print 'Could not create test file.'
        sys.exit(1)

    #
    # Georeference the tif file and set the projection.
    #
    outDs.SetGeoTransform(transform)
    outDs.SetProjection(projection)

    #
    # Create empty array to fill the layer later.
    #
    outData = numpy.zeros([img_cols, img_rows], dtype=int)

    driver = None
    img = None
    img_rows = None
    img_cols = None
    transform = None
    projection = None
    head = None
    layername = None

    #
    # Return datastore for use.
    #
    return outDs, outData


def generate_name(folder, example, stack_type):

    '''This function generates the layer name based on one S2 band name. '''

    #
    # Extract tile name from both new and old S2 naming conventions.
    #
    if (example).startswith('T'):
        fn_parts = example.split('_')
        tileinfo = fn_parts[0]
        utm_tile = tileinfo[1:]
        capture_date = (fn_parts[1])[:8]

    if (example).startswith('S2'):
        tileinfo = (example.split('_'))[9]
        utm_tile = tileinfo[1:]
        tile_folder = os.path.dirname(os.path.dirname(folder))
        head, tail = os.path.split(tile_folder)
        tile_parts = tail.split('_')
        capture_date = (tile_parts[7])[:8]

    layer_name = 'SIAM_layer_S2_{}_{}_{}.tif'.format(
        capture_date, utm_tile, stack_type)

    return layer_name


def open_as_array(layer_path):

    '''This function opens the input layer as a numpy array.'''

    #
    # Get layer name.
    #
    head, layername = os.path.split(layer_path)

    #
    # Open the image.
    #
    img = gdal.Open(layer_path, gdal.GA_ReadOnly)
    if img is None:
        print 'Could not open {}'.format(layername)
        sys.exit(1)

    #
    # Read in the data and get info about it.
    #
    img_band = img.GetRasterBand(1)
    img_rows = img.RasterYSize
    img_cols = img.RasterXSize

    #
    # Read image as array using GDAL.
    #
    img_array = None
    img_array = img_band.ReadAsArray(0,0, img_cols, img_rows)

    img_band = None
    img_rows = None
    img_cols = None

    return img_array


def remove_nodata(folder, outData):

    '''This function removes all pixels that have a value of 5 in any of the
        first 5 bands in the .dat stack created for SIAM. These bands
        correspond to S2 bands 2, 3, 4, 8 and 11. Band 6, or S2 band 12 is not
        included due to the presence of data pixels having a value of 0.
        The bands to be included may need to be reevaluated.'''

    #
    # Access original image folder.
    #
    tile_folder = os.path.dirname(os.path.dirname(folder))
    print tile_folder
    exit()

    #
    # Find path to img folder.
    #
    imgFolder = None

    for dirpath, dirnames, filenames in os.walk(tile_folder, topdown=True):
        for dirname in dirnames:
            if dirname == 'IMG_DATA':
                imgFolder = os.path.join(dirpath, dirname)

    #
    # Determine original file structure.
    #
    metadata_path = []

    for fn in os.listdir(os.path.dirname(imgFolder)):
        if (fn.startswith('S2A_') or fn.startswith('MTD')) and fn.endswith('.xml'):
            metadata_file = fn
            metadata_path.append(os.path.join(os.path.dirname(imgFolder), fn))
    if len(metadata_path) > 1:
        print ('Make sure only the original metadata exists in the tile folder'
            '\n{}'.format(os.path.dirname(imgFolder)))
        sys.exit()

    #
    # Grab relevant bands.
    #
    tile_bands = []

    #
    # Retrieve desired bands from old data structure.
    #
    if metadata_file.startswith('S2A_'):
        for dirpath, dirnames, filenames in os.walk(imgFolder, topdown=True):
            for filename in filenames:
                if (filename.startswith('S2A') and filename.endswith('.jp2')
                        and (fnmatch.fnmatch(filename, '*_B02.*')
                        or fnmatch.fnmatch(filename, '*_B03.*')
                        or fnmatch.fnmatch(filename, '*_B04.*')
                        or fnmatch.fnmatch(filename, '*_B08.*')
                        or fnmatch.fnmatch(filename, '*_B11.*')
                        or fnmatch.fnmatch(filename, '*_B12.*'))):

                    tile_bands.append(os.path.join(dirpath, filename))

    #
    # Retrieve desired bands from data structure.
    #
    elif metadata_file.startswith('M'):
        for dirpath, dirnames, filenames in os.walk(imgFolder, topdown=True):
            for filename in filenames:
                if (filename.startswith('T') and filename.endswith('.jp2')
                        and (fnmatch.fnmatch(filename, '*_B02.*')
                        or fnmatch.fnmatch(filename, '*_B03.*')
                        or fnmatch.fnmatch(filename, '*_B04.*')
                        or fnmatch.fnmatch(filename, '*_B08.*')
                        or fnmatch.fnmatch(filename, '*_B11.*')
                        or fnmatch.fnmatch(filename, '*_B12.*'))):

                    tile_bands.append(os.path.join(dirpath, filename))

    #
    # Put bands in numeric order for processing.
    #
    tile_bands.sort

    for band in tile_bands:

        #
        # Open the band as read only.
        #
        img = gdal.Open(band, gdal.GA_ReadOnly)
        band_id = band[-6:-4]
        if img is None:
            print 'Could not open band #{}'.format(band_id)
            sys.exit(1)
        print 'Processing noData for band #{}'.format(band_id)

        #
        # Cycle through bands 1-5, removing noData. Skip band 6 (S2 B12).
        #
        band_array = (img.GetRasterBand(1)).ReadAsArray()

        #
        # Resample bands 11 and 12 from 20m to 10m resolution.
        #
        if band.endswith(('_B11.jp2','_B12.jp2')):
            print 'Resample by a factor of 2 with nearest interpolation.'
            band_array = scipy.ndimage.zoom(band_array, 2, order=0)

        outData = numpy.where((band_array == 0), (0), outData)

    img = None
    head = None
    layername = None
    dat_file = None
    band_array = None
    proc_folder = None

    return outData


def start_or_quit(siam_folders):

    '''This funciton allows the user to decide whether to process all of the
        siamoutput folders, or not. If yes, a start time is established.'''

    #
    # Hide the main window for the message popup.
    #
    Tkinter.Tk().withdraw()

    #
    # Create the content of the popup window.
    #
    question = ('Number of tiles found: {}'
        '\n\nDo you want to process all folders?').format(len(siam_folders))
    messagebox = tkMessageBox.askyesno('SIAM Layer IQ4SEN', question)

    if not messagebox:
        print 'No folders processed.'
        sys.exit(1)

    #
    # Return start time if user has chosen to continue.
    #
    start_time = datetime.datetime.now()

    print '================================================================'
    print 'Hold on to your hat. This may take ~0.5 minute per S2 tile folder.'
    print 'Number of siamoutput folders found: {}'.format(len(siam_folders))
    print 'Estimated time: {} minutes'.format(int(len(siam_folders)) * 0.5)
    print 'Start time: {}'.format(start_time.time())
    print '================================================================\n\n'

    return start_time


def time_elapsed(start_time):

    '''This function returns the time elapsed.'''

    print 'Elapsed time: {}'.format(
        datetime.datetime.now() - start_time)

if __name__ == "__main__":

    #
    # Register all of the GDAL drivers
    #
    gdal.AllRegister()

    root_folder = 'C:\\tempS2'

    siam_folders = siam_folders(root_folder)

    #
    # Ask user to continue after assessing folders and establish start time.
    #
    start_time = start_or_quit(siam_folders)

    #
    # Create layer of noData (0), vegetation (1), snow/ice (2), clouds (3),
    # and other semi-concepts (4).
    #
    siam_classes = ['_VegBinaryMask.dat', '18SpCt_r88v6.dat']

    siam_layer(siam_folders, 'IQ4SEN', siam_classes, start_time)
