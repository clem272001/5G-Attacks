from datetime import datetime
import uuid
from random import getrandbits
from faker import Faker  
from scapy.contrib.pfcp import CauseValues, IE_ApplyAction, IE_Cause, \
    IE_CreateFAR, IE_CreatePDR, IE_CreateURR, IE_DestinationInterface, \
    IE_DurationMeasurement, IE_EndTime, IE_EnterpriseSpecific, IE_FAR_Id, \
    IE_ForwardingParameters, IE_FSEID, IE_MeasurementMethod,IE_OuterHeaderCreation, \
    IE_NetworkInstance, IE_NodeId, IE_PDI, IE_PDR_Id, IE_Precedence, \
    IE_QueryURR, IE_RecoveryTimeStamp, IE_RedirectInformation, IE_ReportType, \
    IE_ReportingTriggers, IE_SDF_Filter, IE_SourceInterface, IE_StartTime, \
    IE_TimeQuota, IE_UE_IP_Address, IE_URR_Id, IE_UR_SEQN, IE_OuterHeaderRemoval,\
    IE_UsageReportTrigger, IE_VolumeMeasurement, IE_ApplicationId, PFCP,IE_FTEID, \
    PFCPAssociationSetupRequest, PFCPAssociationSetupResponse, \
    PFCPHeartbeatRequest, PFCPHeartbeatResponse, PFCPSessionDeletionRequest, \
    PFCPSessionDeletionResponse, PFCPSessionEstablishmentRequest, \
    PFCPSessionEstablishmentResponse, PFCPSessionModificationRequest, \
    PFCPSessionModificationResponse, PFCPSessionReportRequest
from scapy.contrib.pfcp import PFCPAssociationReleaseRequest
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP, TCP
from scapy.layers.inet6 import IPv6
from scapy.packet import Raw
from scapy.all import send, sniff
import logging
import threading
import signal
import os
import sys
from scapy.layers.inet import IP, UDP, TCP, IPOption_Timestamp
from scapy.layers.inet import IPOption  # Import IPOption


# Read command line arguments
PFCP_CP_IP_V4 = sys.argv[1]
PFCP_UP_IP_V4 = sys.argv[2]
N3_IP_V4 = sys.argv[3]
GNB_IP_V4 = sys.argv[4]

print('Starting traffic generation with the following parameters:')
print()
print('PFCP_CP_IP_V4 =', PFCP_CP_IP_V4)
print('PFCP_UP_IP_V4 =', PFCP_UP_IP_V4)
print('N3_IP_V4 =', N3_IP_V4)
print('GNB_IP_V4 =', GNB_IP_V4)
print()
print("UE IP address and SEID are randomly generated")
print()
input("Press Enter to continue...")

faker = Faker()

def seid():
    return uuid.uuid4().int & (1 << 64) - 1

