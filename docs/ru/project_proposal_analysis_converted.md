# Анализ документа

## Краткое резюме

Документ представляет собой проектное предложение по теме **“Behaviour-driven hybrid learning for data exfiltration detection”**. Основная идея исследования — разработать гибридный ML/DL-фреймворк для обнаружения утечки данных, объединяющий сетевые признаки, host-level telemetry, поведенческое моделирование последовательностей и SHAP-объяснимость.

## Сильные стороны

- **Тема актуальна и прикладная:** data exfiltration, APT, insider threats, DNS tunnelling и encrypted traffic относятся к существенным проблемам кибербезопасности.
- **Хорошо сформулирован исследовательский разрыв:** документ последовательно показывает ограниченность single-modality подходов и недостаток sequence modelling.
- **Логичная структура:** Abstract → Background → Problem Statement → Research Questions → Aim/Objectives → Scope → Methodology → Plan.
- **Методология соответствует задаче:** Design Science Research подходит для разработки и оценки исследовательского артефакта — detection framework.
- **Есть реалистичные ограничения:** автор явно ограничивает scope по времени, данным и вычислительным ресурсам.
- **Оценка продумана:** указаны accuracy, precision, recall, F1-score, FPR, AUC, ablation study и cross-validation.

## Потенциальные слабые места

- **Риск недостаточной связности host и network datasets.** В тексте признаётся, что paired datasets могут отсутствовать, поэтому feature-level integration и simulation должны быть описаны максимально строго.
- **Требуется усилить воспроизводимость.** Желательно явно указать конкретные datasets, preprocessing steps, train/test split strategy и baseline models.
- **SHAP для LSTM/sequence component требует осторожности.** Нужно уточнить, будет ли использоваться KernelSHAP, DeepSHAP или объяснение агрегированных признаков.
- **Некоторые утверждения зависят от актуальности источников.** Библиографические ссылки не были отдельно проверены на существование и корректность DOI при конвертации.
- **Грамматика и академический стиль местами требуют редактуры.** Есть фразы, которые лучше переформулировать для более формального академического тона.

## Рекомендации по доработке

1. Добавить отдельную таблицу с выбранными datasets: название, тип телеметрии, классы, размер, источник, ограничения.
2. Чётко описать механизм объединения host и network признаков, особенно если данные не являются парными.
3. Уточнить архитектуру late fusion: формула/правило агрегации вероятностей, веса компонентов, критерий выбора threshold.
4. Добавить baseline comparison: Random Forest only, XGBoost only, CNN only, LSTM only, hybrid without SHAP, full hybrid.
5. Уточнить, как будет оцениваться explainability: rank stability, case studies, alignment with MITRE ATT&CK tactics.
6. Проверить все ссылки DOI и библиографические данные перед финальной сдачей.

## Итоговая оценка

Проектное предложение выглядит содержательно сильным и методологически последовательным. Главный риск — практическая реализация multi-source integration при отсутствии совместимых host/network датасетов. Если этот риск будет закрыт через чёткую схему feature-level integration, прозрачные baseline experiments и воспроизводимый evaluation pipeline, работа будет выглядеть убедительно как академически, так и практически.

---

**INDIVIDUAL ASSIGNMENT 2**

**PROJECT PROPOSAL**

<table>
<colgroup>
<col style="width: 27%" />
<col style="width: 4%" />
<col style="width: 68%" />
</colgroup>
<thead>
<tr class="header">
<th><strong>Name / TP Number</strong></th>
<th><strong>:</strong></th>
<th>Djumakhodjaeva Malika / TP099270</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><strong>Intake Code</strong></td>
<td><strong>:</strong></td>
<td>APUMF2508CYS(PR)</td>
</tr>
<tr class="even">
<td><strong>Module Code</strong></td>
<td><strong>:</strong></td>
<td>CT095-6-M-RMCE</td>
</tr>
<tr class="odd">
<td><strong>Module Title</strong></td>
<td><strong>:</strong></td>
<td>Research Methodology in Computing and Engineering</td>
</tr>
<tr class="even">
<td><strong>Module Lecturer</strong></td>
<td><strong>:</strong></td>
<td>Dr. Murugananthan Velayutham</td>
</tr>
<tr class="odd">
<td><strong>Nominated Supervisor</strong></td>
<td><strong>:</strong></td>
<td>Dr. Jalil Md Desa</td>
</tr>
<tr class="even">
<td><strong>Project Title</strong></td>
<td><strong>:</strong></td>
<td><p>Behaviour-driven hybrid learning</p>
<p>for data exfiltration detection</p></td>
</tr>
<tr class="odd">
<td><strong>Date Assigned</strong></td>
<td><strong>:</strong></td>
<td>February 6, 2026</td>
</tr>
<tr class="even">
<td><strong>Date Completed</strong></td>
<td><strong>:</strong></td>
<td>April 24, 2026</td>
</tr>
</tbody>
</table>

# Abstract

Data exfiltration is among the most severe and complex cybersecurity
threats faced by modern organizations as it is covert, persistent, and
multi-stage in nature. Traditional intrusion detection systems have
proven to be significantly limited in detection of sophisticated
exfiltration techniques, especially those that utilize encrypted
communication channels, insider threats, and advanced persistent
threats. Although recent studies have explored machine learning and deep
learning approaches to enhance the detection capabilities, the majority
of existing systems use a single data modality - either network traffic
or host-level telemetry - and do not model the sequential behavioural
patterns that characterize the progressive stages of data exfiltration
attacks. This proposal presents a behaviour-driven hybrid machine
learning framework designed to address these limitations by integrating
host telemetry, network traffic analysis, and behavioural sequence
modelling within a unified detection architecture. The proposed
framework will integrate classical ensemble methods like Random Forest
and XGBoost, and components of CNN deep learning with LSTM-based
behavioural sequence modelling to capture both structured feature
patterns and complex temporal relationships in multi-source security
data. The framework will be further integrated with explainable
artificial intelligence technique, namely SHAP-based feature
attribution, to enhance the interpretability of the detection decisions
and facilitate the workflows of security analysts. The framework will be
evaluated using publicly available cybersecurity benchmark datasets with
performance assessed using standard classification metrics. The research
is expected to contribute an enhanced hybrid detection framework that
will extend existing approaches, advance early detection capability for
stealthy multi-stage exfiltration attacks, and provide reproducible
findings that support future research in behavioural intrusion
detection.

