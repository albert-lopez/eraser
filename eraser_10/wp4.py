#!/usr/bin/python3

from rumba.model import *
from rumba.utils import *
from rumba.storyboard import *
from def_var import *

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

storyboard_duration = 20
client_duration = "10"
isQemu = False
is_link_config = False
node_topology_tb = {}
links_bw_dict = {} # <name, <dif_name,bw>>
traffic_sc_list = []

log.set_logging_level('DEBUG')

e_ir1ir2 = ShimEthDIF("e_ir1ir2")
e_pe1ir1 = ShimEthDIF("e_pe1ir1")
e_pe2ir2 = ShimEthDIF("e_pe2ir2")
e_pe3ir2 = ShimEthDIF("e_pe3ir2")
e_hr1pe1 = ShimEthDIF("e_hr1pe1")
e_hr2pe1 = ShimEthDIF("e_hr2pe1")
e_u1hr1 = ShimEthDIF("e_u1hr1")
e_br1pe2 = ShimEthDIF("e_br1pe2")
e_s1br1 = ShimEthDIF("e_s1br1")
shim_dif_dic = {"e_ir1ir2":e_ir1ir2,"e_pe1ir1":e_pe1ir1,"e_pe2ir2":e_pe2ir2,"e_pe3ir2":e_pe3ir2, "e_hr1pe1":e_hr1pe1, "e_hr2pe1":e_hr2pe1,
                "e_u1hr1":e_u1hr1, "e_br1pe2":e_br1pe2, "e_s1br1":e_s1br1}

mr_shim_dif_lst = [e_ir1ir2]


home_dif = NormalDIF("home_dif")
dcn_dif = NormalDIF("dcn_dif")

