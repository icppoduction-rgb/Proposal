# Project Proposal Analysis

---

## Short Summary

The document is a project proposal titled **"Behaviour-driven hybrid learning for data exfiltration detection"**. The core research idea is to develop a hybrid ML/DL framework for data exfiltration detection that combines network features, host-level telemetry, behavioural sequence modelling, and SHAP-based explainability.

---

## Strengths

| Aspect | Assessment |
|:---|:---|
| Topic relevance | Data exfiltration, APTs, insider threats, DNS tunnelling, and encrypted traffic are significant cybersecurity problems |
| Research gap | Consistently shows limitations of single-modality approaches and lack of sequence modelling |
| Structure | Logical: Abstract → Background → Problem Statement → Research Questions → Aim/Objectives → Scope → Methodology → Plan |
| Methodology | Design Science Research is suitable for developing and evaluating a detection framework artifact |
| Limitations | Explicitly limited by time, data availability, and computing resources |
| Evaluation plan | Accuracy, precision, recall, F1-score, FPR, AUC, ablation study, and cross-validation are specified |

---

## Potential Weaknesses

> **1. Risk of insufficient alignment between host and network datasets.**
> The text acknowledges that paired datasets may be unavailable, so feature-level integration and simulation must be described as rigorously as possible.

> **2. Reproducibility needs to be strengthened.**
> It would be useful to explicitly specify the datasets, preprocessing steps, train/test split strategy, and baseline models.

> **3. SHAP for the LSTM/sequence component requires caution.**
> The proposal should clarify whether KernelSHAP, DeepSHAP, or explanations of aggregated features will be used.

> **4. Some claims depend on source currency.**
> Bibliographic references were not separately verified for DOI existence and correctness during conversion.

> **5. Grammar and academic style require local editing.**
> Some phrases should be reformulated to achieve a more formal academic tone.

---

## Recommendations for Revision

1. Add a separate table of selected datasets: name, telemetry type, classes, size, source, and limitations.
2. Clearly describe the mechanism for combining host and network features, especially if the data is not paired.
3. Clarify the late fusion architecture: probability aggregation formula/rule, component weights, and threshold selection criterion.
4. Add baseline comparisons: Random Forest only, XGBoost only, CNN only, LSTM only, hybrid without SHAP, and full hybrid.
5. Clarify how explainability will be evaluated: rank stability, case studies, and alignment with MITRE ATT&CK tactics.
6. Verify all DOI links and bibliographic metadata before final submission.

---

## Final Assessment

> The project proposal is substantively strong and methodologically consistent. The main risk is the practical implementation of multi-source integration when compatible host/network datasets are unavailable. If this risk is addressed through a clear feature-level integration scheme, transparent baseline experiments, and a reproducible evaluation pipeline, the work will be convincing both academically and practically.

---
---

# INDIVIDUAL ASSIGNMENT 2 — PROJECT PROPOSAL

| Field | Value |
|:---|:---|
| **Name / TP Number** | Djumakhodjaeva Malika / TP099270 |
| **Intake Code** | APUMF2508CYS(PR) |
| **Module Code** | CT095-6-M-RMCE |
| **Module Title** | Research Methodology in Computing and Engineering |
| **Module Lecturer** | Dr. Murugananthan Velayutham |
| **Nominated Supervisor** | Dr. Jalil Md Desa |
| **Project Title** | Behaviour-driven hybrid learning for data exfiltration detection |
| **Date Assigned** | February 6, 2026 |
| **Date Completed** | April 24, 2026 |

---

# Abstract

Data exfiltration is among the most severe and complex cybersecurity threats faced by modern organizations as it is covert, persistent, and multi-stage in nature. Traditional intrusion detection systems have proven to be significantly limited in detection of sophisticated exfiltration techniques, especially those that utilize encrypted communication channels, insider threats, and advanced persistent threats. Although recent studies have explored machine learning and deep learning approaches to enhance the detection capabilities, the majority of existing systems use a single data modality — either network traffic or host-level telemetry — and do not model the sequential behavioural patterns that characterize the progressive stages of data exfiltration attacks.

This proposal presents a **behaviour-driven hybrid machine learning framework** designed to address these limitations by integrating host telemetry, network traffic analysis, and behavioural sequence modelling within a unified detection architecture. The proposed framework will integrate classical ensemble methods like Random Forest and XGBoost, and components of CNN deep learning with LSTM-based behavioural sequence modelling to capture both structured feature patterns and complex temporal relationships in multi-source security data. The framework will be further integrated with explainable artificial intelligence technique, namely SHAP-based feature attribution, to enhance the interpretability of the detection decisions and facilitate the workflows of security analysts. The framework will be evaluated using publicly available cybersecurity benchmark datasets with performance assessed using standard classification metrics.

