import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  LinearProgress,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { ChangeEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../i18n";
import type { EditorPage, RawFile } from "../types/api";

const DEFAULT_EDITOR_PAGE_SIZE = 50;
const UPLOAD_CHUNK_SIZE_BYTES = 5 * 1024 * 1024;
const SUPPORTED_UPLOAD_EXTENSIONS = new Set(["csv", "tsv", "parquet", "xlsx", "json", "pcap", "res", "sc"]);

type RawFileDeleteDialogState =
  | { mode: "single"; rawFile: RawFile }
  | { mode: "all" }
  | null;

type PendingPatch = {
  row_index: number;
  column: string;
  value: unknown;
};

type SelectedUploadFile = {
  file: File;
  relativePath: string;
  sizeBytes: number;
  contentType: string | null;
};

function formatBytes(value: number): string {
  if (value === 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB", "TB"];
  let size = value;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size.toFixed(size >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

function patchKey(rowIndex: number, column: string): string {
  return `${rowIndex}:${column}`;
}

function toEditableValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  return String(value);
}

function normalizeUploadRelativePath(file: File): string {
  const webkitRelativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath;
  const value = webkitRelativePath && webkitRelativePath.trim().length > 0 ? webkitRelativePath : file.name;
  return value.replace(/\\/g, "/").replace(/^\/+/, "");
}

function isSupportedUploadPath(relativePath: string): boolean {
  const extension = relativePath.split(".").pop()?.toLowerCase() ?? "";
  return SUPPORTED_UPLOAD_EXTENSIONS.has(extension);
}

function getSelectionRoot(files: SelectedUploadFile[]): string {
  if (files.length === 0) {
    return "";
  }
  const firstSegment = files[0].relativePath.split("/")[0];
  return firstSegment || files[0].relativePath;
}

export function DatasetsPage() {
  const { tokens, ensureAccessToken } = useAuth();
  const { t } = useI18n();

  const uploadInputRef = useRef<HTMLInputElement | null>(null);

  const [selectedFiles, setSelectedFiles] = useState<SelectedUploadFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgressBytes, setUploadProgressBytes] = useState(0);
  const [uploadTotalBytes, setUploadTotalBytes] = useState(0);
  const [currentUploadFile, setCurrentUploadFile] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [uploadWarning, setUploadWarning] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [rawFilesMessage, setRawFilesMessage] = useState<string | null>(null);
  const [rawFilesError, setRawFilesError] = useState<string | null>(null);
  const [rawFilesLoading, setRawFilesLoading] = useState(false);
  const [rawFiles, setRawFiles] = useState<RawFile[]>([]);
  const [rawFileDeleteDialog, setRawFileDeleteDialog] = useState<RawFileDeleteDialogState>(null);
  const [rawFileDeleteLoading, setRawFileDeleteLoading] = useState(false);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editorLoading, setEditorLoading] = useState(false);
  const [editorSaving, setEditorSaving] = useState(false);
  const [editorError, setEditorError] = useState<string | null>(null);
  const [editorRawFile, setEditorRawFile] = useState<RawFile | null>(null);
  const [editorSessionId, setEditorSessionId] = useState<string | null>(null);
  const [editorPage, setEditorPage] = useState<EditorPage | null>(null);
  const [selectedRowIndices, setSelectedRowIndices] = useState<number[]>([]);
  const [pendingPatches, setPendingPatches] = useState<Record<string, PendingPatch>>({});

  const supportsDirectoryUpload = useMemo(() => {
    if (typeof document === "undefined") {
      return false;
    }
    const input = document.createElement("input") as HTMLInputElement & Record<string, unknown>;
    return "webkitdirectory" in input || "directory" in input;
  }, []);

  useEffect(() => {
    const input = uploadInputRef.current;
    if (!input) {
      return;
    }
    input.setAttribute("webkitdirectory", "");
    input.setAttribute("directory", "");
    input.setAttribute("multiple", "");
  }, []);

  const getAccessToken = useCallback(
    async (minRemainingSeconds = 120) => {
      if (!tokens) {
        return null;
      }
      return (await ensureAccessToken(minRemainingSeconds)) ?? tokens.access_token;
    },
    [ensureAccessToken, tokens],
  );

  const loadRawFiles = useCallback(async () => {
    const accessToken = await getAccessToken(90);
    if (!accessToken) {
      setRawFiles([]);
      return;
    }

    setRawFilesLoading(true);
    try {
      setRawFiles(await api.listRawDatasetFiles(accessToken));
      setRawFilesError(null);
    } catch (error) {
      setRawFilesError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setRawFilesLoading(false);
    }
  }, [getAccessToken, t]);

  useEffect(() => {
    void loadRawFiles();
  }, [loadRawFiles]);

  const resetEditorState = useCallback(() => {
    setEditorOpen(false);
    setEditorLoading(false);
    setEditorSaving(false);
    setEditorError(null);
    setEditorRawFile(null);
    setEditorSessionId(null);
    setEditorPage(null);
    setSelectedRowIndices([]);
    setPendingPatches({});
  }, []);

  const flushPendingPatches = useCallback(async () => {
    if (!tokens || !editorRawFile || !editorSessionId) {
      return;
    }

    const patches = Object.values(pendingPatches);
    if (patches.length === 0) {
      return;
    }

    await api.patchRawFileEditorCells(tokens.access_token, editorRawFile.id, editorSessionId, {
      patches: patches.map((item) => ({
        row_index: item.row_index,
        column: item.column,
        value: item.value,
      })),
    });
    setPendingPatches({});
  }, [editorRawFile, editorSessionId, pendingPatches, tokens]);

  const loadEditorPage = useCallback(
    async (targetPage: number, sheetName?: string | null) => {
      if (!tokens || !editorRawFile || !editorSessionId) {
        return;
      }

      setEditorLoading(true);
      setEditorError(null);
      try {
        await flushPendingPatches();
        const page = await api.getRawFileEditorPage(tokens.access_token, editorRawFile.id, editorSessionId, {
          page: targetPage,
          sheet_name: sheetName,
        });
        setEditorPage(page);
        setSelectedRowIndices([]);
      } catch (error) {
        setEditorError(error instanceof Error ? error.message : t("api.errors.request"));
      } finally {
        setEditorLoading(false);
      }
    },
    [editorRawFile, editorSessionId, flushPendingPatches, t, tokens],
  );

  const closeEditor = useCallback(async () => {
    if (tokens && editorRawFile && editorSessionId) {
      try {
        await api.discardRawFileEditorSession(tokens.access_token, editorRawFile.id, editorSessionId);
      } catch {
        // ignore discard errors on close
      }
    }
    resetEditorState();
  }, [editorRawFile, editorSessionId, resetEditorState, tokens]);

  const openEditor = async (rawFile: RawFile) => {
    if (!tokens) {
      return;
    }

    setEditorOpen(true);
    setEditorRawFile(rawFile);
    setEditorLoading(true);
    setEditorError(null);
    setSelectedRowIndices([]);
    setPendingPatches({});

    try {
      const created = await api.createRawFileEditorSession(tokens.access_token, rawFile.id, { page_size: DEFAULT_EDITOR_PAGE_SIZE });
      setEditorSessionId(created.session_id);
      const page = await api.getRawFileEditorPage(tokens.access_token, rawFile.id, created.session_id, { page: 1 });
      setEditorPage(page);
    } catch (error) {
      setEditorError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setEditorLoading(false);
    }
  };

  const handleSelectedFilesChange = (event: ChangeEvent<HTMLInputElement>) => {
    const browserFiles = Array.from(event.target.files ?? []);
    const normalizedFiles = browserFiles
      .map((file) => ({
        file,
        relativePath: normalizeUploadRelativePath(file),
        sizeBytes: file.size,
        contentType: file.type || null,
      }))
      .sort((left, right) => left.relativePath.localeCompare(right.relativePath));

    const supportedFiles = normalizedFiles.filter((item) => isSupportedUploadPath(item.relativePath));
    const skippedFiles = normalizedFiles.length - supportedFiles.length;
    const totalSizeBytes = supportedFiles.reduce((sum, item) => sum + item.sizeBytes, 0);

    setSelectedFiles(supportedFiles);
    setUploadProgressBytes(0);
    setUploadTotalBytes(totalSizeBytes);
    setCurrentUploadFile(null);
    setUploadMessage(null);
    setUploadError(supportedFiles.length === 0 ? t("datasets.upload.emptyFiles") : null);
    setUploadWarning(skippedFiles > 0 ? t("datasets.upload.unsupportedSkipped", { count: skippedFiles }) : null);

    event.target.value = "";
  };

  const chooseFolder = () => {
    setUploadError(null);
    setUploadMessage(null);
    if (!supportsDirectoryUpload) {
      setUploadError(t("datasets.upload.directoryPickerUnsupported"));
      return;
    }
    uploadInputRef.current?.click();
  };

  const uploadSelectedFiles = async () => {
    if (selectedFiles.length === 0) {
      setUploadError(t("datasets.upload.folderRequired"));
      return;
    }

    const totalSizeBytes = selectedFiles.reduce((sum, item) => sum + item.sizeBytes, 0);
    let uploadSessionId: string | null = null;

    setUploading(true);
    setUploadError(null);
    setUploadMessage(null);
    setUploadProgressBytes(0);
    setUploadTotalBytes(totalSizeBytes);
    setCurrentUploadFile(null);

    try {
      const sessionToken = await getAccessToken(180);
      if (!sessionToken) {
        throw new Error(t("api.errors.unauthorized"));
      }

      const session = await api.createDatasetUploadSession(sessionToken, {
        files: selectedFiles.map((item) => ({
          relative_path: item.relativePath,
          size_bytes: item.sizeBytes,
          content_type: item.contentType,
        })),
      });
      uploadSessionId = session.session_id;

      const filesByRelativePath = new Map(session.files.map((item) => [item.relative_path, item]));
      let uploadedBytesBase = 0;

      for (const selectedFile of selectedFiles) {
        const sessionFile = filesByRelativePath.get(selectedFile.relativePath);
        if (!sessionFile) {
          throw new Error(t("datasets.upload.errors.sessionFileMissing", { file: selectedFile.relativePath }));
        }

        setCurrentUploadFile(selectedFile.relativePath);
        let offset = 0;
        while (offset < selectedFile.sizeBytes) {
          const chunk = selectedFile.file.slice(offset, offset + UPLOAD_CHUNK_SIZE_BYTES);
          const chunkLength = chunk.size;
          const chunkToken = await getAccessToken(180);
          if (!chunkToken) {
            throw new Error(t("api.errors.unauthorized"));
          }
          await api.uploadDatasetChunk(
            chunkToken,
            session.session_id,
            sessionFile.file_id,
            chunk,
            offset,
            chunkLength,
            (loadedBytes) => {
              setUploadProgressBytes(Math.min(uploadedBytesBase + offset + loadedBytes, totalSizeBytes));
            },
          );
          offset += chunkLength;
          setUploadProgressBytes(Math.min(uploadedBytesBase + offset, totalSizeBytes));
        }
        uploadedBytesBase += selectedFile.sizeBytes;
        setUploadProgressBytes(Math.min(uploadedBytesBase, totalSizeBytes));
      }

      const completionToken = await getAccessToken(180);
      if (!completionToken) {
        throw new Error(t("api.errors.unauthorized"));
      }
      const completed = await api.completeDatasetUploadSession(completionToken, session.session_id);
      setRawFiles(completed.raw_files);
      setRawFilesError(null);
      setUploadProgressBytes(totalSizeBytes);
      setUploadMessage(t("datasets.upload.success", { count: completed.uploaded_files.length }));
      setSelectedFiles([]);
      setUploadWarning(null);
      setCurrentUploadFile(null);
    } catch (error) {
      if (uploadSessionId) {
        try {
          const cleanupToken = await getAccessToken(0);
          if (cleanupToken) {
            await api.discardDatasetUploadSession(cleanupToken, uploadSessionId);
          }
        } catch {
          // ignore cleanup failures
        }
      }
      setUploadError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setUploading(false);
    }
  };

  const onDeleteRawFile = async () => {
    if (!rawFileDeleteDialog) {
      return;
    }

    setRawFileDeleteLoading(true);
    setRawFilesError(null);
    setRawFilesMessage(null);

    try {
      const accessToken = await getAccessToken(90);
      if (!accessToken) {
        throw new Error(t("api.errors.unauthorized"));
      }
      if (rawFileDeleteDialog.mode === "single") {
        await api.deleteRawDatasetFile(accessToken, rawFileDeleteDialog.rawFile.id);
        setRawFilesMessage(t("datasets.rawFiles.messages.deleted", { name: rawFileDeleteDialog.rawFile.name }));
      } else {
        await api.deleteAllRawDatasetFiles(accessToken);
        setRawFilesMessage(t("datasets.rawFiles.messages.deletedAll"));
      }

      setRawFileDeleteDialog(null);
      await loadRawFiles();
    } catch (error) {
      setRawFilesError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setRawFileDeleteLoading(false);
    }
  };

  const toggleRowSelection = (rowIndex: number, checked: boolean) => {
    setSelectedRowIndices((current) => {
      if (checked) {
        return Array.from(new Set([...current, rowIndex]));
      }
      return current.filter((item) => item !== rowIndex);
    });
  };

  const updateEditorCell = (rowIndex: number, column: string, value: string) => {
    setEditorPage((current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        rows: current.rows.map((row) =>
          row.row_index === rowIndex
            ? { ...row, values: { ...row.values, [column]: value } }
            : row,
        ),
      };
    });
    setPendingPatches((current) => ({
      ...current,
      [patchKey(rowIndex, column)]: { row_index: rowIndex, column, value },
    }));
  };

  const deleteSelectedRows = async () => {
    if (!tokens || !editorRawFile || !editorSessionId || selectedRowIndices.length === 0) {
      return;
    }

    setEditorLoading(true);
    setEditorError(null);
    try {
      await flushPendingPatches();
      const updated = await api.deleteRawFileEditorRows(tokens.access_token, editorRawFile.id, editorSessionId, {
        row_indices: selectedRowIndices,
      });
      const targetPage = Math.min(editorPage?.page ?? 1, updated.total_pages || 1);
      const nextPage = await api.getRawFileEditorPage(tokens.access_token, editorRawFile.id, editorSessionId, {
        page: targetPage,
      });
      setEditorPage(nextPage);
      setSelectedRowIndices([]);
    } catch (error) {
      setEditorError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setEditorLoading(false);
    }
  };

  const deleteColumn = async (column: string) => {
    if (!tokens || !editorRawFile || !editorSessionId) {
      return;
    }

    setEditorLoading(true);
    setEditorError(null);
    try {
      await flushPendingPatches();
      await api.deleteRawFileEditorColumns(tokens.access_token, editorRawFile.id, editorSessionId, { columns: [column] });
      const nextPage = await api.getRawFileEditorPage(tokens.access_token, editorRawFile.id, editorSessionId, {
        page: editorPage?.page ?? 1,
      });
      setEditorPage(nextPage);
    } catch (error) {
      setEditorError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setEditorLoading(false);
    }
  };

  const saveEditorChanges = async () => {
    if (!tokens || !editorRawFile || !editorSessionId) {
      return;
    }

    setEditorSaving(true);
    setEditorError(null);
    setRawFilesMessage(null);
    setRawFilesError(null);

    try {
      await flushPendingPatches();
      await api.saveRawFileEditorSession(tokens.access_token, editorRawFile.id, editorSessionId);
      setRawFilesMessage(t("datasets.editor.messages.saved", { name: editorRawFile.name }));
      await loadRawFiles();
      resetEditorState();
    } catch (error) {
      setEditorError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setEditorSaving(false);
    }
  };

  const uploadPercent = useMemo(() => {
    if (uploadTotalBytes <= 0) {
      return 0;
    }
    return Math.min(100, Math.round((uploadProgressBytes / uploadTotalBytes) * 100));
  }, [uploadProgressBytes, uploadTotalBytes]);

  const selectionSummary = useMemo(() => {
    if (selectedFiles.length === 0) {
      return "";
    }
    return t("datasets.upload.selectionSummary", {
      root: getSelectionRoot(selectedFiles),
      count: selectedFiles.length,
      size: formatBytes(uploadTotalBytes),
    });
  }, [selectedFiles, t, uploadTotalBytes]);

  const editorTotalPages = editorPage?.total_pages ?? 0;
  const editorCurrentPage = editorPage?.page ?? 1;

  return (
    <Stack spacing={3} sx={{ width: "100%" }}>
      <input ref={uploadInputRef} type="file" hidden multiple onChange={handleSelectedFilesChange} />

      <SectionCard title={t("datasets.upload.title")} subtitle={t("datasets.upload.subtitle")}>
        <Stack spacing={1.4}>
          {uploadMessage ? <Alert severity="success">{uploadMessage}</Alert> : null}
          {uploadWarning ? <Alert severity="warning">{uploadWarning}</Alert> : null}
          {uploadError ? <Alert severity="error">{uploadError}</Alert> : null}

          <TextField
            label={t("datasets.upload.folderLabel")}
            value={selectionSummary}
            placeholder={t("datasets.upload.folderPlaceholder")}
            InputProps={{ readOnly: true }}
            fullWidth
          />

          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.2}>
            <Button variant="outlined" onClick={chooseFolder} disabled={uploading}>
              {t("datasets.upload.selectFolder")}
            </Button>
            <Button variant="contained" onClick={() => void uploadSelectedFiles()} disabled={uploading || selectedFiles.length === 0}>
              {uploading ? <CircularProgress color="inherit" size={18} /> : t("datasets.upload.submit")}
            </Button>
          </Stack>

          {uploadTotalBytes > 0 ? (
            <Stack spacing={0.8}>
              <LinearProgress variant="determinate" value={uploadPercent} />
              <Typography variant="body2" color="text.secondary">
                {t("datasets.upload.progress", {
                  uploaded: formatBytes(uploadProgressBytes),
                  total: formatBytes(uploadTotalBytes),
                  percent: uploadPercent,
                })}
              </Typography>
              {currentUploadFile ? (
                <Typography variant="body2" color="text.secondary">
                  {t("datasets.upload.currentFile", { file: currentUploadFile })}
                </Typography>
              ) : null}
            </Stack>
          ) : null}
        </Stack>
      </SectionCard>

      <SectionCard
        title={t("datasets.rawFiles.title")}
        subtitle={t("datasets.rawFiles.subtitle")}
        headerAction={
          <Button
            color="error"
            variant="outlined"
            onClick={() => setRawFileDeleteDialog({ mode: "all" })}
            disabled={rawFilesLoading || rawFiles.length === 0}
          >
            {t("datasets.rawFiles.actions.deleteAll")}
          </Button>
        }
      >
        <Stack spacing={1.2}>
          {rawFilesMessage ? <Alert severity="success">{rawFilesMessage}</Alert> : null}
          {rawFilesError ? <Alert severity="error">{rawFilesError}</Alert> : null}
          {rawFilesLoading ? (
            <Stack direction="row" spacing={1.2} alignItems="center">
              <CircularProgress size={18} />
              <Typography variant="body2" color="text.secondary">
                {t("datasets.rawFiles.loading")}
              </Typography>
            </Stack>
          ) : null}
          <TableContainer
            sx={{
              borderRadius: 3,
              border: (theme) => `1px solid ${theme.palette.divider}`,
              maxHeight: rawFiles.length > 15 ? 560 : undefined,
              overflowY: rawFiles.length > 15 ? "auto" : "visible",
            }}
          >
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t("datasets.rawFiles.columns.id")}</TableCell>
                  <TableCell>{t("datasets.rawFiles.columns.name")}</TableCell>
                  <TableCell>{t("datasets.rawFiles.columns.size")}</TableCell>
                  <TableCell align="right">{t("datasets.rawFiles.columns.actions")}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rawFiles.length > 0 ? (
                  rawFiles.map((rawFile) => (
                    <TableRow key={rawFile.id} hover>
                      <TableCell>{rawFile.id}</TableCell>
                      <TableCell>
                        <Stack spacing={0.2}>
                          <Typography variant="body2">{rawFile.name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {rawFile.relative_path}
                          </Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>{formatBytes(rawFile.size)}</TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                          <Button size="small" variant="outlined" onClick={() => void openEditor(rawFile)}>
                            {t("datasets.rawFiles.actions.edit")}
                          </Button>
                          <Button
                            size="small"
                            color="error"
                            variant="outlined"
                            onClick={() => setRawFileDeleteDialog({ mode: "single", rawFile })}
                          >
                            {t("datasets.rawFiles.actions.delete")}
                          </Button>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={4}>
                      <Box sx={{ py: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          {t("datasets.rawFiles.empty")}
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Stack>
      </SectionCard>

      <Dialog open={editorOpen} onClose={() => void closeEditor()} fullWidth maxWidth="xl">
        <DialogTitle>{t("datasets.editor.title")}</DialogTitle>
        <DialogContent sx={{ display: "grid", gap: 1.5 }}>
          {editorError ? <Alert severity="error">{editorError}</Alert> : null}
          {editorPage?.read_only ? <Alert severity="info">{t("datasets.editor.readOnly")}</Alert> : null}
          {editorLoading ? (
            <Stack direction="row" spacing={1.2} alignItems="center">
              <CircularProgress size={18} />
              <Typography variant="body2" color="text.secondary">
                {t("datasets.editor.loading")}
              </Typography>
            </Stack>
          ) : null}

          {editorPage ? (
            <Stack spacing={1.2}>
              <Stack direction={{ xs: "column", md: "row" }} spacing={1} alignItems={{ xs: "stretch", md: "center" }}>
                <Typography variant="body2" color="text.secondary" sx={{ flexGrow: 1 }}>
                  {t("datasets.editor.pagination", {
                    page: editorCurrentPage,
                    total: Math.max(editorTotalPages, 1),
                    rows: editorPage.total_rows,
                  })}
                </Typography>
                {editorPage.available_sheets.length > 0 ? (
                  <TextField
                    select
                    size="small"
                    label={t("datasets.editor.sheetLabel")}
                    value={editorPage.active_sheet ?? ""}
                    onChange={(event) => {
                      void loadEditorPage(1, event.target.value);
                    }}
                    sx={{ minWidth: 220 }}
                  >
                    {editorPage.available_sheets.map((sheet) => (
                      <MenuItem key={sheet} value={sheet}>
                        {sheet}
                      </MenuItem>
                    ))}
                  </TextField>
                ) : null}
                {!editorPage.read_only ? (
                  <Button
                    variant="outlined"
                    color="error"
                    disabled={selectedRowIndices.length === 0 || editorLoading}
                    onClick={() => void deleteSelectedRows()}
                  >
                    {t("datasets.editor.deleteRows", { count: selectedRowIndices.length })}
                  </Button>
                ) : null}
              </Stack>

              <TableContainer
                sx={{
                  borderRadius: 3,
                  border: (theme) => `1px solid ${theme.palette.divider}`,
                  maxHeight: 520,
                  overflowY: "auto",
                  overflowX: "auto",
                }}
              >
                <Table stickyHeader size="small" sx={{ minWidth: 960 }}>
                  <TableHead>
                    <TableRow>
                      {!editorPage.read_only ? <TableCell padding="checkbox" /> : null}
                      {editorPage.columns.map((column) => (
                        <TableCell key={column}>
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Typography variant="body2">{column}</Typography>
                            {!editorPage.read_only && editorPage.columns.length > 1 ? (
                              <Button size="small" color="error" variant="text" onClick={() => void deleteColumn(column)}>
                                {t("datasets.editor.deleteColumn")}
                              </Button>
                            ) : null}
                          </Stack>
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {editorPage.rows.length > 0 ? (
                      editorPage.rows.map((row) => (
                        <TableRow key={row.row_index} hover>
                          {!editorPage.read_only ? (
                            <TableCell padding="checkbox">
                              <Checkbox
                                checked={selectedRowIndices.includes(row.row_index)}
                                onChange={(event) => toggleRowSelection(row.row_index, event.target.checked)}
                              />
                            </TableCell>
                          ) : null}
                          {editorPage.columns.map((column) => (
                            <TableCell key={`${row.row_index}-${column}`} sx={{ minWidth: 180, verticalAlign: "top" }}>
                              {editorPage.read_only ? (
                                <Typography variant="body2">{toEditableValue(row.values[column])}</Typography>
                              ) : (
                                <TextField
                                  size="small"
                                  fullWidth
                                  value={toEditableValue(row.values[column])}
                                  onChange={(event) => updateEditorCell(row.row_index, column, event.target.value)}
                                />
                              )}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={editorPage.columns.length + (editorPage.read_only ? 0 : 1)}>
                          <Box sx={{ py: 2 }}>
                            <Typography variant="body2" color="text.secondary">
                              {t("datasets.editor.empty")}
                            </Typography>
                          </Box>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              <Stack direction="row" spacing={1} justifyContent="space-between">
                <Button variant="outlined" disabled={editorCurrentPage <= 1 || editorLoading} onClick={() => void loadEditorPage(editorCurrentPage - 1)}>
                  {t("datasets.editor.previous")}
                </Button>
                <Button
                  variant="outlined"
                  disabled={editorCurrentPage >= Math.max(editorTotalPages, 1) || editorLoading || editorTotalPages === 0}
                  onClick={() => void loadEditorPage(editorCurrentPage + 1)}
                >
                  {t("datasets.editor.next")}
                </Button>
              </Stack>
            </Stack>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => void closeEditor()} disabled={editorSaving}>
            {t("datasets.editor.cancel")}
          </Button>
          {!editorPage?.read_only ? (
            <Button variant="contained" onClick={() => void saveEditorChanges()} disabled={editorSaving || editorLoading || !editorPage}>
              {editorSaving ? <CircularProgress color="inherit" size={18} /> : t("datasets.editor.save")}
            </Button>
          ) : null}
        </DialogActions>
      </Dialog>

      <Dialog
        open={Boolean(rawFileDeleteDialog)}
        onClose={() => (rawFileDeleteLoading ? undefined : setRawFileDeleteDialog(null))}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle>
          {rawFileDeleteDialog?.mode === "all" ? t("datasets.rawFiles.deleteAllDialog.title") : t("datasets.rawFiles.deleteDialog.title")}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {rawFileDeleteDialog?.mode === "all"
              ? t("datasets.rawFiles.deleteAllDialog.description")
              : t("datasets.rawFiles.deleteDialog.description", {
                  name: rawFileDeleteDialog?.mode === "single" ? rawFileDeleteDialog.rawFile.name : "",
                })}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRawFileDeleteDialog(null)} disabled={rawFileDeleteLoading}>
            {t("datasets.rawFiles.deleteDialog.cancel")}
          </Button>
          <Button color="error" variant="contained" onClick={() => void onDeleteRawFile()} disabled={rawFileDeleteLoading}>
            {rawFileDeleteLoading ? <CircularProgress color="inherit" size={18} /> : t("datasets.rawFiles.deleteDialog.confirm")}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
