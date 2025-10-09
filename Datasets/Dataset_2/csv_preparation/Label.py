import csv
import os

# Crée le dossier de sortie s'il n'existe pas
os.makedirs("labeled", exist_ok=True)

captures = [
    f for f in os.listdir('.')
    if f.endswith('.csv') and f != 'capture_saine10min.csv'
]

for capture in captures:
    input_file = capture
    output_file = f"labeled/{capture}"

    hdr_len_col = "ip.hdr_len"
    timestamp_col = "ip.opt.time_stamp"
    print(f"Processing: {capture}")

    with open(input_file, newline='', encoding="utf-8") as infile, \
         open(output_file, mode="w", newline='', encoding="utf-8") as outfile:

        reader = csv.DictReader(infile, delimiter=';')
        fieldnames = reader.fieldnames

        if hdr_len_col not in fieldnames:
            raise ValueError(f"Colonne '{hdr_len_col}' introuvable.")
        if timestamp_col not in fieldnames:
            fieldnames.append(timestamp_col)

        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        for row in reader:
            hdr_len = row.get(hdr_len_col)
            pfcp_f_teid_teid = row.get("pfcp.f_teid.teid")
            udp_port = row.get("udp.port")

            new_value = None  # Valeur par défaut = non modifié

            if hdr_len:
                try:
                    if float(hdr_len) > 20:
                        if capture == "capture_2_pfcp-DoS.csv":
                            new_value = 0
                        elif capture == "capture2_pfcp_Deletion.csv":
                            new_value = 1
                        elif capture == "capture2_pfcp_Modification.csv":
                            new_value = 2
                        elif "capture_pdn" in capture:
                            new_value = 5
                    else:
                        #if capture in ("api_injection.csv", "api_injection_plusieurs.csv"):
                         #   new_value = 3
                        if row.get("ip.src") in ('192.168.14.187', '192.168.14.149'):
                            new_value = 3
                        elif row.get("ip.src") == '172.19.41.11' or row.get("ip.src") == '172.19.41.9':
                            new_value = 4
                except ValueError:
                    pass

            if "cve" in capture and pfcp_f_teid_teid:
                try:
                    if int(pfcp_f_teid_teid, 16) > 1024 * 4 * 16:
                        new_value = 6
                except ValueError:
                    pass

            # --- Conditions d'écriture ---
            if new_value is not None:
                row[timestamp_col] = new_value
                writer.writerow(row)
            else:#if udp_port == "8805":  # garder ligne même sans new_value si port == 8805
                writer.writerow(row)

