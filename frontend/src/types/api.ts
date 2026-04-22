export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  is_active: boolean;
  role_name: string;
  session_status: "active" | "inactive";
  created_at: string;
}

export interface UserCreatePayload {
  email: string;
  password: string;
  role: string;
  full_name?: string;
  is_active: boolean;
}

export interface UserUpdatePayload {
  email?: string;
  password?: string;
  role?: string;
  full_name?: string;
  is_active?: boolean;
}

export interface DatasetManifest {
  name: string;
  source_type: "host" | "network";
  description?: string;
  file_name: string;
  required_columns: string[];
  label_column: string;
  timestamp_column: string;
  entity_id_column: string;
  attack_stage_column?: string;
  feature_families: string[];
  mitre_mapping: Record<string, string>;
  lineage: Record<string, string>;
}

export interface Dataset extends Record<string, unknown> {
  id: string;
  name: string;
  source_type: string;
  description?: string | null;
  storage_path: string;
  normalized_path?: string | null;
  detected_format?: string | null;
  normalization_profile?: string | null;
  normalization_summary: Record<string, unknown>;
  normalization_report_path?: string | null;
  validation_status: string;
  validation_errors: Record<string, unknown>;
  created_at: string;
}

export interface ManagedDataset {
  id: string;
  raw_file_id: string;
  name: string;
  file_path: string;
  feature_set: string[];
  created_at: string;
}

export interface RawFile {
  id: string;
  name: string;
  path: string;
  relative_path: string;
  size: number;
  format: string;
  modified_at?: string | null;
}

export interface ArchiveFile {
  id: string;
  name: string;
  path: string;
  relative_path: string;
  size: number;
  format: string;
  created_at?: string | null;
}

export interface RawDatasetInspectResult {
  relative_path: string;
  format: string;
  normalization_profile: string;
  columns: string[];
  suggested_name: string;
  target_columns: string[];
  quality_warnings: string[];
  supporting_only: boolean;
  compatible_feature_schemas: string[];
}

export interface UploadSessionFile {
  file_id: string;
  relative_path: string;
  size_bytes: number;
  uploaded_bytes: number;
  content_type?: string | null;
  status: string;
}

export interface UploadSession {
  session_id: string;
  status: string;
  created_at: string;
  total_size_bytes: number;
  files: UploadSessionFile[];
}

export interface UploadChunkResult {
  session_id: string;
  file_id: string;
  status: string;
  uploaded_bytes: number;
  size_bytes: number;
}

export interface UploadCompleteResult {
  session_id: string;
  status: string;
  uploaded_files: RawFile[];
  raw_files: RawFile[];
}

export interface ArchiveUploadCompleteResult {
  session_id: string;
  status: string;
  uploaded_archives: ArchiveFile[];
  archives: ArchiveFile[];
}

export interface EditorRow {
  row_index: number;
  values: Record<string, unknown>;
}

export interface EditorSession {
  session_id: string;
  file_name: string;
  file_path: string;
  dataset_format: string;
  read_only: boolean;
  page_size: number;
  total_rows: number;
  total_pages: number;
  columns: string[];
  available_sheets: string[];
  active_sheet?: string | null;
  deleted_row_count: number;
  deleted_columns: string[];
  pending_cell_count: number;
}

export interface EditorPage extends EditorSession {
  page: number;
  rows: EditorRow[];
}

export interface EditorSaveResult {
  session_id: string;
  file_path: string;
  size_bytes: number;
  modified_at: string;
  row_count: number;
  column_count: number;
}

export interface FeatureSchema {
  id: string;
  name: string;
  version: string;
  source_type: string;
  definition: Record<string, unknown>;
  created_at: string;
}

export interface TrainingRun {
  id: string;
  dataset_id: string;
  feature_schema_id: string;
  status: string;
  metrics: Record<string, number | Record<string, number>>;
  error_message?: string | null;
  created_at: string;
}

export interface ModelArtifact {
  id: string;
  training_run_id: string;
  model_name: string;
  model_type: string;
  status: string;
  metrics: Record<string, number>;
  artifact_path: string;
  artifact_metadata: Record<string, unknown>;
  created_at: string;
}

export interface InferenceJob {
  id: string;
  model_artifact_id: string;
  status: string;
  error_message?: string | null;
  created_at: string;
}

export interface DetectionResult {
  id: string;
  inference_job_id: string;
  entity_id: string;
  score: number;
  predicted_label: number;
  raw_output: Record<string, unknown>;
  created_at: string;
}

export interface ExplanationJob {
  id: string;
  model_artifact_id: string;
  detection_result_id: string;
  status: string;
  error_message?: string | null;
  created_at: string;
}

export interface ExplanationResult {
  id: string;
  explanation_job_id: string;
  payload: {
    summary: string;
    top_positive: { feature: string; contribution: number }[];
    top_negative: { feature: string; contribution: number }[];
  };
  report_path?: string | null;
  created_at: string;
}

export interface TaskRecord {
  id: string;
  task_name: string;
  object_type: string;
  object_id: string;
  status: string;
  detail: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AutoTrainingJob {
  id: string;
  requested_by_user_id?: string | null;
  source_type?: string | null;
  archive_ids: string[];
  status: string;
  progress_percent: number;
  current_step: string;
  detail: Record<string, unknown>;
  error_message?: string | null;
  dataset_id?: string | null;
  feature_schema_id?: string | null;
  training_run_ids: string[];
  model_artifact_ids: string[];
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface LogEntry {
  /**
   * EN: Structured log record returned by the backend log gateway.
   * RU: Структурированная лог-запись, возвращаемая backend log gateway.
   */
  id: string;
  timestamp?: string | null;
  service: string;
  level: string;
  function: string;
  message: string;
  request: Record<string, unknown>;
  error?: unknown;
  context: Record<string, unknown>;
  source_file: string;
  line_number: number;
  is_valid_json: boolean;
  raw_line?: string | null;
}

export interface LogQueryResult {
  /**
   * EN: Cursor page returned by the log browsing API.
   * RU: Cursor-страница, возвращаемая API просмотра логов.
   */
  items: LogEntry[];
  next_cursor?: string | null;
  has_more: boolean;
  invalid_rows_in_page: number;
  available_services: string[];
}

export interface LogQueryParams {
  /**
   * EN: Query parameters used by the frontend log browsing client.
   * RU: Query-параметры, используемые frontend-клиентом просмотра логов.
   */
  service?: string[];
  date_from?: string;
  date_to?: string;
  time_from?: string;
  time_to?: string;
  level?: string;
  function?: string;
  message?: string;
  error_text?: string;
  search?: string;
  sort?: "asc" | "desc";
  cursor?: string;
  limit?: number;
}
