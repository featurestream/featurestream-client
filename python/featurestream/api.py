import zlib
import json,requests,time
from requests import ConnectionError
from async import AsyncTrainer
from transform import Transform

def to_full_event(event,types={}):
	'''
	 converts a simple {name:value} list to a full event to be posted
	'''
	data=[]
	try_decode = False
	for key,value in event.iteritems():
		if try_decode:
			try:
				key = key.decode()
				value = value.decode()
			except UnicodeDecodeError:
				continue

		if key in types:
			data.append({'name':key,'value':value, 'type':types[key]})
		else:
			data.append({'name':key,'value':value})
		if '_' in key:
			print 'error: character _ not allowed in field names. Event name=',key

	full_event = {'timestamp':int(time.time()*1000000), 'data':data}
	return full_event

class Stream(object):
	stream_id = None
	endpoint = ''
	session = None
	targets = None
	
	def __init__(self, stream_id, targets, endpoint, cookies):
		self.targets = targets
		self.endpoint = endpoint
		self.stream_id = stream_id
		self.session = requests.Session()
		# set any cookies
		if (cookies is not None):
			self.session.cookies = cookies

	def __repr__(self):
		return 'Stream[stream_id='+str(self.stream_id)+', targets='+str(self.targets)+', endpoint='+self.endpoint+']'

	def close(self):
		'''
		 GET /{stream_id}/stop_stream
		 close the stream
		'''
		r=self.session.get(self.endpoint+'/'+str(self.stream_id)+'/stop_stream')
		if (r.status_code != 200):
			print 'error:',r.text
			return False

		self.session.close()
		return True

	def checkpoint(self):
		'''
		 GET /{stream_id}/checkpoint
		 checkpoint the stream
		'''
		r=self.session.get(self.endpoint+'/'+str(self.stream_id)+'/checkpoint')
		if (r.status_code != 200):
			print 'error:',r.text
			return False

		return True

	def train_batch(self, events, types={}):
		'''
		 POST /{stream_id}/train_batch
		 train on an list of events
		'''
		full_events=[to_full_event(event,types) for event in events]
		data = zlib.compress(json.dumps(full_events))
		r=self.session.post(self.endpoint+'/'+str(self.stream_id)+'/train_batch',data=data,headers={'Content-type': 'application/json'},timeout=30)
		if (r.status_code != 200):
			print 'error:',r.text
			return False
		return True

	def train(self, event, types={}):
#		print 'session cookies=',self.session.cookies
		'''
		 POST /{stream_id}/train
		 train on an event
		 event: event as a JSON list of {name:value} pairs
		 if the value has quotes then it is taken to be a categoric (discrete) attribute
		 otherwise it is parsed as a number and taken to be a numeric (continuous) attribute
		 types: optionally specify a map from names to types 
		 where type is one of {NUMERIC,CATEGORIC,DATETIME,TEXT} 
		 Example: 
		 [{'size':12},{'anomaly':'true'},...]
		 In the above there are 2 attributes: size (numeric) and anomaly (categoric) 
		 returns True if event accepted
		'''
		full_event = to_full_event(event,types)
		data = json.dumps(full_event)
		r=self.session.post(self.endpoint+'/'+str(self.stream_id)+'/train',data=data,headers={'Content-type': 'application/json'},timeout=30)
		if (r.status_code != 200):
			print 'error:',r.text
			return False
		return True
	
	def train_iterator(self, it, async=True, types={}, trans=Transform(), batch=100):
		'''
		 trains over the events yielded by the given iterator, 
		 applying the given transformation to each event.
		 if asynchronous=True (default), returns an AsyncTrainer object that can be used
 		 to monitor the progress.
		 batch is the batch size to use
 		 if async=False, blocks until the iterator has no more events
		'''
		if (batch<1):
			print 'error: batch cannot be < 1'
			return False
		if not it:
			print 'warning: empty iterator passed'
			return True

		transformed_it = (trans.transform(x) for x in it)
		if async:
			load_thread = AsyncTrainer(self, transformed_it, types, batch)
			load_thread.start()
			return load_thread
		else:
			events = []
			for event in transformed_it:
				events.append(event)
				if (len(events)>=batch):
					self.train_batch(events,types)
					events = []
			if (len(events)>0):
				return self.train_batch(events,types)
			return True

	def predict(self, event, predict_full=False, types={}):
		'''
		 POST /{stream_id}/predict
		 predict the target fields from the event
		 payload is the event to predict with
		 returns a prediction JSON object with 'prediction' field
		'''
		full_event = to_full_event(event,types)
		data = json.dumps(full_event)
		params = {'predict_full':predict_full}
		r=self.session.post(self.endpoint+'/'+str(self.stream_id)+'/predict',params=params,data=data,headers={'Content-type': 'application/json'})
		if (r.status_code != 200):
			print 'error:',r.text
			return
		return r.json()
	
	def predict_full(self, event, types={}):
		res = self.predict(event, predict_full=True, types=types)
		# add anomaly value if targets present
