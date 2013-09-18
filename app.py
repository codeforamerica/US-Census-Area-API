from sys import stderr
from zipfile import ZipFile
import json

from flask import Flask
from flask import request
from osgeo import ogr, osr
from shapely import wkb

filenames = [
    ('Bay Area Census (2010-2013)', 'datasource.shp', None),
    ]


app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hi there'

@app.route("/areas")
def areas():
    lat = float(request.args['lat'])
    lon = float(request.args['lon'])
    
    # This. Is. Python.
    ogr.UseExceptions()
    
    features = []
    point = ogr.Geometry(wkt='POINT(%f %f)' % (lon, lat))

    #
    # Look at four files in turn
    #
    for (dataname, shpname, zipname) in filenames:
        datasource = ogr.Open(shpname)
        layer = datasource.GetLayer(0)
        
        defn = layer.GetLayerDefn()
        names = [defn.GetFieldDefn(i).name for i in range(defn.GetFieldCount())]
        
        layer.SetSpatialFilter(point)
        
        for feature in layer:
            properties = dict(dataset=dataname)
            
            for (index, name) in enumerate(names):
                properties[name] = feature.GetField(index)
            
            geometry = feature.GetGeometryRef()
            shape = wkb.loads(geometry.ExportToWkb())
            
            features.append(dict(type='Feature', properties=properties, geometry=shape.__geo_interface__))

    geojson = dict(type='FeatureCollection', features=features)
    return json.dumps(geojson)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)