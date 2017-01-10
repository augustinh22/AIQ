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
import fnmatch

import gdal
import numpy


def siam_folders(root_folder):

    # Create empty list for 'siamoutput' folder paths
    siamFolders = []

    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=True):
        for dirname in dirnames:
            if dirname == 'siamoutput'
                    and fnmatch.fnmatch(dirpath, '*PROC_DATA*'):
                siamFolders.append(dirpath)
    return siamFolders

def siam_stack_classes(siam_folders):

    # This function will create a datacube of the desired SIAM layers, saving
    # it to the siamoutput folder.

    for folder in siam_folders:

        # create new list of desired layers and stack.
        siam_layers = []
        for dirpath, dirnames, filenames in os.walk(folder, topdown=True):
            for filename in filenames:
                if filename.endswith('calrefbyt_lndstlk_SIAMCr_33SharedSpCt_r88v6.dat'):
                    siam_layers.append(os.path.join(dirpath, filename))
                if filename.endswith('calrefbyt_lndstlk_SIAMCr_96SpCt_r88v6.dat'):
                    siam_layers.append(os.path.join(dirpath, filename))
        siam_layers.sort
        print siam_layers

        # Calculate number of layers for stack.
        num_layers = len(siam_layers)

        ## Add a means to dynamically create the tiff name.

        # Create tiff file in folder for stack.
        outDs = create_tiff(folder, siam_layers[0], 'iq_classes.tif', num_layers)

        # Keep track of which band we are writing to in the stacked file.
        iteration = 1

        for layer in siam_layers:

            # Get layer name.
            head, layername = os.path.split(layer)

            # Open the image
            img = gdal.Open(layer, gdal.GA_ReadOnly)
            if img is None:
                print 'Could not open {}'.format(layername)
                sys.exit(1)

            # Read in the data and get info about it.
            img_band = img.GetRasterBand(1)
            img_rows = img.RasterYSize
            img_cols = img.RasterXSize

            # Read image as array using GDAL.
            img_array = img_band.ReadAsArray(0,0, img_cols, img_rows)

            # Write the data to the designated band and calculate stats.
            outBand = outDs.GetRasterBand(iteration)
            outBand.WriteArray(outData, 0, 0)

            # Flush data to disk and set the NoData value.
            outBand.FlushCache()
            outBand.SetNoDataValue(-99)
            # Calculate stats.
            stats = outBand.ComputeStatistics(outBand)
            outBand.SetStatistics(stats[0], stats[1], stats[2], stats[3])

            # Clean up.
            del img_band
            del img_array
            del outBand
            del stats
            img = None

            # On we go...
            iteration += 1

        del outDs

def siam_stack_mask(siam_folders):

    # This function will create a datacube of the desired SIAM layers, saving
    # it to the siamoutput folder.

    for folder in siam_folders:

        # Create new list of desired mask layers and stack.
        siam_layers = []
        for dirpath, dirnames, filenames in os.walk(folder, topdown=True):
            for filename in filenames:
                if filename.endswith('calrefbyt_lndstlk_SIAMCr_CAV_VegBinaryMask.dat'):
                    siam_layers.append(os.path.join(dirpath, filename))
        siam_layers.sort
        print siam_layers

        # Calculate number of layers for stack.
        num_layers = len(siam_layers)

        # Create tiff file in folder for stack.
        outDs = create_tiff(folder, siam_layers[0], 'iq_masks.tif', num_layers)

        # Keep track of which band we are writing to in the stacked file.
        iteration = 1

        for layer in siam_layers:

            # Get layer name.
            head, layername = os.path.split(layer)

            # Open the image
            img = gdal.Open(layer, gdal.GA_ReadOnly)
            if img is None:
                print 'Could not open {}'.format(layername)
                sys.exit(1)

            # Read in the data and get info about it.
            img_band = img.GetRasterBand(1)
            img_rows = img.RasterYSize
            img_cols = img.RasterXSize

            # Read image as array using GDAL.
            img_array = img_band.ReadAsArray(0,0, img_cols, img_rows)

            # Write the data to the designated band and calculate stats.
            outBand = outDs.GetRasterBand(iteration)
            outBand.WriteArray(img_array, 0, 0)

            # Flush data to disk and set the NoData value.
            outBand.FlushCache()
            outBand.SetNoDataValue(-99)
            # Calculate stats.
            stats = outBand.ComputeStatistics(outBand)
            outBand.SetStatistics(stats[0], stats[1], stats[2], stats[3])

            # Clean up.
            del img_band
            del img_array
            del outBand
            del stats
            img = None

            # On we go...
            iteration += 1

        del outDs

def create_tiff(folder, layer, tiffname, num_layers):

    # Create file to save to based on a defined layer.
    # All should have the same size and resolution after SIAM processing, so
    # it ought not matter which one.

    # Get layer name.
    head, layername = os.path.split(layer)

    # Open the first layer.
    img = gdal.Open(layer, gdal.GA_ReadOnly)
    if img is None:
        print 'Could not open {}'.format(layername)
        sys.exit(1)

    # Get raster georeference info.
    projection = img.GetProjection()
    transform = img.GetGeoTransform()

    # Establish size of raster from B02 for stacked output file.
    img_rows = img.RasterYSize
    img_cols = img.RasterXSize

    # Open output format driver, see gdal_translate --formats for list.
    format = 'GTiff'
    driver = gdal.GetDriverByName(format)

    # Test stacked band file path.
    filepath = os.path.join(folder, tiffname)

    # Print driver for stacked layers (defined # bands, 8-bit unsigned).
    num_layers = int(num_layers)

    outDs = driver.Create(filepath, img_cols, img_rows, num_layers,
        gdal.GDT_Byte)
    if outDs is None:
        print 'Could not create test file.'
        sys.exit(1)

    # Georeference the tif file and set the projection.
    outDs.SetGeoTransform(transform)
    outDs.SetProjection(projection)

    # Return datastore for use.
    return outDs

    del driver
    img = None


if __name__ == "__main__":

    # Register all of the GDAL drivers
    gdal.AllRegister()

    root_folder = 'C:\\tempS2'

    siam_folders = siam_folders(root_folder)

    siam_stack_classes(siam_folders)

    siam_stack_masks(siam_folders)
