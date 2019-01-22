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

from osgeo import gdal
import numpy
import scipy.ndimage

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
            '-wa', '--warp', dest='warp', action='store', type=str,
            help='EPSG code for warping.', default=None)
        parser.add_argument(
            '--auto', dest='auto', action='store',
            help=('No user input necessary -- automatically converts all '
                  'previously not converted images files.'),
            default=None)

        return parser.parse_args()


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


def warp_imgs(root_folder, imgFolders, warp_epsg):

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

        warp_opts = gdal.WarpOptions(
            format="GTiff",
            resampleAlg=gdal.GRIORA_Bilinear,
            dstSRS='EPSG:{}'.format(warp_epsg))

        for band in tile_bands:

            orginal_name = os.path.basename(band)[:-4]
            warped_name = '{}{}'.format(orginal_name, '.tif')
            warped_filepath = os.path.join(imgFolder, warped_name)
            band_filepath = band

            img = gdal.Open(band, gdal.GA_ReadOnly)
            ds = gdal.Warp(warped_filepath, img, options=warp_opts)
            img = None
            ds = None

            os.remove(band)

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
    logging.basicConfig(filename='log/warp.log',
                        format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.DEBUG)
    logger = logging.getLogger('warp ')

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

        warp_imgs(root_folder, imgFolders_toProcess, options.warp)
