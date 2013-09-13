from sys import stderr

from flask import Flask
from flask import request
from osgeo import ogr, osr

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
    
    layer.SetSpatialFilter(point)
    
    output = []
    
    for feature in layer:
        feature.DumpReadable()
    
    return "hello %s" % point
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)