video_dif = NormalDIF("video_dif", add_default_qos_cubes=False)
video_dif.add_policy("flow-allocator", "qta-ps")
spn_qta_data={'1.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '2.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '3.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '4.cumux':'2:1:100:10000,10000,0:10000,10000,0',
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
          'declaredDeadIntervalInMs':'12000000', 
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
    spn_qta_data={'1.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '2.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '3.cumux':'2:1:100:10000,10000,0:10000,10000,0',
          '4.cumux':'2:1:100:10000,10000,0:10000,10000,0',
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
                  'declaredDeadIntervalInMs':'12000000', 
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



i1 = Node("i1",
         difs = [mr_dif, e_ir1ir2, e_pe1ir1],
         dif_registrations = {mr_dif: [ e_ir1ir2, e_pe1ir1]})

i2 = Node("i2",
         difs = [mr_dif, e_ir1ir2, e_pe2ir2, e_pe3ir2],
         dif_registrations = {mr_dif: [e_ir1ir2, e_pe2ir2, e_pe3ir2]})

pe1 = Node("pe1",
         difs = [spn_dif, mr_dif, e_hr1pe1, e_hr2pe1, e_pe1ir1],
         dif_registrations = {spn_dif: [e_hr1pe1, e_hr2pe1, mr_dif], mr_dif: [e_pe1ir1]})

pe2 = Node("pe2",
         difs = [spn_dif, mr_dif, e_pe2ir2, e_br1pe2],
         dif_registrations = { spn_dif: [e_br1pe2, mr_dif], mr_dif: [e_pe2ir2]})

pe3 = Node("pe3",
         difs = [spn_dif, mr_dif, e_pe3ir2],
         dif_registrations = { spn_dif: [mr_dif], mr_dif: [e_pe3ir2]})

hr1 = Node("hr1",
         difs = [video_dif, home_dif, spn_dif, e_u1hr1, e_hr1pe1],
         dif_registrations = {home_dif: [e_u1hr1], spn_dif: [e_hr1pe1], video_dif: [home_dif, spn_dif]})

hr2 = Node("hr2",
         difs = [spn_dif, e_hr2pe1],
         dif_registrations = {spn_dif: [e_hr2pe1]})

br1 = Node("br1",
	difs = [video_dif, dcn_dif, spn_dif, e_br1pe2, e_s1br1],
	dif_registrations = {dcn_dif: [e_s1br1], spn_dif: [e_br1pe2], video_dif: [dcn_dif,spn_dif]})

c = Node ("c",
    difs = [e_u1hr1,video_dif, home_dif],
    dif_registrations = {video_dif: [home_dif], home_dif: [e_u1hr1]})

s1 = Node ("s1",
	difs = [e_s1br1,video_dif, dcn_dif],
    dif_registrations = {video_dif: [dcn_dif], dcn_dif: [e_s1br1]})

node_dic = {"i1":i1,"i2":i2, "pe1":pe1, "pe2":pe2 , "pe3":pe3, "hr1":hr1, "hr2":hr2, "br1":br1, "c":c, "s1":s1}


#Agrupation of nodes per type
nodes_hr_lst = [hr2]
nodes_pe_lst = [pe2,pe3]
nodes_lst = [i1, i2, pe1, pe2, pe3, hr1, hr2, c, br1, s1];
spn_nodes_lst = [pe1, pe2, pe3, hr1, hr2, br1]
mr_nodes_lst = [i1, i2, pe1, pe2, pe3]
video_dif_nodes_lst = [c, hr1, br1, s1]
    


while (True):
    reply = str(input('JFED testbed (n/y): ')).lower().strip() or "n"
    if reply[0] == 'y':
        isQemu = False
        break
    if reply[0] == 'n':    
        isQemu = True
        break    

admap = [("rina.apps.echotime.server-1--", "spn_dif") ,("rina.apps.echotime.client-1--", "spn_dif")]    

if (isQemu):
    tb = qemu.Testbed(exp_name = experiment_name,
                  username = "root",
                  password = "root")
    exp = irati.Experiment(tb, nodes = nodes_lst, app_mappings = admap)
else:
    tb = jfed.Testbed(exp_name = experiment_name, 
                  cert_file="cert.pem",
                  username="alopez",
                  proj_name="ERASER",
                  authority = wall+".ilabt.iminds.be",
                  image = wall_image,
                  exp_hours="6",
                  image_custom = True)
    exp = irati.Experiment(tb, nodes = nodes_lst, app_mappings = admap, installpath='', enrollment_strategy = 'full-mesh') 
    
    
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
            cmd = "irati-ctl set-policy-set-param "+str(node_ipcp.ipcp_id)+" "+line
            fd = node_dic_file[node.name]
            fd.write(cmd+"\n")
        
def reconfigureTraffic(traffic_file):  
    fd = open(traffic_file,"r")
    global traffic_sc_list
    server_lst = []
    client_lst = []
    traffic_sc_list = []
    for line in fd:
        if (line[-1] == "\n"):
            line = line[:-1]
        if (line.startswith("#")):
            continue
        param_list = line.split("|")
        param_len = len(param_list)
        if (param_len != 7 and param_len != 8 and param_len != 9):
            print ("ERR traffic conf: "+line)
            continue
        tr = Traffic_type(param_list[0],param_list[1],param_list[2],param_list[3],param_list[4],param_list[5] == "True")
        if (param_len == 7):
            server_lst = nodes_hr_lst
            client_lst = nodes_pe_lst
        else:
            node_name = param_list[7]
            node = node_dic.get(node_name)
            if (node != None):
                node = node_dic[node_name]
                server_lst = [node]
                client_lst = []
            else:
                print ("==========>>> Reconfigure traffic: node %s not exists" % (node_name))
                continue
            if (param_len == 9):
                node_name = param_list[8]
                node = node_dic.get(node_name)
                if (node != None):
                    node = node_dic[node_name]
                    client_lst = [node]
                else:
                    print ("==========>>> Reconfigure traffic: node %s not exists" % (node_name))
                    continue
            else:
                client_lst = []
                
                  
        tr_sc = Traffic_serv_clients(tr,server_lst,client_lst,int(param_list[6]))
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
    

    generate_stop_scripts(node_dic_file, nodes_lst, ["spn_dif","mr_dif","video_dif"], node_topology_tb, node_dic_services,client_duration, storyboard_duration)

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

with ExperimentManager(exp,swap_out_strategy=PAUSE_SWAPOUT):
    exp.swap_in()
    
    c.copy_file("files/iporinad_c.conf", ".")
    s1.copy_file("files/iporinad_s.conf", ".")
    if (not isQemu):
        s1.copy_file("files/video.mp4", ".")
        c.execute_command("nohup socat UDP4-LISTEN:8080,fork,su=nobody UDP6:[%s]:8080 &> /dev/null &" % (destination_ip), as_root=True)
    for node in nodes_lst:   
        node.copy_file("files/files.tar", ".")
        node.execute_command("tar xf ./files.tar", as_root=True)
        if (not isQemu):
            node.execute_command("nohup ./mon.sh > /tmp/mon.log 2>&1 &")

    exp.bootstrap_prototype()
    
    write_iface_names(nodes_lst)
    write_dif_vlan(exp)
    
    for node in nodes_lst:
        ipcps_lst = []
        output = node.execute_command("./get_nodes_ipcs_info.py",as_root = True)
        for line in output.split("\n"):
            ipcps_lst.append(Node_ipcp(line))
        node_topology_tb[node.name] = ipcps_lst   
    
#         # Configure IP networking
#     ipcp = c.get_ipcp_by_dif(e_u1hr1)
#     c.execute_command('ifconfig ' + ipcp.ifname + ' 10.10.0.2 netmask 255.255.255.0', as_root=True)
#     c.execute_command('ip route add 10.10.1.0/24 via 10.10.0.1 dev ' + ipcp.ifname, as_root=True)
#     ipcp = hr1.get_ipcp_by_dif(e_u1hr1)
#     hr1.execute_command('ifconfig ' + ipcp.ifname + ' 10.10.0.1 netmask 255.255.255.0', as_root=True)
#     
#     ipcp = s1.get_ipcp_by_dif(e_s1br1)
#     s1.execute_command('ifconfig ' + ipcp.ifname + ' 10.10.1.2 netmask 255.255.255.0', as_root=True)
#     s1.execute_command('ip route add 10.10.0.0/24 via 10.10.1.1 dev ' + ipcp.ifname, as_root=True)
#     ipcp = br1.get_ipcp_by_dif(e_s1br1)
#     br1.execute_command('ifconfig ' + ipcp.ifname + ' 10.10.1.1 netmask 255.255.255.0', as_root=True)
#     
#     # Add routes to tun just in case they are not created
#     time.sleep(2)
#     try: 
#         hr1.execute_command('ip route add 10.10.1.0/24 dev tun0',  as_root=True)
#         br1.execute_command('ip route add 10.10.0.0/24 dev tun0',  as_root=True)
#     except:
#         print ("Route already configured")    
#     
#     if (isQemu):
#         hr1.execute_command('echo 1 > /proc/sys/net/ipv4/ip_forward', as_root=True)
#         br1.execute_command('echo 1 > /proc/sys/net/ipv4/ip_forward', as_root=True)
    
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

