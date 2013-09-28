''' Extract one directory of GeoJSON files per tile from local zip files.

Built for zip files of State, County, CBSA, and Place geometries:

    curl -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/STATE/tl_2013_us_state.zip'
         -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/COUNTY/tl_2013_us_county.zip'
         -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/CBSA/tl_2013_us_cbsa.zip'
         -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/PLACE/tl_2013_[01-99]_place.zip'
'''
from zipfile import ZipFile
from itertools import product
from os import makedirs, remove, stat
from subprocess import Popen
from shutil import copyfile
from os.path import exists
from glob import glob

from ModestMaps.Core import Coordinate
from ModestMaps.OpenStreetMap import Provider

def extract(zipfile):
    '''
    '''
    types = ('.shp', '.shx', '.prj', '.dbf')
    names = [name for name in zipfile.namelist() if name[-4:] in types]
    
    zipfile.extractall(members=names)
    
    shpname = names[0][:-4] + '.shp'
    
    return shpname

def cleanup(shpname):
    '''
    '''
    types = ('.shp', '.shx', '.prj', '.dbf')

    for ext in types:
        remove(shpname[:-4] + ext)

def coordinates(zoom):
    '''
    '''
    osm = Provider()

    for (col, row) in product(range(2**zoom), range(2**zoom)):
        coord = Coordinate(row, col, zoom)
        
        sw = osm.coordinateLocation(coord.down())
        ne = osm.coordinateLocation(coord.right())
        
        yield coord, sw, ne

def prepdir(coord):
    '''
    '''
    path = 'tiles/%(zoom)d/%(column)d/%(row)d' % coord.__dict__
    
    try:
        makedirs(path)
    except OSError:
        pass
    
    return path

def runogr2ogr(cmd):
    '''
    '''
    ogrcmd = Popen(cmd)
    ogrcmd.wait()
    
    assert ogrcmd.returncode == 0, 'Failed on %s' % outname
    
    if 'GeoJSON' in cmd and stat(outname).st_size == 131:
        remove(outname)

if __name__ == '__main__':

    #
    # Extract features for each tile.
    #
    
    zoom = 8
    
    # States need to be first in the list, so 
    zipnames = ['tl_2013_us_state.zip', 'tl_2013_us_county.zip', 'tl_2013_us_cbsa.zip'] \
             + glob('tl_2013_??_place.zip')
    
    for zipname in zipnames:
        zipfile = ZipFile(zipname)
        shpname = extract(zipfile)
        
        for (coord, sw, ne) in coordinates(zoom):
            path = prepdir(coord)

            outname = '%s/%s.json' % (path, shpname[:-4])
            
            if shpname != 'tl_2013_us_state.shp' and not exists(path + '/tl_2013_us_state.json'):
                # skip this probably-empty tile
                continue
            
            print outname, '...'
        
            if exists(outname):
                remove(outname)
            
            cmd = 'ogr2ogr', '-spat', str(sw.lon), str(sw.lat), str(ne.lon), str(ne.lat), \
                  '-t_srs', 'EPSG:4326', '-f', 'GeoJSON', '-lco', 'WRITE_BBOX=YES', outname, shpname
            
            runogr2ogr(cmd)
        
        cleanup(shpname)
    
    #
    # Combine per-state place files into per-tile place files.
    #
    
    for (coord, sw, ne) in coordinates(zoom):
        path = prepdir(coord)
        
        for (index, filename) in enumerate(glob('%s/tl_2013_??_place.json' % path)):
            if filename.endswith('tl_2013_us_place.json'):
                continue
        
            outname = '%s/tl_2013_us_place.json' % path
            
            if index == 0:
                print 'copy', filename, 'to', outname, '...'
            
                copyfile(filename, outname)

            else:
                print 'append', filename, 'to', outname, '...'
            
                from re import compile, S
                pat = compile(r'^{\n"type": "FeatureCollection", *\n"bbox": (\[.+?\]), *\n"features": \[\n(.+)\n\] *\n}\n$', S)

                filedata = open(filename).read()
                filematch = pat.match(filedata)
                assert filematch, 'Bad '+ filename
                
                outdata = open(outname).read()
                outmatch = pat.match(outdata)
                assert outmatch, 'Bad '+ outname
                
                with open(outname, 'w') as out:
                    print >> out, '{\n"type": "FeatureCollection",\n"bbox":',
                    print >> out, outmatch.group(1)+',' # bbox is the same each time
                    print >> out, '"features": ['
                    print >> out, filematch.group(2)
                    print >> out, ','
                    print >> out, outmatch.group(2)
                    print >> out, ']\n}'
