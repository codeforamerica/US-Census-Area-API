from sys import stderr
from os import environ
from urlparse import urlparse
import json

from flask import Flask
from flask import request
from flask import Response
from osgeo import ogr

from geo import get_intersecting_features
from util import json_encode, bool
from census import census_url

app = Flask(__name__)

@app.route('/')
def hello():
    host_port = urlparse(request.base_url).netloc.encode('utf-8')

    with open('index.html') as index:
        return index.read().replace('host:port', host_port)

@app.route("/areas")
def areas():
    lat = float(request.args['lat'])
    lon = float(request.args['lon'])

    include_geom = bool(request.args.get('include_geom', True))
    json_callback = request.args.get('callback', None)
    
    # This. Is. Python.
    ogr.UseExceptions()
    
    if environ.get('GEO_DATASOURCE', None) == census_url:
        #
        # Use the value of the environment variable directly,
        # get_intersecting_features() knows about census_url.
        #
        datasource = environ['GEO_DATASOURCE']
    
    else:
        # Or just open datasource.shp with OGR.
        datasource = ogr.Open('datasource.shp')
    
    point = ogr.Geometry(wkt='POINT(%f %f)' % (lon, lat))
    features = get_intersecting_features(datasource, point, include_geom)

    geojson = dict(type='FeatureCollection', features=features)
    body, mime = json_encode(geojson), 'application/json'
    
    if json_callback:
        body = '%s(%s);\n' % (json_callback, body)
        mime = 'text/javascript'
    
    return Response(body, headers={'Content-type': mime, 'Access-Control-Allow-Origin': '*'})
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)