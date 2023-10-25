#!/bin/bash

source activate aiq27
cd /home/hannah/repos/AIQ/thesis/
python download_linux.py -t 42SWD --auto y -a ./key.txt -w /data/afghanistan_agriculture/products/images/sentinel-2/granules/42SWD
