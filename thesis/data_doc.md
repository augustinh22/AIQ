#
#
#
---
1. Select tiles for download using Sentinel-2 Dashboard

#### _Border of Syria and Turkey_
##### 37SBA
  - python download_linux.py -t 37SBA -d 2015-05-01 -f 2016-05-01 -w /home/hannah/data/37SBA
    - [run on 29.11.2017 at 18:24]
  - python download_linux.py -t 37SBA -d 2016-05-01 -f 2017-05-01 -w /home/hannah/data/37SBA
   - [run on 30.11.2017 at 10:35]
   - Stopped at about 11:00 due to full partition
  - python download_linux.py -t 37SBA -d 2016-05-01 -f 2017-05-01 -w /data/s2/37SBA
    - [run on 30.11.2017 at 13:05]
  - python download_linux.py -t 37SBA -d 2017-05-01 -w /data/s2/37SBA
    - [run on 30.11.2017 at 13:22]
    - [run again on 30.11.207 at 14:58 due to a bunch of 500 errors]
    - [run again on 30.11.207 at 15:39 due to a bunch of 500 errors]
    - [run on 30.11.2017 at 12:30 to get most recent image (02.12)]
  - python download_linux.py -t 37SBA -d 2016-04-01 -f 2017-06-01 -w /data/s2/37SBA
   - [run on 30.11.207 at 16:16]
   - delete S2A_OPER_PRD_MSIL1C_PDMC_20160925T053337_R121_V20160923T082002_20160923T082003.SAFE due to empty metadata file encountered during Conversion
   - python download_linux.py -t 37SBA -d 2016-09-20 -f 2016-09-30 -w /data/s2/37SBA
    - [run on 05.12.207 at 17:09]

##### 37SCA
 - python download_linux.py -t 37SCA -d 2015-05-01 -f 2016-12-07 -w /data/s2/37SCA
  - [run on 30.11.2017 at 19:55]
 - python download_linux.py -t 37SCA -d 2016-12-06 -f 2017-11-03 -w /data/s2/37SCA
  - [run on 01.12.2017 at 9:13]
 - python download_linux.py -t 37SCA -d 2017-11-02 -w /data/s2/37SCA
  -  [run on 04.12.2017 at 12:01]

##### 37SDA
 - python download_linux.py -t 37SDA -d 2015-05-01 -f 2017-08-16 -w /data/s2/37SDA
  -  [run on 01.12.2017 at 13:49 -- ~2:15 on 02.12.2017 for 97 scenes)]
 -  python download_linux.py -t 37SDA -d 2017-08-15  -w /data/s2/37SDA
  -  [run on 04.12.2017 at 12:33 -- 13:31, 21 scenes]

##### Additional Possibilities
###### _Border of Syria and Turkey_
  - 37SEA
###### _South of the Syrian-Turkish border_
 - 37SBV
 - 37SCV
 - 37SDV
 - 37SEV

###### _Turkey north of Syria_
 - 37SBB
 - 37SCB
 - 37SDB
 - 37SEB

##### Create Cronjob
- crontab -e
- insert following: 0 2 * * * . $HOME/.bash_profile; /home/hannah/repos/AIQ/thesis/automate_downloads.sh
- Contents of Script:
"""
#!/bin/bash

source activate aiq27
cd /home/hannah/repos/AIQ/thesis/
python download_linux.py -t 37SBA --auto y -a ./key.txt -w /data/s2/37SBA
python download_linux.py -t 37SCA --auto y -a ./key.txt -w /data/s2/37SCA
python download_linux.py -t 37SDA --auto y -a ./key.txt -w /data/s2/37SDA

python conversion_linux.py --auto y -r /data/s2/37SBA
python conversion_linux.py --auto y -r /data/s2/37SCA
python conversion_linux.py --auto y -r /data/s2/37SDA
"""