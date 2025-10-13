#!/bin/bash

# Vérification argument
if [ -z "$1" ]; then
  echo "Usage: $0 <nb_ue>"
  exit 1
fi

nb_ue=$1
nb_lines=$((nb_ue * 2))

pod_name=$(kubectl get pods | grep upf | awk '{print $1}')

kubectl logs "$pod_name" -c open5gs-upf \
  | grep -oP 'F-SEID\[UP:\K.*?(?= CP:)' \
  | tail -n "$nb_lines" \
  | sort -u \
  > seid_to_delete.txt

echo "Extracted $(wc -l < seid_to_delete.txt) SEID(s) into seid_to_delete.txt"

liste=$(python3 liste.py)

# Récupère l'IP du pod upf
upf_ip=$(kubectl get pod -o json | jq -r '.items[] | select(.metadata.name | test("upf")) | .status.podIP')

# Récupère l'IP du pod smf
smf_ip=$(kubectl get pod -o json | jq -r '.items[] | select(.metadata.name | test("smf")) | .status.podIP')

echo "UPF IP: $upf_ip"
echo "SMF IP: $smf_ip"
echo "$liste"
rm seid_to_delete.txt

sudo python3 sancus-pfcp-Session-deletion-flag.py "$smf_ip" "$upf_ip" eth1  "$liste"
