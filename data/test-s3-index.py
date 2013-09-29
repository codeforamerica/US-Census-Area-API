from time import time
from sys import stderr
from threading import Thread
from thread import get_ident

from requests import get
from shapely.geometry import MultiPolygon, Polygon, Point
from ModestMaps.OpenStreetMap import Provider
from ModestMaps.Geo import Location

def unwind(indexes, arcs, transform):
    '''
    '''
    ring = []
    
    for index in indexes:
        arc = arcs[index if index >= 0 else abs(index) - 1]
        line = [arc[0]]
        
        for (x, y) in arc[1:]:
            line.append((line[-1][0] + x, line[-1][1] + y))
        
        dx, dy = transform['scale']
        tx, ty = transform['translate']
        line = [(x * dx + tx, y * dy + ty) for (x, y) in line]
        
        ring += line if index >= 0 else reversed(line)
    
    return ring

def check(loc, zoom):
    '''
    '''
    osm = Provider()

    point = Point(loc.lon, loc.lat)
    coord = osm.locationCoordinate(loc).zoomTo(zoom)
    path = '%(zoom)d/%(column)d/%(row)d' % coord.__dict__
    url = 'http://forever.codeforamerica.org/Census-API/by-tile/%s.topojson.gz' % path
    
    sw = osm.coordinateLocation(coord.down())
    ne = osm.coordinateLocation(coord.right())
    tile_shp = Polygon([(sw.lon, sw.lat), (sw.lon, ne.lat), (ne.lon, ne.lat), (ne.lon, sw.lat), (sw.lon, sw.lat)])
    
    resp = get(url)
    print >> stderr, 'request took', resp.elapsed, 'from', url, 'in', get_ident()
    
    start = time()
    topo = resp.json()
    
    assert topo['type'] == 'Topology'
    
    for layer in topo['objects']:
        if zoom == 8:
            assert layer in ('state', 'county', 'place', 'cbsa')
        elif zoom == 10:
            assert layer in ('zcta510', 'tract')
        else:
            raise Exception('Unknown layer %d' % zoom)
        
        for object in topo['objects'][layer]['geometries']:
            xmin, ymin, xmax, ymax = object['bbox']
            
            obj_box = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin)])
            
            if not point.within(obj_box):
                # object failed a simple bounding box check and can be discarded.
                continue
            
            if object['type'] == 'Polygon':
                rings = [unwind(ring, topo['arcs'], topo['transform']) for ring in object['arcs']]
                obj_shp = Polygon(rings[0], rings[1:])
                
            elif object['type'] == 'MultiPolygon':
                parts = []
                
                for part in object['arcs']:
                    rings = [unwind(ring, topo['arcs'], topo['transform']) for ring in part]
                    part_shp = Polygon(rings[0], rings[1:])
                    parts.append(part_shp)
                
                obj_shp = MultiPolygon(parts)
            
            else:
                raise Exception(object['type'])
            
            if not point.within(obj_shp):
                # object failed a point-in-polygon check and can be discarded.
                continue
            
            yield object['properties']
    
    print >> stderr, 'check took', (time() - start), 'seconds', 'in', get_ident()

def check_do(loc, zoom, results):
    '''
    '''
    for result in check(loc, zoom):
        results.append(result)

def get_features(loc):
    '''
    '''
    start = time()
    results = []

    t1 = Thread(target=check_do, args=(loc, 10, results))
    t2 = Thread(target=check_do, args=(loc, 8, results))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    print >> stderr, 'results took', (time() - start), 'seconds'
    
    return results

if __name__ == '__main__':
    
    print get_features(Location(37.805311, -122.272540))
    print get_features(Location(37.775793, -122.413549))
