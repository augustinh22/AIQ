#!/bin/bash

source activate aiq27
cd /home/hannah/repos/AIQ/thesis/
python download_linux.py -t 37SBA --auto y -a ./key.txt -w /data/s2/37SBA
python download_linux.py -t 37SCA --auto y -a ./key.txt -w /data/s2/37SCA
python download_linux.py -t 37SDA --auto y -a ./key.txt -w /data/s2/37SDA

python conversion_linux.py --auto y -r /data/s2/37SBA
python conversion_linux.py --auto y -r /data/s2/37SCA
python conversion_linux.py --auto y -r /data/s2/37SDA
