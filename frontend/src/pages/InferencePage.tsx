import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { FormEvent, useCallback, useState } from "react";
import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { formActionSx, formStackSx, noWrapSx, tableRowSx, tableShellSx } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../i18n";
import { usePolling } from "../hooks/usePolling";
import type { ModelArtifact } from "../types/api";

export function InferencePage() {
  const { tokens } = useAuth();
  const { t, tEnum } = useI18n();
  const [jobId, setJobId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [artifactId, setArtifactId] = useState("");
  const [payload, setPayload] = useState("{}");

  const loader = useCallback(async () => {
    if (!tokens) {
      return { models: [], jobs: [], results: [] };
    }
    const [models, jobs] = await Promise.all([api.listModels(tokens.access_token), api.listInferenceJobs(tokens.access_token)]);
    const results = jobId ? await api.getInferenceResults(tokens.access_token, jobId) : [];
    return { models, jobs, results };
  }, [jobId, tokens]);

  const { data } = usePolling(loader);

  const onSelectArtifact = (nextArtifactId: string) => {
    setArtifactId(nextArtifactId);
    const selectedArtifact = (data?.models ?? []).find((artifact) => artifact.id === nextArtifactId) as ModelArtifact | undefined;
    const requiredFeatures = (selectedArtifact?.artifact_metadata?.required_feature_columns as string[] | undefined) ?? [];
    const nextPayload = Object.fromEntries(requiredFeatures.map((feature) => [feature, 0]));
    setPayload(JSON.stringify(nextPayload, null, 2));
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!tokens) {
      return;
    }
    const recordFeatures = JSON.parse(payload) as Record<string, unknown>;
    const selectedArtifact = (data?.models ?? []).find((artifact) => artifact.id === artifactId) as ModelArtifact | undefined;
    const sourceType = (selectedArtifact?.artifact_metadata?.feature_schema as { source_type?: string } | undefined)?.source_type ?? "network";
    const job = await api.createInferenceJob(tokens.access_token, {
      model_artifact_id: artifactId,
      records: [
        {
          entity_id: "interactive-entity",
          event_ts: new Date().toISOString(),
          source_type: sourceType,
          features: recordFeatures,
        },
      ],
    });
    setJobId(job.id);
    setMessage(t("inference.messages.queued", { id: job.id }));
  };

  return (
    <Stack spacing={3} sx={{ width: "100%" }}>
      <SectionCard title={t("inference.request.title")} subtitle={t("inference.request.subtitle")}>
        <Stack component="form" sx={formStackSx} onSubmit={onSubmit}>
          {message ? <Alert severity="info">{message}</Alert> : null}
          <TextField select label={t("inference.form.modelLabel")} value={artifactId} onChange={(e) => onSelectArtifact(e.target.value)}>
            {(data?.models ?? [])
              .filter((artifact) => artifact.status === "promoted")
              .map((artifact) => (
                <MenuItem value={artifact.id} key={artifact.id}>
                  {artifact.model_name} | {tEnum("common.artifactStatus", artifact.status)} |{" "}
                  {String((artifact.artifact_metadata?.feature_schema as { name?: string } | undefined)?.name ?? "schema")}
                </MenuItem>
              ))}
          </TextField>
          <TextField
            label={t("inference.form.payloadLabel")}
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
            multiline
            minRows={8}
          />
          <Stack sx={formActionSx}>
            <Button variant="contained" type="submit">
              {t("inference.form.submit")}
            </Button>
          </Stack>
        </Stack>
      </SectionCard>
      <SectionCard title={t("inference.results.title")} subtitle={t("inference.results.subtitle")}>
        <Box sx={tableShellSx}>
          {(data?.results ?? []).map((result) => (
            <Box
              key={result.id}
              sx={{
                ...tableRowSx,
                gridTemplateColumns: { xs: "1fr", md: "minmax(0, 1fr) auto" },
              }}
            >
              <Typography variant="h6" sx={noWrapSx}>
                {t("inference.results.label", { entityId: result.entity_id, label: result.predicted_label })}
              </Typography>
              <Typography variant="body2" sx={noWrapSx}>
                {t("inference.results.score", { score: result.score.toFixed(4) })}
              </Typography>
            </Box>
          ))}
          {!data?.results?.length ? (
            <Box sx={{ ...tableRowSx, gridTemplateColumns: "1fr" }}>
              <Typography color="text.secondary">{t("inference.results.empty")}</Typography>
            </Box>
          ) : null}
        </Box>
      </SectionCard>
    </Stack>
  );
}
