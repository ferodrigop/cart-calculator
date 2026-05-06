const REFRESH_KEY = "cc.refresh";

let accessToken: string | null = null;
const listeners = new Set<() => void>();

function notify(): void {
  for (const listener of listeners) listener();
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
  notify();
}

export function getRefreshToken(): string | null {
  try {
    return sessionStorage.getItem(REFRESH_KEY);
  } catch {
    return null;
  }
}

export function setRefreshToken(token: string | null): void {
  try {
    if (token === null) sessionStorage.removeItem(REFRESH_KEY);
    else sessionStorage.setItem(REFRESH_KEY, token);
  } catch {
    // sessionStorage may be unavailable (private mode); fail silently.
  }
  notify();
}

export function setTokens(tokens: { access_token: string; refresh_token: string }): void {
  accessToken = tokens.access_token;
  try {
    sessionStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  } catch {
    // ignore
  }
  notify();
}

export function clearTokens(): void {
  accessToken = null;
  try {
    sessionStorage.removeItem(REFRESH_KEY);
  } catch {
    // ignore
  }
  notify();
}

export function isAuthenticated(): boolean {
  return accessToken !== null || getRefreshToken() !== null;
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
