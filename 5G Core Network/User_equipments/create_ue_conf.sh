#!/bin/bash


COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'

# Directory where configuration files will be stored
config_dir="ue-configs"
mkdir -p $config_dir

# Path to the base configuration file
base_config_file="ue.yaml"

# Check if the base configuration file exists
if [ ! -f $base_config_file ]; then
    echo "Base configuration file $base_config_file not found!"
    exit 1
fi

# Loop to create 50 users
for i in $(seq 1 500); do
    # Create the supi value with correct padding
    supi=$(printf "imsi-999700000000%03d" $i)
    
    # Configuration file name
    config_file="${config_dir}/ue-conf-${i}.yaml"
    
    # Create the configuration file with the specific supi
    echo "# ue-conf.yaml" > $config_file
    echo "supi: '${supi}'" >> $config_file
    
    # Append the content of the base configuration file
    tail -n +4 $base_config_file >> $config_file
done

echo "All 500 users config have been created."
