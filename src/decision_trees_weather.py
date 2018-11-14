'''
Created on Nov 14, 2018

@author: pjdrm
'''
import numpy as np

#wind_speed
#forecast_desc
#snow_prob
#visibility
#rain_prob
#cloud_cover

FEAT_NAMES = ['forecast_desc',
              'rain_prob',
              'wind_speed',
              'cloud_cover',
              'visibility',
              'snow_prob']

FEAT_MAP = {'Cloudy': 0,
            'Mostly Cloudy': 1,
            'Partly Cloudy': 2,
            'Showers': 3,
            'Rain': 4,
            'Mostly Clear': 5,
            'Sunny': 6,
            'Mostly Sunny': 7,
            'Partly Sunny': 8,
            'Clear': 9}

VAL_BREAK_PTS = {'wind_speed': 20,
                 'snow_prob': 80,
                 'visibility': 80,
                 'rain_prob': 60,
                 'cloud_cover': 70}

def get_features(feat_names,
                 forecast_log,
                 feat_map,
                 val_break_pts):
    feat_arr = np.zeros(len(feat_names))
    for i, f_name in enumerate(feat_names):
        val = forecast_log[f_name]
        if f_name == "wind_speed":
            if val >= val_break_pts[f_name]:
                val = 1
            else:
                val = 0
        elif f_name == "forecast_desc":
            val = feat_map[val]
        elif f_name == "snow_prob":
            snow_prob = float(val[:-1])
            if snow_prob >= val_break_pts[f_name]:
                val = 1
            else:
                val = 0
        elif f_name == "visibility":
            vis = float(val.split(" ")[0])
            if vis >= val_break_pts[f_name]:
                val = 1
            else:
                val = 0
        elif f_name == "rain_prob":
            rain_prob = float(val)
            if rain_prob >= val_break_pts[f_name]:
                val = 1
            else:
                val = 0
        elif f_name == "cloud_cover":
                cloud_over = float(val[:-1])
                if cloud_over >= val_break_pts[f_name]:
                    val = 1
                else:
                    val = 0
        feat_arr[i] = val
    return feat_arr

def load_features(acc_log):
    with open(acc_log) as f:
        lins = f.readlines()
        
    for lin in lins:
        lin_split = lin.split(" ")
        time_stamp = lin_split[2]+" "+lin_split[3]
        s2cell = lin_split[5]
        forecasts = eval(lin.split("Forecast: ")[1])
        for h in forecasts:
            feat_arr = get_features(FEAT_NAMES,
                                    forecasts[h],
                                    FEAT_MAP,
                                    VAL_BREAK_PTS)
            print(feat_arr)
            
acc_log = "./weather_forecasts/acu/forecast_log.txt"
load_features(acc_log)
    
        