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
import ast
from functools import partial

from traffic import *
from utils import *
from node_ipcp import *
from enum import Enum
from math import ceil
from def_var import *

log.set_logging_level('DEBUG')


storyboard_duration = 750
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
spn_qta_data={'1.cumux':'2:1:100:100000,100000,0:100000,100000,0',
          '2.cumux':'2:1:100:100000,100000,0:100000,100000,0',
          '3.cumux':'2:1:100:100000,100000,0:100000,100000,0',
          '4.cumux':'2:1:100:100000,100000,0:100000,100000,0',
          '1.qosid':'1:1:250000:1000000000', '2.qosid':'1:2:250000:1000000000', 
          '3.qosid':'2:1:250000:1000000000', '4.qosid':'2:2:250000:1000000000', 
          '5.qosid':'3:1:250000:1000000000', '6.qosid':'3:2:250000:1000000000', 
          '7.qosid':'4:1:250000:1000000000', '8.qosid':'4:2:250000:1000000000'}
video_dif.add_policy("rmt", "qta-mux-ps", **spn_qta_data)
video_dif.add_qos_cube("urgent1_low_loss", delay=20, loss=500, initial_credit=100)
video_dif.add_qos_cube("urgent1_high_loss", delay=20, loss=1000, initial_credit=100)
video_dif.add_qos_cube("urgent2_low_loss", delay=40, loss=500, initial_credit=100)
video_dif.add_qos_cube("urgent2_high_loss", delay=40, loss=1000, initial_credit=100)
video_dif.add_qos_cube("urgent3_low_loss", delay=80, loss=500, initial_credit=100)
video_dif.add_qos_cube("urgent3_high_loss", delay=80, loss=1000, initial_credit=100)
video_dif.add_qos_cube("not_urgent_low_loss", delay=0, loss=1500, initial_credit=100)
video_dif.add_qos_cube("best_effort", delay=0, loss=10000, initial_credit=100)
 
enr_data={'enrollTimeoutInMs':'10000', 
          'watchdogPeriodInMs':'300000', 
          'declaredDeadIntervalInMs':'1200000000', 
          'neighborsEnrollerPeriodInMs':'0', 
          'useReliableNFlow':'false', 
          'maxEnrollmentRetries':'0', 
          'n1flows:spn_dif':'8:20/500:20/1000:40/500:40/1000:80/500:80/1000:0/1500:0/10000'}
video_dif.add_policy("enrollment-task", "default", **enr_data)
  
ra_data={'1.qosid':'20/500', 
         '2.qosid':'20/1000', 
         '3.qosid':'40/500', 
         '4.qosid':'40/1000',
         '5.qosid':'80/500',
         '6.qosid':'80/1000',
         '7.qosid':'0/1500',
         '8.qosid':'0/10000'}
video_dif.add_policy("resource-allocator.pduftg", "default", **ra_data)


# Set QoS Policies
if (spn_dif_policy):
    spn_dif = NormalDIF("spn_dif", add_default_qos_cubes=False)
    spn_dif.add_policy("flow-allocator", "qta-ps")
    spn_qta_data={'1.cumux':'2:1:100:100000,100000,0:100000,100000,0',
          '2.cumux':'2:1:100:100000,100000,0:100000,100000,0',
          '3.cumux':'2:1:100:100000,100000,0:100000,100000,0',
          '4.cumux':'2:1:100:100000,100000,0:100000,100000,0',
          '1.qosid':'1:1:250000:1000000000', '2.qosid':'1:2:250000:1000000000', 
          '3.qosid':'2:1:250000:1000000000', '4.qosid':'2:2:250000:1000000000', 
          '5.qosid':'3:1:250000:1000000000', '6.qosid':'3:2:250000:1000000000', 
          '7.qosid':'4:1:250000:1000000000', '8.qosid':'4:2:250000:1000000000'}
    spn_dif.add_policy("rmt", "qta-mux-ps", **spn_qta_data)
    spn_dif.add_qos_cube("urgent1_low_loss", delay=20, loss=500, initial_credit=100)
    spn_dif.add_qos_cube("urgent1_high_loss", delay=20, loss=1000, initial_credit=100)
    spn_dif.add_qos_cube("urgent2_low_loss", delay=40, loss=500, initial_credit=100)
    spn_dif.add_qos_cube("urgent2_high_loss", delay=40, loss=1000, initial_credit=100)
    spn_dif.add_qos_cube("urgent3_low_loss", delay=80, loss=500, initial_credit=100)
    spn_dif.add_qos_cube("urgent3_high_loss", delay=80, loss=1000, initial_credit=100)
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
                 '6.qosid':'50/800',
                 '7.qosid':'50/250',
                 '8.qosid':'50/800'}
        spn_dif.add_policy("resource-allocator.pduftg", "default", **ra_data)
