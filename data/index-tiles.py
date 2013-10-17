''' Extract one directory of GeoJSON files per tile from local zip files.

Built for zip files of State, County, CBSA, and Place geometries:

    curl -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/STATE/tl_2013_us_state.zip'
         -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/COUNTY/tl_2013_us_county.zip'
         -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/CBSA/tl_2013_us_cbsa.zip'
         -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/PLACE/tl_2013_[01-99]_place.zip'
'''
from zipfile import ZipFile
from itertools import product
from os import makedirs, remove, stat, link
from subprocess import Popen
from shutil import copyfile
from os.path import exists
from re import compile, S
from glob import glob

from ModestMaps.Core import Coordinate
from ModestMaps.OpenStreetMap import Provider

zoom_low, zoom_mid, zoom_high = 8, 10, 12

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
    
    if 'GeoJSON' in cmd and stat(outname).st_size <= 131:
        remove(outname)

def append_geojson(srcname, destname):
    ''' Append ogr2ogr-generated source file to destination file.
    
        Uses regular expressions instead of JSON parser, so formats and spacing
        and line breaks and bounding boxes must all match normal ogr2ogr output.
    '''
    pat = compile(r'^{\n"type": "FeatureCollection", *\n"bbox": (\[.+?\]), *\n"features": \[\n(.+)\n\] *\n}\n$', S)

    srcdata = open(srcname).read()
    srcmatch = pat.match(srcdata)
    assert srcmatch, 'Bad '+ srcname
    
    destdata = open(destname).read()
    destmatch = pat.match(destdata)
    assert destmatch, 'Bad '+ destname
    
    with open(destname, 'w') as out:
        print >> out, '{\n"type": "FeatureCollection",\n"bbox":',
        print >> out, destmatch.group(1)+',' # bbox is the same each time
        print >> out, '"features": ['
        print >> out, destmatch.group(2)
        print >> out, ','
        print >> out, srcmatch.group(2)
        print >> out, ']\n}'

if __name__ == '__main__':

    #
    # Extract state, county and CBSA features for each low-zoom tile.
    #
    
    # States need to be first in the list, so 
    zipnames = ['tl_2013_us_state.zip', 'tl_2013_us_county.zip', 'tl_2013_us_cbsa.zip'] \
             + glob('tl_2013_??_place.zip')
    
    for zipname in zipnames:
        zipfile = ZipFile(zipname)
        shpname = extract(zipfile)
        
        for (coord, sw, ne) in coordinates(zoom_low):
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
    
    coords = coordinates(zoom_low)
    
    for (coord, sw, ne) in coords:
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
                append_geojson(filename, outname)

    #
    # Extract ZCTA5 and tract features for each mid-zoom tile.
    #
    
    zipnames = ['tl_2013_us_zcta510.zip'] + glob('tl_2013_??_tract.zip')
    
    for zipname in zipnames:
        zipfile = ZipFile(zipname)
        shpname = extract(zipfile)
        
        for (coord, sw, ne) in coordinates(zoom_mid):
            parent = coord.zoomTo(zoom_low).container()
            
            if not exists(prepdir(parent) + '/tl_2013_us_state.json'):
                # skip this probably-empty tile
                continue
            
            path = prepdir(coord)
            
            outname = '%s/%s.json' % (path, shpname[:-4])
            
            print outname, '...'
            
            if exists(outname):
                remove(outname)
            
            cmd = 'ogr2ogr', '-spat', str(sw.lon), str(sw.lat), str(ne.lon), str(ne.lat), \
                  '-t_srs', 'EPSG:4326', '-f', 'GeoJSON', '-lco', 'WRITE_BBOX=YES', outname, shpname
            
            runogr2ogr(cmd)
        
        cleanup(shpname)
    
    #
    # Combine per-state tract files into per-tile tract files.
    #
    
    coords = coordinates(zoom_mid)
    
    for (coord, sw, ne) in coords:
        path = prepdir(coord)
        
        for (index, filename) in enumerate(glob('%s/tl_2013_??_tract.json' % path)):
            if filename.endswith('tl_2013_us_tract.json'):
                continue
        
            outname = '%s/tl_2013_us_tract.json' % path
            
            if index == 0:
                print 'copy', filename, 'to', outname, '...'
                copyfile(filename, outname)

            else:
                print 'append', filename, 'to', outname, '...'
                append_geojson(filename, outname)
    
    #
    # Extract block and block group features for each high-zoom tile.
    #
    
    zipnames = glob('tl_2013_??_bg.zip') + glob('tl_2013_??_tabblock.zip')
    
    for zipname in zipnames:
        zipfile = ZipFile(zipname)
        shpname = extract(zipfile)
        
        for (coord, sw, ne) in coordinates(zoom_high):
            parent = coord.zoomTo(zoom_low).container()
            
            if not exists(prepdir(parent) + '/tl_2013_us_state.json'):
                # skip this probably-empty tile
                continue
            
            path = prepdir(coord)
            
            outname = '%s/%s.json' % (path, shpname[:-4])
            
            print outname, '...'
            
            if exists(outname):
                remove(outname)
            
            cmd = 'ogr2ogr', '-spat', str(sw.lon), str(sw.lat), str(ne.lon), str(ne.lat), \
                  '-t_srs', 'EPSG:4326', '-f', 'GeoJSON', '-lco', 'WRITE_BBOX=YES', outname, shpname
            
            runogr2ogr(cmd)
        
        cleanup(shpname)
    
    #
    # Combine per-state block files into per-tile block files.
    #
    
    coords = coordinates(zoom_high)
    
    for (coord, sw, ne) in coords:
        path = prepdir(coord)
        
        for (index, filename) in enumerate(glob('%s/tl_2013_??_bg.json' % path)):
            if filename.endswith('tl_2013_us_bg.json'):
                continue
        
            outname = '%s/tl_2013_us_bg.json' % path
            
            if index == 0:
                print 'copy', filename, 'to', outname, '...'
                copyfile(filename, outname)

            else:
                print 'append', filename, 'to', outname, '...'
                append_geojson(filename, outname)
        
        for (index, filename) in enumerate(glob('%s/tl_2013_??_tabblock.json' % path)):
            if filename.endswith('tl_2013_us_tabblock.json'):
                continue
        
            outname = '%s/tl_2013_us_tabblock.json' % path
            
            if index == 0:
                print 'copy', filename, 'to', outname, '...'
                copyfile(filename, outname)

            else:
                print 'append', filename, 'to', outname, '...'
                append_geojson(filename, outname)
    
    #
    # 
    #
    
    zooms = zoom_low, zoom_mid
    
    for zoom in zooms:
        for (coord, sw, ne) in coordinates(zoom):
            path = prepdir(coord)
            
            files = glob('%s/tl_2013_us_*.json' % path)
            
            if not files:
                continue
            
            try:
                shortnames = []
                
                for file in files:
                    # knock off the "tl_2013_us_" part
                    shortname = path + '/' + file[len(path) + 12:]
                    shortnames.append(shortname)
                    link(file, shortname)
                
                outname = path + '.topojson'
                
                print outname, '...'
                
                cmd = './node_modules/topojson/bin/topojson', '--cartesian', \
                      '--allow-empty', '--bbox', '-q', '36000000', '-p', \
                      '--out', outname
                
                cmd += tuple(shortnames)
                
                topocmd = Popen(cmd)
                topocmd.wait()
                
                assert topocmd.returncode == 0, 'Failed on %s' % outname
            
            finally:
                for shortname in shortnames:
                    if shortname not in files:
                        remove(shortname)
