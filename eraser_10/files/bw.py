#!/usr/bin/python3

import sys
import os
from math import ceil

def mean_bandwidth_calc (bytes_per_second, duration = 0):
    i = 0  
    entries = len(bytes_per_second) 
    while (i < entries):
        if (bytes_per_second[i] != 0):
            break
        i = i+1
                
    if (entries - i > duration and duration != 0):
        filtered_bytes_per_second = bytes_per_second[i:i+duration]
    else:
        filtered_bytes_per_second = bytes_per_second[i:]
    
    if (len(filtered_bytes_per_second) == 0):
        return (0)    
        
    return (sum(filtered_bytes_per_second) / len(filtered_bytes_per_second) )

def get_bw_from_file (file_name,duration = 0):
    fd = open(file_name,"r")
    
    stadistics_list_prev = []
    stadistics_list_now = []
    tx_bytes_per_second = []
    rx_bytes_per_second = []
    max_tx_rate = 0
    max_rx_rate = 0
    tx_rate = 0
    rx_rate = 0
    for line in fd:
        line = line[:-1]
        stadistics_list_prev = list(stadistics_list_now)
        stadistics_list_now = line.split(":")
        if (len (stadistics_list_now) != 4):
            print ("==> Error processing line == %s == of file %s. Discarding line." % (line, file_name))
            stadistics_list_now = []
            stadistics_list_prev = []
            continue
        if (len(stadistics_list_prev) != 0):
            try:
                tx_rate = 8*(int(stadistics_list_now[0])-int(stadistics_list_prev[0]))
                rx_rate = 8*(int(stadistics_list_now[1])-int(stadistics_list_prev[1]))
            except:
                print ("==> Error processing line == %s == of file %s. Discarding line." % (line, file_name))
                stadistics_list_now = []
                stadistics_list_prev = []
                continue    
            if (tx_rate > max_tx_rate): 
                max_tx_rate = tx_rate
            if (rx_rate > max_rx_rate): 
                max_rx_rate = rx_rate    
            tx_bytes_per_second.append(tx_rate)
            rx_bytes_per_second.append(rx_rate)
    tx_bw = mean_bandwidth_calc(tx_bytes_per_second, duration)
    rx_bw = mean_bandwidth_calc(rx_bytes_per_second, duration)
    fd.close()
    return ("%f:%f:%f:%f" % (round(tx_bw/1e6,3),round(rx_bw/1e6,3),round(max_tx_rate/1e6,3),round(max_rx_rate/1e6,3)))
    


arg = sys.argv

if (not (len(arg)==2 or len(arg)==3)):
    print ("bw.py <path> [<duration>]")
    sys.exit()

path = arg[1]
if (not os.path.isdir(path)):
    print ("Error: Path does not exists (%s)" % (path))
    sys.exit(1)

duration = 0
if (len(arg)==3):
    duration = int(arg[2])

for root, dirs, files in os.walk(path):  
    for filename in files:
        if (filename.startswith("e_")):
            file = "%s/%s" % (root,filename)
            bw_info = get_bw_from_file(file, duration)
            file_name_parts = filename.split(".")
            print ("%s:%s" % (file_name_parts[0],bw_info))
            
