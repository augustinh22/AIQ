#!/bin/bash

source ~/Datacube/datacube_env/bin/activate

cd /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/sentinel_2/

python prep_s2.py
python index_s2.py

cd /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/siam/

python prep_siam.py
python index_siam.py

datacube -v ingest -c /home/odci/Datacube/agdc-v2/ingest/ingestion_configs/siam/s2_siam_epsg32637_syria.yaml --executor multiproc 10

datacube -v ingest -c /home/odci/Datacube/agdc-v2/ingest/ingestion_configs/siam/s2_siam_epsg32637_syria_25km.yaml --executor multiproc 10
