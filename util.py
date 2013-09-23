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

falsies = set(['f', 'false', 'n', 'no', '0'])

def bool(val):
    ''' Convert a value to boolean.
    
    >>> bool(True), bool(False)
    (True, False)

    >>> bool(1), bool(0)
    (True, False)

    >>> bool('1'), bool('0')
    (True, False)

    >>> bool('y'), bool('n')
    (True, False)

    >>> bool('t'), bool('f')
    (True, False)

    >>> bool('true'), bool('false')
    (True, False)

    >>> bool(99), bool('what')
    (True, True)
    '''
    return str(val).lower() not in falsies

if __name__ == '__main__':
    import doctest
    doctest.testmod()
