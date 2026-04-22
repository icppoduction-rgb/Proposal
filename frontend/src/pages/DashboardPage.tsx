import { Box, Chip, LinearProgress, Stack, Typography } from "@mui/material";
import { useCallback } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { noWrapSx, rowPanelSx, tableRowSx, tableShellSx } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../i18n";
import { usePolling } from "../hooks/usePolling";

function formatMetricValue(value: number | Record<string, number> | undefined, fallback: string): string {
  if (typeof value === "number") {
    return value.toFixed(3);
  }
  return fallback;
}

export function DashboardPage() {
  const { tokens } = useAuth();
  const { t, tEnum } = useI18n();
  const loader = useCallback(async () => {
    if (!tokens) {
      return null;
    }
    const [datasets, trainingRuns, models, jobs, explanations] = await Promise.all([
      api.listDatasets(tokens.access_token),
      api.listTrainingRuns(tokens.access_token),
      api.listModels(tokens.access_token),
      api.listInferenceJobs(tokens.access_token),
      api.listExplanationJobs(tokens.access_token),
    ]);
    return { datasets, trainingRuns, models, jobs, explanations };
  }, [tokens]);
  const { data, loading } = usePolling(loader);

  if (loading || !data) {
    return <LinearProgress />;
  }

  const chartData = [
    { name: t("dashboard.metricLabels.datasets"), value: data.datasets.length },
    { name: t("dashboard.metricLabels.training"), value: data.trainingRuns.length },
    { name: t("dashboard.metricLabels.models"), value: data.models.length },
    { name: t("dashboard.metricLabels.inference"), value: data.jobs.length },
    { name: t("dashboard.metricLabels.explanations"), value: data.explanations.length },
  ];

  return (
    <Stack spacing={3} sx={{ width: "100%" }}>
      <SectionCard title={t("dashboard.state.title")} subtitle={t("dashboard.state.subtitle")}>
        <Stack direction={{ xs: "column", md: "row" }} spacing={1.2} flexWrap="wrap" useFlexGap>
          {chartData.map((item) => (
            <Box key={item.name} sx={{ ...rowPanelSx, minWidth: 0, flex: "1 1 150px", p: 1.2 }}>
              <Typography variant="body2" color="text.secondary" sx={noWrapSx}>
                {item.name}
              </Typography>
              <Typography variant="h4" sx={{ mt: 0.6, ...noWrapSx }}>
                {item.value}
              </Typography>
            </Box>
          ))}
        </Stack>
      </SectionCard>
      <SectionCard title={t("dashboard.overview.title")} subtitle={t("dashboard.overview.subtitle")}>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <XAxis dataKey="name" stroke="#7f95b1" tickLine={false} axisLine={false} />
            <YAxis stroke="#7f95b1" tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                background: "rgba(12, 20, 33, 0.96)",
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 16,
                color: "#ecf3fb",
              }}
            />
            <Bar dataKey="value" fill="#35d2be" radius={[10, 10, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </SectionCard>
      <SectionCard title={t("dashboard.trainingFeed.title")} subtitle={t("dashboard.trainingFeed.subtitle")}>
        {data.trainingRuns.length ? (
          <Box sx={tableShellSx}>
            {data.trainingRuns.slice(0, 6).map((run) => (
              <Box
                key={run.id}
                sx={{
                  ...tableRowSx,
                  gridTemplateColumns: { xs: "1fr", md: "minmax(0, 1fr) auto" },
                }}
              >
                <Stack spacing={0.65} sx={{ minWidth: 0 }}>
                  <Typography variant="h6" sx={noWrapSx}>
                    {t("dashboard.runTitle", { id: run.id.slice(0, 8) })}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={noWrapSx}>
                    {t("dashboard.datasetSchema", {
                      datasetId: run.dataset_id.slice(0, 8),
                      schemaId: run.feature_schema_id.slice(0, 8),
                    })}
                  </Typography>
                </Stack>
                <Stack spacing={0.8} alignItems={{ xs: "flex-start", md: "flex-end" }}>
                  <Chip label={tEnum("common.jobStatus", run.status)} size="small" color={run.status === "completed" ? "success" : "default"} />
                  <Typography variant="body2" sx={noWrapSx}>
                    F1 {formatMetricValue(run.metrics.f1, t("common.na"))}
                  </Typography>
                </Stack>
              </Box>
            ))}
          </Box>
        ) : (
          <Typography color="text.secondary">{t("dashboard.trainingFeed.empty")}</Typography>
        )}
      </SectionCard>
    </Stack>
  );
}
