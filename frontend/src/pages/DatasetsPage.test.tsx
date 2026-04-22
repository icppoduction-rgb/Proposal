// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DatasetsPage } from "./DatasetsPage";

const { apiMock, i18nMock, authMock } = vi.hoisted(() => {
  const apiMock = {
    listRawDatasetFiles: vi.fn(),
    createDatasetUploadSession: vi.fn(),
    uploadDatasetChunk: vi.fn(),
    completeDatasetUploadSession: vi.fn(),
    discardDatasetUploadSession: vi.fn(),
    createRawFileEditorSession: vi.fn(),
    getRawFileEditorPage: vi.fn(),
    patchRawFileEditorCells: vi.fn(),
    deleteRawFileEditorRows: vi.fn(),
    deleteRawFileEditorColumns: vi.fn(),
    saveRawFileEditorSession: vi.fn(),
    discardRawFileEditorSession: vi.fn(),
    deleteRawDatasetFile: vi.fn(),
    deleteAllRawDatasetFiles: vi.fn(),
  };

  const translations = {
    "datasets.upload.title": "Upload data",
    "datasets.upload.subtitle": "Load raw files from a local directory into the platform workspace.",
    "datasets.upload.folderLabel": "Dataset folder",
    "datasets.upload.folderPlaceholder": "Choose a local folder with datasets",
    "datasets.upload.selectFolder": "Choose folder",
    "datasets.upload.submit": "Upload datasets",
    "datasets.upload.selectionSummary": "{root} | {count} files | {size}",
    "datasets.upload.progress": "Uploaded {uploaded} of {total} ({percent}%)",
    "datasets.upload.currentFile": "Current file: {file}",
    "datasets.upload.emptyFiles": "The selected folder does not contain supported raw files.",
    "datasets.upload.unsupportedSkipped": "Skipped unsupported files: {count}",
    "datasets.upload.success": "Datasets uploaded: {count}",
    "datasets.upload.folderRequired": "Select a folder before upload",
    "datasets.upload.errors.sessionFileMissing": "Upload session is missing file metadata: {file}",
    "datasets.rawFiles.title": "Uploaded data",
    "datasets.rawFiles.subtitle": "Review uploaded raw files, edit them when needed, and keep them consistent with dataset registrations.",
    "datasets.rawFiles.loading": "Loading uploaded files...",
    "datasets.rawFiles.empty": "No uploaded files yet.",
    "datasets.rawFiles.columns.id": "ID",
    "datasets.rawFiles.columns.name": "Name",
    "datasets.rawFiles.columns.size": "Size",
    "datasets.rawFiles.columns.actions": "Actions",
    "datasets.rawFiles.actions.edit": "Edit",
    "datasets.rawFiles.actions.delete": "Delete",
    "datasets.rawFiles.actions.deleteAll": "Delete all",
    "datasets.rawFiles.messages.deleted": "File deleted: {name}",
    "datasets.rawFiles.messages.deletedAll": "All raw files deleted",
    "datasets.rawFiles.deleteDialog.title": "Delete file",
    "datasets.rawFiles.deleteDialog.description": "Delete file {name}? This action removes the database record and the file from storage.",
    "datasets.rawFiles.deleteDialog.cancel": "Cancel",
    "datasets.rawFiles.deleteDialog.confirm": "Delete",
    "datasets.rawFiles.deleteAllDialog.title": "Delete all files",
    "datasets.rawFiles.deleteAllDialog.description": "Delete all raw files and clear /app/app-data/raw?",
    "datasets.editor.title": "Raw data editor",
    "datasets.editor.readOnly": "This file is preview-only and cannot be saved back.",
    "datasets.editor.loading": "Loading editor data...",
    "datasets.editor.pagination": "Page {page} of {total} | Rows {rows}",
    "datasets.editor.sheetLabel": "Sheet",
    "datasets.editor.deleteRows": "Delete rows ({count})",
    "datasets.editor.deleteColumn": "Delete column",
    "datasets.editor.empty": "No rows available for the current page.",
    "datasets.editor.previous": "Previous",
    "datasets.editor.next": "Next",
    "datasets.editor.cancel": "Cancel",
    "datasets.editor.save": "Save",
    "datasets.editor.messages.saved": "Saved changes for {name}",
    "api.errors.request": "Request failed",
  } as Record<string, string>;

  const i18nMock = {
    t: (key: string, params?: Record<string, string | number>) => {
      const template = translations[key] ?? key;
      return template.replace(/\{(\w+)\}/g, (_, token: string) => String(params?.[token] ?? `{${token}}`));
    },
  };

  const authMock = { tokens: { access_token: "token" }, ensureAccessToken: vi.fn() };

  return { apiMock, i18nMock, authMock };
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

function buildEditorSession(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    session_id: "editor-session-1",
    file_name: "customers.csv",
    file_path: "/app/app-data/raw/uploads/customers.csv",
    dataset_format: "csv",
    read_only: false,
    page_size: 50,
    total_rows: 1,
    total_pages: 1,
    columns: ["name", "value"],
    available_sheets: [],
    active_sheet: null,
    deleted_row_count: 0,
    deleted_columns: [],
    pending_cell_count: 0,
    ...overrides,
  };
}

function buildEditorPage(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    ...buildEditorSession(),
    page: 1,
    rows: [{ row_index: 0, values: { name: "alpha", value: "1" } }],
    ...overrides,
  };
}

