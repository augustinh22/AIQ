# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------
# #;FROM Andrea Baraldi:
# #;    OBJECTIVE: Radiometric calibration of Sentinel-2A/2B imagery into
# #;        (i)  TOP-OF-ATMOSPHERE (TOA, PLANETARY, EXOATMOSPHERIC)
# #;             reflectance (in range [0,1]), byte-coded,
# #;             i.e., scaled into range {1, 255}, output ENVI file format:
# #;             ...calrefbyt_lndstlk, band sequential (BSQ).
# #;             Equivalent to Landsat bands 1, 2, 3, 4, 5 and 7 are
# #;             the Sentinel-2A/2B bands    2, 3, 4, 8, 11 and 12
# #;             with spatial resolutions   10, 10, 10, 10, 20, 20.
# #;        (ii) faked temperature in kelvin degrees, equivalent to
# #;             10 degree Celsius,output value = 110, output
# #;             ENVI file format: ...caltembyt_lndstlk.
# #;
# #;        where:
# #;            - Sentinel-2A/2B bands are:
# #;
# #;            1, Aerosols (nm): 443?20/2,       Spatial resolution (in m): 60
# #;            2: Vis B (like TM1), 490?65/2,    Spatial resolution (in m): 10
# #;            3: Vis G (like TM2), 560?35/2,    Spatial resolution (in m): 10
# #;            4: Vis R (like TM3), 665?30/2,    Spatial resolution (in m): 10
# #;            5: NIR1 (Red Edge1), 705?15/2,    Spatial resolution (in m): 20
# #;            6: NIR2 (Red Edge2), 740?15/2,    Spatial resolution (in m): 20
# #;            7: NIR3 (Red Edge3),783?20/2,     Spatial resolution (in m): 20
# #;            8: NIR4 (like TM4), 842?115/2,    Spatial resolution (in m): 10
# #;            8a: NIR5, 865?20/2,               Spatial resolution (in m): 20
# #;            9, Water vapour: 945?20/2,        Spatial resolution (in m): 60
# #;            10, Cirrus: 1375?30/2,            Spatial resolution (in m): 60
# #;            11: MIR1 (like TM5) 1610?90/2,    Spatial resolution (in m): 20
# #;            12: MIR2 (like TM7) 2190?180/2    Spatial resolution (in m): 20
# #;
# #;            Hence, equivalent to Landsat bands 1, 2, 3, 4, 5 and 7 are
# #;            the Sentinel-2A/2B bands           2, 3, 4, 8, 11 and 12
# #;            with spatial resolutions          10, 10, 10, 10, 20, 20.

#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import shutil
import datetime
import fnmatch
import argparse
import logging
import xml.etree.ElementTree as etree

import gdal
import numpy
import scipy.ndimage
# from PIL import Image

###############################################################################


def get_args():

    '''
    Gets arguments from command line.
    '''

    #
    # Create download tool help response.
    #
    prog = os.path.basename(sys.argv[0])

    if len(sys.argv) == 1:

        print(
            '\n        {0} [options]'
            '\n        Help: {1} --help'
            '\n        or: {1} -h'
            '\nexample python {0} -r /path/to/data/'
            ).format(sys.argv[0], prog)

        sys.exit(-1)

    else:

        parser = argparse.ArgumentParser(
            prog=prog,
            usage='%(prog)s [options]',
            description='Sentinel data converter.',
            argument_default=None,
            epilog='Go get \'em!')

        #
        # Arguments.
        #
        parser.add_argument(
            '-r', '--read_dir', dest='read_dir', action='store', type=str,
            help='Path where downloaded products are located.', default=None)
        parser.add_argument(
            '--auto', dest='auto', action='store',
            help=('No user input necessary -- automatically converts all '
                  'previously not converted images files.'),
            default=None)

        return parser.parse_args()


