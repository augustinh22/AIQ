1. Download Conda using wget (http://linuxpitstop.com/install-anaconda-miniconda-conda-on-ubuntu-centos-linux/):
  wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
  bash Miniconda2-latest-Linux-x86_64.sh
  conda update conda

2. Create python environment:
  conda create --name aiq27 python=2.7 requests scipy gdal=2.2.0 -c conda-forge

3. Export Environment file:
  conda env export > environment.yml
