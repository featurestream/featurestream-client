import featurestream as fs
import json,string
from featurestream import transform
import sys

filename = sys.argv[1]

def extract_hashtags(s):
	return set(part[1:] for part in s.split() if part.startswith('#'))

def train(stream, filename):
	i=0
	with open(filename, 'rb') as file_in:
		for line in file_in:
			try:
				tweet = json.loads(line)
				text = tweet['text']
				print text
				hashtags = extract_hashtags(text)
				for hashtag in hashtags:
					event = {'text': text, 'hashtag':hashtag}
					ok=stream.train(event,types={'text':'TEXT'})
					if not ok: break
			except KeyError:
				pass

fs.set_endpoint('http://vm:8088/mungio/api')
stream = fs.start_stream(targets={'hashtag':'CATEGORIC'})

print 'training from ',filename
train(stream, filename)

print 'getting stream info'
print stream.get_info()

stream.close()
