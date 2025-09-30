import pandas as pd

df = pd.read_csv('dataset_1_scaled.csv', sep=';')
col_list = df.columns

ip_cols = [c for c in col_list if c.startswith("ip.")]
tcp_cols = [c for c in col_list if c.startswith("tcp.")]
udp_cols = [c for c in col_list if c.startswith("udp.")]
pfcp_cols = [c for c in col_list if c.startswith("pfcp.")]

# Colonnes restantes
other_cols = [c for c in col_list if not (
    c.startswith("ip.") or c.startswith("tcp.") or c.startswith("udp.") or c.startswith("pfcp.")
)]

print(f"{len(ip_cols)} IP : {ip_cols}")
print(f"{len(tcp_cols)} TCP : {tcp_cols}")
print(f"{len(udp_cols)} UDP : {udp_cols}")
print(f"{len(pfcp_cols)} PFCP : {pfcp_cols}")
print(f"{len(other_cols)} Autres : {other_cols}")
