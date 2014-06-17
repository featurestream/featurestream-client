from __future__ import absolute_import
from collections import defaultdict
from csv import Sniffer,DictReader,reader
import gzip

def csv2json(filename, has_header, headers, dialect, missing_values,types):
	if filename.endswith('.gz'):
		csvfile=gzip.open(filename,'rb')
	else:
		csvfile=open(filename,'rb')

	reader = DictReader(csvfile,fieldnames=headers, dialect=dialect)
	if has_header:
		reader.next()
	for row in reader:
		# try to convert all numbers 
		# filter out missing cells
		event = dict([(k,convert(k,v,types)) for k,v in row.iteritems() if (v is not None) and (v.lower() not in missing_values)])
		yield event
	csvfile.close()

def convert(k,v,types):
	return float(v) if (types[k]==0) else v

def is_number(v):
	try:
		float(v)
		return True
	except ValueError:
		return False

def guesstypes(filename, has_header, headers, dialect, missing_values):
	print 'guessing types..'
	if filename.endswith('.gz'):
		csvfile=gzip.open(filename,'rb')
	else:
		csvfile=open(filename,'rb')

	reader = DictReader(csvfile,fieldnames=headers, dialect=dialect)
	if has_header:
		reader.next()
	types=defaultdict(int) # 0 = numeric, 1 = categoric
#		values=defaultdict(set)
	line=0
	for row in reader:
		for k,v	in row.iteritems():
			if (v is not None) and (v.lower() not in missing_values):
				if not is_number(v):
					types[k]=1
		line+=1
		if line>1000: break
#						values[k].add(v)
	csvfile.close()
	return types

def getheaders_dialect(filename):
	if filename.endswith('.gz'):
		csvfile=gzip.open(filename,'rb')
	else:
		csvfile=open(filename,'rb')

	sample = csvfile.read(2000)
	dialect = Sniffer().sniff(sample)
	csvfile.seek(0)
	reader_=reader(csvfile,dialect)
	row=reader_.next()
	csvfile.seek(0)
	has_header = Sniffer().has_header(sample)
	if (not has_header):
		# no header line detected, use 0,1,2,... as header names
		headers = [str(i) for i in range(len(row))]
	else:
		headers = row
	csvfile.close()

	return has_header,headers,dialect

def csv_iterator(filename, types={}, missing_values=['none','nan','na','n/a','','?','??','???','none or unspecified','unspecified','unknown']):
	types_ = types
	has_header,headers,dialect=getheaders_dialect(filename)
	if len(types_) == 0:
		types=guesstypes(filename,has_header,headers,dialect,missing_values)
	else:
		types = defaultdict(int)
		for h in headers:
			if h in types_:
				if types_[h] == 1:
					types[h]=1
				else:
					types[h]=0
	typemap = {0:'NUMERIC',1:'CATEGORIC'}
	print 'types=',map(lambda h:(h,typemap[types[h]]),headers)

	return csv2json(filename,has_header,headers,dialect,missing_values,types)

def fill_csv_blanks(fs, filename, types={}, missing_values=['none','nan','na','n/a','','?','??','???','none or unspecified','unspecified','unknown']):
    # redo work to get types
    types_ = types
    has_header,headers,dialect=getheaders_dialect(filename)
    if len(types_) == 0:
      types=guesstypes(filename,has_header,headers,dialect,missing_values)
    else:
      types = defaultdict(int)
      for h in headers:
        if h in types_:
          if types_[h] == 1:
            types[h]=1
          else:
            types[h]=0
    typemap = {0:'NUMERIC',1:'CATEGORIC'}
    has_header,headers,dialect = getheaders_dialect(filename)
    # create stream
    print 'building model..'
    stream = fs.start_stream(targets = dict(map(lambda h:(h,typemap[types[h]]), headers)))
    # create iterator
    it = csv_iterator(filename,types,missing_values)
    events = list(it)
    # train
    stream.train_batch(events)
    # fill missing cells
    print 'new rows..'
    print headers
    for e in events: 
      pred = stream.predict(e)
      row = map(lambda h:(str(e[h])+'(pred:'+str(pred[h])+')' if h in e else pred[h]), headers)
      # write out the predicted row
      print row
    
        
    
