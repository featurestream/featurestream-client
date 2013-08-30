import re

# take a json event and transform it in some way
class Transform(object):

    def transform(self, event):
        return event

# 
class TransformPipeline(Transform):
    '''
    A transform that executes a pipeline of transforms.
    Created with an iterable of transforms
    '''
    
    transforms = None
    
    def __init__(self,transforms):
        for t in transforms:
            assert isinstance(t,Transform)
        self.transforms = transforms
    
    def transform(self, event):
        for t in self.transforms:
            event = t.transform(event)
        return event

'''
Transform an array into a json dict event using
an array of headers
'''
def array2json(array, headers=None):
    if headers is None:
        # numeric headers
        return dict((str(i),x) for i,x in enumerate(array))
    else:
        return dict((h,x) for h,x in zip(headers,array))

class ExtractFieldsTransform(Transform):
    '''
    Transforms an event by extracting fields according to a mapping.
    Example:
    
    mapping={
    "fields": [
        {"name": "retweet_count", "source": "[tweet][retweet][count]"},
        {"name": "gender", "source": "[demographics][gender]"}
    ]
    }
    
    event={'foo':'bar','tweet':{'retweet':{'foo':'barfoo', 'count':12},'fooby':19}, 'demographics':{'hello':'world', 'gender':'m'}}
    
    transform(event,mapping)={'gender': 'm', 'retweet_count': 12}
    '''
    mapping = None
    
    def __init__(self, mapping):
        self.mapping = mapping

    def transform(self, event):
        new_event = {}
        if 'fields' in self.mapping:
            fieldmaplist = self.mapping['fields']
            for fieldmap in fieldmaplist:
		k = fieldmap['name']
		if 'source' in fieldmap:
		    v = self.lookup(event,fieldmap['source'])
		else: # use k
			if k in event:
				v = event[k]
			else:
				v = None
                if v is not None:
                    new_event[k] = v
        return new_event

    def lookup(self,d,path):
        s=re.findall(r'\[(\w+)\]',path)
        try:
            for x in s:
                d=d[x]
            return d
        except KeyError:
            return None

class FilterTransform(Transform):

	fields = None
	
	def __init__(self,fields):
		self.fields = fields

	def transform(self, event):
		new_event = dict((k,event[k]) for k in self.fields if k in event)
		return new_event


