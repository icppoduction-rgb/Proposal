import { Box, Button, Chip, Stack, Typography } from "@mui/material";
import { useCallback, useState } from "react";
import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { noWrapSx, tableRowSx, tableShellSx } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../i18n";
import { usePolling } from "../hooks/usePolling";

export function ModelsPage() {
  const { tokens } = useAuth();
  const { t, tEnum } = useI18n();
  const [message, setMessage] = useState<string | null>(null);

  const loader = useCallback(() => {
    if (!tokens) {
      return Promise.resolve([]);
    }
    return api.listModels(tokens.access_token);
  }, [tokens]);

  const { data } = usePolling(loader);

  const onPromote = async (artifactId: string) => {
    if (!tokens) {
      return;
    }
    const model = await api.promoteModel(tokens.access_token, artifactId);
    setMessage(t("models.messages.promoted", { modelName: model.model_name }));
  };

  return (
    <Stack spacing={3} sx={{ width: "100%" }}>
      <SectionCard title={t("models.title")} subtitle={t("models.subtitle")}>
        {message ? <Typography sx={{ mb: 2 }}>{message}</Typography> : null}
        <Box sx={tableShellSx}>
          {(data ?? []).map((artifact) => (
            <Box
              key={artifact.id}
              sx={{
                ...tableRowSx,
                gridTemplateColumns: { xs: "1fr", xl: "minmax(0, 1fr) minmax(0, 1.1fr) auto" },
              }}
            >
              <Stack spacing={1} sx={{ minWidth: 0, flex: 1 }}>
                <Typography variant="h6" sx={noWrapSx}>
                  {artifact.model_name} | {artifact.model_type}
                </Typography>
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  <Chip
                    label={tEnum("common.artifactStatus", artifact.status)}
                    size="small"
                    color={artifact.status === "promoted" ? "success" : "default"}
                  />
                  <Chip label={`F1 ${artifact.metrics.f1 ?? t("common.na")}`} size="small" />
                </Stack>
                <Typography variant="body2" color="text.secondary" sx={noWrapSx}>
                  {artifact.artifact_path}
                </Typography>
                {artifact.artifact_metadata?.cross_validation_report_path ? (
                  <Typography variant="caption" color="text.secondary" sx={noWrapSx}>
                    {String(artifact.artifact_metadata.cross_validation_report_path)}
                  </Typography>
                ) : null}
              </Stack>
              <Button variant="contained" onClick={() => void onPromote(artifact.id)} disabled={artifact.status === "promoted"}>
                {t("models.actions.promote")}
              </Button>
            </Box>
          ))}
        </Box>
      </SectionCard>
    </Stack>
  );
}
