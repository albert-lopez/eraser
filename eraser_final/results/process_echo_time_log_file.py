#!/usr/bin/python3


import os
import re
import sys
import statistics_structs as st

def process_echo_file (file_name):
    
    stat = st.FlowStat()

    if (not os.path.exists(file_name)):
        print ("%s not exists" % (file_name))
        return (None)

    fd = open(file_name,"r")
    fd.readline()
    line = fd.readline()
    if ("ERR" in line):
        print ("Error capturing packets: "+line)
        return (None)
    for line in fd:
        if (not line.startswith("SDU")):
            continue
        camps = line.split(",")
        if (len(camps) == 3):
            pattern = r" RTT = ([0-9.]+) ms"
            match = re.match(pattern, camps[2])
            delay = float(match.group(1))/2 #RTT/2
            stat.latency_lst.append(delay)
            stat.latency_avg += delay
            stat.rx_pdus += 1
            if (stat.latency_min > delay):
                stat.latency_min = delay
            if (stat.latency_max < delay):
                stat.latency_max = delay    
        elif (len(camps) == 1):
            pattern = r"SDUs sent: ([0-9]+); SDUs received: ([0-9]+); ([0-9.]+)% SDU loss; Minimum RTT: ([0-9.]+) ms; Maximum RTT: ([0-9.]+) ms; Average RTT:([0-9.]+) ms; Standard deviation: ([0-9.]+) ms"
            match = re.match(pattern, line)
            if (match == None):
                print ("Err end line: "+line)
                return (None)
            stat.tx_pdus = int(match.group(1))
            stat.rx_pdus = int(match.group(2))
            stat.latency_min = float(match.group(4))/2
            stat.latency_max = float(match.group(5))/2 
            stat.latency_avg = float(match.group(6))/2
            stat.endFlow = True
            stat.lost = (stat.tx_pdus - stat.rx_pdus)*100/stat.tx_pdus
            break
        else:
            print (line)
    if (stat.endFlow != True):
        if (stat.rx_pdus == 0):
            print(" No RX packets: "+file_name)
            return (None)
        stat.latency_avg =  stat.latency_avg / stat.rx_pdus          
                
    return (stat)
    
        
if __name__ == '__main__':
    log_format = True
    arg = sys.argv
    if (len(arg) != 3):
        print ("process_echo_time_log_file.py <file_nema> <stat>")
        print ("   <stat> = l  -> End statistics")
        print ("   <stat> = d  -> Dump packets")
        sys.exit()  
        
    
    if (arg[2].startswith("d")):
        log_format = False
        
    file_name = arg[1]
    
    stat = process_echo_file (file_name)
    if (stat != None):
        if (log_format):
            print (str(stat))
        else:
            for delay in stat.latency_lst:
                print(delay)   
    
       
             
            