The research is expected to contribute an enhanced hybrid detection framework that will extend existing approaches, advance early detection capability for stealthy multi-stage exfiltration attacks, and provide reproducible findings that support future research in behavioural intrusion detection.

*Keywords:* data exfiltration detection, hybrid deep learning, CNN, behavioural sequence modelling, LSTM, explainable artificial intelligence.

---

# Table of Contents

- i. Abstract
- ii. Table of Contents
- iii. List of Figures
- iv. List of Tables
- v. List of Abbreviations / Terminology
- 1. Introduction
- 2. Research Background
- 3. Problem Statement
- 4. Research Questions
- 5. Aim & Objectives
- 6. Scope
- 7. Significance of the Research
- 8. Research Methodology
- 9. Research Plan
- 10. Summary
- References

---

# List of Abbreviations / Terminology

| Abbreviation | Definition |
|:---|:---|
| AUC | Area Under the ROC Curve |
| CNN | Convolutional Neural Network |
| DL | Deep Learning |
| DNS | Domain Name System |
| DSR | Design Science Research |
| GCN | Graph Convolutional Network |
| HTTPS | Hypertext Transfer Protocol Secure |
| IDS | Intrusion Detection System |
| LIME | Local Interpretable Model-Agnostic Explanations |
| LSTM | Long Short-Term Memory |
| ML | Machine Learning |
| RNN | Recurrent Neural Network |
| ROC | Receiver Operating Characteristic |
| SHAP | SHapley Additive exPlanations |
| TLS | Transport Layer Security |
| XAI | Explainable Artificial Intelligence |
| XGBoost | Extreme Gradient Boosting |

---

# 1. Introduction

The fast growth of the digital infrastructure has significantly changed the way information is managed and shared by organizations. The large amounts of sensitive information are passed through cloud systems, enterprise networks and personal endpoints devices that have become the main medium of data exchange. Undoubtedly, these advancements are proven to have endless benefits; however, they have also introduced new complex security challenges that require more advanced detection technologies.

Today, one of the most serious threats to the existence of organizations is the concept of **data exfiltration** — the unauthorized transfer of sensitive information between internal systems and external, attacker-controlled destinations. In contrast to other cyberattacks, which are instantly detectable in most cases, data exfiltration is typically covert, persistent, and hardly noticeable at the initial stages (Hozouri et al., 2025). Hackers have created various ways of using valid credentials, encrypted communication systems, and protocols like DNS tunnelling to silently exfiltrate sensitive data from corporate systems over a long period of time (Kamal & Mashaly, 2025).

Traditional intrusion detection systems, which rely primarily on signature-based rules and predefined traffic patterns, have demonstrated significant limitations in identifying such sophisticated and adaptive threats. In response, recent research has increasingly explored machine learning (ML) and deep learning (DL) techniques as more adaptive alternatives capable of identifying anomalous patterns in network flows, system logs, and user behaviour (Chinnasamy et al., 2025). However, the majority of existing approaches analyze either network-level traffic or host-level behaviour in isolation, which constrains their ability to model the full behavioural sequence of multi-stage exfiltration attacks (Hozouri et al., 2025; Kamal & Mashaly, 2025).

This report presents a proposal of the research study aimed at addressing these limitations through the development of a **behaviour-driven hybrid machine learning framework** for data exfiltration detection. The proposed framework integrates host telemetry, network traffic analysis, and behavioural sequence modelling to provide a more comprehensive detection capability against sophisticated exfiltration attacks.

---

# 2. Research Background

Data exfiltration has become one of the most significant cybersecurity issues of the modern world due to the growing reliance on digital systems to store and process sensitive organizational data. Data exfiltration is defined as the illegal movement of sensitive data out of an internal system to an external place under attacker's control. It is often related to the concept of advanced persistent threats (APTs), in which attackers have a silent, persistent access to the hacked systems and steal valuable information systematically (Kamal & Mashaly, 2025). The multi-stage execution of these attacks, which involves reconnaissance, privilege escalation, data gathering, staging, and final exfiltration, complicates the early detection of such attacks especially by traditional security systems (Hakim et al., 2024).