*Keywords:* data exfiltration detection, hybrid deep learning, CNN,
behavioural sequence modelling, LSTM, explainable artificial
intelligence

# Table of Contents

# 

[i. Abstract [2](#abstract)](#abstract)

[ii. Table of Contents [3](#table-of-contents)](#table-of-contents)

[iii. List of Figures [5](#list-of-figures)](#list-of-figures)

[iv. List of Tables [5](#list-of-tables)](#list-of-tables)

[v. List of Abbreviations / Terminology
[5](#list-of-abbreviations-terminology)](#list-of-abbreviations-terminology)

[1. Introduction [6](#introduction)](#introduction)

[2. Research Background [7](#research-background)](#research-background)

[3. Problem Statement [9](#problem-statement)](#problem-statement)

[4. Research Questions [11](#research-questions)](#research-questions)

[5. Aim & Objectives [12](#aim-objectives)](#aim-objectives)

[5.1 Aim [12](#aim)](#aim)

[5.2 Objectives [12](#objectives)](#objectives)

[6. Scope [13](#scope)](#scope)

[6.1 Focus of Detection [13](#focus-of-detection)](#focus-of-detection)

[6.2 Data Sources [13](#data-sources)](#data-sources)

[6.3 Machine Learning Techniques
[13](#machine-learning-techniques)](#machine-learning-techniques)

[6.4 Behavioural Sequence Modelling
[14](#behavioural-sequence-modelling)](#behavioural-sequence-modelling)

[6.5 Explainability [14](#explainability)](#explainability)

[6.6 Evaluation [14](#evaluation)](#evaluation)

[6.7 Geographical and Organizational Scope
[14](#geographical-and-organizational-scope)](#geographical-and-organizational-scope)

[7. Significance of the Research
[15](#significance-of-the-research)](#significance-of-the-research)

[7.1 Addressing a Critical Cybersecurity Challenge
[15](#addressing-a-critical-cybersecurity-challenge)](#addressing-a-critical-cybersecurity-challenge)

[7.2 Advancing the State of the Art in Detection Frameworks
[15](#advancing-the-state-of-the-art-in-detection-frameworks)](#advancing-the-state-of-the-art-in-detection-frameworks)

[7.3 Improving Early Detection of Multi-Stage Attacks
[15](#improving-early-detection-of-multi-stage-attacks)](#improving-early-detection-of-multi-stage-attacks)

[7.4 Supporting the Cybersecurity Research Community
[16](#supporting-the-cybersecurity-research-community)](#supporting-the-cybersecurity-research-community)

[8. Research Methodology
[17](#research-methodology)](#research-methodology)

[8.1 Research Design and Approach
[17](#research-design-and-approach)](#research-design-and-approach)

[8.2 Phase 1: Feature Identification and Dataset Preparation
[18](#phase-1-feature-identification-and-dataset-preparation)](#phase-1-feature-identification-and-dataset-preparation)

[8.2.1 Dataset Selection [18](#dataset-selection)](#dataset-selection)

[8.2.2 Feature Engineering
[18](#feature-engineering)](#feature-engineering)

[8.3 Phase 2: Hybrid Framework Design
[18](#phase-2-hybrid-framework-design)](#phase-2-hybrid-framework-design)

[8.3.1 Framework Architecture
[18](#framework-architecture)](#framework-architecture)

[8.4 Phase 3: Behavioural Sequence Modelling
[19](#phase-3-behavioural-sequence-modelling)](#phase-3-behavioural-sequence-modelling)

[8.5 Phase 4: Explainability Integration
[19](#phase-4-explainability-integration)](#phase-4-explainability-integration)

[8.6 Phase 5: Evaluation and Validation
[20](#phase-5-evaluation-and-validation)](#phase-5-evaluation-and-validation)

[8.6.1 Evaluation Metrics
[20](#evaluation-metrics)](#evaluation-metrics)

[8.6.2 Ethical Considerations
[21](#ethical-considerations)](#ethical-considerations)

[9. Research Plan [22](#research-plan)](#research-plan)

[9.1 Research Timeline Overview
[22](#research-timeline-overview)](#research-timeline-overview)

[9.2 Phase Descriptions and Key Milestones
[22](#phase-descriptions-and-key-milestones)](#phase-descriptions-and-key-milestones)

[9.2.1 Phase 1 – Feature Identification and Dataset Preparation
[23](#phase-1-feature-identification-and-dataset-preparation-1)](#phase-1-feature-identification-and-dataset-preparation-1)

[9.2.2 Phase 2 – Hybrid Framework Design and Implementation
[23](#phase-2-hybrid-framework-design-and-implementation)](#phase-2-hybrid-framework-design-and-implementation)

[9.2.3 Phase 3 – Behavioural Sequence Modelling
[24](#phase-3-behavioural-sequence-modelling-1)](#phase-3-behavioural-sequence-modelling-1)

[9.2.4 Phase 4 – Explainability Integration
[24](#phase-4-explainability-integration-1)](#phase-4-explainability-integration-1)

[9.2.5 Phase 5 – Evaluation and Validation
[24](#phase-5-evaluation-and-validation-1)](#phase-5-evaluation-and-validation-1)

[9.2.6 Report Writing and Defence Preparation (Ongoing)
[24](#report-writing-and-defence-preparation-ongoing)](#report-writing-and-defence-preparation-ongoing)

[9.3 Risk and Contingency Planning
[24](#risk-and-contingency-planning)](#risk-and-contingency-planning)

[10. Summary [26](#summary)](#summary)

[References [27](#references)](#references)

#  List of Figures

[**Figure 1.** DSR Methodology [18](#_Toc226997163)](#_Toc226997163)

[**Figure 2.** Gantt Chart [23](#_Toc226997164)](#_Toc226997164)

#  List of Tables

[**Table 1.** Project Milestones [23](#_Toc226997228)](#_Toc226997228)

[**Table 2**. Risk Assessment [25](#_Toc226997229)](#_Toc226997229)

# List of Abbreviations / Terminology

| AUC     | Area Under the ROC Curve                        |
|---------|-------------------------------------------------|
| CNN     | Convolutional Neural Network                    |
| DL      | Deep Learning                                   |
| DNS     | Domain Name System                              |
| DSR     | Design Science Research                         |
| GCN     | Graph Convolutional Network                     |
| HTTPS   | Hypertext Transfer Protocol Secure              |
| IDS     | Intrusion Detection System                      |
| LIME    | Local Interpretable Model-Agnostic Explanations |
| LSTM    | Long Short-Term Memory                          |
| ML      | Machine Learning                                |
| RNN     | Recurrent Neural Network                        |
| ROC     | Receiver Operating Characteristic               |
| SHAP    | SHapley Additive exPlanations                   |
| TLS     | Transport Layer Security                        |
| XAI     | Explainable Artificial Intelligence             |
| XGBoost | Extreme Gradient Boosting                       |

# 1. Introduction

The fast growth of the digital infrastructure has significantly changed
the way information is managed and shared by organizations. The large
amounts of sensitive information are passed through cloud systems,
enterprise networks and personal endpoints devices that have become the
main medium of data exchange. Undoubtedly, these advancements are proven
to have endless benefits; however, they have also introduced new complex
security challenges that require more advanced detection technologies.

Today, one of the most serious threats to the existence of organizations
is the concept of data exfiltration - the unauthorized transfer of
sensitive information between internal systems and external,
attacker-controlled destinations. In contrast to other cyberattacks,
which are instantly detectable in most cases, data exfiltration is
typically covert, persistent, and hardly noticeable at the initial
stages (Hozouri et al., 2025). Hackers have created various ways of
using valid credentials, encrypted communication systems, and protocols
like DNS tunnelling to silently exfiltrate sensitive data from corporate
systems over a long period of time (Kamal & Mashaly, 2025).

Traditional intrusion detection systems, which rely primarily on
signature-based rules and predefined traffic patterns, have demonstrated
significant limitations in identifying such sophisticated and adaptive
threats. In response, recent research has increasingly explored machine
learning (ML) and deep learning (DL) techniques as more adaptive
alternatives capable of identifying anomalous patterns in network flows,
system logs, and user behaviour (Chinnasamy et al., 2025). However, the
majority of existing approaches analyze either network-level traffic or
host-level behaviour in isolation, which constrains their ability to
model the full behavioural sequence of multi-stage exfiltration attacks
(Hozouri et al., 2025; Kamal & Mashaly, 2025).

This report presents a proposal of the research study aimed at
addressing these limitations through the development of a
behaviour-driven hybrid machine learning framework for data exfiltration
detection. The proposed framework integrates host telemetry, network
traffic analysis, and behavioural sequence modelling to provide a more
comprehensive detection capability against sophisticated exfiltration
attacks.

# 2. Research Background

Data exfiltration has become one of the most significant cybersecurity
issues of the modern world due to the growing reliance on digital
systems to store and process sensitive organizational data. Data
exfiltration is defined as the illegal movement of sensitive data out of
an internal system to an external place under attacker’s control. It is
often related to the concept of advanced persistent threats (APTs), in
which attackers have a silent, persistent access to the hacked systems
and steal valuable information systematically (Kamal & Mashaly, 2025).
The multi-stage execution of these attacks, which involves
reconnaissance, privilege escalation, data gathering, staging, and final
exfiltration, complicates the early detection of such attacks especially
by traditional security systems (Hakim et al., 2024).

Attackers use a variety of different methods to hide exfiltration
activity in regular network traffic. Widely used techniques are DNS
tunnelling, data leakage via HTTPS, abuse of cloud storage platforms,
and use of command-and-control (C2) channels (Hozouri et al., 2025). The
use of encrypted communication protocols (TLS, HTTPS, and
DNS-over-HTTPS) further complicates detection, as majority of security
systems are limited to analysis of traffic metadata (packets size, time,
frequency of communication, etc.) rather than analysis of payload’s
content (Chen et al., 2024). Furthermore, another important exfiltration
method is the insider threats, where organizational members with
authorized access to the system are knowingly or unknowingly used for
exposing sensitive organizational information (Ofori et al., 2025).

The signature-based and rule-based mechanisms have always been used in
traditional intrusion detection systems to detect known attack patterns.
Nevertheless, research comparing popular IDS solutions, such as Snort
and Suricata, indicates that in their default settings, they do not
identify sophisticated exfiltration techniques like ICMP tunnelling
(Qutqut et al., 2026). Such results indicate that signature-based
methods cannot be used solely to deal with evolving security threats.

To address these weaknesses, machine learning and deep learning methods
have become major research directions in cybersecurity threat detection.
Widely used classical algorithms - including Random Forest, Decision
Trees, and Gradient Boosting - have shown strong results in structured
feature classification. Tree-based ensemble techniques, in particular,
have achieved over 99% accuracy in DNS-based data exfiltration detection
(Açıkgözoğlu, 2024; Thomas et al., 2025). The use of deep learning
approaches - namely CNNs, RNNs, and Transformers - has broadened
detection capabilities through the extraction of complex temporal and
spatial features from large-scale network traffic and behavioural log
datasets (Kuppuraju et al., 2025).

In addition to network-level analysis, host-based behavioural detection
has been gaining more and more research interest. Host-based models can
provide a detailed view of user and system behaviour by examining system
call traces, file access patterns, process execution logs, and user
activity, which cannot be observed by network-only techniques. Recent
research shows that by adding contextual and role-based behavioural
features to detection models, it is possible to achieve high accuracy
rates of 94-99%, while reducing the number of false positives (Balogun
et al., 2025). Autoencoders, a type of deep learning models, have also
demonstrated to be effective in identifying covert data exfiltration in
containerised environments using syscall-based behavioural monitoring
(Zuppelli et al., 2024).

Hybrid detection architectures have emerged as a promising direction
that attempts to combine the complementary strengths of multiple
analytical techniques and data sources. Frameworks that integrate
classical machine learning with deep learning models - such as CNN-LSTM
pipelines and ensemble tree models - have demonstrated improved
detection accuracy and robustness compared to single-model approaches
(Cai et al., 2025; Potluri, 2024). In more recent work, reinforcement
learning-driven feature selection has been paired with XAI techniques to
enhance detection capabilities and provide greater model
interpretability in encrypted network traffic (Sammour et al., 2026;
Hanintya et al., 2025).

Despite of this progress, there is still a major gap in the available
literature. The majority of proposed detection systems continue to
operate on a single data modality - either network traffic or host
telemetry - and do not explicitly model the behavioural sequences that
precede and constitute multi-stage data exfiltration attacks (Hozouri et
al., 2025; Kamal & Mashaly, 2025). This gap motivates the development of
an integrated, behaviour-driven detection framework, as examined in
detail in the Problem Statement.

# 3. Problem Statement

Despite significant advancements in machine learning and deep
learning-based intrusion detection, existing data exfiltration detection
systems remain fundamentally limited by their inability to integrate
multi-source behavioural telemetry and model the sequential stages of
sophisticated exfiltration attacks.

The existing detection approaches can be broadly divided into
network-based and host-based systems, both of which offer a partial
perspective on the exfiltration attack lifecycle. The network-based
detection systems analyze traffic flows, packets metadata, and
characteristics of DNS queries to detect abnormal patterns of
communication. Although these methods have shown strong statistical
results - ensemble classifiers have had detection rates over 99% when
tested under controlled conditions (Thomas et al., 2025; Açıkgözoğlu,
2024) - they do not provide insights into host-level activities and user
behaviour. Consequently, the suspicious network activity cannot be
attributed to user actions or application processes, thus, making it
difficult to recreate the chain of events that culminates into data
exfiltration. In addition, the widespread adoption of protocols like
HTTPS, TLS, and DNS-over-HTTPS (DoH) restricts the utility of
payload-based features. This forces network-based systems to use
metadata observations, which may not effectively separate normal and
malicious encrypted traffic (Chen et al., 2024; Sammour et al., 2026).

Host-based behavioural detection systems address some of these
limitations by providing detailed visibility into user activities,
system processes, and file access patterns. These approaches have
demonstrated effectiveness for insider threat detection and behavioural
anomaly identification, particularly when contextual and role-based
features are incorporated into detection models (Balogun et al., 2025;
Singh & Siddalingaiah, 2025). However, host-only detection systems
cannot directly observe the network transmission stage of exfiltration,
where sensitive data is transferred to external attacker-controlled
destinations. Without integration with network telemetry, host-based
models can identify suspicious behaviour but cannot confirm whether
actual data exfiltration has occurred (Zuppelli et al., 2024).

Hybrid detection architectures have attempted to bridge this gap by
combining multiple machine learning techniques and data sources.
Nevertheless, most current hybrid systems are practically
single-modality, with some either using network traffic or host
telemetry instead of actually combining both (Cai et al., 2025; Potluri,
2024). Most importantly, the majority of hybrid solutions are based on
the classification of anomalies at the log level and do not explicitly
model the sequences of behaviour that characterize the progressive
stages of multi-stage exfiltration attacks. The ARKAIV framework
suggested by Hakim et al. (2024) is one of the few research attempts to
predict exfiltration behaviour by mapping system logs to MITRE ATT&CK
tactics, yet it is based on a single source of data and supervised
learning using labelled datasets. Thus, its applicability is limited to
real-world environments where labelled breach data is rare.

Also, although explainable AI techniques like SHAP and LIME have been
incorporated into detection systems to enhance model interpretability,
existing systems mainly provide post-hoc feature importance explanations
instead of attempting to recreate the behavioural sequence of an attack
(Hanintya et al., 2025). This constrains their practical use in the
investigation of incidents and proactive threat response.

Altogether, these constraints indicate that the current detection models
are largely reactive and narrowly scoped, and there is a critical gap in
detecting stealthy, multi-stage data exfiltration attacks that span
across both host and network space. It is thus evident that there is a
need of an integrated detection framework that incorporates host
telemetry, network traffic analysis, and behavioural sequence modelling
in a hybrid machine learning architecture to allow more accurate,
timely, and comprehensive detection of advanced data exfiltration
attacks.

# 4. Research Questions 

Building upon the limitations identified in the problem statement, this
research addresses the following questions:

1.  **What are the key behavioural indicators and multi-source telemetry
    features that characterize the progressive stages of data
    exfiltration attacks across host and network environments?**

This question fills the gap in integrated analysis between host and
network domains, by defining a complete set of features that
characterize the lifecycle of data exfiltration attacks.

2.  **How can classical machine learning and deep learning techniques be
    effectively combined in a hybrid architecture to improve the
    detection accuracy and robustness?**

This question explores how hybrid approaches can leverage complementary
strengths of different learning paradigms to enhance detection
performance on multi-source data.

3.  **How can behavioural sequence modelling be incorporated into a
    hybrid detection framework to identify multi-stage data exfiltration
    attack patterns?**

This question focuses on addressing the limitation of event-level
detection by incorporating temporal relationships between behaviours.

4.  **To what extent can explainable artificial intelligence techniques
    improve the interpretability of detection decisions and support
    incident investigation?**

This question examines how interpretability can enhance the practical
usability of detection systems in real-world security operations.

# 5. Aim & Objectives

## 5.1 Aim

The main aim of this research is to design and evaluate a
behaviour-driven hybrid machine learning framework that integrates
host-level telemetry, network traffic analysis, and behavioural sequence
modelling to improve the detection of sophisticated multi-stage data
exfiltration attacks.

## 5.2 Objectives

- To identify and analyze the key behavioural indicators and
  multi-source telemetry features that characterize the progressive
  stages of data exfiltration attacks across host and network
  environments, drawing on available datasets and literature-informed
  feature definitions.

- To design and implement a hybrid machine learning and deep learning
  architecture that combines classical and deep learning techniques for
  multi-source behavioural data classification.

- To develop and integrate a behavioural sequence modelling component
  into the hybrid framework to enable the detection of multi-stage data
  exfiltration attack patterns.

- To integrate explainable artificial intelligence techniques into the
  proposed framework and evaluate their effectiveness in improving the
  interpretability of detection decisions.

# 6. Scope

This section defines the boundaries of the proposed research to clarify
the extent to which the framework will be developed and evaluated. To
ensure feasibility within the 12-week project timeline, the study will
prioritise a combination of classical machine learning models (Random
Forest and XGBoost) and deep learning models (CNN and LSTM). More
complex extensions such as graph-based neural networks, reinforcement
learning components, and large-scale multi-dataset fusion are excluded
from the implementation and considered as directions for future work.

## 6.1 Focus of Detection

This research will focus specifically on the detection of data
exfiltration attacks in enterprise network environments. The proposed
framework will target multi-stage exfiltration scenarios, including
those associated with advanced persistent threats (APTs), insider
threats, and covert communication channel abuse such as DNS tunnelling
and encrypted HTTPS-based exfiltration.

## 6.2 Data Sources

The proposed framework will integrate two primary categories of security
telemetry - host-level behavioural data and network-level traffic data.
Host-level data includes system call logs, process execution records,
file access events, and user activity logs. Network-level data includes
traffic flow features, packet metadata, DNS query characteristics, and
NetFlow records. Network-based datasets will serve as the primary source
for model training, while host-level behavioural features will be
incorporated either from compatible datasets or through feature-level
simulation where paired datasets are unavailable. The integration will
therefore occur at the feature representation level rather than through
direct raw data fusion. This approach is a deliberate scope constraint,
consistent with the 12-week timeline, and does not diminish the validity
of the multi-source integration architecture.

## 6.3 Machine Learning Techniques

The research will explore the integration of classical machine learning
algorithms - specifically ensemble methods such as Random Forest and
XGBoost - with CNN and LSTM-based sequence modelling. The scope of deep
learning exploration is bounded by computational resource availability
and the time constraints of the research. Reinforcement learning
techniques are considered out of scope for the current study, although
their potential integration is acknowledged as a direction for future
research.

## 6.4 Behavioural Sequence Modelling

The behavioural sequence modelling component of the framework will focus
on modelling the temporal relationships between host and network
behavioural events to identify progressive multi-stage exfiltration
patterns. The scope of sequence modelling is limited to supervised and
semi-supervised approaches using available labelled datasets. Fully
unsupervised sequence modelling, while acknowledged as a valuable future
direction, is considered beyond the scope of this study given the
constraints of available labelled data and evaluation benchmarks.

## 6.5 Explainability

The explainability component of the framework will focus on the
integration of SHAP-based feature attribution techniques to provide
interpretable explanations of detection decisions. The scope of
explainability is limited to post-detection explanation generation. The
practical evaluation of explainability will be assessed in terms of
feature attribution quality and its potential utility for supporting
security analyst workflows.

## 6.6 Evaluation

The evaluation of the proposed framework will be conducted using
controlled experimental settings with publicly available benchmark
datasets. Standard classification metrics such as accuracy, precision,
recall, F1-score, and area under the ROC curve (AUC) will be used to
assess the performance of proposed framework.

## 6.7 Geographical and Organizational Scope

This research is not restricted to any specific geographical region or
industry sector. The proposed framework is designed as a general-purpose
detection solution applicable to enterprise environments broadly.

# 7. Significance of the Research

This section justifies why the proposed research is significant and what
contributions it is likely to have to the areas of cybersecurity and
machine learning.

## 7.1 Addressing a Critical Cybersecurity Challenge

Data exfiltration is one of the most financially and operationally
damaging cyber-attacks. The impact of successful data exfiltration is
not only immediate financial losses but also regulatory penalties,
reputational damage, and long-term competitive harm. The persistent and
covert nature of data exfiltration attacks imply that organizations are
often unaware of current data breaches over a long period of time
(Hozouri et al., 2025). This makes the development of stronger and more
comprehensive detection approach practically significant for
organizations that use digital infrastructure for their operations.

## 7.2 Advancing the State of the Art in Detection Frameworks

Academically, the proposed research directly contributes to the
literature on machine learning-based intrusion detection by filling a
well-defined and justified research gap. As defined in the literature
review and problem statement, most of the current detection systems are
single-data modality systems that do not model the behavioural sequences
of multi-stage exfiltration attacks (Kamal & Mashaly, 2025; Hozouri et
al., 2025). The proposed behaviour-driven hybrid framework extends
existing hybrid detection approaches by combining host telemetry and
network traffic analysis with behavioural sequence modelling into a
single detection architecture - a practice that is underexplored in the
literature.

## 7.3 Improving Early Detection of Multi-Stage Attacks

A particularly significant contribution of the proposed research is its
emphasis on early detection through behavioural sequence modelling. The
existing detection mechanisms are mostly reactive, detecting
exfiltration activity when the transmission has already started (Hakim
et al., 2024). The proposed framework seeks to facilitate earlier
detection of exfiltration activity by modelling the sequential
behavioural patterns leading up to the final exfiltration stage (e.g.
reconnaissance, lateral movement and data staging), thereby reducing the
attacker dwell time and minimising the amount of data that can be
exfiltrated before it is detected. This ability has direct operational
significance to the security operations teams responsible for detection
and incident response

## 7.4 Supporting the Cybersecurity Research Community

The proposed research will contribute to the cybersecurity research
community by providing the systematic assessment of the proposed
framework. The research gives reproducible results that other
researchers can expand on by reporting detailed experimental results and
comparing the performance with representative state-of-the-art
baselines. Moreover, the identification and analysis of cross-domain
behavioural features defining multi-stage exfiltration attacks could
become a useful source of data in future studies on behavioural threat
detection, dataset development, and threat intelligence framework
design.

# 8. Research Methodology

This section describes the research methodology that will be employed to
achieve the aim and objectives of this research.

## 8.1 Research Design and Approach

This research will adopt a quantitative, design science research (DSR)
methodology. Design science research is particularly well-suited to
computing and engineering research that aims to produce and evaluate a
novel artefact - in this case, a behaviour-driven hybrid machine
learning framework - as a solution to an identified practical problem
(Hevner et al., 2004). The DSR methodology involves iterative cycles of
design, implementation, and evaluation, which aligns with the objective
of developing and refining a detection framework through systematic
experimentation. The research will follow a structured five-phase
methodology as illustrated in Figure 1.

<span id="_Toc226997163" class="anchor"></span>**Figure 1.** DSR
Methodology

## 8.2 Phase 1: Feature Identification and Dataset Preparation

The first phase will address Objective 1 and focus on the systematic
identification of behavioural indicators and multi-source telemetry
features that characterize the progressive stages of data exfiltration
attacks.

### 8.2.1 Dataset Selection

This research will utilize publicly available cybersecurity datasets
that provide either host-level or network-level security telemetry. It
is acknowledged that most publicly available datasets provide either
network-level or host-level telemetry independently. Therefore, this
study will focus on integrating features derived from different sources
into a unified representation to simulate multi-source behavioural
analysis.

### 8.2.2 Feature Engineering

Feature engineering will involve the extraction and construction of
features from both host and network data sources. Network-level features
will include traffic flow statistics, packet size distributions,
inter-arrival timing, DNS query entropy, and communication frequency
metrics. Host-level features will include system call frequency
distributions, file access entropy, process execution patterns, and
privilege usage indicators. Additionally, MITRE ATT&CK tactic mappings
will be used as an intermediate layer to align extracted features with
known attack stage indicators, following the approach established by
Hakim et al. (2024). Feature importance analysis will be conducted using
SHAP values to identify the most influential behavioural indicators
contributing to detection performance. This will support the validation
of selected features and their relevance to different stages of data
exfiltration attacks.

## 8.3 Phase 2: Hybrid Framework Design 

The second phase will address Objective 2 and involve the design of the
hybrid machine learning and deep learning architecture.

### 8.3.1 Framework Architecture

In the proposed framework, there will be three principal components that
operate in an integrated pipeline:

- **Multi-source data integration layer** – will ingest, preprocess, and
  normalize host telemetry and network traffic data from multiple
  sources into a unified feature representation suitable for downstream
  modelling components

- **Hybrid ML/DL classification layer** – will apply ensemble methods
  (Random Forest and XGBoost) and deep learning (CNN) to classify
  individual events and traffic samples as benign or malicious based on
  structured feature representations.

- **Behavioural sequence modelling layer** – will be responsible for
  modelling temporal relationships between sequential behavioural events
  to identify multi-stage attack patterns; will be implemented using
  deep learning LSTM approach.

The outputs of the classification and sequence modelling components will
be combined using a late fusion approach, where prediction probabilities
from both components are aggregated to produce the final classification
decision. This proposed design follows the established principle which
demonstrates that hybrid architectures with combined classical and deep
learning techniques can improve both accuracy and generalization
capability in comparison with single-model approaches (Almuhanna &
Dardouri, 2025).

## 8.4 Phase 3: Behavioural Sequence Modelling 

The third phase will address Objective 3 and focus on the development of
the behavioural sequence modelling component of the framework.

Behavioural sequence modelling will be implemented using Long Short-Term
Memory (LSTM) networks, which are well-suited to learning temporal
dependencies in sequential event data (Yumlembam et al., 2025). The
sequence modelling component will receive as input ordered sequences of
behavioural events - derived from both host and network telemetry - and
will learn to identify patterns that are indicative of progressive
multi-stage attack behaviour. Event sequences will be constructed by
aggregating temporally ordered feature vectors within sliding time
windows, allowing the model to capture both short-term and medium-term
behavioural patterns.

Sequences will be constructed using sliding time windows over ordered
event streams. Each sequence will consist of a fixed number of events
(e.g., 50–100 events per sequence), with labels assigned based on the
presence of exfiltration activity within the sequence window. The model
will perform binary classification (benign vs exfiltration) at the
sequence level.

## 8.5 Phase 4: Explainability Integration 

The fourth phase addresses Objective 4 and involve the integration of
explainable artificial intelligence techniques into the proposed
framework.

The main explainability technique that will be used is SHAP (SHapley
Additive exPlanations), consistent with the findings of Hanintya et al.
(2025), whose work demonstrated that SHAP provides the most detailed
both global and local explanations among all XAI methods, when applied
to intrusion detection. The effectiveness of explainability will be
evaluated through both qualitative and quantitative assessment.
Qualitatively, SHAP-based explanations will be analysed for a defined
set of selected detection cases - specifically, a representative sample
of true positives and false positives drawn from each cross-validation
fold - to assess whether generated explanations provide meaningful
insights into the behavioural patterns leading to classification
decisions and whether they align with known attack-stage indicators
documented in the MITRE ATT&CK framework. Quantitatively, SHAP feature
rank-order consistency will be measured across cross-validation folds to
assess the stability and robustness of explanations across different
data distributions. High consistency indicates that explanations reflect
genuine learned patterns rather than artefacts of specific data splits.

## 8.6 Phase 5: Evaluation and Validation

The fifth phase will involve the systematic experimental evaluation of
the proposed framework.

### 8.6.1 Evaluation Metrics

The standard classification measures will be used to determine the
framework performance: accuracy, precision, recall, F1-score, false
positive rate (FPR), and area under the ROC curve (AUC). Since the class
imbalance is often a part of cybersecurity data, i.e. the number of
benign traffic greatly exceeds that of malicious samples, precision,
recall, and F1-score will be considered as the main performance metrics,
with AUC to determine the overall discriminative capability.

To evaluate the effectiveness of the proposed hybrid framework, two
levels of comparison will be performed. First, an ablation study will
compare the full hybrid framework against its individual components to
assess the contribution of each architectural layer to overall detection
performance. Second, where datasets overlap with prior published work,
performance will be benchmarked against comparable state-of-the-art
approaches (e.g., Cai et al., 2025; Chen et al., 2024) to contextualise
the results within existing literature. This dual comparison approach
ensures that both the internal design decisions and the external
research contribution of the framework can be assessed rigorously.

The evaluation will be conducted using stratified k-fold
cross-validation to ensure robustness and generalisability of the
results across different data distributions.

### 8.6.2 Ethical Considerations

Since this study will be based solely on publicly accessible benchmark
data, no personally identifiable information will be collected or
processed. The datasets employed in this study have been availed by
their respective authors to academic research. There will be no live
network traffic capture, and no actual organizational systems will be
accessed or monitored. The study thus poses a low risk of ethical
concerns and does not need a further ethical approval.

# 9. Research Plan

This section presents the timeline and schedule for the proposed
research.

## 9.1 Research Timeline Overview

The research is planned over a period of 12 weeks from May 2026 to
August 2026. The timeline is organized around the five methodological
phases defined in Section 8. Figure 2 presents the detailed research
schedule in the form of a Gantt chart. Tasks are organized by phase and
mapped across the project timeline on a weekly basis.



<span id="_Toc226997164" class="anchor"></span>**Figure 2.** Gantt Chart

## 9.2 Phase Descriptions and Key Milestones

The research is organized into five methodological phases, each with
defined deliverables and milestones. Table 1 summarizes the key
milestones, deliverables, and success criteria for each phase of the
research.

<span id="_Toc226997228" class="anchor"></span>**Table 1.** Project
Milestones

| **Phase**                                                    | **Milestone**                                    | **Key Deliverable**                                     | **Success Criterion**                                                                                                  | **Target Date** |
|--------------------------------------------------------------|--------------------------------------------------|---------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|-----------------|
| **Phase 1** — Feature identification and dataset preparation | Datasets accessed and features extracted         | Preprocessed feature dataset with MITRE ATT&CK mappings | All datasets loaded, cleaned, and feature-engineered with documented feature set                                       | May 15          |
| **Phase 2** — Hybrid framework design                        | Functional classification pipeline implemented   | Hybrid detection framework prototype                    | Framework achieves baseline classification performance on at least one dataset;                                        | June 12         |
| **Phase 3** — Behavioural sequence modelling                 | LSTM sequence model integrated into framework    | Integrated LSTM sequence modelling component            | Model captures temporal event sequences across host and network telemetry; integrated output feeds ensemble layer      | July 3          |
| **Phase 4** — Explainability integration                     | SHAP module integrated and producing outputs     | SHAP explanation module with sequence-aware attribution | SHAP values generated for individual detection decisions; explanations validated against known attack sequences        | July 24         |
| **Phase 5** — Evaluation and validation                      | All experiments completed and results documented | Experimental results report with comparative analysis   | Framework outperforms at least one baseline on F1-score and AUC across cross-validation folds; ablation study complete | August 14       |
| Report writing                                               | Final report submitted                           | Completed research report and slides                    | Report meets submission requirements; all sections finalized and proofread                                             | August 28       |

### 9.2.1 Phase 1 – Feature Identification and Dataset Preparation

This phase involves systematic literature review to identify behavioural
indicators, selection and access of benchmark datasets, feature
engineering from host and network telemetry, and MITRE ATT&CK tactic
mapping. The key milestone of this phase is a finalized feature set and
preprocessed dataset ready for modelling. The deliverable is a
documented feature engineering report.

### 9.2.2 Phase 2 – Hybrid Framework Design and Implementation

This phase involves the design of the multi-source integration layer and
hybrid ML/DL classification architecture, implementation of framework
components, and development of baseline models for comparison. The key
milestone is a functional prototype of the hybrid classification
framework. The deliverable is an implemented and tested classification
pipeline.

### 9.2.3 Phase 3 – Behavioural Sequence Modelling

This phase involves the development of the LSTM-based sequence modelling
component and integration of the sequence modelling layer into the
broader hybrid framework. The key milestone is a fully integrated
framework with behavioural sequence modelling capability.

### 9.2.4 Phase 4 – Explainability Integration

This phase involves the integration of SHAP-based explainability into
the framework and the design of sequence-aware explanation outputs. The
key milestone is a functional explainability module producing
interpretable detection outputs.

### 9.2.5 Phase 5 – Evaluation and Validation

This phase involves cross-validation experiments, ablation studies
assessing the contribution of individual framework components, external
baseline comparisons against state-of-the-art approaches (e.g., Cai et
al., 2025; Chen et al., 2024), and cross-dataset generalizability
evaluation. The key milestone is a complete set of experimental results
with comparative analysis.

### 9.2.6 Report Writing and Defence Preparation (Ongoing)

Involves continuous chapter writing throughout the research process,
final draft review and revisions, oral defence preparation, and final
submission in August 2026.

## 9.3 Risk and Contingency Planning

Table 2 summarizes the key risks identified for this research and the
corresponding contingency measures.

<span id="_Toc226997229" class="anchor"></span>**Table 2**. Risk
Assessment

| **Risk**                                                           | **Likelihood** | **Impact** | **Mitigation**                                                                                        |
|--------------------------------------------------------------------|----------------|------------|-------------------------------------------------------------------------------------------------------|
| Dataset incompatibility between host and network sources           | Medium         | High       | Use feature-level integration and synthetic host behaviour simulation to align heterogeneous datasets |
| Computational resource constraints limiting deep learning training | Medium         | Medium     | Utilize cloud-based computing resources (e.g., Google Colab, Kaggle); optimize model complexity       |
| Underperformance of sequence modelling component                   | Low            | Medium     | Fall back to simpler temporal aggregation features; adjust scope of O3                                |
| Timeline delays due to integration complexity                      | Medium         | Medium     | Maintain buffer weeks (Weeks 10-12) for revisions; prioritize core objectives O1–O3                   |

# 10. Summary

This proposal has presented a research study addressing a clearly
identified gap in the existing literature on data exfiltration
detection. Current detection systems - whether network-based,
host-based, predictive, or hybrid - remain fundamentally limited by
their reliance on single-modality telemetry and their inability to model
the sequential behavioural patterns that characterize multi-stage
exfiltration attacks.

In response, this proposal will introduce a behaviour-driven hybrid
machine learning framework that integrates three principal components: a
multi-source data integration layer combining host and network
telemetry, a hybrid ML/DL classification layer leveraging ensemble
methods, deep learning architecture, and a behavioural sequence
modelling layer based on LSTM network. SHAP-based explainability will be
further incorporated to improve the interpretability of detection
decisions.

The research is guided by four research questions addressing
cross-domain feature identification, hybrid architecture design,
behavioural sequence modelling, and explainability integration. These
are mapped to four objectives, each representing a concrete and
assessable unit of work. The use of publicly available benchmark
datasets limits the scope and guarantees ethical compliance and
reproducibility. The 12-week research plan is structured into five
methodological phases that have defined milestones and mitigation
strategies against risks.

The significance of this research is both academic and practical
dimensions. It will build upon existing hybrid detection architectures
by enhancing behavioural sequence modelling and multi-source feature
integration, and provide reproducible results to the research community.
Practically, it will improve early detection of stealthy multi-stage
attacks and enhances model interpretability for security operations
teams.

In conclusion, the proposed framework will represent a timely and
well-motivated contribution to cybersecurity, directly addressing the
limitations of existing approaches and responding to emerging research
priorities in multi-source telemetry integration, behavioural modelling,
and explainable intrusion detection.

# References

Açıkgözoğlu, E. (2024). Comparison Of Machine Learning Algorithms For
Detection Of Data Exfiltration Over DNS. *Yalvaç Akademi Dergisi*,
*9*(2), 61–70. https://doi.org/10.57120/yalvac.1507402

Almuhanna, R., & Dardouri, S. (2025). A deep learning/machine learning
approach for anomaly based network intrusion detection. *Frontiers in
Artificial Intelligence*, *8*, 1625891.
https://doi.org/10.3389/frai.2025.1625891

Balogun, S. A., Ijiga, O. M., Okika, N., Enyejo, L. A., & Agbo, O. J.
(2025). Machine Learning-Based Detection of SQL Injection and Data
Exfiltration Through Behavioral Profiling of Relational Query Patterns.
*International Journal of Innovative Science and Research Technology*,
49–63. https://doi.org/10.38124/ijisrt/25aug324

Cai, X., Zhang, H., Ahmed, C. M., & Koide, H. (2025). Detecting advanced
persistent threat exfiltration with ensemble deep learning tree models
and novel detection metrics. *IEEE Access*, *13*, 81803–81822.
https://doi.org/10.1109/access.2025.3567772

Chen, Z., Simsek, M., Kantarci, B., Bagheri, M., & Djukic, P. (2024).
Machine learning-enabled hybrid intrusion detection system with host
data transformation and an advanced two-stage classifier. *Computer
Networks*, *250*, 110576. https://doi.org/10.1016/j.comnet.2024.110576

Chinnasamy, R., Subramanian, M., Easwaramoorthy, S. V., & Cho, J.
(2025). Deep learning-driven methods for network-based intrusion
detection systems: A systematic review. *ICT Express*, *11*(1), 181–215.
https://doi.org/10.1016/j.icte.2025.01.005

Hakim, A. R., Ramli, K., Salman, M., Pranggono, B., & Agustina, E. R.
(2024). ARKAIV: Predicting data exfiltration using supervised machine
learning based on tactics mapping from threat reports and event logs.
*IEEE Access*, *13*, 28381–28397.
https://doi.org/10.1109/access.2024.3524502

Hanintya, D. L., Sukarno, P., & Wardana, A. A. (2025). Comparing
Explainable AI Framework: Study case on detection of DNS exfiltration
attach using neural network. *Procedia Computer Science*, *269*,
1022–1032. https://doi.org/10.1016/j.procs.2025.09.044

Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science
in information systems research. *MIS Quarterly, 28*(1), 75–105.
https://doi.org/10.2307/25148625

Hozouri, A., Mirzaei, A., & Effatparvar, M. (2025). A comprehensive
survey on intrusion detection systems with advances in machine learning,
deep learning and emerging cybersecurity challenges. *Discover
Artificial Intelligence*, *5*(1).
https://doi.org/10.1007/s44163-025-00578-1

Kamal, H., & Mashaly, M. (2025). Robust intrusion detection system using
an improved hybrid deep learning model for binary and Multi-Class
classification in IoT networks. *Technologies*, *13*(3), 102.
https://doi.org/10.3390/technologies13030102

Kuppuraju, S. Y., Ojha, S. S., & Kumar, M. (2025). Real-Time detection
of data exfiltration using deep learning in edge computing systems.
*International Journal of Innovative Research in Computer Science &
Technology*, *13*(2), 6–13. https://doi.org/10.55524/ijircst.2025.13.2.2

Ofori, H. K., Bell-Dzide, K., Brown-Acquaye, W. L., Lempogo, F.,
Frimpong, S. O., Agbehadji, I. E., & Millham, R. C. (2025). Application
of machine learning and deep learning techniques for enhanced insider
threat detection in cybersecurity: Bibliometric review. *Symmetry*,
*17*(10), 1704. https://doi.org/10.3390/sym17101704

Potluri, S. (2024). A Deep Learning-Driven framework for detecting
anomalous data breaches in distributed cloud storage infrastructures.
*International Journal of Artificial Intelligence Data Science and
Machine Learning*, *5*(3).
https://doi.org/10.63282/3050-9262.ijaidsml-v5i3p109

Qutqut, M. H., Ahmed, A., Taqi, M. K., Abimanyu, J., Ajes, E. T., &
Alhaj, F. (2026). A comparative evaluation of SnORt and Suricata for
detecting data exfiltration tunnels in cloud environments. *Journal of
Cybersecurity and Privacy*, *6*(1), 17.
https://doi.org/10.3390/jcp6010017

Sammour, M., Othman, M. F. I., Hassan, A., Bhais, O., & Talib, M. S.
(2026). Advanced DNS tunneling detection: a hybrid reinforcement
learning and metaheuristic approach. *Frontiers in Computer Science*,
*7*. https://doi.org/10.3389/fcomp.2025.1728980

Singh, P. R. N., & Siddalingaiah, N. (2025). Permission-level risk
profiling and anomaly detection in IoT using machine learning.
*International Journal of Information Technology*.
https://doi.org/10.1007/s41870-025-02977-0

Thomas, R., Yerima, S. Y., Alkharoossi, S. K., Alkhoori, M. M., & Ahmed,
A. (2025). DNS Exfiltration Attack and Dataset Generation for Machine
Learning-Based Detection. *3rd International Conference on Cyber
Resilience ICCR2025*, 1–6.
https://doi.org/10.1109/iccr67387.2025.11292120

Yumlembam, R., Issac, B., Jacob, S. M., Yang, L., & Krishnan, D. (2025).
Insider Threat Detection Using GCN and Bi-LSTM with Explicit and
Implicit Graph Representations. *arXiv (Cornell University)*.
https://doi.org/10.48550/arxiv.2512.18483

Zuppelli, M., Guarascio, M., Caviglione, L., & Liguori, A. (2024). No
Country for Leaking Containers: Detecting Exfiltration of Secrets
Through AI and Syscalls. *ARES ’24: Proceedings of the 19th
International Conference on Availability, Reliability and Security (July
2024)*, 1–8. https://doi.org/10.1145/3664476.3670884
