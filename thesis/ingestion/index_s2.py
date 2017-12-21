import os
import sys
import logging
import subprocess

def main(datasets):

    for yaml_path in datasets:
        cmd = ['datacube', '-v', 'dataset', 'add',  yaml_path]

        logger.info('Indexing dataset: {}'.format(yaml_path))

        ps = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        output = ps.communicate()[0]
        for line in output.splitlines():
            logger.debug("[*] {0}".format(line))

if __name__ == "__main__":

    #
    # Set-up logger.
    #
    log_dir = os.path.join('/home/odci/Datacube/agdc-v2/ingest/prepare_scripts/sentinel_2/', 'log')
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    logger_filepath = os.path.join(log_dir, 'index_s2.log')

    logging.basicConfig(filename=logger_filepath,
                        format='%(asctime)s:%(levelname)s:%(message)s',
                        level=logging.DEBUG)
    logger = logging.getLogger('index_s2')

    # datasets = ['/data/s2/37SBA/S2A_OPER_PRD_MSIL1C_PDMC_20161007T104254_R121_V20150830T082006_20150830T082754.SAFE/datacube-metadata.yaml']
    datasets = []
    for dirpath, dirnames, filenames in os.walk('/data/s2/', topdown=True):
        for filename in filenames:
            if filename.endswith('.yaml'):
               datasets.append(os.path.join(dirpath, filename))
    main(datasets)