Attackers use a variety of different methods to hide exfiltration activity in regular network traffic. Widely used techniques are DNS tunnelling, data leakage via HTTPS, abuse of cloud storage platforms, and use of command-and-control (C2) channels (Hozouri et al., 2025). The use of encrypted communication protocols (TLS, HTTPS, and DNS-over-HTTPS) further complicates detection, as majority of security systems are limited to analysis of traffic metadata (packets size, time, frequency of communication, etc.) rather than analysis of payload's content (Chen et al., 2024). Furthermore, another important exfiltration method is the insider threats, where organizational members with authorized access to the system are knowingly or unknowingly used for exposing sensitive organizational information (Ofori et al., 2025).

The signature-based and rule-based mechanisms have always been used in traditional intrusion detection systems to detect known attack patterns. Nevertheless, research comparing popular IDS solutions, such as Snort and Suricata, indicates that in their default settings, they do not identify sophisticated exfiltration techniques like ICMP tunnelling (Qutqut et al., 2026). Such results indicate that signature-based methods cannot be used solely to deal with evolving security threats.

To address these weaknesses, machine learning and deep learning methods have become major research directions in cybersecurity threat detection. Widely used classical algorithms — including Random Forest, Decision Trees, and Gradient Boosting — have shown strong results in structured feature classification. Tree-based ensemble techniques, in particular, have achieved over 99% accuracy in DNS-based data exfiltration detection (Açıkgözoğlu, 2024; Thomas et al., 2025). The use of deep learning approaches — namely CNNs, RNNs, and Transformers — has broadened detection capabilities through the extraction of complex temporal and spatial features from large-scale network traffic and behavioural log datasets (Kuppuraju et al., 2025).

In addition to network-level analysis, host-based behavioural detection has been gaining more and more research interest. Host-based models can provide a detailed view of user and system behaviour by examining system call traces, file access patterns, process execution logs, and user activity, which cannot be observed by network-only techniques. Recent research shows that by adding contextual and role-based behavioural features to detection models, it is possible to achieve high accuracy rates of 94–99%, while reducing the number of false positives (Balogun et al., 2025). Autoencoders, a type of deep learning models, have also demonstrated to be effective in identifying covert data exfiltration in containerised environments using syscall-based behavioural monitoring (Zuppelli et al., 2024).

Hybrid detection architectures have emerged as a promising direction that attempts to combine the complementary strengths of multiple analytical techniques and data sources. Frameworks that integrate classical machine learning with deep learning models — such as CNN-LSTM pipelines and ensemble tree models — have demonstrated improved detection accuracy and robustness compared to single-model approaches (Cai et al., 2025; Potluri, 2024). In more recent work, reinforcement learning-driven feature selection has been paired with XAI techniques to enhance detection capabilities and provide greater model interpretability in encrypted network traffic (Sammour et al., 2026; Hanintya et al., 2025).

Despite of this progress, there is still a major gap in the available literature. The majority of proposed detection systems continue to operate on a single data modality — either network traffic or host telemetry — and do not explicitly model the behavioural sequences that precede and constitute multi-stage data exfiltration attacks (Hozouri et al., 2025; Kamal & Mashaly, 2025). This gap motivates the development of an integrated, behaviour-driven detection framework, as examined in detail in the Problem Statement.

---

# 3. Problem Statement

Despite significant advancements in machine learning and deep learning-based intrusion detection, existing data exfiltration detection systems remain fundamentally limited by their inability to integrate multi-source behavioural telemetry and model the sequential stages of sophisticated exfiltration attacks.

**First**, many solutions rely on **single-modality telemetry**. Network-based detection systems analyze traffic flows, packets metadata, and characteristics of DNS queries to detect abnormal patterns of communication. Although these methods have shown strong statistical results — ensemble classifiers have had detection rates over 99% when tested under controlled conditions (Thomas et al., 2025; Açıkgözoğlu, 2024) — they do not provide insights into host-level activities and user behaviour.

**Second**, most detection systems do not adequately **model temporal behavior**. Host-based behavioural detection systems address some of these limitations by providing detailed visibility into user activities, system processes, and file access patterns. However, host-only detection systems cannot directly observe the network transmission stage of exfiltration, where sensitive data is transferred to external attacker-controlled destinations.

**Third**, hybrid detection architectures have attempted to bridge this gap by combining multiple machine learning techniques and data sources. Nevertheless, most current hybrid systems are practically single-modality, and do not explicitly model the sequences of behaviour that characterize the progressive stages of multi-stage exfiltration attacks.

