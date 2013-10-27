from shapely import wkb
from util import json_encode

def features_geojson(features, json_callback):
    '''
    '''
    geojson = dict(type='FeatureCollection', features=features)
    body, mime = json_encode(geojson), 'application/json'
    
    if json_callback:
        body = '%s(%s);\n' % (json_callback, body)
        mime = 'text/javascript'
    
    return body, mime

def layer_features(layer, include_geom, offset=0, count=25):
    '''
    '''
    features = []

    defn = layer.GetLayerDefn()
    names = [defn.GetFieldDefn(i).name for i in range(defn.GetFieldCount())]
    
    # Skip leading features
    for skip in range(offset):
        layer.GetNextFeature()
    
    for feature in layer:
        # Stop reading features
        if len(features) == count:
            break
    
        properties = dict()
        
        for (index, name) in enumerate(names):
            properties[name] = feature.GetField(index)
        
        if not include_geom:
            features.append(dict(type='Feature', properties=properties, geometry=None))
            continue
        
        geometry = feature.GetGeometryRef()
        shape = wkb.loads(geometry.ExportToWkb())
        
        features.append(dict(type='Feature', properties=properties, geometry=shape.__geo_interface__))
    
    return features

def get_intersecting_features(datasource, geometry, include_geom):
    '''
    '''
    layer = datasource.GetLayer(0)
    layer.SetSpatialFilter(geometry)
    
    return layer_features(layer, include_geom)

def get_matching_features(datasource, where_clause, include_geom):
    '''
    '''
    layer = datasource.GetLayer(0)
    layer.SetAttributeFilter(where_clause)
    
    return layer_features(layer, include_geom)
