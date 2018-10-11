#!/usr/bin/python3

from rumba.model import *
from rumba.utils import *
from rumba.storyboard import *
import rumba.executors.ssh as ssh

# import testbed plugins
import rumba.testbeds.jfed as jfed
import rumba.testbeds.qemu as qemu

# import prototype plugins
import rumba.prototypes.irati as irati

import rumba.log as log
from rumba.utils import ExperimentManager

import statistics
import shutil
import time
import sys
from functools import partial

from traffic import *
from utils import *
from node_ipcp import *
from enum import Enum
from math import ceil
from def_var import *

log.set_logging_level('DEBUG')


storyboard_duration = 900
client_duration = 600

is_link_config = False

class PE_Type(Enum):
    ISP = 1
    DATACENTER = 2
    VIDEO_CLIENT = 3
    NORMAL = 4
    
#********************** SCENARIO BUILD ********************    

shim_dif_dic = {}
node_dif_dic = {}

mr_shim_dif_lst = []
nodes_lst = []
ir_nodes_lst = []
pe_nodes_lst = []
c_pe_nodes_lst = []
s_pe_nodes_lst = []
isp_pe_nodes_lst = []
cloud_pe_nodes_lst = []
hr_nodes_lst = []
client_nodes_lst = []
spn_nodes_lst = []
mr_nodes_lst = []
video_dif_nodes_lst = []
node_topology_tb = {}
links_bw_dict = {} # <name, <dif_name,bw>>

# Set QoS Policies


dcn_dif = NormalDIF("dcn_dif")
# hr_dif is created down
video_dif = NormalDIF("video_dif", add_default_qos_cubes=False)
video_dif.add_policy("flow-allocator", "qta-ps")
spn_qta_data={'1.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '2.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '3.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '1.qosid':'1:1:250000:1000000000', '2.qosid':'1:2:250000:1000000000', 
          '3.qosid':'2:1:250000:1000000000', '4.qosid':'2:2:250000:1000000000', 
          '5.qosid':'3:1:250000:1000000000', '6.qosid':'3:2:250000:1000000000'}
video_dif.add_policy("rmt", "qta-mux-ps", **spn_qta_data)
video_dif.add_qos_cube("urgent1_low_loss", delay=20, loss=500, initial_credit=100)
video_dif.add_qos_cube("urgent1_high_loss", delay=20, loss=1000, initial_credit=100)
video_dif.add_qos_cube("urgent2_low_loss", delay=40, loss=500, initial_credit=100)
video_dif.add_qos_cube("urgent2_high_loss", delay=40, loss=1000, initial_credit=100)
video_dif.add_qos_cube("not_urgent_low_loss", delay=0, loss=1500, initial_credit=100)
video_dif.add_qos_cube("best_effort", delay=0, loss=10000, initial_credit=100)
 
enr_data={'enrollTimeoutInMs':'10000', 
          'watchdogPeriodInMs':'300000', 
          'declaredDeadIntervalInMs':'1200000000', 
          'neighborsEnrollerPeriodInMs':'0', 
          'useReliableNFlow':'false', 
          'maxEnrollmentRetries':'0', 
          'n1flows:spn_dif':'6:20/500:20/1000:40/500:40/1000:0/1500:0/10000'}
video_dif.add_policy("enrollment-task", "default", **enr_data)
  
ra_data={'1.qosid':'20/500', 
         '2.qosid':'20/1000', 
         '3.qosid':'40/500', 
         '4.qosid':'40/1000',
         '5.qosid':'0/1500',
         '6.qosid':'0/10000'}
video_dif.add_policy("resource-allocator.pduftg", "default", **ra_data)