**Fourth**, although explainable AI techniques like SHAP and LIME have been incorporated into detection systems to enhance model interpretability, existing systems mainly provide **post-hoc feature importance explanations** instead of attempting to recreate the behavioural sequence of an attack (Hanintya et al., 2025).

> Altogether, these constraints indicate a critical gap in detecting stealthy, multi-stage data exfiltration attacks that span across both host and network space. There is a clear need for an integrated detection framework that incorporates host telemetry, network traffic analysis, and behavioural sequence modelling in a hybrid machine learning architecture.

---

# 4. Research Questions

Building upon the limitations identified in the problem statement, this research addresses the following questions:

**RQ1. What are the key behavioural indicators and multi-source telemetry features that characterize the progressive stages of data exfiltration attacks across host and network environments?**

This question fills the gap in integrated analysis between host and network domains, by defining a complete set of features that characterize the lifecycle of data exfiltration attacks.

**RQ2. How can classical machine learning and deep learning techniques be effectively combined in a hybrid architecture to improve the detection accuracy and robustness?**

This question explores how hybrid approaches can leverage complementary strengths of different learning paradigms to enhance detection performance on multi-source data.

**RQ3. How can behavioural sequence modelling be incorporated into a hybrid detection framework to identify multi-stage data exfiltration attack patterns?**

This question focuses on addressing the limitation of event-level detection by incorporating temporal relationships between behaviours.

**RQ4. To what extent can explainable artificial intelligence techniques improve the interpretability of detection decisions and support incident investigation?**

This question examines how interpretability can enhance the practical usability of detection systems in real-world security operations.

---

# 5. Aim & Objectives

## 5.1 Aim

The main aim of this research is to design and evaluate a **behaviour-driven hybrid machine learning framework** that integrates host-level telemetry, network traffic analysis, and behavioural sequence modelling to improve the detection of sophisticated multi-stage data exfiltration attacks.

## 5.2 Objectives

1. To identify and analyze the key behavioural indicators and multi-source telemetry features that characterize the progressive stages of data exfiltration attacks across host and network environments, drawing on available datasets and literature-informed feature definitions.

2. To design and implement a hybrid machine learning and deep learning architecture that combines classical and deep learning techniques for multi-source behavioural data classification.

3. To develop and integrate a behavioural sequence modelling component into the hybrid framework to enable the detection of multi-stage data exfiltration attack patterns.

4. To integrate explainable artificial intelligence techniques into the proposed framework and evaluate their effectiveness in improving the interpretability of detection decisions.

---

# 6. Scope

This section defines the boundaries of the proposed research to clarify the extent to which the framework will be developed and evaluated. To ensure feasibility within the 12-week project timeline, the study will prioritise a combination of classical machine learning models (Random Forest and XGBoost) and deep learning models (CNN and LSTM). More complex extensions such as graph-based neural networks, reinforcement learning components, and large-scale multi-dataset fusion are excluded from the implementation and considered as directions for future work.

## 6.1 Focus of Detection

This research will focus specifically on the detection of data exfiltration attacks in enterprise network environments. The proposed framework will target multi-stage exfiltration scenarios, including those associated with advanced persistent threats (APTs), insider threats, and covert communication channel abuse such as DNS tunnelling and encrypted HTTPS-based exfiltration.

## 6.2 Data Sources

The proposed framework will integrate two primary categories of security telemetry — host-level behavioural data and network-level traffic data.

- **Host-level data:** system call logs, process execution records, file access events, and user activity logs.
- **Network-level data:** traffic flow features, packet metadata, DNS query characteristics, and NetFlow records.

Network-based datasets will serve as the primary source for model training, while host-level behavioural features will be incorporated either from compatible datasets or through feature-level simulation where paired datasets are unavailable.

## 6.3 Machine Learning Techniques

The research will explore the integration of classical machine learning algorithms — specifically ensemble methods such as Random Forest and XGBoost — with CNN and LSTM-based sequence modelling. Reinforcement learning techniques are considered out of scope for the current study.

## 6.4 Behavioural Sequence Modelling

The behavioural sequence modelling component will focus on modelling the temporal relationships between host and network behavioural events to identify progressive multi-stage exfiltration patterns. The scope is limited to supervised and semi-supervised approaches using available labelled datasets.

## 6.5 Explainability

The explainability component will focus on the integration of **SHAP-based feature attribution** techniques. The practical evaluation of explainability will be assessed in terms of feature attribution quality and its potential utility for supporting security analyst workflows.

## 6.6 Evaluation

