#-------------------------------------------------------------------------------
# Name:        Sentinel2 'Conversion'
# Purpose:     This script uses numpy, gdal and scipy to convert all bands to
#              8-bit, resample bands 11 and 12 to 10m pixels and build a 6-band
#              .dat stack. It also creates a single band .dat file
#              with a constant value of 110 as a fake thermal band for SIAM.
#
# Author:      h.Augustin
#
# Created:     14.12.2016
#
#-------------------------------------------------------------------------------

#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import numpy
import gdal
import scipy.ndimage

# Register all of the GDAL drivers
gdal.AllRegister()

### Here we'll add some walking to get to each IMG_DATA folder. What follows is
### roughly what ought to happen within each IMG_DATA folder. Dynamic
### file name creation (e.g. ..._calrefbyt_lndstlk) also needs to be
### implemented.

IMG_DATA = './'

tile_bands = []
for tile_band in os.listdir(IMG_DATA):
    if tile_band.endswith('.jp2'):
        tile_bands.append(tile_band)
tile_bands.sort
print tile_bands

# Create the folder for processed data if it doesn't exist.
PROC_DATA = '{}/PROC_DATA'.format(IMG_DATA)
if not(os.path.exists(PROC_DATA)):
    os.mkdir(PROC_DATA)

print '------------------------------------------------------------------'
print 'Hold on to your hat. This may take ~10 minutes per S2 tile folder.'
print '------------------------------------------------------------------'

# Create file to save stack to -- there is probably a better way to do this!!
# Also create fake thermal band file.
for band in tile_bands:
    # Get a band with 10m pixel size to get georeferencing, etc. metadata.
    if band.endswith('_B02.jp2'):

        # Open the B02 image.
        img = gdal.Open(band)
        band_id = band[-6:-4]
        if img is None:
            print 'Could not open band #{}'.format(band_id)
            sys.exit(1)

        # Get raster georeference info from B02 for stacked output file.
        projection = img.GetProjection()
        transform = img.GetGeoTransform()
        # xOrigin = transform[0]
        # yOrigin = transform[3]
        # pixelWidth = transform[1]
        # pixelHeight = transform[5]

        # Establish size of raster from B02 for stacked output file.
        img_rows = img.RasterYSize
        img_cols = img.RasterXSize
        print img_rows, img_cols

        # Open output format driver, see gdal_translate --formats for list.
        format = 'ENVI'
        driver = gdal.GetDriverByName(format)

        # Test stacked band file path.
        filepath = '{}/test_calrefbyt_lndstlk.dat'.format(PROC_DATA)

        # Print driver for stacked layers (6 bands, 8-bit unsigned).
        outDs = driver.Create(filepath, img_cols, img_rows, 6, gdal.GDT_Byte)
        if outDs is None:
            print 'Could not create test file.'
            sys.exit(1)

        # Test thermal band path.
        filepath = '{}/test_caltembyt_lndstlk.dat'.format(PROC_DATA)

        # Print driver for fake thermal band (1 band, 8-bit unsigned).
        thermDs = driver.Create(filepath, img_cols, img_rows, 1, gdal.GDT_Byte)
        if thermDs is None:
            print 'Could not create test file.'
            sys.exit(1)

        # Create constant array with a value of 110.
        therm_array = numpy.ones((img_rows, img_cols)).astype(int)
        therm_array = therm_array * 110
        print therm_array
        print therm_array.shape

        # Write the data to the designated band.
        outBand = thermDs.GetRasterBand(1)
        outBand.WriteArray(therm_array, 0, 0)

        # Flush data to disk, set the NoData value and calculate stats
        outBand.FlushCache()
        outBand.SetNoDataValue(-99)

        # Georeference the image and set the projection.
        thermDs.SetGeoTransform(transform)
        thermDs.SetProjection(projection)

        # Clean up.
        del therm_array
        del band_id
        thermDs = None
        img = None

# Keep track of which band in the stacked file we are writing to.
iteration = 1

