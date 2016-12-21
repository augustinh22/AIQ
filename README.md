This project is under development for the capstone I3 Project course in
the University of Salzburg's M.Sc program in Applied Geoinformatics.  

## Configuration
* If not already installed, install Python 2.7.x
 * Check if you require 32 or 64 bit.
 * Download necessary .msi from https://www.python.org/downloads/
 * Run windows installer (.msi)
* Set Python 2.7 installed location to $PATH if not automatically set by installer.
 * system properties --> environment variables
 * Add path to the directory containing Python to the Path variable
  * e.g. C:\Python27
 * Add path to the scripts directory within the installed directory as well.
  * e.g. C:\Python27\Scripts
 * Now you ought to be able to run Python from the command line!
 * [Note: Adding the Python system variables to the beginning of the list is recommended.]
* Install aria2 downloading agent.
 * Go to: https://aria2.github.io/
 * Download most recent version of either 32 or 64 bit
 * Unzip and move the contents directly into the folder containing Python.
 * Python can now access aria2!
* Install Python package "requests".
 * Go to: http://docs.python-requests.org/en/master/
 * Follow installation instructions.
  * e.g. as easy as "pip install requests" unless you have pip problems.
* Download kml tiling grid.
 * Go to: https://sentinel.esa.int/web/sentinel/missions/sentinel-2/data-products
 * Download kml file: S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000_21000101T000000_B00.kml
 * Save in folder where iq_download.py is located.

## Example queries:
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
