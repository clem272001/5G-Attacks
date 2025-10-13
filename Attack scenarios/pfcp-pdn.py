from scapy.contrib.pfcp import *
from scapy.all import IP, UDP, Raw, send, IPOption_Timestamp
def imsi_to_bcd(imsi):
    if len(imsi) % 2 != 0:
        imsi += 'f'
    bcd = ''
    for i in range(0, len(imsi), 2):
        bcd += imsi[i+1] + imsi[i]
    return bcd.lower()

def imei_to_bcd_reorder(imei):
    if len(imei) % 2 != 0:
        imei += "F"
    bcd_reordered = ""
    for i in range(0, len(imei), 2):
        bcd_reordered += imei[i+1] + imei[i]
    return bcd_reordered.lower()


def build_create_pdr_1(pdr_id, precedence,source_interface,SD,FAR_ID,URR_ID,QER_ID,ipv4,extra_data=None,):
    create_pdr = IE_CreatePDR(length=69)
    pdr_id_element = IE_PDR_Id(id=pdr_id, extra_data=extra_data,length=2)
    precedence_element = IE_Precedence(precedence=precedence, extra_data=extra_data,length=4)
    pdi = IE_PDI(length=27)
    source_interface_element = IE_SourceInterface(interface=source_interface, extra_data=extra_data,length=1)
    networkInstance = IE_NetworkInstance(instance="internet",length=9)
    ue_ip_address = IE_UE_IP_Address(SD=SD,V4=1,ipv4=ipv4,length=5)
    FARID = IE_FAR_Id(id=FAR_ID,length=4)
    URRID = IE_URR_Id(id=URR_ID,length=4)
    QERID = IE_QER_Id(id=QER_ID,length=4)
    create_pdr /= pdr_id_element /precedence_element /pdi/source_interface_element/networkInstance/ue_ip_address/FARID/URRID/QERID
    return create_pdr

def build_create_pdr_2(pdr_id, precedence,source_interface,   CHID,CH,V6,V4,QFI,    SD,FAR_ID,QER_ID,ipv4,extra_data=None,):
    create_pdr = IE_CreatePDR(length=72)
    pdr_id_element = IE_PDR_Id(id=pdr_id, extra_data=extra_data,length=2)
    precedence_element = IE_Precedence(precedence=precedence, extra_data=extra_data,length=4)
    pdi = IE_PDI(length=32)
    source_interface_element = IE_SourceInterface(interface=source_interface, extra_data=extra_data,length=1)
    FTEID = IE_FTEID(CHID=CHID,CH=CH,V6=V6,V4=V4,length=1)
    networkInstance = IE_NetworkInstance(instance="internet",length=9)
    ue_ip_address = IE_UE_IP_Address(SD=SD,V4=1,ipv4=ipv4,length=5)
    OuterHeaderRemoval=  IE_OuterHeaderRemoval(header=0,length=2,pdu_session_container=1)
    FARID = IE_FAR_Id(id=FAR_ID,length=4)
    QERID = IE_QER_Id(id=QER_ID,length=4)
    create_pdr /= pdr_id_element /precedence_element /pdi/source_interface_element/FTEID/networkInstance/ue_ip_address/OuterHeaderRemoval/FARID/QERID
    return create_pdr


def build_create_far_1():
    create_far = IE_CreateFAR(length=18)
    far_id = IE_FAR_Id(id=1,length=4)
    apply_action = IE_ApplyAction(length=1,NOCP=1,BUFF=1)
    bar_id = IE_BAR_Id(id=1,length=1)
    create_far /= far_id/apply_action/bar_id
    return create_far

def build_create_far_2():
    create_far = IE_CreateFAR(length=35)
    far_id = IE_FAR_Id(id=2,length=4)
    apply_action = IE_ApplyAction(length=1,FORW=1)
    forwarding_parameters = IE_ForwardingParameters(length=18)
    destination_interface = IE_DestinationInterface(interface=1, length=1)
    networkInstance = IE_NetworkInstance(instance="internet", length=9)
    create_far /= far_id/apply_action/forwarding_parameters/destination_interface/networkInstance
    return create_far


def build_session_establishment_request(src_ip, dst_ip, seq, imsi, imei):
    session_request = PFCP(
        version=1,
        S=1,
        message_type=50,
        seq=seq,
        seid=0x0000000000000000
    )
    node_id = IE_NodeId(
        id_type=0,
        ipv4=src_ip,
        length=5
    )
    session_request /= node_id
    fseid = IE_FSEID(
        v4=1,
        seid=0x0000000000000189,
        ipv4=src_ip,
        length=13
    )
    session_request /= fseid
    create_pdr_1 = build_create_pdr_1(pdr_id=1,precedence=255,source_interface=1,SD=1,FAR_ID=1,URR_ID=1,QER_ID=1,ipv4="192.168.100.2") 
    session_request /= create_pdr_1
    create_pdr_2 = build_create_pdr_2(pdr_id=2,precedence=255,source_interface=0,CHID=0,CH=1,V6=1,V4=1,QFI=1,SD=0,FAR_ID=2,QER_ID=1,ipv4="192.168.100.2")
    session_request/=create_pdr_2
    create_far_1 = build_create_far_1()
    session_request /= create_far_1
    create_far_2 = build_create_far_2()
    session_request /= create_far_2

    pdn_type = IE_PDNType(length=1,pdn_type=0)
    session_request /= pdn_type

    imsi_bcd = imsi_to_bcd(imsi)
    imei_bcd = imei_to_bcd_reorder(imei)
    fixed_part = "008d00130308"
    user_id_hex = fixed_part + imsi_bcd + "08" + imei_bcd
    user_id_raw = Raw(bytes.fromhex(user_id_hex))
    session_request /= user_id_raw
    APN_DNN = IE_APN_DNN(length=9,apn_dnn="internet")
    session_request /= APN_DNN
    # Create an IP timestamp option
    msg = 6
    ip_timestamp_option = IPOption_Timestamp(copy_flag=0, optclass='control', option='timestamp', flg=0, timestamp=int(msg))
    ip_packet = IP(src=src_ip, dst=dst_ip, options=[ip_timestamp_option])
    udp_packet = UDP(sport=8805, dport=8805)
    final_packet = ip_packet / udp_packet / session_request
    return final_packet

if __name__ == "__main__":
    smf_ip = "192.168.130.182"
    upf_ip = "192.168.14.162"
    imsi_base = "001010000000002"
    imei_base = 4370816125816153
    seq = 2
    imsi = f"{int(imsi_base):015d}"
    imei = str(imei_base)
    packet = build_session_establishment_request(smf_ip, upf_ip, seq, imsi, imei)
    send(packet)
