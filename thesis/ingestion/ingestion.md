# Dataset ingestion


## Setting up the environment

Start the python virtual environment

```bash
[odci@cf000508 dataset_types]$ source ~/Datacube/datacube_env/bin/activate
```

The command line should now look like this

```bash
(datacube_env)  [odci@cf000508 dataset_types]$
```

## Product definition of the siam metadata

Product add command

```bash
(datacube_env) [odci@cf000508 dataset_types]$ datacube -v product add /home/odci/Datacube/agdc-v2/ingest/dataset_types/siam/siam_il.yaml
```

yields the following result

```bash
2017-12-18 14:30:21,054 18749 datacube INFO Running datacube command: /home/odci/Datacube/datacube_env/bin/datacube -v product add siam/siam_il.yaml
2017-12-18 14:30:21,141 18749 datacube.index.postgres._dynamic INFO Creating index: dix_siam_il_lat_lon_time
2017-12-18 14:30:21,153 18749 datacube.index.postgres._dynamic INFO Creating index: dix_siam_il_time_lat_lon
Added "siam_il"
```
