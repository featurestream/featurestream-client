from __future__ import absolute_import
import arff # pip install liac-arff
import gzip

def arff2json(filename): 

    if filename.endswith('.gz'):
        f=gzip.open(filename,'rb')
    else:
        f=open(filename,'rb')
        
    data = arff.load(f)

    # see https://pypi.python.org/pypi/liac-arff/1.1
    for record in data['data']:
        if not record:
            continue
        event = {}
        for i,attr in enumerate(data['attributes']):
            event.update({attr[0]:record[i]})

        yield event

def arff_iterator(filename, missing_values=['none','nan','na','n/a','','?','??','???','none or unspecified','unspecified','unknown']):

    return arff2json(filename)
