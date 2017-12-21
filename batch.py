#-------------------------------------------------------------------------------
# Name:        SIAM batch creator
# Purpose:     This script uses a Tkinter GUI to create a SIAM
#              batch file based on SIAM compatible files located in a target
#              directory.
#
# Author:      h.Augustin
#
# Created:     21.12.2016
#
#-------------------------------------------------------------------------------

#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import sys
import Tkinter
import fnmatch
import subprocess
import tkMessageBox

import gdal

# Set GDAL environment variable for translating grib to tiff.
# os.environ['GDAL_DATA'] = r'C:\Program Files\GDAL\gdal-data'


def param_check():

    if var00.get() == '':

        info = 'Please enter SIAM executable location!'
        tkMessageBox.showerror('Missing Parameter', info)

    elif s2_Folder.get() == '':

        info = 'Please enter root folder!'
        tkMessageBox.showerror('Missing Parameter', info)

    elif var06.get() == 'Select one.':

        info = 'Please select an image type!\n\nSentinel 2 is LANDSAT_LIKE.'
        tkMessageBox.showerror('Missing Parameter', info)

    else:

        master.quit()


def show_params():

    if var06.get() == 'Select one.':

        info = 'Please select an image type!\n\nSentinel 2 is LANDSAT_LIKE.'
        tkMessageBox.showerror('Missing Parameter', info)

    else:

        test = ('S2 path:\n  {}\n\n'
            'Image type: {} ({})\n'
            'Sensor type: {} ({})\n'
            'Processing with a binary mask: {}\n'
            'Crisp classification: {}\n'
            'Smoke-plume mask: {}\n'
            'Cloud mask: {}\n'
            'Burnt area mask: {}\n'
            'Vegetation binary mask: {}\n'
            'Vegetation trinary mask: {}\n'
            'Baresoil built-up trinary mask: {}\n'
            'Cloud trinary mask: {}\n'
            'Water trinary mask: {}\n'
            'Shadow trinary mask: {}\n'
            'Urban area binary mask: {}\n'
            'Shape: {}').format(
            s2_Folder.get(), var06.get(), image_type[var06.get()],
            sensor_type.get(), data_type[sensor_type.get()],
            var03.get(), var07.get(), var09.get(), var10.get(), var11.get(),
            var12.get(), var13.get(), var14.get(), var15.get(), var16.get(),
            var17.get(), var18.get(), var19.get())

        tkMessageBox.showinfo('Test Parameters', test)

#------------------------------------------------------------------------------#
#                                     GUI                                      #
#------------------------------------------------------------------------------#

#
# Create GUI interface frames.
#
master = Tkinter.Tk()
title = Tkinter.Frame(master)
title.pack(side='top')
siam_input = Tkinter.Frame(master)
siam_input.pack()
s2_input = Tkinter.Frame(master)
s2_input.pack()
img_options = Tkinter.Frame(master)
img_options.pack()
sensor_options = Tkinter.Frame(master)
sensor_options.pack()
binary = Tkinter.Frame(master)
binary.pack()
buttons = Tkinter.Frame(master)
buttons.config(pady=15)
buttons.pack(side='bottom')

#
# Title
#
label01 = Tkinter.Label(title, text="SIAM Batch Creator")
label01.config(width=30, font=("Courier", 44))
label01.pack(pady=15)

#
# Define SIAM .exe location text entry box.
#
label02 = Tkinter.Label(siam_input, text="Insert SIAM .exe path: ")
label02.pack(pady=15, side='left')

var00 = Tkinter.StringVar()
var00.set(
    r'C:\SIAM\SIAM_r88v7\SIAM_License_Executables\SIAM_r88v7_Windows.exe')
var00x = Tkinter.Entry(siam_input, textvariable=var00, justify='left')
var00x.config(width=61)
var00x.pack(pady=15, side='right')

#
# Define S2 root folder text entry box.
#
label03 = Tkinter.Label(s2_input, text='Path to root folder where images '
    'including .dat files for SIAM are saved: ')
label03.pack(pady=15, side='left')

cwd = os.getcwd()
root_folder = os.path.join(cwd, 'tempS2')

s2_Folder = Tkinter.StringVar()
s2_Folder.set(root_folder)
s2_Folderx = Tkinter.Entry(s2_input, textvariable=s2_Folder, justify='left')
s2_Folderx.config(width=40)
s2_Folderx.pack(pady=15, side='right')

#
# Create image-type dropdown menu.
#
label04 = Tkinter.Label(img_options, text="Select an image type for SIAM: ")
label04.pack(side='left')

