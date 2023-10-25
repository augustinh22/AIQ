#!/bin/bash

source activate aiq27
cd /home/hannah/repos/AIQ/thesis/
python download_linux.py -t 37SBA --auto y -a ./key.txt -w /data/seodc/products/images/sentinel-2/granules/37SBA
python download_linux.py -t 37SCA --auto y -a ./key.txt -w /data/seodc/products/images/sentinel-2/granules/37SCA
python download_linux.py -t 37SDA --auto y -a ./key.txt -w /data/seodc/products/images/sentinel-2/granules/37SDA
python download_linux.py -t 37SBU --auto y -a ./key.txt -w /data/seodc/products/images/sentinel-2/granules/37SBU
python download_linux.py -t 37SBV --auto y -a ./key.txt -w /data/seodc/products/images/sentinel-2/granules/37SBV
