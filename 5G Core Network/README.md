
This guide covers the full setup and configuration Open5GS on a Kubernetes cluster.

## **1. Recommended Kernel Version: Linux 5.8.0**

To ensure compatibility, install the recommended Linux kernel version:
```bash
sudo apt install linux-image-5.8.0-63-generic linux-headers-5.8.0-63-generic
```

---
## **2. Open5GS Setup**

### **Step 1: Extract Open5GS**
```bash
tar -xvf open5gs.tgz
```

### **Step 2: Set Up Open5GS Kubernetes Cluster**
Run the Ansible playbook to configure the Kubernetes cluster for Open5GS:
```bash
ansible-playbook -i inventory/vagrant.hosts playbooks/ansible-playbook.yaml
```

### **Step 3: Set Up Open5GS**
```bash
ansible-playbook -i inventory/vagrant.hosts playbooks/open5gs-playbook.yaml
```

### **To start the Cluster:**
```bash
  sudo vagrant up (in the cluster directory)
```

### **To connect to the VMs:**
```bash
  Master : sudo vagrant ssh master-open5gs
  Worker01: sudo vagrant ssh worker-open5gs-01
  Worker02: sudo vagrant ssh worker-open5gs-02
```

### **To stop the Cluster:**
```bash
  sudo vagrant halt (in the cluster directory)
```

### **To manage snapshot:**
```bash
  sudo vagrant snapshot (list, save, ...)
```

**Expose the Open5GS Web UI:**
```bash
kubectl expose service open5gs-webui --type=NodePort --target-port=9999 --name=webui-ext
```

### **Web UI:**
- **Web UI Credentials:**
    - Username: `admin`
    - Password: `1423`

---

## **4. User Traffic Generation Scripts**

These scripts will simulate user equipment (UE) traffic.

### **Step 1: Create UE Configuration File**
In the `User_equipment_script` folder, generate UE configurations:
```bash
bash create_ue_conf.sh
```

### **Step 2: Add Subscribers to Open5GS Database**
```bash
python3 add_subscribers_open5gs_mongodb.py
```

### **Step 3: Simulate Traffic Variation (UE Connection/Disconnection)**
```bash
python3 generate_ue_pfcp_traffic.py
```

### **Step 4: Monitor UE Traffic**
```bash
python3 monitoring.py
```

---