The evaluation will be conducted using controlled experimental settings with publicly available benchmark datasets. Standard classification metrics such as **accuracy, precision, recall, F1-score, and AUC** will be used to assess the performance.

## 6.7 Geographical and Organizational Scope

This research is not restricted to any specific geographical region or industry sector. The proposed framework is designed as a general-purpose detection solution applicable to enterprise environments broadly.

---

# 7. Significance of the Research

## 7.1 Addressing a Critical Cybersecurity Challenge

Data exfiltration is one of the most financially and operationally damaging cyber-attacks. The impact of successful data exfiltration is not only immediate financial losses but also regulatory penalties, reputational damage, and long-term competitive harm. The persistent and covert nature of data exfiltration attacks imply that organizations are often unaware of current data breaches over a long period of time (Hozouri et al., 2025).

## 7.2 Advancing the State of the Art in Detection Frameworks

Academically, the proposed research directly contributes to the literature on machine learning-based intrusion detection by filling a well-defined and justified research gap. The proposed behaviour-driven hybrid framework extends existing hybrid detection approaches by combining host telemetry and network traffic analysis with behavioural sequence modelling into a single detection architecture — a practice that is underexplored in the literature.

## 7.3 Improving Early Detection of Multi-Stage Attacks

A particularly significant contribution is the emphasis on **early detection through behavioural sequence modelling**. The existing detection mechanisms are mostly reactive, detecting exfiltration activity when the transmission has already started (Hakim et al., 2024). The proposed framework seeks to facilitate earlier detection by modelling the sequential behavioural patterns leading up to the final exfiltration stage (e.g. reconnaissance, lateral movement and data staging).

## 7.4 Supporting the Cybersecurity Research Community

The proposed research will contribute to the cybersecurity research community by providing the systematic assessment of the proposed framework. The research gives reproducible results that other researchers can expand on by reporting detailed experimental results and comparing the performance with representative state-of-the-art baselines.

---

# 8. Research Methodology

## 8.1 Research Design and Approach

This research will adopt a quantitative, **design science research (DSR)** methodology. Design science research is particularly well-suited to computing and engineering research that aims to produce and evaluate a novel artefact — in this case, a behaviour-driven hybrid machine learning framework — as a solution to an identified practical problem (Hevner et al., 2004). The research will follow a structured five-phase methodology.

---

## 8.2 Phase 1: Feature Identification and Dataset Preparation

The first phase will address Objective 1 and focus on the systematic identification of behavioural indicators and multi-source telemetry features that characterize the progressive stages of data exfiltration attacks.

### 8.2.1 Dataset Selection

This research will utilize publicly available cybersecurity datasets that provide either host-level or network-level security telemetry. The study will focus on integrating features derived from different sources into a unified representation to simulate multi-source behavioural analysis.

### 8.2.2 Feature Engineering

Feature engineering will involve the extraction and construction of features from both host and network data sources:

- **Network-level features:** traffic flow statistics, packet size distributions, inter-arrival timing, DNS query entropy, and communication frequency metrics.
- **Host-level features:** system call frequency distributions, file access entropy, process execution patterns, and privilege usage indicators.

Additionally, MITRE ATT&CK tactic mappings will be used as an intermediate layer to align extracted features with known attack stage indicators, following the approach established by Hakim et al. (2024).

---

## 8.3 Phase 2: Hybrid Framework Design

The second phase will address Objective 2 and involve the design of the hybrid machine learning and deep learning architecture.

### 8.3.1 Framework Architecture

The proposed framework contains three principal components:

| Layer | Description |
|:---|:---|
| **Multi-source data integration layer** | Ingests, preprocesses, and normalizes host telemetry and network traffic data into a unified feature representation |
| **Hybrid ML/DL classification layer** | Applies ensemble methods (Random Forest and XGBoost) and deep learning (CNN) to classify events as benign or malicious |
| **Behavioural sequence modelling layer** | Models temporal relationships between sequential behavioural events using LSTM to identify multi-stage attack patterns |

The outputs of the classification and sequence modelling components will be combined using a **late fusion** approach, where prediction probabilities from both components are aggregated to produce the final classification decision.

---

## 8.4 Phase 3: Behavioural Sequence Modelling

The third phase will address Objective 3 and focus on the development of the behavioural sequence modelling component.

Behavioural sequence modelling will be implemented using **Long Short-Term Memory (LSTM)** networks. The sequence modelling component will receive ordered sequences of behavioural events derived from both host and network telemetry and will learn to identify patterns indicative of progressive multi-stage attack behaviour.

