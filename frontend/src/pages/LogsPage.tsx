import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { formActionSx, formGridSx, formStackSx, noWrapSx, tableRowSx, tableShellSx } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../i18n";
import type { LogEntry, LogQueryResult } from "../types/api";

type LogFilters = {
  service: string;
  level: string;
  function: string;
  message: string;
  error_text: string;
  search: string;
  date_from: string;
  date_to: string;
  time_from: string;
  time_to: string;
  sort: "asc" | "desc";
};

function createDefaultFilters(): LogFilters {
  return {
    service: "",
    level: "",
    function: "",
    message: "",
    error_text: "",
    search: "",
    date_from: "",
    date_to: "",
    time_from: "",
    time_to: "",
    sort: "desc",
  };
}

const logsFilterGridSx = {
  ...formGridSx,
  gridTemplateColumns: {
    xs: "1fr",
    lg: "repeat(3, minmax(0, 1fr))",
  },
};

const logsDateTimeGroupSx = {
  display: "grid",
  gap: 1,
  gridTemplateColumns: {
    xs: "1fr",
    sm: "repeat(2, minmax(0, 1fr))",
  },
};

const logsStreamViewportSx = {
  minHeight: 220,
  maxHeight: {
    xs: "42vh",
    md: "48vh",
    xl: "54vh",
  },
  overflowY: "auto",
  pr: 0.5,
  mr: -0.5,
  scrollbarGutter: "stable",
};

/**
 * EN: Format an ISO timestamp for user-facing presentation.
 * RU: Форматирует ISO-время для отображения пользователю.
 */
function formatTimestamp(value?: string | null): string {
  if (!value) {
    return "n/a";
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

/**
 * EN: Pretty-print structured payloads inside read-only detail fields.
 * RU: Форматирует структурированные payload-ы для read-only полей деталей.
 */
function formatJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2);
}

/**
 * EN: Map log severity to MUI chip colors used by the log list.
 * RU: Сопоставляет уровень логирования цветам MUI Chip в списке логов.
 */
function getLevelColor(level: string): "error" | "warning" | "success" | "default" {
  const normalized = level.toLowerCase();
  if (normalized === "error" || normalized === "critical") {
    return "error";
  }
  if (normalized === "warning") {
    return "warning";
  }
  if (normalized === "info") {
    return "success";
  }
  return "default";
}

/**
 * EN: Build the API payload from UI filter state.
 * RU: Собирает API-payload из состояния фильтров UI.
 */
function buildLogQuery(filters: LogFilters, cursor?: string | null) {
  return {
    service: filters.service ? [filters.service] : undefined,
    date_from: filters.date_from || undefined,
    date_to: filters.date_to || undefined,
    time_from: filters.time_from || undefined,
    time_to: filters.time_to || undefined,
    level: filters.level || undefined,
    function: filters.function || undefined,
    message: filters.message || undefined,
    error_text: filters.error_text || undefined,
    search: filters.search || undefined,
    sort: filters.sort,
    cursor: cursor || undefined,
    limit: 50,
  };
}

/**
 * EN: Logs page for cursor-based browsing, filtering, and inspection of JSONL logs.
 * RU: Страница Logs для cursor-based просмотра, фильтрации и анализа JSONL-логов.
 */
