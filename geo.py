from shapely import wkb
from census import get_features as census_features, census_url

def get_intersecting_features(datasource, geometry, include_geom):
    '''
    '''
    if datasource == census_url:
        return census_features(geometry, include_geom)
    
    features = []

    layer = datasource.GetLayer(0)
    
    defn = layer.GetLayerDefn()
    names = [defn.GetFieldDefn(i).name for i in range(defn.GetFieldCount())]
    
    layer.SetSpatialFilter(geometry)
    
    for feature in layer:
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
