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
        head, tile_file = os.path.split(folder)

        # If it is the old version, then rename the tile package.
        if tile_file.startswith("S2A_"):

            # Return path and name of package folder, extracting date and time
            # of image capture.
            package = os.path.dirname(os.path.dirname(folder))
            head, tail = os.path.split(package)
            package_parts = tail.split("_")
            capture_info = package_parts[7]

            # capture_date = capture_info[1:-7]

            # Replace the creation date and time with the capture date and time.
            file_parts = tile_file.split("_")
            file_parts[7] = capture_info[1:]
            new_name = "_".join(file_parts)
            new_path = os.path.join(os.path.dirname(folder), new_name)
            os.rename(folder, new_path)


def move_and_meta(tile_folders, root_folder, delete):

    for folder in tile_folders:

        # Move tile folder to temp folder.
        shutil.move(folder, root_folder)

        if delete is True:
            # Remove original file structure
            shutil.rmtree(os.path.dirname(os.path.dirname(folder)))
        else:
            # Move original file structure without images to metadata folder.
            metadata_dir = os.path.join(root_folder, 'metadata')
            if not(os.path.exists(metadata_dir)):
                os.mkdir(metadata_dir)
            shutil.move(os.path.dirname(os.path.dirname(folder)), metadata_dir)


def new_to_S2A(root_folder):

    # Rename new L1C folders to start with S2A_
    for fn in os.listdir(root_folder):
        if not os.path.isdir(os.path.join(root_folder, fn)):
            continue # Not a directory.
        if fn.startswith('S2A_'):
            continue
        elif fn.startswith('L1C'):
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
    move_and_meta(mod_folders, root_folder, False)

    # Modify new tile name directories (post-06.12.16) to start with S2A.
    new_to_S2A(root_folder)
