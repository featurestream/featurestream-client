import featurestream as fs
import json,gzip
from featurestream.transform import ExtractFieldsTransform

filename = 'tweets.gz'

sentiment_pos = ["=)", "=D", ":)", "=P", ":P", "=]", ";)", ":-)"]
sentiment_neg = ["=(", ":-(", ":(", ":{", ":[", "={", "=["]

mapping = {'fields': [
  {'name': 'text', 'source': '[text]'},
  {'name': 'name', 'source': '[user][screen_name]'},
]}

def train(stream, filename):
	i=0
	transform = ExtractFieldsTransform(mapping)
	with gzip.open(filename, 'rb') as file_in:
		for line in file_in:
			try:
				event = transform.transform(json.loads(line))
				# from unicode, strip punctuation and go lowercase
				# (now done in stringtokenizer transformer on server)
#				s = string.lower(training_data['text'].encode('ascii','ignore'))
#				event['text'] = s.translate(string.maketrans("",""),string.punctuation)

				# add sentiment if exists
				pos = sum([c in event['text'] for c in sentiment_pos])
				neg = sum([c in event['text'] for c in sentiment_neg])
				if (pos + neg > 0):
					#event['sentiment'] = str(pos-neg)
					event['positive']='true' if pos > 0 else 'false'
				ok=stream.train(event)
				if not ok: break
				i+=1
				if (i%1000==0): print i
			except KeyError:
				pass

stream = fs.start_stream(learner='rf_classifier',target='positive')
print 'got stream_id =',stream.stream_id

print 'training from ',filename
train(stream, filename)

print 'getting stream info'
print stream.get_stats()

stream.close()
