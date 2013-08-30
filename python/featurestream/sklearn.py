'''
Created on 6 May 2013

module to help with interfacing with sklearn

@author: adt
'''
from __future__ import absolute_import

from sklearn.base import BaseEstimator,ClassifierMixin,RegressorMixin,ClusterMixin
from sklearn.utils import array2d
from featurestream.transform import array2json
import featurestream as fs
from numpy import float32, float64
import numpy as np

DTYPE = float32
DOUBLE = float64

class FeatureStreamEstimator(BaseEstimator):

    stream = None
    target = None

    def __init__(self, learner, target='target'):
        self.target = target
        self.stream = fs.start_stream(learner=learner, target=self.target)
    
    def __repr__(self):
        return 'FeatureStreamEstimator[stream='+str(self.stream)+']'

    def fit(self, X, y=None, headers=None, verbose=False):

        X = array2d(X)

        if (X.ndim != 2):
            raise ValueError('X must have dimension 2, ndim='+X.ndim)        

#        n_samples, self.n_features_ = X.shape
        y = np.atleast_1d(y)
#        y = y.astype(DOUBLE)

        if self.target is not None:
            if y is None:
                y = [None]*len(X)
            if (len(y) != len(X)):
                raise ValueError('y must be same shape as X, len(X)='+str(len(X))+', len(y)='+str(len(y)))

        if headers is not None:
            if (len(headers) != len(X)):
                raise ValueError('headers must be same shape as X, len(X)='+str(len(X))+', len(headers)='+str(len(headers)))


        for x,t in zip(X,y):
            if verbose: print x,t
            event = array2json(x,headers)
            if self.target is not None:
                event[self.target] = t
            self.stream.train(event)
    
    def transform(self, X):
        
        result = []
        for x in X:
            event = array2json(x)
            result.append(self.stream.transform(event))
        return result
        
    def predict(self, X):
        
        result = []
        for x in X:
            event = array2json(x)
	    # should this be a numpy type?
            result.append(float(self.stream.predict(event)['prediction']))
        return result
            
class FeatureStreamClassifier(FeatureStreamEstimator, ClassifierMixin):
    
    def __init__(self, learner='ensemble_classifier'):
        super(FeatureStreamClassifier, self).__init__(learner)
    
class FeatureStreamRegressor(FeatureStreamEstimator, RegressorMixin):
    
    def __init__(self, learner='ensemble_regressor'):
        super(FeatureStreamRegressor, self).__init__(learner)

class FeatureStreamCluster(FeatureStreamEstimator, ClusterMixin):

    def __init__(self, learner='clustering'):
        super(FeatureStreamCluster, self).__init__(learner, target=None)
    
