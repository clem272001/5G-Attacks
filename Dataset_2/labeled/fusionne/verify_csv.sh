#!/bin/bash

echo "========== [Analyse ip.opt.time_stamp] =========="

for file in *.csv; do
    echo ""
    echo "[+] Fichier : $file"

    if csvcut -d ';' -n "$file" | grep -q "ip.opt.time_stamp"; then
        echo "  → ip.opt.time_stamp (valeurs uniques) :"
        csvcut -d ';' -c "ip.opt.time_stamp" "$file" | tail -n +2 | sort | uniq -c | sort -nr
    else
        echo "Colonne 'ip.opt.time_stamp' non trouvée dans $file"
    fi
done

#echo ""
echo "========== [Analyse du nombre de colonnes par ligne] =========="

for file in *.csv; do
    echo ""
    echo "[+] Fichier : $file"
    awk -F';' '{print NF}' "$file" | sort | uniq -c
done
