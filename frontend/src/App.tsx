import { CircularProgress, Stack, Typography } from "@mui/material";
import { Navigate, Route, Routes } from "react-router-dom";
import { noWrapSx } from "./components/ui";
import { useAuth } from "./hooks/useAuth";
import { useI18n } from "./i18n";
import { AppShell } from "./layouts/AppShell";
import { AutoTrainingPage } from "./pages/AutoTrainingPage";
import { DataManagementPage } from "./pages/DataManagementPage";
import { DashboardPage } from "./pages/DashboardPage";
import { DatasetsPage } from "./pages/DatasetsPage";
import { ExplanationsPage } from "./pages/ExplanationsPage";
import { InferencePage } from "./pages/InferencePage";
import { LoginPage } from "./pages/LoginPage";
import { LogsPage } from "./pages/LogsPage";
import { ModelsPage } from "./pages/ModelsPage";
import { TrainingPage } from "./pages/TrainingPage";
import { UsersPage } from "./pages/UsersPage";

function ProtectedApp() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/datasets" element={<DatasetsPage />} />
        <Route path="/datasets/management" element={<DataManagementPage />} />
        <Route path="/auto-training" element={<AutoTrainingPage />} />
        <Route path="/training" element={<TrainingPage />} />
        <Route path="/models" element={<ModelsPage />} />
        <Route path="/inference" element={<InferencePage />} />
        <Route path="/explanations" element={<ExplanationsPage />} />
        <Route path="/logs" element={<LogsPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}

export default function App() {
  const { loading, user } = useAuth();
  const { loading: i18nLoading, t } = useI18n();

  if (loading || i18nLoading) {
    return (
      <Stack justifyContent="center" alignItems="center" spacing={2} minHeight="100vh">
        <CircularProgress color="primary" />
        <Typography variant="body2" color="text.secondary" sx={noWrapSx}>
          {t("app.loading")}
        </Typography>
      </Stack>
    );
  }

  return user ? <ProtectedApp /> : <LoginPage />;
}