for band in tile_bands:
    if band.endswith(('_B02.jp2','_B03.jp2','_B04.jp2','_B08.jp2')):
        # Open the image
        img = gdal.Open(band)
        band_id = band[-6:-4]
        if img is None:
            print 'Could not open band #{}'.format(band_id)
            sys.exit(1)

        # Read in the data and get info about it.
        img_band = img.GetRasterBand(1)
        img_rows = img.RasterYSize
        img_cols = img.RasterXSize
        print img_rows, img_cols

        # Read image as array using GDAL.
        img_array = img_band.ReadAsArray(0,0, img_cols, img_rows)
        print 'Original array: \n{}'.format(img_array)
        print 'Original shape: {}'.format(img_array.shape)
        print 'Original max: {}'.format(numpy.amax(img_array))
        print 'Original min: {}'.format(numpy.amin(img_array))

        # Adjust outliers.
        outData = img_array / 10000.0
        for i in range(0, img_rows):
            for j in range(0, img_cols):
                if outData[i,j] > 1:
                    outData[i,j] = 1
                elif outData[i,j] < 0:
                    outData[i,j] = 0
                else:
                    outData[i,j] = outData[i,j]

        # Convert to 8-bit.
        outData = ((numpy.absolute(outData) * 255.0) + 0.5).astype(int)

        # Write the data to the designated band.
        outBand = outDs.GetRasterBand(iteration)
        outBand.WriteArray(outData, 0, 0)

        # Flush data to disk.
        outBand.FlushCache()

        # Clean up.
        del band_id
        del img_array
        del outData
        img = None

        # On we go...
        iteration += 1

    if band.endswith(('_B11.jp2','_B12.jp2')):
        # Open the image
        img = gdal.Open(band)
        band_id = band[-6:-4]
        if img is None:
            print 'Could not open band #{}'.format(band_id)
            sys.exit(1)

        # Read in the data and get info about it.
        img_band = img.GetRasterBand(1)
        img_rows = img.RasterYSize
        img_cols = img.RasterXSize
        print img_rows, img_cols

        # Read image as array
        img_array = img_band.ReadAsArray(0,0, img_cols, img_rows)
        print 'Original array: \n{}'.format(img_array)
        print 'Original shape: {}'.format(img_array.shape)
        print 'Original max: {}'.format(numpy.amax(img_array))
        print 'Original min: {}'.format(numpy.amin(img_array))

        # Adjust outliers.
        outData = img_array / 10000.0
        for i in range(0, img_rows):
            for j in range(0, img_cols):
                if outData[i,j] > 1:
                    outData[i,j] = 1
                elif outData[i,j] < 0:
                    outData[i,j] = 0
                else:
                    outData[i,j] = outData[i,j]

        ## Resampling to zoom factor of 2, since original pixel size is 20m.
        print 'Resample by a factor of 2 with nearest interpolation.'
        outData = scipy.ndimage.zoom(outData, 2, order=0)
        print 'Resampled Size: {}'.format(outData.shape)

        # Convert to 8-bit.
        outData = ((numpy.absolute(outData) * 255.0) + 0.5).astype(int)

        # Write the data to the designated band.
        outBand = outDs.GetRasterBand(iteration)
        outBand.WriteArray(outData, 0, 0)

        # Flush data to disk.
        outBand.FlushCache()

        # Clean up.
        del band_id
        del img_array
        del outData
        img = None

        # On we go...
        iteration += 1

# Georeference the stacked .dat file and set the projection.
outDs.SetGeoTransform(transform)
outDs.SetProjection(projection)

# Clean up.
outDs = None


#------------------------------------------------------------------------------#
# A bit of confused configuration for Windows (GDAL, etc.) -- not finished     #
#------------------------------------------------------------------------------#


# Download and install MSVC for your version of Windows
# Download and install GDAL for Windows based on your version of MSVC
# * http://www.gisinternals.com/release.php
# * gdal-201-1800-x64-core.msi
# * Set system path environment variable to include GDAL folder
# * Set system environment variable GDAL_DATA to the gdal-data folder in GDAL
# Download GDAL Python bindings for Windows
# * http://www.gisinternals.com/release.php
# * GDAL-2.1.2.win-amd64-py2.7.msi
# * Make sure that it binds to the correct installation of Python.
# * copy the missing bits from the unofficial windows binary wheel interpolation
#    into gdal in Python if necessary:
#    (http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal)
# Download and install Numpy + MKL and SciPy Python packages for Windows
# * http://www.lfd.uci.edu/~gohlke/pythonlibs/
# * pip install .whl
