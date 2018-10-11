#!/usr/bin/python3

from rumba.storyboard import *
from functools import partial
import node_ipcp as nipcp
import ast
        
def write_statistics(nodes_lst,dif_name,node_topology_tb):
    for node in nodes_lst:
        node_ipcps = node_topology_tb[node.name];
        node_ipcp = nipcp.get_node_ipcp_with_dif(node_ipcps,dif_name)
        if (node_ipcp == None):
            continue
        cmd = "./statistics.py %s" % (node_ipcp.ipcp_id)
        node.execute_command(cmd, as_root = True)

def write_iface_names(nodes_lst):
    fd = open("/tmp/rumba/nodes_ifaces","w")
    for node in nodes_lst:
        for dif in node.difs:
            if (dif.name.startswith("e")):
                ipcp = node.get_ipcp_by_dif(dif)
                fd.write("%s;%s;%s\n" % (node.name, dif.name, ipcp.ifname))
    fd.close()

def calculate_bw_links(nodes_lst, path, duration):
    shim_dif_bw = {}
    for node in nodes_lst:
        node_path = path+node.name+"/"
        cmd = "./files/bw.py %s %d" % (node_path,duration)
        cmd_fd = os.popen(cmd)
        fd = open(node_path+"links_bw_statistics.log","w")
        for line in cmd_fd:
            fd.write(line)
            camps = line.split(":")
            if (len(camps)!=5):
                print ("=============================>>>+>  "+line)
                continue
            mean_tx_bw = float(camps[1])
            bw_nodes = shim_dif_bw.get(camps[0]) 
            if (bw_nodes == None):
                bw_nodes = {}
                shim_dif_bw[camps[0]] = bw_nodes
            bw_nodes[node.name] = mean_tx_bw    
        fd.close()
        cmd_fd.close()
        
    fd1 = open(path+"/link_bw_summary.txt","w")
    fd1.write(str(shim_dif_bw)+"\n")
    fd1.close    
    return (shim_dif_bw)


def reconfigureLinkCapacity(link_capacity, shim_dif_lst, links_bw_dict, is_link_config, node_dic_file):
    link_bw = 1000
    fd1 = open("./reconf_link_bw.txt","w")
    fd1.write("New capacity: %s\n" % (link_capacity));
    fd1.write("Not limited bw: %s\n" % (str(links_bw_dict)))
    for dif in shim_dif_lst:
        print ("DIF name " + dif.name)

        for node in dif.members:
            node_name = node.name
            fd = node_dic_file.get(node_name)
            ipcp = node.get_ipcp_by_dif(dif)
            if (link_capacity == 0):
                link_bw = 1000
                bw = 0
                fd.write("tc qdisc del dev %s root\n" % ipcp.ifname)
                fd1.write("=> %s[%s] : no limit\n" % (dif.name, node_name))
            else:
                links_bw_ht = links_bw_dict["bw_all"]
                nodes_bw = links_bw_ht[dif.name]
                bw = nodes_bw[node_name]   
                link_bw = math.floor(bw / (link_capacity / 100))
                if (link_bw > 1000):
                    link_bw = 1000
                if (link_bw == 0):
                    link_bw = 1 
                print("==================>>>===========>>>> %s [%s] -> %f   %d" % (dif.name, node_name ,bw, link_bw ))
                fd1.write("=> %s[%s] : %f  ->  %d\n" % (dif.name, node_name, bw, link_bw))          
                # Set bw:
                if is_link_config:
                    fd.write("tc qdisc del dev %s root\n" % ipcp.ifname)
                fd.write("tc qdisc add dev %s root handle 1: htb default 1\n" % (ipcp.ifname))
                fd.write("tc class add dev %s parent 1: classid 1:1 htb rate %dmbit\n" % (ipcp.ifname, link_bw))
        
    fd1.close()
        