#		for t in self.targets:
#			if t in event and t in res:
#				res[t]['anomaly']=sum([y for (x,y) in res[t]['prediction'].items() if x!=event[t]])
		return res

	def transform(self, event, types={}):
		'''
		 POST /{stream_id}/transform
		 transform the event using whatever internal representation the learner uses
		 not all learners support this method
		 teturns a vector
		'''
		full_event = to_full_event(event,types)
		r=self.session.post(self.endpoint+'/'+str(self.stream_id)+'/transform',data=json.dumps(full_event),headers={'Content-type': 'application/json'})
		if (r.status_code != 200):
			print 'error:',r.text
			return
		return r.json()

	def get_info(self):
		'''
		 GET /{stream_id}/get_info
		 gets info about the current stream
		 returns a stats JSON object
		'''
		r=self.session.get(self.endpoint+'/'+str(self.stream_id)+'/get_info')
		if (r.status_code != 200):
			print 'error:',r.text
			return

		return r.json()

	def get_schema(self):
		'''
		 GET /{stream_id}/get_schema
		 gets schema for the current stream
		 returns a stats JSON object
		'''
		r=self.session.get(self.endpoint+'/'+str(self.stream_id)+'/get_schema')
		if (r.status_code != 200):
			print 'error:',r.text
			return

		return r.json()

	def get_stats(self, key=None, start=None, end=None):
		'''
		 GET /{stream_id}/get_stats
		 gets stats about the current stream
		 returns two lists: the first is ticks, the second stats) (tick is currently #instances trained)
		 params:
		 key - the key to query for (if not present, returns a list of keys)
		 start - start tick, inclusive, -1 or None denotes earliest possible
		 end - end tick, exclusive, -1 or None denotes latest possible
		 except if start,end are both None, returns only the latest stat
		TODO is this what we want? if start,end are both None then we get a list of length 1, not a value
		'''
		params={'key':key,'start':start,'end':end}
		r=self.session.get(self.endpoint+'/'+str(self.stream_id)+'/get_stats', params=params)
		if (r.status_code != 200):
			print 'error:',r.text
			return

		X = r.json()
		if key is None: # returns a list of keys
			return X
		elif start is None and end is None and len(X)==1:
			# special case
			return X.values()[0]
		else:
			# sort by increasing key as jsonification messes this up
			X = map(lambda (k,v):[int(k),v],X.iteritems())
			X.sort(key=lambda (k,v):k)
			return [x[0] for x in X], [x[1] for x in X]

	def clear_stats(self):
		'''
		 GET /{stream_id}/clear_stats
		 clears stats about the current stream
		'''
		r=self.session.get(self.endpoint+'/'+str(self.stream_id)+'/clear_stats')
		if (r.status_code != 200):
			print 'error:',r.text

	def related_fields(self, target, k=5):
		'''
		 GET /{stream_id}/related_fields
		 returns the k variables most related to the target variable, ordered by decreasing relevance
		 if k=-1, return all variables
		'''
		params={'target':target}
		r=self.session.get(self.endpoint+'/'+str(self.stream_id)+'/related_fields',params=params)
		if (r.status_code != 200):
			print 'error:',r.text
			return
		features = r.json()
		# extract top k
		top_features = sorted(features.items(), key=lambda (x,y):y, reverse=True)[:k]
		return top_features

ACCESS = "your_access_key"
ENDPOINT = 'http://api.featurestream.io:8088/api'

def set_endpoint(endpoint):
	global ENDPOINT
	ENDPOINT = endpoint
	print 'set endpoint to',ENDPOINT

def set_access(access):
	global ACCESS
	ACCESS = access
	print 'set access key to',ACCESS

def check_health(endpoint=None):
	if endpoint is None:
		endpoint = ENDPOINT
	try:
		r=requests.get(endpoint+'/health')
		return (r.status_code == 200)
	except ConnectionError:
		return False

def get_streams(access=None, endpoint=None):
	if access is None:
		access = ACCESS
	if endpoint is None:
		endpoint = ENDPOINT
	params={'access':access}
	r=requests.get(endpoint+'/get_streams',params=params)
	if (r.status_code != 200):
		print 'error:',r.text
		return;
	return r.json()

def get_stream(stream_id, endpoint=None):
	'''
	 GET /{stream_id}/get_stream
	 get existing stream details
	 params: stream_id
	 returns stream object
	'''
	if endpoint is None:
		endpoint = ENDPOINT
	params={}
	r=requests.get(endpoint+'/'+str(stream_id)+'/get_stream',params=params)
	cookies = r.cookies
	if (r.status_code != 200):
		print 'error:',r.text
		return;
	j = r.json()
	targets = j['targets']

	return Stream(stream_id, targets, endpoint, cookies)

def start_stream(targets={}, access=None, endpoint=None):
	'''
	 POST /start_stream
	 start a new stream
	 params: 
	 access = access key
	 body:
	 targets = map from targets to types, eg {'value':'NUMERIC', 'spam':'CATEGORIC'}
	 returns streamId
	'''
	if access is None:
		access = ACCESS
	if endpoint is None:
		endpoint = ENDPOINT

	if (not check_health(endpoint)):
		print 'error: service health check failed - please contact help@featurestream.io or try later'
		return

	# remap targets list to longer form
	full_targets = []
	for target,target_type in targets.items():
		full_targets.append({'name':target,'type':target_type})
    
	params={'access':access}
	r=requests.post(endpoint+'/start_stream',params=params,data=json.dumps(full_targets),headers={'Content-type': 'application/json'})
	cookies = r.cookies
	if (r.status_code != 200):
		print 'error:',r.text
		return;
	j=r.json()
	stream_id = j['streamId']

	return Stream(stream_id, targets, endpoint, cookies)
