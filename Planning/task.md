# Task for Codex — Hybrid ML/DL Training Framework

> **Reference architecture:** `docs/ru/architecture.md`  
> **Project language:** Python 3.11+  
> **Platform:** Windows 11 / Linux compatible  
> **Status:** Database infrastructure ready. `normalization/` and `train/` need to be implemented.

---

## Context: What already exists

Study these files **before writing any code**:

| File / Folder | What it does |
|:---|:---|
| `manage.py` | CLI entry point — `argparse` with `module service action` pattern. **Extend this file**, do not replace it. |
| `scripts/database/duckdb_service.py` | DuckDB Docker helpers (`DuckDBDockerConfig`, `build_duckdb_config`). Reuse for config resolution. |
| `scripts/workdatasets/read_format.py` | `FileFormatReader` — reads JSON/CSV/PCAP/binary files from `datasets-new/`. Use this to read raw data. |
| `scripts/json_data.py` | `JsonData` — simple JSON read/write helper. |
| `scripts/convertion/dns_convertion.py` | DNS file conversion pattern. |
| `scripts/convertion/host_convertion.py` | Host file conversion with `HostConversionConfig` dataclass. Follow same OOP style. |
| `datasets-new/dns/` | Converted DNS datasets (JSON wrappers). TRAIN/TEST/VALIDATION splits. |
| `datasets-new/host/` | Converted Host datasets (JSON wrappers). TRAIN/TEST/VALIDATION splits. |
| `.env` | All paths and config. Load via `python-dotenv`. |
| `databases/duckdb/docker-compose.yml` | DuckDB runs in Docker, mounts `DUCKDB_DATA_PATH` volume. Python connects directly to `{DUCKDB_DATA_PATH}/{DUCKDB_DATABASE}` via the `duckdb` Python package. |

---

## DNS Dataset Structure (from `datasets-new/dns/TRAIN/`)

Each JSON file has this wrapper format:
```json
{
  "data": {
    "type": "csv",
    "metadata": {
      "path": "...",
      "rows": 22768,
      "columns": ["rr", "A_frequency", "entropy", ...]
    },
    "content": [
      {"rr": "0.0", "A_frequency": "0", ...}
    ]
  }
}
```

**Stateful feature files** (27 columns each): `stateful_features-light_{benign,audio,compressed,exe,image,text,video}.json`  
**Stateless feature files** (15 columns each): `stateless_features-light_{benign,audio,compressed,exe,image,text,video}.json`  
**Domain list files**: `benign.json`, `malware.json`, `phishing.json`, `spam.json`  
**CSV domain files**: `CSV_benign.json`, `CSV_malware.json`, `CSV_phishing.json`, `CSV_spam.json`

**Label mapping:**
```python
DNS_LABELS = {
    "benign": 0,
    "malware": 1,
    "phishing": 2,
    "spam": 3,
    "exfiltration": 4,  # audio, compressed, exe, image, text, video
}
```

**Stateful columns:**
`rr, A_frequency, NS_frequency, CNAME_frequency, SOA_frequency, NULL_frequency, PTR_frequency, HINFO_frequency, MX_frequency, TXT_frequency, AAAA_frequency, SRV_frequency, OPT_frequency, rr_type, rr_count, rr_name_entropy, rr_name_length, distinct_ns, distinct_ip, unique_country, unique_asn, distinct_domains, reverse_dns, a_records, unique_ttl, ttl_mean, ttl_variance`

**Stateless columns:**
`timestamp, FQDN_count, subdomain_length, upper, lower, numeric, entropy, special, labels, labels_max, labels_average, longest_word, sld, len, subdomain`

---

## Host Dataset Structure (from `datasets-new/host/`)

Files named: `{adjective}_{name}_{number}__{hash}.json`  
Three source datasets: **ADFA IDS**, **LID-DS 2021**, **Maintainable Log Dataset**

Each JSON file is a wrapper similar to DNS. Content varies: text (syscall sequences), CSV, JSONL, binary.

**Label mapping:**
```python
HOST_LABELS = {"benign": 0, "attack": 1}
```

---

## What needs to be implemented

### 1. `normalization/` — Dataset normalization

Create this folder with the following files:

```
normalization/
├── __init__.py
├── base.py
├── dns_normalizer.py
├── host_normalizer.py
├── feature_engineer.py
├── sequence_builder.py
├── data_validator.py
└── db_writer.py
```