# Set QoS Policies
if (spn_dif_policy):
    spn_dif = NormalDIF("spn_dif", add_default_qos_cubes=False)
    spn_dif.add_policy("flow-allocator", "qta-ps")
    spn_qta_data={'1.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '2.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '3.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '1.qosid':'1:1:250000:1000000000', '2.qosid':'1:2:250000:1000000000', 
          '3.qosid':'2:1:250000:1000000000', '4.qosid':'2:2:250000:1000000000', 
          '5.qosid':'3:1:250000:1000000000', '6.qosid':'3:2:250000:1000000000'}
    spn_dif.add_policy("rmt", "qta-mux-ps", **spn_qta_data)
    spn_dif.add_qos_cube("urgent1_low_loss", delay=20, loss=500, initial_credit=100)
    spn_dif.add_qos_cube("urgent1_high_loss", delay=20, loss=1000, initial_credit=100)
    spn_dif.add_qos_cube("urgent2_low_loss", delay=40, loss=500, initial_credit=100)
    spn_dif.add_qos_cube("urgent2_high_loss", delay=40, loss=1000, initial_credit=100)
    spn_dif.add_qos_cube("not_urgent_low_loss", delay=0, loss=1500, initial_credit=100)
    spn_dif.add_qos_cube("best_effort", delay=0, loss=10000, initial_credit=100)
    if (mr_dif_policy):
        enr_data={'enrollTimeoutInMs':'10000', 
                  'watchdogPeriodInMs':'300000', 
                  'declaredDeadIntervalInMs':'1200000000', 
                  'neighborsEnrollerPeriodInMs':'0', 
                  'useReliableNFlow':'false', 
                  'maxEnrollmentRetries':'0', 
                  'n1flows:mr_dif':'4:10/250:10/800:50/250:50/800'}
        spn_dif.add_policy("enrollment-task", "default", **enr_data)
         
        ra_data={'1.qosid':'10/250', 
                 '2.qosid':'10/800', 
                 '3.qosid':'10/250', 
                 '4.qosid':'10/800',
                 '5.qosid':'50/250',
                 '6.qosid':'50/800'}
        spn_dif.add_policy("resource-allocator.pduftg", "default", **ra_data)
else:
    spn_dif = NormalDIF("spn_dif")


if (mr_dif_policy):
    mr_dif = NormalDIF("mr_dif", add_default_qos_cubes=False)
    mr_dif.add_policy("flow-allocator", "qta-ps")
    mr_qta_data={'1.cumux':'2:1:100:10000,10000,0:10000,10000,0',
              '2.cumux':'2:1:100:10000,10000,0:10000,10000,0',
              '1.qosid':'1:1:250000:1000000000', '2.qosid':'1:2:250000:1000000000', 
              '3.qosid':'2:1:250000:1000000000', '4.qosid':'2:2:250000:1000000000'}
    mr_dif.add_policy("rmt", "qta-mux-ps", **mr_qta_data)
    mr_dif.add_qos_cube("mr_urgent1_low_loss", delay=5, loss=200, initial_credit=100)
    mr_dif.add_qos_cube("mr_urgent1_high_loss", delay=5, loss=700, initial_credit=100)
    mr_dif.add_qos_cube("mr_urgent2_low_loss", delay=30, loss=200, initial_credit=100)
    mr_dif.add_qos_cube("mr_urgent2_high_loss", delay=30, loss=700, initial_credit=100)
else:
    mr_dif = NormalDIF("mr_dif")




def get_pe_type(x,y):
    if ( x==0 and y==0 ):
        return (PE_Type.ISP)
    if ( x== ir_max_x -1 and y==0 ):
        return (PE_Type.DATACENTER)
    if ( x== ir_max_x -1 and y==1 ):
        return (PE_Type.VIDEO_CLIENT)
    if ( x==0 and y == ir_max_y -1 ):
        return (PE_Type.VIDEO_CLIENT)
    if ( x==ir_max_x -1 and y == ir_max_y -1):
        return (PE_Type.VIDEO_CLIENT)
    if ( x== ceil(ir_max_x/2) -1 and y==ir_max_y - 1):
        return (PE_Type.ISP)
    return PE_Type.NORMAL

def build_hr_node(x,y,i,e_pe_hr, have_client=False):   
    node_name = "hr-%d-%d-%d" % (x,y,i) 
    if (have_client):
        hr_dif_name = "%s_dif" % (node_name)
        hr_dif = NormalDIF(hr_dif_name)
        
        e_c_name = "e_hr_%d_%d_%d_c_%d_%d" % (x,y,i,x,y)
        e_c =  ShimEthDIF(e_c_name)
        shim_dif_dic[e_c_name] = e_c
        c_name = "c-%d-%d" % (x,y)
        c_node = Node(c_name,
            difs = [video_dif, hr_dif, e_c],
            dif_registrations = { hr_dif: [e_c], video_dif: [hr_dif]})
        node_dif_dic[c_name] = c_node
        client_nodes_lst.append(c_node)
        video_dif_nodes_lst.append(c_node)
          
        hr = Node(node_name,
            difs = [video_dif, hr_dif, spn_dif, e_pe_hr, e_c],
            dif_registrations = {spn_dif:[e_pe_hr], hr_dif:[e_c], video_dif:[hr_dif,spn_dif]})
        video_dif_nodes_lst.append(hr)
    else:
        hr = Node(node_name,
            difs = [spn_dif, e_pe_hr],
            dif_registrations = {spn_dif:[e_pe_hr]})
    node_dif_dic[node_name] = hr
    hr_nodes_lst.append(hr)

    
