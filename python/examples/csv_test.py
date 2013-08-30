import featurestream as fs
from featurestream.csv import csv_iterator
import time
import argparse,pprint

# train on each line of the csv file line-by-line, then test
def train_test(train_filename, test_filename=None, target=None, learner=None, types={}, error=None, verbose=False):

    stream = fs.start_stream(learner=learner, target=target)
    print 'stream_id=',stream.stream_id

    print 'training...',train_filename
    for event in csv_iterator(train_filename, types=types):
        ok = stream.train(event)
        if not ok: break
        
    print 'stats='
    pprint.pprint(stream.stats())
    
    if (test_filename is not None):
	print 'sleeping'
	time.sleep(15)
        print 'testing...',test_filename
        stream.clear_stats()
        n_correct=0
        n_total=0
        se=0
        for event in csv_iterator(test_filename, types=types):
#            print event
            prediction = stream.predict(event)['prediction']
        
            actual = event[target]
            if verbose: print 'actual=',actual,'predicted=',prediction,'event=',event
            if (error=='rmse'):
                # for regression
                if not isnan(float(prediction)):
                    se+=(float(prediction)-float(actual))**2
            if (error=='accuracy'):
                # for classification
                if (prediction==actual):
                    n_correct+=1
            n_total+=1

        print 'n_total=',n_total
        if (error=='accuracy'):
            print 'n_correct, accuracy=',(n_correct)/(float(n_total))
        if (error=='rmse'):
            print 'rmse=',sqrt(se/n_total)

    stream.close()
        
#    print 'info=', json.dumps(stream.info(stream_id),indent=1)

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('--train',dest='train_filename',required=True)
    parser.add_argument('--test',dest='test_filename')
    parser.add_argument('--error',dest='error', choices=['rmse', 'accuracy'])
    parser.add_argument('--target',dest='target')
    parser.add_argument('--learner',dest='learner', required=True)
    parser.add_argument('--missing_values',dest='missing_values',type=list)
    parser.add_argument('--types',dest='types',type=dict)
    parser.add_argument('--verbose', dest='verbose', action='store_const',
                   const=True, default=False, help='verbose')

    args=parser.parse_args()
    print args

    if args.types is None:
	args.types={}

    if args.missing_values is None:
        train_test(args.train_filename, args.test_filename, target=args.target, learner=args.learner, types=args.types, error=args.error, verbose=args.verbose)
    else:
        train_test(args.train_filename, args.test_filename, target=args.target, learner=args.learner, missing_values=args.missing_values, types=args.types, error=args.error, verbose=args.verbose)

