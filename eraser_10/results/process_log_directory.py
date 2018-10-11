#!/usr/bin/python3


import os
import sys
import process_echo_time_log_file as pecho
import statistics_structs as st
from fileinput import filename



def processFile(file_name,stat):
    fd = open(file_name,"r")
    line = fd.readline()
    if (not line.startswith("Total")):
        print (file_name)
    for line in fd:
        if line.startswith("#"):
            continue;
        line = line.lstrip()
        if (not (line[0].isdigit() or line[0] == "(")):
            print (file_name)
        if (line[0].isdigit()):
            line = line.replace(" ","")
            camps = line.split("|")
            lost = float(camps[3][:-1]) # remove %)
            if (lost < 0):
                print ("----- >negative lost: " +file_name)
                continue                   
            stat.tx_packets = stat.tx_packets + int(camps[2])
            stat.rx_packets = stat.rx_packets + int(camps[1])
            # Latency obtained using rina_echo_time
                        

#*********************************************************************#



traffic_types = ["video_call","gaming","voip","file_sharing","interactive"]
qos_st_dic = {}
for traffic in traffic_types:
    qos_st_dic[traffic] = st.QoS_Statistics(traffic) 


arg = sys.argv
if (len(arg) != 3):
    print ("process_log_directory.py <path> <end_path>")
    sys.exit()
    
path = arg[1]
if (not os.path.exists(path)):
    print ("ERR: The path %s doesn't exist" % (path))
    sys.exit()

end_path = arg[2]
if (not os.path.exists(end_path)):
    reply = str(input(end_path+' not exists. Create it? (y/n): ')).lower().strip() or "y"
    if reply[0] == 'y':
        os.makedirs(end_path)
    if reply[0] == 'n':
        sys.exit(1)
        
nodes = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]            

for node in nodes:
    files_lst = os.listdir("%s/%s/"%(path,node))
    for traffic in traffic_types:
        qos_st = qos_st_dic.get(traffic)
        file_name = "%s/%s/server_%s_%s.rumba.log" % (path,node,traffic,node)
        if (os.path.exists(file_name)):
            processFile(file_name,qos_st)  
        file_mon_lst = [f for f in files_lst if f.startswith(traffic+"_mon")]
        for file_name in file_mon_lst:
            flow_st = pecho.process_echo_file("%s/%s/%s" % (path,node,file_name))
            if (flow_st == None):
                print ("Error processing file: %s" % (file_name))
                continue
            st.Add_FlowStat_to_QoS_Stat(flow_st, qos_st, updateTxRxPak = False)
            # Add CDF
            fd = open("%s/%s.csv" % (end_path,traffic),"a")                
            for delay in flow_st.latency_lst:
                fd.write("%f\n" %(delay))
            fd.close()    
            if (flow_st.endFlow == False):
                print ("Latency statistics for QoS %s not complete: %s. Rx packets: %d" % (qos_st.name, file_name, flow_st.rx_pdus))    
              

for traffic in traffic_types:
    print (str(qos_st_dic.get(traffic)))


