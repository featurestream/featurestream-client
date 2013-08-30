# Get twitter:
# sudo pip install twitter
# http://mike.verdone.ca/twitter/
# Get your keys from here: https://dev.twitter.com/apps/new


from twitter import *
import os, json, pprint

# twitter name = 'name'
CONSUMER_KEY = ''
CONSUMER_SECRET = ''
oauth_token = ''
oauth_secret = ''
auth=OAuth(oauth_token, oauth_secret, CONSUMER_KEY, CONSUMER_SECRET)

twitter_stream = TwitterStream(auth=auth)
iterator = twitter_stream.statuses.sample()

for tweet in iterator:
	print(json.dumps(tweet))