export function LogsPage() {
  const { tokens } = useAuth();
  const { t } = useI18n();
  const [services, setServices] = useState<string[]>([]);
  const [filters, setFilters] = useState<LogFilters>(() => createDefaultFilters());
  const [appliedFilters, setAppliedFilters] = useState<LogFilters>(() => createDefaultFilters());
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LogQueryResult | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<LogEntry | null>(null);

  /**
   * EN: Load the service catalog used by the service filter dropdown.
   * RU: Загружает каталог сервисов для dropdown-фильтра по сервисам.
   */
  const loadServices = useCallback(async () => {
    if (!tokens) {
      setServices([]);
      return;
    }
    try {
      const nextServices = await api.listLogServices(tokens.access_token);
      setServices(nextServices);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : t("api.errors.request"));
    }
  }, [t, tokens]);

  /**
   * EN: Fetch one cursor page from the backend gateway and optionally append it.
   * RU: Загружает одну cursor-страницу из backend gateway и при необходимости добавляет её к текущему списку.
   */
  const loadLogs = useCallback(
    async (queryFilters: LogFilters, cursor?: string | null, append = false) => {
      if (!tokens) {
        setResult(null);
        return;
      }
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }
      try {
        const payload = await api.listLogs(tokens.access_token, buildLogQuery(queryFilters, cursor));
        setError(null);
        setServices((current) => (current.length > 0 ? current : payload.available_services));
        setResult((current) => {
          if (!append || !current) {
            return payload;
          }
          return {
            ...payload,
            items: [...current.items, ...payload.items],
          };
        });
      } catch (nextError) {
        setError(nextError instanceof Error ? nextError.message : t("api.errors.request"));
      } finally {
        setLoading(false);
        setLoadingMore(false);
      }
    },
    [t, tokens],
  );

  useEffect(() => {
    void loadServices();
  }, [loadServices]);

  useEffect(() => {
    void loadLogs(appliedFilters, undefined, false);
  }, [appliedFilters, loadLogs]);

  /**
   * EN: Apply the current filter draft and reset the cursor stream.
   * RU: Применяет текущий черновик фильтров и сбрасывает cursor-поток.
   */
  const onApplyFilters = () => {
    const nextFilters = { ...filters };
    setAppliedFilters(nextFilters);
  };

  /**
   * EN: Reset filters to defaults and reload the first cursor page.
   * RU: Сбрасывает фильтры к значениям по умолчанию и заново загружает первую cursor-страницу.
   */
  const onResetFilters = () => {
    const nextFilters = createDefaultFilters();
    setFilters(nextFilters);
    setAppliedFilters(nextFilters);
  };

  /**
   * EN: Request the next cursor page and append it to the existing list.
   * RU: Запрашивает следующую cursor-страницу и добавляет её к текущему списку.
   */
  const onLoadMore = () => {
    if (!result?.has_more || !result.next_cursor || loadingMore) {
      return;
    }
    void loadLogs(appliedFilters, result.next_cursor, true);
  };

  const invalidRowsShown = useMemo(() => result?.items.filter((item) => !item.is_valid_json).length ?? 0, [result]);

  return (
    <Stack spacing={3} sx={{ width: "100%" }}>
      <SectionCard title={t("logs.filters.title")} subtitle={t("logs.filters.subtitle")}>
        <Stack sx={formStackSx}>
          {error ? <Alert severity="error">{error}</Alert> : null}
          <GridFilters filters={filters} services={services} onChange={setFilters} t={t} />
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.2} sx={formActionSx}>
            <Button variant="contained" onClick={onApplyFilters}>
              {t("logs.filters.apply")}
            </Button>
            <Button variant="outlined" onClick={onResetFilters}>
              {t("logs.filters.reset")}
            </Button>
          </Stack>
        </Stack>
      </SectionCard>

      <SectionCard
        title={t("logs.list.title")}
        subtitle={t("logs.list.subtitle", {
          visible: result?.items.length ?? 0,
          invalid: invalidRowsShown,
        })}
      >
        {loading ? <Typography color="text.secondary">{t("logs.list.loading")}</Typography> : null}
        <Box sx={logsStreamViewportSx}>
          <Box sx={tableShellSx}>
            {(result?.items ?? []).map((entry) => (
              <Box
                key={entry.id}
                sx={{
                  ...tableRowSx,
                  gridTemplateColumns: { xs: "1fr", xl: "minmax(0, 1.2fr) minmax(0, 1.6fr) auto" },
                  borderLeft:
                    entry.level.toLowerCase() === "error"
                      ? "3px solid rgba(244, 67, 54, 0.8)"
                      : entry.level.toLowerCase() === "warning"
                        ? "3px solid rgba(255, 167, 38, 0.85)"
                        : "3px solid transparent",
                }}
              >
                <Stack spacing={0.8} sx={{ minWidth: 0 }}>
                  <Typography variant="body2" color="text.secondary">
                    {formatTimestamp(entry.timestamp)}
                  </Typography>
                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                    <Chip label={entry.service} size="small" />
                    <Chip label={entry.level} size="small" color={getLevelColor(entry.level)} />
                    {!entry.is_valid_json ? <Chip label={t("logs.list.invalid")} size="small" color="warning" /> : null}
                  </Stack>
                </Stack>
                <Stack spacing={0.7} sx={{ minWidth: 0 }}>
                  <Typography variant="h6" sx={noWrapSx}>
                    {entry.function}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {entry.message}
                  </Typography>
                  {entry.error ? (
                    <Typography variant="caption" color="warning.main" sx={noWrapSx}>
                      {typeof entry.error === "string" ? entry.error : formatJson(entry.error)}
                    </Typography>
                  ) : null}
                </Stack>
                <Button variant="outlined" onClick={() => setSelectedEntry(entry)}>
                  {t("logs.list.details")}
                </Button>
              </Box>
            ))}
          </Box>

          {result && result.items.length === 0 && !loading ? (
            <Typography color="text.secondary" sx={{ mt: 2 }}>
              {t("logs.list.empty")}
            </Typography>
          ) : null}
        </Box>

        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1.2}
          justifyContent="space-between"
          alignItems={{ xs: "stretch", sm: "center" }}
          sx={{ mt: 2 }}
        >
          <Typography variant="body2" color="text.secondary">
            {t("logs.list.visibleSummary", { count: result?.items.length ?? 0 })}
          </Typography>
          {result?.has_more ? (
            <Button variant="outlined" onClick={onLoadMore} disabled={loadingMore}>
              {loadingMore ? t("logs.list.loadingMore") : t("logs.list.loadMore")}
            </Button>
          ) : result?.items.length ? (
            <Typography variant="body2" color="text.secondary">
              {t("logs.list.endOfStream")}
            </Typography>
          ) : null}
        </Stack>
      </SectionCard>

      <Dialog open={Boolean(selectedEntry)} onClose={() => setSelectedEntry(null)} fullWidth maxWidth="md">
        <DialogTitle>{t("logs.details.title")}</DialogTitle>
        <DialogContent>
          {selectedEntry ? (
            <Stack spacing={2}>
              <Typography variant="body2" color="text.secondary">
                {selectedEntry.source_file}:{selectedEntry.line_number}
              </Typography>
              <TextField label={t("logs.fields.timestamp")} value={formatTimestamp(selectedEntry.timestamp)} fullWidth InputProps={{ readOnly: true }} />
              <TextField label={t("logs.fields.service")} value={selectedEntry.service} fullWidth InputProps={{ readOnly: true }} />
              <TextField label={t("logs.fields.level")} value={selectedEntry.level} fullWidth InputProps={{ readOnly: true }} />
              <TextField label={t("logs.fields.function")} value={selectedEntry.function} fullWidth InputProps={{ readOnly: true }} />
              <TextField label={t("logs.fields.message")} value={selectedEntry.message} fullWidth multiline minRows={2} InputProps={{ readOnly: true }} />
              <TextField label={t("logs.fields.request")} value={formatJson(selectedEntry.request)} fullWidth multiline minRows={4} InputProps={{ readOnly: true }} />
              <TextField
                label={t("logs.fields.context")}
                value={formatJson(selectedEntry.context)}
                fullWidth
                multiline
                minRows={4}
                InputProps={{ readOnly: true }}
              />
              <TextField label={t("logs.fields.error")} value={formatJson(selectedEntry.error)} fullWidth multiline minRows={4} InputProps={{ readOnly: true }} />
              {selectedEntry.raw_line ? (
                <TextField label={t("logs.fields.rawLine")} value={selectedEntry.raw_line} fullWidth multiline minRows={3} InputProps={{ readOnly: true }} />
              ) : null}
            </Stack>
          ) : null}
        </DialogContent>
      </Dialog>
    </Stack>
  );
}

