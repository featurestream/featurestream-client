import json,requests,time
from async import AsyncTrainer
from transform import Transform

def to_full_event(event,types={}):
	'''
	 converts a simple {name:value} list to a full event to be posted
	'''
	data=[]
	for key,value in event.iteritems():
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
	learner = None
	target = None
	
	def __init__(self, stream_id, learner, target, endpoint):
		self.learner = learner
		self.target = target
		self.endpoint = endpoint
		self.stream_id = stream_id
		self.session = requests.Session()

	def __repr__(self):
		return 'Stream[stream_id='+str(self.stream_id)+', learner='+self.learner+', target='+self.target+', endpoint='+self.endpoint+']'

	def close(self):
		'''
		 GET /{stream_id}/stop_stream
		 close the stream
		'''
		r=self.session.get(self.endpoint+'/'+str(self.stream_id)+'/stop_stream')
		if (r.status_code != 200):
			print 'error:',r.text
			return

		self.session.close()
		return True

	def train_batch(self, events, types={}):
		'''
		 POST /{stream_id}/train_batch
		 train on an list of events
		'''
		full_events=[to_full_event(event,types) for event in events]
		r=self.session.post(self.endpoint+'/'+str(self.stream_id)+'/train_batch',data=json.dumps(full_events),headers={'Content-type': 'application/json'},timeout=30)
		if (r.status_code != 200):
			print 'error:',r.text
			return False
		return True

	def train(self, event, types={}):
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
		r=self.session.post(self.endpoint+'/'+str(self.stream_id)+'/train',data=json.dumps(full_event),headers={'Content-type': 'application/json'},timeout=30)
		if (r.status_code != 200):
			print 'error:',r.text
			return False
		return True
	
	def train_iterator(self, it, async=True, trans=Transform(), batch=100):
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

		transformed_it = (trans.transform(x) for x in it)
		if async:
			load_thread = AsyncTrainer(self, transformed_it, batch)
			load_thread.start()
			return load_thread
		else:
			events = []
			for event in transformed_it:
				events.append(event)
				if (len(events)>=batch):
					self.train_batch(events)
					events = []
			if (len(events)>0):
				self.train_batch(events)

	def predict(self, event, types={}):
		'''
		 POST /{stream_id}/predict
		 predict the target field from the event
		 payload is the event to predict with
		 returns a prediction JSON object with 'prediction' field
		'''
		full_event = to_full_event(event,types)
		r=self.session.post(self.endpoint+'/'+str(self.stream_id)+'/predict',data=json.dumps(full_event),headers={'Content-type': 'application/json'})
		if (r.status_code != 200):
			print 'error:',r.text
			return
		return r.json()
	
	def predict_full(self, event, types={}):
		'''
		 POST /{stream_id}/predict_full
		 predict the target field from the event
		 payload is the event to predict with
		 returns a prediction JSON object with 'prediction' field, which is usually a vector or map
		'''
		full_event = to_full_event(event,types)
		r=self.session.post(self.endpoint+'/'+str(self.stream_id)+'/predict_full',data=json.dumps(full_event),headers={'Content-type': 'application/json'})
		if (r.status_code != 200):
			print 'error:',r.text
			return
		res= r.json()
		# add anomaly value if target present
		if self.target in event:
			res['anomaly']=sum([y for (x,y) in res['prediction'].items() if x!=event[self.target]])
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
			

	def check(self):
		# do some checks
		stats = self.info()
		# 1) target leak: if feature_importances==feature_importances_full and |feature_importances|==1
		if 'feature_importances' in stats:
			fi=stats['feature_importances'].keys()
			fi_full=stats['feature_importances_full'].keys()
			if len(fi)==1 and fi[0]==fi_full[0]:
				print 'possible feature leak:',fi[0]

class ClusteringStream(Stream):

	def __init__(self, stream_id, endpoint):
		super(ClusteringStream, self).__init__(stream_id, 'clustering', None, endpoint)
	
	def __repr__(self):
		return 'MungiClusteringStream[stream_id='+str(self.stream_id)+', learner='+self.learner+', endpoint='+self.endpoint+']'

	def get_clusters(self,k=None):
		'''
		 GET /{stream_id}/clustering/get_clusters
		 gets k centroids
		 params: 
		 k: number of centroids to return, if not specified, returns all the current centroids
		'''
		params={'k':k}
		r=self.session.get(self.endpoint+'/'+str(self.stream_id)+'/clustering/get_clusters',params=params)
		if (r.status_code != 200):
			print 'error:',r.text
			return;
		return r.json()
	
	def closest_centroid(self, event, types={}):
		'''
		 POST /{stream_id}/clustering/closest_centroid
		 returns the closest centroid to the given point
		'''
		full_event = to_full_event(event,types)
		r=self.session.post(self.endpoint+'/'+str(self.stream_id)+'/clustering/closest_centroid',data=json.dumps(full_event),headers={'Content-type': 'application/json'})
		if (r.status_code != 200):
			print 'error:',r.text
			return
		return r.json()

ACCESS = "your_access_key"
ENDPOINT = 'http://107.22.187.28:8088/mungio/api'

def set_endpoint(endpoint):
	global ENDPOINT
	ENDPOINT = endpoint
	print 'set endpoint to',ENDPOINT

def set_access(access):
	global ACCESS
	ACCESS = access
	print 'set access key to',ACCESS

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
	if (r.status_code != 200):
		print 'error:',r.text
		return;
	j = r.json()
	learner = j['learnerType']
	target = j['target']

	return _get_stream_obj(stream_id, learner, target, endpoint)

def _get_stream_obj(stream_id, learner, target, endpoint):
	if learner == 'clustering':
		return ClusteringStream(stream_id, endpoint)
	else:
		return Stream(stream_id, learner, target, endpoint)
	
def start_stream(learner=None, target=None, access=None, endpoint=None):
	'''
	 GET /start_stream
	 start a new stream
	 params: 
	 target = target attribute to predict
	 access = access key
	 learner = {rf_classifier,rf_regressor, etc.}
	 returns streamId
	'''
	if access is None:
		access = ACCESS
	if endpoint is None:
		endpoint = ENDPOINT
	params={'target':target,'learner':learner,'access':access}
	print 'starting stream with params =', params
	r=requests.get(endpoint+'/start_stream',params=params)
	if (r.status_code != 200):
		print 'error:',r.text
		return;
	j=r.json()
	stream_id = j['streamId']

	return _get_stream_obj(stream_id, learner, target, endpoint)
