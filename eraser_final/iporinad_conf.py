#!/usr/bin/python3
import os
import sys
import paramiko
import time
 
fd = open("/tmp/rumba/ssh_info","r")
ssh_nodes_info = {}
for line in fd:
    camps = line.split(";")
    ssh_nodes_info[camps[0]] = camps[2]
fd.close

ssh = None
def run_command (host,cmd, background= False):
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, 22, "alopez")
    if (not background):
        (stdin, stdout, stderr) = ssh.exec_command(cmd)
    
        # Wait for the command to terminate
        while not stdout.channel.exit_status_ready() and not stdout.channel.recv_ready():
            time.sleep(1)
        stdoutstring = stdout.readlines()
        for stdoutrow in stdoutstring:
            print (stdoutrow)
        stderrstring = stderr.readlines()
        for stderrrow in stderrstring:
            print (stderrrow)
    else:
        channel = ssh.get_transport().open_session()
        channel.exec_command(cmd+' > /dev/null 2>&1 &')  
    ssh.close()  



arg = sys.argv
if (len(arg) != 2):
    print ("iporinad_conf g[old]|i[interactive]")
    sys.exit()
    
if (arg[1]!="g" and arg[1]!="i"):
    print ("iporinad_conf g[old]|i[interactive]")
    sys.exit()

qos = ""
if (arg[1] == "g"):
    qos = "-L 500 -E 20"
run_command(ssh_nodes_info["c-2-1"],"sudo killall iporinad", True)
run_command(ssh_nodes_info["c-2-2"],"sudo killall iporinad", True)
run_command(ssh_nodes_info["c-0-2"],"sudo killall iporinad", True)
run_command(ssh_nodes_info["s1"],"sudo killall iporinad", True)
run_command(ssh_nodes_info["c-2-1"],"sudo iporinad %s -c ./iporinad_c1.conf" % (qos), True)
run_command(ssh_nodes_info["c-2-2"],"sudo iporinad %s -c ./iporinad_c2.conf" % (qos), True)
run_command(ssh_nodes_info["c-0-2"],"sudo iporinad %s -c ./iporinad_c3.conf" % (qos), True)
run_command(ssh_nodes_info["s1"],"sudo iporinad %s -c ./iporinad_s1.conf" % (qos), True)
