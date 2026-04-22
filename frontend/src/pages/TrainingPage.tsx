import { Alert, Box, Button, Chip, Grid2, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { FormEvent, useCallback, useState } from "react";
import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { formActionSx, formGridSx, formStackSx, noWrapSx, tableRowSx, tableShellSx } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../i18n";
import { usePolling } from "../hooks/usePolling";

function formatMetricValue(value: number | Record<string, number> | undefined, fallback: string): string {
  if (typeof value === "number") {
    return String(value);
  }
  return fallback;
}

export function TrainingPage() {
  const { tokens } = useAuth();
  const { t, tEnum } = useI18n();
  const [message, setMessage] = useState<{ text: string; severity: "success" | "error" } | null>(null);
  const [payload, setPayload] = useState({
    dataset_id: "",
    feature_schema_id: "",
    sequence_length: 50,
    sequence_stride: 10,
  });

  const loader = useCallback(async () => {
    if (!tokens) {
      return { datasets: [], schemas: [], runs: [] };
    }
    const [datasets, schemas, runs] = await Promise.all([
      api.listDatasets(tokens.access_token),
      api.listFeatureSchemas(tokens.access_token),
      api.listTrainingRuns(tokens.access_token),
    ]);
    return { datasets, schemas, runs };
  }, [tokens]);

  const { data } = usePolling(loader);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!tokens) {
      return;
    }
    if (!payload.dataset_id) {
      setMessage({ text: t("training.messages.datasetRequired"), severity: "error" });
      return;
    }
    if (!payload.feature_schema_id) {
      setMessage({ text: t("training.messages.featureSchemaRequired"), severity: "error" });
      return;
    }
    const selectedDataset = (data?.datasets ?? []).find((dataset) => dataset.id === payload.dataset_id);
    if (!selectedDataset) {
      setMessage({ text: t("training.messages.datasetUnavailable"), severity: "error" });
      return;
    }
    if (selectedDataset.validation_status !== "validated") {
      setMessage({ text: t("training.messages.datasetValidationRequired"), severity: "error" });
      return;
    }
    const run = await api.createTrainingRun(tokens.access_token, {
      ...payload,
      models: ["random_forest", "xgboost", "cnn", "lstm", "fusion"],
      hyperparameters: {},
    });
    setMessage({ text: t("training.messages.queued", { id: run.id }), severity: "success" });
  };

  return (
    <Stack spacing={3} sx={{ width: "100%" }}>
      <SectionCard title={t("training.newRun.title")} subtitle={t("training.newRun.subtitle")}>
        <Stack component="form" sx={formStackSx} onSubmit={onSubmit}>
          {message ? <Alert severity={message.severity}>{message.text}</Alert> : null}
          <Grid2 container sx={formGridSx}>
            <TextField
              select
              required
              label={t("training.form.datasetLabel")}
              value={payload.dataset_id}
              onChange={(e) => setPayload({ ...payload, dataset_id: e.target.value })}
            >
              {(data?.datasets ?? [])
                .filter((dataset) => dataset.validation_status === "validated")
                .map((dataset) => (
                <MenuItem value={dataset.id} key={dataset.id}>
                  {dataset.name} {dataset.normalization_profile ? `| ${dataset.normalization_profile}` : ""}
                </MenuItem>
                ))}
            </TextField>
            <TextField
              select
              required
              label={t("training.form.featureSchemaLabel")}
              value={payload.feature_schema_id}
              onChange={(e) => setPayload({ ...payload, feature_schema_id: e.target.value })}
            >
              {(data?.schemas ?? []).map((schema) => (
                <MenuItem value={schema.id} key={schema.id}>
                  {schema.name} v{schema.version}
                </MenuItem>
              ))}
            </TextField>
          </Grid2>
          <Grid2 container sx={formGridSx}>
            <TextField
              label={t("training.form.sequenceLengthLabel")}
              type="number"
              value={payload.sequence_length}
              onChange={(e) => setPayload({ ...payload, sequence_length: Number(e.target.value) })}
            />
            <TextField
              label={t("training.form.sequenceStrideLabel")}
              type="number"
              value={payload.sequence_stride}
              onChange={(e) => setPayload({ ...payload, sequence_stride: Number(e.target.value) })}
            />
          </Grid2>
          <Stack sx={formActionSx}>
            <Button variant="contained" type="submit">
              {t("training.form.submit")}
            </Button>
          </Stack>
        </Stack>
      </SectionCard>
      <SectionCard title={t("training.history.title")} subtitle={t("training.history.subtitle")}>
        <Box sx={tableShellSx}>
          {(data?.runs ?? []).map((run) => (
            <Box
              key={run.id}
              sx={{
                ...tableRowSx,
                gridTemplateColumns: { xs: "1fr", md: "minmax(0, 1fr) auto" },
              }}
            >
              <Stack spacing={0.65} sx={{ minWidth: 0 }}>
                <Typography variant="h6" sx={noWrapSx}>
                  {t("training.runTitle", { id: run.id.slice(0, 8) })}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={noWrapSx}>
                  {t("training.datasetSchema", {
                    datasetId: run.dataset_id.slice(0, 8),
                    schemaId: run.feature_schema_id.slice(0, 8),
                  })}
                </Typography>
              </Stack>
              <Stack spacing={0.75} alignItems={{ xs: "flex-start", md: "flex-end" }}>
                <Chip label={tEnum("common.jobStatus", run.status)} size="small" color={run.status === "completed" ? "success" : "default"} />
                <Typography variant="body2" sx={noWrapSx}>
                  F1 {formatMetricValue(run.metrics.f1, t("common.na"))}
                </Typography>
                <Typography variant="body2" sx={noWrapSx}>
                  AUC {formatMetricValue(run.metrics.auc, t("common.na"))} | FPR {formatMetricValue(run.metrics.fpr, t("common.na"))}
                </Typography>
              </Stack>
            </Box>
          ))}
        </Box>
      </SectionCard>
    </Stack>
  );
}