---

#### `normalization/base.py`

```python
from abc import ABC, abstractmethod
import pandas as pd
from dataclasses import dataclass

@dataclass
class NormalizationResult:
    """Result of a normalization run."""
    source: str
    split: str
    rows_loaded: int
    rows_normalized: int
    rows_written: int
    errors: list[str]

class BaseNormalizer(ABC):
    """
    Abstract base class for dataset normalizers.
    Each subclass handles one data source (DNS or Host).
    """

    def __init__(self, split: str, workers: int = 4):
        """
        Args:
            split: Dataset split — TRAIN, TEST, or VALIDATION
            workers: Number of parallel workers for file reading
        """
        ...

    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Load raw data from datasets-new/ into a DataFrame."""
        ...

    @abstractmethod
    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize features: scale numerics, encode categoricals."""
        ...

    @abstractmethod
    def encode_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add integer label_id column based on string label column."""
        ...

    def validate(self, df: pd.DataFrame) -> list[str]:
        """Check for nulls, unexpected values, column mismatch. Returns error list."""
        ...

    def run(self) -> NormalizationResult:
        """Execute full normalization pipeline: load → validate → normalize → encode."""
        ...
```

---

#### `normalization/dns_normalizer.py`

Implement `DNSStatefulNormalizer(BaseNormalizer)` and `DNSStatelessNormalizer(BaseNormalizer)`.

**Requirements:**
- Use `concurrent.futures.ThreadPoolExecutor` to read multiple JSON files in parallel (I/O-bound).
- Read files from `datasets-new/dns/{split}/` — only `stateful_features-light_*.json` or `stateless_features-light_*.json` accordingly.
- Extract `data.content` list from each JSON file and convert to DataFrame.
- Add `label` column: extract from filename (e.g. `stateful_features-light_audio.json` → `exfiltration`, `stateful_features-light_benign.json` → `benign`).
- Label logic: `benign` → `benign`; `malware/phishing/spam` → use their name; `audio/compressed/exe/image/text/video` → `exfiltration`.
- Normalize all numeric columns to `float32` using `sklearn.preprocessing.StandardScaler`.
- Fill NaN with column median.
- Do NOT modify `datasets-new/` files. Read only.

**Class signatures:**
```python
class DNSStatefulNormalizer(BaseNormalizer):
    def __init__(self, datasets_new_dns_path: str, split: str, workers: int = 4): ...

class DNSStatelessNormalizer(BaseNormalizer):
    def __init__(self, datasets_new_dns_path: str, split: str, workers: int = 4): ...
```

---

#### `normalization/host_normalizer.py`

Implement `HostNormalizer(BaseNormalizer)`.

**Requirements:**
- Read files from `datasets-new/host/{split}/`. Use `ThreadPoolExecutor` for parallel reading.
- Each file's `data.type` can be: `text`, `csv`, `jsonl`, `binary`. Handle each gracefully.
- For `text` type: content is a list of syscall strings or log lines. Aggregate into statistical features per file:
  - `event_count` — total events in file
  - `unique_events` — number of unique event types
  - `event_entropy` — Shannon entropy of event type distribution
  - `mean_inter_event_gap` — if timestamps present, mean gap between events
- For `csv` type: use columns as features directly.
- Add `label` column: determine from filename prefix or parent folder name. If indeterminate, default to `unknown` (exclude from training).
- Use `ProcessPoolExecutor` for CPU-intensive aggregation of large text files.
- Normalize with `StandardScaler`.

**Class signature:**
```python
class HostNormalizer(BaseNormalizer):
    def __init__(self, datasets_new_host_path: str, split: str, workers: int = 4): ...
```

---

#### `normalization/sequence_builder.py`

Build temporal event sequences for LSTM training.

**Requirements:**
- Input: stateless DNS DataFrame (with `timestamp` column) or host text-content DataFrame (ordered events).
- Sort by `timestamp` per source file group.
- Apply sliding window: `window_size=64`, `stride=16`.
- Each window → one sequence of shape `(window_size, n_features)`.
- Label per window: majority label within window.
- Output: save sequences to HDF5 file at `sequences/{split}_dns.h5` and `sequences/{split}_host.h5`.
- HDF5 structure:
  ```
  /X  — shape (N, window_size, n_features), dtype float32
  /y  — shape (N,), dtype int32
  ```

