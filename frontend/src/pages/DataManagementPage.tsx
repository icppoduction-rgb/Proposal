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
  FormControl,
  FormControlLabel,
  FormGroup,
  FormHelperText,
  Grid2,
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
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { formActionSx, formGridSx, formStackSx } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { usePolling } from "../hooks/usePolling";
import { useI18n } from "../i18n";
import type { FeatureSchema, ManagedDataset, RawDatasetInspectResult, RawFile } from "../types/api";

type FormErrors = Partial<Record<"name" | "raw_file_id" | "feature_set", string>>;

type ManagedDatasetDeleteDialogState =
  | { mode: "single"; dataset: ManagedDataset }
  | { mode: "all" }
  | null;

function formatDateTime(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return parsed.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function extractFeatureFamilies(schema: FeatureSchema): string[] {
  const rawValue = schema.definition.feature_families;
  if (!Array.isArray(rawValue)) {
    return [];
  }
  return rawValue.filter((item): item is string => typeof item === "string" && item.length > 0);
}

export function DataManagementPage() {
  const { tokens } = useAuth();
  const { t } = useI18n();

  const [reloadNonce, setReloadNonce] = useState(0);
  const [registerMessage, setRegisterMessage] = useState<string | null>(null);
  const [registerError, setRegisterError] = useState<string | null>(null);
  const [inspectError, setInspectError] = useState<string | null>(null);
  const [rawFilesError, setRawFilesError] = useState<string | null>(null);
  const [rawFilesLoading, setRawFilesLoading] = useState(false);
  const [rawFiles, setRawFiles] = useState<RawFile[]>([]);
  const [inspection, setInspection] = useState<RawDatasetInspectResult | null>(null);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [managedDeleteDialog, setManagedDeleteDialog] = useState<ManagedDatasetDeleteDialogState>(null);
  const [managedDeleteLoading, setManagedDeleteLoading] = useState(false);
  const [managedValidationLoadingId, setManagedValidationLoadingId] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    raw_file_id: "",
    feature_set: [] as string[],
  });

  const managementLoader = useCallback(async () => {
    if (!tokens) {
      return { managedDatasets: [], featureSchemas: [] };
    }

    const [managedDatasets, featureSchemas] = await Promise.all([
      api.listManagedDatasets(tokens.access_token),
      api.listFeatureSchemas(tokens.access_token),
    ]);

    return { managedDatasets, featureSchemas };
  }, [reloadNonce, tokens]);

  const {
    data: managementData,
    error: managementLoadError,
    loading: managementLoading,
  } = usePolling(managementLoader);

  const managedDatasets = managementData?.managedDatasets ?? [];
  const featureSchemas = managementData?.featureSchemas ?? [];

  const loadRawFiles = useCallback(async () => {
    if (!tokens) {
      setRawFiles([]);
      return;
    }

    setRawFilesLoading(true);
    try {
      setRawFiles(await api.listRawDatasetFiles(tokens.access_token));
      setRawFilesError(null);
    } catch (error) {
      setRawFilesError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setRawFilesLoading(false);
    }
  }, [t, tokens]);

  useEffect(() => {
    void loadRawFiles();
  }, [loadRawFiles, reloadNonce]);

  const selectedRawFile = useMemo(
    () => rawFiles.find((item) => item.id === form.raw_file_id) ?? null,
    [form.raw_file_id, rawFiles],
  );

  useEffect(() => {
    if (!form.raw_file_id || selectedRawFile) {
      return;
    }

    setForm((current) => ({
      ...current,
      raw_file_id: "",
      feature_set: [],
    }));
    setInspection(null);
  }, [form.raw_file_id, selectedRawFile]);

  useEffect(() => {
    if (!tokens || !selectedRawFile) {
      setInspection(null);
      setInspectError(null);
      return;
    }

    let active = true;
    setInspectError(null);
    setInspection(null);

    api
      .inspectRawDatasetFile(tokens.access_token, selectedRawFile.relative_path)
      .then((preview) => {
        if (!active) {
          return;
        }

        setInspection(preview);
        setForm((current) => ({
          ...current,
          name: preview.suggested_name,
        }));
        setFormErrors((current) => ({
          ...current,
          name: undefined,
          raw_file_id: undefined,
        }));
      })
      .catch((error) => {
        if (active) {
          setInspectError(error instanceof Error ? error.message : t("api.errors.request"));
        }
      });

    return () => {
      active = false;
    };
  }, [selectedRawFile, t, tokens]);

  const featureOptions = useMemo(() => {
    const compatibleSchemaNames = new Set(inspection?.compatible_feature_schemas ?? []);
    const relevantSchemas =
      compatibleSchemaNames.size > 0
        ? featureSchemas.filter((schema) => compatibleSchemaNames.has(schema.name))
        : featureSchemas;

    return Array.from(new Set(relevantSchemas.flatMap(extractFeatureFamilies))).sort((left, right) => left.localeCompare(right));
  }, [featureSchemas, inspection]);

  useEffect(() => {
    setForm((current) => {
      const nextFeatureSet = current.feature_set.filter((item) => featureOptions.includes(item));
      if (nextFeatureSet.length === current.feature_set.length) {
        return current;
      }
      return {
        ...current,
        feature_set: nextFeatureSet,
      };
    });
  }, [featureOptions]);

  const toggleFeatureFamily = (value: string, checked: boolean) => {
    setForm((current) => ({
      ...current,
      feature_set: checked
        ? Array.from(new Set([...current.feature_set, value]))
        : current.feature_set.filter((item) => item !== value),
    }));
    setFormErrors((current) => ({ ...current, feature_set: undefined }));
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!tokens) {
      return;
    }

    const nextErrors: FormErrors = {};
    if (!form.name.trim()) {
      nextErrors.name = t("datasets.form.validation.required");
    }
    if (!form.raw_file_id.trim()) {
      nextErrors.raw_file_id = t("datasets.form.validation.required");
    }
    if (form.feature_set.length === 0) {
      nextErrors.feature_set = t("datasets.form.validation.required");
    }

    setFormErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setRegisterMessage(null);
    setRegisterError(null);

    try {
      await api.registerManagedDataset(tokens.access_token, {
        name: form.name.trim(),
        raw_file_id: form.raw_file_id,
        feature_set: form.feature_set,
      });
      setRegisterMessage(t("datasets.messages.registered"));
      setForm({
        name: "",
        raw_file_id: "",
        feature_set: [],
      });
      setInspection(null);
      setReloadNonce((current) => current + 1);
    } catch (error) {
      setRegisterError(error instanceof Error ? error.message : t("api.errors.request"));
    }
  };

  const onDeleteManagedDataset = async () => {
    if (!tokens || !managedDeleteDialog) {
      return;
    }

    setManagedDeleteLoading(true);
    setRegisterError(null);

    try {
      if (managedDeleteDialog.mode === "single") {
        await api.deleteManagedDataset(tokens.access_token, managedDeleteDialog.dataset.id);
      } else {
        await api.deleteAllManagedDatasets(tokens.access_token);
      }

      setRegisterMessage(
        managedDeleteDialog.mode === "single"
          ? t("datasets.list.messages.deleted", { name: managedDeleteDialog.dataset.name })
          : t("datasets.list.messages.deletedAll"),
      );
      setManagedDeleteDialog(null);
      setReloadNonce((current) => current + 1);
    } catch (error) {
      setRegisterError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setManagedDeleteLoading(false);
    }
  };

  const onValidateManagedDataset = async (dataset: ManagedDataset) => {
    if (!tokens) {
      return;
    }

    setManagedValidationLoadingId(dataset.id);
    setRegisterMessage(null);
    setRegisterError(null);

    try {
      const task = await api.validateManagedDataset(tokens.access_token, dataset.id);
      setRegisterMessage(t("datasets.messages.validationQueued", { id: task.id }));
    } catch (error) {
      setRegisterError(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setManagedValidationLoadingId(null);
    }
  };

  return (
    <Stack spacing={3} sx={{ width: "100%" }}>
      <SectionCard title={t("datasets.register.title")} subtitle={t("datasets.register.subtitle")}>
        <Stack component="form" sx={formStackSx} onSubmit={onSubmit}>
          {registerMessage ? <Alert severity="success">{registerMessage}</Alert> : null}
          {registerError ? <Alert severity="error">{registerError}</Alert> : null}
          {rawFilesError ? <Alert severity="error">{rawFilesError}</Alert> : null}
          {inspectError ? <Alert severity="warning">{inspectError}</Alert> : null}
          {inspection ? (
            <Alert severity={inspection.supporting_only ? "warning" : "info"}>
              {t("datasets.form.inspectSummary", {
                format: inspection.format,
                profile: inspection.normalization_profile,
                schemas: inspection.compatible_feature_schemas.join(", ") || "n/a",
              })}
            </Alert>
          ) : null}

          <Grid2 container sx={formGridSx}>
            <TextField
              label={t("datasets.form.nameLabel")}
              value={form.name}
              onChange={(event) => {
                setForm((current) => ({ ...current, name: event.target.value }));
                setFormErrors((current) => ({ ...current, name: undefined }));
              }}
              error={Boolean(formErrors.name)}
              helperText={formErrors.name}
            />
            <TextField
              select
              label={t("datasets.form.fileNameLabel")}
              value={form.raw_file_id}
              onChange={(event) => {
                setForm((current) => ({
                  ...current,
                  raw_file_id: event.target.value,
                  feature_set: [],
                }));
                setFormErrors((current) => ({ ...current, raw_file_id: undefined, feature_set: undefined }));
                setRegisterMessage(null);
              }}
              error={Boolean(formErrors.raw_file_id)}
              helperText={formErrors.raw_file_id}
              disabled={rawFilesLoading || rawFiles.length === 0}
            >
              <MenuItem value="" disabled>
                {t("datasets.form.fileSelectPlaceholder")}
              </MenuItem>
              {rawFiles.map((rawFile) => (
                <MenuItem key={rawFile.id} value={rawFile.id}>
                  {rawFile.relative_path}
                </MenuItem>
              ))}
            </TextField>
          </Grid2>

          {rawFilesLoading ? (
            <Stack direction="row" spacing={1.2} alignItems="center">
              <CircularProgress size={18} />
              <Typography variant="body2" color="text.secondary">
                {t("datasets.rawFiles.loading")}
              </Typography>
            </Stack>
          ) : null}

          {rawFiles.length === 0 && !rawFilesLoading ? (
            <Typography variant="body2" color="text.secondary">
              {t("datasets.form.noFiles")}
            </Typography>
          ) : null}

          {inspection ? (
            <Stack spacing={0.75}>
              <Typography variant="body2" color="text.secondary">
                {t("datasets.form.targetColumns", { columns: inspection.target_columns.join(", ") })}
              </Typography>
              {(inspection.quality_warnings ?? []).map((warning) => (
                <Typography key={warning} variant="caption" color="warning.main">
                  {warning}
                </Typography>
              ))}
            </Stack>
          ) : null}

          <FormControl error={Boolean(formErrors.feature_set)}>
            <Typography variant="body2" sx={{ mb: 0.8 }}>
              {t("datasets.form.featureFamiliesLabel")}
            </Typography>
            <Box
              sx={{
                borderRadius: 3,
                border: (theme) => `1px solid ${theme.palette.divider}`,
                px: 1.5,
                py: 1.2,
                maxHeight: featureOptions.length > 8 ? 240 : undefined,
                overflowY: featureOptions.length > 8 ? "auto" : "visible",
              }}
            >
              {featureOptions.length > 0 ? (
                <FormGroup>
                  {featureOptions.map((featureFamily) => (
                    <FormControlLabel
                      key={featureFamily}
                      control={
                        <Checkbox
                          checked={form.feature_set.includes(featureFamily)}
                          onChange={(event) => toggleFeatureFamily(featureFamily, event.target.checked)}
                        />
                      }
                      label={featureFamily}
                    />
                  ))}
                </FormGroup>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  {t("datasets.form.featureSetEmpty")}
                </Typography>
              )}
            </Box>
            <FormHelperText>{formErrors.feature_set ?? t("datasets.form.featureSetHint")}</FormHelperText>
          </FormControl>

          <Stack sx={formActionSx}>
            <Button type="submit" variant="contained" disabled={rawFiles.length === 0 || rawFilesLoading}>
              {t("datasets.form.submit")}
            </Button>
          </Stack>
        </Stack>
      </SectionCard>

      <SectionCard
        title={t("datasets.list.title")}
        subtitle={t("datasets.list.subtitle")}
        headerAction={
          <Button
            color="error"
            variant="outlined"
            onClick={() => setManagedDeleteDialog({ mode: "all" })}
            disabled={managementLoading || managedDatasets.length === 0}
          >
            {t("datasets.list.actions.deleteAll")}
          </Button>
        }
      >
        <Stack spacing={1.2}>
          {managementLoadError ? <Alert severity="error">{managementLoadError}</Alert> : null}
          {managementLoading ? (
            <Stack direction="row" spacing={1.2} alignItems="center">
              <CircularProgress size={18} />
              <Typography variant="body2" color="text.secondary">
                {t("datasets.list.loading")}
              </Typography>
            </Stack>
          ) : null}
          <TableContainer
            sx={{
              borderRadius: 3,
              border: (theme) => `1px solid ${theme.palette.divider}`,
              maxHeight: managedDatasets.length > 15 ? 560 : undefined,
              overflowY: managedDatasets.length > 15 ? "auto" : "visible",
            }}
          >
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t("datasets.list.columns.id")}</TableCell>
                  <TableCell>{t("datasets.list.columns.name")}</TableCell>
                  <TableCell>{t("datasets.list.columns.filePath")}</TableCell>
                  <TableCell>{t("datasets.list.columns.createdAt")}</TableCell>
                  <TableCell align="right">{t("datasets.list.columns.actions")}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {managedDatasets.length > 0 ? (
                  managedDatasets.map((dataset) => (
                    <TableRow key={dataset.id} hover>
                      <TableCell>{dataset.id}</TableCell>
                      <TableCell>
                        <Stack spacing={0.3}>
                          <Typography variant="body2">{dataset.name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {dataset.feature_set.join(", ")}
                          </Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>{dataset.file_path}</TableCell>
                      <TableCell>{formatDateTime(dataset.created_at)}</TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => void onValidateManagedDataset(dataset)}
                            disabled={managedValidationLoadingId === dataset.id}
                          >
                            {managedValidationLoadingId === dataset.id ? (
                              <CircularProgress color="inherit" size={16} />
                            ) : (
                              t("datasets.actions.validate")
                            )}
                          </Button>
                          <Button
                            size="small"
                            color="error"
                            variant="outlined"
                            onClick={() => setManagedDeleteDialog({ mode: "single", dataset })}
                          >
                            {t("datasets.list.actions.delete")}
                          </Button>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <Box sx={{ py: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          {t("datasets.list.empty")}
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

      <Dialog
        open={Boolean(managedDeleteDialog)}
        onClose={() => (managedDeleteLoading ? undefined : setManagedDeleteDialog(null))}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle>
          {managedDeleteDialog?.mode === "all" ? t("datasets.list.deleteAllDialog.title") : t("datasets.list.deleteDialog.title")}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {managedDeleteDialog?.mode === "all"
              ? t("datasets.list.deleteAllDialog.description")
              : t("datasets.list.deleteDialog.description", {
                  name: managedDeleteDialog?.mode === "single" ? managedDeleteDialog.dataset.name : "",
                })}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setManagedDeleteDialog(null)} disabled={managedDeleteLoading}>
            {t("datasets.list.deleteDialog.cancel")}
          </Button>
          <Button color="error" variant="contained" onClick={() => void onDeleteManagedDataset()} disabled={managedDeleteLoading}>
            {managedDeleteLoading ? <CircularProgress color="inherit" size={18} /> : t("datasets.list.deleteDialog.confirm")}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
