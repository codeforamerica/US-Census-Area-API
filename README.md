US Census Area API
==================

Simple geospatial API for US Census, in response to the
[Census Area API hack request](https://github.com/codeforamerica/hack-requests/blob/master/census-area-API.md)

Installing
----

This is a Flask-based Python application which requires compiled
geospatial libraries Shapely and GDAL to run, available via the
[open source GIS Heroku buildpack](https://github.com/codeforamerica/heroku-buildpack-pygeo).

Sample data local to San Francisco is included, and will be expanded
to include the complete United States.

To run, call `python app.py` or see the sample gunicorn command in `Procfile`.
