# coding=utf-8
"""
Ingest data from the command-line.
"""
from __future__ import absolute_import

import uuid
import logging
from xml.etree import ElementTree
from pathlib import Path
import yaml
import click
from osgeo import osr
import os
import sys
import datetime
# image boundary imports
import rasterio
from rasterio.errors import RasterioIOError
import rasterio.features
import shapely.affinity
import shapely.geometry
import shapely.ops


# IMAGE BOUNDARY CODE


def safe_valid_region(images, mask_value=None):
    try:
        return valid_region(images, mask_value)
    except (OSError, RasterioIOError):
        return None


def valid_region(images, mask_value=None):
    mask = None
    for fname in images:
        # ensure formats match
        with rasterio.open(str(fname), 'r') as ds:
            transform = ds.transform
            img = ds.read(1)

            if mask_value is not None:
                new_mask = img & mask_value == mask_value
            else:
                # new_mask = img != ds.nodata
                new_mask = img != 0
            if mask is None:
                mask = new_mask
            else:
                mask |= new_mask

    shapes = rasterio.features.shapes(mask.astype('uint8'), mask=mask)
    shape = shapely.ops.unary_union([shapely.geometry.shape(shape) for shape, val in shapes if val == 1])
    type(shapes)
    # convex hull
    geom = shape.convex_hull

    # buffer by 1 pixel
    geom = geom.buffer(1, join_style=3, cap_style=3)

    # simplify with 1 pixel radius
    geom = geom.simplify(1)

    # intersect with image bounding box
    geom = geom.intersection(shapely.geometry.box(0, 0, mask.shape[1], mask.shape[0]))

    # transform from pixel space into CRS space
    geom = shapely.affinity.affine_transform(geom, (transform.a, transform.b, transform.d,
                                                    transform.e, transform.xoff, transform.yoff))

    output = shapely.geometry.mapping(geom)

    return geom
    # output['coordinates'] = _to_lists(output['coordinates'])
    # return output


def _to_lists(x):
    """
    Returns lists of lists when given tuples of tuples
    """
    if isinstance(x, tuple):
        return [_to_lists(el) for el in x]

    return x


def get_geo_ref_points(root):
    nrows = int(root.findall('./*/Tile_Geocoding/Size[@resolution="10"]/NROWS')[0].text)
    ncols = int(root.findall('./*/Tile_Geocoding/Size[@resolution="10"]/NCOLS')[0].text)

    ulx = int(root.findall('./*/Tile_Geocoding/Geoposition[@resolution="10"]/ULX')[0].text)
    uly = int(root.findall('./*/Tile_Geocoding/Geoposition[@resolution="10"]/ULY')[0].text)

    xdim = int(root.findall('./*/Tile_Geocoding/Geoposition[@resolution="10"]/XDIM')[0].text)
    ydim = int(root.findall('./*/Tile_Geocoding/Geoposition[@resolution="10"]/YDIM')[0].text)

    return {
        'ul': {'x': ulx, 'y': uly},
        'ur': {'x': ulx + ncols * abs(xdim), 'y': uly},
        'll': {'x': ulx, 'y': uly - nrows * abs(ydim)},
        'lr': {'x': ulx + ncols * abs(xdim), 'y': uly - nrows * abs(ydim)},
    }


def get_coords(geo_ref_points, spatial_ref):
    t = osr.CoordinateTransformation(spatial_ref, spatial_ref.CloneGeogCS())

    def transform(p):
        lon, lat, z = t.TransformPoint(p['x'], p['y'])
        return {'lon': lon, 'lat': lat}

    return {key: transform(p) for key, p in geo_ref_points.items()}


def get_relevantpaths(path):
    for dirpath, dirnames, filenames in os.walk(str(path.parent)):
        for dirname in dirnames:
            if dirname == 'siamoutput':
                siamoutput = os.path.join(dirpath, dirname)
        for filename in filenames:
            if filename == 'datacube-metadata.yaml':
                datacube_YAML = os.path.join(dirpath, filename)
    return siamoutput, datacube_YAML

