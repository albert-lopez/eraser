#!/usr/bin/python3

import sys

class QoS_Statistics:
    def __init__(self, name):
        self.name = name
        self.latency_min = sys.maxsize
        self.latency_max = 0
        self.latency_avg = 0
        self.rx_packets_mon = 0  # ctr of packets used to obtain average latency
        self.rx_packets = 0
        self.tx_packets = 0
    def __str__(self):
        if (self.tx_packets != 0): 
            lost = ((self.tx_packets-self.rx_packets)/self.tx_packets)*100
        else:
            lost = 0    
        return "QoS: %s \n\t min_latency: %f \n\t avg_latency: %f\n\t max_latency: %f \n\t rx pdus: %d \n\t tx pdus: %d \n\t lost: %f \n" % \
            (self.name, self.latency_min, self.latency_avg, self.latency_max, self.rx_packets, self.tx_packets, lost)    

class FlowStat:
    def __init__(self):
        # times in us
        self.latency_min = sys.maxsize
        self.latency_max = 0
        self.latency_avg = 0
        self.latency_lst = []
        self.endFlow = False
        self.rx_pdus = 0
        self.tx_pdus = 0
        self.lost = 0
    def __str__(self):
        return "\t min_latency: %f \n\t avg_latency: %f\n\t max_latency: %f \n\t rx_pdus: %d \n\t tx_pdus: %d \n" % (self.latency_min, self.latency_avg, self.latency_max, self.rx_pdus,self.tx_pdus)    


# Used only for monitor flows
def Add_FlowStat_to_QoS_Stat(flow_stat, qos_stat, updateTxRxPak = True):
    if (qos_stat.latency_min > flow_stat.latency_min): qos_stat.latency_min = flow_stat.latency_min
    if (qos_stat.latency_max < flow_stat.latency_max): qos_stat.latency_max = flow_stat.latency_max
    latency_avg = 0
    if (qos_stat.rx_packets_mon != 0):
        latency_avg = qos_stat.latency_avg * qos_stat.rx_packets_mon
        latency_avg += flow_stat.latency_avg*flow_stat.rx_pdus
        qos_stat.rx_packets_mon += flow_stat.rx_pdus
        qos_stat.latency_avg = latency_avg / qos_stat.rx_packets_mon
    else:
        qos_stat.latency_avg = flow_stat.latency_avg
        qos_stat.rx_packets_mon = flow_stat.rx_pdus
    if (updateTxRxPak and flow_stat.tx_pdus != 0):    
        qos_stat.rx_packets += flow_stat.rx_pdus
        qos_stat.tx_packets += flow_stat.tx_pdus
