import os
import time
import random
import subprocess

nbr_ues = 80
ue_processes = {}

# Function to start a UE process
def start_ue(num_ue):
    ue_config = f'ue-conf-{num_ue}.yaml'
    ue_logs = f'ue-logs-{num_ue}.log'
    try:
        with open(f'ue-logs/{ue_logs}', 'wb') as log_file:
            process = subprocess.Popen(
                ["nr-ue", "-c", f"ue-configs/{ue_config}"],
                stdout=log_file,
                stderr=subprocess.STDOUT
            )
            ue_processes[num_ue] = process
            print(f'UE {num_ue} started with PID {process.pid}')
    except Exception as e:
        print(f"Failed to start UE {num_ue}: {e}")

# Function to stop a UE process
def stop_ue(num_ue):
    process = ue_processes.get(num_ue)
    if process:
        try:
            process.terminate()
            process.wait()  # Ensure the process has terminated
            del ue_processes[num_ue]
            print(f'UE {num_ue} with PID {process.pid} stopped')
        except Exception as e:
            print(f"Failed to stop UE {num_ue}: {e}")

# Start initial UE processes
for num_ue in range(1, nbr_ues + 1):
    start_ue(num_ue)
    time.sleep(0.2)
print("\nAll UEs started!\n")
time.sleep(3)
print('Starting traffic changes\n')

# Simulate traffic variation
while True:
    try:
        for _ in range(random.randint(1, 9)):
            ues_to_stop = [num_ue for num_ue in ue_processes.keys() if random.randint(1, 20) == 1]
            if ues_to_stop:
                ue_to_stop = random.choice(ues_to_stop)
                stop_ue(ue_to_stop)
        if len(ue_processes) < 0.8 * nbr_ues:
            range_start = 11
        else:
            range_start = random.randint(1, 11)
        for _ in range(range_start):
            ues_to_start = [num_ue for num_ue in range(1, nbr_ues + 1) if num_ue not in ue_processes.keys()]
            if ues_to_start:
                ue_to_start = random.choice(ues_to_start)
                start_ue(ue_to_start)
    except Exception as e:
        print(f"Error during traffic simulation: {e}")

    # Wait before next variation
    print("Current active UEs:", len(ue_processes))
    time.sleep(random.uniform(0.5, 1.5))
