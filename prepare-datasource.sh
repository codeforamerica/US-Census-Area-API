#!/usr/bin/env tcsh -ex

#
# All original source files below originate from
# ftp://ftp.census.gov:21//geo/tiger/TIGER2013/
#

#
# Large areas clipped to:
# http://www.openstreetmap.org/?box=yes&bbox=-123.060%2C38.902%2C-121.131%2C36.815
#

ogr2ogr -sql "SELECT STATEFP, '' AS COUNTYFP, CAST(GEOID AS character(16)), NAME, MTFCC, ALAND, AWATER, INTPTLAT, INTPTLON, 'tl_2013_us_state' AS table FROM tl_2013_us_state" \
    -spat -123.060 36.815 -121.131 38.902 \
    -overwrite tl_2013_us_state/tl_2013_us_state{-smush,}.shp

ogr2ogr -sql "SELECT STATEFP, '' AS COUNTYFP, CAST(GEOID AS character(16)), NAME, MTFCC, ALAND, AWATER, INTPTLAT, INTPTLON, 'tl_2013_06_place' AS table FROM tl_2013_06_place" \
    -spat -123.060 36.815 -121.131 38.902 \
    -overwrite tl_2013_06_place/tl_2013_06_place{-smush,}.shp

ogr2ogr -sql "SELECT STATEFP, COUNTYFP, CAST(GEOID AS character(16)), NAME, MTFCC, ALAND, AWATER, INTPTLAT, INTPTLON, 'tl_2013_us_county' AS table FROM tl_2013_us_county" \
    -spat -123.060 36.815 -121.131 38.902 \
    -overwrite tl_2013_us_county/tl_2013_us_county{-smush,}.shp

ogr2ogr -sql "SELECT '' AS STATEFP, '' AS COUNTYFP, CAST(GEOID10 AS character(16)) AS GEOID, '' AS NAME, MTFCC10 AS MTFCC, ALAND10 AS ALAND, AWATER10 AS AWATER, INTPTLAT10 AS INTPTLAT, INTPTLON10 AS INTPTLON, 'tl_2013_us_zcta510' AS table FROM tl_2013_us_zcta510" \
    -spat -123.060 36.815 -121.131 38.902 \
    -overwrite tl_2013_us_zcta510/tl_2013_us_zcta510{-smush,}.shp

#
# Small areas clipped to:
# http://www.openstreetmap.org/?box=yes&bbox=-122.535%2C37.936%2C-122.076%2C37.667
#

ogr2ogr -sql "SELECT STATEFP, COUNTYFP, CAST(GEOID AS character(16)), NAME, MTFCC, ALAND, AWATER, INTPTLAT, INTPTLON, 'tl_2013_06_tract' AS table FROM tl_2013_06_tract" \
    -spat -122.535 37.667 -122.076 37.936 \
    -overwrite tl_2013_06_tract/tl_2013_06_tract{-smush,}.shp

ogr2ogr -sql "SELECT STATEFP, COUNTYFP, CAST(GEOID AS character(16)), NAMELSAD AS NAME, MTFCC, ALAND, AWATER, INTPTLAT, INTPTLON, 'tl_2013_06_bg' AS table FROM tl_2013_06_bg" \
    -spat -122.535 37.667 -122.076 37.936 \
    -overwrite tl_2013_06_bg/tl_2013_06_bg{-smush,}.shp

ogr2ogr -sql "SELECT STATEFP, COUNTYFP, CAST(GEOID AS character(16)), '' AS NAMELSAD, MTFCC, ALAND, AWATER, INTPTLAT, INTPTLON, 'tl_2013_06_tabblock' AS table FROM tl_2013_06_tabblock" \
    -spat -122.535 37.667 -122.076 37.936 \
    -overwrite tl_2013_06_tabblock/tl_2013_06_tabblock{-smush,}.shp

#
# Final output to bay-area-census Shapefile.
#

ogr2ogr -overwrite -t_srs EPSG:4326 bay-area-census.shp tl_2013_us_state/tl_2013_us_state-smush.shp
ogr2ogr -append -update -t_srs EPSG:4326 bay-area-census.shp tl_2013_us_county/tl_2013_us_county-smush.shp
ogr2ogr -append -update -t_srs EPSG:4326 bay-area-census.shp tl_2013_06_place/tl_2013_06_place-smush.shp
ogr2ogr -append -update -t_srs EPSG:4326 bay-area-census.shp tl_2013_06_tract/tl_2013_06_tract-smush.shp
ogr2ogr -append -update -t_srs EPSG:4326 bay-area-census.shp tl_2013_06_bg/tl_2013_06_bg-smush.shp
ogr2ogr -append -update -t_srs EPSG:4326 bay-area-census.shp tl_2013_06_tabblock/tl_2013_06_tabblock-smush.shp
ogr2ogr -append -update -t_srs EPSG:4326 bay-area-census.shp tl_2013_us_zcta510/tl_2013_us_zcta510-smush.shp

rm -f bay-area-census.zip && zip -j bay-area-census.zip bay-area-census.{shp,shx,dbf,prj}
