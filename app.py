from sys import stderr

from flask import Flask
from flask import request
from osgeo import ogr, osr
from shapely import wkb

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
    
    datasource = ogr.Open('gz_2010_06_140_00_500k/gz_2010_06_140_00_500k.shp')
    layer = datasource.GetLayer(0)
    point = ogr.Geometry(wkt='POINT(%f %f)' % (lon, lat))
    
    defn = layer.GetLayerDefn()
    names = [defn.GetFieldDefn(i).name for i in range(defn.GetFieldCount())]
    
    layer.SetSpatialFilter(point)
    
    for feature in layer:
        
        properties = dict()
        
        for (index, name) in enumerate(names):
            properties[name] = feature.GetField(index)
        
        geometry = feature.GetGeometryRef()
        shape = wkb.loads(geometry.ExportToWkb())

        feature.DumpReadable()
        print >> stderr, properties
        print >> stderr, shape.__geo_interface__
    
    return "hello %s" % point
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)