#!/usr/bin/python3


import os
import sys


def read_value(file):
    fd = open(file,"r")
    value = fd.read()
    fd.close()
    return (value[:-1])
        
arg = sys.argv
if (len(arg)!=2):
    print ("statistics.py <dif_id>")
    sys.exit()
path = "/sys/rina/ipcps/"+str(arg[1])+"/rmt/n1_ports/"


aux_dif_name = read_value("/sys/rina/ipcps/"+str(arg[1])+"/name")
dif_name = aux_dif_name.split(".")[0]

if (dif_name == "spn_dif" or dif_name == "video_dif"): 
    urgencies = 3
    cheries = 2
if (dif_name == "mr_dif"):
    urgencies = 2
    cheries = 2


file_result = "/tmp/statistics_info.%s.rumba.log" % (dif_name)
file_result2 = "/tmp/statistics_h_info.%s.rumba.log" % (dif_name)
file_old = "/tmp/last_drop_pdus.%s.log" % (dif_name)
file_current = "/tmp/current_drop_pdus.%s.log" % (dif_name)
file_exist = False

fd_current = open(file_current,"w")    




ports = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
ports.sort()
for port in ports:
    # Summary of drop packets per port
    tx_pdus = read_value("%s%s/tx_pdus" % (path,port))
    drop_pdus = read_value("%s%s/drop_pdus" % (path,port))
    fd_current.write("port:%s:%s:%s\n" % (port,tx_pdus,drop_pdus))
    # Drop packets of the port divided by  urgencies level
    for u_l in range(1,urgencies+1):
        tx_cumux = read_value("%s%s/qta_mux/cumux/urgency_queues/%d/tx_pdus" % (path,port,u_l))
        max_queue = read_value("%s%s/qta_mux/cumux/urgency_queues/%d/max_occupation" % (path,port,u_l))
        info = "%s:%s" % (max_queue,tx_cumux)
        for c_l in range(1,cheries+1):
            qosid = (u_l-1)*cheries + c_l
            tx_pdu_ps = read_value("%s%s/qta_mux/token_bucket_filters/%d/tbf_tx_pdus" % (path,port,qosid))
            drop_ps = read_value("%s%s/qta_mux/token_bucket_filters/%d/tbf_drop_pdus" % (path,port,qosid))
            drop_cumux_qos = read_value("%s%s/qta_mux/token_bucket_filters/%d/dropped_pdus_cu_mux" % (path,port,qosid))
            info = "%s:%s:%s:%s" %(info,tx_pdu_ps,drop_ps,drop_cumux_qos)
        fd_current.write("%s\n" %(info))  
fd_current.close()

if (os.path.exists(file_old)):
    file_exist = True
if (file_exist):
    fd_end = open(file_result,"w")
    fd_old = open(file_old,"r")
    fd_current = open(file_current,"r") 
    while True:
        line1 = fd_old.readline()
        line2 = fd_current.readline()
        if not line1:
            break
        line1 = line1[:-1]
        line2 = line2[:-1]
        if (line1.startswith("port")):
            camps1 = line1.split(":")
            camps2 = line2.split(":")
            fd_end.write("port:%s:%d:%d\n" % (camps1[1], int(camps2[2]) - int(camps1[2]), int(camps2[3]) - int(camps1[3])))
        else:
            camps1 = line1.split(":")
            camps2 = line2.split(":")
            info = camps2[0]    
            for i in range (1,len(camps1)):
                info = "%s:%d" % (info,  int(camps2[i]) - int(camps1[i])) 
            fd_end.write("%s\n" % (info))
    fd_end.close()
    fd_current.close()
    fd_old.close()            
else:
    os.system("cp %s %s" % (file_current, file_result))

fd_end = open(file_result,"r")
fd_end_h = open(file_result2,"w")

urgency = 0
while True:
    line1 = fd_end.readline()
    if (line1 == None or line1 == ""):
        break
    if (line1.startswith("port")):
        camps = line1.split(":")
        try:
            fd_end_h.write("Port: %s, Tx PDUs: %s, Drop PDUs: %s\n" % (camps[1], camps[2], camps[3]))
        except:
            print (line1)
            print ("Statistics process line error 1")
            sys.exit()    
        urgency = 0
    else:
        camps = line1.split(":")
        try:
            info = "   Urg_Lev: %d,  Max Queue: %s, Tx Cumux %s" % (urgency, camps[0], camps[1])
            for c_l in range(cheries): 
                info = "%s, Cher_Lev: %d, Tx P/S: %s, Drop P/S: %s, Drop Cumux: %s" % (info, c_l, camps[c_l*3+2], camps[c_l*3+3], camps[c_l*3+4])
            fd_end_h.write(info+"\n");
        except:
            print (line1)
            print ("Statistics process line error 2")
            sys.exit()  
    urgency = urgency+1
    
os.system("mv %s %s" % (file_current, file_old))

       
