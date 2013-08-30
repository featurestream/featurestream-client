import featurestream as fs
import json,gzip
from featurestream.transform import ExtractFieldsTransform

file = 'retweets.gz'

mapping = {'fields': [
  {'name': 'content', 'source': '[interaction][content]'},
  {'name': 'sentiment', 'source': '[salience][content][sentiment]'},
  {'name': 'retweet-count', 'source': '[twitter][retweet][count]'},
  {'name': 'friends-count', 'source': '[twitter][retweet][user][friends_count]'},
  {'name': 'followers-count', 'source': '[twitter][retweet][user][followers_count]'},
  {'name': 'statuses-count', 'source': '[twitter][retweet][user][statuses_count]'}
]}

def train(stream, file):

	transform = ExtractFieldsTransform(mapping)
	with gzip.open(file, 'rb') as file_in:
		for event in file_in:
			try:
				training_data = transform.transform(json.loads(event))
				print training_data
				# from unicode, strip punctuation and go lowercase
				# (now done in stringtokenizer transformer on server)
#				s = string.lower(training_data['content'].encode('ascii','ignore'))
#				training_data['content'] = s.translate(string.maketrans("",""),string.punctuation)
				training_data['positive'] = '+' if training_data['sentiment'] >= 0 else '-'
				del training_data['sentiment'] # target leak			
				ok = stream.train(training_data)
				if not ok: break
			except KeyError:
				# either a tick or missing gender/content
				pass

stream = fs.start_stream('rf_classifier','positive')

print 'training from ',file
train(stream, file)

print 'getting stream info'
print stream.get_stats()