else:
    spn_dif = NormalDIF("spn_dif")


if (mr_dif_policy):
    mr_dif = NormalDIF("mr_dif", add_default_qos_cubes=False)
    mr_dif.add_policy("flow-allocator", "qta-ps")
    mr_qta_data={'1.cumux':'2:1:100:100000,100000,0:100000,100000,0',
              '2.cumux':'2:1:100:100000,100000,0:100000,100000,0',
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
nodes_lst = node_dif_dic.values()

print ("================================== Number of nodes: %d" % len (nodes_lst))
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
    elif (group.startswith("hrs-")):
        nodes_lst = []
        camps = group.split("-")
        num = camps[1]
        for hr in hr_nodes_lst:
            camps = hr.name.split("-")
            if (camps[-1] == num):
                nodes_lst.append(hr)
        if (len(nodes_lst)==0):
            print ("ERR processing traffic file: No hrs with num %s" % (num))
            return (None)        
        return (nodes_lst)           
    else:
        nodes = group.split(",")
        nodes_lst = []
        for node_name in nodes:   
            node = node_dif_dic.get(node_name)
            if (node == None):
                print ("ERR processing traffic file: Node %s not exists" % (node_name))
                return (None)
            nodes_lst.append(node)
        return(nodes_lst)
    return (None)
    
    
def reconfigureQoS(qos_file,mr_nodes_lst,spn_nodes_lst,video_dif_nodes_lst,node_topology_tb,node_dic_file):    
    fd = open(qos_file,"r")
    dif_name = ""
    nodes = []
    for line in fd:
        if (line[-1] == "\n"):
            line = line[:-1]
        if (line.startswith("dif:")):
            dif_name = (line.split(":"))[1]
            if (dif_name != "spn_dif" and dif_name != "mr_dif" and dif_name != "video_dif"):
                print ("ERR: Wrong QoS file: Unknown dif "+dif_name)
                sys.exit()
            if (dif_name == "video_dif" and spn_nodes_lst != None):
                nodes = video_dif_nodes_lst    
            if (dif_name == "spn_dif" and spn_nodes_lst != None):
                nodes = spn_nodes_lst
            if (dif_name == "mr_dif" and mr_nodes_lst != None):
                nodes = mr_nodes_lst  
            continue
        if (dif_name == ""):
            print ("ERR: Wrong QoS file: No dif defined")
            sys.exit()
        if (len(nodes) == 0):
            continue   
        for node in nodes:
            node_ipcps = node_topology_tb[node.name];
            node_ipcp = get_node_ipcp_with_dif(node_ipcps,dif_name)
            if (node_ipcp != None):
                cmd = "irati-ctl set-policy-set-param "+str(node_ipcp.ipcp_id)+" "+line
            else:
                print ("---IPCPS reload problem : (%s)----" % (node.name))
                for ipcp in node_ipcps:
                    print (ipcp)
                print (str(node_ipcps))
                print (str(node_ipcp))
                print ("DIF name: "+dif_name)
                sys.exit()
            fd = node_dic_file[node.name]
            fd.write(cmd+"\n")
        
def reconfigureTraffic(traffic_file):  
    fd = open(traffic_file,"r")
    traffic_sc_list = []
    for line in fd:
        if (line[-1] == "\n"):
            line = line[:-1]
        if (line.startswith("#")):
            continue
        param_list = line.split("|")
        if (len(param_list) != 9):
            print("==================================================================================")
            print("WARNING: Not valid line -> "+line)
            return (None)
        tr = Traffic_type(param_list[0],param_list[1],param_list[2],param_list[3],param_list[4],param_list[5] == "True")
        server_lst = get_nodes_lst(param_list[7])
        clients_lst = get_nodes_lst(param_list[8])
        if (server_lst == None or (tr.c_tool != None and clients_lst == None)):
            print("==================================================================================")
            print("WARNING: Not valid group -> "+line)
            return (None)
        tr_sc = Traffic_serv_clients(tr,server_lst,clients_lst,int(param_list[6]))
        traffic_sc_list.append(tr_sc)
    fd.close()
    return (traffic_sc_list)      

def newStoryboard(link_capacity=-1, qos_file=None, traffic_file=None, shim2vlan = None):
    node_dic_file = generate_initial_start_scripts(nodes_lst,["spn_dif","mr_dif","video_dif"], node_topology_tb, shim2vlan)
    node_dic_services = {}

    traffic_sc_list = []
    if (traffic_file):
        traffic_sc_list = reconfigureTraffic(traffic_file)
        if (traffic_sc_list == None):
            print ("ERR: No traffic matrix")
            return (None)

    # reconfigure QoS    
    if (qos_file):
	    #reconfigureQoS(qos_file,mr_nodes_lst if mr_dif_policy else [],spn_nodes_lst if spn_dif_policy else [],video_dif_nodes_lst,node_topology_tb,node_dic_file)   
        reconfigureQoS(qos_file,mr_nodes_lst,spn_nodes_lst,video_dif_nodes_lst,node_topology_tb,node_dic_file)
    #Define bandwidth of the link
    print ("LINK ===================>>>>> %d" % (link_capacity))
    if(link_capacity != -1):
        reconfigureLinkCapacity(link_capacity, mr_shim_dif_lst, links_bw_dict, is_link_config, node_dic_file)       
        
    # Generate servers
    for tr_sc in traffic_sc_list:
        tr = tr_sc.tr_type
        for s_n in tr_sc.servers_nodes:
            # add service type to kill later
            node_services_lst = node_dic_services.get(s_n.name)
            if (node_services_lst == None):
                node_services_lst = []
                node_dic_services[s_n.name] = node_services_lst
            if (not tr.s_tool in node_services_lst):
                node_services_lst.append(tr.s_tool)
            # Create server
            fd = node_dic_file[s_n.name]
            fd.write("%s\n" % (tr.get_server_cmd(s_n.name)))
            # If bidireccional traffic
            if (tr.is_bidirectional):
                for c_n in tr_sc.clients_nodes_per_server:
                    # add service type to kill later
                    node_services_lst = node_dic_services.get(c_n.name)
                    if (node_services_lst == None):
                        node_services_lst = []
                        node_dic_services[c_n.name] = node_services_lst
                    if (not tr.s_tool in node_services_lst):
                        node_services_lst.append(tr.s_tool)
                    # Create server
                    fd = node_dic_file[c_n.name]
                    fd.write("%s\n" % (tr.get_server_cmd(c_n.name)))
    
    # Sleep 5 seconds to be sure that all servers are ready
    for fd in node_dic_file.values():
        fd.write("sleep 5 \n")                
                    
                    
    event_number = 0;
    # Generate traffic
    for tr_sc in traffic_sc_list:
        tr = tr_sc.tr_type
        if (tr.c_tool == None):
            continue
        for s_n in tr_sc.servers_nodes:
            for c_n in tr_sc.clients_nodes_per_server:
                for i in range(tr_sc.instances_per_client):
                    fd = node_dic_file[c_n.name]
                    cmd = tr.get_client_cmd(s_n.name, c_n.name, i, event_number, client_duration)
                    fd.write("nohup %s\n" % (cmd))
                    event_number += 1
                    if (tr.is_bidirectional):
                        fd = node_dic_file[s_n.name]
                        cmd = tr.get_client_cmd(c_n.name, s_n.name, i, event_number, client_duration)
                        fd.write("nohup %s\n" % (cmd))
                        event_number += 1
    generate_stop_scripts(node_dic_file, nodes_lst, ["spn_dif","mr_dif","video_dif"], node_topology_tb, node_dic_services, client_duration, storyboard_duration)

def startStoryboard (it_name):
    for node in nodes_lst:
        if (not os.path.exists("nodes_scripts/start_%s.sh" % node.name)):
            print ("==============>>>>>> Node script not generated: "+node.name)
            continue
        node.copy_file("nodes_scripts/start_%s.sh" % node.name, ".")
        node.execute_command("chmod 777 ./*.sh", as_root=True)
    input("Press Enter to start the traffic generator...")
    for node in nodes_lst:    
        node.execute_command("nohup ./start_%s.sh > /tmp/start_script.rumba.log 2>&1 &" % (node.name), as_root=True)

    time.sleep(10+storyboard_duration)
    prefix = "/tmp/rumba/%s_%s/" % (experiment_name,it_name)
    fetch_logs(prefix, nodes_lst)

    for node in nodes_lst:
        cmd = "tar xf %s/%s/%s.rumba.log -C %s/%s/" % \
            (prefix,node.name, node.name,prefix,node.name)
        os.system(cmd)
    calculate_bw_links(nodes_lst, prefix, int(client_duration))
    os.system("cp -r nodes_scripts "+prefix)
    if (os.path.exists("./reconf_link_bw.txt")):
        os.system("cp ./reconf_link_bw.txt "+prefix)

def configure_iporinad_nodes():
    s1 = node_dif_dic["s1"]
    s1.copy_file("files/iporinad_s1.conf",".")
    #s1.execute_command('ifconfig lo:0 10.10.1.1 netmask 255.255.255.0', as_root=True)

    c1 = node_dif_dic["c-%d-%d" % (ir_max_x -1 , 1)]
    c1.copy_file("files/iporinad_c1.conf",".")
    #c1.execute_command('ifconfig lo:0 10.10.2.1 netmask 255.255.255.0', as_root=True)

    c2 = node_dif_dic["c-%d-%d" % (ir_max_x -1 , ir_max_y -1)]
    c2.copy_file("files/iporinad_c2.conf",".")
    #c2.execute_command('ifconfig lo:0 10.10.3.1 netmask 255.255.255.0', as_root=True)

    c3 = node_dif_dic["c-%d-%d" % (0 , ir_max_y -1)]
    c3.copy_file("files/iporinad_c3.conf",".")
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

set_dif_vlan(exp)
if (True):
    for node in nodes_lst:
        ipcps_lst = []
        output = node.execute_command("./get_nodes_ipcs_info.py",as_root = True)
        for line in output.split("\n"):
            ipcps_lst.append(Node_ipcp(line))
        node_topology_tb[node.name] = ipcps_lst  
        
    # Storyboards bucle
    link_capacity = 0
    old_link_capacity = 0
    subname_aux = ""
    qos_file_aux = "traffic/qos.conf"
    traffic_file = "traffic/traffic.conf"
    newTraffic = True
    bw_per_traffic_type = False
    iteration = 0
    
    while (True):
        reply = str(input('Has link capacity previously configured in this experiment(y/n)? [n] ')).lower().strip() or "n"
        if reply[0] == 'y':
            is_link_config = True
            bw_file = "/tmp/rumba/%s_bw_all/link_bw_summary.txt" % (experiment_name)
            if (not os.path.exists(bw_file)):
                print ("Bw all fine not exists")
                continue
            fd = open(bw_file, "r")
            links_bw_dict["bw_all"] = ast.literal_eval(fd.readline())
            print (str(links_bw_dict["bw_all"]))
            fd.close
            break
        if reply[0] == 'n':
            is_link_config = False
            break
    
    while (True):
        while (True):
            reply = str(input('New storyboard (y/n): ')).lower().strip() or "y"
            if reply[0] == 'y':
                break
            if reply[0] == 'n':
                sys.exit(1)

        while (True):
            in_cap = input("Limit link capacity % (0 no limit) ["+str(old_link_capacity)+"]:") or str(old_link_capacity)
            if (in_cap.isdigit):
                int_in_cap = int(in_cap)
                if (int_in_cap == old_link_capacity):
                    link_capacity = -1
                else:
                    if ((int_in_cap > 200 or int_in_cap < 50) and int_in_cap != 0 and int_in_cap != -2):
                        print ("Limit link capacity should be between 50% and 200%")
                        continue
                    if (int_in_cap == -2):
                        int_in_cap = 0
                    link_capacity = int_in_cap
                    old_link_capacity = int_in_cap      
                break
    
        while (True):
            qos_file = None 
            reply = str(input('Change QoS parameters (n/y): ')).lower().strip() or "n"
            if reply[0] == 'y':
                f = input("QoS file ["+qos_file_aux+"]:") or qos_file_aux
                if (f != "-"):   
                    if (os.path.exists(f)):
                        qos_file = f
                        qos_file_aux = qos_file 
                        break
                    print ("File not exists")
                else:
                    break 
            if reply[0] == 'n':    
                break
        
        while (True):
            reply = str(input('Use new traffic matrix ['+traffic_file+'] (n/y): ')).lower().strip() or "n"
            if reply[0] == 'y':
                newTraffic = True
                f = input("Traffic file ["+traffic_file+"]:") or traffic_file
                if (os.path.exists(f)):
                    traffic_file = f
                    while (True):
                        reply = str(input('Check bw per traffic type (n/y): ')).lower().strip() or "n"
                        if reply[0] == 'y':
                            bw_per_traffic_type = True
                            break
                        if reply[0] == 'n':
                            bw_per_traffic_type = False
                            break
                    break    
                print ("File not exists")
            if reply[0] == 'n':
                newTraffic = False
                if (os.path.exists(traffic_file)):
                    break
                print ("File %s not exists" % traffic_file)
        
        while (True):
            duration_str = input("Client duration ["+str(client_duration)+"]:") or str(client_duration)
            if (duration_str.isdigit):
                client_duration = int(duration_str)
                break   
        
        while (True):
            duration_str = input("Storyboard duration ["+str(storyboard_duration)+"]:") or str(storyboard_duration)
            if (duration_str.isdigit):
                storyboard_duration = int(duration_str)
                break     
    
        while (True):
            reply = str(input('Use default storyboard name (y/n): ')).lower().strip() or "y"
            if reply[0] == 'y':
                if (subname_aux != ""):
                    subname = ("%s_%d_%d" % (subname_aux,old_link_capacity,iteration))
                else:
                    subname = ("%d_%d" % (old_link_capacity,iteration))   
                
                dir_name = "/tmp/rumba/%s_%s" % (experiment_name,subname)    
                if (not os.path.exists(dir_name)):
                    iteration = iteration + 1
                    break
                print ("Subname %s already used", subname)
            if reply[0] == 'n':
                iteration = 0    
                subname_aux = input("Subname of storyboard:")
                subname = ("%s_%d_%d" % (subname_aux,old_link_capacity,iteration))
                dir_name = "/tmp/rumba/%s_%s" % (experiment_name,subname)
                if (not os.path.exists(dir_name)):
                    iteration = iteration + 1
                    break
                print ("Subname %s already used", subname)
        
        restart = False
        while (True):
            reply = str(input('Is info correct (y/n) ')).lower().strip() or "y"
            if reply[0] == 'y':
                break
            if reply[0] == 'n':
                restart = True
                break
        if (restart):
            continue   
        
        
        if (newTraffic):
            capacity = -1
            if (old_link_capacity != 0):
                capacity = 0
            # If new traffic, for each type of traffic run a storyboard to get the BW used for each one
            fd = open(traffic_file,"r")
            # aux_traffic_file is used to get bw used for each traffic flow 
            aux_traffic_file = "/tmp/rumba/aux_traffic"
            if (bw_per_traffic_type):
                it = 0 
                for line in fd:
                    if (line[-1] == "\n"):
                        line = line[:-1]
                        if (line.startswith("#")):
                            continue
                        fd1 = open(aux_traffic_file,"w")
                        fd1.write(line)
                        fd1.close()
                        it_name = "bw_"+str(it)
                        newStoryboard(capacity,None,aux_traffic_file,exp.shim2vlan)
                        startStoryboard (it_name)
                        prefix = "/tmp/rumba/%s_%s/" % (experiment_name,it_name) 
                        links_bw_dict[it_name] = calculate_bw_links(nodes_lst, prefix, client_duration)
                        it = it+1
                        capacity = 0
            # Also get bw for all tarffic
            it_name = "bw_all" 
            newStoryboard(capacity,None,traffic_file,exp.shim2vlan)
            startStoryboard (it_name)
            prefix = "/tmp/rumba/%s_%s/" % (experiment_name,it_name) 
            links_bw_dict[it_name] = calculate_bw_links(nodes_lst, prefix, client_duration)
            print ("-------------------------------  BW LINK TABLE -------------------------------")
            print (str(links_bw_dict["bw_all"]))    
            fd.close
            newTraffic = False
            fd1 = open(prefix+"/reconf_link_bw.txt","w")
            fd1.write(str(links_bw_dict["bw_all"])+"\n")
            fd1.close
            continue
         
        print (str(links_bw_dict)) 
        
        newStoryboard(link_capacity,qos_file, traffic_file,exp.shim2vlan) 
        startStoryboard (subname)
        time.sleep(2)

