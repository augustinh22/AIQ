1. Download Conda using wget (http://linuxpitstop.com/install-anaconda-miniconda-conda-on-ubuntu-centos-linux/):
  
  `wget https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh`
  
  `sudo sh Miniconda2-latest-Linux-x86_64.sh -b -p /usr/local/miniconda`
  
  `export PATH=/usr/local/miniconda/bin:$PATH`
  
  `source ~/.bashrc`
  
  `conda update conda`

2. Create python environment:
  
  `conda create --name aiq27 python=2.7 requests scipy gdal=2.2.3 -c conda-forge`
  
  *Note: if the gdal version can no longer be found in the conda repository, don't pin the version (i.e. remove `=2.2.3`).*

3. Export Environment file:
  
  `conda env export > environment.yml`
