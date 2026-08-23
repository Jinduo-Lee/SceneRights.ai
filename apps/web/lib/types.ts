export type AIAssessment =
  | "present"
  | "absent"
  | "not_visible"
  | "changed"
  | "uncertain";

export type ReviewStatus =
  | "open"
  | "confirmed"
  | "not_issue"
  | "escalated"
  | "resolved";

export type ModelAssessment = "clear" | "likely" | "uncertain";

export type Priority = "high" | "medium" | "low";

export type Severity = "high" | "medium" | "low";

export type PolicyRuleStatus = "extracted" | "approved" | "rejected";

export type PolicyDocumentStatus =
  | "uploaded"
  | "processing"
  | "ready"
  | "failed";

export type AnalysisRunStatus = "queued" | "running" | "succeeded" | "failed";

export type ClipRole = "reference" | "comparison";

export type FindingType = "continuity" | "visual_review";

export type ErrorCode =
  | "UPLOAD_FAILED"
  | "PARSE_FAILED"
  | "GEMINI_TIMEOUT"
  | "INVALID_GEMINI_OUTPUT"
  | "MEDIA_PROCESSING_FAILED"
  | "MCP_UNAVAILABLE"
  | "QUERY_REJECTED"
  | "UNAUTHORIZED"
  | "NOT_FOUND"
  | "INVALID_TRANSITION";

export interface Project {
  project_id: string;
  name: string;
  status: string;
  created_at: string;
}

export interface PolicyDocument {
  project_id: string;
  policy_id: string;
  filename: string;
  gcs_uri: string;
  status: PolicyDocumentStatus;
  created_at: string;
  updated_at: string;
}

export interface PolicyRule {
  project_id: string;
  policy_id: string;
  policy_rule_id: string;
  document_name: string;
  policy_type: string;
  rule_text: string;
  source_quote: string;
  priority: Priority;
  status: PolicyRuleStatus;
  version: number;
  effective_date?: string | null;
  created_at: string;
}

export interface Scene {
  project_id: string;
  scene_id: string;
  name: string;
  reference_clip_id?: string | null;
  created_at: string;
}

export interface Clip {
  project_id: string;
  clip_id: string;
  scene_id: string;
  role: ClipRole;
  gcs_uri: string;
  created_at: string;
}

export interface AnalysisRun {
  project_id: string;
  scene_id: string;
  analysis_run_id: string;
  status: AnalysisRunStatus;
  step: string;
  error_code?: string | null;
  started_at: string;
  completed_at?: string | null;
  findings_count?: number | null;
}

export interface Finding {
  project_id: string;
  scene_id: string;
  finding_id: string;
  analysis_run_id: string;
  finding_type: FindingType;
  object_type: string;
  object_label: string;
  reference_clip: string;
  comparison_clip: string;
  ai_assessment: AIAssessment;
  model_assessment: ModelAssessment;
  severity: Severity;
  policy_rule_id: string;
  policy_rule_version: number;
  policy_document: string;
  policy_rule: string;
  source_quote: string;
  timestamp_ms: number;
  created_at: string;
  review_status: ReviewStatus;
}

export interface Decision {
  project_id: string;
  finding_id: string;
  review_status: ReviewStatus;
  previous_status: ReviewStatus;
  reviewer: string;
  comment?: string | null;
  created_at: string;
}

export interface ToolCallSummary {
  tool: string;
  sql_summary: string;
  row_count: number;
  latency_ms: number;
  status: string;
}

export interface AgentQueryRequest {
  project_id: string;
  scene_id: string;
  message: string;
}

export interface AgentQueryResponse {
  answer: string;
  tool_calls: ToolCallSummary[];
}

export interface ErrorDetail {
  code: ErrorCode;
  message: string;
  retryable: boolean;
  details?: Record<string, unknown>;
}

export interface ErrorEnvelope {
  error: ErrorDetail;
}
