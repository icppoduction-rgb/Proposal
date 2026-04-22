import {
  Alert,
  Box,
  Button,
  Chip,
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
import { formActionSx, formStackSx, noWrapSx, tableShellSx } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { usePolling } from "../hooks/usePolling";
import { useI18n } from "../i18n";
import type { ArchiveFile, AutoTrainingJob, UploadSession } from "../types/api";

const UPLOAD_CHUNK_SIZE_BYTES = 5 * 1024 * 1024;
const SUPPORTED_ARCHIVE_SUFFIXES = [".tar.gz", ".tar.bz2", ".tar.xz", ".tgz", ".tbz2", ".txz", ".zip", ".tar", ".gz", ".bz2", ".xz"];

type ArchiveDeleteDialogState =
  | { mode: "single"; archive: ArchiveFile }
  | { mode: "all" }
  | null;

type SelectedArchiveFile = {
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

function formatDateTime(value?: string | null): string {
  if (!value) {
    return "n/a";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function normalizeUploadRelativePath(file: File): string {
  const webkitRelativePath = (file as File & { webkitRelativePath?: string }).webkitRelativePath;
  const value = webkitRelativePath && webkitRelativePath.trim().length > 0 ? webkitRelativePath : file.name;
  return value.replace(/\\/g, "/").replace(/^\/+/, "");
}

function isSupportedArchivePath(relativePath: string): boolean {
  const lowered = relativePath.toLowerCase();
  return SUPPORTED_ARCHIVE_SUFFIXES.some((suffix) => lowered.endsWith(suffix));
}

function getSelectionRoot(files: SelectedArchiveFile[]): string {
  if (files.length === 0) {
    return "";
  }
  const firstSegment = files[0].relativePath.split("/")[0];
  return firstSegment || files[0].relativePath;
}

function jobRunning(job: AutoTrainingJob): boolean {
  return job.status === "pending" || job.status === "running";
}

export function AutoTrainingPage() {
  const { tokens, ensureAccessToken } = useAuth();
  const { t, tEnum } = useI18n();
  const uploadInputRef = useRef<HTMLInputElement | null>(null);

  const [reloadNonce, setReloadNonce] = useState(0);
  const [selectedFiles, setSelectedFiles] = useState<SelectedArchiveFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgressBytes, setUploadProgressBytes] = useState(0);
  const [uploadTotalBytes, setUploadTotalBytes] = useState(0);
  const [currentUploadFile, setCurrentUploadFile] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [uploadWarning, setUploadWarning] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [archiveDeleteDialog, setArchiveDeleteDialog] = useState<ArchiveDeleteDialogState>(null);
  const [archiveDeleteLoading, setArchiveDeleteLoading] = useState(false);
  const [startTrainingLoading, setStartTrainingLoading] = useState(false);

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

  const loader = useCallback(async () => {
    const accessToken = await getAccessToken(90);
    if (!accessToken) {
      return { archives: [], jobs: [] };
    }
    const [archives, jobs] = await Promise.all([
      api.listAutoTrainingArchives(accessToken),
      api.listAutoTrainingJobs(accessToken),
    ]);
    return { archives, jobs };
  }, [getAccessToken, reloadNonce]);

  const { data, error, loading } = usePolling(loader);
  const archives = data?.archives ?? [];
  const jobs = data?.jobs ?? [];
  const hasActiveJob = jobs.some(jobRunning);

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

    const supportedFiles = normalizedFiles.filter((item) => isSupportedArchivePath(item.relativePath));
    const skippedFiles = normalizedFiles.length - supportedFiles.length;
    const totalSizeBytes = supportedFiles.reduce((sum, item) => sum + item.sizeBytes, 0);

    setSelectedFiles(supportedFiles);
    setUploadProgressBytes(0);
    setUploadTotalBytes(totalSizeBytes);
    setCurrentUploadFile(null);
    setUploadMessage(null);
    setUploadError(supportedFiles.length === 0 ? t("autoTraining.upload.emptyFiles") : null);
    setUploadWarning(skippedFiles > 0 ? t("autoTraining.upload.unsupportedSkipped", { count: skippedFiles }) : null);
    event.target.value = "";
  };

  const chooseFolder = () => {
    setUploadError(null);
    setUploadMessage(null);
    if (!supportsDirectoryUpload) {
      setUploadError(t("autoTraining.upload.directoryPickerUnsupported"));
      return;
    }
    uploadInputRef.current?.click();
  };

  const uploadSelectedFiles = async () => {
    if (selectedFiles.length === 0) {
      setUploadError(t("autoTraining.upload.folderRequired"));
      return;
    }

    let uploadSessionId: string | null = null;
    const totalSizeBytes = selectedFiles.reduce((sum, item) => sum + item.sizeBytes, 0);

    setUploading(true);
    setUploadError(null);
    setUploadMessage(null);
    setUploadProgressBytes(0);
    setUploadTotalBytes(totalSizeBytes);

    try {
      const sessionToken = await getAccessToken(180);
      if (!sessionToken) {
        throw new Error(t("api.errors.unauthorized"));
      }

      const session = await api.createAutoTrainingUploadSession(sessionToken, {
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
          throw new Error(t("autoTraining.upload.errors.sessionFileMissing", { file: selectedFile.relativePath }));
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
          await api.uploadAutoTrainingArchiveChunk(
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
      await api.completeAutoTrainingUploadSession(completionToken, session.session_id);
      setSelectedFiles([]);
      setUploadWarning(null);
      setCurrentUploadFile(null);
      setUploadProgressBytes(totalSizeBytes);
      setUploadMessage(t("autoTraining.upload.success", { count: selectedFiles.length }));
      setReloadNonce((current) => current + 1);
    } catch (error) {
      if (uploadSessionId) {
        try {
          const cleanupToken = await getAccessToken(0);
          if (cleanupToken) {
            await api.discardAutoTrainingUploadSession(cleanupToken, uploadSessionId);
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

  const onDeleteArchive = async () => {
    if (!archiveDeleteDialog) {
      return;
    }
    setArchiveDeleteLoading(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const accessToken = await getAccessToken(90);
      if (!accessToken) {
        throw new Error(t("api.errors.unauthorized"));
      }
      if (archiveDeleteDialog.mode === "single") {
        await api.deleteAutoTrainingArchive(accessToken, archiveDeleteDialog.archive.id);
        setActionMessage(t("autoTraining.archives.messages.deleted", { name: archiveDeleteDialog.archive.name }));
      } else {
        await api.deleteAllAutoTrainingArchives(accessToken);
        setActionMessage(t("autoTraining.archives.messages.deletedAll"));
      }
      setArchiveDeleteDialog(null);
      setReloadNonce((current) => current + 1);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setArchiveDeleteLoading(false);
    }
  };

  const onStartTraining = async () => {
    setStartTrainingLoading(true);
    setActionMessage(null);
    setActionError(null);
    try {
      const accessToken = await getAccessToken(90);
      if (!accessToken) {
        throw new Error(t("api.errors.unauthorized"));
      }
      const job = await api.startAutoTrainingJob(accessToken);
      setActionMessage(t("autoTraining.jobs.messages.started", { id: job.id }));
      setReloadNonce((current) => current + 1);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setStartTrainingLoading(false);
    }
  };

  return (
    <Stack spacing={3} sx={{ width: "100%" }}>
      <SectionCard title={t("autoTraining.upload.title")} subtitle={t("autoTraining.upload.subtitle")}>
        <Stack sx={formStackSx}>
          {uploadMessage ? <Alert severity="success">{uploadMessage}</Alert> : null}
          {uploadWarning ? <Alert severity="warning">{uploadWarning}</Alert> : null}
          {uploadError ? <Alert severity="error">{uploadError}</Alert> : null}

          <input ref={uploadInputRef} type="file" hidden onChange={handleSelectedFilesChange} />
          <TextField
            label={t("autoTraining.upload.folderLabel")}
            value={
              selectedFiles.length > 0
                ? t("autoTraining.upload.selectionSummary", {
                    root: getSelectionRoot(selectedFiles),
                    count: selectedFiles.length,
                    size: formatBytes(uploadTotalBytes),
                  })
                : ""
            }
            placeholder={t("autoTraining.upload.folderPlaceholder")}
            InputProps={{ readOnly: true }}
          />

          <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
            <Button variant="outlined" onClick={chooseFolder} disabled={uploading}>
              {t("autoTraining.upload.selectFolder")}
            </Button>
            <Button variant="contained" onClick={() => void uploadSelectedFiles()} disabled={uploading}>
              {uploading ? t("autoTraining.upload.uploading") : t("autoTraining.upload.submit")}
            </Button>
          </Stack>

          {uploading || uploadProgressBytes > 0 ? (
            <Stack spacing={0.8}>
              <LinearProgress
                variant={uploadTotalBytes > 0 ? "determinate" : "indeterminate"}
                value={uploadTotalBytes > 0 ? (uploadProgressBytes / uploadTotalBytes) * 100 : undefined}
              />
              <Typography variant="body2" color="text.secondary">
                {t("autoTraining.upload.progress", {
                  uploaded: formatBytes(uploadProgressBytes),
                  total: formatBytes(uploadTotalBytes),
                  percent: uploadTotalBytes > 0 ? Math.round((uploadProgressBytes / uploadTotalBytes) * 100) : 0,
                })}
              </Typography>
              {currentUploadFile ? (
                <Typography variant="caption" color="text.secondary" sx={noWrapSx}>
                  {t("autoTraining.upload.currentFile", { file: currentUploadFile })}
                </Typography>
              ) : null}
            </Stack>
          ) : null}
        </Stack>
      </SectionCard>

      <SectionCard title={t("autoTraining.archives.title")} subtitle={t("autoTraining.archives.subtitle")}>
        <Stack spacing={1.2}>
          {actionMessage ? <Alert severity="success">{actionMessage}</Alert> : null}
          {actionError ? <Alert severity="error">{actionError}</Alert> : null}
          {error ? <Alert severity="error">{error}</Alert> : null}

          <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
            <Button variant="contained" onClick={() => void onStartTraining()} disabled={startTrainingLoading || hasActiveJob || archives.length === 0}>
              {startTrainingLoading ? t("autoTraining.jobs.actions.starting") : t("autoTraining.jobs.actions.start")}
            </Button>
            <Button
              variant="outlined"
              color="error"
              onClick={() => setArchiveDeleteDialog({ mode: "all" })}
              disabled={archiveDeleteLoading || archives.length === 0 || hasActiveJob}
            >
              {t("autoTraining.archives.actions.deleteAll")}
            </Button>
          </Stack>

          {loading ? (
            <Stack direction="row" spacing={1.2} alignItems="center">
              <CircularProgress size={18} />
              <Typography variant="body2" color="text.secondary">
                {t("autoTraining.archives.loading")}
              </Typography>
            </Stack>
          ) : null}

          {!loading && archives.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {t("autoTraining.archives.empty")}
            </Typography>
          ) : null}

          {archives.length > 0 ? (
            <TableContainer sx={{ ...tableShellSx, maxHeight: archives.length > 15 ? 520 : undefined }}>
              <Table stickyHeader size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>{t("autoTraining.archives.columns.id")}</TableCell>
                    <TableCell>{t("autoTraining.archives.columns.name")}</TableCell>
                    <TableCell>{t("autoTraining.archives.columns.size")}</TableCell>
                    <TableCell>{t("autoTraining.archives.columns.createdAt")}</TableCell>
                    <TableCell>{t("autoTraining.archives.columns.actions")}</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {archives.map((archive) => (
                    <TableRow key={archive.id} hover>
                      <TableCell sx={noWrapSx}>{archive.id}</TableCell>
                      <TableCell>
                        <Stack spacing={0.25}>
                          <Typography variant="body2" sx={noWrapSx}>
                            {archive.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={noWrapSx}>
                            {archive.relative_path} | {archive.format}
                          </Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>{formatBytes(archive.size)}</TableCell>
                      <TableCell>{formatDateTime(archive.created_at)}</TableCell>
                      <TableCell>
                        <Button
                          color="error"
                          size="small"
                          onClick={() => setArchiveDeleteDialog({ mode: "single", archive })}
                          disabled={hasActiveJob}
                        >
                          {t("autoTraining.archives.actions.delete")}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : null}
        </Stack>
      </SectionCard>

      <SectionCard title={t("autoTraining.jobs.title")} subtitle={t("autoTraining.jobs.subtitle")}>
        <Stack spacing={1.2}>
          {loading && jobs.length === 0 ? (
            <Stack direction="row" spacing={1.2} alignItems="center">
              <CircularProgress size={18} />
              <Typography variant="body2" color="text.secondary">
                {t("autoTraining.jobs.loading")}
              </Typography>
            </Stack>
          ) : null}

          {!loading && jobs.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {t("autoTraining.jobs.empty")}
            </Typography>
          ) : null}

          {jobs.map((job) => (
            <Box key={job.id} sx={{ ...tableShellSx, p: 1.5 }}>
              <Stack spacing={1}>
                <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={1}>
                  <Stack spacing={0.4} sx={{ minWidth: 0 }}>
                    <Typography variant="h6" sx={noWrapSx}>
                      {t("autoTraining.jobs.jobTitle", { id: job.id.slice(0, 8) })}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={noWrapSx}>
                      {t("autoTraining.jobs.jobMeta", {
                        sourceType: job.source_type ? tEnum("common.sourceType", job.source_type) : t("common.na"),
                        archives: String((job.detail.archive_count as number | undefined) ?? job.archive_ids.length),
                      })}
                    </Typography>
                  </Stack>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <Chip label={tEnum("common.jobStatus", job.status)} size="small" color={job.status === "completed" ? "success" : job.status === "failed" ? "error" : "default"} />
                    <Typography variant="body2">{Math.round(job.progress_percent)}%</Typography>
                  </Stack>
                </Stack>

                <LinearProgress variant="determinate" value={Math.max(0, Math.min(job.progress_percent, 100))} />

                <Typography variant="body2" color="text.secondary">
                  {t("autoTraining.jobs.currentStep", { step: t(`autoTraining.jobs.steps.${job.current_step}`) })}
                </Typography>

                {job.error_message ? <Alert severity="error">{job.error_message}</Alert> : null}

                <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
                  <TextField
                    label={t("autoTraining.jobs.fields.createdAt")}
                    value={formatDateTime(job.created_at)}
                    InputProps={{ readOnly: true }}
                    size="small"
                  />
                  <TextField
                    label={t("autoTraining.jobs.fields.datasetId")}
                    value={job.dataset_id ?? ""}
                    InputProps={{ readOnly: true }}
                    size="small"
                  />
                  <TextField
                    label={t("autoTraining.jobs.fields.trainingRuns")}
                    value={job.training_run_ids.join(", ")}
                    InputProps={{ readOnly: true }}
                    size="small"
                  />
                </Stack>
              </Stack>
            </Box>
          ))}
        </Stack>
      </SectionCard>

      <Dialog open={archiveDeleteDialog !== null} onClose={() => setArchiveDeleteDialog(null)}>
        <DialogTitle>
          {archiveDeleteDialog?.mode === "all" ? t("autoTraining.archives.deleteAllDialog.title") : t("autoTraining.archives.deleteDialog.title")}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {archiveDeleteDialog?.mode === "all"
              ? t("autoTraining.archives.deleteAllDialog.description")
              : t("autoTraining.archives.deleteDialog.description", { name: archiveDeleteDialog?.archive.name ?? "" })}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setArchiveDeleteDialog(null)}>{t("autoTraining.archives.deleteDialog.cancel")}</Button>
          <Button color="error" onClick={() => void onDeleteArchive()} disabled={archiveDeleteLoading}>
            {t("autoTraining.archives.deleteDialog.confirm")}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
