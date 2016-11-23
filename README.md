This project is under development for the capstone I3 Project course in
the University of Salzburg's M.Sc program in Applied Geoinformatics.  

## Configuration
* Set Python 2.7 to $PATH
 * system properties --> environment variables
 * Add path to the directory containing python to the Path variable
  * e.g. C:\Python27\ArcGIS10.4
 * Now you can run Python from the command line!
* Install aria2 downloading agent
 * Go to: https://aria2.github.io/
 * Download most recent version
 * Unzip and copy the contents into the folder containing python
 * Python can now access aria2!
* Install requests
 * Go to: http://docs.python-requests.org/en/master/
 * Follow installation instructions
* Download kml tiling grid
 * Go to: https://sentinel.esa.int/web/sentinel/missions/sentinel-2/data-products
 * Download kml file: S2A_OPER_GIP_TILPAR_MPC__20151209T095117_V20150622T000000_21000101T000000_B00.kml
 * Save in folder where iq_download.py is located
 
## Example queries:
###Point
* python iq_download.py --lat 47.083 --lon 12.842

### Polygon
* python iq_download.py --latmin 46 --latmax 48 --lonmin 12 --lonmax 14'

### Location
* python iq_download.py -l Vienna

### Tile
* python iq_download.py -t 33TUN

### Discover tiles
* python iq_download.py -l Salzburg -t ? -d 2016-11-10
