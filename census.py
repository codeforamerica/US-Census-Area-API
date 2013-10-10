from time import time
from sys import stderr
from threading import Thread
from thread import get_ident

from requests import get
from shapely.geometry import MultiPolygon, Polygon, LineString, Point
from ModestMaps.OpenStreetMap import Provider
from ModestMaps.Geo import Location

census_url = 'http://forever.codeforamerica.org/Census-API/'

def unwind(indexes, arcs, transform):
    ''' Unwind a set of TopoJSON arc indexes into a transformed line or ring.
    
        Arc index documentation, with explanation of negative indexes:
            https://github.com/topojson/topojson-specification#214-arc-indexes
        
        Transformations:
            https://github.com/topojson/topojson-specification#212-transforms
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

def decode(object, topo):
    ''' Decode a single object geometry from a TopoJSON topology.
    
        Throw an error if it's anything other than a polygon or multipolygon.
    '''
    arcs, transform = topo['arcs'], topo['transform']
    
    if object['type'] == 'Polygon':
        rings = [unwind(indexes, arcs, transform) for indexes in object['arcs']]
        return Polygon(rings[0], rings[1:])
        
    if object['type'] == 'MultiPolygon':
        parts = []
        
        for part in object['arcs']:
            rings = [unwind(indexes, arcs, transform) for indexes in part]
            part_shp = Polygon(rings[0], rings[1:])
            parts.append(part_shp)
        
        return MultiPolygon(parts)
    
    raise Exception(object['type'])

def retrieve_zoom_features(loc, zoom, include_geom):
    ''' Retrieve all features enclosing a given point location at a zoom level.
    
        Requests TopoJSON tile from forever.codeforamerica.org spatial index,
        decodes bounding boxes and geometries if necessary, then yields a stream
        of any feature feature whose geometry covers the requested point.
    '''
    osm = Provider()

    point = Point(loc.lon, loc.lat)
    coord = osm.locationCoordinate(loc).zoomTo(zoom)
    path = '%(zoom)d/%(column)d/%(row)d' % coord.__dict__
    url = census_url + 'by-tile/%s.topojson.gz' % path
    
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
            x_, y_, _x, _y = object['bbox']
            
            obj_box = Polygon([(x_, y_), (x_, _y), (_x, _y), (_x, y_), (x_, y_)])
            
            if not point.within(obj_box):
                # object failed a simple bounding box check and can be discarded.
                bbox_fails += 1
                continue
            
            obj_shp = decode(object, topo)
            
            if not point.within(obj_shp):
                # object failed a point-in-polygon check and can be discarded.
                shape_fails += 1
                continue
            
            feature = {'type': 'Feature', 'properties': object['properties']}
            
            if include_geom:
                feature['geometry'] = obj_shp.__geo_interface__
            
            yield feature
    
    print >> stderr, 'check took', (time() - start), 'seconds', 'in', hex(get_ident()), 'with', bbox_fails, 'bbox fails and', shape_fails, 'shape fails'

def get_features(point, include_geom):
    ''' Get a list of features found at the given point location.
    
        Thread calls to retrieve_zoom_features().
    '''
    loc = Location(point.GetY(), point.GetX())
    
    def _retrieve_zoom_features(zoom, results):
        for result in retrieve_zoom_features(loc, zoom, include_geom):
            results.append(result)
    
    start = time()
    results = []
    
    threads = [
        Thread(target=_retrieve_zoom_features, args=(10, results)),
        Thread(target=_retrieve_zoom_features, args=(8, results))
        ]

    for t in threads:
        t.start()
    
    for t in threads:
        t.join()
    
    print >> stderr, 'results took', (time() - start), 'seconds'
    
    return results
