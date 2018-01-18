# Dataset ingestion


## Setting up the environment

Start the python virtual environment

```bash
[odci@cf000508 dataset_types]$
```

The command line should now look like this

```bash
(datacube_env)  [odci@cf000508 dataset_types]$
```

## Product definition of the sentinel 2 products
```bash
(datacube_env) [odci@cf000508 dataset_types]$ datacube -v product add /home/odci/Datacube/agdc-v2/ingest/dataset_types/sentinel_2/s2_granules.yaml
```

## Product definition of the siam information layer products

Product add command

```bash
(datacube_env) [odci@cf000508 dataset_types]$ datacube -v product add /home/odci/Datacube/agdc-v2/ingest/dataset_types/siam/siam_il2.yaml
```

yields the following result (_note: modified name to siam_il2 to match proper product definition_)

```bash
2017-12-18 14:30:21,054 18749 datacube INFO Running datacube command: /home/odci/Datacube/datacube_env/bin/datacube -v product add siam/siam_il2.yaml
2017-12-18 14:30:21,141 18749 datacube.index.postgres._dynamic INFO Creating index: dix_siam_il2_lat_lon_time
2017-12-18 14:30:21,153 18749 datacube.index.postgres._dynamic INFO Creating index: dix_siam_il2_time_lat_lon
Added "siam_il2"
```

## Prepare metadata and index sentinel-2 products

This creates a metadata file (datacube-metadata.yaml) for each sentinel-2 product in each product folder located in the three tile folders (37SBA, 37SCA, 37SDA) in /data/s2/.
```bash
(datacube_env) [odci@cf000508 dataset_types]$ python /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/sentinel_2/prep_s2.py
```
Once the metadata have been created, the products can be batch indexed using the following command:
```bash
(datacube_env) [odci@cf000508 dataset_types]$ python /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/sentinel_2/index_s2.py
```
## Prepare metadata and index siam information layers
This creates a metadata file (siam-metadata.yaml) for each batch of siam information products already existing for a given sentinel-2 dataset located in the three tile folders (37SBA, 37SCA, 37SDA) in /data/s2/.
```bash
(datacube_env) [odci@cf000508 dataset_types]$ python /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/siam/prep_siam.py
```
Once the metadata have been created, the products can be batch indexed using the following command:
```bash
(datacube_env) [odci@cf000508 dataset_types]$ python /home/odci/Datacube/agdc-v2/ingest/prepare_scripts/siam/index_siam.py
```
_note: the metadata created for the source sentinel-2 dataset is incorporated in this process, which initiates an automatic index check of the source dataset making an initial sentinel-2 indexing redundant._

## Ingest siam products
In this step, a new product definition is created and associated metadata are both automatically ingested into the datacube database at once.
One ingestion config was created for 100km tiles, and another for 25km tiles. Multiprocessing can be set-up, depending on what your hardware can handle.

```bash
datacube -v ingest -c /home/odci/Datacube/agdc-v2/ingest/ingestion_configs/siam/s2_siam_epsg32637_syria.yaml --executor multiproc 10
```

```bash
datacube -v ingest -c /home/odci/Datacube/agdc-v2/ingest/ingestion_configs/siam/s2_siam_epsg32637_syria_25km.yaml --executor multiproc 10
```
_note: be sure to have the optional (and poorly documented) [fuse_data](https://github.com/opendatacube/datacube-core/issues/147) flag set to copy in order to better handle overlapping areas._

_note: Be sure that the permissions of whatever folder you are writing the ingested data to (in this case e.g. /data/s2/ingested_data/siam_syria/v1/) are set to 777 according to the [documentation](https://github.com/ceos-seo/data_cube_ui/blob/master/docs/ingestion_guide.md)_
