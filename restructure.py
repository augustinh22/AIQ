import os
import fnmatch
import shutil

root_folder = r'C:\tempS2'

# Create empty list for tile folder paths
tile_folders = []
for dirpath, dirnames, filenames in os.walk(root_folder, topdown=True):
    for dirname in dirnames:
        if (dirname == 'IMG_DATA'
                and fnmatch.fnmatch(dirpath, '*GRANULE*')):
            tile_folders.append(dirpath)
print tile_folders

for folder in tile_folders:
    # Move tile folder to temp folder.
    shutil.move(folder, root_folder)
    # Remove original file structure
    shutil.rmtree(str(folder[:-70]))
