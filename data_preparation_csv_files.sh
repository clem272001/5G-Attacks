#!/bin/bash

# Liste des captures
# Liste des captures
CAPTURES=(
  $(ls pcap_files_dataset_2/*.pcap)
)


FIELDS_FILE="field_list.txt"

# Vérifier que le fichier de champs existe
if [[ ! -f "$FIELDS_FILE" ]]; then
  echo "❌ Fichier $FIELDS_FILE introuvable."
  exit 1
fi

# Lire les champs à extraire
FIELD_OPTS=""
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ -z "$line" || "$line" =~ ^# ]] && continue
  FIELD_OPTS+=" -e $line"
done < "$FIELDS_FILE"

# Créer le dossier de sortie s’il n’existe pas
#mkdir -p dataset_with_all_features

# Boucle sur chaque capture
for capture in "${CAPTURES[@]}"; do
  echo "[+] Traitement : $capture"
  file_name=$(basename "$capture" .pcap)
  output_file="Dataset_2/$file_name.csv"

  tshark -r "$capture" \
    -Y "not (udp.port == 2152)" \
    -T fields $FIELD_OPTS \
    -E header=y -E separator=';' -E quote=d -E occurrence=f \
    > "$output_file"
    
  echo "[✓] Sauvegardé : $output_file"
done
