// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DataManagementPage } from "./DataManagementPage";

const { apiMock, usePollingMock, i18nMock, authMock } = vi.hoisted(() => {
  const apiMock = {
    listRawDatasetFiles: vi.fn(),
    inspectRawDatasetFile: vi.fn(),
    registerManagedDataset: vi.fn(),
    validateManagedDataset: vi.fn(),
    deleteManagedDataset: vi.fn(),
    deleteAllManagedDatasets: vi.fn(),
  };

  const translations = {
    "datasets.rawFiles.loading": "Loading uploaded files...",
    "datasets.register.title": "Dataset registration",
    "datasets.register.subtitle": "Register a dataset by linking it to an already uploaded raw file.",
    "datasets.messages.registered": "Dataset registered",
    "datasets.form.nameLabel": "Name",
    "datasets.form.fileNameLabel": "Uploaded file",
    "datasets.form.fileSelectPlaceholder": "Select a previously uploaded file",
    "datasets.form.featureFamiliesLabel": "Feature families",
    "datasets.form.submit": "Register dataset",
    "datasets.form.inspectSummary": "Format: {format} | profile: {profile} | schemas: {schemas}",
    "datasets.form.targetColumns": "Target columns: {columns}",
    "datasets.form.noFiles": "Upload files in the data loading module before registering a dataset.",
    "datasets.form.featureSetEmpty": "No feature families are available for the selected file yet.",
    "datasets.form.featureSetHint": "Select one or more feature families.",
    "datasets.form.validation.required": "This field is required",
    "datasets.list.title": "Datasets",
    "datasets.list.subtitle": "Registered datasets linked to uploaded files.",
    "datasets.list.loading": "Loading...",
    "datasets.list.empty": "No registered datasets yet.",
    "datasets.list.columns.id": "ID",
    "datasets.list.columns.name": "Name",
    "datasets.list.columns.filePath": "File path",
    "datasets.list.columns.createdAt": "Created at",
    "datasets.list.columns.actions": "Actions",
    "datasets.list.actions.delete": "Delete",
    "datasets.list.actions.deleteAll": "Clear all",
    "datasets.actions.validate": "Validate and normalize",
    "datasets.list.messages.deleted": "Dataset deleted: {name}",
    "datasets.list.messages.deletedAll": "All dataset records deleted",
    "datasets.list.deleteDialog.title": "Delete dataset",
    "datasets.list.deleteDialog.description": "Delete dataset {name}? Only the registry record will be removed.",
    "datasets.list.deleteDialog.cancel": "Cancel",
    "datasets.list.deleteDialog.confirm": "Delete",
    "datasets.list.deleteAllDialog.title": "Clear all datasets",
    "datasets.list.deleteAllDialog.description": "Delete all dataset records? This action requires confirmation.",
    "datasets.messages.validationQueued": "Validation job queued: {id}",
    "api.errors.request": "Request failed",
  } as Record<string, string>;

  const usePollingMock = vi.fn(() => ({
    data: {
      managedDatasets: [],
      featureSchemas: [],
    },
    error: null,
    loading: false,
  }));

  const i18nMock = {
    t: (key: string, params?: Record<string, string | number>) => {
      const template = translations[key] ?? key;
      return template.replace(/\{(\w+)\}/g, (_, token: string) => String(params?.[token] ?? `{${token}}`));
    },
  };

  const authMock = { tokens: { access_token: "token" } };

  return { apiMock, usePollingMock, i18nMock, authMock };
});