def get_PROC_DATA(path):

    for dirpath, dirnames, filenames in os.walk(path):
        for dirname in dirnames:
            if dirname == 'PROC_DATA':
                PROC_DATA =  os.path.join(dirpath, dirname)

    return PROC_DATA

def get_siamlayers(path):
    
    layers = ['18SpCt', '33SharedSpCt', '48SpCt', '96SpCt', 'HazePentarnaryMask', 'VegBinaryMask', 'fRatioGreennessIndex', 'cBrightness']
    siam_dict = {}
    print(path)
    for item in os.listdir(path):
        for layer in layers:
            if layer in item and item.endswith('.dat'):
                siam_dict[layer] = os.path.join('siamoutput', item)
    for item in os.listdir(os.path.dirname(path)):
        if item.endswith('nodata.dat'):
            siam_dict['nodata'] = item

    return siam_dict

def prepare_dataset(path):

    root = ElementTree.parse(str(path)).getroot()

    siamoutput_path, datacubeYAML_path = get_relevantpaths(path)
    siam_dict = get_siamlayers(siamoutput_path)

    siamoutput_file = os.path.join(siamoutput_path, (os.listdir(siamoutput_path))[0])
    ct_time = (datetime.datetime.fromtimestamp(os.path.getmtime(siamoutput_file)).strftime('%Y-%m-%dT%H:%M:%SZ'))
    del siamoutput_file

    with open(datacubeYAML_path, 'r') as f: 
        datacube_YAML = yaml.load(f.read())

    granules = {granule.get('granuleIdentifier'): [imid.text for imid in granule.findall('IMAGE_ID')]
                for granule in root.findall('./*/Product_Info/Product_Organisation/Granule_List/Granules')}

    if not granules:
        granules = {granule.get('granuleIdentifier'): [imid.text for imid in granule.findall('IMAGE_ID')]
            for granule in root.findall('./*/Product_Info/Product_Organisation/Granule_List/Granule')}

    for key, value in granules.items():
        found_IMAGE_IDs = value

    if len(granules) > 10 or len(found_IMAGE_IDs) > 10:

        documents = []
        for granule_id, images in granules.items():
            gran_path = str(path.parent.joinpath('GRANULE', granule_id, granule_id[:-7].replace('MSI', 'MTD') + '.xml'))
            if os.path.exists(gran_path):
                root = ElementTree.parse(gran_path).getroot()

                sensing_time = root.findall('./*/SENSING_TIME')[0].text
                cs_code = root.findall('./*/Tile_Geocoding/HORIZONTAL_CS_CODE')[0].text
                spatial_ref = osr.SpatialReference()
                spatial_ref.SetFromUserInput(cs_code)
                geo_ref_points = get_geo_ref_points(root)

                documents.append({
                'id': str(uuid.uuid4()),
                'product_type': 'INFORMATIONLAYERS',
                'creation_dt': ct_time,
                'platform': {'code': 'SIAM_IL'},
                'instrument': {'name': 'SIAM'},
                'extent': {
                    'from_dt': sensing_time,
                    'to_dt': sensing_time,
                    'center_dt': sensing_time,
                    'coord': get_coords(geo_ref_points, spatial_ref),
                },
                'format': {'name': 'ENVI'},
                'grid_spatial': {
                    'projection': {
                        'geo_ref_points': geo_ref_points,
                        'spatial_reference': spatial_ref.ExportToWkt(),
                    }
                },
                'image': {
                    'bands': {
                        key: {
                            'path': value,
                            'layer': 1,
                        } for key, value in siam_dict.items()
                        }
                },

                'lineage': {
                    'source_datasets': {
                        'level1': datacube_YAML }},
            })

    else:
        granules = {granule.get('granuleIdentifier'): [imid.text for imid in granule.findall('IMAGE_FILE')]
                    for granule in root.findall('./*/Product_Info/Product_Organisation/Granule_List/Granule')}

        documents = []
        for granule_id, images in granules.items():

            gran_path = str(path.parent.joinpath((os.path.dirname(os.path.dirname(images[0]))), 'MTD_TL.xml'))
            root = ElementTree.parse(gran_path).getroot()

            sensing_time = root.findall('./*/SENSING_TIME')[0].text
            cs_code = root.findall('./*/Tile_Geocoding/HORIZONTAL_CS_CODE')[0].text
            spatial_ref = osr.SpatialReference()
            spatial_ref.SetFromUserInput(cs_code)
            geo_ref_points = get_geo_ref_points(root)

            documents.append({
                'id': str(uuid.uuid4()),
                'product_type': 'INFORMATIONLAYERS',
                'creation_dt': ct_time,
                'platform': {'code': 'SIAM_IL'},
                'instrument': {'name': 'SIAM'},
                'extent': {
                    'from_dt': sensing_time,
                    'to_dt': sensing_time,
                    'center_dt': sensing_time,
                    'coord': get_coords(geo_ref_points, spatial_ref),
                },
                'format': {'name': 'ENVI'},
                'grid_spatial': {
                    'projection': {
                        'geo_ref_points': geo_ref_points,
                        'spatial_reference': spatial_ref.ExportToWkt(),
                    }
                },
                'image': {
                    'bands': {
                       key : {
                            'path': value,
                            'layer': 1,
                        } for key, value in siam_dict.items()
                        }
                },

                'lineage': {
                    'source_datasets': {
                        'level1': datacube_YAML }},
            })
    return documents


