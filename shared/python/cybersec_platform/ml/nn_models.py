from __future__ import annotations

from typing import Any

import numpy as np
import torch


class EventCnnBinaryClassifier(torch.nn.Module):
    def __init__(self, input_size: int) -> None:
        super().__init__()
        self.network = torch.nn.Sequential(
            torch.nn.Conv1d(1, 8, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.Conv1d(8, 16, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.AdaptiveAvgPool1d(1),
        )
        self.output = torch.nn.Linear(16, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        hidden = self.network(x).squeeze(-1)
        return torch.sigmoid(self.output(hidden))


class SequenceLstmBinaryClassifier(torch.nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 24) -> None:
        super().__init__()
        self.lstm = torch.nn.LSTM(input_size=input_size, hidden_size=hidden_size, batch_first=True)
        self.output = torch.nn.Linear(hidden_size, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        encoded, _ = self.lstm(x)
        last_hidden = encoded[:, -1, :]
        return torch.sigmoid(self.output(last_hidden))


def predict_event_cnn(payload: dict[str, Any], features: np.ndarray) -> np.ndarray:
    model = EventCnnBinaryClassifier(input_size=payload["input_size"])
    model.load_state_dict(payload["state_dict"])
    model.eval()
    with torch.no_grad():
        tensor = torch.tensor(features[:, None, :], dtype=torch.float32)
        return model(tensor).squeeze(-1).numpy()


def predict_sequence_lstm(payload: dict[str, Any], features: np.ndarray) -> np.ndarray:
    model = SequenceLstmBinaryClassifier(input_size=payload["input_size"], hidden_size=payload.get("hidden_size", 24))
    model.load_state_dict(payload["state_dict"])
    model.eval()
    with torch.no_grad():
        tensor = torch.tensor(features, dtype=torch.float32)
        return model(tensor).squeeze(-1).numpy()

