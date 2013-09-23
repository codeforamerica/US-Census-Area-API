from StringIO import StringIO
from json import JSONEncoder
from re import compile

float_pat = compile(r'^-?\d+\.\d+(e-?\d+)?$')
charfloat_pat = compile(r'^[\[,\,]-?\d+\.\d+(e-?\d+)?$')

def json_encode(data):
    ''' Encode stream of JSON with 7-digits floating point precision.
    '''
    encoder = JSONEncoder(separators=(',', ':'))
    encoded = encoder.iterencode(data)
    output = StringIO()
    
    for token in encoded:
        if charfloat_pat.match(token):
            # in python 2.7, we see a character followed by a float literal
            output.write(token[0] + '%.7f' % float(token[1:]))
        
        elif float_pat.match(token):
            # in python 2.6, we see a simple float literal
            output.write('%.7f' % float(token))
            
        else:
            output.write(token)
    
    return output.getvalue()
