## Setup Environment
```
wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh

sudo sh Miniconda2-latest-Linux-x86_64.sh -b -p /usr/local/miniconda

export PATH=/usr/local/miniconda/bin:$PATH

source ~/.bashrc

conda update conda

conda create --name aiq27 python=2.7 requests scipy gdal -c conda-forge
```

## Automate Queries
```
#!/bin/bash

source activate aiq27
cd /home/jirathana/repos/AIQ/thesis

python download_linux.py -w /home/shared/Morph/S-1/Re118_Asc -s S1 -s1pr SLC -s1mo IW -o 118 -od asc --unzip n --lat 64.05 --lon -16.94 --auto y -a ./key.txt

python download_linux.py -w /home/shared/Morph/S-1/Re111_Desc -s S1 -s1pr SLC -s1mo IW -o 111 -od desc --unzip n --lat 64.05 --lon -16.94 --auto y -a ./key.txt
```

```
crontab -e

0 2 * * * . $HOME/.bash_profile; /home/jirathana/repos/AIQ/other/automate_sentinel1.sh
