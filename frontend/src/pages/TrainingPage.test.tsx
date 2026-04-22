// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TrainingPage } from "./TrainingPage";

const { apiMock, usePollingMock, i18nMock, authMock } = vi.hoisted(() => {
  const apiMock = {
    createTrainingRun: vi.fn(),
  };

  const translations = {
    "training.newRun.title": "New training run",
    "training.newRun.subtitle": "Hybrid training of sequential models with late fusion",
    "training.history.title": "Training history",
    "training.history.subtitle": "Candidate models remain separated until promotion",
    "training.form.datasetLabel": "Dataset",
    "training.form.featureSchemaLabel": "Feature schema",
    "training.form.sequenceLengthLabel": "Sequence length",
    "training.form.sequenceStrideLabel": "Sequence stride",
    "training.form.submit": "Start training",
    "training.messages.queued": "Training queued: {id}",
    "training.messages.datasetRequired": "Select a dataset before starting training.",
    "training.messages.featureSchemaRequired": "Select a feature schema before starting training.",
    "training.messages.datasetUnavailable": "The selected dataset is no longer available.",
    "training.messages.datasetValidationRequired": "Dataset must be validated before training.",
    "training.runTitle": "Run {id}",
    "training.datasetSchema": "Dataset {datasetId} | Schema {schemaId}",
    "common.na": "n/a",
  } as Record<string, string>;

  const usePollingMock = vi.fn(() => ({
    data: {
      datasets: [],
      schemas: [],
      runs: [],
    },
  }));

  const i18nMock = {
    t: (key: string, params?: Record<string, string | number>) => {
      const template = translations[key] ?? key;
      return template.replace(/\{(\w+)\}/g, (_, token: string) => String(params?.[token] ?? `{${token}}`));
    },
    tEnum: (_scope: string, value: string) => value,
  };

  const authMock = { tokens: { access_token: "token" } };

  return { apiMock, usePollingMock, i18nMock, authMock };
});

vi.mock("../api/client", () => ({
  api: apiMock,
}));

vi.mock("../hooks/useAuth", () => ({
  useAuth: () => authMock,
}));

vi.mock("../hooks/usePolling", () => ({
  usePolling: (...args: unknown[]) => usePollingMock(...args),
}));

vi.mock("../i18n", () => ({
  useI18n: () => i18nMock,
}));

describe("TrainingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePollingMock.mockReturnValue({
      data: {
        datasets: [
          {
            id: "dataset-validated",
            name: "Validated dataset",
            validation_status: "validated",
            normalization_profile: "dns_pcap_dns_flow",
          },
        ],
        schemas: [
          {
            id: "schema-1",
            name: "dns-pcap-flow",
            version: "1.0.0",
          },
        ],
        runs: [],
      },
    });
    apiMock.createTrainingRun.mockResolvedValue({ id: "run-1" });
  });

  it("shows an error when the dataset is missing", async () => {
    render(<TrainingPage />);

    fireEvent.submit(screen.getByRole("button", { name: "Start training" }).closest("form") as HTMLFormElement);

    expect(await screen.findByText("Select a dataset before starting training.")).toBeTruthy();
    expect(apiMock.createTrainingRun).not.toHaveBeenCalled();
  });

  it("queues a training run for a validated dataset and selected schema", async () => {
    render(<TrainingPage />);

    fireEvent.mouseDown(screen.getByRole("combobox", { name: "Dataset" }));
    fireEvent.click(await screen.findByRole("option", { name: "Validated dataset | dns_pcap_dns_flow" }));

    fireEvent.mouseDown(screen.getByRole("combobox", { name: "Feature schema" }));
    fireEvent.click(await screen.findByRole("option", { name: "dns-pcap-flow v1.0.0" }));

    fireEvent.click(screen.getByRole("button", { name: "Start training" }));

    await waitFor(() =>
      expect(apiMock.createTrainingRun).toHaveBeenCalledWith("token", {
        dataset_id: "dataset-validated",
        feature_schema_id: "schema-1",
        sequence_length: 50,
        sequence_stride: 10,
        models: ["random_forest", "xgboost", "cnn", "lstm", "fusion"],
        hyperparameters: {},
      }),
    );
    expect(await screen.findByText("Training queued: run-1")).toBeTruthy();
  });
});
