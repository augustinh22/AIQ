#by Dirk Tiede (modified for Python 3 in ArcGIS Pro by H.Augustin)
#Version Date 2015-10-14
    ##; FROM Andrea Baraldi:
    ##        OBJECTIVE: Radiometric calibration of Sentinel-2A/2B imagery into
    ##;          (i)  TOP-OF-ATMOSPHERE (TOA, PLANETARY, EXOATMOSPHERIC) reflectance (in range [0,1]),
    ##;               byte-coded, i.e., scaled into range {1, 255},
    ##;               output ENVI file format: ...calrefbyt_lndstlk, band sequential (BSQ).
    ##;               Equivalent to Landsat bands 1, 2, 3, 4, 5 and 7 are
    ##;               the Sentinel-2A/2B bands    2, 3, 4, 8, 11 and 12
    ##;               with spatial resolutions   10, 10, 10, 10, 20, 20.
    ##;          (ii) faked temperature in kelvin degrees, equivalent to 10 degree Celsius,
    ##;               output value = 110, output ENVI file format: ...caltembyt_lndstlk.
    ##;
    ##;          where:
    ##;
    ##;             - Sentinel-2A/2B bands are:
    ##;
    ##;              1, Aerosols (nm): 443?20/2,        Spatial resolution (in m): 60
    ##;              2: Vis B (like TM1), 490?65/2,     Spatial resolution (in m): 10
    ##;              3: Vis G (like TM2), 560?35/2,     Spatial resolution (in m): 10
    ##;              4: Vis R (like TM3), 665?30/2,     Spatial resolution (in m): 10
    ##;              5: NIR1 (Red Edge1), 705?15/2,     Spatial resolution (in m): 20
    ##;              6: NIR2 (Red Edge2), 740?15/2,     Spatial resolution (in m): 20
    ##;              7: NIR3 (Red Edge3),783?20/2,      Spatial resolution (in m): 20
    ##;              8: NIR4 (like TM4), 842?115/2,     Spatial resolution (in m): 10
    ##;              8a: NIR5, 865?20/2,                Spatial resolution (in m): 20
    ##;              9, Water vapour: 945?20/2,         Spatial resolution (in m): 60
    ##;              10, Cirrus: 1375?30/2,             Spatial resolution (in m): 60
    ##;              11: MIR1 (like TM5) 1610?90/2,     Spatial resolution (in m): 20
    ##;              12: MIR2 (like TM7) 2190?180/2     Spatial resolution (in m): 20
    ##;
    ##;              Hence, equivalent to Landsat bands 1, 2, 3, 4, 5 and 7 are
    ##;              the Sentinel-2A/2B bands           2, 3, 4, 8, 11 and 12
    ##;              with spatial resolutions          10, 10, 10, 10, 20, 20.

import sys, os, math, time
import arcpy
from arcpy import env
from arcpy.sa import *

arcpy.CheckOutExtension("spatial")

### constants for thermal thresholds
##MAXTEMP_KELVIN_THRESHOLD = 428.       #in Celsius: Max kelvin 428. - 273.14 = Max Celsius = 154.86
##MINTEMP_KELVIN_THRESHOLD = 173.       #in Celsius: Min Kelvin 173. - 273.14 = Min Celsius = -100.14



#Parameters
inputMain = arcpy.GetParameterAsText(0)
if inputMain == '':
    inputMain = r"D:\temp_S2A"
outMain = arcpy.GetParameterAsText(1)
##if outMain == '':
##    outMain = "input"
arcpy.env.overwriteOutput = True
arcpy.AddMessage (inputMain)
# Get and print a list of dat from the workspace

imgFolders = []
walk = arcpy.da.Walk(inputMain, topdown=True,)
for dirpath, dirnames, filenames in walk:
    #print dirpath, dirnames
    for dirname in dirnames:
        if dirname == "IMG_DATA":
            imgFolders.append(os.path.join(dirpath, dirname))

    ##if dirs == "IMG_DATA":
