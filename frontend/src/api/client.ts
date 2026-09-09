import type { AskResponse, DailyBrief, IntelligenceSearchResponse, Recommendation, User, UserProfile } from "../types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function request<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new ApiError("The NEXUS backend is unavailable. It may be starting from a free-tier cold start.", 0);
  }
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail || body);
    } catch {
      // Keep the status-based message when the response is not JSON.
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function download(path: string, token: string, fallbackName: string) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    let message = `Download failed with status ${response.status}`;
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : message;
    } catch {
      // Keep the status-based message when the response is not JSON.
    }
    throw new ApiError(message, response.status);
  }
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^";]+)"?/i);
  const filename = match?.[1] || fallbackName;
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    return request<{ access_token: string; token_type: string }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
  },
  register: (payload: { name: string; email: string; age: number; password: string }) =>
    request<User>("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  me: (token: string) => request<User>("/auth/me", {}, token),
  dailyBrief: (token: string) => request<DailyBrief>("/intelligence/daily-brief", {}, token),
  recommendations: (token: string) =>
    request<{ generated_for: string; recommendations: Recommendation[] }>("/intelligence/recommendations", {}, token),
  ask: (token: string, message: string) =>
    request<AskResponse>("/intelligence/ask", { method: "POST", body: JSON.stringify({ message }) }, token),
  search: (token: string, query: string, limit = 30) =>
    request<IntelligenceSearchResponse>(`/intelligence/search?q=${encodeURIComponent(query)}&limit=${limit}`, {}, token),
  profile: (token: string) => request<UserProfile>("/profile/me", {}, token),
  updateProfile: (token: string, payload: Partial<Omit<UserProfile, "id" | "user_id" | "created_at" | "updated_at">>) =>
    request<UserProfile>("/profile/me", { method: "PATCH", body: JSON.stringify(payload) }, token),
};

export { API_BASE_URL };
