const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function parseResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed");
  }
  return payload;
}

export async function uploadZip(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/api/upload/zip`, {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}

export async function uploadGitHub(repoUrl, branch) {
  const response = await fetch(`${API_BASE_URL}/api/upload/github`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl, branch: branch || null }),
  });
  return parseResponse(response);
}

export async function askCodebase(projectId, question, topK = 6) {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, question, top_k: topK }),
  });
  return parseResponse(response);
}

export async function debugCodebase(projectId, errorMessage, stackTrace, topK = 8) {
  const response = await fetch(`${API_BASE_URL}/api/debug`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: projectId,
      error_message: errorMessage,
      stack_trace: stackTrace || null,
      top_k: topK,
    }),
  });
  return parseResponse(response);
}
