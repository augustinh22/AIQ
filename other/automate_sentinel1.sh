#!/bin/bash

source activate aiq27
cd /home/jirathana/repos/AIQ/thesis

python download_linux.py -w /home/shared/Morph/S-1/Re118_Asc -s S1 -s1pr SLC -s1mo IW -o 118 -od asc --unzip n --lat 64.05 --lon -16.94 --auto y -a ./key.txt

python download_linux.py -w /home/shared/Morph/S-1/Re111_Desc -s S1 -s1pr SLC -s1mo IW -o 111 -od desc --unzip n --lat 64.05 --lon -16.94 --auto y -a ./key.txt