**Class signature:**
```python
class SequenceBuilder:
    def __init__(self, window_size: int = 64, stride: int = 16, output_dir: str = "sequences"): ...

    def build_from_dataframe(self, df: pd.DataFrame, feature_cols: list[str],
                              label_col: str, output_name: str) -> str:
        """Build sequences and save to HDF5. Returns path to saved file."""
        ...
```

---

#### `normalization/db_writer.py`

Write normalized DataFrames to DuckDB.

**Requirements:**
- Connect to DuckDB at `{DUCKDB_DATA_PATH}/{DUCKDB_DATABASE}` using the `duckdb` Python package.
- Create tables if they don't exist. Use `CREATE TABLE IF NOT EXISTS`.
- Write in chunks of `chunk_size=10_000` rows to avoid memory spikes.
- Use `INSERT INTO ... SELECT * FROM df` via `duckdb.execute()`.
- Schema:

```sql
-- DNS stateful
CREATE TABLE IF NOT EXISTS dns_stateful_features (
    id            BIGINT,
    source_file   VARCHAR,
    split         VARCHAR,
    label         VARCHAR,
    label_id      INTEGER,
    rr            FLOAT,
    A_frequency   FLOAT,
    NS_frequency  FLOAT,
    CNAME_frequency FLOAT,
    SOA_frequency FLOAT,
    NULL_frequency FLOAT,
    PTR_frequency FLOAT,
    HINFO_frequency FLOAT,
    MX_frequency  FLOAT,
    TXT_frequency FLOAT,
    AAAA_frequency FLOAT,
    SRV_frequency FLOAT,
    OPT_frequency FLOAT,
    rr_type       FLOAT,
    rr_count      FLOAT,
    rr_name_entropy FLOAT,
    rr_name_length FLOAT,
    distinct_ns   FLOAT,
    distinct_ip   FLOAT,
    unique_country FLOAT,
    unique_asn    FLOAT,
    distinct_domains FLOAT,
    reverse_dns   FLOAT,
    a_records     FLOAT,
    unique_ttl    FLOAT,
    ttl_mean      FLOAT,
    ttl_variance  FLOAT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DNS stateless
CREATE TABLE IF NOT EXISTS dns_stateless_features (
    id               BIGINT,
    source_file      VARCHAR,
    split            VARCHAR,
    label            VARCHAR,
    label_id         INTEGER,
    ts               TIMESTAMP,
    FQDN_count       FLOAT,
    subdomain_length FLOAT,
    upper            FLOAT,
    lower            FLOAT,
    numeric          FLOAT,
    entropy          FLOAT,
    special          FLOAT,
    labels           FLOAT,
    labels_max       FLOAT,
    labels_average   FLOAT,
    longest_word     FLOAT,
    sld              FLOAT,
    len              FLOAT,
    subdomain        FLOAT,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Host features
CREATE TABLE IF NOT EXISTS host_features (
    id              BIGINT,
    source_file     VARCHAR,
    dataset         VARCHAR,
    split           VARCHAR,
    label           VARCHAR,
    label_id        INTEGER,
    event_count     FLOAT,
    unique_events   FLOAT,
    event_entropy   FLOAT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Experiments log
CREATE TABLE IF NOT EXISTS experiments (
    id          BIGINT,
    version     VARCHAR,
    started_at  TIMESTAMP,
    finished_at TIMESTAMP,
    status      VARCHAR,
    config      JSON,
    metrics     JSON
);
```

**Class signature:**
```python
class DuckDBWriter:
    def __init__(self, db_path: str, chunk_size: int = 10_000): ...

    def ensure_schema(self) -> None:
        """Create all tables if they don't exist."""
        ...

    def write_dataframe(self, df: pd.DataFrame, table: str) -> int:
        """Write DataFrame in chunks. Returns total rows written."""
        ...

    def log_experiment(self, version: str, config: dict, metrics: dict, status: str) -> None:
        """Insert a row into experiments table."""
        ...
```

---

### 2. `train/` — Model training pipeline

Create this folder:

```
train/
├── __init__.py
├── pipeline.py
├── trainers/
│   ├── __init__.py
│   ├── base_trainer.py
│   ├── ensemble_trainer.py
│   ├── cnn_trainer.py
│   └── lstm_trainer.py
├── fusion/
│   ├── __init__.py
│   └── late_fusion.py
├── explainability/
│   ├── __init__.py
│   └── shap_explainer.py
├── evaluation/
│   ├── __init__.py
│   └── metrics.py
└── utils/
    ├── __init__.py
    ├── progress.py
    ├── data_loader.py
    └── checkpoint.py
```

---

#### `train/trainers/base_trainer.py`

```python
from abc import ABC, abstractmethod
import numpy as np
from dataclasses import dataclass

@dataclass
class TrainResult:
    """Training outcome for a single model."""
    model_name: str
    version: str
    train_loss: float | None
    val_loss: float | None
    val_f1: float
    val_auc: float
    duration_seconds: float
    artifact_paths: dict[str, str]  # {"model": "models/v1/rf.joblib", ...}

class BaseTrainer(ABC):
    """
    Abstract base class for all model trainers.
    Subclasses implement fit() and predict_proba().
    """

    def __init__(self, version: str, device: str = "cpu"):
        """
        Args:
            version: Model version string, e.g. 'v1'
            device: 'cpu', 'cuda', or 'mps'
        """
        ...

    @abstractmethod
    def fit(self, X_train: np.ndarray, y_train: np.ndarray,
            X_val: np.ndarray, y_val: np.ndarray) -> TrainResult:
        """Train the model and return result with metrics."""
        ...

    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return class probability array, shape (N, n_classes)."""
        ...

    @abstractmethod
    def save(self, output_dir: str) -> dict[str, str]:
        """Save model artifacts. Returns dict of {artifact_name: path}."""
        ...

    @abstractmethod
    def load(self, model_dir: str) -> None:
        """Load model artifacts from directory."""
        ...
```

---

#### `train/trainers/ensemble_trainer.py`

Implement `RandomForestTrainer(BaseTrainer)` and `XGBoostTrainer(BaseTrainer)`.

**Requirements:**
- `RandomForestTrainer`: use `sklearn.ensemble.RandomForestClassifier` with `n_jobs=-1`.
  - Hyperparams from `**kwargs`: `n_estimators=200`, `max_depth=None`, `class_weight="balanced"`.
  - Save with `joblib.dump`.
- `XGBoostTrainer`: use `xgboost.XGBClassifier`.
  - Hyperparams: `n_estimators=300`, `max_depth=6`, `learning_rate=0.05`, `eval_metric="logloss"`, early stopping on val.
  - Device: pass `device` param if CUDA available.
  - Save as `xgboost.json`.
- Both must implement `predict_proba()` returning probabilities for each class.
- After fitting, compute `val_f1` and `val_auc` and include in `TrainResult`.

---

#### `train/trainers/cnn_trainer.py`

Implement `CNNTrainer(BaseTrainer)` using **PyTorch**.

**Architecture** (`CNNClassifier` nn.Module):
```
Input: (batch, n_features)                → Reshape to (batch, 1, n_features)
Conv1d(1, 64, kernel_size=3, padding=1)   → ReLU → BatchNorm1d
Conv1d(64, 128, kernel_size=3, padding=1) → ReLU → BatchNorm1d → MaxPool1d(2)
Dropout(0.3)
Flatten
Linear(128 * (n_features // 2), 256) → ReLU → Dropout(0.3)
Linear(256, n_classes)
Output: Softmax (for predict_proba) / raw logits (for loss)
```

**Requirements:**
- Use `torch.utils.data.DataLoader` with `num_workers=workers, pin_memory=True`.
- Use `torch.cuda.amp.autocast` if CUDA available.
- Log loss and accuracy per epoch using `train/utils/progress.py` (Rich progress bar).
- Save as `cnn.pt` (state_dict only).
- Hyperparams: `epochs=50`, `batch_size=256`, `lr=0.001`, `weight_decay=1e-4`.

---

#### `train/trainers/lstm_trainer.py`

Implement `LSTMTrainer(BaseTrainer)` using **PyTorch**.

**Architecture** (`LSTMClassifier` nn.Module):
```
Input: (batch, window_size, n_features)
LSTM(n_features, hidden_size=128, num_layers=2, batch_first=True, dropout=0.3)
→ take last hidden state h[-1]: (batch, hidden_size)
→ Attention: self-attention over LSTM outputs (optional but preferred)
Linear(128, 64) → ReLU → Dropout(0.3)
Linear(64, n_classes)
Output: Softmax / raw logits
```