def nodata_array(tile_bands, PROC_DATA):

    '''
    This function creates a noData mask array based on all pixels that have
    a value of 0 in any of the original Sentinel-2 bands used to create the
    6 band .dat SIAM input file, and saves a copy as '*nodata.dat'.
    These correspond to S2 bands: 2, 3, 4, 8, 10 and 11.
    '''

    #
    # Create array with same projection, etc.
    #
    noData = gdal.Open(tile_bands[0], gdal.GA_ReadOnly)
    noData_array = (noData.GetRasterBand(1)).ReadAsArray()
    noData_array = numpy.where((noData_array > 0), (1), noData_array)
    #
    # Establish size of raster from B02 for nodata output file.
    #
    projection = noData.GetProjection()
    transform = noData.GetGeoTransform()
    img_rows = noData.RasterYSize
    img_cols = noData.RasterXSize

    #
    # Open output format driver, see gdal_translate --formats for list.
    #
    gdal_format = 'ENVI'
    driver = gdal.GetDriverByName(gdal_format)

    #
    # Test nodata mask file path.
    #
    band_basename = os.path.basename(tile_bands[0])
    nodata_file = '{}nodata.dat'.format(
        os.path.basename(band_basename[:-7]))
    filepath = os.path.join(PROC_DATA, nodata_file)

    #
    # Print driver for nodata mask (1 band, 8-bit unsigned).
    #
    outDs = driver.Create(filepath, img_cols, img_rows, 1,
                          gdal.GDT_Byte)
    if outDs is None:
        print 'Could not create test file.'
        sys.exit(1)

    #
    # Georeference the nodata .dat file and set the projection.
    #
    outDs.SetGeoTransform(transform)
    outDs.SetProjection(projection)

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
        # Cycle through bands, removing noData.
        #
        band_array = (img.GetRasterBand(1)).ReadAsArray()

        #
        # Resample bands 11 and 12 from 20m to 10m resolution.
        #
        if band.endswith(('_B11.tif', '_B12.tif')):
            #
            # Nearest neighbour interpolation.
            #
            band_array = scipy.ndimage.zoom(band_array, 2, order=0)

        #
        # Adjust output layer to 0 where there is nodata.
        #
        noData_array = numpy.where((band_array == 0), (0), noData_array)

    #
    # Invert array to mask, where 0 are values to be processed and 1 is nodata.
    #
    noData_array = numpy.where((noData_array == 0), (1), (0))

    #
    # Write the data to the designated band.
    #
    outBand = outDs.GetRasterBand(1)
    outBand.WriteArray(noData_array, 0, 0)

    #
    # Flush data to disk.
    #
    outBand.FlushCache()

    #
    # Calculate statistics.
    #
    stats = outBand.ComputeStatistics(False)
    outBand.SetStatistics(stats[0], stats[1], stats[2], stats[3])

    del gdal_format
    del outDs
    del outBand
    del noData
    img = None
    band_id = None
    band_array = None
    outBand = None
    stats = None

    return noData_array


def check_imgFolders(options_in):

    #
    # Create list for IMG_DATA folder and existing PROC_DATA folder paths.
    #
    imgFolders = []
    procFolders = []

    for dirpath, dirnames, filenames in os.walk(
            options_in.read_dir, topdown=True):

        for dirname in dirnames:

            if dirname == 'IMG_DATA':

                imgFolders.append(os.path.join(dirpath, dirname))

            elif dirname == 'PROC_DATA':

                procFolder = os.path.join(dirpath, dirname)

                procFolders.append(procFolder)
    #
    # Determine which tile folders have no PROC_DATA folder.
    #
    unprocFolders = []

    for imgFolder in imgFolders:

        test_path = os.path.join(os.path.dirname(imgFolder), 'PROC_DATA')

        if test_path in procFolders:
            continue
        else:
            unprocFolders.append(imgFolder)

    #
    # Check validity of relevant PROC_DATA contents.
    #
    for procFolder in procFolders:

        #
        # Initialize variables for PROC_DATA folder.
        #
        caltembyt_path = None
        caltembyt_size = 0
        calrefbyt_path = None
        calrefbyt_size = 0
        remove_procFolder = None

        for filename in os.listdir(procFolder):

            if filename.endswith('caltembyt_lndstlk.dat'):

                caltembyt_path = os.path.join(procFolder, filename)
                caltembyt_size = os.path.getsize(caltembyt_path)

                if caltembyt_size < 5:
                    remove_procFolder = True
                    logger.info('caltembyt file error: ' + caltembyt_path)

            elif filename.endswith('calrefbyt_lndstlk.dat'):

                calrefbyt_path = os.path.join(procFolder, filename)
                calrefbyt_size = os.path.getsize(calrefbyt_path)

                if calrefbyt_size < 5:
                    remove_procFolder = True
                    logger.info('calrefbyt file error: ' + calrefbyt_path)

        #
        # Removes PROC_DATA folders with problem files and adds to list to be
        # processed.
        #
        if remove_procFolder is True:
            shutil.rmtree(procFolder)
            logger.info('Removed Folder: ' + procFolder)
            unprocFolders.append(procFolder)

    #
    # Create the content of the popup window.
    #
    question = (
        'Number of tiles found: {}'
        '\n\nDo you want to process all unprocessed folders [{}]?'
        ).format(len(imgFolders), len(unprocFolders))

    print question

    ins = None
    bool_ans = None

    if options_in.auto is not None:

        ins = 'y'

    else:

        while True:

            ins = raw_input('Answer [y/n]: ')

            if ins == 'y' or ins == 'n':

                break

            else:

                print 'Your input should indicate yes [y] or no [n].'

    if ins == 'y' or ins == 'Y' or ins == 'yes' or ins == 'Yes':

        bool_ans = True

    return bool_ans, unprocFolders


