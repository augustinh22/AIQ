#-------------------------------------------------------------------------------
# Name:        Data cubes for IQ.
# Purpose:     This script creates desired data cubes for import into IQ based
#              on SIAM output.
#
# Author:      h.Augustin
#
# Created:     10.01.2017
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

    #
    # Create empty list for 'siamoutput' folder paths
    #
    siamFolders = []

    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=True):
        for dirname in dirnames:
            if (dirname == 'siamoutput'
                    and fnmatch.fnmatch(dirpath, '*PROC_DATA*')):
                siamFolders.append(os.path.join(dirpath, dirname))

    return siamFolders


def siam_stack(siam_folders, stack_type, layer_endings):

    '''This function will create a datacube of the desired SIAM layers, saving
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
        # Calculate number of layers for stack.
        #
        num_layers = len(siam_layers)

        #
        # Extract tile name from both new and old S2 naming conventions.
        #
        if (example).startswith('T'):
            tileinfo = (example.split("_"))[0]
            utm_tile = tileinfo[1:]

        if (example).startswith('S2'):
            tileinfo = (example.split("_"))[9]
            utm_tile = tileinfo[1:]

        stack_name = 'S2_{}_{}.tif'.format(utm_tile, stack_type)

        #
        # Create tiff file in folder for stack.
        #
        outDs = create_tif(siam_layers[0], stack_name, num_layers)

        for layer in siam_layers:

            #
            # Keep track of which band we are writing to in the stacked file.
            #
            band_in_stack = None

            if layer.endswith('VegBinaryMask.dat'):
                band_in_stack = 1
            if layer.endswith('UrbanAreaSeedPixelBinaryMask.dat'):
                band_in_stack = 2
            if layer.endswith('33SharedSpCt_r88v6.dat'):
                band_in_stack = 1
            if layer.endswith('96SpCt_r88v6.dat'):
                band_in_stack = 2

            #
            # Get layer name.
            #
            head, layername = os.path.split(layer)

            #
            # Open the image.
            #
            img = gdal.Open(layer, gdal.GA_ReadOnly)
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
            img_array = img_band.ReadAsArray(0,0, img_cols, img_rows)

            #
            # Write the data to the designated band.
            outBand = outDs.GetRasterBand(band_in_stack)
            outBand.WriteArray(img_array, 0, 0)

            #
            # Flush data to disk and set the NoData value.
            #
            outBand.FlushCache()
            outBand.SetNoDataValue(-99)

            #
            # Clean up.
            #
            del img_band
            del img_array
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
    # Return datastore for use.
    #
    return outDs

    del driver
    img = None


if __name__ == "__main__":

    #
    # Register all of the GDAL drivers
    #
    gdal.AllRegister()

    root_folder = 'C:\\tempS2'

    siam_folders = siam_folders(root_folder)

    #
    # Create class stack.
    #
    siam_classes = ['33SharedSpCt_r88v6.dat', '96SpCt_r88v6.dat']

    siam_stack(siam_folders, 'CLS', siam_classes)

    #
    # Create mask stack.
    #
    siam_masks = ['VegBinaryMask.dat', 'UrbanAreaSeedPixelBinaryMask.dat']

    siam_stack(siam_folders, 'MSK', siam_masks)
