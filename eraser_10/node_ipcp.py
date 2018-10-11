#!/usr/bin/python3



class Node_ipcp:
    def __init__(self,nodes_ipcs_info):
        list = nodes_ipcs_info.split(":")
        self.ipcp_id = list[0]
        self.dif_name = list[1]
        self.address = None
        self.ports = []
        if (len(list)!=2):
            self.address = list[2]
            ports = list[3].split(",")
            if (len(ports)>1): 
                self.ports = ports[1:]
    
    def __str__(self):
        if (self.address == None):   
            return ("%s:%s" % (self.ipcp_id, self.dif_name))
        else:
            return ("%s:%s:%s:%s" % (self.ipcp_id, self.dif_name,self.address, str(self.ports)))
                
def get_node_ipcp_with_dif (ipcps, dif_name):
    for ipcp in ipcps:
        if (ipcp.dif_name == dif_name):
            return (ipcp)
    return (None)    
    