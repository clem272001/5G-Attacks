#!/bin/bash

# Liste des captures
# Liste des captures
CAPTURES=(
  $(ls *.pcap)
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
mkdir -p dataset_with_all_features

# Boucle sur chaque capture
for capture in "${CAPTURES[@]}"; do
  echo "[+] Traitement : $capture"

  output_file="${capture%.pcap}.csv"

  tshark -r "$capture" \
    -Y "udp.port == 8805" \
    -T fields $FIELD_OPTS \
    -E header=y -E separator=';' -E quote=d -E occurrence=f \
    > "$output_file"

  echo "[✓] Sauvegardé : $output_file"
done