Event sequences will be constructed using sliding time windows:
- Each sequence will consist of a fixed number of events (e.g., **50–100 events per sequence**).
- Labels will be assigned based on the presence of exfiltration activity within the sequence window.
- The model will perform **binary classification** (benign vs exfiltration) at the sequence level.

---

## 8.5 Phase 4: Explainability Integration

The fourth phase addresses Objective 4 and involves the integration of explainable artificial intelligence techniques into the proposed framework.

The main explainability technique will be **SHAP (SHapley Additive exPlanations)**, consistent with the findings of Hanintya et al. (2025), whose work demonstrated that SHAP provides the most detailed both global and local explanations among all XAI methods, when applied to intrusion detection.

The effectiveness of explainability will be evaluated through both:

- **Qualitative assessment:** SHAP-based explanations will be analysed for a defined set of selected detection cases (true positives and false positives) to assess whether generated explanations provide meaningful insights aligned with MITRE ATT&CK indicators.
- **Quantitative assessment:** SHAP feature rank-order consistency will be measured across cross-validation folds to assess the stability and robustness of explanations across different data distributions.

---

## 8.6 Phase 5: Evaluation and Validation

The fifth phase will involve the systematic experimental evaluation of the proposed framework.

### 8.6.1 Evaluation Metrics

| Metric | Role |
|:---|:---|
| accuracy | Overall classification accuracy |
| precision | Attack class prediction precision |
| recall | Attack detection completeness |
| **F1-score** | Primary metric for class-imbalanced data |
| false positive rate | False positive control |
| **AUC** | Overall discriminative capability |

To evaluate the effectiveness of the proposed hybrid framework, two levels of comparison will be performed:

1. **Ablation study** — comparing the full hybrid framework against its individual components.
2. **State-of-the-art benchmark** — benchmarking against comparable approaches (e.g., Cai et al., 2025; Chen et al., 2024).

The evaluation will be conducted using **stratified k-fold cross-validation** to ensure robustness and generalisability.

### 8.6.2 Ethical Considerations

Since this study will be based solely on publicly accessible benchmark data, no personally identifiable information will be collected or processed. There will be no live network traffic capture, and no actual organizational systems will be accessed or monitored. The study thus poses a **low risk of ethical concerns** and does not need further ethical approval.

---

# 9. Research Plan

The research is planned over a period of **12 weeks** from May 2026 to August 2026, organized around five methodological phases.

## 9.2 Phase Descriptions and Key Milestones

**Table 1. Project Milestones**

| Phase | Milestone | Key Deliverable | Success Criterion | Target Date |
|:---|:---|:---|:---|:---:|
| **Phase 1** — Feature identification and dataset preparation | Datasets accessed and features extracted | Preprocessed feature dataset with MITRE ATT&CK mappings | All datasets loaded, cleaned, and feature-engineered with documented feature set | May 15 |
| **Phase 2** — Hybrid framework design | Functional classification pipeline implemented | Hybrid detection framework prototype | Framework achieves baseline classification performance on at least one dataset | June 12 |
| **Phase 3** — Behavioural sequence modelling | LSTM sequence model integrated into framework | Integrated LSTM sequence modelling component | Model captures temporal event sequences; integrated output feeds ensemble layer | July 3 |
| **Phase 4** — Explainability integration | SHAP module integrated and producing outputs | SHAP explanation module with sequence-aware attribution | SHAP values generated for individual detection decisions; validated against known attack sequences | July 24 |
| **Phase 5** — Evaluation and validation | All experiments completed and results documented | Experimental results report with comparative analysis | Framework outperforms at least one baseline on F1-score and AUC; ablation study complete | August 14 |
| **Report writing** | Final report submitted | Completed research report and slides | Report meets submission requirements; all sections finalized and proofread | August 28 |

---

### 9.2.1 Phase 1 — Feature Identification and Dataset Preparation

Involves systematic literature review to identify behavioural indicators, selection and access of benchmark datasets, feature engineering from host and network telemetry, and MITRE ATT&CK tactic mapping. Deliverable: a documented feature engineering report.

### 9.2.2 Phase 2 — Hybrid Framework Design and Implementation

Involves the design of the multi-source integration layer and hybrid ML/DL classification architecture, implementation of framework components, and development of baseline models for comparison.

### 9.2.3 Phase 3 — Behavioural Sequence Modelling

Involves the development of the LSTM-based sequence modelling component and integration of the sequence modelling layer into the broader hybrid framework.