function buildRawFile(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: "raw-file-1",
    name: "customers.csv",
    path: "/app/app-data/raw/uploads/customers.csv",
    relative_path: "uploads/customers.csv",
    size: 128,
    format: "csv",
    modified_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function buildManagedDataset(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: "managed-dataset-1",
    raw_file_id: "raw-file-1",
    name: "Managed telemetry",
    file_path: "/app/app-data/raw/uploads/customers.csv",
    feature_set: ["dns", "network_flow"],
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function buildFeatureSchema(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: "schema-1",
    name: "dns-domain-tabular",
    version: "1.0.0",
    source_type: "network",
    definition: {
      feature_families: ["dns", "network_flow"],
    },
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

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

describe("DataManagementPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    usePollingMock.mockReturnValue({
      data: {
        managedDatasets: [],
        featureSchemas: [buildFeatureSchema()],
      },
      error: null,
      loading: false,
    });

    apiMock.listRawDatasetFiles.mockResolvedValue([buildRawFile()]);
    apiMock.inspectRawDatasetFile.mockResolvedValue({
      relative_path: "uploads/customers.csv",
      format: "csv",
      normalization_profile: "generic_tabular",
      columns: ["entity_id", "event_ts", "feature_a"],
      suggested_name: "customers-dataset",
      target_columns: ["entity_id", "event_ts", "source_type", "label"],
      quality_warnings: [],
      supporting_only: false,
      compatible_feature_schemas: ["dns-domain-tabular"],
    });
    apiMock.registerManagedDataset.mockResolvedValue(buildManagedDataset());
    apiMock.validateManagedDataset.mockResolvedValue({
      id: "task-1",
      task_name: "normalization.validate_dataset",
      object_type: "dataset",
      object_id: "legacy-dataset-1",
      status: "pending",
      detail: {},
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });
    apiMock.deleteManagedDataset.mockResolvedValue({ message: "deleted" });
    apiMock.deleteAllManagedDatasets.mockResolvedValue({ message: "deleted" });
  });

  it("autofills the dataset name, renders feature checkboxes, and submits the registry record", async () => {
    render(<DataManagementPage />);

    await waitFor(() => expect(apiMock.listRawDatasetFiles).toHaveBeenCalledWith("token"));

    fireEvent.mouseDown(screen.getByRole("combobox", { name: "Uploaded file" }));
    fireEvent.click(await screen.findByRole("option", { name: "uploads/customers.csv" }));

    await waitFor(() => expect(apiMock.inspectRawDatasetFile).toHaveBeenCalledWith("token", "uploads/customers.csv"));
    expect(await screen.findByDisplayValue("customers-dataset")).toBeTruthy();

    fireEvent.click(await screen.findByRole("checkbox", { name: "dns" }));
    fireEvent.click(await screen.findByRole("checkbox", { name: "network_flow" }));
    fireEvent.click(screen.getByRole("button", { name: "Register dataset" }));

    await waitFor(() =>
      expect(apiMock.registerManagedDataset).toHaveBeenCalledWith("token", {
        name: "customers-dataset",
        raw_file_id: "raw-file-1",
        feature_set: ["dns", "network_flow"],
      }),
    );
    expect(await screen.findByText("Dataset registered")).toBeTruthy();
  });

  it("renders empty states for raw files and managed datasets", async () => {
    apiMock.listRawDatasetFiles.mockResolvedValueOnce([]);
    usePollingMock.mockReturnValueOnce({
      data: {
        managedDatasets: [],
        featureSchemas: [],
      },
      error: null,
      loading: false,
    });

    render(<DataManagementPage />);

    await waitFor(() => expect(apiMock.listRawDatasetFiles).toHaveBeenCalledWith("token"));
    expect(await screen.findByText("Upload files in the data loading module before registering a dataset.")).toBeTruthy();
    expect(screen.getByText("No registered datasets yet.")).toBeTruthy();
  });

  it("deletes a managed dataset record from the registry table", async () => {
    usePollingMock.mockReturnValue({
      data: {
        managedDatasets: [buildManagedDataset()],
        featureSchemas: [buildFeatureSchema()],
      },
      error: null,
      loading: false,
    });

    render(<DataManagementPage />);

    const datasetRow = (await screen.findByText("Managed telemetry")).closest("tr") as HTMLElement;
    fireEvent.click(within(datasetRow).getByRole("button", { name: "Delete" }));

    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(apiMock.deleteManagedDataset).toHaveBeenCalledWith("token", "managed-dataset-1"));
    expect(await screen.findByText("Dataset deleted: Managed telemetry")).toBeTruthy();
  });

  it("queues validation for a managed dataset from the registry table", async () => {
    usePollingMock.mockReturnValue({
      data: {
        managedDatasets: [buildManagedDataset()],
        featureSchemas: [buildFeatureSchema()],
      },
      error: null,
      loading: false,
    });

    render(<DataManagementPage />);

    const datasetRow = (await screen.findByText("Managed telemetry")).closest("tr") as HTMLElement;
    fireEvent.click(within(datasetRow).getByRole("button", { name: "Validate and normalize" }));

    await waitFor(() => expect(apiMock.validateManagedDataset).toHaveBeenCalledWith("token", "managed-dataset-1"));
    expect(await screen.findByText("Validation job queued: task-1")).toBeTruthy();
  });

  it("clears all managed dataset records after confirmation", async () => {
    usePollingMock.mockReturnValue({
      data: {
        managedDatasets: [buildManagedDataset()],
        featureSchemas: [buildFeatureSchema()],
      },
      error: null,
      loading: false,
    });

    render(<DataManagementPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Clear all" }));

    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(apiMock.deleteAllManagedDatasets).toHaveBeenCalledWith("token"));
    expect(await screen.findByText("All dataset records deleted")).toBeTruthy();
  });
});
