#!/usr/bin/python3
import os
import multiprocessing.dummy
import multiprocessing

def ping(node_info):
    response = os.system("ping6 -c 1 %s > /dev/null" %(node_info[0]))
    if response == 0:
        print ("%s[%s]: ok" % (node_info[1],node_info[0]))
    else:
        print ("==> %s[%s]: KO" % (node_info[1],node_info[0])) 


nodes = []

fd = open("/tmp/rumba/ssh_info","r")
for line in fd:
    camps = line.split(";")
    nodes.append([camps[2],camps[0]])
fd.close

p = multiprocessing.dummy.Pool(10)
   
p.map(ping, nodes)


 