/**
 * EN: Render the filter form shared by the log browsing page.
 * RU: Отрисовывает форму фильтров, используемую страницей просмотра логов.
 */
function GridFilters({
  filters,
  services,
  onChange,
  t,
}: {
  filters: LogFilters;
  services: string[];
  onChange: (nextValue: LogFilters) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}) {
  return (
    <Box sx={logsFilterGridSx}>
      <TextField select label={t("logs.fields.service")} value={filters.service} onChange={(event) => onChange({ ...filters, service: event.target.value })}>
        <MenuItem value="">{t("logs.filters.allServices")}</MenuItem>
        {services.map((service) => (
          <MenuItem key={service} value={service}>
            {service}
          </MenuItem>
        ))}
      </TextField>
      <TextField select label={t("logs.fields.level")} value={filters.level} onChange={(event) => onChange({ ...filters, level: event.target.value })}>
        <MenuItem value="">{t("logs.filters.allLevels")}</MenuItem>
        {["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].map((level) => (
          <MenuItem key={level} value={level}>
            {level}
          </MenuItem>
        ))}
      </TextField>
      <TextField label={t("logs.fields.function")} value={filters.function} onChange={(event) => onChange({ ...filters, function: event.target.value })} />
      <Box sx={logsDateTimeGroupSx}>
        <TextField
          label={t("logs.fields.dateFrom")}
          type="date"
          value={filters.date_from}
          onChange={(event) => onChange({ ...filters, date_from: event.target.value })}
          InputLabelProps={{ shrink: true }}
        />
        <TextField
          label={t("logs.fields.timeFrom")}
          type="time"
          value={filters.time_from}
          onChange={(event) => onChange({ ...filters, time_from: event.target.value })}
          InputLabelProps={{ shrink: true }}
        />
      </Box>
      <Box sx={logsDateTimeGroupSx}>
        <TextField
          label={t("logs.fields.dateTo")}
          type="date"
          value={filters.date_to}
          onChange={(event) => onChange({ ...filters, date_to: event.target.value })}
          InputLabelProps={{ shrink: true }}
        />
        <TextField
          label={t("logs.fields.timeTo")}
          type="time"
          value={filters.time_to}
          onChange={(event) => onChange({ ...filters, time_to: event.target.value })}
          InputLabelProps={{ shrink: true }}
        />
      </Box>
      <TextField select label={t("logs.fields.sort")} value={filters.sort} onChange={(event) => onChange({ ...filters, sort: event.target.value as "asc" | "desc" })}>
        <MenuItem value="desc">{t("logs.sort.desc")}</MenuItem>
        <MenuItem value="asc">{t("logs.sort.asc")}</MenuItem>
      </TextField>
    </Box>
  );
}
