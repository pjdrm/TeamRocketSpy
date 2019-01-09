'''
Created on Nov 14, 2018

@author: pjdrm
'''
import numpy as np
import datetime
from sklearn import tree
from sklearn.model_selection import cross_val_score
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import cross_val_predict
from sklearn.externals.six import StringIO
import pydotplus

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

NAME_MAP = {1: 'Sunny',
           2: 'Rain',
           3: 'Partly Cloudy',
           4: 'Cloudy',
           5: 'Windy',
           6: 'Snow',
           7: 'Fog',
           11: 'Clear',
           13: 'Partly Cloudy (night)',
           16: 'Extreme'}

S2ID_2_LK = {'943841672003846144': '273981',
             '943839472980590592': '273947'}

def get_features(feat_names,
                 forecast_log,
                 feat_map,
                 val_break_pts):
    feat_arr = np.zeros(len(feat_names)+len(feat_map))
    for i, f_name in enumerate(feat_names):
        i = len(feat_map)+i-1
        val = forecast_log[f_name]
        if f_name == "wind_speed":
            if val >= val_break_pts[f_name]:
                val = 1
            else:
                val = 0
        elif f_name == "forecast_desc":
            i = feat_map[val]
            feat_arr[i] = 1
            continue
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
        feat_arr[i] = int(val)
    return feat_arr

def match_ingame_weather(ingame_weather, time_stamp, h, s2cell_lk):
    ts_split = time_stamp.split(" ")
    ts_h = int(ts_split[1][0:2])
    h_split = h.split(" ")
    tc = int(h_split[1].replace("tc", ""))
    date_1 = datetime.datetime.strptime(ts_split[0], "%d-%m-%y")
    if tc >= 24:
        #its the next day
        date_1 = date_1 + datetime.timedelta(days=1)
    elif "am" in h_split[0] and ts_h >= 17:
        #its the next day
        date_1 = date_1 + datetime.timedelta(days=1)
    
    h_24 = datetime.datetime.strptime(h_split[0], '%I%p').strftime('%H')
    date_str = date_1.strftime('%d-%m-%y')+" "+h_24
    if date_str in ingame_weather[s2cell_lk]:
        return int(ingame_weather[s2cell_lk][date_str])
    else:
        return -1

def load_features(acc_log, ingame_weather):
    with open(acc_log) as f:
        lins = f.readlines()
        
    datasets = {}
    for lin in lins:
        lin_split = lin.split(" ")
        time_stamp = lin_split[2]+" "+lin_split[3]
        s2cell = lin_split[5]
        forecasts = eval(lin.split("Forecast: ")[1])
        time_stamp_h = lin_split[3][0:2]
        if time_stamp_h not in datasets:
            datasets[time_stamp_h] = []
            
        for h in forecasts:
            feat_arr = get_features(FEAT_NAMES,
                                    forecasts[h],
                                    FEAT_MAP,
                                    VAL_BREAK_PTS)
            Y = match_ingame_weather(ingame_weather, time_stamp, h, s2cell)
            if Y != -1:
                feat_arr[-1] = Y
                datasets[time_stamp_h].append(feat_arr)
                #print(feat_arr)
    learn_decision_tree(datasets)
            
def load_ingame_weather(ingame_log, s2id2lk):
    with open(ingame_log) as f:
        lins = f.readlines()
    
    ingame_weather = {}
    for k in s2id2lk:
        ingame_weather[s2id2lk[k]] = {}
        
    for lin in lins:
        lin_split = lin.split(" ")
        s2cell_id = lin_split[3]
        weather_condition = lin_split[5]
        if weather_condition == '11':
            weather_condition = '1' #merging Clear in Sunny weather since they are the same
        elif weather_condition == '13':
            weather_condition = '3' #merging Partly Cloudy (night) in Partly Cloudy since they are the same
        time_stamp = lin_split[7]+" "+lin_split[8][0:2]
        s2cell_lk = s2id2lk[s2cell_id]
        cell_ig_weather = ingame_weather[s2cell_lk]
        if time_stamp not in cell_ig_weather:
            cell_ig_weather[time_stamp] = weather_condition
    return ingame_weather

def learn_decision_tree(datasets):
    n_folds = 6
    best_avg = -1
    best_X = None
    best_Y = None
    best_h = None
    results_str = ""
    for d_k in datasets:
        if len(datasets[d_k]) == 0:
            print("WARNING: 0 data points for model %s" % d_k)
            continue
        dataset = np.vstack(datasets[d_k])
        X = dataset[:,0:-1]
        Y = dataset[:,-1]
        if Y.shape[0] <= n_folds*2:
            print("WARNING: not enough data points for model %s" % d_k)
            continue
        clf = tree.DecisionTreeClassifier(criterion='entropy')
        scores = cross_val_score(clf, X, Y, cv=n_folds)
        avg = np.average(scores)
        results_str += "Model: "+d_k+" Cross_val_score "+str(avg)+" #instances: "+str(Y.shape[0])+"\n"
        if avg > best_avg:
            best_avg = avg
            best_X = X
            best_Y = Y
            best_h = d_k
            
    feat_map_inv = {v: k for k, v in FEAT_MAP.items()}
    feature_names = []
    for i in range(len(feat_map_inv)):
        feature_names.append(feat_map_inv[i])
    for other_feat in FEAT_NAMES[1:]:
        feature_names.append(other_feat)
        
    unique_Y = np.sort(np.unique(best_Y))
    class_names = []
    for y in unique_Y:
        class_names.append(NAME_MAP[y])
    clf = clf.fit(best_X, best_Y)
    y_pred = cross_val_predict(clf, best_X, best_Y, cv=n_folds)
    conf_mat = confusion_matrix(best_Y, y_pred)
    
    cm_str = "\t"
    for cn in class_names:
        cm_str += cn+"\t"
    
    cm_str += '\n'   
    for i in range(conf_mat.shape[0]):
        cm_str += class_names[i]+'\t'
        for j in range(conf_mat.shape[1]):
            cm_str += str(conf_mat[i][j])+'\t'
        cm_str += '\n'
    
    print(results_str)
    print(cm_str)
    print("Best AVG accuracy: %f\nBest time to get Accu weather: %sh" %(best_avg, best_h))
    dot_data = StringIO()
    tree.export_graphviz(clf, out_file=dot_data, 
                         feature_names=feature_names,  
                         class_names=class_names,  
                         filled=True, rounded=True,  
                         special_characters=True)
    graph = pydotplus.graph_from_dot_data(dot_data.getvalue())  
    graph.write_pdf("dt_test.pdf")
    
    
ingame_log = "/home/pjdrm/Desktop/PgL/weather_forecasts/ingame/forecast_log.txt"
ingame_weather = load_ingame_weather(ingame_log, S2ID_2_LK)

acc_log = "/home/pjdrm/Desktop/PgL/weather_forecasts/acu/forecast_log.txt"
load_features(acc_log, ingame_weather)
        