import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControlLabel,
  Grid2,
  MenuItem,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { FormEvent, useCallback, useState } from "react";
import { api } from "../api/client";
import { SectionCard } from "../components/SectionCard";
import { formActionSx, formGridSx, formStackSx } from "../components/ui";
import { useAuth } from "../hooks/useAuth";
import { useI18n } from "../i18n";
import { usePolling } from "../hooks/usePolling";
import type { User, UserCreatePayload, UserUpdatePayload } from "../types/api";

const PASSWORD_MIN_LENGTH = 16;

type UserFormState = UserCreatePayload;

type UserFormErrors = Partial<Record<"email" | "password", string>>;

function createEmptyForm(): UserFormState {
  return {
    email: "",
    password: "",
    role: "analyst",
    full_name: "",
    is_active: true,
  };
}

function buildUserUpdatePayload(form: UserFormState): UserUpdatePayload {
    return {
      email: form.email,
      role: form.role,
      full_name: (form.full_name ?? "").trim(),
      is_active: form.is_active,
      ...(form.password ? { password: form.password } : {}),
    };
}

export function UsersPage() {
  const { tokens, user } = useAuth();
  const { t, tEnum } = useI18n();
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [formErrors, setFormErrors] = useState<UserFormErrors>({});
  const [payload, setPayload] = useState<UserFormState>(createEmptyForm);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  const loader = useCallback(() => {
    if (!tokens || user?.role_name !== "admin") {
      return Promise.resolve([]);
    }
    return api.listUsers(tokens.access_token);
  }, [tokens, user?.role_name, reloadKey]);

  const { data, error, loading } = usePolling(loader);
  const users = data ?? [];

  const resetForm = () => {
    setPayload(createEmptyForm());
    setEditingUser(null);
    setFormErrors({});
  };

  const validateForm = (): boolean => {
    const nextErrors: UserFormErrors = {};
    if (!payload.email.trim()) {
      nextErrors.email = t("users.validation.emailRequired");
    }
    if (!editingUser && !payload.password) {
      nextErrors.password = t("users.validation.passwordRequired");
    }
    if (payload.password && payload.password.length < PASSWORD_MIN_LENGTH) {
      nextErrors.password = t("users.validation.passwordMinLength", { count: PASSWORD_MIN_LENGTH });
    }
    setFormErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!tokens || !validateForm()) {
      return;
    }

    setSubmitting(true);
    setMessage(null);
    setErrorMessage(null);

    try {
      if (editingUser) {
        const updated = await api.updateUser(tokens.access_token, editingUser.id, buildUserUpdatePayload(payload));
        setMessage(t("users.messages.updated", { email: updated.email }));
      } else {
        const created = await api.createUser(tokens.access_token, payload);
        setMessage(t("users.messages.created", { email: created.email }));
      }
      resetForm();
      setReloadKey((value) => value + 1);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (account: User) => {
    setEditingUser(account);
    setPayload({
      email: account.email,
      password: "",
      role: account.role_name,
      full_name: account.full_name ?? "",
      is_active: account.is_active,
    });
    setFormErrors({});
    setMessage(null);
    setErrorMessage(null);
  };

  const confirmDelete = async () => {
    if (!tokens || !deleteTarget) {
      return;
    }

    setDeleting(true);
    setMessage(null);
    setErrorMessage(null);

    try {
      await api.deleteUser(tokens.access_token, deleteTarget.id);
      setMessage(t("users.messages.deleted", { email: deleteTarget.email }));
      if (editingUser?.id === deleteTarget.id) {
        resetForm();
      }
      setDeleteTarget(null);
      setReloadKey((value) => value + 1);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : t("api.errors.request"));
    } finally {
      setDeleting(false);
    }
  };

  if (user?.role_name !== "admin") {
    return <Alert severity="warning">{t("users.messages.accessDenied")}</Alert>;
  }

  return (
    <Stack spacing={3} sx={{ width: "100%" }}>
      <SectionCard
        title={editingUser ? t("users.form.editTitle") : t("users.form.title")}
        subtitle={editingUser ? t("users.form.editSubtitle") : t("users.form.subtitle")}
      >
        <Stack component="form" sx={formStackSx} onSubmit={onSubmit}>
          {message ? <Alert severity="success">{message}</Alert> : null}
          {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}
          <Grid2 container sx={formGridSx}>
            <TextField
              label={t("common.email")}
              value={payload.email}
              error={Boolean(formErrors.email)}
              helperText={formErrors.email}
              onChange={(event) => setPayload({ ...payload, email: event.target.value })}
            />
            <TextField
              label={t("users.form.fullNameLabel")}
              value={payload.full_name}
              onChange={(event) => setPayload({ ...payload, full_name: event.target.value })}
            />
          </Grid2>
          <Grid2 container sx={formGridSx}>
            <TextField
              label={t("common.password")}
              type="password"
              value={payload.password}
              error={Boolean(formErrors.password)}
              helperText={formErrors.password ?? t("users.form.passwordHint", { count: PASSWORD_MIN_LENGTH })}
              onChange={(event) => setPayload({ ...payload, password: event.target.value })}
            />
            <TextField
              select
              label={t("users.form.roleLabel")}
              value={payload.role}
              onChange={(event) => setPayload({ ...payload, role: event.target.value })}
            >
              <MenuItem value="analyst">{tEnum("common.role", "analyst")}</MenuItem>
              <MenuItem value="admin">{tEnum("common.role", "admin")}</MenuItem>
            </TextField>
          </Grid2>
          <FormControlLabel
            control={
              <Switch
                checked={payload.is_active}
                onChange={(event) => setPayload({ ...payload, is_active: event.target.checked })}
              />
            }
            label={t("users.form.isActiveLabel")}
          />
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} sx={formActionSx}>
            <Button type="submit" variant="contained" disabled={submitting}>
              {submitting ? <CircularProgress color="inherit" size={18} /> : editingUser ? t("users.form.update") : t("users.form.submit")}
            </Button>
            {editingUser ? (
              <Button type="button" variant="outlined" onClick={resetForm} disabled={submitting}>
                {t("users.form.cancelEdit")}
              </Button>
            ) : null}
          </Stack>
        </Stack>
      </SectionCard>
      <SectionCard title={t("users.list.title")} subtitle={t("users.list.subtitle")}>
        {error ? <Alert severity="error">{error}</Alert> : null}
        {loading ? (
          <Stack direction="row" spacing={1.5} alignItems="center">
            <CircularProgress size={18} />
            <Typography variant="body2" color="text.secondary">
              {t("users.list.loading")}
            </Typography>
          </Stack>
        ) : (
          <TableContainer
            sx={{
              borderRadius: 3,
              border: (theme) => `1px solid ${theme.palette.divider}`,
              maxHeight: users.length > 10 ? 560 : undefined,
              overflowY: users.length > 10 ? "auto" : "visible",
            }}
          >
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t("users.list.columns.name")}</TableCell>
                  <TableCell>{t("common.email")}</TableCell>
                  <TableCell>{t("users.list.columns.role")}</TableCell>
                  <TableCell>{t("users.list.columns.sessionStatus")}</TableCell>
                  <TableCell align="right">{t("users.list.columns.actions")}</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.length ? (
                  users.map((account) => (
                    <TableRow key={account.id} hover>
                      <TableCell>{account.full_name || t("common.na")}</TableCell>
                      <TableCell>{account.email}</TableCell>
                      <TableCell>{tEnum("common.role", account.role_name)}</TableCell>
                      <TableCell>
                        {t(account.session_status === "active" ? "common.activeState.active" : "common.activeState.inactive")}
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                          <Button size="small" variant="outlined" onClick={() => startEdit(account)}>
                            {t("users.actions.edit")}
                          </Button>
                          <Button size="small" color="error" variant="outlined" onClick={() => setDeleteTarget(account)}>
                            {t("users.actions.delete")}
                          </Button>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5}>
                      <Box sx={{ py: 2 }}>
                        <Typography variant="body2" color="text.secondary">
                          {t("users.list.empty")}
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </SectionCard>
      <Dialog open={Boolean(deleteTarget)} onClose={() => (deleting ? undefined : setDeleteTarget(null))} fullWidth maxWidth="xs">
        <DialogTitle>{t("users.deleteDialog.title")}</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {t("users.deleteDialog.description", { email: deleteTarget?.email ?? t("common.na") })}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)} disabled={deleting}>
            {t("users.deleteDialog.cancel")}
          </Button>
          <Button color="error" variant="contained" onClick={confirmDelete} disabled={deleting}>
            {deleting ? <CircularProgress color="inherit" size={18} /> : t("users.deleteDialog.confirm")}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
