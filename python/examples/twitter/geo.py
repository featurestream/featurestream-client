import featurestream as fs
import json,string
from featurestream import transform
import sys

filename = sys.argv[1]

def train(stream, filename):
	i=0
	with open(filename, 'rb') as file_in:
		for line in file_in:
			try:
				tweet = json.loads(line)
				coords = tweet['geo']['coordinates']
				event = {'lat': coords[0], 'long': coords[1]}
				ok=stream.train(event)
				if not ok: break
				i+=1
				if (i%1000==0): print i
			except KeyError:
				pass

clusterer = fs.start_stream(learner='clustering')
print 'got stream_id =',clusterer.stream_id

print 'training from ',filename
train(clusterer, filename)

print 'getting stream info'
print clusterer.get_info()

clusterer.close()
