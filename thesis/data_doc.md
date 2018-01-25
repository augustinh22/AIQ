#
#
#
---
### 1. Select tiles for download using Sentinel-2 Dashboard

#### _Border of Syria and Turkey_
##### 37SBA
```bash
python download_linux.py -t 37SBA -d 2015-05-01 -f 2016-05-01 -w /home/hannah/data/37SBA
```
  - [run on 29.11.2017 at 18:24]

```bash
python download_linux.py -t 37SBA -d 2016-05-01 -f 2017-05-01 -w /home/hannah/data/37SBA
```
  - [run on 30.11.2017 at 10:35]
  - Stopped at about 11:00 due to full partition
  
```bash
python download_linux.py -t 37SBA -d 2016-05-01 -f 2017-05-01 -w /data/s2/37SBA
```
  - [run on 30.11.2017 at 13:05]

```bash
python download_linux.py -t 37SBA -d 2017-05-01 -w /data/s2/37SBA
```
  - [run on 30.11.2017 at 13:22]
  - [run again on 30.11.207 at 14:58 due to a bunch of 500 errors]
  - [run again on 30.11.207 at 15:39 due to a bunch of 500 errors]
  - [run on 30.11.2017 at 12:30 to get most recent image (02.12)]

```bash
python download_linux.py -t 37SBA -d 2016-04-01 -f 2017-06-01 -w /data/s2/37SBA
```
  - [run on 30.11.207 at 16:16]
  - delete S2A_OPER_PRD_MSIL1C_PDMC_20160925T053337_R121_V20160923T082002_20160923T082003.SAFE due to empty metadata file encountered during Conversion

```bash
python download_linux.py -t 37SBA -d 2016-09-20 -f 2016-09-30 -w /data/s2/37SBA
```

   - [run on 05.12.207 at 17:09]

##### 37SCA
```bash
 - python download_linux.py -t 37SCA -d 2015-05-01 -f 2016-12-07 -w /data/s2/37SCA
  - [run on 30.11.2017 at 19:55]
 - python download_linux.py -t 37SCA -d 2016-12-06 -f 2017-11-03 -w /data/s2/37SCA
  - [run on 01.12.2017 at 9:13]
 - python download_linux.py -t 37SCA -d 2017-11-02 -w /data/s2/37SCA
  -  [run on 04.12.2017 at 12:01]
```

##### 37SDA
```bash
python download_linux.py -t 37SDA -d 2015-05-01 -f 2017-08-16 -w /data/s2/37SDA
```
 -  [run on 01.12.2017 at 13:49 -- ~2:15 on 02.12.2017 for 97 scenes)]

```bash
python download_linux.py -t 37SDA -d 2017-08-15  -w /data/s2/37SDA
```
 -  [run on 04.12.2017 at 12:33 -- 13:31, 21 scenes]

##### Additional Possibilities
###### _Border of Syria and Turkey_
37SEA

###### _South of the Syrian-Turkish border_
37SBV, 37SCV, 37SDV, 37SEV

###### _Turkey north of Syria_
37SBB, 37SCB, 37SDB, 37SEB

### 2. Convert tiles.
05.12.2017
  - average of less than 45s per tile for 433 tiles (total: 5.4h)
  - only logged 228 tiles at 2h39m, so average of 41.65seconds per tile
  - based on this average, it took 5.01h for 433 tiles

19.12.2017
  - all files deleted, adjusted for pixels with a value of 0.
  - 443 tiles, started at 14:04, estimated around 1 minute per tile due to nodata adjustment. in 8:09 hours for 443 tiles,. -- 8:09 hours for all 443 tiles.

08.01.2018
  - create nodata masks for each tile (460) retroactively.
  - start 17:30, end 20:44 -- time 3.25hours.

### 3. Initial SIAM processing
##### 37SBA
 started 13:30 on 06.12.2017 (121 tiles) -- finished 00:38 on 07.12.2017

##### 37SCA
13:51 on 06.12.2017 (193 tiles)
  - cancelled before first finish due to server load
Manually deleted siamoutput folder

started again at 14:48 on 06.12.2017 (193 tiles)
  - finished 08:19 on 07.12.2017

##### 37SDA
started 14:32 on 06.12.2017 (119 tiles)
  - finished 01:11 on 07.12.2017