def generate_initial_start_scripts(nodes_lst, dif_name_lst,node_topology_tb, shim2vlan):
    node_dic_file = {}
    os.system("rm nodes_scripts/*")
    for node in nodes_lst:
        fd = open("nodes_scripts/start_"+node.name+".sh","w")
        node_dic_file[node.name]=fd
        fd.write("#!/bin/sh\n")
        fd.write("echo %s\n" % (node.name))
        # Configure start bw monitor
        for dif in node.difs:
            if (dif.name.startswith("e")):
                ipcp = node.get_ipcp_by_dif(dif)
                cmd = "ifconfig %s.%d txqueuelen 1" % (ipcp.ifname, shim2vlan[dif.name])
                fd.write("%s\n" % (cmd))
                cmd = "ifconfig %s txqueuelen 1" % (ipcp.ifname)
                fd.write("%s\n" % (cmd))
                cmd = "nohup  ./if_bw.sh %s > /tmp/%s.rumba.log 2>&1 &" % (ipcp.ifname,dif.name)
                fd.write("%s\n" % (cmd))
        # Write statistics
        for dif_name in dif_name_lst:
            node_ipcps = node_topology_tb[node.name];
            node_ipcp = nipcp.get_node_ipcp_with_dif(node_ipcps,dif_name)
            if (node_ipcp == None):
                continue
            fd.write("./statistics.py %s\n" % (node_ipcp.ipcp_id))
    return (node_dic_file)
        
def generate_stop_scripts(node_dic_file,nodes_lst,dif_name_lst,node_topology_tb, node_dic_services, client_duration, storyboard_duration):
    for node in nodes_lst: 
        computation_time = storyboard_duration - client_duration
        node_services = node_dic_services.get(node.name);
        fd = node_dic_file[node.name]   
        fd.write("sleep %d \n" % (client_duration))
        if (node_services != None and "rina-echo-time" in node_services):
            fd.write("killall -q rina-echo-time 2>&1\n")
            node_services.remove("rina-echo-time")
        fd.write("sleep %d \n" % (computation_time))
  
        fd.write("killall -q if_bw.sh 2>&1\n")
        # Kill servers
        if (node_services != None):
            for service in node_services:
                fd.write("killall -q %s 2>&1\n" % (service))
        # Write statistics
        for dif_name in dif_name_lst:
            node_ipcps = node_topology_tb[node.name];
            node_ipcp = nipcp.get_node_ipcp_with_dif(node_ipcps,dif_name)
            if (node_ipcp == None):
                continue
            fd.write("./statistics.py %s\n" % (node_ipcp.ipcp_id))
        # Compact log files    
        fd.write("cd /tmp\n")
        fd.write("tar cf %s.tar *rumba.log\n" % node.name)
        fd.write("rm *rumba.log\n")
        fd.write("mv %s.tar %s.rumba.log\n" % (node.name,node.name))
        fd.write("cd\n")
        fd.close()

def fetch_logs(local_dir, nodes_lst):

    if not os.path.isdir(local_dir):
        os.mkdir(local_dir)
        
    for node in nodes_lst:
        dst_dir = os.path.join(local_dir, node.name)
        if not os.path.isdir(dst_dir):
            os.mkdir(dst_dir)
        logs_list = node.execute_command('ls /tmp/*.rumba.log '
                                         '|| echo ""')
        logs_list = [x for x in logs_list.split('\n') if x != '']
        logger.debug('Log list is:\n%s', logs_list)
        node.fetch_files(logs_list, dst_dir)

def write_dif_vlan(exp):
    fd = open("/tmp/rumba/dif_vlans","w")
    fd.write(str(exp.shim2vlan))
    print ("====================  shim2vlan ========================== ")
    print (str(exp.shim2vlan))
    fd.close()

    

def set_dif_vlan(exp):
    fd = open("/tmp/rumba/dif_vlans","r")
    exp.shim2vlan = ast.literal_eval(fd.readline())
    print ("====================  shim2vlan ========================== ")
    print (str(exp.shim2vlan))
    fd.close()
