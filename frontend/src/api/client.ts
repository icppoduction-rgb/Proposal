import { translateApiErrorMessage } from "../i18n";
import type {
  ArchiveFile,
  ArchiveUploadCompleteResult,
  AutoTrainingJob,
  Dataset,
  DatasetManifest,
  DetectionResult,
  EditorPage,
  EditorSaveResult,
  EditorSession,
  ExplanationJob,
  ExplanationResult,
  FeatureSchema,
  LogQueryParams,
  LogQueryResult,
  InferenceJob,
  ManagedDataset,
  ModelArtifact,
  RawFile,
  RawDatasetInspectResult,
  TaskRecord,
  TokenPair,
  TrainingRun,
  UploadChunkResult,
  UploadCompleteResult,
  UploadSession,
  User,
  UserCreatePayload,
  UserUpdatePayload,
} from "../types/api";

const API_BASE = "/api";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

async function readErrorMessage(response: Response): Promise<string> {
  const text = await response.text();

  try {
    const payload = JSON.parse(text) as { detail?: string; message?: string } | string;
    if (typeof payload === "string") {
      return payload;
    }
    if (typeof payload.detail === "string") {
      return payload.detail;
    }
    if (typeof payload.message === "string") {
      return payload.message;
    }
  } catch {
    return text;
  }

  return text;
}

