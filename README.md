This project is under development for the capstone I3 Project course in
the University of Salzburg's M.Sc program in Applied Geoinformatics.  

## Configuration (for Windows 64-bit and Python 2.7)
1. If not already installed, install Python 2.7.x
 * Download necessary .msi from https://www.python.org/downloads/
     * _Note: 32-bit is default. You have to explicitly download 64-bit._
 * Run windows installer (.msi)
2. Set Python 2.7 installed location to $PATH if not automatically set by installer.
 * system properties --> environment variables
 * Add path to the directory containing Python to the Path variable
    * e.g. C:\Python27
 * Add path to the scripts directory within the installed directory as well.
    * e.g. C:\Python27\Scripts
 * Now you ought to be able to run Python from the command line!
    * check this by opening PowerShell and typing 'python'
 * _Note: Adding the Python system variables to the beginning of the list is recommended._
3. Install aria2 downloading agent.
 * Go to: https://aria2.github.io/
 * Download most recent 64-bit version
    * e.g. aria2-1.30.0-win-64bit-build1.zip
 * Unzip and move the contents directly into the folder containing Python.
 * Python can now access aria2!
4. Install Python package "requests"
 * Go to: http://docs.python-requests.org/en/master/
 * Follow installation instructions.
    * e.g. as easy as "pip install requests" unless you have pip problems
5. Download kml tiling grid
 * Go to: https://sentinel.esa.int/web/sentinel/missions/sentinel-2/data-products
 * Download kml file: <pre>S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000_21000101T000000_B00.kml</pre>
 * Save in folder where __iq_download.py__ is located.
6. Download and install MSVC 2008 (for Python 2.7.x) and Service Pack 1
 * Go to http://www.lfd.uci.edu/~gohlke/pythonlibs/
 * Follow the two links in the Introduction. Install MSVC 2008 first, then SP1 (64-bit)
 * _Note: These installations will require you to restart your computer._
7. Download and install Numpy + MKL and SciPy Python unofficial Windows binaries for Python 2.7
 * http://www.lfd.uci.edu/~gohlke/pythonlibs/
 * Download the Numpy+MKL and SciPy wheels for Python 2.7 (64-bit)
    * e.g. numpy‑1.12.0rc1+mkl‑cp27‑cp27m‑win_amd64.whl
    * e.g. scipy‑0.18.1‑cp27‑cp27m‑win_amd64.whl
 * Navigate to their download location in Powershell and type "pip install _filename_.whl"
 * _Note: Install the Numpy+MKL wheel first since SciPy and GDAL depend on it._
8. Download and install GDAL for Windows
 * Go to: http://www.gisinternals.com/release.php
 * Python 2.7 uses 1500 which is MSVC 2008 -- find the correct GDAL core installer
    * e.g. gdal-201-1500-x64-core.msi
 * Install using the installer
 * Set system path environment variable to include GDAL folder
    * e.g. C:\Program Files\GDAL
 * Set system environment variable GDAL_DATA to the gdal-data folder in GDAL
    * e.g. C:\Program Files\GDAL\gdal-data
 * Set system environment variable GDAL_DRIVER_PATH to gdalplugins folder
    * e.g. C:\Program Files\GDAL\gdalplugins
9. Download GDAL Python bindings for Windows
 * Go to: http://www.gisinternals.com/release.php
 * Python 2.7 uses 1500 which is MSVC 2008 -- find the correct Python binding installer
    * e.g. GDAL-2.1.2.win-amd64-py2.7.msi
 * Make sure that it binds to the correct installation of Python
    * i.e. explicitly identify python folder, e.g. C:\Python27
 * Unfortunately this download is currently missing the array function. Copy the
   missing files from another unofficial windows binary .whl found at the following
   website into the GDAL folder in Python if they are missing:
    * Go to: http://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal
        - Download appropriate .whl file (e.g. GDAL-2.1.2-cp27-cp27m-win_amd64.whl)
        - Unzip using something like 7zip
        - specifically go to: GDAL-2.1.2-cp27-cp27m-win_amd64.whl\osgeo\
        - make sure all .pyd files in that directory are included in the
          original python bindings installed using the gisinternals installer.
          If not, copy paste into e.g. C:\Python27\Lib\site-packages\osgeo
          The _gdal_array.pyd_ file is the most important.
          Why not just install this wheel? Because it is suppposed to install
          its own core version of GDAL, but it didn't work as far as I could tell,
          and is not compatible with the GDAL core downloaded from gisinternals
          that can also be used from the commmand line instead of just in python.

# iq_download.py
## Example queries
### Point
* python iq_download.py --lat 47.083 --lon 12.842

### Polygon
* python iq_download.py --latmin 46 --latmax 48 --lonmin 12 --lonmax 14

### Location
* python iq_download.py -l Vienna

### Tile
* python iq_download.py -t 33TUN

### Discover tiles
* python iq_download.py -l Salzburg -t ? -d 2016-11-10
   * This query returns all results identified as including 'Salzburg' as well as 
     lists all of the tiles located within the package. Not so relevant now for 
     single tile packages.

# conversion.py
* This script runs without any parameters, converting the bands in IMG_DATA folders
  located in the directory structure of C:\tempS2 and saving the results
  in a new folder called PROC_DATA.
  It uses GDAL, Numpy and SciPy to convert bands to 8-bit, resample the 20m resolution
  bands to 10m resolution, modify outliers (e.g. clouds) and create a 6 band
  stack out of these pre-processed bands.
  It also creates a fake thermal layer (110 constant) for use in SIAM.

# restructure.py
* This script copies all of the tile specific folders from the main directory
  structure (i.e. folders inside the GRANULE folder) and pastes them in the
  defined root (e.g. C:\tempS2). After moving, it deletes the original structure.
  This is necessary due to long file names, even with the data published
  after 06.12.16, and since data outside the GRANULE folders is not used.

# batch.py
* This script runs without any parameters, but requires user input using a GUI.
  It automatically creates a SIAM output folder within PROC_DATA and a batch script
  to process all .dat files created in __conversion.py__ or otherwise located within
  a PROC_DATA folder within the defined root directory (in this case, C:\tempS2).
  Launching the batchfile automatically after creation will be added at a later date.
  
![Batch GUI](/images/batch_tk.jpg?raw=true "Batch GUI")
