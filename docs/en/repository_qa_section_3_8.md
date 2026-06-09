# Repository Q&A (Sections 3.3-3.8)

Scope of analysis: all repository files were reviewed (`scripts`, `docs`, `report`, `planning`, `temp_data`, `logs`, project config files).  
Important context: this repository currently implements dataset inventory/filtering/sorting/export, not model training/evaluation pipelines.

---

## 1. Dataset Selection (Section 3.3)

**Q:** Which specific dataset(s) did you use?  
**A:** Based on actual processed paths in `temp_data`:
- DNS:
  - `CIC-Bell-DNS-2021` (TRAIN + VALIDATION)
  - `CIC-Bell-DNS-EXF-2021` (TRAIN)
  - `Mendeley-DNS-Exfiltration-Dataset` (TEST)
- Host:
  - TRAIN: `ADFA IDS`, `LID-DS 2021`, `Maintainable Log Dataset`
  - VALIDATION: `LID-DS 2019`, `LANL Dataset`, `Windows-Event-Log -OTRF-Security-Datasets`
  - TEST: `Dynamic-Malware-Analysis-Dataset`, `ISOT-Cloud-IDS-Dataset`, `Unified-Host-Network-Dataset -LANL`

**Q:** For each dataset: how many samples total, how many benign vs. malicious, how many features?  
**A:** Not fully specified in this repository. Confirmed values found:
- `CIC-Bell-DNS-2021`: about 1,000,000 domains, about 99% benign (document claim).
- For other datasets, sample counts / class split / feature counts are not provided in repo files.

**Q:** Did you use separate datasets for network and host data, or one dataset?  
**A:** Separate datasets and separate pipelines are used (`dns` and `host` flows are implemented independently in code and JSON outputs).

**Q:** If host-level features were simulated/derived from network data, describe exactly what you did.  
**A:** No implemented feature simulation/derivation logic was found. Only a proposal-level statement exists: feature-level integration/simulation may be used if paired host-network data is unavailable.

---

## 2. Data Preprocessing (Section 3.4.1)

**Q:** How did you handle missing values?  
**A:** No missing-value handling logic for model features is implemented in repository code.

**Q:** Which normalisation method?  
**A:** No normalization/scaling method is implemented (`MinMaxScaler`, `StandardScaler`, etc. are absent).

**Q:** How were categorical features encoded?  
**A:** No categorical encoding implementation found.

**Q:** Train/test split ratio or cross-validation only?  
**A:** No numeric train/test split ratio is implemented. The docs mention planned stratified k-fold cross-validation, but no concrete fold count/config in code.

---

## 3. Class Imbalance (Section 3.4.3)

**Q:** Did you apply SMOTE, random undersampling, class weights, or another technique?  
**A:** No implemented imbalance-mitigation method was found (no SMOTE/undersampling/class-weights code).

---

## 4. Model Architecture Details (Sections 3.5.2 and 3.5.3)

**Q:** Random Forest hyperparameters/tuning?  
**A:** Not specified in code or concrete experiment configs.

**Q:** XGBoost hyperparameters/tuning?  
**A:** Not specified.

**Q:** CNN architecture details?  
**A:** Not specified.

**Q:** LSTM architecture/training details?  
**A:** Not specified. Only proposal-level intent is present (LSTM for sequence-level binary classification).

---

## 5. Sequence Construction (Section 3.6)

**Q:** How many events per sequence?  
**A:** Proposal says planned range is 50-100 events per sequence. No implemented value in code.

**Q:** Sliding window step size / overlap?  
**A:** Not specified in implementation or concrete config.

**Q:** Temporal alignment across modalities?  
**A:** No explicit implemented alignment algorithm found.

---

## 6. Decision Fusion (Section 3.5.4)

**Q:** Exact mechanism?  
**A:** Proposal-level statement: late fusion by aggregating probabilities from classification and sequence components.

**Q:** If weighted, how were weights determined?  
**A:** Not specified.

---

## 7. SHAP Variants (Section 3.7)

**Q:** TreeSHAP for RF/XGBoost?  
**A:** Not specified.

**Q:** DeepSHAP or KernelSHAP for CNN/LSTM?  
**A:** Not specified. Only generic "SHAP-based feature attribution" is documented.

---

## 8. Experimental Environment (Section 3.8)

**Q:** Number of cross-validation folds?  
**A:** "Stratified k-fold cross-validation" is mentioned, but the exact k is not specified.

**Q:** Statistical significance tests used?  
**A:** Not specified (no paired t-test/Wilcoxon config found).

**Q:** Hardware (CPU/GPU/RAM)?  
**A:** Not specified. Docs only mention cloud resources may be used if needed (e.g., Colab/Kaggle).

**Q:** Software versions (Python/libs)?  
**A:** Not specified for ML stack. Repository `requirements.txt` contains only:
- `python-dotenv`
- `rich`
No pinned versions and no ML libraries listed.

**Q:** Random seed?  
**A:** Not specified in code/docs.

---

## Additional factual repository metrics (implemented data-preparation stage)

**Q:** What is actually executed in current codebase?  
**A:** Dataset scanning, role assignment, host filtering, format-based sorting, and path export to JSON.

**Q:** Current processed volume from repository artifacts?  
**A:**
- DNS sorted/exported files: 35 (`temp_data/sort-path-dns-file-summary.json`)
- Host filtered kept file paths: 361,646 (`PATH_REPORT/en/stage-one/Task3...` and `temp_data/sort-path-host-file-summary.json`)