##### Reprocessed with nodata masks
started between 10:36 and 10:48 on 09.01.18 in 12 batches for 462 tiles
  - finished at 14:56 with uneven batch sizes.

### 4. Create Cronjob to automate processes to keep up-to-date.
```bash
crontab -e
```

- insert following:

```bash
0 2 * * * . $HOME/.bash_profile; /home/hannah/repos/AIQ/thesis/automate_downloads.sh
```

Contents of Script:

```
#!/bin/bash

source activate aiq27
cd /home/hannah/repos/AIQ/thesis/
python download_linux.py -t 37SBA --auto y -a ./key.txt -w /data/s2/37SBA/
python download_linux.py -t 37SCA --auto y -a ./key.txt -w /data/s2/37SCA/
python download_linux.py -t 37SDA --auto y -a ./key.txt -w /data/s2/37SDA/

python conversion_linux.py --auto y -r /data/s2/37SBA/
python conversion_linux.py --auto y -r /data/s2/37SCA/
python conversion_linux.py --auto y -r /data/s2/37SDA/

python batch_linux.py --auto y -r /data/s2/
cd /home/hannah/repos/AIQ/thesis/siam/
LATEST=$(find . -mmin -60 -type f)
if [ -z "$LATEST" ]
then
  echo "\$LATEST is empty."
else
  bash "$LATEST"
fi
```

### 5. Index Sentinel-2 Datata
2017-12-21 Indexed all original data -- less than 5 minutes to create the yaml docs and 10 minutes to index all ~450 scenes.

```bash
(datacube_env) [odci@cf000508 dataset_types]$ datacube -v product add /home/odci/Datacube/agdc-v2/ingest/dataset_types/sentinel_2/s2_granules.yaml
```
#### Deal with re-indexed scenes...
```bash
sudo su - postgres

psql
\c datacube
\dt agdc.*
```

```sql
DELETE FROM agdc.dataset_location
    WHERE added IN
        (SELECT A.added
        FROM agdc.dataset_location A
        WHERE EXISTS (SELECT B.uri_body, count(*) FROM agdc.dataset_location B GROUP BY B.uri_body HAVING count(*) > 1 AND A.uri_body = B.uri_body) AND A.added < '2018-01-15 13:15:00.000');

DELETE FROM agdc.dataset
    WHERE id NOT IN
        (SELECT dataset_ref FROM agdc.dataset_location);
```

### 6. Automate indexing S2 Data
#### Create Crontab for admin to change permissions on all files in /data/s2/
```bash
40 2 * * * sudo chown -R hannah:aiq /data/s2/
55 2 * * * sudo chown -R hannah:aiq /data/s2/
```
#### Create crontab for automating all indexing operations (to be expanded with ingestion)
```bash
42 2 * * * . $HOME/.bash_profile; /data/s2/automate_ODC.sh
```
- Be sure permissions are correct if editing: sudo chmod 755 automate_ODC.sh

```bash
#!/bin/bash

source ~/Datacube/datacube_env/bin/activate

cd /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/sentinel_2/
python prep_s2.py
python index_s2.py
```

### Index SIAM dataset
#### Add product definition