def build_br_node(x,y,e1):
    e2_name = "e_br_s1"
    e2 = ShimEthDIF(e2_name)
    shim_dif_dic[e2_name] = e2
    
    br = Node("br",
         difs = [video_dif, dcn_dif, spn_dif, e1, e2 ],
         dif_registrations = { spn_dif: [e1], dcn_dif: [e2], video_dif: [dcn_dif,spn_dif]})
    node_dif_dic["br"] = br
    video_dif_nodes_lst.append(br)
    
    s1 = Node("s1",
         difs = [video_dif, dcn_dif, e2 ],
         dif_registrations = {video_dif: [dcn_dif], dcn_dif: [e2]})
    node_dif_dic["s1"] = s1
    video_dif_nodes_lst.append(s1)
    

def build_pe_node(x,y,e_ir_pe):
    node_name = "pe-%d-%d" % (x,y)
    pe_type = get_pe_type(x,y)
    
    if (pe_type == PE_Type.NORMAL or pe_type == PE_Type.VIDEO_CLIENT):
        shim_dif_lst = []
        for i in range(hr_per_pe):
            e_name = "e_pe_%d_%d_hr_%d" % (x,y,i)
            e = ShimEthDIF(e_name)
            shim_dif_dic[e_name] = e
            shim_dif_lst.append(e)
            
            if (pe_type == PE_Type.VIDEO_CLIENT and i == 0 and use_video_nodes == True):
                build_hr_node(x,y,i,e, True)
            else:
                build_hr_node(x,y,i,e, False)
                
        pe_node =  Node(node_name,
                    difs = [spn_dif, mr_dif, e_ir_pe]+shim_dif_lst,
                    dif_registrations = {spn_dif: [mr_dif]+shim_dif_lst, mr_dif: [e_ir_pe]})
        c_pe_nodes_lst.append(pe_node)
                       
    elif (pe_type == PE_Type.DATACENTER):
        if (use_video_nodes == True):
            e1_name = "e_pe_%d_%d_br" % (x,y)
            e1 = ShimEthDIF(e1_name)
            shim_dif_dic[e1_name] = e1
        
            build_br_node(x,y,e1)
    
            pe_node =  Node(node_name,
                    difs = [spn_dif, mr_dif, e_ir_pe, e1],
                    dif_registrations = {spn_dif:[e1,mr_dif], mr_dif:[e_ir_pe]})
        else:
            pe_node =  Node(node_name,
                    difs = [spn_dif, mr_dif, e_ir_pe],
                    dif_registrations = {spn_dif:[mr_dif], mr_dif:[e_ir_pe]})   
        cloud_pe_nodes_lst.append(pe_node)
        s_pe_nodes_lst.append(pe_node)
    else:
        pe_node =  Node(node_name,
                    difs = [spn_dif, mr_dif, e_ir_pe],
                    dif_registrations = {spn_dif:[mr_dif], mr_dif:[e_ir_pe]})  
        isp_pe_nodes_lst.append(pe_node)
        s_pe_nodes_lst.append(pe_node)     
    
    node_dif_dic[node_name] = pe_node
    pe_nodes_lst.append(pe_node)

def build_ir_node_3(x,y):
    pe_type = get_pe_type(x,y)
    add_pe_node = True
    if (pe_type == PE_Type.DATACENTER and use_video_nodes == False and wall == "wall2"):
        add_pe_node = False
    
    if (add_pe_node):
        e1_name = "e_ir_%d_%d_pe_%d_%d" % (x,y,x,y) 
        e1 = ShimEthDIF(e1_name)
        shim_dif_dic[e1_name] = e1
        build_pe_node(x,y,e1)
    
    if (x == 0):
        e2_name = "e_ir_%d_%d_ir_%d_%d" % (x,y,x+1,y)
        e2 = ShimEthDIF(e2_name)
        shim_dif_dic[e2_name] = e2
        mr_shim_dif_lst.append(e2)
    else:
        e2_name = "e_ir_%d_%d_ir_%d_%d" % (x-1,y,x,y)
        e2 = shim_dif_dic[e2_name]   
    
    if (y == 0):
        e3_name = "e_ir_%d_%d_ir_%d_%d" % (x,y,x,y+1)
        e3 = ShimEthDIF(e3_name)
        shim_dif_dic[e3_name] = e3
        mr_shim_dif_lst.append(e3)
    else:
        e3_name = "e_ir_%d_%d_ir_%d_%d" % (x,y-1,x,y)
        e3 = shim_dif_dic[e3_name]
        
    ir_name = "ir-%d-%d" % (x,y)
    if (add_pe_node):
        ir = Node(ir_name,
             difs = [mr_dif, e1,e2,e3],
             dif_registrations = {mr_dif: [e1,e2,e3]})
    else:
        ir = Node(ir_name,
            difs = [mr_dif,e2,e3],
            dif_registrations = {mr_dif: [e2,e3]})   
    node_dif_dic[ir_name] = ir
    ir_nodes_lst.append(ir)
    
    