class PfcpSkeleton(object):
    def __init__(self, pfcp_cp_ip, pfcp_up_ip, ue_ip):
        self.pfcp_cp_ip = pfcp_cp_ip
        self.pfcp_up_ip = pfcp_up_ip
        self.ue_ip = ue_ip
        self.ts = int(0)
        self.seq = 1
        self.nodeId = IE_NodeId(id_type=2, id="ergw")
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def ie_ue_ip_address(self, SD=0):
        return IE_UE_IP_Address(ipv4=self.ue_ip, V4=1, SD=SD)

    def ie_fseid(self):
        return IE_FSEID(ipv4=self.pfcp_cp_ip, v4=1, seid=self.cur_seid)

    def associate(self):
        self.chat(PFCPAssociationSetupRequest(IE_list=[
            IE_RecoveryTimeStamp(timestamp=self.ts),
            self.nodeId
        ]))

    def heartbeatRep(self):
        pkt = sniff(iface="veth0", filter="udp port 8805", count=1)
        resp = pkt[0][PFCP]
        self.logger.info("REQ: %r" % resp.message_type)
        if resp.message_type == 1:
            heartReq = resp[PFCPHeartbeatRequest]
            heartRep = PFCPHeartbeatResponse(IE_list=[
                IE_RecoveryTimeStamp(timestamp=self.ts)])
            self.chat(heartRep, resp.seq)

    def heartbeat(self):
        self.chat(PFCPHeartbeatRequest(IE_list=[
            IE_RecoveryTimeStamp(timestamp=self.ts)
        ]))

    def establish_session_request(self):
        self.cur_seid = seid()
        self.chat(PFCPSessionEstablishmentRequest(IE_list=[
            # UPLINK FAR=1, PDR=1
            IE_CreateFAR(IE_list=[
                IE_ApplyAction(FORW=1),
                IE_FAR_Id(id=1)
            ]),
            IE_CreatePDR(IE_list=[
                IE_FAR_Id(id=1),
                IE_PDI(IE_list=[
                    IE_NetworkInstance(instance="access"),
                    IE_SDF_Filter(
                        FD=1,
                        flow_description="permit out ip from any to assigned"),
                    IE_SourceInterface(interface="Access"),
                    self.ie_ue_ip_address(SD=0),
                    IE_FTEID(V4=1, TEID=1111, ipv4=N3_IP_V4)
                ]),
                IE_PDR_Id(id=1),
                IE_Precedence(precedence=200),
                IE_OuterHeaderRemoval(),
            ]),

            # DOWNLINK FAR=2, PDR=2
            IE_CreateFAR(IE_list=[
                IE_ApplyAction(FORW=1),
                IE_FAR_Id(id=2),
                IE_ForwardingParameters(IE_list=[
                    IE_DestinationInterface(interface="Access"),
                    IE_NetworkInstance(instance="n6"),
                    IE_OuterHeaderCreation(GTPUUDPIPV4=1, TEID=2222, ipv4=GNB_IP_V4)
                ])
            ]),
            IE_CreatePDR(IE_list=[
                IE_FAR_Id(id=2),
                IE_PDI(IE_list=[
                    IE_NetworkInstance(instance="n6"),
                    IE_SourceInterface(interface="Core"),
                    self.ie_ue_ip_address(SD=1)
                ]),
                IE_PDR_Id(id=2),
                IE_Precedence(precedence=200),
                IE_OuterHeaderRemoval(),
            ]),
            self.ie_fseid(),
            IE_NodeId(id_type=2, id="cp")
        ]), seid=self.cur_seid)

    def chat(self, pkt, seq=None, seid=None):
        self.logger.info("REQ: %r" % pkt)
        msg = 0
        # Create an IP timestamp option
        ip_timestamp_option = IPOption_Timestamp(copy_flag=0, optclass='control', option='timestamp', flg=0, timestamp=int(msg))
        # Send the packet with the IP timestamp option
        send(
            IP(src=self.pfcp_cp_ip, dst=self.pfcp_up_ip, options=[ip_timestamp_option]) /
            UDP(sport=8805, dport=8805) /
            PFCP(
                version=1,
                S=0 if seid is None else 1,
                seid=0 if seid is None else seid,
                seq=self.seq if seq is None else seq
            ) /
            pkt
        )
        if seq is None:
            self.seq += 1



    def signal_fun(self, signum, frame):
        self.chat(PFCPAssociationReleaseRequest(IE_list=[
            self.nodeId
        ]))
        os._exit(0)

class SessionEstablishmentThread(threading.Thread):
    def __init__(self, threadID, name, pfcp_cp_ip, pfcp_up_ip, n3_ip, gnb_ip):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.pfcp_cp_ip = pfcp_cp_ip
        self.pfcp_up_ip = pfcp_up_ip
        self.n3_ip = n3_ip
        self.gnb_ip = gnb_ip
        self.running = True

    def run(self):
        while self.running:
            UE_IP_V4 = faker.ipv4()
            print(UE_IP_V4)  # Random UE IP
            pfcp_client = PfcpSkeleton(self.pfcp_cp_ip, self.pfcp_up_ip, UE_IP_V4)
            pfcp_client.heartbeat()
            pfcp_client.establish_session_request()
            print(f"Thread {self.threadID}: Session established for UE IP {UE_IP_V4}")
            #time.sleep(1)  # Optional: Adjust the interval between requests

    def stop(self):
        self.running = False

def signal_handler(signum, frame):
    global threads
    print("Stopping threads...")
    for thread in threads:
        thread.stop()
    for thread in threads:
        thread.join()
    print("All threads stopped.")
    sys.exit(0)

if __name__ == "__main__":
    count = 0
    threads = []
    num_threads = 100  # Number of concurrent threads

    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C

    for i in range(num_threads):
        thread = SessionEstablishmentThread(i, f"Thread-{i}", PFCP_CP_IP_V4, PFCP_UP_IP_V4, N3_IP_V4, GNB_IP_V4)
        thread.start()
        threads.append(thread)
        count += 1
        print(f"\n\n\nPackets : {count}\n\n\n")

    # Wait for all threads to finish
    for t in threads:
        t.join()

    print("All threads completed.")
