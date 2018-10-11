#!/usr/bin/python3

from rumba.model import *
from rumba.utils import *

import argparse
import sys

from rumba.storyboard import *

class Traffic_type:
    def __init__(self,s_tool, s_options, c_tool, c_options, name, is_bidirectional):
        self.s_tool = s_tool
        self.s_options = s_options
        self.c_tool = c_tool
        self.c_options = c_options
        self.name = name
        self.is_bidirectional = is_bidirectional
        
    def get_server(self, node):   
        server_ap_id = self.name+"_"+node
        return Server(self.s_tool, options=self.s_options.replace("<server_ap_id>", str(server_ap_id)), arrival_rate=0,mean_duration=10,s_id=server_ap_id)
    
    def get_client(self, server_node, client_node, duration):
        server_ap_id = self.name+"_"+server_node
        client_ap_id = self.name+"_"+server_node+"_"+client_node
        cmd_options = self.c_options.replace("<server_ap_id>", str(server_ap_id))
        cmd_options = cmd_options.replace("<client_ap_id>", str(client_ap_id))
        cmd_options = cmd_options.replace("<duration>", str(duration))
        cmd_options = cmd_options.replace("<icmp_ctr>", str(int(duration/0.1))) # used for rina echo time. Pakets each 100 ms
        return Client(self.c_tool, options=cmd_options,c_id=client_ap_id)
    
    def get_server_cmd(self, server_node):
        server_ap_id = self.name+"_"+server_node
        cmd_options = self.s_options.replace("<server_ap_id>", str(server_ap_id))
        log_file = "/tmp/server_"+server_ap_id+".rumba.log"
        return self.s_tool+" "+cmd_options+" > "+log_file+" &"
    
    def get_client_cmd(self, server_node, client_node, instance_number, flowid, duration = 10):
        server_ap_id = self.name+"_"+server_node
        client_ap_id = self.name+"_"+server_node+"_"+client_node
        cmd_options = self.c_options.replace("<server_ap_id>", str(server_ap_id))
        cmd_options = cmd_options.replace("<client_ap_id>", str(client_ap_id))
        cmd_options = cmd_options.replace("<duration>", str(duration))
        cmd_options = cmd_options.replace("<flowid>", str(flowid))
        cmd_options = cmd_options.replace("<icmp_ctr>", str(int(duration/0.1))) # used for rina echo time. Pakets each 100 ms
        log_file = "/tmp/"+client_ap_id+"."+str(instance_number)+"."+str(flowid)+".rumba.log"
        return self.c_tool+" "+cmd_options+" > "+log_file+" &"


    
class Traffic_serv_clients:
    def __init__(self, tr_type, servers_nodes, clients_nodes_per_server, instances_per_client):
        self.tr_type = tr_type
        self.servers_nodes = servers_nodes
        self.clients_nodes_per_server = clients_nodes_per_server
        self.instances_per_client = instances_per_client
        