import { Box, Button, Stack, TextField, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { noWrapSx } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import type { Language } from "../i18n";
import { useI18n } from "../i18n";

const languageOptions: Language[] = ["en", "ru"];

export function LoginPage() {
  const { login } = useAuth();
  const { language, setLanguage, t } = useI18n();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin123456");
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : t("login.error"));
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        px: 2,
        position: "relative",
        background:
          "radial-gradient(circle at left top, rgba(36, 112, 120, 0.34), transparent 24%), linear-gradient(180deg, #07111b 0%, #08111d 52%, #050b13 100%)",
      }}
    >
      <Box
        sx={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          background:
            "radial-gradient(circle at 15% 18%, rgba(81, 220, 203, 0.12), transparent 22%), radial-gradient(circle at 84% 12%, rgba(51, 91, 149, 0.12), transparent 20%)",
        }}
      />
      <Box
        component="form"
        onSubmit={onSubmit}
        sx={{
          position: "relative",
          zIndex: 1,
          width: "min(500px, 100%)",
          p: { xs: 3, md: 3.75 },
          borderRadius: "12px",
          border: "1px solid rgba(255,255,255,0.08)",
          background: "linear-gradient(180deg, rgba(18, 28, 44, 0.94) 0%, rgba(12, 20, 33, 0.98) 100%)",
          boxShadow: "0 32px 72px rgba(2, 6, 17, 0.42)",
          backdropFilter: "blur(18px)",
        }}
      >
        <Stack spacing={3} alignItems="center">
          <Box sx={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}>
            <Typography
              sx={{
                fontSize: { xs: "2.3rem", md: "2.9rem" },
                lineHeight: 0.94,
                letterSpacing: "-0.07em",
                fontWeight: 900,
                textTransform: "uppercase",
                color: "transparent",
                backgroundImage: "linear-gradient(135deg, rgba(245, 251, 255, 0.98) 0%, rgba(177, 240, 233, 0.92) 100%)",
                WebkitBackgroundClip: "text",
                backgroundClip: "text",
                textShadow: `0 0 20px ${alpha("#35d2be", 0.14)}`,
                textAlign: "center",
                ...noWrapSx,
              }}
            >
              PROPOSAL
            </Typography>
            <Box
              sx={{
                mt: 1.1,
                width: 54,
                height: 3,
                borderRadius: 999,
                background: "linear-gradient(90deg, rgba(53, 210, 190, 0.9) 0%, rgba(177, 240, 233, 0.18) 100%)",
              }}
            />
          </Box>
          <Stack direction="row" spacing={1} justifyContent="center" sx={{ width: "100%" }}>
            {languageOptions.map((option) => {
              const selected = language === option;
              return (
                <Button
                  key={option}
                  type="button"
                  variant={selected ? "contained" : "outlined"}
                  size="small"
                  onClick={() => setLanguage(option)}
                  sx={{ minWidth: 72 }}
                >
                  {t(`login.language.${option}`)}
                </Button>
              );
            })}
          </Stack>
          <Stack spacing={3} sx={{ width: "100%" }}>
            <TextField
              label={t("common.email")}
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              fullWidth
              error={Boolean(error)}
              helperText={error ?? " "}
            />
            <TextField
              label={t("common.password")}
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              fullWidth
              error={Boolean(error)}
            />
            <Button type="submit" size="large" variant="contained" fullWidth>
              {t("login.submit")}
            </Button>
          </Stack>
        </Stack>
      </Box>
    </Box>
  );
}
