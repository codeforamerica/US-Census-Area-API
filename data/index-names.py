''' Create one JSON index file per three-letter name prefix from local zip files.

Built for zip files of State, County, and Place geometries:

    curl -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/STATE/tl_2013_us_state.zip'
         -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/COUNTY/tl_2013_us_county.zip'
         -OL 'ftp://ftp.census.gov:21//geo/tiger/TIGER2013/PLACE/tl_2013_[01-99]_place.zip'
'''
from zipfile import ZipFile
from collections import defaultdict
from operator import itemgetter
from itertools import groupby
from glob import glob
from os import remove
from json import dump

from unidecode import unidecode
from osgeo import ogr

state_fips = {
    '01': 'Alabama',
    '02': 'Alaska',
    '04': 'Arizona',
    '05': 'Arkansas',
    '06': 'California',
    '08': 'Colorado',
    '09': 'Connecticut',
    '10': 'Delaware',
    '11': 'District of Columbia',
    '12': 'Florida',
    '13': 'Georgia',
    '15': 'Hawaii',
    '16': 'Idaho',
    '17': 'Illinois',
    '18': 'Indiana',
    '19': 'Iowa',
    '20': 'Kansas',
    '21': 'Kentucky',
    '22': 'Louisiana',
    '23': 'Maine',
    '24': 'Maryland',
    '25': 'Massachusetts',
    '26': 'Michigan',
    '27': 'Minnesota',
    '28': 'Mississippi',
    '29': 'Missouri',
    '30': 'Montana',
    '31': 'Nebraska',
    '32': 'Nevada',
    '33': 'New Hampshire',
    '34': 'New Jersey',
    '35': 'New Mexico',
    '36': 'New York',
    '37': 'North Carolina',
    '38': 'North Dakota',
    '39': 'Ohio',
    '40': 'Oklahoma',
    '41': 'Oregon',
    '42': 'Pennsylvania',
    '44': 'Rhode Island',
    '45': 'South Carolina',
    '46': 'South Dakota',
    '47': 'Tennessee',
    '48': 'Texas',
    '49': 'Utah',
    '50': 'Vermont',
    '51': 'Virginia',
    '53': 'Washington',
    '54': 'West Virginia',
    '55': 'Wisconsin',
    '56': 'Wyoming',
    '60': 'American Samoa',
    '64': 'Federated States of Micronesia',
    '66': 'Guam',
    '68': 'Marshall Islands',
    '69': 'Northern Mariana Islands',
    '70': 'Palau',
    '72': 'Puerto Rico',
    '74': 'U.S. Minor Outlying Islands',
    '78': 'Virgin Islands of the U.S.',
    }

if __name__ == '__main__':

    index = defaultdict(lambda: [])

    for zipname in glob('*.zip'):
        zipfile = ZipFile(zipname)
        
        types = ('.shp', '.shx', '.prj', '.dbf')
        names = [name for name in zipfile.namelist() if name[-4:] in types]
        
        zipfile.extractall(members=names)
        
        shpname = names[0][:-4] + '.shp'
        
        shp_ds = ogr.Open(shpname)
        layer = shp_ds.GetLayer(0)
        
        for feature in layer:
            if shpname == 'tl_2013_us_county.shp':
                name = feature.GetField('NAMELSAD').decode('latin-1')
            else:
                name = feature.GetField('NAME').decode('latin-1')
        
            geoid = feature.GetField('GEOID')
            name_ascii = unidecode(name)
            state = state_fips[geoid[:2]]
            
            key = name_ascii[:3].lower()
            index[key].append(dict(name=name, name_ascii=name_ascii,
                                   state=state, geoid=geoid, source=shpname))
            
            print key, name
            
        for ext in types:
            remove(shpname[:-4] + ext)
    
    for (key, content) in index.items():
        content.sort(key=itemgetter('name'))

        with open(key + '.json', 'w') as out:
            dump(content, out, indent=2)
