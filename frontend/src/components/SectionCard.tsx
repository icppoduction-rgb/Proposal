import { Box, Card, CardContent, Stack, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";
import { EyebrowPill, noWrapSx } from "./ui";

export function SectionCard({
  eyebrow,
  title,
  subtitle,
  headerAction,
  children,
}: {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  headerAction?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <Card
      elevation={0}
      sx={(theme) => ({
        position: "relative",
        width: "100%",
        height: "100%",
        borderRadius: "24px",
        border: `1px solid ${alpha(theme.palette.common.white, 0.08)}`,
        background: `linear-gradient(180deg, ${alpha("#172133", 0.94)} 0%, ${alpha("#111a2a", 0.98)} 100%)`,
        boxShadow: `0 14px 30px ${alpha("#020611", 0.18)}`,
        overflow: "hidden",
        "&::before": {
          content: '""',
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(255,255,255,0.028) 0%, rgba(255,255,255,0.01) 18%, rgba(255,255,255,0) 48%)",
          pointerEvents: "none",
        },
      })}
    >
      <CardContent
        sx={{
          position: "relative",
          zIndex: 1,
          p: { xs: 2, md: 2.35 },
          "&:last-child": { pb: { xs: 2, md: 2.35 } },
        }}
      >
        <Stack
          direction={{ xs: "column", md: "row" }}
          justifyContent="space-between"
          spacing={2}
          sx={{ mb: 1.6, pb: 1.3, borderBottom: "1px solid rgba(255,255,255,0.07)" }}
        >
          <Stack spacing={1.2} sx={{ minWidth: 0 }}>
            {eyebrow ? <EyebrowPill>{eyebrow}</EyebrowPill> : null}
            <Typography
              variant="h5"
              color="text.primary"
              sx={{ fontSize: { xs: "1.45rem", md: "1.65rem" }, lineHeight: 1.02, letterSpacing: "-0.03em", ...noWrapSx }}
            >
              {title}
            </Typography>
            {subtitle ? (
              <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 760 }}>
                {subtitle}
              </Typography>
            ) : null}
          </Stack>
          {headerAction ? <Box sx={{ flexShrink: 0, maxWidth: "100%" }}>{headerAction}</Box> : null}
        </Stack>
        {children}
      </CardContent>
    </Card>
  );
}
