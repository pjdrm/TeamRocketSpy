'''
Created on Sep 5, 2018

@author: root
'''
import os
import wget

portals_info = {}
gym_coords = {}
intel_scrape_dir = "/home/pjdrm/workspace/TeamRocketSpy/ingress_scrapes/"
for intel_scrape in os.listdir(intel_scrape_dir):
    if intel_scrape == "gym_images":
        continue
    with open(intel_scrape_dir+intel_scrape, encoding='ISO-8859-1') as f:
        lins = f.readlines()[1:-1]
    
    for portal in lins:
        portal_split = portal.split(",")
        if len(portal_split) == 4:
            name = portal_split[0].strip()
            lat = portal_split[1].strip()[:7]
            long = portal_split[2].strip()[:7]
            img_url = portal_split[3].strip()
        else:
            name = portal_split[0]+" "+portal_split[1].strip()
            lat = portal_split[2].strip()[:7]
            long = portal_split[3].strip()[:7]
            img_url = portal_split[4].strip()
            
        if name not in portals_info:
            portals_info[name] = []
        portals_info[name].append([[long, lat], img_url])

pokenav_gyms_fp = "/home/pjdrm/workspace/TeamRocketSpy/LisbonGyms.csv"
gyms_pokenav_info = {}
with open(pokenav_gyms_fp) as pokenav_gyms_file:
    pokenav_gyms = pokenav_gyms_file.readlines()

for gym in pokenav_gyms:
    if gym.startswith("~~REMOVED POI~~"):
        continue
    gym_split = gym.split(",gym,")
    name = gym_split[0].strip().replace('"', '').replace(',', '')
    lat = gym_split[1].split(",")[0].strip()[:7]
    long = gym_split[1].split(",")[1].strip()[:7]
    
    if name not in gyms_pokenav_info:
        gyms_pokenav_info[name] = []
    gyms_pokenav_info[name].append([long, lat])

discord_gyms_dir = "/home/pjdrm/workspace/TeamRocketSpy/gyms_discord/"
coord_cvs_areas = ["alameda-areeiro-gulbenkian.txt", "parque-das-nacoes.txt", "campo-grande-conchas.txt"]
coords_cvs = "" 
for gym_file in os.listdir(discord_gyms_dir):
    with open(discord_gyms_dir+gym_file) as f:
        lins = f.readlines()[1:-1]
    
    if gym_file not in coord_cvs_areas:
        continue
    
    for gym in lins:
        gym_name = gym[2:-1].strip()
        if gym_name in gyms_pokenav_info:
            for coords in gyms_pokenav_info[gym_name]:
                pn_long = coords[0]
                pn_lat = coords[1]
                coords_cvs += str(pn_lat)+","+str(pn_long)+"\n"
                
with open("coords.cvs", "w+") as f:
    f.write(coords_cvs)
    
gyms_out_fp = ""
i = 0
for gym_name in gyms_pokenav_info:
    for coords in gyms_pokenav_info[gym_name]:
        pn_long = coords[0]
        pn_lat = coords[1]
        if gym_name not in portals_info:
            print("Gym not found: %s %s %s"%(gym_name, pn_lat, pn_long))
            i += 1
            continue
        for portal in portals_info[gym_name]:
            port_long = portal[0][0]
            port_lat = portal[0][1]
            if port_long == pn_long and port_lat == pn_lat:
                gyms_out_fp += gym_name+","+pn_lat+","+port_long+","+portal[1]+"\n"
                break

print("%d gyms not found"%i)
with open("updateGyms.txt", "w+") as f_out:
    f_out.write(gyms_out_fp)
#print(gyms_out_fp)

'''        
discord_gyms_dir = "/home/pjdrm/workspace/TeamRocketSpy/gyms_discord/"
out_imgs = "/home/pjdrm/workspace/TeamRocketSpy/ingress_scrapes/gym_images/img"
out_coords = "/home/pjdrm/workspace/TeamRocketSpy/coords.cvs"
gym_info_file = "/home/pjdrm/workspace/TeamRocketSpy/updateGyms.txt"
gym_info = ""
i = 0
coord_cvs_areas = ["alameda-areeiro-gulbenkian.txt"]
with open(out_coords, "w+") as out_coords_f:
    for gym_file in os.listdir(discord_gyms_dir):
        with open(discord_gyms_dir+gym_file) as f:
            lins = f.readlines()[1:-1]
            
        for gym in lins:
            gym_name = gym[2:-1].strip()
            if gym_name in gyms_imgs_dict:
                #print("Found gym "+gym_name)
                if gym_file in coord_cvs_areas:
                    out_coords_f.write(gym_coords[gym_name][1]+","+gym_coords[gym_name][0]+"\n")
                gym_info += gym_name + "," + str(gym_coords[gym_name][1])+","+gym_coords[gym_name][0]+","+gyms_imgs_dict[gym_name]+"\n"
                #wget.download(gyms_imgs_dict[gym_name], out=out_imgs+str(i)+".jpeg")
                i += 1
            else:
                print("Could not find gym "+gym_name)

with open(gym_info_file, "w+") as f:
    f.write(gym_info)

print("Matched %d gyms"%i)
'''