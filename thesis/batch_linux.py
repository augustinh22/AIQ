#-------------------------------------------------------------------------------
# Name:        SIAM batch creator
# Purpose:     This script uses a Tkinter GUI to create a SIAM
#              batch file based on SIAM compatible files located in a target
#              directory.
#
# Author:      h.Augustin
#
# Created:     21.12.2016
# Modified:    07.12.2017
#
#-------------------------------------------------------------------------------

#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import shutil
import fnmatch
import argparse
import logging
from time import strftime as date

import gdal

# Set GDAL environment variable for translating grib to tiff.
# os.environ['GDAL_DATA'] = r'C:\Program Files\GDAL\gdal-data'

def get_args():

    '''Gets arguments from command line. '''

    #
    # Create download tool help response.
    #
    prog = os.path.basename(sys.argv[0])

    if len(sys.argv) == 1:

        print('\n        {0} [options]'
            '\n        Help: {1} --help'
            '\n        or: {1} -h'
            '\nexample python {0} -r /path/to/data/ --burnt-area 1').format(
            sys.argv[0], prog)

        sys.exit(-1)

    else:

        parser = argparse.ArgumentParser(prog=prog,
            usage='%(prog)s [options]',
            description='SIAM batch creator.',
            argument_default=None,
            epilog='Go get \'em!')

        #
        # General arguments.
        #
        parser.add_argument('-r', '--read_dir', dest='read_dir', action='store',
                type=str, help='Path where downloaded products are located.',
                default=None)
        parser.add_argument('-s', '--siam', dest='siam', action='store',
                type=str, help='Path to SIAM executable.',
                default='/opt/siam/SIAM_compilation_Ubuntu/SIAM_Ubuntu_r88v7.exe')
        parser.add_argument('-w', '--write_dir', dest='write_dir', action='store',
                type=str, help='Path to save SIAM batch.',
                default='/home/hannah/repos/AIQ/thesis/siam/')
        parser.add_argument('--auto', dest='auto', action='store',
                help=('Automatically creates batch file without user input.'),
                choices=['y','n'], default=None)

        #
        # Optional parameters.
        #
        parser.add_argument('-03', '--bin-mask', dest='var03', action='store',
                help=('Use a binary mask for processing. Default 0.'),
                choices=['1','0'], default=0)
        parser.add_argument('-07', '--crisp', dest='var07', action='store',
                help=('Crisp[1] or fuzzy [0] classification. Default 1.'),
                choices=['1','0'], default=1)
        parser.add_argument('-09', '--smoke-plume', dest='var09', action='store',
                help=('Create smoke-plume mask. Default 0.'),
                choices=['1','0'], default=0)
        parser.add_argument('-10', '--cloud', dest='var10', action='store',
                help=('Create cloud mask. Default 0.'),
                choices=['1','0'], default=0)
        parser.add_argument('-11', '--burnt-area', dest='var11', action='store',
                help=('Create burnt-area mask. Default 0.'),
                choices=['1','0'], default=0)
        parser.add_argument('-12', '--veg-bin', dest='var12', action='store',
                help=('Create binary vegetation mask. Default 1.'),
                choices=['1','0'], default=1)
        parser.add_argument('-13', '--veg-tri', dest='var13', action='store',
                help=('Create trinary vegetation mask. Default 0.'),
                choices=['1','0'], default=0)
        parser.add_argument('-14', '--baresoil', dest='var14', action='store',
                help=('Create trinary baresoil builtup mask. Default 0.'),
                choices=['1','0'], default=0)
        parser.add_argument('-15', '--cloud-tri', dest='var15', action='store',
                help=('Create trinary cloud mask. Default 0.'),
                choices=['1','0'], default=0)
        parser.add_argument('-16', '--water-tri', dest='var16', action='store',
                help=('Create trinary water mask. Default 0.'),
                choices=['1','0'], default=0)
        parser.add_argument('-17', '--shadow-tri', dest='var17', action='store',
                help=('Create trinary shadow mask. Default 0.'),
                choices=['1','0'], default=0)
        parser.add_argument('-18', '--urban-bin', dest='var18', action='store',
                help=('Create binary urban area mask. Default 0.'),
                choices=['1','0'], default=0)
        parser.add_argument('-19', '--shape', dest='var19', action='store',
                help=('Calculate shape indicators. Default 0.'),
                choices=['1','0'], default=1)

        return parser.parse_args()


