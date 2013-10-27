from sys import stderr
from os import environ
from urlparse import urlparse
from StringIO import StringIO
from zipfile import ZipFile, ZIP_DEFLATED
from time import time

from flask import Flask
from flask import request
from flask import Response
from flask import render_template
from osgeo import ogr

from util import json_encode, bool
from geo import get_intersecting_features, get_matching_features, features_geojson
from census import census_url, get_features as census_features

app = Flask(__name__)

def is_census_datasource(environ):
    ''' Return true if the environment specifies the U.S. Census datasource.
    '''
    return environ.get('GEO_DATASOURCE', None) == census_url

def get_datasource(environ):
    ''' Return an environment-appropriate datasource.
    
        For local data, this will be an OGR Datasource object.
    '''
    if is_census_datasource(environ):
        # Use the value of the environment variable directly,
        datasource = environ['GEO_DATASOURCE']
    
    else:
        # Or just open datasource.shp with OGR.
        datasource = ogr.Open('datasource.shp')
    
    return datasource

@app.route('/')
def hello():
    host_port = urlparse(request.base_url).netloc.encode('utf-8')
    is_downloadable = not is_census_datasource(environ)
    is_us_census = is_census_datasource(environ)
    
    return render_template('index.html', **locals())

@app.route('/.well-known/status')
def status():
    datasource = get_datasource(environ)
    
    status = {
        'status': 'ok' if bool(datasource) else 'Bad datasource: %s' % repr(datasource),
        'updated': int(time()),
        'dependencies': [],
        'resources': {}
        }

    body = json_encode(status)

    return Response(body, headers={'Content-type': 'application/json',
                                   'Access-Control-Allow-Origin': '*'})

@app.route("/areas")
def areas():
    ''' Retrieve geographic areas.
    '''
    is_census = is_census_datasource(environ)
    
    lat = float(request.args['lat'])
    lon = float(request.args['lon'])

    include_geom = bool(request.args.get('include_geom', True))
    json_callback = request.args.get('callback', None)

    layer_names = is_census and request.args.get('layers', '')
    layer_names = layer_names and set(layer_names.split(','))
    
    # This. Is. Python.
    ogr.UseExceptions()
    
    point = ogr.Geometry(wkt='POINT(%f %f)' % (lon, lat))

    if is_census:
        features = census_features(point, include_geom, layer_names)
    
    else:
        datasource = get_datasource(environ)
        features = get_intersecting_features(datasource, point, include_geom)
    
    geojson = dict(type='FeatureCollection', features=features)
    body, mime = json_encode(geojson), 'application/json'
    
    if json_callback:
        body = '%s(%s);\n' % (json_callback, body)
        mime = 'text/javascript'
    
    return Response(body, headers={'Content-type': mime, 'Access-Control-Allow-Origin': '*'})

@app.route('/select')
def select():
    ''' Retrieve features.
    '''
    if is_census_datasource(environ):
        error = "Can't select individual features from " + census_url
        return Response(render_template('error.html', error=error), status=404)

    where_clause = request.args.get('where', None)
    where_clause = where_clause and str(where_clause)
    
    page_number = int(request.args.get('page', 1))
    
    include_geom = bool(request.args.get('include_geom', True))
    json_callback = request.args.get('callback', None)

    # This. Is. Python.
    ogr.UseExceptions()
    
    datasource = get_datasource(environ)
    features = get_matching_features(datasource, where_clause, page_number, include_geom)
    body, mime = features_geojson(features, json_callback)
    
    return Response(body, headers={'Content-type': mime, 'Access-Control-Allow-Origin': '*'})

@app.errorhandler(404)
def error_404(error):
    return render_template('error.html', error=str(error))

@app.route('/datasource.zip')
def download_zip():
    if is_census_datasource(environ):
        error = "Can't download all of " + census_url
        return Response(render_template('error.html', error=error), status=404)
    
    buffer = StringIO()
    archive = ZipFile(buffer, 'w', ZIP_DEFLATED)
    archive.write('datasource.shp')
    archive.write('datasource.shx')
    archive.write('datasource.dbf')
    archive.write('datasource.prj')
    archive.close()
    
    return Response(buffer.getvalue(), headers={'Content-Type': 'application/zip'})
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)