##        if os.path.isdir(os.path.join(inputMain, name)):
##            directory = os.path.join(inputMain, name)
##            imgFolders.append(directory)
print(imgFolders)
for imgFolder in imgFolders:
    arcpy.env.workspace = imgFolder
    rasters = []
    reflectList = []
    walk = arcpy.da.Walk(imgFolder, datatype="RasterDataset", type=['JP2'])
    for dirpath, dirnames, filenames in walk:
        for filename in filenames:
                    rasters.append(os.path.join(dirpath, filename))
    if outMain == '':
        outFolder_new = imgFolder [:-8] + "PROC_DATA"
        if not arcpy.Exists(outFolder_new):
            arcpy.CreateFolder_management(imgFolder[:-8], "PROC_DATA")


    rasters.sort
    print(rasters)
    for rast in rasters:
        if rast.endswith(("_B02.jp2","_B03.jp2","_B04.jp2","_B08.jp2")):
            print(rast)
            #outname = rast[:-4] + ".dat"
            if outMain == '':
                outname = outFolder_new + "\\" + os.path.basename(rast)[:-4] + ".dat"
                #outname = rast[:-4] + ".dat"
            else:
                outname = outMain + "\\" + os.path.basename(rast)[:-4] + ".dat"
            outraster = Raster(rast)
            outraster = outraster / 10000.0
            #outraster.save("c:\\temp\\test.tif")
            outraster = Con((outraster >=0) & (outraster<=1), outraster, Con(outraster < 0,0, Con((outraster > 1), 1)))
            outraster = Int((Abs(outraster)*255.0)+0.5)
            arcpy.CopyRaster_management (outraster, outname, "", "", "", "", "", "8_BIT_UNSIGNED")
            reflectList.append(outname)
        if rast.endswith(("_B11.jp2","_B12.jp2")):
            print(rast)
            #outname = rast[:-4] + ".dat"
            if outMain == '':
                outname = outFolder_new + "\\" + os.path.basename(rast)[:-4] + ".dat"
                #outname = rast[:-4] + ".dat"
            else:
                outname = outMain + "\\" + os.path.basename(rast)[:-4] + ".dat"
            outraster = Raster(rast)
            outraster = outraster / 10000.0
            #outraster.save("c:\\temp\\test.tif")
            outraster = Con((outraster >=0) & (outraster<=1), outraster, Con(outraster < 0,0, Con((outraster > 1), 1)))
            arcpy.Resample_management(outraster, "temprast", "10", "NEAREST")
            outraster = Int((Abs("temprast")*255.0)+0.5)
            arcpy.CopyRaster_management (outraster, outname, "", "", "", "", "", "8_BIT_UNSIGNED")
            reflectList.append(outname)
        print(reflectList)
        reflectList.sort()
        print(reflectList)
        arcpy.AddMessage(reflectList)
        arcpy.Delete_management("temprast")
    if len(reflectList)>1:
        arcpy.AddMessage (reflectList)
        outname_calref = outname[:-7] + "calrefbyt_lndstlk.dat"
        instring = ';'.join(reflectList)
        print(instring)
        arcpy.CompositeBands_management (instring, outname_calref)
        outConstRaster = CreateConstantRaster("110", "INTEGER", "10", arcpy.Describe(outname_calref).Extent)
        sr = arcpy.Describe(outname_calref).spatialReference
        arcpy.DefineProjection_management(outConstRaster, sr)
        outtemp = outname[:-7] + "caltembyt_lndstlk.dat"
        arcpy.CopyRaster_management (outConstRaster, outtemp, "", "", "", "", "", "8_BIT_UNSIGNED")
        for rast in reflectList:
            arcpy.Delete_management(rast)
        arcpy.AddMessage ("xxxxxxxx calculated xxxxxxxx: " + outname)
        arcpy.AddMessage ("xxxxxxxx calculated xxxxxxxx: " + outtemp)
