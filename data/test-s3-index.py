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
    topo = resp.json()

    print >> stderr, 'request took', resp.elapsed, 'from', url, 'in', hex(get_ident())
    
    start = time()
    
    assert topo['type'] == 'Topology'
    
    bbox_fails, shape_fails = 0, 0
    
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
                bbox_fails += 1
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
                shape_fails += 1
                continue
            
            p = object['properties']
            
            yield p.get('NAME', None), p.get('NAMELSAD', None), p.get('GEOID', None), p.get('GEOID10', None)
    
    print >> stderr, 'check took', (time() - start), 'seconds', 'in', hex(get_ident()), 'with', bbox_fails, 'bbox fails and', shape_fails, 'shape fails'

def retrieve_zoom_features(loc, zoom, results):
    '''
    '''
    for result in check(loc, zoom):
        results.append(result)

def get_features(loc):
    '''
    '''
    start = time()
    results = []
    
    threads = [
        Thread(target=retrieve_zoom_features, args=(loc, 10, results)),
        Thread(target=retrieve_zoom_features, args=(loc, 8, results))
        ]

    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    print >> stderr, 'results took', (time() - start), 'seconds'
    
    return results

if __name__ == '__main__':
    
    print get_features(Location(47.620510, -122.349305)) # Space Needle
    print get_features(Location(37.805311, -122.272540)) # Oakland City Hall
    print get_features(Location(37.775793, -122.413549)) # Code for America
    print get_features(Location(40.753526, -73.976626)) # Grand Central Station
    print get_features(Location(38.871006, -77.055963)) # The Pentagon
    print get_features(Location(29.951057, -90.081090)) # The Superdome
    print get_features(Location(41.878874, -87.635907)) # Sears Tower