async function request<T>(
  path: string,
  method: HttpMethod,
  accessToken?: string | null,
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(translateApiErrorMessage(message, response.status));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

function buildQueryString(params: Record<string, string | number | string[] | undefined>): string {
  /**
   * EN: Serialize query parameters while preserving repeated keys for arrays.
   * RU: Сериализует query-параметры, сохраняя повторяющиеся ключи для массивов.
   */

  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === "") {
      return;
    }
    if (Array.isArray(value)) {
      value.filter(Boolean).forEach((item) => query.append(key, item));
      return;
    }
    query.set(key, String(value));
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export const api = {
  login(email: string, password: string) {
    return request<TokenPair>("/auth/login", "POST", undefined, { email, password });
  },
  refresh(refreshToken: string) {
    return request<TokenPair>(`/auth/refresh?refresh_token=${encodeURIComponent(refreshToken)}`, "POST");
  },
  logout(refreshToken: string) {
    return request<{ message: string }>(`/auth/logout?refresh_token=${encodeURIComponent(refreshToken)}`, "POST");
  },
  me(token: string) {
    return request<User>("/auth/me", "GET", token);
  },
  listUsers(token: string) {
    return request<User[]>("/users", "GET", token);
  },
  createUser(token: string, payload: UserCreatePayload) {
    return request<User>("/users", "POST", token, payload);
  },
  updateUser(token: string, userId: string, payload: UserUpdatePayload) {
    return request<User>(`/users/${encodeURIComponent(userId)}`, "PUT", token, payload);
  },
  deleteUser(token: string, userId: string) {
    return request<{ message: string }>(`/users/${encodeURIComponent(userId)}`, "DELETE", token);
  },
  listDatasets(token: string) {
    return request<Dataset[]>("/datasets", "GET", token);
  },
  listManagedDatasets(token: string) {
    return request<ManagedDataset[]>("/datasets/management", "GET", token);
  },
  listAutoTrainingArchives(token: string) {
    return request<ArchiveFile[]>("/auto-training/archives", "GET", token);
  },
  createAutoTrainingUploadSession(
    token: string,
    payload: { files: { relative_path: string; size_bytes: number; content_type?: string | null }[] },
  ) {
    return request<UploadSession>("/auto-training/uploads/sessions", "POST", token, payload);
  },
  uploadAutoTrainingArchiveChunk(
    token: string,
    sessionId: string,
    fileId: string,
    chunk: Blob,
    offset: number,
    chunkLength: number,
    onProgress?: (loadedBytes: number) => void,
  ) {
    return new Promise<UploadChunkResult>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("PUT", `${API_BASE}/auto-training/uploads/sessions/${encodeURIComponent(sessionId)}/files/${encodeURIComponent(fileId)}`);
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.setRequestHeader("Content-Type", "application/octet-stream");
      xhr.setRequestHeader("X-Chunk-Offset", String(offset));
      xhr.setRequestHeader("X-Chunk-Length", String(chunkLength));

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          onProgress?.(event.loaded);
        }
      };

      xhr.onerror = () => reject(new Error(translateApiErrorMessage("Request failed")));
      xhr.onload = async () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText) as UploadChunkResult);
          return;
        }

        const message = await readErrorMessage(
          new Response(xhr.responseText, {
            status: xhr.status,
            headers: { "Content-Type": xhr.getResponseHeader("Content-Type") ?? "text/plain" },
          }),
        );
        reject(new Error(translateApiErrorMessage(message, xhr.status)));
      };

      xhr.send(chunk);
    });
  },
  completeAutoTrainingUploadSession(token: string, sessionId: string) {
    return request<ArchiveUploadCompleteResult>(`/auto-training/uploads/sessions/${encodeURIComponent(sessionId)}/complete`, "POST", token);
  },
  discardAutoTrainingUploadSession(token: string, sessionId: string) {
    return request<void>(`/auto-training/uploads/sessions/${encodeURIComponent(sessionId)}`, "DELETE", token);
  },
  deleteAutoTrainingArchive(token: string, archiveId: string) {
    return request<{ message: string }>(`/auto-training/archives/${encodeURIComponent(archiveId)}`, "DELETE", token);
  },
  deleteAllAutoTrainingArchives(token: string) {
    return request<{ message: string }>("/auto-training/archives", "DELETE", token);
  },
  listAutoTrainingJobs(token: string) {
    return request<AutoTrainingJob[]>("/auto-training/jobs", "GET", token);
  },
  startAutoTrainingJob(token: string, payload?: { archive_ids?: string[] }) {
    return request<AutoTrainingJob>("/auto-training/jobs", "POST", token, payload ?? {});
  },
  listRawDatasetFiles(token: string) {
    return request<RawFile[]>("/datasets/raw-files", "GET", token);
  },
  inspectRawDatasetFile(token: string, relativePath: string) {
    return request<RawDatasetInspectResult>("/datasets/raw-files/inspect", "POST", token, { relative_path: relativePath });
  },
  deleteRawDatasetFile(token: string, rawFileId: string) {
    return request<{ message: string }>(`/datasets/raw-files/${encodeURIComponent(rawFileId)}`, "DELETE", token);
  },
  deleteAllRawDatasetFiles(token: string) {
    return request<{ message: string }>("/datasets/raw-files", "DELETE", token);
  },
  registerDataset(token: string, payload: DatasetManifest) {
    return request<Dataset>("/datasets/register", "POST", token, payload);
  },
  registerManagedDataset(token: string, payload: { name: string; raw_file_id: string; feature_set: string[] }) {
    return request<ManagedDataset>("/datasets/management", "POST", token, payload);
  },
  validateManagedDataset(token: string, datasetId: string) {
    return request<TaskRecord>(`/datasets/management/${encodeURIComponent(datasetId)}/validate`, "POST", token);
  },
  deleteManagedDataset(token: string, datasetId: string) {
    return request<{ message: string }>(`/datasets/management/${encodeURIComponent(datasetId)}`, "DELETE", token);
  },
  deleteAllManagedDatasets(token: string) {
    return request<{ message: string }>("/datasets/management", "DELETE", token);
  },
  createDatasetUploadSession(
    token: string,
    payload: { files: { relative_path: string; size_bytes: number; content_type?: string | null }[] },
  ) {
    return request<UploadSession>("/datasets/uploads/sessions", "POST", token, payload);
  },
  uploadDatasetChunk(
    token: string,
    sessionId: string,
    fileId: string,
    chunk: Blob,
    offset: number,
    chunkLength: number,
    onProgress?: (loadedBytes: number) => void,
  ) {
    return new Promise<UploadChunkResult>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("PUT", `${API_BASE}/datasets/uploads/sessions/${encodeURIComponent(sessionId)}/files/${encodeURIComponent(fileId)}`);
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.setRequestHeader("Content-Type", "application/octet-stream");
      xhr.setRequestHeader("X-Chunk-Offset", String(offset));
      xhr.setRequestHeader("X-Chunk-Length", String(chunkLength));

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          onProgress?.(event.loaded);
        }
      };

      xhr.onerror = () => reject(new Error(translateApiErrorMessage("Request failed")));
      xhr.onload = async () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText) as UploadChunkResult);
          return;
        }

        const message = await readErrorMessage(
          new Response(xhr.responseText, {
            status: xhr.status,
            headers: { "Content-Type": xhr.getResponseHeader("Content-Type") ?? "text/plain" },
          }),
        );
        reject(new Error(translateApiErrorMessage(message, xhr.status)));
      };

      xhr.send(chunk);
    });
  },
  completeDatasetUploadSession(token: string, sessionId: string) {
    return request<UploadCompleteResult>(`/datasets/uploads/sessions/${encodeURIComponent(sessionId)}/complete`, "POST", token);
  },
  discardDatasetUploadSession(token: string, sessionId: string) {
    return request<void>(`/datasets/uploads/sessions/${encodeURIComponent(sessionId)}`, "DELETE", token);
  },
  createRawFileEditorSession(token: string, rawFileId: string, payload?: { page_size?: number; sheet_name?: string | null }) {
    return request<EditorSession>(`/datasets/raw-files/${encodeURIComponent(rawFileId)}/editor-sessions`, "POST", token, payload ?? {});
  },
  getRawFileEditorPage(token: string, rawFileId: string, sessionId: string, params?: { page?: number; sheet_name?: string | null }) {
    const query = buildQueryString({
      page: params?.page ?? 1,
      sheet_name: params?.sheet_name ?? undefined,
    });
    return request<EditorPage>(
      `/datasets/raw-files/${encodeURIComponent(rawFileId)}/editor-sessions/${encodeURIComponent(sessionId)}${query}`,
      "GET",
      token,
    );
  },
  patchRawFileEditorCells(
    token: string,
    rawFileId: string,
    sessionId: string,
    payload: { patches: { row_index: number; column: string; value: unknown }[] },
  ) {
    return request<EditorSession>(
      `/datasets/raw-files/${encodeURIComponent(rawFileId)}/editor-sessions/${encodeURIComponent(sessionId)}/cells`,
      "PATCH",
      token,
      payload,
    );
  },
  deleteRawFileEditorRows(token: string, rawFileId: string, sessionId: string, payload: { row_indices: number[] }) {
    return request<EditorSession>(
      `/datasets/raw-files/${encodeURIComponent(rawFileId)}/editor-sessions/${encodeURIComponent(sessionId)}/rows/delete`,
      "POST",
      token,
      payload,
    );
  },
  deleteRawFileEditorColumns(token: string, rawFileId: string, sessionId: string, payload: { columns: string[] }) {
    return request<EditorSession>(
      `/datasets/raw-files/${encodeURIComponent(rawFileId)}/editor-sessions/${encodeURIComponent(sessionId)}/columns/delete`,
      "POST",
      token,
      payload,
    );
  },
  saveRawFileEditorSession(token: string, rawFileId: string, sessionId: string) {
    return request<EditorSaveResult>(
      `/datasets/raw-files/${encodeURIComponent(rawFileId)}/editor-sessions/${encodeURIComponent(sessionId)}/save`,
      "POST",
      token,
    );
  },
  discardRawFileEditorSession(token: string, rawFileId: string, sessionId: string) {
    return request<void>(
      `/datasets/raw-files/${encodeURIComponent(rawFileId)}/editor-sessions/${encodeURIComponent(sessionId)}`,
      "DELETE",
      token,
    );
  },
  validateDataset(token: string, datasetId: string) {
    return request<TaskRecord>(`/datasets/${datasetId}/validate`, "POST", token);
  },
  listFeatureSchemas(token: string) {
    return request<FeatureSchema[]>("/feature-schemas", "GET", token);
  },
  createFeatureSchema(token: string, payload: Record<string, unknown>) {
    return request<FeatureSchema>("/feature-schemas", "POST", token, payload);
  },
  listTrainingRuns(token: string) {
    return request<TrainingRun[]>("/training-runs", "GET", token);
  },
  createTrainingRun(token: string, payload: Record<string, unknown>) {
    return request<TrainingRun>("/training-runs", "POST", token, payload);
  },
  listModels(token: string) {
    return request<ModelArtifact[]>("/models", "GET", token);
  },
  promoteModel(token: string, artifactId: string) {
    return request<ModelArtifact>(`/models/${artifactId}/promote`, "POST", token);
  },
  listInferenceJobs(token: string) {
    return request<InferenceJob[]>("/inference-jobs", "GET", token);
  },
  createInferenceJob(token: string, payload: Record<string, unknown>) {
    return request<InferenceJob>("/inference-jobs", "POST", token, payload);
  },
  getInferenceResults(token: string, jobId: string) {
    return request<DetectionResult[]>(`/inference-jobs/${jobId}/results`, "GET", token);
  },
  listExplanationJobs(token: string) {
    return request<ExplanationJob[]>("/explanations", "GET", token);
  },
  requestExplanation(token: string, payload: Record<string, unknown>) {
    return request<ExplanationJob>("/explanations", "POST", token, payload);
  },
  getExplanationResult(token: string, jobId: string) {
    return request<ExplanationResult>(`/explanations/${jobId}/result`, "GET", token);
  },
  listTasks(token: string) {
    return request<TaskRecord[]>("/tasks", "GET", token);
  },
  listLogServices(token: string) {
    /**
     * EN: Load the service catalog used by the Logs filter form.
     * RU: Загружает каталог сервисов для формы фильтрации Logs.
     */
    return request<string[]>("/logs/services", "GET", token);
  },
  listLogs(token: string, params: LogQueryParams) {
    /**
     * EN: Fetch one cursor page of structured logs through the backend gateway.
     * RU: Получает одну cursor-страницу структурированных логов через backend gateway.
     */
    const query = buildQueryString({
      service: params.service,
      date_from: params.date_from,
      date_to: params.date_to,
      time_from: params.time_from,
      time_to: params.time_to,
      level: params.level,
      function: params.function,
      message: params.message,
      error_text: params.error_text,
      search: params.search,
      sort: params.sort,
      cursor: params.cursor,
      limit: params.limit,
    });
    return request<LogQueryResult>(`/logs${query}`, "GET", token);
  },
  getHealth(token: string) {
    return request<{ status: string }>("/health/ready", "GET", token);
  },
};
