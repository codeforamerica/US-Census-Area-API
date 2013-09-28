''' Extract one GeoJSON file per GEOID from local zip files.

Built for zip files of State, County, and Place geometries:

    curl -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/STATE/tl_2013_us_state.zip'
         -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/COUNTY/tl_2013_us_county.zip'
         -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/PLACE/tl_2013_[01-99]_place.zip'
'''
from zipfile import ZipFile
from subprocess import Popen
from os.path import exists
from glob import glob
from os import remove

from osgeo import ogr

if __name__ == '__main__':

    for zipname in glob('*.zip'):
        zipfile = ZipFile(zipname)
        
        types = ('.shp', '.shx', '.prj', '.dbf')
        names = [name for name in zipfile.namelist() if name[-4:] in types]
        
        zipfile.extractall(members=names)
        
        shpname = names[0][:-4] + '.shp'
        
        shp_ds = ogr.Open(shpname)
        layer = shp_ds.GetLayer(0)
        
        for feature in layer:
            geoid = feature.GetField('GEOID')
            outname = '%s.json' % geoid
            
            print shpname, geoid, '...'
        
            if exists(outname):
                remove(outname)
            
            ogr2ogr = 'ogr2ogr', '-where', "GEOID='%s'" % geoid, \
                      '-t_srs', 'EPSG:4326', '-f', 'GeoJSON', outname, shpname
            
            ogrcmd = Popen(ogr2ogr)
            ogrcmd.wait()
            
            assert ogrcmd.returncode == 0, 'Failed on GEOID %s' % geoid
        
        for ext in types:
            remove(shpname[:-4] + ext)
