import { Alert, Box, Button, Grid2, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { FormEvent, useCallback, useState } from "react";
import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { formActionSx, formGridSx, formStackSx, noWrapSx, tableRowSx, tableShellSx } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../i18n";
import { usePolling } from "../hooks/usePolling";

export function ExplanationsPage() {
  const { tokens } = useAuth();
  const { t, tEnum } = useI18n();
  const [explanationJobId, setExplanationJobId] = useState("");
  const [inferenceJobId, setInferenceJobId] = useState("");
  const [modelArtifactId, setModelArtifactId] = useState("");
  const [detectionResultId, setDetectionResultId] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const loader = useCallback(async () => {
    if (!tokens) {
      return { explanationJobs: [], explanationResult: null, models: [], inferenceJobs: [], results: [] };
    }
    const [models, inferenceJobs, explanationJobs] = await Promise.all([
      api.listModels(tokens.access_token),
      api.listInferenceJobs(tokens.access_token),
      api.listExplanationJobs(tokens.access_token),
    ]);
    const selectedJobId = inferenceJobId || inferenceJobs[0]?.id;
    const results = selectedJobId ? await api.getInferenceResults(tokens.access_token, selectedJobId) : [];
    const explanationResult = explanationJobId ? await api.getExplanationResult(tokens.access_token, explanationJobId).catch(() => null) : null;
    return { explanationJobs, explanationResult, models, inferenceJobs, results };
  }, [explanationJobId, inferenceJobId, tokens]);

  const { data } = usePolling(loader);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!tokens) {
      return;
    }
    const job = await api.requestExplanation(tokens.access_token, {
      model_artifact_id: modelArtifactId,
      detection_result_id: detectionResultId,
      top_k: 5,
    });
    setExplanationJobId(job.id);
    setMessage(t("explanations.messages.queued", { id: job.id }));
  };

  return (
    <Stack spacing={3} sx={{ width: "100%" }}>
      <SectionCard title={t("explanations.request.title")} subtitle={t("explanations.request.subtitle")}>
        <Stack component="form" sx={formStackSx} onSubmit={onSubmit}>
          {message ? <Alert severity="info">{message}</Alert> : null}
          <Grid2 container sx={formGridSx}>
            <TextField select label="Inference job" value={inferenceJobId} onChange={(e) => setInferenceJobId(e.target.value)}>
              {(data?.inferenceJobs ?? []).map((job) => (
                <MenuItem key={job.id} value={job.id}>
                  {job.id.slice(0, 8)} | {tEnum("common.jobStatus", job.status)}
                </MenuItem>
              ))}
            </TextField>
            <TextField select label={t("explanations.form.modelArtifactLabel")} value={modelArtifactId} onChange={(e) => setModelArtifactId(e.target.value)}>
              {(data?.models ?? []).map((artifact) => (
                <MenuItem key={artifact.id} value={artifact.id}>
                  {artifact.model_name} | {tEnum("common.artifactStatus", artifact.status)}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label={t("explanations.form.detectionResultLabel")}
              value={detectionResultId}
              onChange={(e) => setDetectionResultId(e.target.value)}
            >
              {(data?.results ?? []).map((result) => (
                <MenuItem key={result.id} value={result.id}>
                  {t("explanations.form.scoreOption", { entityId: result.entity_id, score: result.score.toFixed(3) })}
                </MenuItem>
              ))}
            </TextField>
          </Grid2>
          <Stack sx={formActionSx}>
            <Button variant="contained" type="submit">
              {t("explanations.form.submit")}
            </Button>
          </Stack>
        </Stack>
      </SectionCard>
      <SectionCard title={t("explanations.details.title")} subtitle={t("explanations.details.subtitle")}>
        {data?.explanationResult ? (
          <Stack spacing={2}>
            <Typography color="text.secondary">{data.explanationResult.payload.summary}</Typography>
            <Stack spacing={1.2}>
              <Typography variant="h6" sx={noWrapSx}>
                {t("explanations.details.positiveTitle")}
              </Typography>
              <Box sx={tableShellSx}>
                {(data.explanationResult.payload.top_positive ?? []).map((item) => (
                  <Box
                    key={item.feature}
                    sx={{
                      ...tableRowSx,
                      gridTemplateColumns: { xs: "1fr", md: "minmax(0, 1fr) auto" },
                    }}
                  >
                    <Typography sx={{ ...noWrapSx, flex: 1 }}>{item.feature}</Typography>
                    <Typography color="primary.light" sx={noWrapSx}>
                      {item.contribution.toFixed(4)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Stack>
            <Stack spacing={1.2}>
              <Typography variant="h6" sx={noWrapSx}>
                {t("explanations.details.negativeTitle")}
              </Typography>
              <Box sx={tableShellSx}>
                {(data.explanationResult.payload.top_negative ?? []).map((item) => (
                  <Box
                    key={item.feature}
                    sx={{
                      ...tableRowSx,
                      gridTemplateColumns: { xs: "1fr", md: "minmax(0, 1fr) auto" },
                    }}
                  >
                    <Typography sx={{ ...noWrapSx, flex: 1 }}>{item.feature}</Typography>
                    <Typography color="text.secondary" sx={noWrapSx}>
                      {item.contribution.toFixed(4)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Stack>
          </Stack>
        ) : (
          <Typography color="text.secondary">{t("explanations.details.empty")}</Typography>
        )}
      </SectionCard>
    </Stack>
  );
}
