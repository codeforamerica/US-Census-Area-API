from sys import stderr
from zipfile import ZipFile
from os import chdir, getcwd
import json

from flask import Flask
from flask import request
from osgeo import ogr, osr
from shapely import wkb

filenames = [
    ('Census Counties (2010)', 'gz_2010_us_050_00_500k/gz_2010_us_050_00_500k.shp', 'gz_2010_us_050_00_500k.zip'),
    ('Congressional Districts (113th)', 'cb_rd13_us_cd113_500k/cb_rd13_us_cd113_500k.shp', 'cb_rd13_us_cd113_500k.zip'),
    ('Census Places (2010)', 'gz_2010_06_160_00_500k/gz_2010_06_160_00_500k.shp', 'gz_2010_06_160_00_500k.zip'),
    ('Census Tracts (2010)', 'gz_2010_06_140_00_500k/gz_2010_06_140_00_500k.shp', 'gz_2010_06_140_00_500k.zip'),
    ]
zipdir = getcwd()
chdir('/tmp')

for (dataname, shpname, zipname) in filenames:
    zippath = zipdir + '/' +zipname
    print >> stderr, 'extracting', zippath, 'in', getcwd()
    ZipFile(zippath).extractall()

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