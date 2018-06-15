'''
Created on Jun 1, 2018

@author: pjdrm
'''
import urllib.request
import json
import wget

def gyms_info():
    response = urllib.request.urlopen('https://raw.githubusercontent.com/pjdrm/PgP-Data/master/data/region-map.json')
    html = eval(str(response.read()))
    print(html)
    #region_map_json = json.loads(html)
    #print(region_map_json)
    
gyms_info()