**Requirements:**
- Read sequences from HDF5 file (`sequences/{split}_dns.h5` or `sequences/{split}_host.h5`).
- Implement `SequenceDataset(torch.utils.data.Dataset)` that reads from HDF5 lazily (one batch at a time, not loading all into RAM).
- Use gradient clipping: `torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)`.
- Hyperparams: `epochs=100`, `batch_size=128`, `lr=0.001`, `hidden_size=128`.
- Save as `lstm.pt`.

---

#### `train/fusion/late_fusion.py`

```python
import numpy as np
from scipy.optimize import minimize

class LateFusion:
    """
    Weighted average of probability outputs from multiple models.
    Weights are optimized on validation set to maximize F1-score.
    """

    def __init__(self, n_models: int):
        """
        Args:
            n_models: Number of models to fuse (e.g. 3 for RF+CNN+LSTM)
        """
        self.weights: np.ndarray = np.ones(n_models) / n_models

    def optimize_weights(self, proba_list: list[np.ndarray], y_true: np.ndarray) -> np.ndarray:
        """
        Find weights that maximize F1-score on validation predictions.

        Args:
            proba_list: List of (N, n_classes) probability arrays, one per model
            y_true: True integer labels, shape (N,)

        Returns:
            Optimized weights array of shape (n_models,)
        """
        ...

    def predict(self, proba_list: list[np.ndarray]) -> np.ndarray:
        """
        Weighted combination of probabilities.
        Returns predicted class labels, shape (N,).
        """
        ...

    def predict_proba(self, proba_list: list[np.ndarray]) -> np.ndarray:
        """Returns fused probabilities, shape (N, n_classes)."""
        ...

    def save(self, path: str) -> None:
        """Save weights to JSON file."""
        ...

    def load(self, path: str) -> None:
        """Load weights from JSON file."""
        ...
```

---

#### `train/explainability/shap_explainer.py`

```python
import numpy as np

class SHAPExplainer:
    """
    SHAP-based feature attribution.
    Selects explainer type automatically based on model type.
    """

    def explain_tree(self, model, X: np.ndarray, feature_names: list[str]) -> dict:
        """TreeExplainer for RandomForest or XGBoost. Returns shap_values dict."""
        ...

    def explain_deep(self, model, X_tensor, feature_names: list[str]) -> dict:
        """DeepExplainer / GradientExplainer for PyTorch CNN or LSTM."""
        ...

    def plot_summary(self, shap_values, feature_names: list[str], output_path: str) -> None:
        """Save SHAP beeswarm summary plot as PNG."""
        ...

    def top_features(self, shap_values, feature_names: list[str], n: int = 20) -> list[tuple[str, float]]:
        """Return top-N features by mean absolute SHAP value."""
        ...
```

---

#### `train/evaluation/metrics.py`

```python
import numpy as np
from dataclasses import dataclass

@dataclass
class EvaluationReport:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc: float
    fpr: float
    confusion_matrix: list[list[int]]
    per_class: dict[str, dict[str, float]]

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray,
                    y_proba: np.ndarray) -> EvaluationReport:
    """
    Compute all classification metrics.
    Uses sklearn: accuracy_score, precision_recall_fscore_support, roc_auc_score.
    """
    ...

def print_report(report: EvaluationReport, model_name: str) -> None:
    """Print formatted report using Rich Table."""
    ...
```

---

#### `train/utils/progress.py`

Implement `TrainingProgress` using **Rich**.

```python
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console
from rich.table import Table
from rich.live import Live
from contextlib import contextmanager

class TrainingProgress:
    """Rich-based progress display for training pipeline."""

    def __init__(self): ...

    @contextmanager
    def training_session(self, title: str):
        """Context manager that shows a live header panel."""
        ...

    def add_model_task(self, name: str, total_steps: int) -> int:
        """Add a progress task for a model. Returns task_id."""
        ...

    def update(self, task_id: int, advance: int = 1, description: str = "") -> None:
        """Advance a progress bar."""
        ...

    def print_metrics_table(self, results: list[dict]) -> None:
        """Print a Rich table of model metrics after training completes."""
        ...

    def print_banner(self, version: str) -> None:
        """Print the training start banner."""
        ...
```

