'''
Created on Jun 3, 2018

@author: root
'''
import json
import wget
import os

def get_raw_gym_raw(raw_gyms_dict, gym_id):
    for gym_dict in raw_gyms_dict:
        if gym_dict["gymId"] == gym_id:
            return gym_dict["gymName"]
        
url_gyms_metadata = 'https://raw.githubusercontent.com/pjdrm/PgP-Data/master/data/gyms-metadata.json'
url_regions = 'https://raw.githubusercontent.com/pjdrm/PgP-Data/master/data/region-map.json'
url_gyms_raw = 'https://raw.githubusercontent.com/pjdrm/PgP-Data/master/data/gyms.json'

wget.download(url_gyms_metadata)
wget.download(url_regions)
wget.download(url_gyms_raw)

with open('gyms-metadata.json') as f:
    gyms_metadata_dict = json.load(f)
    
with open('region-map.json') as f:
    regions_dict = json.load(f)
    
with open('gyms.json') as f:
    gyms_raw_dict = json.load(f)
    
os.remove('gyms-metadata.json')
os.remove('region-map.json')
os.remove('gyms.json')

for region in regions_dict:
    str_gym_list = "**"+region.upper()+"**\n"
    region_gym_names = []
    for gym_id in regions_dict[region]:
        '''
        if gym_id in gyms_metadata_dict and "nickname" in gyms_metadata_dict[gym_id]:
            gym_name = gyms_metadata_dict[gym_id]["nickname"]
            if gyms_metadata_dict[gym_id]["is_ex"]:
                gym_name += " **(EX raid)**"
        else:
            gym_name = get_raw_gym_raw(gyms_raw_dict, gym_id)
        '''
        gym_name = get_raw_gym_raw(gyms_raw_dict, gym_id)
        region_gym_names.append(gym_name)
    region_gym_names.sort()
    for gym_name in region_gym_names:
        str_gym_list += "- "+gym_name+"\n"
    with open("../gyms_discord/"+region+".txt", "w+") as f:
        f.write(str_gym_list)