def check_procFolders(options):

    procFolders = []
    siamFolders = []

    for dirpath, dirnames, filenames in os.walk(options.read_dir, topdown=True):

        for dirname in dirnames:

            if dirname == 'PROC_DATA':

                procFolders.append(os.path.join(dirpath, dirname))

            elif dirname == 'siamoutput':

                siamFolders.append(os.path.join(dirpath, dirname))
    #
    # Determine which tile folders have no siamoutput folder.
    #
    unprocFolders = []

    for procFolder in procFolders:

        test_path = os.path.join(procFolder, 'siamoutput')

        if test_path in siamFolders:
            print os.listdir(test_path)
            print sum(os.path.getsize(f) for f in os.listdir(test_path) if os.path.isfile(f))
            continue
        else:
            unprocFolders.append(procFolder)

    #
    # Check validity of relevant siamoutput contents.
    #
    for siamFolder in siamFolders:

        #
        # Initialize variables for PROC_DATA folder.
        #
        siam_Parts = [ '18SpCt',
                       '33SharedSpCt',
                       '48SpCt',
                       '96SpCt',
                       'VegBinaryMask',
                       'fRatioGreennessIndex' ]

        remove_siamFolder = None

        for filename in os.listdir(siamFolder):

            #
            # Check only .dat files.
            #
            if filename.endswith('.dat'):

                for part in siam_Parts:

                    siam_wildcard = '*{}*'.format(part)

                    if fnmatch.fnmatch(filename, siam_wildcard):

                        file_path = os.path.join(siamFolder, filename)
                        file_size = os.path.getsize(file_path)

                        if file_size < 5:
                            remove_siamFolder = True
                            logger.info('File smaller than 5 bytes: ' +
                                file_path)

        #
        # Removes siamoutput folders with problem files and adds to list to be
        # processed.
        #
        if remove_siamFolder is True:
            shutil.rmtree(siamFolder)
            logger.info('Removed Folder: ' + siamFolder)
            unprocFolders.append(os.path.dirname(siamFolder))

    #
    # If no unprocessed folders, skip input from user.
    #
    if len(unprocFolders) == 0:
        question = ('{} unprocessed tiles from {} found.').format(
            str(len(unprocFolders)), str(len(procFolders)))
        print question
        bool_answer = None
        return bool_answer, unprocFolders

    question = ('{} unprocessed tiles from {} found. '
        'Create batch for SIAM?').format(str(len(unprocFolders)),
        str(len(procFolders)))

    print question

    ins = None
    bool_answer = None

    if options.auto is not None:

        ins = 'y'

    else:

        while True:

            ins = raw_input('Answer [y/n]: ')

            if (ins == 'y' or ins == 'n'):

                break

            else:

                print  'Your input should indicate yes [y] or no [n].'

    if ins == 'y' or ins == 'Y' or ins == 'yes' or ins == 'Yes':

        bool_answer = True

    return bool_answer, unprocFolders


