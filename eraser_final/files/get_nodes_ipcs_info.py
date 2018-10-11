#!/usr/bin/python3


import os

path = "/sys/rina/ipcps/"

def read_value(file):
    fd = open(file,"r")
    value = fd.read()
    fd.close()
    return (value[:-1])

def print_normal_dif(ipcp_id):
    aux_dif_name = read_value(path+ipcp+"/name")
    dif_name = aux_dif_name.split(".")[0]
    address = read_value(path+ipcp+"/address")
    ports = [p for p in os.listdir(path+ipcp+"/rmt/n1_ports/") if os.path.isdir(os.path.join(path, p))]
    port_str = ""
    for port_id in ports:
        port_str = port_str+","+port_id
    print ("%s:%s:%s:%s" % (ipcp_id,dif_name,address,port_str))
    
def print_eth_dif(ipcp_id):
    aux_dif_name = read_value(path+ipcp+"/name")
    dif_name = aux_dif_name.split(".")[1]
    print ("%s:%s" % (ipcp_id,dif_name))        

ipcps = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]


for ipcp in ipcps:
    dif_type = read_value(path+ipcp+"/type")
    dif_type = dif_type
    if (dif_type == "normal"):
        print_normal_dif(ipcp)
    elif (dif_type == "shim-eth-vlan"):
        print_eth_dif(ipcp)
  
