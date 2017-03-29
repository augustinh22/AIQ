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

import gdal
import numpy


def siam_folders(root_folder):

    '''This function creates a list of siamoutput folder paths.'''

    siamFolders = []

    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=True):
        for dirname in dirnames:
            if (dirname == 'siamoutput'
                    and fnmatch.fnmatch(dirpath, '*PROC_DATA*')):
                siamFolders.append(os.path.join(dirpath, dirname))

    return siamFolders


def siam_layer(siam_folders, stack_type, layer_endings):

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

                print '\nExtracted snow-ice and clouds from 18 granularity.\n'
                del img_array

            elif layer.endswith('VegBinaryMask.dat'):

                outData = numpy.where((img_array == 1), (1), outData)

                print '\nExtracted vegetation mask.\n'
                del img_array

        #
        # Add '4' as placeholder for all other semi-concepts or noData
        #
        outData = numpy.where((outData == 0), (4), outData)

        #
        # Replace noData with zeros
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
        img = None
        del outDs


def create_tif(layer, tiffname, num_layers):

    '''Create file to save to based on a defined layer.
        All should have the same size and resolution after SIAM processing, so
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

    #
    # Return datastore for use.
    #
    return outDs, outData

    del driver
    img = None


def generate_name(folder, example, stack_type):

    #
    # Extract tile name from both new and old S2 naming conventions.
    #
    if (example).startswith('T'):
        fn_parts = example.split("_")
        tileinfo = fn_parts[0]
        utm_tile = tileinfo[1:]
        capture_date = (file_parts[2])[:8]

    if (example).startswith('S2'):
        tileinfo = (example.split("_"))[9]
        utm_tile = tileinfo[1:]
        tile_folder = os.path.dirname(os.path.dirname(folder))
        head, tail = os.path.split(tile_folder)
        tile_parts = tail.split("_")
        capture_date = (tile_parts[7])[:8]

    layer_name = 'SIAM_layer_S2_{}_{}_{}.tif'.format(
        capture_date, utm_tile, stack_type)

    return layer_name


def open_as_array(layer_path):

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

    del img_band

    return img_array

def remove_nodata(folder, outData):

    #
    # Access .dat file used as input for siam.
    #
    proc_folder = os.path.dirname(folder)

    #
    # Retrieve dat file path
    #
    for dirpath, dirnames, filenames in os.walk(proc_folder, topdown=True):
        for filename in filenames:
            if filename.endswith('_calrefbyt_lndstlk.dat'):
                dat_file = os.path.join(dirpath, filename)

    #
    # Get layer name.
    #
    head, layername = os.path.split(dat_file)

    #
    # Open the image.
    #
    img = gdal.Open(dat_file, gdal.GA_ReadOnly)
    if img is None:
        print 'Could not open {}'.format(layername)
        sys.exit(1)

    for band in range(1, 7):
        band_array = (img.GetRasterBand(band)).ReadAsArray()
        outData = numpy.where((band_array == 0), (0), outData)

    img = None
    del head
    del layername
    del dat_file
    del band_array

    return outData


if __name__ == "__main__":

    #
    # Register all of the GDAL drivers
    #
    gdal.AllRegister()

    root_folder = 'C:\\tempS2'

    siam_folders = siam_folders(root_folder)

    #
    # Create layer of noData (0), vegetation (1), snow/ice (2), clouds (3),
    # and other semi-concepts (4).
    #
    siam_classes = ['_VegBinaryMask.dat', '18SpCt_r88v6.dat']

    siam_layer(siam_folders, 'IQ4SEN', siam_classes)
