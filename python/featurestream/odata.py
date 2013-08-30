'''
Created on 18 Feb 2013

@author: adt
'''
import requests,sys,json
import json2csv

"""
retrieve JSON from Azure marketplace / allegedly any OData endpoint
"""
# azure keys
auth=("xxx","yyy")

def get_resource(uri):                                                                                           
    print uri
    r=requests.get(uri,params={'$format':'json', '$top':'100000'},auth=auth)
#    r=requests.get(uri,params={'$format':'json'},auth=auth)
    if (r.status_code != 200):
        print r.url
        print r.text        
        return None
    else:
        return r.json()

def get_entity(path):
    print "retrieving",path,auth

    # get entity
    
    pool_path='../data/'
    

    # TODO set uuid = md5(file)
    from hashlib import md5
    import os.path
    s=md5(path).digest().encode('hex_codec')
    fname = os.path.join(pool_path, s+'.json')

# pull all pages
    obj=[]
    with open(fname,'w+') as f:
        while(True):
            r=get_resource(path)
            if r is None: break
            data=r['d']
            size = len(data['results'])
            items = data['results']
            obj.extend(items)
            if '__next' in data.keys():
                path=data['__next']
            else:
                break

        f.write(json.dumps(obj,indent=0))
        
    
    # to csv
    return json2csv.json2csv(fname)


if __name__ == "__main__":
#    userkey=sys.argv[2]
#    passkey=sys.argv[3]
#    auth=(userkey,passkey)
    path=sys.argv[1] # 'https://api.datamarket.azure.com'
    get_entity(path)
    # TODO get all entities at the path
    # TODO get all datasets at the path

