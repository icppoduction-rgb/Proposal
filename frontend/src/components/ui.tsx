import { Box, Stack, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";

export const noWrapSx = {
  minWidth: 0,
  whiteSpace: "nowrap",
  overflow: "hidden",
  textOverflow: "ellipsis",
};

export const rowPanelSx = {
  p: { xs: 1.5, md: 1.7 },
  borderRadius: "16px",
  border: "1px solid rgba(255,255,255,0.08)",
  background: "linear-gradient(180deg, rgba(27, 40, 59, 0.9) 0%, rgba(20, 31, 48, 0.96) 100%)",
  boxShadow: "0 8px 18px rgba(2, 6, 17, 0.14)",
  transition: "border-color 160ms ease, background-color 160ms ease",
  position: "relative",
  overflow: "hidden",
  "&::before": {
    content: '""',
    position: "absolute",
    inset: "0 0 auto 0",
    height: 1,
    background: "linear-gradient(90deg, rgba(135, 244, 232, 0.14), rgba(135, 244, 232, 0))",
  },
  "&:hover": {
    borderColor: "rgba(53, 210, 190, 0.3)",
    background: "linear-gradient(180deg, rgba(23, 36, 59, 0.94) 0%, rgba(17, 27, 44, 0.98) 100%)",
  },
};

export const formGridSx = {
  display: "grid",
  gap: 1,
  gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" },
};

export const formStackSx = {
  gap: 1.1,
  "& .MuiTextField-root": {
    minWidth: 0,
  },
};

export const formActionSx = {
  pt: 0.4,
  display: "flex",
  justifyContent: "stretch",
  "& > .MuiButton-root": {
    width: "100%",
    justifyContent: "center",
  },
};

export const tableShellSx = {
  borderRadius: "18px",
  border: "1px solid rgba(255,255,255,0.08)",
  background: "linear-gradient(180deg, rgba(17, 26, 41, 0.94) 0%, rgba(13, 21, 34, 0.98) 100%)",
  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)",
  overflow: "hidden",
};

export const tableRowSx = {
  px: { xs: 1.35, md: 1.7 },
  py: { xs: 1.2, md: 1.3 },
  display: "grid",
  alignItems: "center",
  columnGap: 1.5,
  rowGap: 1,
  minWidth: 0,
  borderBottom: "1px solid rgba(255,255,255,0.06)",
  backgroundColor: "rgba(255,255,255,0.015)",
  transition: "background-color 160ms ease, border-color 160ms ease",
  "& > *": {
    minWidth: 0,
  },
  "&:hover": {
    backgroundColor: "rgba(255,255,255,0.03)",
    borderColor: "rgba(53, 210, 190, 0.18)",
  },
  "&:last-child": {
    borderBottom: "none",
  },
};

export function EyebrowPill({ children }: { children: React.ReactNode }) {
  return (
    <Box
      component="span"
      sx={(theme) => ({
        display: "inline-flex",
        alignItems: "center",
        maxWidth: "100%",
        px: 1.5,
        py: 0.7,
        borderRadius: 999,
        border: `1px solid ${alpha(theme.palette.primary.main, 0.22)}`,
        backgroundColor: alpha(theme.palette.primary.main, 0.12),
        color: alpha(theme.palette.primary.light, 0.92),
        boxShadow: `0 0 0 1px ${alpha(theme.palette.primary.main, 0.06)} inset`,
        ...noWrapSx,
      })}
    >
      <Typography variant="caption" sx={{ fontWeight: 600, letterSpacing: "0.02em", ...noWrapSx }}>
        {children}
      </Typography>
    </Box>
  );
}

export function PageHeader({
  eyebrow,
  title,
  subtitle,
  action,
}: {
  eyebrow?: string;
  title: string;
  subtitle: string;
  action?: React.ReactNode;
}) {
  return (
    <Stack
      direction={{ xs: "column", lg: "row" }}
      justifyContent="space-between"
      alignItems={{ xs: "flex-start", lg: "flex-end" }}
      spacing={2}
    >
      <Stack spacing={1.25} sx={{ minWidth: 0, maxWidth: 860 }}>
        {eyebrow ? <EyebrowPill>{eyebrow}</EyebrowPill> : null}
        <Typography
          variant="h3"
          sx={{
            ...noWrapSx,
            fontSize: { xs: "2.5rem", md: "3rem" },
            lineHeight: 0.98,
            letterSpacing: "-0.05em",
          }}
        >
          {title}
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 760 }}>
          {subtitle}
        </Typography>
      </Stack>
      {action ? <Box sx={{ flexShrink: 0, maxWidth: "100%" }}>{action}</Box> : null}
    </Stack>
  );
}
