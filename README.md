US Census Area API
==================

Simple geospatial API for U.S. Census and other data sources, in response to the
[Census Area API hack request](https://github.com/codeforamerica/hack-requests/blob/master/census-area-API.md).

This application can be run in two distinct ways. When the environment variable `GEO_DATASOURCE=http://forever.codeforamerica.org/Census-API/` is present, the API will serve nationwide U.S. Census geographies from the state to block level. See this in action at [census.codeforamerica.org](http://census.codeforamerica.org) and use it freely.

Otherwise, it will use a local OGR-compatible datasource such as a shapefile or GeoJSON to serve any data and make it available for download. A sample copy with Bay Area Census data can be found at
[census-api-bay-area.herokuapp.com](http://census-api-bay-area.herokuapp.com).

Installing
----

This is a [Flask](http://flask.pocoo.org/)-based Python application which
requires compiled geospatial libraries [Shapely](http://toblerity.org/shapely/)
and [GDAL](http://trac.osgeo.org/gdal/) to run. Directions here assume that you have an OGR-compatible datasource you’d like to use.

### Test Locally

1. Download and unpack [sample Bay Area data](http://forever.codeforamerica.org.s3.amazonaws.com/Census-API/bay-area-data.zip).
2. Ensure that *datasource.shp* and other files are located in the same directory as *app.py*.
3. Call `python app.py` for a test server.

### Run Locally with Gunicorn

To run a more robust installation using the Python WSGI HTTP server
[Gunicorn](http://gunicorn.org/), prepare local data as in steps 1 & 2 above,
then call:

    gunicorn app:app

### Run on Heroku

Compiled geospatial libraries for Heroku are available via the
[open source GIS Heroku buildpack](https://github.com/codeforamerica/heroku-buildpack-pygeo). Create a new Heroku app with this buildpack:

    heroku create --buildpack https://github.com/codeforamerica/heroku-buildpack-pygeo

There are two possible ways to run the API on Heroku:

1. Fork this repository, download and commit your own data as *datasource.shp*,
and push the combined application + data repository to Heroku.

2. Use the `ZIPPED_DATA_URL` support in *heroku-buildpack-pygeo* to configure
a remote zip file such as *bay-area-data.zip* (URL linked above),
**making sure to install the Heroku plugin**
[user-env-compile](https://devcenter.heroku.com/articles/labs-user-env-compile).
Data will be automatically retrieved and expanded to *datasource.shp* at
compile time.
