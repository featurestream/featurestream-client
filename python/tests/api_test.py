import featurestream as fs
import random
import sys
import pprint
from collections import defaultdict

fs.set_endpoint('http://192.168.2.3:8080')

def classify_test(f,n=4000,mink=0,maxk=100):
	stream = fs.start_stream(learner='rf_classifier', target='f')
	print 'n=',n,'stream_id=',stream.stream_id
	# train phase
	for _ in xrange(n):
		j = random.randint(mink,maxk)
		event={}
		event['value']=j
		event['f']=f(j)
		ok = stream.train(event)
		if not ok: return
	# test phase
	# todo

	accuracy = stream.stats('accuracy')
	stream.close()
	return accuracy

def train_threshold_event(n,label_prob,stream,k,d,attrs,thresholds):

	for _ in xrange(n):
		event = dict(('d.'+str(i),random.randint(0,k)) for i in xrange(d))
		if random.random() <= label_prob:
			event['target'] = str(all([event['d.'+str(i)]>thresholds[i] for i in attrs]))
		ok = stream.train(event)
		if not ok: break

def separator_test(n=2000):
	print 'separator test','n=',n
	stream=fs.start_stream(learner='rf_classifier', target='anomaly')
	print "stream_id=",stream.stream_id
	for _ in xrange(n):
		stream.train({'size':random.randint(1,50), 'type':random.choice(['a','b','c']), 'anomaly':'true'})
		stream.train({'size':random.randint(50,100), 'type':random.choice(['d','a','f']), 'anomaly':'false'})
	# predictions
	ok=True
	x=stream.predict({'size':99})['prediction']
	print x, 'expected false'
	ok &= (x=='false')
	x=stream.predict({'size':40, 'type':'a'})['prediction']
	print x, 'expected true'
	ok &= (x=='true')
	x=stream.predict({'type':'f'})['prediction']
	print x, 'expected false'
	ok &= (x=='false')
	stream.close()
	return ok

def posneg_test():
	print 'posneg test'
	f = lambda i:'+' if (i>=0) else '-'
	accuracy = classify_test(f,mink=-100,maxk=100)
	print 'accuracy=',accuracy,'expected >0.95'
	return accuracy >0.95

def margin_test():
	for f in [1, 10, 25, 50, 75, 99]:
		print 'margin test, f=',f
		accuracy = classify_test(lambda i:str(i<=f),mink=0,maxk=100)
		print 'accuracy=',accuracy,'expected >0.95'
		if accuracy < 0.95: return False
	return True

def test(test_fn, **kwargs):
	res = test_fn(**kwargs)
	if res: print '[PASS]' 
	else: print '[FAIL]'

if __name__ == "__main__":
	if len(sys.argv) > 1:
		tests = map(lambda x:eval(x),sys.argv[1:])
	else:
		tests = [separator_test,
			posneg_test,
			margin_test]
	for t in tests:
		test(t)