def build_ir_node_4(x,y):
    
    #UP
    if (y == 0):
        e1_name = "e_ir_%d_%d_pe_%d_%d" % (x,y,x,y)
        e1 = ShimEthDIF(e1_name)
        shim_dif_dic[e1_name] = e1
        build_pe_node(x,y,e1)
    else:
        e1_name = "e_ir_%d_%d_ir_%d_%d" % (x,y-1,x,y)
        e1 = shim_dif_dic[e1_name]    
    
    #RIGHT    
    if (x == (ir_max_x -1)):
        e2_name = "e_ir_%d_%d_pe_%d_%d" % (x,y,x,y)
        e2 = ShimEthDIF(e2_name)
        shim_dif_dic[e2_name] = e2
        build_pe_node(x,y,e2)
    else:
        e2_name = "e_ir_%d_%d_ir_%d_%d" % (x,y,x+1,y)
        e2 = ShimEthDIF(e2_name)
        mr_shim_dif_lst.append(e2)
        shim_dif_dic[e2_name] = e2   
           
    #DOWN
    if (y == (ir_max_y -1)):
        e3_name = "e_ir_%d_%d_pe_%d_%d" % (x,y,x,y)
        e3 = ShimEthDIF(e3_name)
        shim_dif_dic[e3_name] = e3
        build_pe_node(x,y,e3)
    else:
        e3_name = "e_ir_%d_%d_ir_%d_%d" % (x,y,x,y+1)
        e3 = ShimEthDIF(e3_name)
        mr_shim_dif_lst.append(e3)
        shim_dif_dic[e3_name] = e3
    
    #LEFT
    if (x == 0):
        e4_name = "e_ir_%d_%d_pe_%d_%d" % (x,y,x,y)
        e4 = ShimEthDIF(e4_name)
        shim_dif_dic[e4_name] = e4
        build_pe_node(x,y,e4)
    else:
        e4_name = "e_ir_%d_%d_ir_%d_%d" % (x-1,y,x,y)
        e4 = shim_dif_dic[e4_name]
        
    ir_name = "ir-%d-%d" % (x,y)
    ir = Node(ir_name,
         difs = [mr_dif, e1,e2,e3,e4],
         dif_registrations = {mr_dif: [e1,e2,e3,e4]})
    node_dif_dic[ir_name] = ir
    ir_nodes_lst.append(ir)    
    

# build nodes
for x in range(ir_max_x):
    for y in range(ir_max_y):
        if ((x == 0 or x == ir_max_x - 1) and (y == 0 or y == ir_max_y - 1)):
            build_ir_node_3(x,y)
        else:
            build_ir_node_4(x,y)
            
spn_nodes_lst = pe_nodes_lst + hr_nodes_lst
mr_nodes_lst = pe_nodes_lst + ir_nodes_lst   

print ("==================================")
print (str(shim_dif_dic))
print ("==================================")    
#***************************************************************************            

while (True):
    reply = str(input('JFED testbed (n/y): ')).lower().strip() or "n"
    if reply[0] == 'y':
        isQemu = False
        break
    if reply[0] == 'n':    
        isQemu = True
        break       
    
nodes_lst = node_dif_dic.values()         

if (isQemu):
    tb = qemu.Testbed(exp_name = experiment_name,
                  username = "root",
                  password = "root")
    exp = irati.Experiment(tb, nodes = nodes_lst, enrollment_strategy = 'full-mesh')
else:
    tb = jfed.Testbed(exp_name = experiment_name, 
                  cert_file="cert.pem",
                  username="alopez",
                  proj_name="ERASER",
                  authority = wall+".ilabt.iminds.be",
                  image = wall_image,
                  exp_hours="12",
                  image_custom = True)
    exp = irati.Experiment(tb, nodes = nodes_lst, installpath='', enrollment_strategy = 'full-mesh')            

#***************************************************************************

