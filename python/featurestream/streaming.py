import requests
import json

def json_stream_iterator(location, headers=None, auth=None, ignore_errors=True):

	r = requests.get(location, stream=True, headers=headers, auth=auth)
	try:
		for line in r.iter_lines():
			if line:
				try:
					yield json.loads(line)
				except:
					if not ignore_errors:
						raise ValueError('error parsing line='+line)
	finally:
		r.close()

