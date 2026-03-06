#!/bin/bash

# This script was developed in a VM running Ubuntu 20.04
# Before executing, ensure virtualization is enabled for your machine
# If running inside a VM ensure nested virtualization is supported and enabled
# The installation of the vulnerable kernel version is omitted

set -euo pipefail

# Clone repo
git clone https://github.com/clem272001/5G-Attacks

# Install prerequisites
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-daemon \
virtinst bridge-utils vagrant vagrant-libvirt ansible

sudo systemctl enable --now libvirtd
sudo usermod -aG libvirt $USER

# Create the VMs for master and workers
cd 5G-Attacks/5G\ Core\ Network/
sudo vagrant up

# Give proper permissions to vagrant ssh keys
sudo chmod 600 .vagrant/machines/*/libvirt/private_key

# Load br_netfilter kernel module (required for K8s networking)
# Must do for master and both workers
hosts=("master-open5gs" "worker-open5gs-01" "worker-open5gs-02")

for host in "${hosts[@]}"; do
    echo "Configuring $host..."
    sudo vagrant ssh "$host" << 'REMOTE_EOF'
sudo modprobe br_netfilter
echo "br_netfilter" | sudo tee /etc/modules-load.d/br_netfilter.conf

cat <<'K8S_EOF' | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
K8S_EOF

sudo sysctl --system

REMOTE_EOF
done

# Run ansible playbook for k8s
sudo ansible-playbook -i inventory/vagrant.hosts \
playbooks/ansible-playbook.yaml

# Install required ansible collections
sudo ansible-galaxy collection install kubernetes.core
sudo ansible-galaxy collection install community.general

# Run ansible playbook for open5gs
sudo ansible-playbook -i inventory/vagrant.hosts \
playbooks/open5gs-playbook.yaml

# Pull latest mongodb image and patch it where necessary (default not supported anymore)
echo "Configuring mongodb image in master node..."
sudo vagrant ssh master-open5gs << 'REMOTE_EOF'
sudo docker pull bitnami/mongodb:latest

# Save the Docker image and import to containerd
sudo docker save bitnami/mongodb:latest | sudo ctr -n k8s.io images import --all-platforms -

# Patch mongodb image in deployments
kubectl set image deployment/open5gs-mongodb mongodb=bitnami/mongodb:latest
kubectl set image deployment/open5gs-webui init=bitnami/mongodb:latest

REMOTE_EOF

# This fixes some connectivity issues that the workers had due to restrictive firewall rules (unable to communicate with master node)
for host in "${hosts[@]}"; do
    [[ "$host" == master-* ]] && continue

    echo "Configuring worker $host..."
    sudo vagrant ssh "$host" << 'REMOTE_EOF'
    sudo iptables -I INPUT 1 -i eth1 -j ACCEPT
    sudo iptables -I OUTPUT 1 -o eth1 -j ACCEPT
REMOTE_EOF
done

# Patch deprecated 'mongo' command in webui add_admin script
# New command is 'mongosh'
sudo vagrant ssh master-open5gs << 'REMOTE_EOF'


kubectl get configmap open5gs-webui -o yaml > /tmp/open5gs-webui-cm.yaml

sed -i 's/\bmongo\b/mongosh/g' /tmp/open5gs-webui-cm.yaml

kubectl apply -f /tmp/open5gs-webui-cm.yaml

kubectl rollout restart deployment open5gs-webui

echo "Sleeping 60s for rollout..."
sleep 60

# Delete all pods to start them fresh
echo "Deleting all pods in default namespace..."
kubectl delete pods --all -n default --grace-period=0 --force

echo "Sleeping for pod init..."
sleep 120

REMOTE_EOF

# Vagrant up in case one of the VMs went off (happens sometimes idk why)
sudo vagrant up
sleep 90

echo "\n\nScript finished. Pod status:\n"
sudo vagrant ssh master-open5gs << 'REMOTE_EOF'
    kubectl get pods -n default
REMOTE_EOF

sleep 10

# Expose webui service
sudo vagrant ssh master-open5gs << 'REMOTE_EOF'
    kubectl expose service open5gs-webui --type=NodePort --target-port=9999 --name=webui-ext
REMOTE_EOF

# Get the assigned ports from this output
WEBUI_PORT=$(sudo vagrant ssh master-open5gs -c "kubectl get svc webui-ext -o jsonpath='{.spec.ports[0].nodePort}'")
echo "webui port: $WEBUI_PORT"