#-------------------------------------------------------------------------------
# Name:        Sentinel2 'Conversion' for SIAM.
# Purpose:     Use NumPy, GDAL and SciPy to convert all Sentinel2 bands to
#              8-bit, resample bands 11 and 12 to 10m pixels and build a 6-band
#              stack in the ENVI format (i.e. including .hdr). It also creates
#              a single band ENVI .dat/.hdr file with a constant value of 110
#              as a fake thermal band for SIAM.
#              This script is based on an ArcPy Python toolbox developed by
#              Dirk Tiede.
#
# Author:      h.Augustin
#
# Created:     14.12.2016
#
#-------------------------------------------------------------------------------
##; FROM Andrea Baraldi:
##;     OBJECTIVE: Radiometric calibration of Sentinel-2A/2B imagery into
##;         (i)  TOP-OF-ATMOSPHERE (TOA, PLANETARY, EXOATMOSPHERIC)
##;              reflectance (in range [0,1]), byte-coded,
##;              i.e., scaled into range {1, 255}, output ENVI file format:
##;              ...calrefbyt_lndstlk, band sequential (BSQ).
##;              Equivalent to Landsat bands 1, 2, 3, 4, 5 and 7 are
##;              the Sentinel-2A/2B bands    2, 3, 4, 8, 11 and 12
##;              with spatial resolutions   10, 10, 10, 10, 20, 20.
##;         (ii) faked temperature in kelvin degrees, equivalent to
##;              10 degree Celsius,output value = 110, output
##;              ENVI file format: ...caltembyt_lndstlk.
##;
##;         where:
##;             - Sentinel-2A/2B bands are:
##;
##;             1, Aerosols (nm): 443?20/2,       Spatial resolution (in m): 60
##;             2: Vis B (like TM1), 490?65/2,    Spatial resolution (in m): 10
##;             3: Vis G (like TM2), 560?35/2,    Spatial resolution (in m): 10
##;             4: Vis R (like TM3), 665?30/2,    Spatial resolution (in m): 10
##;             5: NIR1 (Red Edge1), 705?15/2,    Spatial resolution (in m): 20
##;             6: NIR2 (Red Edge2), 740?15/2,    Spatial resolution (in m): 20
##;             7: NIR3 (Red Edge3),783?20/2,     Spatial resolution (in m): 20
##;             8: NIR4 (like TM4), 842?115/2,    Spatial resolution (in m): 10
##;             8a: NIR5, 865?20/2,               Spatial resolution (in m): 20
##;             9, Water vapour: 945?20/2,        Spatial resolution (in m): 60
##;             10, Cirrus: 1375?30/2,            Spatial resolution (in m): 60
##;             11: MIR1 (like TM5) 1610?90/2,    Spatial resolution (in m): 20
##;             12: MIR2 (like TM7) 2190?180/2    Spatial resolution (in m): 20
##;
##;             Hence, equivalent to Landsat bands 1, 2, 3, 4, 5 and 7 are
##;             the Sentinel-2A/2B bands           2, 3, 4, 8, 11 and 12
##;             with spatial resolutions          10, 10, 10, 10, 20, 20.

#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import datetime
import tkMessageBox
import Tkinter

import gdal
import numpy
import scipy.ndimage

# Create empty list for IMG_DATA folder paths
imgFolders = []

for dirpath, dirnames, filenames in os.walk('C:/tempS2', topdown=True):
    for dirname in dirnames:
        if dirname == 'IMG_DATA':
            imgFolders.append(os.path.join(dirpath, dirname))
## print imgFolders

# Create question to continue based on the number of scenes found.
question = ('Number of tiles found: {}'
    '\n\nDo you want to process all folders?').format(len(imgFolders))

# Hide the main window.
Tkinter.Tk().withdraw()
# Create the content of the window.
messagebox = tkMessageBox.askyesno('Sentinel for SIAM', question)

if not messagebox:
    print 'No folders processed.'
    sys.exit(1)

start_time = datetime.datetime.now()