def get_nodes_lst (group):
    group = group.replace(" ", "")
    group = group.lower()
    if (group == "hr"):
        return(hr_nodes_lst)
    elif (group == "isp"):
        return(isp_pe_nodes_lst)
    elif (group == "cloud"):
        return(cloud_pe_nodes_lst)
    elif (group == "video_server"):
        return ([node_dif_dic["s1"]])
    elif (group == "video_client1"):
        return ([node_dif_dic["c-%d-%d" % (ir_max_x -1 , 1)]])
    elif (group == "video_client2"):
        return ([node_dif_dic["c-%d-%d" % (ir_max_x -1 , ir_max_y -1)]]) 
    elif (group == "video_client3"):
        return ([node_dif_dic["c-%d-%d" % (0 , ir_max_y -1)]])
    elif (group == "video_clients"):
        return (client_nodes_lst)
    elif (group == "c_pes"):
        return(c_pe_nodes_lst)
    elif (group == "s_pes"):
        return(s_pe_nodes_lst)
    else:
        node = node_dif_dic.get(group)
        if (node != None):
            return ([node])
        return(None)


def configure_iporinad_nodes():
    s1 = node_dif_dic["s1"]
    s1.copy_file("files/iporinad_s1.conf",".")
    #s1.execute_command('ifconfig lo:0 10.10.1.1 netmask 255.255.255.0', as_root=True)

    c1 = node_dif_dic["c-%d-%d" % (ir_max_x -1 , 1)]
    c1.copy_file("files/iporinad_c1.conf",".")
    c1.execute_command("nohup socat UDP4-LISTEN:8081,fork,su=nobody UDP6:[%s]:8081 &> /dev/null &" % (destination_ip), as_root=True)
    #c1.execute_command('ifconfig lo:0 10.10.2.1 netmask 255.255.255.0', as_root=True)

    c2 = node_dif_dic["c-%d-%d" % (ir_max_x -1 , ir_max_y -1)]
    c2.copy_file("files/iporinad_c2.conf",".")
    c2.execute_command("nohup socat UDP4-LISTEN:8082,fork,su=nobody UDP6:[%s]:8082 &> /dev/null &" % (destination_ip), as_root=True)
    #c2.execute_command('ifconfig lo:0 10.10.3.1 netmask 255.255.255.0', as_root=True)

    c3 = node_dif_dic["c-%d-%d" % (0 , ir_max_y -1)]
    c3.copy_file("files/iporinad_c3.conf",".")
    c2.execute_command("nohup socat UDP4-LISTEN:8083,fork,su=nobody UDP6:[%s]:8083 &> /dev/null &" % (destination_ip), as_root=True)
    #c3.execute_command('ifconfig lo:0 10.10.4.1 netmask 255.255.255.0', as_root=True)

print(exp)

executor = ssh.SSHExecutor(tb)
fd = open("/tmp/rumba/ssh_info","r")
ssh_nodes_info = {}
for line in fd:
    if (line[-1] == "\n"):
            line = line[:-1]
    camps = line.split(";")
    ssh_nodes_info[camps[0]] = [camps[1],camps[2],camps[3],camps[4]]
fd.close

fd = open("/tmp/rumba/nodes_ifaces","r")
for line in fd:
    line = line[:-1]
    try:
        camps = line.split(";")
        node = node_dif_dic.get(camps[0])
        ipcp = node.get_ipcp_by_dif(shim_dif_dic.get(camps[1]))
    
        ipcp.ifname = camps[2]
    except:
        print (camps[0])
        print (camps[1])
        print (str(shim_dif_dic.get(camps[1])))
        for ipcp in node.ipcps:
            print ("->"+str(ipcp.dif))
fd.close    
    
for node in exp.nodes:
    node.executor = executor
    ssh_config = node.ssh_config
    ssh_config.username = ssh_nodes_info[node.name][0]
    ssh_config.hostname = ssh_nodes_info[node.name][1]
    ssh_config.port = ssh_nodes_info[node.name][2]
    node.execute_command('sudo -s ulimit -c unlimited')
    node.execute_command('sysctl -w kernel.core_pattern=/tmp/core13', as_root=True)


# for node in exp.nodes:
#     try:
#         node.execute_command('reboot', as_root=True)
#     except:
#         print ("Can't reboot node %s: %s" % (node.name, node.ssh_config.hostname))
#         continue
input ("Press return to reload irati:")
if (use_video_nodes):
    configure_iporinad_nodes()
exp.bootstrap_prototype()
write_iface_names(nodes_lst)
write_dif_vlan(exp)
