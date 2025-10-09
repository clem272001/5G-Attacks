#!/bin/bash

set -e  # Stop if any command fails

# Liste des scripts à exécuter
STEPS=(
    "step1_clean_datasets.py"
    "step2_tcp_flags.py"
    "step3_advanced_clean.py"
    "step4_impute_numerical.py"
    "step5_encoding.py"
    "step6_filtering_labeling.py"
    "step7_z_score_normalization.py"
)

for script in "${STEPS[@]}"; do
    echo "Starting $script ..."
    python3 "$script"
    echo "Finished $script"
    echo "-------------------------------"
done

echo "All steps completed successfully."

