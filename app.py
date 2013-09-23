from sys import stderr
import json

from flask import Flask
from flask import request
from flask import Response
from osgeo import ogr

from geo import get_intersecting_features
from util import json_encode, bool

filenames = [
    ('Bay Area Census (2010-2013)', 'datasource.shp', None),
    ]

app = Flask(__name__)

@app.route('/')
def hello():
    with open('index.html') as index:
        return index.read()

@app.route("/areas")
def areas():
    lat = float(request.args['lat'])
    lon = float(request.args['lon'])

    include_geom = bool(request.args.get('include_geom', True))
    json_callback = request.args.get('callback', None)
    
    # This. Is. Python.
    ogr.UseExceptions()
    
    features = []
    point = ogr.Geometry(wkt='POINT(%f %f)' % (lon, lat))
    args = point, include_geom

    #
    # Look at four files in turn
    #
    for (dataname, shpname, zipname) in filenames:
        features += get_intersecting_features(ogr.Open(shpname), dataname, *args)

    geojson = dict(type='FeatureCollection', features=features)
    body, mime = json_encode(geojson), 'application/json'
    
    if json_callback:
        body = '%s(%s);\n' % (json_callback, body)
        mime = 'text/javascript'
    
    return Response(body, headers={'Content-type': mime})
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)