var06 = Tkinter.StringVar()
image_type = {"LANDSAT_LIKE": 1, "SPOT_LIKE": 2, "AVHRR_LIKE": 3, "VHR_LIKE": 4}
var06.set('Select one.')
var06x = Tkinter.OptionMenu(img_options, var06, *image_type.keys())
var06x.config(width=15, anchor='w')
var06x.pack(pady=10, side='right')
# image_type[var06.get()] returns the key value

label05 = Tkinter.Label(sensor_options, text="Select the actual sensor: ")
label05.pack(side='left')

sensor_type = Tkinter.StringVar()
data_type = {"Sentinel-2": 1, "Landsat 8": 2, "clip_mosaic_calrefbyt": 3}
sensor_type.set('Select one.')
sensor_typex = Tkinter.OptionMenu(sensor_options, sensor_type, *data_type.keys())
sensor_typex.config(width=15, anchor='w')
sensor_typex.pack(pady=10, side='right')

#
# Create checkboxes for all binary variables.
#
var03 = Tkinter.IntVar()
var03x = Tkinter.Checkbutton(binary, text="Use a binary mask for processing",
    variable=var03, anchor='w', height=1, width=50)
var03x.pack()

var07 = Tkinter.IntVar()
var07.set(1)
var07x = Tkinter.Checkbutton(binary,
    text="Use crisp classification (default=true)",
    variable=var07, anchor='w', height=1, width=50)
var07x.pack()

var09 = Tkinter.IntVar()
var09x = Tkinter.Checkbutton(binary, text="Smoke-plume mask",
    variable=var09, anchor='w', height=1, width=50)
var09x.pack()

var10 = Tkinter.IntVar()
var10x = Tkinter.Checkbutton(binary, text="Cloud mask",
    variable=var10, anchor='w', height=1, width=50)
var10x.pack()

var11 = Tkinter.IntVar()
var11x = Tkinter.Checkbutton(binary, text="Burnt area mask",
    variable=var11, anchor='w', height=1, width=50)
var11x.pack()

var12 = Tkinter.IntVar()
var12x = Tkinter.Checkbutton(binary, text="Vegetation binary mask",
    variable=var12, anchor='w', height=1, width=50)
var12x.pack()

var13 = Tkinter.IntVar()
var13x = Tkinter.Checkbutton(binary, text="Vegetation trinary mask",
    variable=var13, anchor='w', height=1, width=50)
var13x.pack()

var14 = Tkinter.IntVar()
var14x = Tkinter.Checkbutton(binary, text="Baresoil builtup trinary mask",
    variable=var14, anchor='w', height=1, width=50)
var14x.pack()

var15 = Tkinter.IntVar()
var15x = Tkinter.Checkbutton(binary, text="Cloud trinary mask",
    variable=var15, anchor='w', height=1, width=50)
var15x.pack()

var16 = Tkinter.IntVar()
var16x = Tkinter.Checkbutton(binary, text="Water trinary mask",
    variable=var16, anchor='w', height=1, width=50)
var16x.pack()

var17 = Tkinter.IntVar()
var17x = Tkinter.Checkbutton(binary, text="Shadow trinary mask",
    variable=var17, anchor='w', height=1, width=50)
var17x.pack()

var18 = Tkinter.IntVar()
var18x = Tkinter.Checkbutton(binary, text="Urban area binary mask",
    variable=var18, anchor='w', height=1, width=50)
var18x.pack()

var19 = Tkinter.IntVar()
var19x = Tkinter.Checkbutton(binary, text="Shape.",
    variable=var19, anchor='w', height=1, width=50)
var19x.pack()

#
# Ability to close GUI and print current state of variables using bottons.
#
button01 = Tkinter.Button(buttons, text='Continue', command=param_check)
button01.pack()
button02 = Tkinter.Button(buttons, text='Test', command=show_params)
button02.pack()

#
# Creates GUI box where widgets go.
#
Tkinter.mainloop()

#------------------------------------------------------------------------------#
#         Search for number of tiles and ask whether to continue               #
#------------------------------------------------------------------------------#