#### Index
```
(datacube_env) [odci@cf000508 siam]$ datacube -v dataset add /data/s2/37SBA/S2A_OPER_PRD_MSIL1C_PDMC_20161007T104254_R121_V20150830T082006_20150830T082754.SAFE/GRANULE/S2A_OPER_MSI_L1C_TL_EPA__20161006T204405_A000976_T37SBA_N02.04/PROC_DATA/siam-metadata.yaml
2018-01-17 15:16:16,295 8532 datacube INFO Running datacube command: /home/odci/Datacube/datacube_env/bin/datacube -v dataset add /data/s2/37SBA/S2A_OPER_PRD_MSIL1C_PDMC_20161007T104254_R121_V20150830T082006_20150830T082754.SAFE/GRANULE/S2A_OPER_MSI_L1C_TL_EPA__20161006T204405_A000976_T37SBA_N02.04/PROC_DATA/siam-metadata.yaml
Indexing datasets  [####################################]  100%2018-01-17 15:16:16,363 8532 datacube-dataset INFO Matched Dataset <id=bf0c6842-1bf5-4c63-86cc-84eb1d690d6b type=siam_il2 location=/data/s2/37SBA/S2A_OPER_PRD_MSIL1C_PDMC_20161007T104254_R121_V20150830T082006_20150830T082754.SAFE/GRANULE/S2A_OPER_MSI_L1C_TL_EPA__20161006T204405_A000976_T37SBA_N02.04/PROC_DATA/siam-metadata.yaml>
2018-01-17 15:16:16,364 8532 datacube.index._datasets INFO Indexing c4e3a133-dc6f-429e-be76-fa4f5c591741
2018-01-17 15:16:16,374 8532 datacube.index._datasets WARNING Duplicate dataset, not inserting: c4e3a133-dc6f-429e-be76-fa4f5c591741
2018-01-17 15:16:16,386 8532 datacube.index._datasets INFO Indexing bf0c6842-1bf5-4c63-86cc-84eb1d690d6b
```
__
#### Ingest
be sure to set "fuse_data: copy" acccording to https://github.com/opendatacube/datacube-core/issues/147

select as subquery:
```sql
SELECT count(*) FROM (SELECT added FROM agdc.dataset_location WHERE added > '2018-01-17 16:00:00.000') as subquery;
```

```bash
datacube -v ingest -c /home/odci/Datacube/agdc-v2/ingest/ingestion_configs/siam/s2_siam_epsg32637_syria_25km.yaml --executor multiproc 10

datacube -v ingest -c /home/odci/Datacube/agdc-v2/ingest/ingestion_configs/siam/s2_siam_epsg32637_syria.yaml --executor multiproc 6
```

#### Delete process:
```sql
DELETE  FROM agdc.dataset_location WHERE added > '2018-01-17 16:00:00.000';
DELETE FROM agdc.dataset_source WHERE dataset_ref NOT IN (SELECT dataset_ref FROM agdc.dataset_location);
DELETE FROM agdc.dataset WHERE id NOT IN (SELECT dataset_ref FROM agdc.dataset_location);
DELETE FROM agdc.dataset_type WHERE name = 'siam_utm37n_tiled';
```

## Jupyter notebook
```bash
cd /home/odci/Datacube/data_cube_notebooks/
source activate cubeenv_2
jupyter notebook
# hit control-Z
disown -h
bg
```

#### Drop DB and re-create (22.01.2018 @ 13:00)
```sql
DELETE FROM agdc.dataset_location;

DELETE FROM agdc.dataset_source;

DELETE FROM agdc.dataset;

DELETE FROM agdc.dataset_type;
```

```bash
source ~/Datacube/datacube_env/bin/activate

python /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/siam/prep_siam.py

python /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/sentinel_2/prep_s2.py
```

```bash
datacube -v product add /home/odci/Datacube/agdc-v2/ingest/dataset_types/sentinel_2/s2_granules.yaml
datacube -v product add /home/odci/Datacube/agdc-v2/ingest/dataset_types/siam/siam_il.yaml

datacube -v ingest -c /home/odci/Datacube/agdc-v2/ingest/ingestion_configs/siam/s2_siam_epsg32637_syria_100km.yaml --executor multiproc 10
datacube -v ingest -c /home/odci/Datacube/agdc-v2/ingest/ingestion_configs/siam/s2_siam_epsg32637_syria_10km.yaml --executor multiproc 10
```
@ 13:14:33 - 13:26:15 for 471 scenes
```bash
python /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/sentinel_2/index_s2.py
```

@ 13:27:57 - 13:39:41 for 471 scenes
```bash
python /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/siam/index_siam.py

sudo chown -R hannah:aiq /data/s2/ingested_data/siam_syria/v1
sudo chmod 777  /data/s2/ingested_data/siam_syria/v1
```

@ 14:13 - 16:08:15 (2373 processes)
```bash
datacube -v ingest -c /home/odci/Datacube/agdc-v2/ingest/ingestion_configs/siam/s2_siam_epsg32637_syria_100km.yaml --executor multiproc 10
```

@ 2018-01-25 21:35 (57696 tasks)
```bash
2018-01-25 21:35:23,053 10741 agdc-ingest INFO 57696 tasks discovered
```
