import importlib.util
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from train.fusion.late_fusion import LateFusion
from train.trainers.ensemble_trainer import RandomForestTrainer


class TrainingPipelineTests(unittest.TestCase):
    def test_late_fusion_optimizes_weights(self) -> None:
        y_true = np.array([0, 1, 1, 0], dtype=np.int32)
        proba_a = np.array([[0.9, 0.1], [0.2, 0.8], [0.4, 0.6], [0.8, 0.2]], dtype=np.float32)
        proba_b = np.array([[0.6, 0.4], [0.3, 0.7], [0.7, 0.3], [0.4, 0.6]], dtype=np.float32)

        weights = LateFusion(n_models=2).optimize_weights([proba_a, proba_b], y_true)

        self.assertEqual(weights.shape, (2,))
        self.assertAlmostEqual(float(np.sum(weights)), 1.0, places=5)

    def test_random_forest_trainer_fits_dummy_arrays(self) -> None:
        X_train = np.array([[0, 0], [1, 1], [0, 1], [1, 0]], dtype=np.float32)
        y_train = np.array([0, 1, 0, 1], dtype=np.int32)
        X_val = np.array([[0, 0], [1, 1]], dtype=np.float32)
        y_val = np.array([0, 1], dtype=np.int32)

        trainer = RandomForestTrainer(version="unit", n_estimators=5, random_state=42)
        result = trainer.fit(X_train, y_train, X_val, y_val)
        proba = trainer.predict_proba(X_val)

        self.assertEqual(result.model_name, "random_forest")
        self.assertEqual(proba.shape, (2, 2))

    @unittest.skipIf(importlib.util.find_spec("torch") is None, "torch is not installed")
    def test_cnn_and_lstm_trainers_import_with_torch(self) -> None:
        from train.trainers.cnn_trainer import CNNTrainer
        from train.trainers.lstm_trainer import LSTMTrainer

        self.assertEqual(CNNTrainer(version="unit", epochs=1, batch_size=2).model_name, "cnn")
        self.assertEqual(LSTMTrainer(version="unit", epochs=1, batch_size=2).model_name, "lstm")

    @unittest.skipIf(importlib.util.find_spec("torch") is None, "torch is not installed")
    def test_cnn_trainer_handles_single_feature_input(self) -> None:
        from train.trainers.cnn_trainer import CNNTrainer

        X_train = np.array([[0.0], [1.0], [2.0], [3.0]], dtype=np.float32)
        y_train = np.array([0, 1, 0, 1], dtype=np.int32)
        X_val = np.array([[0.5], [2.5]], dtype=np.float32)
        y_val = np.array([0, 1], dtype=np.int32)

        trainer = CNNTrainer(version="unit", epochs=1, batch_size=2, workers=0)
        result = trainer.fit(X_train, y_train, X_val, y_val)

        self.assertEqual(result.model_name, "cnn")
        self.assertEqual(trainer.predict_proba(X_val).shape, (2, 2))

    @unittest.skipIf(importlib.util.find_spec("h5py") is None, "h5py is not installed")
    @unittest.skipIf(importlib.util.find_spec("torch") is None, "torch is not installed")
    def test_lstm_trainer_rejects_empty_hdf5_sequences(self) -> None:
        import h5py
        from train.trainers.lstm_trainer import LSTMTrainer

        with TemporaryDirectory() as temp_dir:
            train_path = Path(temp_dir) / "train.h5"
            val_path = Path(temp_dir) / "val.h5"
            for path in (train_path, val_path):
                with h5py.File(path, "w") as handle:
                    handle.create_dataset("X", data=np.empty((0, 4, 2), dtype=np.float32))
                    handle.create_dataset("y", data=np.empty((0,), dtype=np.int32))

            with self.assertRaisesRegex(ValueError, "at least one sequence"):
                LSTMTrainer(version="unit", epochs=1).fit_from_hdf5(train_path, val_path)

    @unittest.skipIf(importlib.util.find_spec("duckdb") is None, "duckdb is not installed")
    def test_duckdb_loader_returns_empty_for_missing_tables(self) -> None:
        from train.utils.data_loader import DuckDBDataLoader

        with TemporaryDirectory() as temp_dir:
            loader = DuckDBDataLoader(Path(temp_dir) / "empty.duckdb")
            try:
                X, y = loader.load_host("TRAIN")
            finally:
                loader.close()

        self.assertEqual(X.shape, (0, 4))
        self.assertEqual(y.shape, (0,))

    def test_manage_help_does_not_crash(self) -> None:
        result = subprocess.run(
            [sys.executable, "manage.py", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