def create_batch(options, unprocFolders):

    #
    # Register all of the GDAL drivers.
    #
    gdal.AllRegister()

    #
    # Create empty batch file for SIAM.
    #

    timestamp = date('%Y%m%dT%H%M%S')

    if len(unprocFolders) > 1:

        batFilename = 'SIAM_multiple_batch_LANDSAT_{}.sh'.format(timestamp)

    else:

        batFilename = 'SIAM_batch_LANDSAT_{}.sh'.format(timestamp)

    batch_path = os.path.join(options.write_dir, batFilename)

    with open(batch_path, 'a') as f:

        f.write('#!/bin/bash\n')

    #
    # Convert binary variables and image type identifier from GUI to strings.
    #
    var00 = options.siam
    var03 = str(options.var03)
    var06 = str(1)
    var07 = str(options.var07)
    var09 = str(options.var09)
    var10 = str(options.var10)
    var11 = str(options.var11)
    var12 = str(options.var12)
    var13 = str(options.var13)
    var14 = str(options.var14)
    var15 = str(options.var15)
    var16 = str(options.var16)
    var17 = str(options.var17)
    var18 = str(options.var18)
    var19 = str(options.var19)

    for unprocFolder in unprocFolders:

        var01 = unprocFolder

        #
        # Create the folder for SIAM output data if it doesn't exist.
        #
        siam_output = os.path.join(unprocFolder, 'siamoutput')

        if not(os.path.exists(siam_output)):

            os.mkdir(siam_output)

        var08 = siam_output

        #
        # Fill var02 variable with the calrefbyt filename.
        #
        for filename in os.listdir(unprocFolder):

            if (filename.endswith('.dat')
                    and fnmatch.fnmatch(filename, '*_calrefbyt_*')):

                var02 = filename

        #
        # Go to next folder if calibrated, stacked raster not yet craeted.
        #
        if not var02:

            print '*_calrefbyt_* not found in {}'.format(unprocFolder)
            logger.error('*_calrefbyt_* not found in {}'.format(unprocFolder))
            print 'Tile not processed.'

            continue

        #
        # Path to calrefbyt.
        #
        calrefbyt = os.path.join(unprocFolder, var02)

        #
        # Open image to calculate rows and columns.
        #
        img = gdal.Open(calrefbyt, gdal.GA_ReadOnly)

        if img is None:

            print '\nCould not open *calrefbyt*.dat'
            print 'Folder not processed: {}\n'.format(unprocFolder)
            logger.error(('Could not open *calrefbyt*.dat. '
                'Folder not processed: {}\n').format(unprocFolder))

            continue

        var04 = str(img.RasterYSize)  # Rows.
        var05 = str(img.RasterXSize)  # Columns.

        #
        # Create string to write to batch file.
        #
        batch_entry = ' '.join((var00, var01, var02, var03, var04, var05,
            var06, var07, var08, var09, var10, var11, var12, var13, var14,
            var15, var16, var17, var18, var19))

        with open(batch_path, 'a') as f:

            f.write(batch_entry + '\n')
        ## print batch_entry

        #
        # Clean up.
        #
        img = None

    #
    # Location.
    #
    print '\n\n{} created.\nSaved to: {}\n\n'.format(batFilename, batch_path)
    logger.info('{} created. Saved to: {}\n\n'.format(batFilename, batch_path))


if __name__ == '__main__':
    #
    # Set-up logger.
    #
    logging.basicConfig(filename='log/batch.log',
                    format='%(asctime)s:%(levelname)s:%(message)s',
                    level=logging.DEBUG)
    logger = logging.getLogger('batch')

    #
    # Parse command line to get global arguments.
    #
    options = get_args()

    bool_answer, unprocFolders = check_procFolders(options)

    if bool_answer:

        create_batch(options, unprocFolders)

    else:

        print '\nNo SIAM batch file created.\n'

        sys.exit()


#------------------------------------------------------------------------------#
#                Parameters from Example batch file explained.                 #
#------------------------------------------------------------------------------#

# (0) C:\SIAM\SIAM_r88v7\SIAM_License_Executables\SIAM_r88v7_Windows.exe   [SIAM executable]
# (1) E:\Temp_ha\S2A_OPER_MSI_L1C_TL_MTI__20150813T201603_A000734_T33TUN_N01.03   [location of calibrated files]
# (2) S2A_OPER_MSI_L1C_TL_MTI__20150813T201603_A000734_T33TUN_calrefbyt_lndstlk.dat   [calibrated file]
# (3) 0  [Use a binary mask for processing]
# (4) 10980  [rows]
# (5) 10980  [columns]
# (6) 1  [image type: ("LANDSAT_LIKE","1")("SPOT_LIKE","2")("AVHRR_LIKE","3")("VHR_LIKE","4")]
# (7) 1  [Select crisp or fuzzy classification]
# (8) E:\Temp_ha\S2A_OPER_MSI_L1C_TL_MTI__20150813T201603_A000734_T33TUN_N01.03\siamoutput  [output folder]
# (9) 0  [Smoke-Plume mask]
# (10) 0  [Cloud Mask]
# (11) 0  [Burnt area mask]
# (12) 1  [Vegetation Binary mask]
# (13) 0  [Vegetation Trinary mask]
# (14) 0 [Baresoil Builtup Trinary mask]
# (15) 0 [Cloud Trinary mask]
# (16) 0 [Water Trinary mask]
# (17) 0 [Shadow Trinary mask]
# (18) 1 [Urban area binary mask]
# (19) 0 [SHAPE???]
