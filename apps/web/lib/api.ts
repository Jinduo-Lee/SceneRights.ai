import {
  PolicyDocument,
  PolicyRule,
  Clip,
  Scene,
  AnalysisRun,
  Finding,
  ErrorEnvelope,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const DEFAULT_DEMO_TOKEN =
  process.env.NEXT_PUBLIC_DEMO_ACCESS_TOKEN || "demo-secret-token";
export const DEFAULT_PROJECT_ID =
  process.env.NEXT_PUBLIC_DEMO_PROJECT_ID || "project_001";

async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${DEFAULT_DEMO_TOKEN}`);
  }
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    try {
      const errData: ErrorEnvelope = await response.json();
      if (errData?.error?.message) {
        throw new Error(errData.error.message);
      }
    } catch (e: any) {
      if (e instanceof Error && e.message) throw e;
    }
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response;
}

export async function uploadPolicy(
  file: File,
  projectId: string = DEFAULT_PROJECT_ID
): Promise<PolicyDocument> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/policies`,
    {
      method: "POST",
      body: formData,
    }
  );
  return res.json();
}

export async function processPolicy(
  policyId: string,
  projectId: string = DEFAULT_PROJECT_ID
): Promise<{
  policy_id: string;
  status: string;
  rules_extracted: number;
  rules: PolicyRule[];
}> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/policies/${policyId}/process`,
    {
      method: "POST",
    }
  );
  return res.json();
}

export async function getPolicies(
  projectId: string = DEFAULT_PROJECT_ID
): Promise<PolicyDocument[]> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/policies`
  );
  return res.json();
}

export async function getPolicyRules(
  policyId: string,
  projectId: string = DEFAULT_PROJECT_ID
): Promise<PolicyRule[]> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/policies/${policyId}/rules`
  );
  return res.json();
}

export async function approvePolicyRule(
  policyId: string,
  ruleId: string,
  projectId: string = DEFAULT_PROJECT_ID
): Promise<PolicyRule> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/policies/${policyId}/rules/${ruleId}/approve`,
    {
      method: "POST",
    }
  );
  return res.json();
}

export async function rejectPolicyRule(
  policyId: string,
  ruleId: string,
  projectId: string = DEFAULT_PROJECT_ID
): Promise<PolicyRule> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/policies/${policyId}/rules/${ruleId}/reject`,
    {
      method: "POST",
    }
  );
  return res.json();
}

export async function seedProject(
  projectId: string = DEFAULT_PROJECT_ID
): Promise<{ status: string }> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/seed`,
    {
      method: "POST",
    }
  );
  return res.json();
}

// Milestone 3 Video & Continuity API helpers

export async function uploadClip(
  file: File,
  sceneId: string = "scene_12",
  role: string = "comparison",
  projectId: string = DEFAULT_PROJECT_ID
): Promise<Clip> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("scene_id", sceneId);
  formData.append("role", role);

  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/clips`,
    {
      method: "POST",
      body: formData,
    }
  );
  return res.json();
}

export async function getClips(
  projectId: string = DEFAULT_PROJECT_ID
): Promise<Clip[]> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/clips`
  );
  return res.json();
}

export async function createScene(
  sceneId: string = "scene_12",
  name: string = "Scene 12",
  projectId: string = DEFAULT_PROJECT_ID
): Promise<Scene> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/scenes`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scene_id: sceneId, name }),
    }
  );
  return res.json();
}

export async function getScene(
  sceneId: string = "scene_12",
  projectId: string = DEFAULT_PROJECT_ID
): Promise<Scene> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/scenes/${sceneId}`
  );
  return res.json();
}

export async function setReferenceClip(
  sceneId: string = "scene_12",
  referenceClipId: string,
  projectId: string = DEFAULT_PROJECT_ID
): Promise<Scene> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/scenes/${sceneId}/reference`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reference_clip_id: referenceClipId }),
    }
  );
  return res.json();
}

export async function analyzeScene(
  sceneId: string = "scene_12",
  comparisonClipId: string = "take_b",
  idempotencyKey?: string,
  projectId: string = DEFAULT_PROJECT_ID
): Promise<{ analysis_run_id: string; status: string }> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (idempotencyKey) {
    headers["Idempotency-Key"] = idempotencyKey;
  }

  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/scenes/${sceneId}/analyze`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ comparison_clip_id: comparisonClipId }),
    }
  );
  return res.json();
}

export async function getAnalysisRun(
  analysisRunId: string,
  projectId: string = DEFAULT_PROJECT_ID
): Promise<AnalysisRun> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/analysis/${analysisRunId}`
  );
  return res.json();
}

export async function getSceneFindings(
  sceneId: string = "scene_12",
  projectId: string = DEFAULT_PROJECT_ID
): Promise<Finding[]> {
  const res = await fetchWithAuth(
    `${API_BASE_URL}/api/projects/${projectId}/scenes/${sceneId}/findings`
  );
  return res.json();
}
