const API_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options) {
  const response = await fetch(`${API_URL}${path}`, options);
  const body = await response.json();

  if (!response.ok) {
    const detail = Array.isArray(body.detail)
      ? body.detail.map((error) => error.msg).join(", ")
      : body.detail;
    throw new Error(detail || "Request failed");
  }

  return body;
}

export function extractContract(text) {
  return request("/api/v1/extract", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export const listContracts = () => request("/api/v1/contracts");
export const getContract = (id) => request(`/api/v1/contracts/${id}`);