---

#### `train/utils/data_loader.py`

```python
import pandas as pd
import numpy as np
import duckdb

class DuckDBDataLoader:
    """Load normalized features from DuckDB for training."""

    def __init__(self, db_path: str): ...

    def load_dns_stateful(self, split: str) -> tuple[np.ndarray, np.ndarray]:
        """Returns (X, y) arrays for DNS stateful features."""
        ...

    def load_dns_stateless(self, split: str) -> tuple[np.ndarray, np.ndarray]:
        """Returns (X, y) arrays for DNS stateless features."""
        ...

    def load_host(self, split: str) -> tuple[np.ndarray, np.ndarray]:
        """Returns (X, y) arrays for host features."""
        ...

    def load_combined(self, split: str) -> tuple[np.ndarray, np.ndarray]:
        """Load and concatenate all sources. Returns (X, y)."""
        ...
```

---

#### `train/utils/checkpoint.py`

```python
import json
from pathlib import Path

class CheckpointManager:
    """Save and restore training checkpoints per model version."""

    def __init__(self, version: str, models_dir: str = "models"): ...

    def save(self, model_name: str, epoch: int, state: dict) -> None:
        """Save checkpoint dict as JSON + binary state."""
        ...

    def load_latest(self, model_name: str) -> dict | None:
        """Load the most recent checkpoint. Returns None if none exists."""
        ...

    def is_complete(self, model_name: str) -> bool:
        """Check if model training already completed for this version."""
        ...
```

---

#### `train/pipeline.py`

The main orchestrator. Runs the full pipeline.

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

@dataclass
class PipelineConfig:
    version: str
    source: str             # "dns" | "host" | "all"
    models: list[str]       # ["rf", "xgb", "cnn", "lstm"]
    split_train: str        # "TRAIN"
    split_val: str          # "VALIDATION"
    epochs_cnn: int
    epochs_lstm: int
    batch_size: int
    lr: float
    workers: int
    device: str
    no_shap: bool
    resume: bool
    db_path: str
    models_dir: str
    sequences_dir: str

class TrainPipeline:
    """
    Orchestrates the full training process:
    data loading → parallel training → fusion → evaluation → saving.
    """

    def __init__(self, config: PipelineConfig): ...

    async def run(self) -> dict:
        """
        Execute full pipeline asynchronously.
        RF + XGBoost + CNN run in parallel via asyncio.gather.
        LSTM runs after (uses sequence data).
        Returns final evaluation metrics dict.
        """
        ...

    async def _train_ensemble(self, X_train, y_train, X_val, y_val): ...
    async def _train_cnn(self, X_train, y_train, X_val, y_val): ...
    async def _train_lstm(self): ...

    def _save_model_version(self, trainers, fusion, metrics) -> None:
        """Save all artifacts and metadata.json to models/{version}/."""
        ...
```

---

### 3. `models/` — Model storage

Create the folder structure. Do NOT pre-populate with model files.

```
models/
└── .gitkeep
```

Each trained version will create `models/v{N}/` automatically with:
- `random_forest.joblib`
- `xgboost.json`
- `cnn.pt`
- `lstm.pt`
- `fusion_weights.json`
- `feature_scaler.joblib`
- `label_encoder.joblib`
- `shap_summary.png`
- `metadata.json`

---

### 4. `sequences/` — HDF5 sequence storage

Create the folder:
```
sequences/
└── .gitkeep
```

`SequenceBuilder` will write files here: `{split}_{source}.h5`

---

### 5. Extend `manage.py`

Add new commands to the existing `match` block. Follow the existing `module service action` pattern exactly.

**Add these commands:**

```python
case ("normalize", "dns", "stateful" | "stateless"):
    # Run DNSStatefulNormalizer or DNSStatelessNormalizer
    # Split determined by optional --split arg (default: all splits)

case ("normalize", "host", "all"):
    # Run HostNormalizer for all splits

case ("normalize", "all", "all"):
    # Run all normalizers sequentially

case ("train", version, model_spec):
    # version like "v1", model_spec like "all" | "rf" | "xgb" | "cnn" | "lstm"
    # Read additional args from argv for epochs, batch_size, etc.

case ("evaluate", version, split):
    # Load models/version/, run evaluation on given split, print report

