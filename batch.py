#-------------------------------------------------------------------------------
# Name:        SIAM batch creator
# Purpose:     This script uses Tkinter to create a GUI for creating one SIAM
#              batch file.
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
import tkMessageBox

import gdal

def show_params():
    if var06.get() == 'Select one.':
        print '\nPlease pick an image type!\n'
    else:
        print('\nImage type: {} ({})'.format(
            var06.get(), image_type[var06.get()]))
        print 'SIAM path: {}'.format(var00.get())
        print 'S2 path: {}'.format(s2_Folder.get())
        print 'Processing with a binary mask: {}'.format(var03.get())
        print 'Fuzzy classification: {}'.format(var07.get())
        print 'Smoke-plume mask: {}'.format(var09.get())
        print 'Cloud mask: {}'.format(var10.get())
        print 'Burnt area mask: {}'.format(var11.get())
        print 'Vegetation binary mask: {}'.format(var12.get())
        print 'Vegetation trinary mask: {}'.format(var13.get())
        print 'Baresoil built-up trinary mask: {}'.format(var14.get())
        print 'Cloud trinary mask: {}'.format(var15.get())
        print 'Water trinary mask: {}'.format(var16.get())
        print 'Shadow trinary mask: {}'.format(var17.get())
        print 'Urban area binary mask: {}'.format(var18.get())


#------------------------------------------------------------------------------#
#                                     GUI                                      #
#------------------------------------------------------------------------------#

# Create GUI interface frames.
master = Tkinter.Tk()
title = Tkinter.Frame(master)
title.pack(side='top')
siam_input = Tkinter.Frame(master)
siam_input.pack()
s2_input = Tkinter.Frame(master)
s2_input.pack()
img_options = Tkinter.Frame(master)
img_options.pack()
binary = Tkinter.Frame(master)
binary.pack()
buttons = Tkinter.Frame(master)
buttons.pack(side='bottom')

# Title.
label01 = Tkinter.Label(title, text="SIAM Batch Creator")
label01.config(width=30, font=("Courier", 44))
label01.pack(pady=15)

# Define SIAM .exe location text entry box.
label02 = Tkinter.Label(siam_input, text="Insert SIAM .exe path: ")
label02.pack(pady=15, side='left')

var00 = Tkinter.StringVar()
var00.set(
    r'E:\SIAM\installation\SIAM_License_Executables\SIAM_r88v6_Windows.exe')
var00x = Tkinter.Entry(siam_input, textvariable=var00, justify='left')
var00x.config(width=40)
var00x.pack(pady=15, side='right')

# Define S2 root folder text entry box.
label03 = Tkinter.Label(s2_input, text='Path to folder where Sentinel 2 data '
    'are saved: ')
label03.pack(pady=15, side='left')

s2_Folder = Tkinter.StringVar()
s2_Folder.set(r'C:\tempS2')
s2_Folderx = Tkinter.Entry(s2_input, textvariable=s2_Folder, justify='left')
s2_Folderx.config(width=40)
s2_Folderx.pack(pady=15, side='right')

# Create image-type dropdown menu.
label04 = Tkinter.Label(img_options, text="Select an image type: ")
label04.pack(side='left')

var06 = Tkinter.StringVar()
image_type = {"LANDSAT_LIKE": 1, "SPOT_LIKE": 2, "AVHRR_LIKE": 3, "VHR_LIKE": 4}
var06.set('Select one.')
var06x = Tkinter.OptionMenu(img_options, var06, *image_type.keys())
var06x.config(width=15)
var06x.pack(pady=10, side='right')
# image_type[var06.get()] returns the key value

# Create checkboxes for all binary variables.
var03 = Tkinter.IntVar()
var03x = Tkinter.Checkbutton(binary, text="Use a binary mask for processing",
    variable=var03, justify='left', height=1, width=60)
var03x.pack()

var07 = Tkinter.IntVar()
var07x = Tkinter.Checkbutton(binary,
    text="Use fuzzy classification instead of crisp",
    variable=var07, justify='left', height=1, width=60)
var07x.pack()

var09 = Tkinter.IntVar()
var09x = Tkinter.Checkbutton(binary, text="Smoke-Plume mask",
    variable=var09, justify='left', height=1, width=60)
var09x.pack()

var10 = Tkinter.IntVar()
var10x = Tkinter.Checkbutton(binary, text="Cloud mask",
    variable=var10, justify='left', height=1, width=60)
var10x.pack()

var11 = Tkinter.IntVar()
var11x = Tkinter.Checkbutton(binary, text="Burnt area mask",
    variable=var11, justify='left', height=1, width=60)
var11x.pack()

var12 = Tkinter.IntVar()
var12x = Tkinter.Checkbutton(binary, text="Vegetation Binary mask",
    variable=var12, justify='left', height=1, width=60)
var12x.pack()

