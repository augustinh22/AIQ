#!/bin/bash

source ~/Datacube/datacube_env/bin/activate

cd /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/sentinel_2/
python prep_s2.py
python index_s2.py
