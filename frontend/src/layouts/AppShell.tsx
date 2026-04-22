import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import MenuRoundedIcon from "@mui/icons-material/MenuRounded";
import {
  AppBar,
  Box,
  Button,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  Toolbar,
  Typography,
  useMediaQuery,
} from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import { useMemo, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { noWrapSx } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../i18n";

const navItems = [
  { labelKey: "nav.overview", href: "/" },
  { labelKey: "nav.dataUpload", href: "/datasets" },
  { labelKey: "nav.dataManagement", href: "/datasets/management" },
  { labelKey: "nav.autoTraining", href: "/auto-training" },
  { labelKey: "nav.training", href: "/training" },
  { labelKey: "nav.models", href: "/models" },
  { labelKey: "nav.inference", href: "/inference" },
  { labelKey: "nav.explanations", href: "/explanations" },
  { labelKey: "nav.logs", href: "/logs" },
  { labelKey: "nav.users", href: "/users" },
];

const pageHeaderMeta: Record<string, { titleKey: string; subtitleKey?: string }> = {
  "/": {
    titleKey: "layout.headers.overview.title",
    subtitleKey: "layout.headers.overview.subtitle",
  },
  "/datasets": {
    titleKey: "layout.headers.dataUpload.title",
    subtitleKey: "layout.headers.dataUpload.subtitle",
  },
  "/datasets/management": {
    titleKey: "layout.headers.dataManagement.title",
    subtitleKey: "layout.headers.dataManagement.subtitle",
  },
  "/auto-training": {
    titleKey: "layout.headers.autoTraining.title",
    subtitleKey: "layout.headers.autoTraining.subtitle",
  },
  "/training": {
    titleKey: "layout.headers.training.title",
    subtitleKey: "layout.headers.training.subtitle",
  },
  "/models": {
    titleKey: "layout.headers.models.title",
    subtitleKey: "layout.headers.models.subtitle",
  },
  "/inference": {
    titleKey: "layout.headers.inference.title",
    subtitleKey: "layout.headers.inference.subtitle",
  },
  "/explanations": {
    titleKey: "layout.headers.explanations.title",
    subtitleKey: "layout.headers.explanations.subtitle",
  },
  "/logs": {
    titleKey: "layout.headers.logs.title",
    subtitleKey: "layout.headers.logs.subtitle",
  },
  "/users": {
    titleKey: "layout.headers.users.title",
    subtitleKey: "layout.headers.users.subtitle",
  },
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  const { logout } = useAuth();
  const { t } = useI18n();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up("lg"));
  const [mobileOpen, setMobileOpen] = useState(false);
  const activeNavItem = useMemo(() => navItems.find((item) => item.href === pathname) ?? navItems[0], [pathname]);
  const pageHeader = pageHeaderMeta[pathname];
  const drawerWidth = 290;

  const drawerContent = (
    <Box
      sx={{
        height: "100%",
        p: { xs: 1.5, md: 1.9 },
      }}
    >
      <Stack
        sx={{
          height: "100%",
          p: 1.75,
          borderRadius: "26px",
          border: `1px solid ${alpha(theme.palette.common.white, 0.08)}`,
          background: `linear-gradient(180deg, ${alpha("#101928", 0.96)} 0%, ${alpha("#0c1523", 0.98)} 100%)`,
          boxShadow: `0 18px 42px ${alpha("#020611", 0.24)}`,
        }}
      >
        <Stack spacing={1.6}>
          <Box
            sx={{
              px: 1.15,
              py: 1.35,
              borderRadius: "18px",
              border: `1px solid ${alpha(theme.palette.common.white, 0.06)}`,
              backgroundColor: alpha(theme.palette.common.white, 0.025),
            }}
          >
            <Stack spacing={0.95} sx={{ minWidth: 0 }}>
              <Typography
                sx={{
                  ...noWrapSx,
                  fontSize: { xs: "1.95rem", xl: "2.12rem" },
                  lineHeight: 0.94,
                  letterSpacing: "-0.07em",
                  fontWeight: 900,
                  textTransform: "uppercase",
                  color: "transparent",
                  backgroundImage: `linear-gradient(135deg, ${alpha("#f5fbff", 0.98)} 0%, ${alpha(
                    theme.palette.primary.light,
                    0.86,
                  )} 100%)`,
                  WebkitBackgroundClip: "text",
                  backgroundClip: "text",
                  textShadow: `0 0 20px ${alpha(theme.palette.primary.main, 0.14)}`,
                }}
              >
                Proposal
              </Typography>
              <Box
                sx={{
                  width: 54,
                  height: 3,
                  borderRadius: 999,
                  background: `linear-gradient(90deg, ${alpha(theme.palette.primary.main, 0.88)} 0%, ${alpha(
                    theme.palette.primary.light,
                    0.16,
                  )} 100%)`,
                }}
              />
            </Stack>
          </Box>
          <List sx={{ display: "grid", gap: 0.85, p: 0 }}>
            {navItems.map((item) => (
              <ListItemButton
                key={item.href}
                component={Link}
                to={item.href}
                selected={pathname === item.href}
                onClick={() => setMobileOpen(false)}
                sx={{
                  px: 1.35,
                  py: 1.08,
                  borderRadius: "14px",
                  border: `1px solid ${alpha(theme.palette.common.white, pathname === item.href ? 0.1 : 0.05)}`,
                  backgroundColor:
                    pathname === item.href ? alpha(theme.palette.primary.main, 0.12) : alpha(theme.palette.common.white, 0.02),
                  boxShadow: pathname === item.href ? `inset 0 0 0 1px ${alpha(theme.palette.primary.main, 0.12)}` : "none",
                  "&:hover": {
                    backgroundColor: alpha(theme.palette.primary.main, 0.08),
                  },
                  "&.Mui-selected": {
                    backgroundColor: alpha(theme.palette.primary.main, 0.14),
                    boxShadow: `inset 0 0 0 1px ${alpha(theme.palette.primary.main, 0.12)}`,
                  },
                }}
              >
                <ListItemText
                  primary={t(item.labelKey)}
                  primaryTypographyProps={{ sx: { fontWeight: activeNavItem.href === item.href ? 650 : 560, ...noWrapSx } }}
                />
              </ListItemButton>
            ))}
          </List>
        </Stack>
        <Box sx={{ mt: "auto", pt: 1.5 }}>
          <Button
            variant="outlined"
            startIcon={<LogoutRoundedIcon />}
            onClick={() => void logout()}
            fullWidth
            sx={{ borderRadius: "14px" }}
          >
            {t("common.logout")}
          </Button>
        </Box>
      </Stack>
    </Box>
  );

  return (
    <Box
      sx={{
        position: "relative",
        minHeight: "100vh",
        background:
          "radial-gradient(circle at left top, rgba(45, 123, 130, 0.3), transparent 24%), linear-gradient(180deg, #07111b 0%, #08101a 52%, #050b13 100%)",
      }}
    >
      <Box
        sx={{
          pointerEvents: "none",
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 8% 0%, rgba(78, 205, 186, 0.12), transparent 18%), radial-gradient(circle at 82% 20%, rgba(67, 112, 182, 0.08), transparent 24%)",
        }}
      />
      <Box sx={{ display: "flex", minHeight: "100vh", position: "relative", zIndex: 1 }}>
        {isDesktop ? (
          <Drawer
            variant="permanent"
            sx={{
              width: drawerWidth + 32,
              flexShrink: 0,
              "& .MuiDrawer-paper": {
                width: drawerWidth + 32,
                boxSizing: "border-box",
                p: 0,
                background: "transparent",
                border: "none",
                boxShadow: "none",
              },
            }}
          >
            {drawerContent}
          </Drawer>
        ) : (
          <Drawer
            open={mobileOpen}
            onClose={() => setMobileOpen(false)}
            variant="temporary"
            ModalProps={{ keepMounted: true }}
            sx={{
              "& .MuiDrawer-paper": {
                width: Math.min(drawerWidth, 320),
                boxSizing: "border-box",
                p: 0,
                background: "transparent",
                border: "none",
                boxShadow: "none",
              },
            }}
          >
            {drawerContent}
          </Drawer>
        )}
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Box sx={{ p: { xs: 1.5, md: 1.9 } }}>
            <Box
              sx={{
                minHeight: "calc(100vh - 24px)",
                borderRadius: { xs: "20px", md: "28px" },
                border: `1px solid ${alpha(theme.palette.common.white, 0.08)}`,
                background: `linear-gradient(180deg, ${alpha("#0d1624", 0.96)} 0%, ${alpha("#0a121d", 0.98)} 100%)`,
                boxShadow: `0 20px 46px ${alpha("#020611", 0.22)}`,
                overflow: "hidden",
              }}
            >
              <AppBar
                position="sticky"
                elevation={0}
                color="transparent"
                sx={{
                  borderBottom: `1px solid ${alpha(theme.palette.common.white, 0.06)}`,
                  backgroundColor: alpha("#0b1320", 0.72),
                  backdropFilter: "blur(18px)",
                }}
              >
                <Toolbar
                  sx={{
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    gap: 2,
                    px: { xs: 2, md: 3 },
                    py: pageHeader ? { xs: 1.35, md: 1.6 } : 0,
                    minHeight: pageHeader ? "unset" : undefined,
                  }}
                >
                  <Stack direction="row" spacing={1.5} alignItems="center" sx={{ minWidth: 0 }}>
                    {!isDesktop ? (
                      <IconButton color="inherit" onClick={() => setMobileOpen(true)} sx={{ flexShrink: 0 }}>
                        <MenuRoundedIcon />
                      </IconButton>
                    ) : null}
                    <Box sx={{ minWidth: 0 }}>
                      {pageHeader ? (
                        <Stack spacing={0.55} sx={{ minWidth: 0 }}>
                          <Typography
                            variant="h5"
                            sx={{
                              ...noWrapSx,
                              fontSize: { xs: "1.4rem", md: "1.7rem" },
                              lineHeight: 1.03,
                              fontWeight: 760,
                              letterSpacing: "-0.04em",
                            }}
                          >
                            {t(pageHeader.titleKey)}
                          </Typography>
                          {pageHeader.subtitleKey ? (
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              sx={{
                                maxWidth: "100%",
                                fontSize: { xs: "0.98rem", md: "1.06rem" },
                                lineHeight: 1.52,
                                ...noWrapSx,
                              }}
                            >
                              {t(pageHeader.subtitleKey)}
                            </Typography>
                          ) : null}
                        </Stack>
                      ) : null}
                    </Box>
                  </Stack>
                  <Box sx={{ flexShrink: 0 }} />
                </Toolbar>
              </AppBar>
              <Box sx={{ p: { xs: 2, md: 2.5, xl: 3 } }}>
                <Box sx={{ width: "100%", minWidth: 0 }}>{children}</Box>
              </Box>
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
