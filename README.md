http://featurestream.io is a service that consumes JSON events, incrementally builds a predictive model and provides a simple prediction API. It can also do things like anomaly detection. We'll use the python library in this guide.  If you have any problems, comments or questions, contact us at [hello@featurestream.io](mailto:hello@featurestream.io)

# REST API

We currently expose a REST API at http://api.featurestream.io:8088/api, which supports the following major operations (in addition to a few less interesting ones):

__POST /start_stream___

start a new stream

params: access = access key

body: targets = map from targets to types, eg {'value':'NUMERIC', 'spam':'CATEGORIC'}

returns streamId

__GET /{stream_id}/stop_stream__

close the stream

__POST /{stream_id}/train__

train on an event

body: event as a JSON list of {name:value} pairs

If the value has quotes then it is taken to be a categoric (discrete) attribute
otherwise it is parsed as a number and taken to be a numeric (continuous) attribute
types: optionally specify a map from names to types 
where type is one of {NUMERIC,CATEGORIC,DATETIME,TEXT} 

__POST /{stream_id}/predict__

predict the target fields from the event

body: the JSON event to predict the target fields for

returns a prediction JSON object

__GET /{stream_id}/get_info__

gets info about the current stream

returns a stats JSON object

__GET /{stream_id}/get_schema__

gets schema for the current stream

returns a stats JSON object

__GET /{stream_id}/related_fields__

returns the k variables most related to the target variable, ordered by decreasing relevance. If k=-1, returns all variables.

__GET /{stream_id}/get_stream__

retrieve an existing stream

returns a stream object


# Getting started

