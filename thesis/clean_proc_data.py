import os
import sys

def findProcData(input_dir):

    proc_data_dirs = list()

    for dirpath, dirnames, filenames in os.walk(input_dir):
        if dirpath.endswith('PROC_DATA'):
            proc_data_dirs.append(dirpath)

    return proc_data_dirs


if __name__ == '__main__':

    dirNames = ['/data/s2/37SBA/', '/data/s2/37SCA/', '/data/s2/37SDA']

    for directory in dirNames:

        proc_data_dirs = findProcData(directory)
        
        for proc_data in proc_data_dirs:

            files = os.listdir(proc_data)

            #
            # Delete empty PROC_DATA folders
            #
            if len(files) == 0:
                os.rmdir(proc_data)
                continue
            
            files_to_delete = ('_calrefbyt_lndstlk.dat.aux.xml',
                              '_caltembyt_lndstlk.dat.aux.xml',
                              '_caltembyt_lndstlk.hdr',
                              '_calrefbyt_lndstlk.hdr',
                              '_caltembyt_lndstlk.dat',
                              '_calrefbyt_lndstlk.dat')
            for fn in files:
                if fn.endswith(files_to_delete):
                     to_remove = os.path.join(proc_data, fn)
                     os.remove(to_remove)

