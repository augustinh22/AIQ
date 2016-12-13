import sys
import numpy
import gdal
import scipy.ndimage

# register all of the GDAL drivers
gdal.AllRegister()

# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

# open the image
img = gdal.Open("S2A_OPER_MSI_L1C_TL_MTI__20160406T160011_A004119_T48PXV_B11.jp2")
if img is None:
  print 'Could not open image file.'
  sys.exit(1)

# read in the data and get info about it
band1 = img.GetRasterBand(1)
rows = img.RasterYSize
cols = img.RasterXSize

print band1, rows, cols

myarray = numpy.array(img.GetRasterBand(1).ReadAsArray())
print "done"

## Resampling
print 'Resample by a factor of 2 with nearest interpolation:'
test = scipy.ndimage.zoom(myarray, 2, order=0)
print test.shape
test_rows = rows * 2
test_cols = cols * 2

# create the output image
driver = img.GetDriver()

#print driver
outDs = driver.Create("c:/Temp/test.jp2", test_cols, test_rows, 1, gdal.GDT_Int32)
if outDs is None:
    print 'Could not create test.jp2'
    sys.exit(1)

outBand =  outDs.GetRasterBand(1)
outData = numpy.zeros((test_rows,test_cols), numpy.int16)

# write the data
outBand.WriteArray(test, 0, 0)

# flush data to disk, set the NoData value and calculate stats
outBand.FlushCache()
outBand.SetNoDataValue(-99)

# georeference the image and set the projection
outDs.SetGeoTransform(img.GetGeoTransform())
outDs.SetProjection(img.GetProjection())

del outData

## https://gis.stackexchange.com/questions/32995/how-to-fully-load-a-raster-into-a-numpy-array
## https://gis.stackexchange.com/questions/37238/writing-numpy-array-to-raster-file


## Configuration
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
#
