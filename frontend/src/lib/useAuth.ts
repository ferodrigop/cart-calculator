import { useSyncExternalStore } from "react";

import { getAccessToken, getRefreshToken, isAuthenticated, subscribe } from "@/lib/auth";

type AuthSnapshot = {
  isAuthenticated: boolean;
  hasAccessToken: boolean;
  hasRefreshToken: boolean;
};

let cached: AuthSnapshot = computeSnapshot();
let cachedAccess: string | null = getAccessToken();
let cachedRefresh: string | null = getRefreshToken();

function computeSnapshot(): AuthSnapshot {
  return {
    isAuthenticated: isAuthenticated(),
    hasAccessToken: getAccessToken() !== null,
    hasRefreshToken: getRefreshToken() !== null,
  };
}

function getSnapshot(): AuthSnapshot {
  const access = getAccessToken();
  const refresh = getRefreshToken();
  if (access !== cachedAccess || refresh !== cachedRefresh) {
    cachedAccess = access;
    cachedRefresh = refresh;
    cached = computeSnapshot();
  }
  return cached;
}

export function useAuth(): AuthSnapshot {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