#
# Sentinel-2
#
if data_type[sensor_type.get()] == 1:

    procFolders = []

    for dirpath, dirnames, filenames in os.walk(s2_Folder.get(), topdown=True):

        for dirname in dirnames:

            if dirname == 'PROC_DATA':

                procFolders.append(os.path.join(dirpath, dirname))

    #
    # Hide the main window.
    #
    Tkinter.Tk().withdraw()

    question = ('Would you like to process {} tiles in SIAM?').format(
        str(len(procFolders)))

    #
    # Create the content of the window.
    #
    messagebox = tkMessageBox.askyesno('SIAM batch creator',
        question)


    #------------------------------------------------------------------------------#
    #                  Create batch file and launch SIAM or quit                   #
    #------------------------------------------------------------------------------#

    if messagebox:

        #
        # Register all of the GDAL drivers.
        #
        gdal.AllRegister()

        #
        # Create empty batch file for SIAM.
        #
        var06_text = var06.get()

        if len(procFolders) > 1:

            batFilename = 'SIAM_multiple_batch_{}.bat'.format(var06_text[:-5])

        else:

            batFilename = 'SIAM_batch_{}.bat'.format(var06_text[:-5])

        batch_path = os.path.join(s2_Folder.get(), batFilename)

        #
        # Convert binary variables and image type identifier from GUI to strings.
        #
        var00 = var00.get()
        var03 = str(var03.get())
        var06 = str(image_type[var06.get()])
        var07 = str(var07.get())
        var09 = str(var09.get())
        var10 = str(var10.get())
        var11 = str(var11.get())
        var12 = str(var12.get())
        var13 = str(var13.get())
        var14 = str(var14.get())
        var15 = str(var15.get())
        var16 = str(var16.get())
        var17 = str(var17.get())
        var18 = str(var18.get())
        var19 = str(var19.get())

        for procFolder in procFolders:

            var01 = procFolder

            #
            # Create the folder for SIAM output data if it doesn't exist.
            #
            siam_output = os.path.join(procFolder, 'siamoutput')

            if not(os.path.exists(siam_output)):

                os.mkdir(siam_output)

            var08 = siam_output

            #
            # Fill var02 variable with the calrefbyt filename.
            #
            for filename in os.listdir(procFolder):

                if (filename.endswith('.dat')
                        and fnmatch.fnmatch(filename, '*_calrefbyt_*')):

                    var02 = filename

            #
            # Go to next folder if calibrated, stacked raster not yet craeted.
            #
            if not var02:

                print '*_calrefbyt_* not found in {}'.format(procFolder)
                print 'Tile not processed.'

                continue

            #
            # Path to calrefbyt.
            #
            calrefbyt = os.path.join(procFolder, var02)

            #
            # Open image to calculate rows and columns.
            #
            img = gdal.Open(calrefbyt, gdal.GA_ReadOnly)

            if img is None:

                print '\nCould not open *calrefbyt*.dat'
                print 'Folder not processed: {}\n'.format(procFolder)

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

    else:

        print '\nNo SIAM batch file created.\n'

        sys.exit()

#
# Landsat-8
#
elif data_type[sensor_type.get()] == 2:

    #
    # Create list for landsat-8 folders folder paths.
    #
    landsat8Folders = []

    for dirpath, dirnames, filenames in os.walk(s2_Folder.get(), topdown=True):

        for dirname in dirnames:

            if dirname.startswith('LC08_L1TP_') and dirname.endswith('_T1'):

                landsat8Folders.append(os.path.join(dirpath, dirname))

    #
    # Hide the main window.
    #
    Tkinter.Tk().withdraw()

    question = ('Wold you like to process {} landsat8 images in SIAM?').format(
        len(landsat8Folders))

    #
    # Create the content of the window.
    #
    messagebox = tkMessageBox.askyesno('SIAM batch creator',
        question)


    #------------------------------------------------------------------------------#
    #                  Create batch file and launch SIAM or quit                   #
    #------------------------------------------------------------------------------#

    if messagebox:

        #
        # Register all of the GDAL drivers.
        #
        gdal.AllRegister()

        #
        # Create empty batch file for SIAM.
        #
        var06_text = var06.get()

        if len(procFolders) > 1:

            batFilename = 'SIAM_multiple_batch_{}.bat'.format(var06_text[:-5])

        else:

            batFilename = 'SIAM_batch_{}.bat'.format(var06_text[:-5])

        batch_path = os.path.join(s2_Folder.get(), batFilename)

        #
        # Convert binary variables and image type identifier from GUI to strings.
        #
        var00 = var00.get()
        var03 = str(var03.get())
        var06 = str(image_type[var06.get()])
        var07 = str(var07.get())
        var09 = str(var09.get())
        var10 = str(var10.get())
        var11 = str(var11.get())
        var12 = str(var12.get())
        var13 = str(var13.get())
        var14 = str(var14.get())
        var15 = str(var15.get())
        var16 = str(var16.get())
        var17 = str(var17.get())
        var18 = str(var18.get())
        var19 = str(var19.get())

        for landsat8Folder in landsat8Folders:

            var01 = landsat8Folder

            #
            # Create the folder for SIAM output data if it doesn't exist.
            #
            siam_output = os.path.join(landsat8Folder, 'siamoutput')

            if not(os.path.exists(siam_output)):

                os.mkdir(siam_output)

            var08 = siam_output

            #
            # Fill var02 variable with the calrefbyt filename.
            #
            for filename in os.listdir(landsat8Folder):

                if (filename.endswith('.dat')
                        and fnmatch.fnmatch(filename, '*_calrefbyt_*')):

                    var02 = filename

            #
            # Go to next folder if calibrated, stacked raster not yet craeted.
            #
            if not var02:

                print '*_calrefbyt_* not found in {}'.format(landsat8Folder)
                print 'Tile not processed.'

                continue

            #
            # Path to calrefbyt.
            #
            calrefbyt = os.path.join(landsat8Folder, var02)

            #
            # Open image to calculate rows and columns.
            #
            img = gdal.Open(calrefbyt, gdal.GA_ReadOnly)

            if img is None:

                print '\nCould not open *calrefbyt*.dat'
                print 'Folder not processed: {}\n'.format(landsat8Folder)

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

    else:

        print '\nNo SIAM batch file created.\n'

        sys.exit()