var13 = Tkinter.IntVar()
var13x = Tkinter.Checkbutton(binary, text="Vegetation Trinary mask",
    variable=var13, justify='left', height=1, width=60)
var13x.pack()

var14 = Tkinter.IntVar()
var14x = Tkinter.Checkbutton(binary, text="Baresoil Builtup Trinary mask",
    variable=var14, justify='left', height=1, width=60)
var14x.pack()

var15 = Tkinter.IntVar()
var15x = Tkinter.Checkbutton(binary, text="Cloud Trinary mask",
    variable=var15, justify='left', height=1, width=60)
var15x.pack()

var16 = Tkinter.IntVar()
var16x = Tkinter.Checkbutton(binary, text="Water Trinary mask",
    variable=var16, justify='left', height=1, width=60)
var16x.pack()

var17 = Tkinter.IntVar()
var17x = Tkinter.Checkbutton(binary, text="Shadow trinary mask",
    variable=var17, justify='left', height=1, width=60)
var17x.pack()

var18 = Tkinter.IntVar()
var18x = Tkinter.Checkbutton(binary, text="Urban area binary mask",
    variable=var18, justify='left', height=1, width=60)
var18x.pack()

# Ability to close GUI and print current state of variables using bottons.
button01 = Tkinter.Button(buttons, text='Continue', command=master.quit)
button01.pack()
button02 = Tkinter.Button(buttons, text='Show', command=show_params)
button02.pack()

# Not sure what this does.
Tkinter.mainloop()

#------------------------------------------------------------------------------#
#         Search for number of tiles and ask whether to continue               #
#------------------------------------------------------------------------------#

procFolders = []

for dirpath, dirnames, filenames in os.walk(s2_Folder.get(), topdown=True):
    for dirname in dirnames:
        if dirname == 'PROC_DATA':
            procFolders.append(os.path.join(dirpath, dirname))

# Hide the main window.
Tkinter.Tk().withdraw()

question = ('Would you like to create a batch file\n to process {} tiles'
    ' in SIAM?').format(str(len(procFolders)))
# Create the content of the window.
messagebox = tkMessageBox.askyesno('SIAM batch creator',
    question)


#------------------------------------------------------------------------------#
#                         Create batch file or quit                            #
#------------------------------------------------------------------------------#

if messagebox:

    # register all of the GDAL drivers
    gdal.AllRegister()

    ## Batch file, might need to be saved in PROC_DATA -- here is just the name
    var06_text = var06.get()
    batFilename = 'SIAM_multiple_batch_{}.bat'.format(var06_text[:-5])
    print '\n\n'
    print batFilename
    batch_path = os.path.join(s2_Folder.get(), batFilename)
    print batch_path

    # Convert binary variables and image type identifier from GUI to strings.
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

    for procFolder in procFolders:

        var01 = procFolder

        # Create the folder for siam data if it doesn't exist.
        siam_output = os.path.join(procFolder, 'siamoutput')
        if not(os.path.exists(siam_output)):
            os.mkdir(siam_output)
        var08 = siam_output

        # Fill var02 variable with the calrefbyt filename.
        for filename in os.listdir(procFolder):
            if (filename.endswith('.dat')
                    and fnmatch.fnmatch(filename, '*_calrefbyt_*')):
                var02 = filename

        # Go to next folder if calibrated, stacked raster not yet craeted.
        if not var02:
            print '*_calrefbyt_* not found in {}'.format(procFolder)
            print 'Tile not processed.'
            continue

        # Path to calrefbyt.
        calrefbyt = os.path.join(procFolder, var02)

        # Open image to calculate rows and columns.
        img = gdal.Open(calrefbyt, gdal.GA_ReadOnly)
        if img is None:
            print '\nCould not open *calrefbyt*.dat'
            print 'Folder: {}\n'.format(procFolder)
            continue
        # Rows.
        var04 = str(img.RasterYSize)
        # Columns.
        var05 = str(img.RasterXSize)

        # Create string to write to batch file.
        batch_entry = ' '.join((var00, var01, var02, var03, var04, var05,
            var06, var07, var08, var09, var10, var11, var12, var13, var14,
            var15, var16, var17, var18))
        with open(batch_path, 'a') as f:
            f.write(batch_entry + '\n')
        # print batch_entry

        # Clean up.
        img = None
else:
    print '\nNo SIAM batch file created.\n'
    sys.exit()

#------------------------------------------------------------------------------#
#                             Launch batch file                                #
#------------------------------------------------------------------------------#


# Excerpt from Tiede's ArcGIS Python Toolbox to launch SIAM
# myprocess = subprocess.Popen(batFilename)
#
# myprocess.wait()               # We wait for process to finish
# print myprocess.returncode     # then we get its returncode.


#------------------------------------------------------------------------------#
#                Parameters from Example batch file explained.                 #
#------------------------------------------------------------------------------#

# (0) E:\SIAM\installation\SIAM_License_Executables\SIAM_r88v6_Windows.exe   [SIAM executable]
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
