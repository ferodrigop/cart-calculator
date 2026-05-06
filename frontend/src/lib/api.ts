import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/auth";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

type RefreshResponse = {
  access_token: string;
  refresh_token: string;
};

let refreshInFlight: Promise<string | null> | null = null;

async function performRefresh(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });

  if (!res.ok) {
    clearTokens();
    return null;
  }

  const data = (await res.json()) as RefreshResponse;
  setTokens(data);
  return data.access_token;
}

function refreshAccessToken(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = performRefresh().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

type ApiFetchOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  auth?: boolean;
};

async function send(path: string, options: ApiFetchOptions, token: string | null): Promise<Response> {
  const headers = new Headers(options.headers);
  const isForm = options.body instanceof URLSearchParams;
  if (options.body !== undefined && !isForm && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  if (token && options.auth !== false) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let body: BodyInit | undefined;
  if (options.body === undefined) {
    body = undefined;
  } else if (isForm) {
    body = options.body as URLSearchParams;
  } else {
    body = JSON.stringify(options.body);
  }

  return fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body,
  });
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  let res = await send(path, options, getAccessToken());

  if (res.status === 401 && options.auth !== false && getRefreshToken()) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await send(path, options, newToken);
    }
  }

  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      // non-JSON error body — ignore
    }
    if (res.status === 401) {
      clearTokens();
    }
    const message =
      (body && typeof body === "object" && "detail" in body && typeof body.detail === "string"
        ? body.detail
        : null) ?? res.statusText ?? `HTTP ${res.status}`;
    throw new ApiError(res.status, message, body);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