case ("info", "models", _):
    # List all versions in models/ with their metadata.json summary

case ("info", "db", _):
    # Show DuckDB table row counts
```

**For parsing extra args** in train/normalize commands, add a secondary `argparse.ArgumentParser` inside the case block:
```python
case ("train", version, model_spec):
    sub = argparse.ArgumentParser()
    sub.add_argument("--epochs-cnn", type=int, default=50)
    sub.add_argument("--epochs-lstm", type=int, default=100)
    sub.add_argument("--batch-size", type=int, default=256)
    sub.add_argument("--lr", type=float, default=0.001)
    sub.add_argument("--workers", type=int, default=4)
    sub.add_argument("--device", type=str, default="auto")
    sub.add_argument("--no-shap", action="store_true")
    sub.add_argument("--resume", action="store_true")
    sub_args = sub.parse_args(sys.argv[4:])
    ...
```

---

### 6. Update `requirements.txt`

Replace the current minimal requirements with:

```
python-dotenv==1.1.1
rich
pandas>=2.0
numpy>=1.26
scikit-learn>=1.4
xgboost>=2.0
torch>=2.2
shap>=0.45
h5py>=3.10
duckdb>=1.0
joblib>=1.3
scipy>=1.12
```

---

## Coding standards (mandatory)

1. **OOP everywhere** — no standalone functions except module-level helpers. Use dataclasses for config and results.
2. **Docstrings on every class, method, and function** — include `Args:`, `Returns:`, `Raises:` where applicable.
3. **Type hints on every function signature** — no bare `def f(x)`.
4. **`concurrent.futures.ThreadPoolExecutor`** for I/O (file reading).
5. **`concurrent.futures.ProcessPoolExecutor`** for CPU-bound normalization.
6. **`asyncio`** for the training pipeline orchestration.
7. **Rich** for all CLI output — no bare `print()` in new code.
8. **Do not modify** `scripts/`, `datasets-new/`, `databases/` directories.
9. **Read `.env` values** only via `os.getenv()` after `load_dotenv()`. Never hardcode paths.
10. The `duckdb` Python package connects to the file at `Path(os.getenv("DUCKDB_DATA_PATH")) / os.getenv("DUCKDB_DATABASE")`. The Docker container provides interactive inspection only — Python reads/writes the `.duckdb` file directly.

---

## Environment variables (from `.env`)

```
PATH_DATASETS_NEW_DNS_FOLDER   # path to datasets-new/dns
PATH_DATASETS_NEW_HOST_FOLDER  # path to datasets-new/host
DUCKDB_DATA_PATH               # directory where .duckdb file lives
DUCKDB_DATABASE                # filename e.g. proposal.duckdb
SEQUENCES_DIR                  # path to sequences/ output folder (default: ./sequences)
MODELS_DIR                     # path to models/ output folder (default: ./models)
```

---

## Expected CLI usage after implementation

```bash
# Step 1 — Start database (already configured)
python manage.py db duckdb start

# Step 2 — Normalize DNS datasets
python manage.py normalize dns stateful
python manage.py normalize dns stateless

# Step 3 — Normalize Host datasets
python manage.py normalize host all

# Step 4 — Train full hybrid framework version v1
python manage.py train v1 all --epochs-cnn 50 --epochs-lstm 100 --batch-size 256

# Step 5 — Evaluate on test split
python manage.py evaluate v1 TEST

# Step 6 — Check model info
python manage.py info models all
```

---

## Definition of done

- [ ] `normalization/` — all 7 files implemented, classes instantiable, `run()` produces a non-empty DataFrame
- [ ] `normalization/db_writer.py` — `DuckDBWriter.write_dataframe()` creates tables and inserts rows without error
- [ ] `train/` — all files implemented, `TrainPipeline` can be instantiated without import errors
- [ ] `train/trainers/` — each trainer's `fit()` and `predict_proba()` work on dummy NumPy arrays
- [ ] `train/fusion/late_fusion.py` — `optimize_weights()` runs without error on random probability arrays
- [ ] `models/` folder exists with `.gitkeep`
- [ ] `sequences/` folder exists with `.gitkeep`
- [ ] `manage.py` — new commands registered and parseable
- [ ] `requirements.txt` — updated
- [ ] All classes have docstrings and type hints
- [ ] `python manage.py --help` does not crash (existing commands still work)