print '=================================================================='
print 'Hold on to your hat. This may take ~10 minutes per S2 tile folder.'
print 'Number of IMG_DATA folders found: {}'.format(len(imgFolders))
print 'Estimated time: {} minutes'.format(int(len(imgFolders)) * 10)
print 'Start time: {}'.format(start_time.time())
print '==================================================================\n\n'

# Register all of the GDAL drivers
gdal.AllRegister()

for imgFolder in imgFolders:

    tile_bands = []

    for dirpath, dirnames, filenames in os.walk(imgFolder, topdown=True):
        for filename in filenames:
            if filename.startswith('S2A') and filename.endswith('.jp2'):
                tile_bands.append(os.path.join(dirpath, filename))

    tile_bands.sort
    ## print tile_bands

    # Create the folder for processed data if it doesn't exist.
    PROC_DATA = '{}PROC_DATA'.format(imgFolder[:-8])
    if not(os.path.exists(PROC_DATA)):
        os.mkdir(PROC_DATA)

    # Create file to save stack to -- there is probably a better way to do this!
    # Also create fake thermal band file.
    for band in tile_bands:
        # Get a band with 10m pixel size to get georeferencing, etc. metadata.
        if band.endswith('_B02.jp2'):

            # Open the B02 image.
            img = gdal.Open(band, GA_ReadOnly)
            band_id = band[-6:-4]
            tile_id = band[-13:-8]
            if img is None:
                print 'Could not open band #{}'.format(band_id)
                sys.exit(1)

            print '------------------------------------------------------------'
            print 'Processing tile {}\n\n'.format(tile_id)


            # Get raster georeference info from B02 for output .dat files.
            projection = img.GetProjection()
            transform = img.GetGeoTransform()
            ## xOrigin = transform[0]
            ## yOrigin = transform[3]
            ## pixelWidth = transform[1]
            ## pixelHeight = transform[5]

            # Establish size of raster from B02 for stacked output file.
            img_rows = img.RasterYSize
            img_cols = img.RasterXSize

            # Open output format driver, see gdal_translate --formats for list.
            format = 'ENVI'
            driver = gdal.GetDriverByName(format)

            # Test stacked band file path.
            filepath = '{}/{}calrefbyt_lndstlk.dat'.format(
                PROC_DATA, os.path.basename(band)[:-3])

            # Print driver for stacked layers (6 bands, 8-bit unsigned).
            outDs = driver.Create(filepath, img_cols, img_rows, 6,
                gdal.GDT_Byte)
            if outDs is None:
                print 'Could not create test file.'
                sys.exit(1)
            # Georeference the stacked .dat file and set the projection.
            outDs.SetGeoTransform(transform)
            outDs.SetProjection(projection)

            print 'Creating fake thermal band for {}'.format(tile_id)

            # Test thermal band path.
            filepath = '{}/{}caltembyt_lndstlk.dat'.format(
                PROC_DATA, os.path.basename(band)[:-3])

            # Print driver for fake thermal band (1 band, 8-bit unsigned).
            thermDs = driver.Create(filepath, img_cols, img_rows, 1,
                gdal.GDT_Byte)
            if thermDs is None:
                print 'Could not create test file.'
                sys.exit(1)
            # Georeference the fake thermal band and set the projection.
            thermDs.SetGeoTransform(transform)
            thermDs.SetProjection(projection)

            # Create constant array with a value of 110.
            therm_array = numpy.ones((img_rows, img_cols)).astype(int)
            therm_array = therm_array * 110
            ## print therm_array
            ## print therm_array.shape

            # Write the data to the designated band.
            outBand = thermDs.GetRasterBand(1)
            outBand.WriteArray(therm_array, 0, 0)

            # Flush data to disk, set the NoData value and calculate stats.
            outBand.FlushCache()
            outBand.SetNoDataValue(-99)

            print 'Elapsed time: {}'.format(
                datetime.datetime.now() - start_time)
            print 'Fake thermal band created.\n\n'

            # Clean up.
            del band_id
            del driver
            del therm_array
            del outBand
            thermDs = None
            img = None

    # Keep track of which band we are writing to in the stacked file.
    iteration = 1
    print 'Creating 6 band stack for tile {}\n'.format(tile_id)

    for band in tile_bands:
        if band.endswith(('_B02.jp2','_B03.jp2','_B04.jp2','_B08.jp2')):
            # Open the image
            img = gdal.Open(band, GA_ReadOnly)
            band_id = band[-6:-4]
            if img is None:
                print 'Could not open band #{}'.format(band_id)
                sys.exit(1)

            print 'Processing band #{}'.format(band_id)

            # Read in the data and get info about it.
            img_band = img.GetRasterBand(1)
            img_rows = img.RasterYSize
            img_cols = img.RasterXSize

            # Read image as array using GDAL.
            img_array = img_band.ReadAsArray(0,0, img_cols, img_rows)
            ## print 'Original array: \n{}'.format(img_array)
            print 'Original shape: {}'.format(img_array.shape)
            ## print 'Original max: {}'.format(numpy.amax(img_array))
            ## print 'Original min: {}'.format(numpy.amin(img_array))

            # Adjust outliers.
            outData = img_array / 10000.0
            for i in range(0, img_rows):
                for j in range(0, img_cols):
                    if outData[i,j] > 1:
                        outData[i,j] = 1
                    elif outData[i,j] < 0:
                        outData[i,j] = 0

            # Convert to 8-bit.
            outData = ((numpy.absolute(outData) * 255.0) + 0.5).astype(int)

            # Write the data to the designated band.
            outBand = outDs.GetRasterBand(iteration)
            outBand.WriteArray(outData, 0, 0)

            # Flush data to disk, set the NoData value and calculate stats.
            outBand.FlushCache()
            outBand.SetNoDataValue(-99)

            print 'Elapsed time: {}'.format(
                datetime.datetime.now() - start_time)
            print 'Band #{} completed.\n'.format(band_id)

            # Clean up.
            del img_band
            del band_id
            del img_array
            del outData
            del outBand
            img = None

            # On we go...
            iteration += 1

        if band.endswith(('_B11.jp2','_B12.jp2')):
            # Open the image
            img = gdal.Open(band, GA_ReadOnly)
            band_id = band[-6:-4]
            if img is None:
                print 'Could not open band #{}'.format(band_id)
                sys.exit(1)

            print 'Processing band #{}'.format(band_id)

            # Read in the data and get info about it.
            img_band = img.GetRasterBand(1)
            img_rows = img.RasterYSize
            img_cols = img.RasterXSize

            # Read image as array.
            img_array = img_band.ReadAsArray(0,0, img_cols, img_rows)
            ## print 'Original array: \n{}'.format(img_array)
            print 'Original shape: {}'.format(img_array.shape)
            ## print 'Original max: {}'.format(numpy.amax(img_array))
            ## print 'Original min: {}'.format(numpy.amin(img_array))

            # Adjust outliers.
            outData = img_array / 10000.0
            for i in range(0, img_rows):
                for j in range(0, img_cols):
                    if outData[i,j] > 1:
                        outData[i,j] = 1
                    elif outData[i,j] < 0:
                        outData[i,j] = 0

            ## Resampling to zoom factor of 2, since original pixel size is 20m.
            print 'Resample by a factor of 2 with nearest interpolation.'
            outData = scipy.ndimage.zoom(outData, 2, order=0)
            print 'Resampled size: {}'.format(outData.shape)

            # Convert to 8-bit.
            outData = ((numpy.absolute(outData) * 255.0) + 0.5).astype(int)

            # Write the data to the designated band.
            outBand = outDs.GetRasterBand(iteration)
            outBand.WriteArray(outData, 0, 0)

            # Flush data to disk, set the NoData value and calculate stats
            outBand.FlushCache()
            outBand.SetNoDataValue(-99)

            print 'Elapsed time: {}'.format(
                datetime.datetime.now() - start_time)
            print 'Band #{} completed.\n'.format(band_id)

            # Clean up.
            del img_band
            del band_id
            del img_array
            del outData
            del outBand
            img = None

            # On we go...
            iteration += 1

    print 'Tile {} processed and stacked.'.format(tile_id)
    print '------------------------------------------------------------\n\n\n'

    # Clean up.
    del tile_id
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