### 9.2.4 Phase 4 — Explainability Integration

Involves the integration of SHAP-based explainability into the framework and the design of sequence-aware explanation outputs.

### 9.2.5 Phase 5 — Evaluation and Validation

Involves cross-validation experiments, ablation studies, external baseline comparisons against state-of-the-art approaches (e.g., Cai et al., 2025; Chen et al., 2024), and cross-dataset generalizability evaluation.

### 9.2.6 Report Writing and Defence Preparation (Ongoing)

Continuous chapter writing throughout the research process, final draft review and revisions, oral defence preparation, and final submission in August 2026.

---

## 9.3 Risk and Contingency Planning

**Table 2. Risk Assessment**

| Risk | Likelihood | Impact | Mitigation |
|:---|:---:|:---:|:---|
| Dataset incompatibility between host and network sources | Medium | High | Use feature-level integration and synthetic host behaviour simulation to align heterogeneous datasets |
| Computational resource constraints limiting deep learning training | Medium | Medium | Utilize cloud-based computing resources (e.g., Google Colab, Kaggle); optimize model complexity |
| Underperformance of sequence modelling component | Low | Medium | Fall back to simpler temporal aggregation features; adjust scope of Objective 3 |
| Timeline delays due to integration complexity | Medium | Medium | Maintain buffer weeks (Weeks 10–12) for revisions; prioritize core objectives O1–O3 |

---

# 10. Summary

This proposal has presented a research study addressing a clearly identified gap in the existing literature on data exfiltration detection. Current detection systems — whether network-based, host-based, predictive, or hybrid — remain fundamentally limited by their reliance on single-modality telemetry and their inability to model the sequential behavioural patterns that characterize multi-stage exfiltration attacks.

In response, this proposal will introduce a **behaviour-driven hybrid machine learning framework** that integrates three principal components:

| Component | Purpose |
|:---|:---|
| Multi-source data integration layer | Combines host and network telemetry |
| Hybrid ML/DL classification layer | Ensemble methods + deep learning architecture |
| Behavioural sequence modelling layer | LSTM-based temporal attack pattern detection |

SHAP-based explainability will be further incorporated to improve the interpretability of detection decisions.

The research is guided by **four research questions** addressing cross-domain feature identification, hybrid architecture design, behavioural sequence modelling, and explainability integration. These are mapped to four objectives, each representing a concrete and assessable unit of work. The use of publicly available benchmark datasets limits the scope and guarantees ethical compliance and reproducibility. The 12-week research plan is structured into five methodological phases with defined milestones and mitigation strategies against risks.

The significance of this research has both **academic and practical dimensions**:
- **Academically:** builds upon existing hybrid detection architectures by enhancing behavioural sequence modelling and multi-source feature integration.
- **Practically:** improves early detection of stealthy multi-stage attacks and enhances model interpretability for security operations teams.

> In conclusion, the proposed framework will represent a timely and well-motivated contribution to cybersecurity, directly addressing the limitations of existing approaches and responding to emerging research priorities in multi-source telemetry integration, behavioural modelling, and explainable intrusion detection.

---

# References

Açıkgözoğlu, E. (2024). Comparison Of Machine Learning Algorithms For Detection Of Data Exfiltration Over DNS. *Yalvaç Akademi Dergisi*, *9*(2), 61–70. https://doi.org/10.57120/yalvac.1507402

Almuhanna, R., & Dardouri, S. (2025). A deep learning/machine learning approach for anomaly based network intrusion detection. *Frontiers in Artificial Intelligence*, *8*, 1625891. https://doi.org/10.3389/frai.2025.1625891

Balogun, S. A., Ijiga, O. M., Okika, N., Enyejo, L. A., & Agbo, O. J. (2025). Machine Learning-Based Detection of SQL Injection and Data Exfiltration Through Behavioral Profiling of Relational Query Patterns. *International Journal of Innovative Science and Research Technology*, 49–63. https://doi.org/10.38124/ijisrt/25aug324

Cai, X., Zhang, H., Ahmed, C. M., & Koide, H. (2025). Detecting advanced persistent threat exfiltration with ensemble deep learning tree models and novel detection metrics. *IEEE Access*, *13*, 81803–81822. https://doi.org/10.1109/access.2025.3567772

Chen, Z., Simsek, M., Kantarci, B., Bagheri, M., & Djukic, P. (2024). Machine learning-enabled hybrid intrusion detection system with host data transformation and an advanced two-stage classifier. *Computer Networks*, *250*, 110576. https://doi.org/10.1016/j.comnet.2024.110576