vi.mock("../api/client", () => ({
  api: apiMock,
}));

vi.mock("../hooks/useAuth", () => ({
  useAuth: () => authMock,
}));

vi.mock("../i18n", () => ({
  useI18n: () => i18nMock,
}));

describe("DatasetsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authMock.ensureAccessToken.mockResolvedValue("token");

    apiMock.listRawDatasetFiles.mockResolvedValue([buildRawFile()]);
    apiMock.createDatasetUploadSession.mockResolvedValue({
      session_id: "upload-session-1",
      status: "open",
      created_at: "2026-01-01T00:00:00Z",
      total_size_bytes: 64,
      files: [
        {
          file_id: "upload-file-1",
          relative_path: "incoming/customers.csv",
          size_bytes: 64,
          uploaded_bytes: 0,
          content_type: "text/csv",
          status: "pending",
        },
      ],
    });
    apiMock.uploadDatasetChunk.mockImplementation(
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
          session_id: "upload-session-1",
          file_id: "upload-file-1",
          status: "uploaded",
          uploaded_bytes: chunkLength,
          size_bytes: chunkLength,
        };
      },
    );
    apiMock.completeDatasetUploadSession.mockResolvedValue({
      session_id: "upload-session-1",
      status: "completed",
      uploaded_files: [buildRawFile({ id: "raw-file-2", relative_path: "incoming/customers.csv", path: "/app/app-data/raw/incoming/customers.csv" })],
      raw_files: [
        buildRawFile(),
        buildRawFile({
          id: "raw-file-2",
          name: "customers.csv",
          relative_path: "incoming/customers.csv",
          path: "/app/app-data/raw/incoming/customers.csv",
        }),
      ],
    });
    apiMock.discardDatasetUploadSession.mockResolvedValue(undefined);
    apiMock.createRawFileEditorSession.mockResolvedValue(buildEditorSession());
    apiMock.getRawFileEditorPage.mockResolvedValue(buildEditorPage());
    apiMock.patchRawFileEditorCells.mockResolvedValue(buildEditorSession({ pending_cell_count: 1 }));
    apiMock.deleteRawFileEditorRows.mockResolvedValue(buildEditorSession());
    apiMock.deleteRawFileEditorColumns.mockResolvedValue(buildEditorSession({ columns: ["name"] }));
    apiMock.saveRawFileEditorSession.mockResolvedValue({
      session_id: "editor-session-1",
      file_path: "/app/app-data/raw/uploads/customers.csv",
      size_bytes: 144,
      modified_at: "2026-01-01T00:00:00Z",
      row_count: 1,
      column_count: 2,
    });
    apiMock.discardRawFileEditorSession.mockResolvedValue(undefined);
    apiMock.deleteRawDatasetFile.mockResolvedValue({ message: "deleted" });
    apiMock.deleteAllRawDatasetFiles.mockResolvedValue({ message: "deleted" });
  });

  it("uploads a selected folder through session and chunk APIs", async () => {
    const { container } = render(<DatasetsPage />);

    await waitFor(() => expect(apiMock.listRawDatasetFiles).toHaveBeenCalledWith("token"));

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(["entity_id,event_ts,label\n1,2026-01-01,0\n"], "customers.csv", { type: "text/csv" });
    Object.defineProperty(file, "webkitRelativePath", { value: "incoming/customers.csv" });

    fireEvent.change(fileInput, { target: { files: [file] } });
    expect(await screen.findByDisplayValue(`incoming | 1 files | ${file.size} B`)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Upload datasets" }));

    await waitFor(() =>
      expect(apiMock.createDatasetUploadSession).toHaveBeenCalledWith("token", {
        files: [
          {
            relative_path: "incoming/customers.csv",
            size_bytes: file.size,
            content_type: "text/csv",
          },
        ],
      }),
    );
    await waitFor(() => expect(apiMock.uploadDatasetChunk).toHaveBeenCalled());
    await waitFor(() => expect(apiMock.completeDatasetUploadSession).toHaveBeenCalledWith("token", "upload-session-1"));
    expect(await screen.findByText("Datasets uploaded: 1")).toBeTruthy();
  });

  it("accepts res and sc files in the upload selection", async () => {
    apiMock.createDatasetUploadSession.mockResolvedValueOnce({
      session_id: "upload-session-2",
      status: "open",
      created_at: "2026-01-01T00:00:00Z",
      total_size_bytes: 96,
      files: [
        {
          file_id: "upload-file-res",
          relative_path: "incoming/metrics.res",
          size_bytes: 32,
          uploaded_bytes: 0,
          content_type: "text/plain",
          status: "pending",
        },
        {
          file_id: "upload-file-sc",
          relative_path: "incoming/events.sc",
          size_bytes: 64,
          uploaded_bytes: 0,
          content_type: "text/plain",
          status: "pending",
        },
      ],
    });
    apiMock.completeDatasetUploadSession.mockResolvedValueOnce({
      session_id: "upload-session-2",
      status: "completed",
      uploaded_files: [
        buildRawFile({ id: "raw-file-res", name: "metrics.res", relative_path: "incoming/metrics.res", path: "/app/app-data/raw/incoming/metrics.res", format: "res" }),
        buildRawFile({ id: "raw-file-sc", name: "events.sc", relative_path: "incoming/events.sc", path: "/app/app-data/raw/incoming/events.sc", format: "sc" }),
      ],
      raw_files: [
        buildRawFile(),
        buildRawFile({ id: "raw-file-res", name: "metrics.res", relative_path: "incoming/metrics.res", path: "/app/app-data/raw/incoming/metrics.res", format: "res" }),
        buildRawFile({ id: "raw-file-sc", name: "events.sc", relative_path: "incoming/events.sc", path: "/app/app-data/raw/incoming/events.sc", format: "sc" }),
      ],
    });

    const { container } = render(<DatasetsPage />);

    await waitFor(() => expect(apiMock.listRawDatasetFiles).toHaveBeenCalledWith("token"));

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const resFile = new File(["timestamp,cpu_usage\n1631256556.235,0.25\n"], "metrics.res", { type: "text/plain" });
    const scFile = new File(["1631256556434973186 0 30852 apache2 30852 select < res=0 exe=apache2\n"], "events.sc", { type: "text/plain" });
    Object.defineProperty(resFile, "webkitRelativePath", { value: "incoming/metrics.res" });
    Object.defineProperty(scFile, "webkitRelativePath", { value: "incoming/events.sc" });

    fireEvent.change(fileInput, { target: { files: [resFile, scFile] } });
    fireEvent.click(screen.getByRole("button", { name: "Upload datasets" }));

    await waitFor(() =>
      expect(apiMock.createDatasetUploadSession).toHaveBeenCalledWith("token", {
        files: [
          {
            relative_path: "incoming/events.sc",
            size_bytes: scFile.size,
            content_type: "text/plain",
          },
          {
            relative_path: "incoming/metrics.res",
            size_bytes: resFile.size,
            content_type: "text/plain",
          },
        ],
      }),
    );
  });

  it("opens a read-only editor for pcap files", async () => {
    apiMock.listRawDatasetFiles.mockResolvedValueOnce([
      buildRawFile({
        id: "raw-file-pcap",
        name: "traffic.pcap",
        path: "/app/app-data/raw/uploads/traffic.pcap",
        relative_path: "uploads/traffic.pcap",
        format: "pcap",
      }),
    ]);
    apiMock.createRawFileEditorSession.mockResolvedValueOnce(
      buildEditorSession({
        session_id: "editor-session-pcap",
        file_name: "traffic.pcap",
        file_path: "/app/app-data/raw/uploads/traffic.pcap",
        dataset_format: "pcap",
        read_only: true,
        columns: ["query", "answer"],
      }),
    );
    apiMock.getRawFileEditorPage.mockResolvedValueOnce(
      buildEditorPage({
        session_id: "editor-session-pcap",
        file_name: "traffic.pcap",
        file_path: "/app/app-data/raw/uploads/traffic.pcap",
        dataset_format: "pcap",
        read_only: true,
        columns: ["query", "answer"],
        rows: [{ row_index: 0, values: { query: "example.org", answer: "1.1.1.1" } }],
      }),
    );

    render(<DatasetsPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Edit" }));

    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("This file is preview-only and cannot be saved back.")).toBeTruthy();
    expect(within(dialog).queryByRole("button", { name: "Save" })).toBeNull();
  });

  it("saves edited CSV data through the editor session API", async () => {
    render(<DatasetsPage />);

    fireEvent.click(await screen.findByRole("button", { name: "Edit" }));

    const dialog = await screen.findByRole("dialog");
    const cellInput = within(dialog).getByDisplayValue("alpha");
    fireEvent.change(cellInput, { target: { value: "bravo" } });
    fireEvent.click(within(dialog).getByRole("button", { name: "Save" }));

    await waitFor(() =>
      expect(apiMock.patchRawFileEditorCells).toHaveBeenCalledWith("token", "raw-file-1", "editor-session-1", {
        patches: [{ row_index: 0, column: "name", value: "bravo" }],
      }),
    );
    await waitFor(() => expect(apiMock.saveRawFileEditorSession).toHaveBeenCalledWith("token", "raw-file-1", "editor-session-1"));
    expect(await screen.findByText("Saved changes for customers.csv")).toBeTruthy();
  });

  it("deletes a single raw file from the uploaded data table", async () => {
    render(<DatasetsPage />);

    const rawFileRow = (await screen.findByText("customers.csv")).closest("tr") as HTMLElement;
    fireEvent.click(within(rawFileRow).getByRole("button", { name: "Delete" }));

    const dialog = await screen.findByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete" }));

    await waitFor(() => expect(apiMock.deleteRawDatasetFile).toHaveBeenCalledWith("token", "raw-file-1"));
    expect(await screen.findByText("File deleted: customers.csv")).toBeTruthy();
  });
});
