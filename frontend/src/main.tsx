import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";
import { alpha } from "@mui/material/styles";
import App from "./App";
import { AuthProvider } from "./hooks/useAuth";
import { I18nProvider } from "./i18n";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#35d2be", light: "#86f4e8", dark: "#1c8678" },
    secondary: { main: "#9eb1c8" },
    background: { default: "#07111b", paper: "#0f1928" },
    text: { primary: "#ecf3fb", secondary: "#8da0ba" },
  },
  typography: {
    fontFamily: '"IBM Plex Sans", "Segoe UI", sans-serif',
    h3: { fontWeight: 700, letterSpacing: "-0.05em" },
    h4: { fontWeight: 700, letterSpacing: "-0.04em" },
    h5: { fontWeight: 680, letterSpacing: "-0.03em" },
    h6: { fontWeight: 650, letterSpacing: "-0.02em" },
    button: { fontWeight: 600, textTransform: "none" },
  },
  shape: {
    borderRadius: 2,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background:
            "radial-gradient(circle at left top, rgba(36, 109, 119, 0.32), transparent 26%), linear-gradient(180deg, #07111b 0%, #08101a 52%, #050b13 100%)",
        },
        "#root": {
          minHeight: "100vh",
        },
        "*::-webkit-scrollbar": {
          width: 10,
          height: 10,
        },
        "*::-webkit-scrollbar-thumb": {
          backgroundColor: "rgba(130, 158, 188, 0.22)",
          borderRadius: 999,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: ({ theme }) => ({
          backgroundImage: "none",
          backgroundColor: alpha("#0d1523", 0.95),
          borderRight: `1px solid ${alpha(theme.palette.common.white, 0.06)}`,
          boxShadow: `inset -1px 0 0 ${alpha(theme.palette.primary.main, 0.06)}`,
        }),
      },
    },
    MuiButton: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: 8,
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
          boxShadow: "none",
          paddingInline: theme.spacing(2.1),
          minHeight: 46,
        }),
        contained: ({ theme }) => ({
          background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${alpha(theme.palette.primary.light, 0.82)} 100%)`,
          color: "#041016",
          "&:hover": {
            boxShadow: `0 12px 28px ${alpha(theme.palette.primary.main, 0.28)}`,
          },
        }),
        outlined: ({ theme }) => ({
          borderColor: alpha(theme.palette.common.white, 0.14),
          backgroundColor: alpha(theme.palette.common.white, 0.03),
          "&:hover": {
            borderColor: alpha(theme.palette.primary.main, 0.4),
            backgroundColor: alpha(theme.palette.primary.main, 0.08),
          },
        }),
      },
    },
    MuiChip: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: 999,
          border: `1px solid ${alpha(theme.palette.common.white, 0.08)}`,
          backgroundColor: alpha(theme.palette.common.white, 0.04),
        }),
        label: {
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: ({ theme }) => ({
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
          borderRadius: 8,
          marginInline: theme.spacing(0.75),
          marginBlock: theme.spacing(0.35),
        }),
      },
    },
    MuiTextField: {
      defaultProps: {
        variant: "outlined",
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: 10,
          backgroundColor: alpha(theme.palette.common.white, 0.035),
          "& fieldset": {
            borderColor: alpha(theme.palette.common.white, 0.1),
          },
          "&:hover fieldset": {
            borderColor: alpha(theme.palette.primary.main, 0.32),
          },
          "&.Mui-focused fieldset": {
            borderColor: alpha(theme.palette.primary.main, 0.54),
            boxShadow: `0 0 0 4px ${alpha(theme.palette.primary.main, 0.08)}`,
          },
        }),
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: ({ theme }) => ({
          borderRadius: 10,
          border: `1px solid ${alpha(theme.palette.common.white, 0.08)}`,
        }),
      },
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <I18nProvider>
          <AuthProvider>
            <App />
          </AuthProvider>
        </I18nProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