def convert_imgs(root_folder, imgFolders):

    start_time = datetime.datetime.now()

    print '================================================================='
    print 'Hold on to your hat. This may take ~45s per S2 tile folder.'
    print 'Number of unprocessed IMG_DATA folders found: {}'.format(
        len(imgFolders))
    print 'Estimated time: {} minutes'.format(int(len(imgFolders)) * 0.75)
    print 'Start time: {}'.format(start_time.time())
    print '=================================================================\n'

    message = (
        'Root Folder: {} \nNumber of unprocessed IMG_DATA folders '
        'found: {}\nStart time: {}'
        ).format(root_folder, len(imgFolders), start_time.time())
    logger.info(message)
    #
    # Register all of the GDAL drivers.
    #
    gdal.AllRegister()

    #
    # Possible XML Schema namespaces (plus a few potential future ones.)
    #
    XML_namespaces = ['https://psd-14.sentinel2.eo.esa.int/',
                      'https://psd-12.sentinel2.eo.esa.int/',
                      'https://psd-13.sentinel2.eo.esa.int/',
                      'https://psd-15.sentinel2.eo.esa.int/',
                      'https://psd-16.sentinel2.eo.esa.int/']

    i = 0

    for imgFolder in imgFolders:

        metadata_path = []

        for fn in os.listdir(os.path.dirname(imgFolder)):
            if ((fn.startswith('S2A_') or fn.startswith('MTD'))
                    and fn.endswith('.xml')):
                metadata_file = fn
                metadata_path.append(
                    os.path.join(os.path.dirname(imgFolder), fn))

        if len(metadata_path) > 1:
            message = (
                'Make sure only the original metadata exists in the tile '
                'folder\n{}\nAborting.'
                ).format(os.path.dirname(imgFolder))
            print message
            logger.critical(message)
            sys.exit()

        #
        # Parse the metadata xml-file. There should only be one path.
        #
        try:
            tree = etree.parse(metadata_path[0])
        except Exception as e:
            message = (
                '{} {} in {} could not be parsed.'
                ).format(str(e), metadata_path[0], imgFolder)
            logger.critical(message)

        for namespace in XML_namespaces:

            try:

                #
                # Get metadata values from the General_Info element.
                #
                General_Info = tree.find(
                    '{' + namespace + 'PSD/'
                    'S2_PDI_Level-1C_Tile_Metadata.xsd}General_Info')
                TILE_ID = General_Info.find('TILE_ID').text
                tile_id = TILE_ID[-12:-7]
                SENSING_TIME = General_Info.find('SENSING_TIME').text

                #
                # Get metadata values from the Geometric_Info element.
                #
                Geometric_Info = tree.find(
                    '{' + namespace + 'PSD/'
                    'S2_PDI_Level-1C_Tile_Metadata.xsd}Geometric_Info')
                HORIZONTAL_CS_NAME = Geometric_Info.find(
                    'Tile_Geocoding').find('HORIZONTAL_CS_NAME').text
                HORIZONTAL_CS_CODE = Geometric_Info.find(
                    'Tile_Geocoding').find('HORIZONTAL_CS_CODE').text
                break

            except Exception as e:
                message = ('{} {} in {} could not be parsed with {}.').format(
                    str(e), metadata_path[0], imgFolder, namespace)
                logger.error(message)
        else:
            message = ('{} in {} could not be parsed.').format(
                metadata_path[0], imgFolder)
            logger.error(message)
            continue

        tile_bands = []

        #
        # Retrieve desired bands from old data structure.
        #
        if metadata_file.startswith('S2A_'):
            for dirpath, dirnames, filenames in os.walk(
                    imgFolder, topdown=True):
                for filename in filenames:
                    if (filename.startswith('S2A')
                            and filename.endswith('.jp2')
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
            for dirpath, dirnames, filenames in os.walk(
                    imgFolder, topdown=True):
                for filename in filenames:
                    if (filename.startswith('T')
                            and filename.endswith('.jp2')
                            and (fnmatch.fnmatch(filename, '*_B02.*')
                                 or fnmatch.fnmatch(filename, '*_B03.*')
                                 or fnmatch.fnmatch(filename, '*_B04.*')
                                 or fnmatch.fnmatch(filename, '*_B08.*')
                                 or fnmatch.fnmatch(filename, '*_B11.*')
                                 or fnmatch.fnmatch(filename, '*_B12.*'))):

                        tile_bands.append(os.path.join(dirpath, filename))

        #
        # Put bands in numeric order for processing. Redundant, keep anyways.
        #
        tile_bands.sort()

        #
        # Create the folder for processed data if it doesn't exist.
        #
        PROC_DATA = os.path.join(os.path.dirname(imgFolder), 'PROC_DATA')
        if not os.path.exists(PROC_DATA):
            os.mkdir(PROC_DATA)

        #
        # Create file to save stack to -- there is probably a better way to do
        # this! Also create fake thermal band file.
        #

        print tile_bands
        noData_array = None
        noData_array = nodata_array(tile_bands, PROC_DATA)

        for band in tile_bands:

            if band.endswith('_B02.tif'):

                #
                # Open B02 image in order to initialize .dat files. Any band
                # with 10m pixel size would do. Gets georeferencing info, etc.
                #
                img = gdal.Open(band, gdal.GA_ReadOnly)
                band_id = band[-6:-4]
                if img is None:
                    message = (
                        '{} in {} could not be opened.'
                        ).format(band, imgFolder)
                    print message
                    logger.critical(message)
                    sys.exit(1)

                print '-------------------------------------------------------'
                print 'Processing tile {} sensed at {}'.format(
                    tile_id, SENSING_TIME)
                print 'Coordinate system: {}, {}\n\n'.format(
                    HORIZONTAL_CS_NAME, HORIZONTAL_CS_CODE)

                #
                # Get raster georeference info from B02 for output .dat files.
                #
                projection = img.GetProjection()
                transform = img.GetGeoTransform()
                # xOrigin = transform[0]
                # yOrigin = transform[3]
                # pixelWidth = transform[1]
                # pixelHeight = transform[5]

                #
                # Establish size of raster from B02 for stacked output file.
                #
                img_rows = img.RasterYSize
                img_cols = img.RasterXSize

                #
                # Open output format driver, see gdal_translate for formats.
                #
                gdal_format = 'ENVI'
                driver = gdal.GetDriverByName(gdal_format)

                #
                # Test stacked band file path.
                #
                stacked_file = '{}calrefbyt_lndstlk.dat'.format(
                    os.path.basename(band)[:-7])
                filepath = os.path.join(PROC_DATA, stacked_file)

                #
                # Print driver for stacked layers (6 bands, 8-bit unsigned).
                #
                outDs = driver.Create(filepath, img_cols, img_rows, 6,
                                      gdal.GDT_Byte)
                if outDs is None:
                    print 'Could not create test file.'
                    sys.exit(1)

                #
                # Georeference the stacked .dat file and set the projection.
                #
                outDs.SetGeoTransform(transform)
                outDs.SetProjection(projection)

                print 'Creating fake thermal band for {}\n'.format(tile_id)

                #
                # Create thermal band file path.
                #
                thermal_file = '{}caltembyt_lndstlk.dat'.format(
                    os.path.basename(band)[:-7])
                filepath = os.path.join(PROC_DATA, thermal_file)

                #
                # Print driver for fake thermal band (1 band, 8-bit unsigned).
                #
                thermDs = driver.Create(filepath, img_cols, img_rows, 1,
                                        gdal.GDT_Byte)
                if thermDs is None:
                    print 'Could not create test file.'
                    sys.exit(1)

                #
                # Georeference the fake thermal band and set the projection.
                #
                thermDs.SetGeoTransform(transform)
                thermDs.SetProjection(projection)

                #
                # Create constant array with a value of 110.
                #
                therm_array = numpy.ones((img_rows, img_cols)).astype(int)
                therm_array = therm_array * 110

                #
                # Remove pixels having no data in any of the input bands.
                #
                therm_array = numpy.where(
                    (noData_array == 1), (0), therm_array)

                #
                # Write the data to the designated band.
                #
                outBand = thermDs.GetRasterBand(1)
                outBand.WriteArray(therm_array, 0, 0)

                #
                # Flush data to disk and set the NoData value.
                #
                outBand.FlushCache()
                # outBand.SetNoDataValue(-99)

                #
                # Calculate statistics.
                #
                stats = outBand.ComputeStatistics(False)
                outBand.SetStatistics(stats[0], stats[1], stats[2], stats[3])

                print 'Fake thermal band created.\n\n'
                print 'Elapsed time: {}'.format(
                    datetime.datetime.now() - start_time)

                #
                # Clean up.
                #
                del driver
                band_id = None
                therm_array = None
                outBand = None
                stats = None
                thermDs = None
                img = None

        print 'Creating 6 band stack for tile {}\n'.format(tile_id)

        for band in tile_bands:

            #
            # Keep track of which band we are writing to in the stacked file.
            #

            band_in_stack = None

            if band.endswith('_B02.jp2'):
                band_in_stack = 1
            if band.endswith('_B03.jp2'):
                band_in_stack = 2
            if band.endswith('_B04.jp2'):
                band_in_stack = 3
            if band.endswith('_B08.jp2'):
                band_in_stack = 4
            if band.endswith('_B11.jp2'):
                band_in_stack = 5
            if band.endswith('_B12.jp2'):
                band_in_stack = 6

            #
            # This if statement is redundant now, but keep for now anyways.
            #
            if band.endswith(('_B02.jp2', '_B03.jp2', '_B04.jp2', '_B08.jp2',
                              '_B11.jp2', '_B12.jp2')):

                #
                # Open the band as read only.
                #
                img = gdal.Open(band, gdal.GA_ReadOnly)
                band_id = band[-6:-4]
                if img is None:
                    message = ('Could not open band #{} in {}').format(
                        band_id, imgFolder)
                    print message
                    logger.critical(message)
                    sys.exit(1)
                print 'Processing band #{}'.format(band_id)

                #
                # Retrieve band and get dimensions.
                #
                img_band = img.GetRasterBand(1)
                img_rows = img.RasterYSize
                img_cols = img.RasterXSize

                #
                # Read image as array using GDAL.
                #
                img_array = img_band.ReadAsArray(0, 0, img_cols, img_rows)
                print 'Original shape: {}'.format(img_array.shape)
                # print 'Original max: {}'.format(numpy.amax(img_array))
                # print 'Original min: {}'.format(numpy.amin(img_array))

                #
                # Adjust outliers (very high reflectance and negative).
                #
                outData = img_array / 10000.0
                outData = numpy.where((outData > 1), (1), outData)
                outData = numpy.where((outData < 0), (0), outData)

                #
                # Old, slow method for reference.
                #
                # for i in range(0, img_rows):
                #     for j in range(0, img_cols):
                #         if outData[i,j] > 1:
                #             outData[i,j] = 1
                #         elif outData[i,j] < 0:
                #             outData[i,j] = 0

                img_array = None

                #
                # Resample bands 11 and 12 from 20m to 10m resolution.
                #
                if band.endswith(('_B11.tif', '_B12.tif')):

                    print 'start resample: {}'.format(
                        datetime.datetime.now() - start_time)

                    print 'Resample by a factor of 2 - nearest interpolation.'
                    outData = scipy.ndimage.zoom(outData, 2, order=0)

                    # print 'Resample by a factor of 2 - bilinear interpolation.'
                    #
                    # # Reference:
                    # # ndimage "bilinear" spline interpolation
                    # # (a bit weird, not really bilinear...)
                    # #
                    # # outData = scipy.ndimage.zoom(outData, 2, order=1)
                    #
                    # #
                    # # Calculate bilinear interpolation (2x2) using pillow
                    # # (comparable to ArcGIS output)
                    # #
                    # im = Image.fromarray(outData)
                    # img_cols_2 = int(img_cols)*2
                    # img_rows_2 = int(img_rows)*2
                    # im = im.resize((img_cols_2, img_rows_2), resample=Image.BILINEAR)
                    # outData = numpy.array(im)
                    #
                    # #
                    # # Close and clean up.
                    # #
                    # im.close()
                    # del im

                    print 'end resample: {}'.format(
                        datetime.datetime.now() - start_time)
                    print 'Resampled size: {}'.format(outData.shape)

                #
                # Convert to 8-bit.
                #
                outData = ((numpy.absolute(outData) * 255.0) + 0.5).astype(int)

                #
                # Remove pixels having no data in any of the input bands.
                #
                outData = numpy.where((noData_array == 1), (0), outData)

                #
                # Write the data to the designated band.
                #
                outBand = outDs.GetRasterBand(band_in_stack)
                outBand.WriteArray(outData, 0, 0)

                #
                # Flush data to disk and set the NoData value.
                #
                outBand.FlushCache()
                # outBand.SetNoDataValue(-99)

                #
                # Calculate statistics.
                #
                stats = outBand.ComputeStatistics(False)
                outBand.SetStatistics(stats[0], stats[1], stats[2], stats[3])

                print 'Band #{} completed.\n'.format(band_id)
                print 'Elapsed time: {}'.format(
                    datetime.datetime.now() - start_time)

                #
                # Clean up to avoid problems processing bands to follow.
                #
                del outData
                del outBand
                img_band = None
                band_id = None
                stats = None
                img = None

        i += 1

        message = (
            'Tile {}, {} of {} processed and stacked.'
            ).format(tile_id, str(i), len(imgFolders))
        print message
        print '------------------------------------------------------------\n'
        logger.info(message)

        #
        # Clean up to avoid problems processing tiles to follow.
        #
        del metadata_path
        del tree
        del SENSING_TIME
        del HORIZONTAL_CS_NAME
        del HORIZONTAL_CS_CODE
        del tile_bands
        del tile_id
        outDs = None
        noData_array = None

    print '\n\n==============================================================='
    print 'Done processing.'
    print 'End time: {}'.format(datetime.datetime.now().time())
    print 'Total elapsed time: {}'.format(datetime.datetime.now() - start_time)
    print '===============================================================\n\n'
    message = ('End time: {}').format(datetime.datetime.now().time())
    logger.info(message)
    message = ('Total elapsed time: {}').format(
        datetime.datetime.now() - start_time)
    logger.info(message)


if __name__ == '__main__':

    #
    # Set-up logger.
    #
    logging.basicConfig(filename='log/converter.log',
                        format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.DEBUG)
    logger = logging.getLogger('converter ')

    #
    # Define S2 root folder, where all downloads are located.
    #
    options = get_args()
    root_folder = options.read_dir

    bool_answer, imgFolders_toProcess = check_imgFolders(options)

    if not bool_answer:
        print 'No folders processed.'
        sys.exit(1)

    if imgFolders_toProcess == 0:

        print 'No new folders to process.'
        logger.info('No new folders to process.')

    else:

        convert_imgs(root_folder, imgFolders_toProcess)
