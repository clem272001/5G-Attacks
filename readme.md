# 5G Attacks Dataset

---

## Repository Structure

```
├── Datasets
│   ├── Dataset_1
│   │   ├── dataset_1.csv
│   │   └── pcap_files_dataset_1/
│   │       └── dataset_1.pcap
│   ├── Dataset_2
│   │   ├── csv_preparation/
│   │   │   ├── capture_*.csv
│   │   │   ├── fusionner.py
│   │   │   └── Label.py
│   │   ├── dataset_2.csv
│   │   └── pcap_files_dataset_2/
│   │       └── capture_*.pcap
│   ├── Dataset_3
│   │   ├── csv_preparation/
│   │   │   ├── capture_*.csv
│   │   │   ├── fusionner.py
│   │   │   └── Label.py
│   │   ├── dataset_3.csv
│   │   └── pcap_files_dataset_3/
│   │       └── capture_*.pcap
│   ├── data_preparation_csv_files.sh
│   └── field_list.txt
├── Data preparation
│   ├── dataset_1_final.csv
│   ├── dataset_2_final.csv
│   ├── dataset_3_final.csv
│   └── preparation/
│       ├── dataset_[1-3]_*.csv
│       ├── pipeline.sh
│       └── step[1-7]_*.py
└── Intrusion Detection Systems
    ├── dataset_1_final.csv
    ├── dataset_2_final.csv
    ├── dataset_3_final.csv
    ├── Figure_iso_macro.png
    ├── Isolation_Forest.py
    ├── KNN.py
    ├── MLP_autoencoder.py
    └── randomforest.py
```

---

## Datasets

The `Datasets` directory contains all the raw and processed traffic data used for building the intrusion detection datasets.

Each dataset folder (`Dataset_1`, `Dataset_2`, `Dataset_3`) includes:
- A `pcap_files_dataset_*` subfolder containing the raw `.pcap` captures.
- A `dataset_*.csv` file generated from feature extraction and CSV preparation/labeling.

**CSV preparation and labeling**
- `Label.py` → assigns attack labels. All labels are written into the `ip.opt.time_stamp` field. If no rule applies the row is kept unchanged.
- `fusionner.py` → merges multiple CSV files from different captures (e.g., distinct attack scenarios).

**Label legend and how each scenario is flagged (written to `ip.opt.time_stamp`)**

| Label | Scenario (short)                                  | Flagging condition (what the script checks)                                                                                                    |
|------:|---------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| **0** | PFCP Flooding — *Denial of Service*               | `ip.hdr_len > 20` **and** input filename == `capture_2_pfcp-DoS.csv`. Writes `0` to `ip.opt.time_stamp`.                                |
| **1** | PFCP Deletion — *Denial of Service*               | `ip.hdr_len > 20` **and** filename == `capture2_pfcp_Deletion.csv`. Writes `1`.                                                               |
| **2** | PFCP Modification — *Denial of Service*           | `ip.hdr_len > 20` **and** filename == `capture2_pfcp_Modification.csv`. Writes `2`.                                                           |
| **3** | NMAP Scan — *Reconnaissance*                      | `ip.hdr_len` missing or `<= 20` **and** `ip.src` is `192.168.14.187` or `192.168.14.149`. Writes `3`. (Detects known scanner IPs.)             |
| **4** | Reverse Shell — *Lateral movement*                | `ip.hdr_len` missing or `<= 20` **and** `ip.src` is `172.19.41.11` or `172.19.41.9`. Writes `4`. (Source IPs identified as compromised hosts.) |
| **5** | UPF PDN-0 Fault — *Denial of Service*             | `ip.hdr_len > 20` **and** filename contains substring `capture_pdn`. Writes `5`.                                                               |
| **6** | PFCP Restoration - TEID DoS — *Denial of Service* | filename contains `cve` **and** `pfcp.f_teid.teid` exists and parsed as hex > `65536`. Writes `6`.                                              |

**Feature extraction**
- The script `Datasets/data_preparation_csv_files.sh` automates the extraction process.
- It reads the list of protocol fields from `Datasets/field_list.txt` and calls `tshark` to export those fields into CSV files.

---

## Data Preparation Pipeline

The preprocessing pipeline (`Data preparation/preparation/`) consists of 7 sequential steps:

| Step | Script | Description |
|------|--------|-------------|
| 1 | `step1_clean_datasets.py` | Removing empty or constant features across the three datasets. |
| 2 | `step2_tcp_flags.py` | Decoding TCP options and splitting them into individual binary variables. |
| 3 | `step3_advanced_clean.py` | Advanced cleaning & removing specific features. |
| 4 | `step4_impute_numerical.py` | Impute missing numerical values. |
| 5 | `step5_encoding.py` | Time conversion & frequency + one-hot encoding. |
| 6 | `step6_correlation_filtering.py` | Pearson correlation filtering. |
| 7 | `step7_z_score_normalization.py` | Normalization of features (z-score). |

To run the full preprocessing pipeline (from the repository root):

```bash
cd "Data preparation/preparation"
chmod +x pipeline.sh   # optional: make pipeline executable
./pipeline.sh          # or: bash pipeline.sh
```

---

## Intrusion Detection Systems

The `Intrusion Detection Systems` folder contains preprocessed datasets, model implementations and evaluation artifacts used to train and evaluate anomaly/classification models.

- `dataset_1_final.csv`, `dataset_2_final.csv`, `dataset_3_final.csv`  
  Final, cleaned, labeled and preprocessed CSV files used as inputs for training and evaluation of the models.

- `Isolation_Forest.py`  
  Unsupervised anomaly detection implementation using an isolation-forest approach.

- `randomforest.py`  
  Supervised Random Forest classifier—trains on labeled data and outputs performance metrics.

- `KNN.py`  
  k-NN baseline classifier.

- `MLP_autoencoder.py`  
  Neural autoencoder for reconstruction-based anomaly detection.

- `Figure_iso_macro.png`  
  Example figure showing macro-averaged Precision–Recall results (used for threshold selection).

---

## Notes & Requirements

- Make sure `tshark` is installed and accessible in your environment (`sudo apt install tshark`).  
- Python dependencies: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `scipy`. Check script headers for exact requirements.  
- Several rules in `Label.py` depend on hard-coded filenames and IPs — update them if your experimental setup changes.