Clone featurestream-client
```
git clone https://github.com/featurestream/featurestream-client.git
```
The best way to get started is by using the ipython notebook. [Install ipython](http://ipython.org/install.html) and fire up ipython notebook:
```
featurestream-client/python $ ipython notebook getting-started.ipynb
```
If you don't have ipython or just want to see the example, take a look [here](http://nbviewer.ipython.org/6448149) or see below.

# Getting started (python)
The following example opens a stream, asynchronously adds some events from a csv file, and retrieves a prediction. Import the library and give it your access key:

```python
import featurestream as fs
fs.set_access('your_access_key')
# do a quick health check on the service
print 'healthy=',fs.check_health()
```
We're going to load some events from a CSV file (this is an example that from the KDD'99 cup - see http://kdd.ics.uci.edu/databases/kddcup99/kddcup99.html)

Import the `featurestream.csv` library and get an iterator of events from a CSV file:

```python
import featurestream.csv as csv
events = csv.csv_iterator('../resources/KDDTrain_1Percent.csv')
```
The parser automatically tries to infer types based on a sample of the file; in this case we don't want to change its type inference; see later for how to do this and more advanced use. If the CSV file has no header, the parser creates variable names `0,1,2,3,...` according to the column numbers (see below for more details on parsing CSV files and other formats)

Look at the first event; we'll use this later.

```python
>>> e = events.next()
>>> e
{'0': 0.0,
 '1': 'tcp',
 '10': 0.0,
 '11': 0.0,
 '12': 0.0,
 '13': 0.0,
 '14': 0.0,
 '15': 0.0,
 '16': 0.0,
 '17': 0.0,
 '18': 0.0,
 '19': 0.0,
 '2': 'ftp_data',
 ...
 '4': 491.0,
 '40': 0.0,
 '41': 'normal',
 '5': 0.0,
 '6': 0.0,
 '7': 0.0,
 '8': 0.0,
 '9': 0.0}
```

Events are simple JSON maps `{'name1':value1, ..., 'name_k':value_k}`. If `value` is enclosed in quotes then it is treated as a categoric type, otherwise it is treated as numeric type. For example `event={'some_numeric_val':12.1, 'some_categoric_val':'True', 'numeric_as_categoric':'12.1'}`. You can also specify explicit types if you want; see `api.py` for further documentation. (The engine also supports other types including textual and datetime - TODO describe this later!)

Start a new stream:

```python
stream = fs.start_stream(targets={'41':'CATEGORIC','40':'NUMERIC'})
```

This should try to create a stream with two targets, one for column `41` with categoric type and one for column `40` with numeric type. Check that the stream was created successfully:

```python
>>> stream
Stream[stream_id=3121598785123213694, targets={'40': 'NUMERIC', '41': 'CATEGORIC'}, endpoint=http://api.featurestream.io/api']
```

A stream is created by calling `start_stream(targets)` where `targets` is a map of target names to their types, either CATEGORIC or NUMERIC at present. Each stream is uniquely identified by its `stream_id`. If you close your python console or lose the stream handle, you can call `get_stream(stream_id)` to retrieve the stream object.

```python
>>> stream.stream_id
3121598785123213694L
```

Send the events iterator asynchronously to the stream:

```python
t=stream.train_iterator(events, batch=500)
```

This returns an object `t` which gives you access to the training process (see below for more details).

Wait for the stream to consume some of the events (there are 2500 events in the file, wait until at least 1500 are done!) (almost all the time is spent transferring data, particularly since the servers are in the `us-east-1` AWS region currently).

Examine the progress:

```python
>>> t
AsyncTrainer[stream_id=3121598785123213694, is_running=False, train_count=2499, error_count=0, batch=500]
```

See if it predicts one of the original events correctly:

```python
>>> stream.predict(e)
{'40': 0.0035392940503651336, '41': 'normal'}
```

This returns a simple prediction for each target.

You can also get estimated probabilities for categoric targets by using `predict_full`:

```python
>>> stream.predict_full(e)
{'40': 0.0035392940503651336,
 '41': {'anomaly': 0.30498747069759924, 'normal': 0.6950125293024008}}
```

Featurestream's engine is very good at handling missing values, or noisy data. In particular, for missing values, it can 'integrate them out' to get predictions. For example, the following (predicting with the empty event) returns the distribution of the entire stream:

```python
stream.predict_full({})
{'40': 0.12046304950468253,
 '41': {'anomaly': 0.47833171345263276, 'normal': 0.5216682865473672}}
```

So, about 47.7% of events had variable 41 as 'anomaly' and 52.3% as 'normal', and the average value of variable '40' was 0.12. In the future, we can allow returning more full values for numeric targets, including distributions. The ability to leave out missing values makes featurestream very powerful for handling a wide range of real-life data sources.

Examine which variables are most related to a target variable:

```python
>>> stream.related_fields('41')
[('2', 0.3770347330783282),
 ('1', 0.19141914188838352),
 ('3', 0.19008269160361074),
 ('4', 0.08723446747760971),
 ('5', 0.0684207229686264)]
```
This returns a distribution over all variables, summing to 1, which describes how strongly each variable contributes to predicting the value of the target variable. This allows you to understand more about the structure of your data. By default, it returns the top 5 variables but you can change this by passing the argument `k=10` (for the top 10) or `k=-1` (for all fields).

Examine the stream statistics for one of the targets:

```python
>>> stream.get_stats()['41']
{'accuracy': 0.8783513405362144,
 'auc': -1.0,
 'confusion': {'anomaly': {'anomaly': 1001, 'normal': 192},
  'normal': {'anomaly': 112, 'normal': 1194}},
 'exp_accuracy': [0.8783513405362154,
  0.9243864078858117,
  0.9387295341257783,
  0.948508066478172,
  0.962130093642003],
 'n_correct': 2195.0,
 'n_models': 30,
 'n_total': 2499.0,
 'scores': {'anomaly': {'F1': 0.8681699913269733,
   'precision': 0.8390611902766136,
   'recall': 0.89937106918239},
  'normal': {'F1': 0.887072808320951,
   'precision': 0.9142419601837672,
   'recall': 0.8614718614718615}},
 'type': 'classification'}
```

See below for more information about what these statistics represent. Featurestream calculates these statistics without you having to do cross-validation, training/test set splits, and so on. Furthermore, they are computed in near real-time as your stream is ingested.

You can also examine the stats for the numeric target:

```python
>>> stream.get_stats()['40']
{'correlation_coefficient': 0.9080827150546844,
 'exp_rmse': [0.047846214020193026,
  0.026736475934155627,
  0.022184095577206565,
  0.022028100688291842,
  0.02069833929335216],
 'mean_abs_error': 0.04784621402019295,
 'n_models': 30,
 'n_predictable': 2498,
 'n_total': 2499,
 'n_unpredictable': 1,
 'rmse': 0.13471805922350763,
 'type': 'regression'}
```

So, how did we do so far?

```python
>>> stream.get_stats()['41']['accuracy']
0.8756
```
Pretty good, we hope!

It's good practice to close the stream after you're done with it.

```python
>>> stream.close()
True
```

We hope this example gives you a flavor of what featurestream.io can do for you. You've just scratched the surface! See below for some more details about the calls and objects used above, and more information. We will also be updating this document as we improve the service and add more functionality. We'd love to get some more use case examples. Please say [hello@featurestream.io](hello@featurestream.io)


# CSV and ARFF files
CSV and ARFF files can be handled using modules `featurestream.csv` and `featurestream.arff`, which each produce an iterator of events.

```python
import featurestream as fs
import featurestream.csv as csv
import featurestream.arff as arff

# CSV
stream = fs.start_stream(targets={'41':'CATEGORIC'})
events = csv.csv_iterator('../resources/KDDTrain_1Percent.csv')
# ARFF
stream = fs.start_stream(targets={'class':'CATEGORIC'})
events = arff.arff_iterator('../resources/iris.arff')

# train on the events
for event in events:
  stream.train(event)
```

The ARFF iterator reads the types from the ARFF header. The CSV iterator takes a sample of the data (1000 lines by default) and uses that to try to infer types. Remember that you need to regenerate (or clone) the iterator if you want to run through it again later.

A more efficient way of processing an iterator is by using `stream.train_iterator(iterator, async=True, batch=100)`, which takes an iterator and two optional arguments: `async` if you want to train asynchronously in another thread, and `batch` which sets the batch size. This returns an `AsyncTrainer` object you can use to query the progress.

```python
In [20]: stream = fs.start_stream(learner='rf_classifier', target='41',endpoint=master)
starting stream with params = {'access': 'your_access_key', 'learner': 'rf_classifier', 'target': '41'}

In [21]: events = csv.csv_iterator('../resources/KDDTrain_1Percent.csv')
guessing types..
types= defaultdict(<type 'int'>, {'1': 1, '3': 1, '2': 1, '41': 1})

In [22]: t=stream.train_iterator(events)

In [23]: t
Out[23]: AsyncTrainer[stream_id=5462813263693773231, is_running=True, train_count=1600, error_count=0, batch=100]

In [24]: t
Out[24]: AsyncTrainer[stream_id=5462813263693773231, is_running=True, train_count=2400, error_count=0, batch=100]

In [25]: t
Out[25]: AsyncTrainer[stream_id=5462813263693773231, is_running=False, train_count=2500, error_count=0, batch=100]

# how many items have been trained
t.get_train_count()

# how many errors
t.get_error_count()

# the last error e.g.
# (<type 'exceptions.ValueError'>, ValueError('No JSON object could be decoded',))
t.get_last_error()

# has it got to the end
t.is_running()

# stop before getting to the end
t.stop()

# wait until it has finished
t.join()
```

A third alternative is to directly use `stream.train_batch(events,batch=100)`, which takes a list of events and an optional batch size parameter (to avoid many round trips to the server).

```python
events = csv.csv_iterator('../resources/KDDTrain_1Percent.csv')
stream.train_batch(list(events))
```

You could also stream through some events to test the model; see the section `clear_stats()` below for an example of how to do get error statistics this way. The example in `examples/csv_test.py` streams a CSV file into the `train` API, then optionally tests against a separate test CSV file. To run it with the example CSV file in the `resource` directory, do:
```
/featurestream-client/python/examples$ PYTHONPATH=../ python csv_test.py --train ../../resources/KDDTrain_1Percent.csv --test ../../resources/KDDTest.csv --learner rf_classifier --target 41 --error accuracy
```

# transforming JSON events
Suppose you receive JSON events with various nested fields and you want to extract a particular set of fields to use as events. `featurestream.transform` provides a simple way of doing this, and allows building pipelines of event transformers. Here's an example of how to use the `ExtractFieldsTransform` to extract two fields `interaction.content` and `salience.content.sentiment` (from the datasift example). The path to each field is specified using `[<fieldname>][<fieldname>]...` and note the new field name it is mapped to.

```python
import featurestream as fs
from featurestream.transform import *

mapping = {'fields': [
  {'name': 'content', 'source': '[interaction][content]'},
  {'name': 'sentiment', 'source': '[salience][content][sentiment]'}
]}
transform = ExtractFieldsTransform(mapping)
In [8]: event = {'status':'active', 'tick':96, 'interaction':{'x':10,'y':13,'content':'some content'}, 'salience':{'level':4, 'content':{'allowed':1, 'sentiment':3, 'lang':'en'}}}

In [9]: transform1.transform(event)
Out[9]: {'content': 'some content', 'sentiment': 3}
```

Since a `Transform` object takes an event and returns another event, you can pipeline them using `TransformPipeline`:

```python
transform1 = ExtractFieldsTransform(mapping)
transform2 = MyTransform(...)
pipeline = TransformPipeline([transform1,transform2])
for event in events:
    stream.train(pipeline.transform(event))
```

This is especially useful for dealing with data from streams, such as twitter.

# stats
Streams keep track of various statistics for each target, which can be examined with `stream.get_stats()`. They differ depending on the type of the target.

For categoric targets:

```python
{
# the overall accuracy so far
'accuracy': 0.816,
# the area under curve so far (only for binary targets)
'auc': 0.8180340660558233,
# the confusion matrix - for each true label, what labels were predicted with what frequency
# '?' means the classifier couldn't make a prediction
'confusion': {'anomaly': {'?': 8, 'anomaly': 942, 'normal': 243},
   'normal': {'?': 5, 'anomaly': 204, 'normal': 1098}},
# a list of exponential moving averages of accuracy with different decays
# the first entry has no decay -> same as overall accuracy
# the last only considers roughly the last 100 elements
'exp_accuracy': [0.8160000000000006,
  0.8759494197679079,
  0.8896917925536387,
  0.8923437655681115,
  0.90003334432228],
# the total number of correct predictions
'n_correct': 2040.0,
# the total number of entries trained
'n_total': 2500.0,
# for each target label, the precision/recall/F1 scores
# see http://en.wikipedia.org/wiki/F1_score
'scores': {'anomaly': {'F1': 0.8054724241128687,
   'precision': 0.7896060352053647,
   'recall': 0.8219895287958116},
  'normal': {'F1': 0.8293051359516617,
   'precision': 0.8400918133129304,
   'recall': 0.8187919463087249}}
# the type of stream learner
'type':'classification'
}
```

For numeric targets:

```python
{
# the pearson correlation coefficient
# http://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient
'correlation_coefficient': 0.749853117443013205,
# the mean absolute error
'mean_abs_error': 167.154943129684,
# the number of predictable events seen
'n_predictable': 1930,
# the number of events seen
'n_total': 2010,
# the number of unpredictable events seen
'n_unpredictable': 80,
# the RMSE - see http://en.wikipedia.org/wiki/Root-mean-square_deviation
'rmse': 2182.995229029628
}
```

## clear_stats()
You can clear the stats for a stream by calling `stream.clear_stats()`. For a fun example, try testing a classifier on its training set to see if the result improves (not a recommended methodology!).

```python
import featurestream as fs
import featurestream.csv as csv
> stream = fs.start_stream(targets={'41':'CATEGORIC'})
> events = list(csv.csv_iterator('../resources/KDDTrain_1Percent.csv'))
> stream.train_batch(events)
> stream.get_stats()['41']['accuracy']
0.8750520616409829
> stream.clear_stats()
> stream.train_batch(events)
> stream.get_stats()['41']['accuracy']
0.9541857559350271
```

## info
The method `stream.get_info()` will return more structural information about the stream and the learner. TODO: elaborate on this.

# some bigger examples
Here are two archetypal examples:

## KDDCUP example
Download the file

```
wget http://kdd.ics.uci.edu/databases/kddcup99/kddcup.data.gz
```
Load into featurestream

```python
import featurestream as fs
import featurestream.csv as csv

stream=fs.start_stream(learner='rf_classifier', target='41')
t=stream.train_iterator(csv.csv_iterator('../resources/covtype.data.gz'), batch=500)
# ...
stream.get_stats()
```

## forest covertype
Note: the csv parser we use infers variables that have a small number of numeric values, such as binary variables, as having numeric type. There is nothing wrong with this, as the learner will still build a good model. In a future release, we will automate the handling of this, but in the meantime you can force the type detection of the csv parser as in the example below by including `{variable_name:'1'}` in the `types` argument.
```
wget http://archive.ics.uci.edu/ml/machine-learning-databases/covtype/covtype.data.gz
```

```python
import featurestream as fs
import featurestream.csv as csv

stream=fs.start_stream(learner='rf_classifier', target='54')
# use the following if you want to force categoric variables
# this actually seems to give worse accuracy right now, but is faster
# events=csv.csv_iterator('../resources/covtype.data.gz', types={'11':'1','12':'1','13':'1','14':'1','15':'1','16':'1','17':'1','18':'1','19':'1','20':'1','21':'1','22':'1','23':'1','24':'1','25':'1','26':'1','27':'1','28':'1','29':'1','30':'1','31':'1','32':'1','33':'1','34':'1','35':'1','36':'1','37':'1','38':'1','39':'1','40':'1','41':'1','42':'1','43':'1','44':'1','45':'1','46':'1','47':'1','48':'1','49':'1','50':'1','51':'1','52':'1','53':'1','54':'1'})
# use the following if you want to use all numeric variables
events=csv.csv_iterator('../resources/covtype.data.gz')
t=stream.train_iterator(events,batch=500)
# ...
stream.get_stats()
{u'accuracy': 0.7276820062800224,
 u'confusion': {u'1.0': {u'1.0': 7982,
   u'2.0': 9508,
   u'3.0': 3,
   u'5.0': 478,
   u'6.0': 14,
   u'7.0': 1191},
  u'2.0': {u'1.0': 2185,
   u'2.0': 50687,
   u'3.0': 156,
   u'4.0': 13,
   u'5.0': 1264,
   u'6.0': 320,
   u'7.0': 265},
  u'3.0': {u'2.0': 664, u'3.0': 635, u'4.0': 1125, u'5.0': 387, u'6.0': 1509},
  u'4.0': {u'2.0': 74, u'3.0': 175, u'4.0': 3631, u'5.0': 40, u'6.0': 400},
  u'5.0': {u'1.0': 18,
   u'2.0': 2383,
   u'3.0': 143,
   u'4.0': 24,
   u'5.0': 2141,
   u'6.0': 122,
   u'7.0': 1},
  u'6.0': {u'2.0': 833, u'3.0': 459, u'4.0': 1216, u'5.0': 399, u'6.0': 1413},
  u'7.0': {u'1.0': 610, u'2.0': 174, u'5.0': 38, u'7.0': 3498}},
 u'exp_accuracy': [0.727682006280015,
  0.7929695506094349,
  0.8465440048209535,
  0.8953181400037337,
  0.9185661108299555],
 u'n_correct': 69987.0,
 u'n_models': 50,
 u'n_total': 96178.0,
 u'scores': {u'1.0': {u'F1': 0.5326482266190652,
   u'precision': 0.4162494785148102,
   u'recall': 0.7394163964798518},
  u'2.0': {u'F1': 0.8503602794997189,
   u'precision': 0.923428675532884,
   u'recall': 0.788007400152356},
  u'3.0': {u'F1': 0.21558309285350535,
   u'precision': 0.14699074074074073,
   u'recall': 0.40420114576702737},
  u'4.0': {u'F1': 0.7030690289476232,
   u'precision': 0.8405092592592592,
   u'recall': 0.6042602762522883},
  u'5.0': {u'F1': 0.44701952187075894,
   u'precision': 0.44308774834437087,
   u'recall': 0.4510216979144723},
  u'6.0': {u'F1': 0.3489750555692764,
   u'precision': 0.32708333333333334,
   u'recall': 0.3740074113287454},
  u'7.0': {u'F1': 0.7542857142857143,
   u'precision': 0.8097222222222222,
   u'recall': 0.7059535822401615}},
 u'type': u'classification'}
```

# scikit-learn integration
Warning: this is experimental!

The module `featurestream.sklearn` provides basic integration with scikit-learn, by providing classes `FeatureStreamClassifier, FeatureStreamRegressor, FeatureStreamCluster` implementing `BaseEstimator` and other interfaces. This should enable using mostly all the examples in scikit learn with these classes. Here are some examples, see http://scikit-learn.org/dev/datasets/index.html for more datasets.

## iris dataset
See http://scikit-learn.org/dev/modules/generated/sklearn.datasets.load_iris.html#sklearn.datasets.load_iris

```python
from featurestream.sklearn import *
from sklearn.datasets import load_iris
data = load_iris() # get the dataset
X = data.data
y = map(lambda x:data.target_names[x],data.target) # map targets to their categorical names
clf = FeatureStreamClassifier()
clf.fit(X,y) # train
...
```

## digits dataset

```python
import pylab as pl
from sklearn import datasets,metrics
from featurestream.sklearn import *
import featurestream as fs
digits = datasets.load_digits()

# The data that we are interested in is made of 8x8 images of digits,
# let's have a look at the first 3 images, stored in the `images`
# attribute of the dataset. If we were working from image files, we
# could load them using pylab.imread. For these images know which
# digit they represent: it is given in the 'target' of the dataset.
for index, (image, label) in enumerate(zip(digits.images, digits.target)[:4]):
    pl.subplot(2, 4, index + 1)
    pl.axis('off')
    pl.imshow(image, cmap=pl.cm.gray_r, interpolation='nearest')
    pl.title('Training: %i' % label)

# To apply an classifier on this data, we need to flatten the image, to
# turn the data in a (samples, feature) matrix:
n_samples = len(digits.images)
data = digits.images.reshape((n_samples, -1))

# map targets to categorical values (need to be str currently)
y = map(lambda x:str(digits.target_names[x]),digits.target)
X = data

classifier = FeatureStreamClassifier()
classifier.fit(X,y)

accuracy = classifier.stream.stats('accuracy')
# this is probably pretty bad on such a small stream...
# making featurestream work well on fixed-size datasets is a TODO
# let's see why this did so badly
[x['size'] for _,x in classifier.stream.info()['ensemble'].items()]
# [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
# so all the learners are single-node decision stumps

# transform each event into an internal feature representation
Z = classifier.transform(X)

# TODO do something with these transformed vectors

```


