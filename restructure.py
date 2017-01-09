import os
import fnmatch
import shutil

root_folder = 'C:\\tempS2'

# Create empty list for tile folder paths
tile_folders = []
for dirpath, dirnames, filenames in os.walk(root_folder, topdown=True):
    for dirname in dirnames:
        if (dirname == 'IMG_DATA'
                and fnmatch.fnmatch(dirpath, '*GRANULE*')):
            tile_folders.append(dirpath)
print tile_folders

for folder in tile_folders:
    # This needs to return capture date for old structure.
    # path_parts = folder.split("\\")
    # granule_file = path_parts[:-1]
    # if granule_file.startswith("S2A_"):
        # package_file = path_parts[:-3]
        # package_parts = package_file.split("_")[]
        # datetimeinfo = package_parts[7]
        # capture_date = datetimeinfo[:-7]

    # Move tile folder to temp folder.
    shutil.move(folder, root_folder)

    # If old structure, rename to replace creation date with capture date in title.

    # Remove original file structure
    shutil.rmtree(str(folder[:-70]))

# Rename new L1C folders to start with S2A_
for fn in os.listdir(root_folder):
    if not os.path.isdir(os.path.join(root_folder, fn)):
        continue # Not a directory.
    if fn.startswith('S2A_'):
        continue
    else:
        new_fn = 'S2A_{}'.format(fn)
        os.rename(os.path.join(root_folder, fn), os.path.join(root_folder, new_fn))
