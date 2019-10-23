#!/bin/bash

source activate aiq27
cd /home/hannah/repos/AIQ/thesis/
python download_linux.py -t 37SBA --auto y -a ./key.txt -w /data/s2/37SBA
python download_linux.py -t 37SCA --auto y -a ./key.txt -w /data/s2/37SCA
python download_linux.py -t 37SDA --auto y -a ./key.txt -w /data/s2/37SDA
python download_linux.py -t 37SBU --auto y -a ./key.txt -w /data/s2/37SBU
python download_linux.py -t 37SBV --auto y -a ./key.txt -w /data/s2/37SBV

python conversion_linux.py --auto y -r /data/s2/37SBA
python conversion_linux.py --auto y -r /data/s2/37SCA
python conversion_linux.py --auto y -r /data/s2/37SDA
python conversion_linux.py --auto y -r /data/s2/37SBU
python conversion_linux.py --auto y -r /data/s2/37SBV

python batch_linux.py --auto y -r /data/s2/
cd /home/hannah/repos/AIQ/thesis/siam/
LATEST=$(find . -mmin -60 -type f)
if [ -z "$LATEST" ]
then
  echo "\$LATEST is empty."
else
  bash "$LATEST"
fi
