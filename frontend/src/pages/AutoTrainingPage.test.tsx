// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AutoTrainingPage } from "./AutoTrainingPage";
import type { UploadSession } from "../types/api";

const { apiMock, usePollingMock, i18nMock, authMock } = vi.hoisted(() => {
  const apiMock = {
    createAutoTrainingUploadSession: vi.fn(),
    uploadAutoTrainingArchiveChunk: vi.fn(),
    completeAutoTrainingUploadSession: vi.fn(),
    discardAutoTrainingUploadSession: vi.fn(),
    deleteAutoTrainingArchive: vi.fn(),
    deleteAllAutoTrainingArchives: vi.fn(),
    startAutoTrainingJob: vi.fn(),
  };

  const translations = {
    "autoTraining.upload.title": "Archive upload",
    "autoTraining.upload.subtitle": "Upload archives from a local folder.",
    "autoTraining.upload.folderLabel": "Archive folder",
    "autoTraining.upload.folderPlaceholder": "Choose folder",
    "autoTraining.upload.selectFolder": "Choose folder",
    "autoTraining.upload.submit": "Upload archives",
    "autoTraining.upload.uploading": "Uploading...",
    "autoTraining.upload.selectionSummary": "{root} | {count} files | {size}",
    "autoTraining.upload.progress": "Uploaded {uploaded} of {total} ({percent}%)",
    "autoTraining.upload.currentFile": "Current archive: {file}",
    "autoTraining.upload.emptyFiles": "The selected folder does not contain supported archives.",
    "autoTraining.upload.unsupportedSkipped": "Skipped unsupported files: {count}",
    "autoTraining.upload.success": "Archives uploaded: {count}",
    "autoTraining.upload.folderRequired": "Select a folder with archives before upload",
    "autoTraining.upload.errors.sessionFileMissing": "Upload session is missing archive metadata: {file}",
    "autoTraining.archives.title": "Uploaded archives",
    "autoTraining.archives.subtitle": "Manage uploaded archives.",
    "autoTraining.archives.loading": "Loading uploaded archives...",
    "autoTraining.archives.empty": "No uploaded archives yet.",
    "autoTraining.archives.columns.id": "ID",
    "autoTraining.archives.columns.name": "Name",
    "autoTraining.archives.columns.size": "Size",
    "autoTraining.archives.columns.createdAt": "Uploaded at",
    "autoTraining.archives.columns.actions": "Actions",
    "autoTraining.archives.actions.delete": "Delete",
    "autoTraining.archives.actions.deleteAll": "Delete all",
    "autoTraining.archives.messages.deleted": "Archive deleted: {name}",
    "autoTraining.archives.messages.deletedAll": "All archives deleted",
    "autoTraining.archives.deleteDialog.title": "Delete archive",
    "autoTraining.archives.deleteDialog.description": "Delete archive {name}?",
    "autoTraining.archives.deleteDialog.cancel": "Cancel",
    "autoTraining.archives.deleteDialog.confirm": "Delete",
    "autoTraining.archives.deleteAllDialog.title": "Delete all archives",
    "autoTraining.archives.deleteAllDialog.description": "Delete all archives?",
    "autoTraining.jobs.title": "Automatic training runs",
    "autoTraining.jobs.subtitle": "Track automatic training.",
    "autoTraining.jobs.loading": "Loading automatic training runs...",
    "autoTraining.jobs.empty": "No automatic training runs yet.",
    "autoTraining.jobs.jobTitle": "Auto training {id}",
    "autoTraining.jobs.jobMeta": "Source: {sourceType} | Archives: {archives}",
    "autoTraining.jobs.currentStep": "Current step: {step}",
    "autoTraining.jobs.actions.start": "Start training",
    "autoTraining.jobs.actions.starting": "Starting...",
    "autoTraining.jobs.messages.started": "Automatic training started: {id}",
    "autoTraining.jobs.fields.createdAt": "Created at",
    "autoTraining.jobs.fields.datasetId": "Dataset ID",
    "autoTraining.jobs.fields.trainingRuns": "Training run ID",
    "autoTraining.jobs.steps.queued": "Queued",
    "autoTraining.jobs.steps.training_models": "Training models",
    "api.errors.request": "Request failed",
    "common.na": "n/a",
    "common.sourceType.host": "Host",
    "common.sourceType.network": "Network",
    "common.jobStatus.pending": "Queued",
    "common.jobStatus.running": "Running",
    "common.jobStatus.completed": "Completed",
    "common.jobStatus.failed": "Failed",
  } as Record<string, string>;

  const usePollingMock = vi.fn(() => ({
    data: { archives: [], jobs: [] },
    error: null,
    loading: false,
  }));

  const i18nMock = {
    t: (key: string, params?: Record<string, string | number>) => {
      const template = translations[key] ?? key;
      return template.replace(/\{(\w+)\}/g, (_, token: string) => String(params?.[token] ?? `{${token}}`));
    },
    tEnum: (scope: string, value: string) => translations[`${scope}.${value}`] ?? value,
  };

  const authMock = { tokens: { access_token: "token" }, ensureAccessToken: vi.fn() };

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

function buildArchive(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    id: "archive-1",
    name: "trace-1.zip",
    path: "/app/app-data/archives/incoming/trace-1.zip",
    relative_path: "incoming/trace-1.zip",
    size: 128,
    format: "zip",
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("AutoTrainingPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authMock.ensureAccessToken.mockResolvedValue("token");
    usePollingMock.mockReturnValue({
      data: { archives: [], jobs: [] },
      error: null,
      loading: false,
    });
    apiMock.createAutoTrainingUploadSession.mockResolvedValue({
      session_id: "archive-upload-session-1",
      status: "open",
      created_at: "2026-01-01T00:00:00Z",
      total_size_bytes: 64,
      files: [
        {
          file_id: "archive-file-1",
          relative_path: "incoming/sample.zip",
          size_bytes: 64,
          uploaded_bytes: 0,
          content_type: "application/zip",
          status: "pending",
        },
      ],
    } satisfies UploadSession);
    apiMock.uploadAutoTrainingArchiveChunk.mockImplementation(
      async (
        _token: string,
        _sessionId: string,
        _fileId: string,
        _chunk: Blob,
        _offset: number,
        chunkLength: number,
        onProgress?: (loadedBytes: number) => void,
      ) => {
        onProgress?.(chunkLength);
        return {
          session_id: "archive-upload-session-1",
          file_id: "archive-file-1",
          status: "uploaded",
          uploaded_bytes: chunkLength,
          size_bytes: chunkLength,
        };
      },
    );
    apiMock.completeAutoTrainingUploadSession.mockResolvedValue({
      session_id: "archive-upload-session-1",
      status: "completed",
      uploaded_archives: [buildArchive()],
      archives: [buildArchive()],
    });
    apiMock.discardAutoTrainingUploadSession.mockResolvedValue(undefined);
    apiMock.deleteAutoTrainingArchive.mockResolvedValue({ message: "deleted" });
    apiMock.deleteAllAutoTrainingArchives.mockResolvedValue({ message: "deleted" });
    apiMock.startAutoTrainingJob.mockResolvedValue({
      id: "job-1",
      requested_by_user_id: "user-1",
      source_type: "host",
      archive_ids: ["archive-1"],
      status: "pending",
      progress_percent: 0,
      current_step: "queued",
      detail: { archive_count: 1 },
      error_message: null,
      dataset_id: null,
      feature_schema_id: null,
      training_run_ids: [],
      model_artifact_ids: [],
      created_at: "2026-01-01T00:00:00Z",
      started_at: null,
      completed_at: null,
    });
  });

  it("uploads only supported archive files from the selected folder", async () => {
    const { container } = render(<AutoTrainingPage />);

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const zipFile = new File(["zip-data"], "sample.zip", { type: "application/zip" });
    const ignoredFile = new File(["plain"], "ignored.txt", { type: "text/plain" });
    Object.defineProperty(zipFile, "webkitRelativePath", { value: "incoming/sample.zip" });
    Object.defineProperty(ignoredFile, "webkitRelativePath", { value: "incoming/ignored.txt" });

    fireEvent.change(fileInput, { target: { files: [zipFile, ignoredFile] } });
    expect(await screen.findByDisplayValue(`incoming | 1 files | ${zipFile.size} B`)).toBeTruthy();
    expect(await screen.findByText("Skipped unsupported files: 1")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Upload archives" }));

    await waitFor(() =>
      expect(apiMock.createAutoTrainingUploadSession).toHaveBeenCalledWith("token", {
        files: [
          {
            relative_path: "incoming/sample.zip",
            size_bytes: zipFile.size,
            content_type: "application/zip",
          },
        ],
      }),
    );
    await waitFor(() => expect(apiMock.uploadAutoTrainingArchiveChunk).toHaveBeenCalled());
    await waitFor(() => expect(apiMock.completeAutoTrainingUploadSession).toHaveBeenCalledWith("token", "archive-upload-session-1"));
    expect(await screen.findByText("Archives uploaded: 1")).toBeTruthy();
  });

  it("refreshes the access token during archive upload", async () => {
    authMock.ensureAccessToken
      .mockResolvedValueOnce("token-create")
      .mockResolvedValueOnce("token-chunk")
      .mockResolvedValueOnce("token-complete");

    const { container } = render(<AutoTrainingPage />);

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const zipFile = new File(["zip-data"], "sample.zip", { type: "application/zip" });
    Object.defineProperty(zipFile, "webkitRelativePath", { value: "incoming/sample.zip" });

    fireEvent.change(fileInput, { target: { files: [zipFile] } });
    fireEvent.click(screen.getByRole("button", { name: "Upload archives" }));

    await waitFor(() =>
      expect(apiMock.createAutoTrainingUploadSession).toHaveBeenCalledWith("token-create", {
        files: [
          {
            relative_path: "incoming/sample.zip",
            size_bytes: zipFile.size,
            content_type: "application/zip",
          },
        ],
      }),
    );
    await waitFor(() => expect(apiMock.uploadAutoTrainingArchiveChunk).toHaveBeenCalledWith(
      "token-chunk",
      "archive-upload-session-1",
      "archive-file-1",
      expect.any(Blob),
      0,
      zipFile.size,
      expect.any(Function),
    ));
    await waitFor(() => expect(apiMock.completeAutoTrainingUploadSession).toHaveBeenCalledWith("token-complete", "archive-upload-session-1"));
  });

  it("renders existing automatic training job progress", async () => {
    usePollingMock.mockReturnValue({
      data: {
        archives: [buildArchive()],
        jobs: [
          {
            id: "job-running",
            requested_by_user_id: "user-1",
            source_type: "host",
            archive_ids: ["archive-1"],
            status: "running",
            progress_percent: 72,
            current_step: "training_models",
            detail: { archive_count: 1 },
            error_message: null,
            dataset_id: "dataset-1",
            feature_schema_id: "schema-1",
            training_run_ids: ["training-run-1"],
            model_artifact_ids: [],
            created_at: "2026-01-01T00:00:00Z",
            started_at: "2026-01-01T00:00:10Z",
            completed_at: null,
          },
        ],
      },
      error: null,
      loading: false,
    });

    render(<AutoTrainingPage />);

    expect(await screen.findByText("Auto training job-runn")).toBeTruthy();
    expect(screen.getByText("Current step: Training models")).toBeTruthy();
    expect(screen.getByDisplayValue("dataset-1")).toBeTruthy();
  });

  it("starts automatic training for uploaded archives", async () => {
    usePollingMock.mockReturnValue({
      data: {
        archives: [buildArchive()],
        jobs: [],
      },
      error: null,
      loading: false,
    });

    render(<AutoTrainingPage />);
    fireEvent.click(screen.getByRole("button", { name: "Start training" }));

    await waitFor(() => expect(apiMock.startAutoTrainingJob).toHaveBeenCalledWith("token"));
    expect(await screen.findByText("Automatic training started: job-1")).toBeTruthy();
  });
});
