#-------------------------------------------------------------------------------
# Name:        Restructuring for SIAM and IQ.
# Purpose:     This script takes the originally downloaded S2 file
#              structure and accesses the individual tile directories
#              located within the IMG_DATA folder. It then modifies the tile
#              under the old naming convention (pre-06.12.16) to have the
#              sensing/capture date in the title, rather than the day
#              the data was processed, which can be days to months laterself.
#              It then moves all tile directories to a given root folder,
#              with the purpose of reducing overall path length for Windows.
#              Finally, it renames tile folders under the new naming
#              convention, adding "S2A" to the first part "L1C_*".
#
# Author:      h.Augustin
#
# Created:     21.12.2016
# Updated:     09.01.2017
#
#-------------------------------------------------------------------------------

#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-

import os
import fnmatch
import shutil


def tile_folders(root_folder):

    # Create empty list for tile folder paths.
    tile_folders = []
    for dirpath, dirnames, filenames in os.walk(root_folder, topdown=True):
        for dirname in dirnames:
            if (dirname == 'IMG_DATA'
                    and fnmatch.fnmatch(dirpath, '*GRANULE*')):
                tile_folders.append(dirpath)
    return tile_folders


def change_to_capture(tile_folders):

    for folder in tile_folders:

        # This needs to return capture date for old structure.

#       os.path.dirname(os.path.dirname(file)) ## directory of directory of file

        # path_parts = folder.split("\\")
        # granule_file = path_parts[-1]
        # if granule_file.startswith("S2A_"):
            # package_file = path_parts[-3]
            # package_parts = package_file.split("_")
            # capture_info = package_parts[7]

            # capture_date = capture_info[1:-7]

            # granule_parts = granule_file.split("_")
            # granule_parts[4] = capture_info[1:]
            # new_name = "_".join(granule_parts)
            # os.path.abspath(folder)
            # os.rename(granule_file, new_name)

def move_and_delete(tile_folders, root_folder):

    for folder in tile_folders:

        # Move tile folder to temp folder.
        shutil.move(folder, root_folder)
        # Remove original file structure
        shutil.rmtree(str(folder[:-70]))

def new_to_S2A(root_folder):

    # Rename new L1C folders to start with S2A_
    for fn in os.listdir(root_folder):
        if not os.path.isdir(os.path.join(root_folder, fn)):
            continue # Not a directory.
        if fn.startswith('S2A_'):
            continue
        else:
            new_fn = 'S2A{}'.format(fn)
            os.rename(os.path.join(root_folder, fn), os.path.join(root_folder, new_fn))

if __name__ == "__main__":

    root_folder = 'C:\\tempS2'

    # List all original tile folders.
    orig_folders = tile_folders(root_folder)

    # Modify old tile name directories (pre-06.12.16) to capture date and time
    # instead of creation date and time.
    change_to_capture(orig_folders)

    # List all tile folders after modification.
    mod_folders = tile_folders(root_folder)

    # Move folders to root directory.
    move_and_delete(mod_folders, root_folder)

    # Modify new tile name directories (post-06.12.16) to start with S2A.
    new_to_S2A(root_folder)
