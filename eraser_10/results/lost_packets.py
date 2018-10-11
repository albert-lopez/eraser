#!/usr/bin/python3


import os
import sys
import statistics_structs as st

mr_max1=0
mr_max2=0
spn_max1=0
spn_max2=0
spn_max3=0
spn_max4=0
spn_file_name = ["","","",""]
mr_file_name = ["",""]


def processFile(file_name):
    fd = open(file_name,"r")
    for line in fd:
        line = line [:-1]
        camps = line.split(":")
        if (camps[2]  != "0" or camps[3]  != "0"):
            print (line)
            print ("Drop interface:" +file_name)
            return
        
def processLine(fd,file_name):
    line = fd.readline()
    if not line:
        print ("2:"+file_name)
        sys.exit()               
    line = line [:-1]
    camps = line.split(":")
    if (len(camps)!=8):
        print ("3:"+file_name+"  :"+line)
        sys.exit()
    lost = int(camps[3])+int(camps[4])+int(camps[6])+int(camps[7])
    max = int(camps[0])
    return ((lost,max))
            
        
def processFile2(file_name):
    fd = open(file_name,"r")
    is_spn = False
    if ("spn_dif" in file_name):
        is_spn = True;
    lost = 0
    
    global mr_max1
    global mr_max2
    global spn_max1
    global spn_max2
    global spn_max3
    global spn_max4

    
      
        
    while True:
        line = fd.readline()
        if not line:
            break
        line = line [:-1]
        camps = line.split(":")
        if (len(camps)!=4):
            print ("1:"+file_name)
            sys.exit()
        if (is_spn):
            val = processLine(fd, file_name)
            lost += val[0];
            if (val[1] > spn_max1):
                spn_max1 = val[1]
                spn_file_name[0] = file_name
            val = processLine(fd, file_name)
            lost += val[0];
            if (val[1] > spn_max2):
                spn_max2 = val[1]
                spn_file_name[1] = file_name
            val = processLine(fd, file_name)
            lost += val[0];
            if (val[1] > spn_max3):
                spn_max3 = val[1]
                spn_file_name[2] = file_name
#             val = processLine(fd, file_name)
#             lost += val[0];
#             if (val[1] > spn_max4):
#                 spn_max4 = val[1]
#                 spn_file_name[3] = file_name
        else:
            val = processLine(fd, file_name)
            lost += val[0];
            if (val[1] > mr_max1):
                mr_max1 = val[1]
                mr_file_name[0] = file_name
            val = processLine(fd, file_name)
            lost += val[0];
            if (val[1] > mr_max2):
                mr_max2 = val[1]
                mr_file_name[1] = file_name
    if (lost != 0):
        print ("Drop qtamux: "+file_name +":  "+str(lost))    
                        

#*********************************************************************#



traffic_types = ["vlc_video","vlc","video_call","voip","vpn","hd_video","interactive"]
qos_st_dic = {}
for traffic in traffic_types:
    qos_st_dic[traffic] = st.QoS_Statistics(traffic) 


arg = sys.argv
if (len(arg) != 2):
    print ("lost_packets.py <path>")
    sys.exit()
    
path = arg[1]
if (not os.path.exists(path)):
    print ("ERR: The path %s doesn't exist" % (path))
    sys.exit()

        
nodes = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]            

for node in nodes:
    files_lst = os.listdir("%s/%s/"%(path,node))
    files_ifaces = [f for f in files_lst if f.startswith("e_")]
    for file in files_ifaces:
        processFile("%s/%s/%s"%(path,node,file))
    files_ifaces = [f for f in files_lst if f.startswith("statistics_info")]
    for file in files_ifaces:
        processFile2("%s/%s/%s"%(path,node,file))

print ("SPN_DIF: %d-%d-%d-%d" % (spn_max1, spn_max2, spn_max3, spn_max4))
print (str(spn_file_name))
print ("MR_DIF: %d-%d" % (mr_max1, mr_max2))
print (str(mr_file_name))      
    