Chinnasamy, R., Subramanian, M., Easwaramoorthy, S. V., & Cho, J. (2025). Deep learning-driven methods for network-based intrusion detection systems: A systematic review. *ICT Express*, *11*(1), 181–215. https://doi.org/10.1016/j.icte.2025.01.005

Hakim, A. R., Ramli, K., Salman, M., Pranggono, B., & Agustina, E. R. (2024). ARKAIV: Predicting data exfiltration using supervised machine learning based on tactics mapping from threat reports and event logs. *IEEE Access*, *13*, 28381–28397. https://doi.org/10.1109/access.2024.3524502

Hanintya, D. L., Sukarno, P., & Wardana, A. A. (2025). Comparing Explainable AI Framework: Study case on detection of DNS exfiltration attach using neural network. *Procedia Computer Science*, *269*, 1022–1032. https://doi.org/10.1016/j.procs.2025.09.044

Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems research. *MIS Quarterly, 28*(1), 75–105. https://doi.org/10.2307/25148625

Hozouri, A., Mirzaei, A., & Effatparvar, M. (2025). A comprehensive survey on intrusion detection systems with advances in machine learning, deep learning and emerging cybersecurity challenges. *Discover Artificial Intelligence*, *5*(1). https://doi.org/10.1007/s44163-025-00578-1

Kamal, H., & Mashaly, M. (2025). Robust intrusion detection system using an improved hybrid deep learning model for binary and Multi-Class classification in IoT networks. *Technologies*, *13*(3), 102. https://doi.org/10.3390/technologies13030102

Kuppuraju, S. Y., Ojha, S. S., & Kumar, M. (2025). Real-Time detection of data exfiltration using deep learning in edge computing systems. *International Journal of Innovative Research in Computer Science & Technology*, *13*(2), 6–13. https://doi.org/10.55524/ijircst.2025.13.2.2

Ofori, H. K., Bell-Dzide, K., Brown-Acquaye, W. L., Lempogo, F., Frimpong, S. O., Agbehadji, I. E., & Millham, R. C. (2025). Application of machine learning and deep learning techniques for enhanced insider threat detection in cybersecurity: Bibliometric review. *Symmetry*, *17*(10), 1704. https://doi.org/10.3390/sym17101704

Potluri, S. (2024). A Deep Learning-Driven framework for detecting anomalous data breaches in distributed cloud storage infrastructures. *International Journal of Artificial Intelligence Data Science and Machine Learning*, *5*(3). https://doi.org/10.63282/3050-9262.ijaidsml-v5i3p109

Qutqut, M. H., Ahmed, A., Taqi, M. K., Abimanyu, J., Ajes, E. T., & Alhaj, F. (2026). A comparative evaluation of SnORt and Suricata for detecting data exfiltration tunnels in cloud environments. *Journal of Cybersecurity and Privacy*, *6*(1), 17. https://doi.org/10.3390/jcp6010017

Sammour, M., Othman, M. F. I., Hassan, A., Bhais, O., & Talib, M. S. (2026). Advanced DNS tunneling detection: a hybrid reinforcement learning and metaheuristic approach. *Frontiers in Computer Science*, *7*. https://doi.org/10.3389/fcomp.2025.1728980

Singh, P. R. N., & Siddalingaiah, N. (2025). Permission-level risk profiling and anomaly detection in IoT using machine learning. *International Journal of Information Technology*. https://doi.org/10.1007/s41870-025-02977-0

Thomas, R., Yerima, S. Y., Alkharoossi, S. K., Alkhoori, M. M., & Ahmed, A. (2025). DNS Exfiltration Attack and Dataset Generation for Machine Learning-Based Detection. *3rd International Conference on Cyber Resilience ICCR2025*, 1–6. https://doi.org/10.1109/iccr67387.2025.11292120

Yumlembam, R., Issac, B., Jacob, S. M., Yang, L., & Krishnan, D. (2025). Insider Threat Detection Using GCN and Bi-LSTM with Explicit and Implicit Graph Representations. *arXiv (Cornell University)*. https://doi.org/10.48550/arxiv.2512.18483

Zuppelli, M., Guarascio, M., Caviglione, L., & Liguori, A. (2024). No Country for Leaking Containers: Detecting Exfiltration of Secrets Through AI and Syscalls. *ARES '24: Proceedings of the 19th International Conference on Availability, Reliability and Security (July 2024)*, 1–8. https://doi.org/10.1145/3664476.3670884
