import os
import argparse
import subprocess
import re
import time

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
RESET = "\033[0m"


nbr_links = 80
nbr_column = 6
start = 1
watch_delay = 0.2


links_total = [("uesimtun"+str(i)) for i in range(start,nbr_links+1)]
# Command to be executed

while True:
    command = "ip -br a | grep uesimtun"
    command2 = "ps aux | grep 'nr-ue -c ue-configs' | wc -l"
    # Execute the command and capture the output
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    result2 = subprocess.run(command2, shell=True, capture_output=True, text=True)

    # Get the output
    output = result.stdout
    output2 = result2.stdout
    
    interfaces = output.split("\n")[:-1]
    links_up = []
    for interface in interfaces:
        links_up.append(re.split(r'\s+', interface)[0])
    
    columns = "".join([("Column"+str(i) + (" \t\t")) for i in range(1,nbr_column+1)])
    #virer uesimtun0
    if "uesimtun0" in links_up:
        links_up.pop(links_up.index("uesimtun0"))
    line = ""
    for link in links_total[:]:
        link_str= link +(" "*(11-len(link)))
        if links_total.index(link)%nbr_column==0:
            line += "\n"
        if link in links_up:
            line += link_str + f": {GREEN}UP\t\t{RESET}"
        else:
            line += link_str + f": {RED}DOWN\t{RESET}"
    os.system("clear")
    print("\nInterface Status\n------------------\n")
    print(columns)
    print(line)
    print("\nTotal links : "+str(len(links_up))+"/"+str(len(links_total))+"\n")
    print("Procces nbr: "+str(int(output2)-2))
    time.sleep(watch_delay)
