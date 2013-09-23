from shapely import wkb

def get_intersecting_features(datasource, dataname, geometry):
    '''
    '''
    features = []

    layer = datasource.GetLayer(0)
    
    defn = layer.GetLayerDefn()
    names = [defn.GetFieldDefn(i).name for i in range(defn.GetFieldCount())]
    
    layer.SetSpatialFilter(geometry)
    
    for feature in layer:
        properties = dict(dataset=dataname)
        
        for (index, name) in enumerate(names):
            properties[name] = feature.GetField(index)
        
        geometry = feature.GetGeometryRef()
        shape = wkb.loads(geometry.ExportToWkb())
        
        features.append(dict(type='Feature', properties=properties, geometry=shape.__geo_interface__))
    
    return features