@click.command(help="Prepare Sentinel 2 dataset for ingestion into the Data Cube.")
@click.argument('datasets',
                type=click.Path(exists=True, readable=True, writable=True),
                nargs=-1)
def main(datasets):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

    for dataset in datasets:
        path = Path(dataset)

        if path.is_dir():
            print(path)
            xml_path = Path(path.joinpath(path.stem.replace('PRD_MSIL1C', 'MTD_SAFL1C') + '.xml'))
            if not xml_path.exists():
                xml_path = Path(path.joinpath('MTD_MSIL1C' + '.xml'))
                print (xml_path)
            if xml_path.exists():
                path = xml_path
                del xml_path
        if path.suffix != '.xml':
            raise RuntimeError('want xml')

        logging.info("Processing %s", path)
        documents = prepare_dataset(path)
        print(documents)
        #
        # BE sure to save in PROC_DATA folder.
        #
        PROC_DATA = get_PROC_DATA(dataset)
        if documents:
            yaml_path = os.path.join(PROC_DATA, 'siam-metadata.yaml')
            logging.info("Writing %s dataset(s) into %s", len(documents), yaml_path)
            with open(yaml_path, 'w') as stream:
                yaml.dump_all(documents, stream)
        else:
            logging.info("No datasets discovered. Bye!")


if __name__ == "__main__":
    root_folder = '/data/s2/'
    granule_folders = ['37SBA', '37SCA', '37SDA', '37SBU', '37SBV']
    datasets = []
    for tile in granule_folders:
        folder_path = os.path.join(root_folder, tile)
        for ds in os.listdir(folder_path):
            dataset = os.path.join(folder_path, ds)
            test_path = get_PROC_DATA(dataset)
            yaml_test = Path(os.path.join(test_path, 'siam-metadata.yaml'))
            if not yaml_test.exists():
                datasets.append(dataset)
    # datasets = ['/data/s2/37SBA/S2A_OPER_PRD_MSIL1C_PDMC_20160714T041913_R021_V20150902T083049_20150902T083049.SAFE/']
    # datasets = ['/data/s2/37SBA/S2A_OPER_PRD_MSIL1C_PDMC_20161007T104254_R121_V20150830T082006_20150830T082754.SAFE']
    main(datasets)
