#!/usr/bin/python3

from rumba.model import *
from rumba.utils import *
from rumba.storyboard import *
import rumba.executors.ssh as ssh
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

storyboard_duration = 5
client_duration = "2"
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
          'declaredDeadIntervalInMs':'120000000', 
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
                  'declaredDeadIntervalInMs':'120000000', 
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
    camps = line.split(";")
    node = node_dic.get(camps[0])
    ipcp = node.get_ipcp_by_dif(shim_dif_dic.get(camps[1]))
    ipcp.ifname = camps[2]
fd.close    
    
for node in exp.nodes:
    node.executor = executor
    ssh_config = node.ssh_config
    ssh_config.username = ssh_nodes_info[node.name][0]
    ssh_config.hostname = ssh_nodes_info[node.name][1]
    ssh_config.port = ssh_nodes_info[node.name][2]

if (False):
    for node in exp.nodes:
        try:
            node.execute_command('reboot', as_root=True)
        except:
            print ("Can't reboot node %s: %s" % (node.name, node.ssh_config.hostname))
            continue
input ("Press return to reload irati:")

if (isQemu):
    hr1.copy_file("files/iporinad_c.conf", ".")
    br1.copy_file("files/iporinad_s.conf", ".")
    for node in nodes_lst:   
        node.copy_file("files/files.tar", ".")
        node.execute_command("tar xf ./files.tar", as_root=True)
else:        
    c.execute_command("nohup socat UDP4-LISTEN:8080,fork,su=nobody UDP6:[%s]:8080 &> /dev/null &" % (destination_ip), as_root=True)
exp.bootstrap_prototype()
write_iface_names(nodes_lst)
write_dif_vlan(exp)
        