#
# Landsat-8 or Sentinel-2 clipped mosaic.
#
elif data_type[sensor_type.get()] == 3:

    #
    # Create list for landsat-8 or sentinel-2 clipped mosaic folder paths.
    #
    mosaicFiles = []

    for dirpath, dirnames, filenames in os.walk(s2_Folder.get(), topdown=True):

        for filename in filenames:

            if filename.endswith('_clip_mosaic_calrefbyt_lndstlk.dat'):

                mosaicFiles.append(os.path.join(dirpath, filename))

    print mosaicFiles

    #
    # Hide the main window.
    #
    Tkinter.Tk().withdraw()

    question = ('Wold you like to process {} mosaics in SIAM?').format(
        len(mosaicFiles))

    #
    # Create the content of the window.
    #
    messagebox = tkMessageBox.askyesno('SIAM batch creator',
        question)


    #------------------------------------------------------------------------------#
    #                  Create batch file and launch SIAM or quit                   #
    #------------------------------------------------------------------------------#

    if messagebox:

        #
        # Register all of the GDAL drivers.
        #
        gdal.AllRegister()

        #
        # Create empty batch file for SIAM.
        #
        var06_text = var06.get()

        if len(mosaicFiles) > 1:

            batFilename = 'SIAM_multiple_batch_{}.bat'.format(var06_text[:-5])

        else:

            batFilename = 'SIAM_batch_{}.bat'.format(var06_text[:-5])

        batch_path = os.path.join(s2_Folder.get(), batFilename)

        #
        # Convert binary variables and image type identifier from GUI to strings.
        #
        var00 = var00.get()
        var03 = str(var03.get())
        var06 = str(image_type[var06.get()])
        var07 = str(var07.get())
        var09 = str(var09.get())
        var10 = str(var10.get())
        var11 = str(var11.get())
        var12 = str(var12.get())
        var13 = str(var13.get())
        var14 = str(var14.get())
        var15 = str(var15.get())
        var16 = str(var16.get())
        var17 = str(var17.get())
        var18 = str(var18.get())
        var19 = str(var19.get())

        for mosaicFile in mosaicFiles:

            var01 = os.path.dirname(mosaicFile)

            #
            # Create the folder for SIAM output data if it doesn't exist.
            #
            siam_output = os.path.join(var01, 'siamoutput')

            if not(os.path.exists(siam_output)):

                os.mkdir(siam_output)

            var08 = siam_output

            #
            # Fill var02 variable with the calrefbyt filename.
            #
            var02 = os.path.basename(mosaicFile)

            #
            # Path to calrefbyt.
            #
            calrefbyt = mosaicFile

            #
            # Open image to calculate rows and columns.
            #
            img = gdal.Open(calrefbyt, gdal.GA_ReadOnly)

            if img is None:

                print '\nCould not open *calrefbyt*.dat'
                print 'Folder not processed: {}\n'.format(os.path.dirname(mosaicFile))

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

    else:

        print '\nNo SIAM batch file created.\n'

        sys.exit()
#------------------------------------------------------------------------------#
#                              Launch batch file.                              #
#------------------------------------------------------------------------------#

## May need to add threading to avoid GUI freezing upon launch.

# Excerpt from Tiede's ArcGIS Python Toolbox to launch SIAM

# myprocess = subprocess.Popen(batch_path)
# myprocess.wait()               # We wait for process to finish
# print myprocess.returncode     # then we get its returncode.


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
