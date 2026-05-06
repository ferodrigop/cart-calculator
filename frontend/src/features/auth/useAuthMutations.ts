import { useMutation } from "@tanstack/react-query";

import type { LoginValues, RegisterValues } from "@/features/auth/schemas";
import { apiFetch } from "@/lib/api";
import { setTokens } from "@/lib/auth";

type TokenPair = {
  access_token: string;
  refresh_token: string;
};

type RegisterResponse = {
  id: string;
  email: string;
  created_at: string;
};

function loginRequest(email: string, password: string): Promise<TokenPair> {
  // /auth/login uses OAuth2 password flow → form-encoded body with `username`.
  const body = new URLSearchParams({ username: email, password });
  return apiFetch<TokenPair>("/auth/login", { method: "POST", body, auth: false });
}

export function useLogin() {
  return useMutation({
    mutationFn: ({ email, password }: LoginValues) => loginRequest(email, password),
    onSuccess: (tokens) => {
      setTokens(tokens);
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: async ({ email, password }: RegisterValues) => {
      await apiFetch<RegisterResponse>("/auth/register", {
        method: "POST",
        body: { email, password },
        auth: false,
      });
      return loginRequest(email, password);
    },
    onSuccess: (tokens) => {
      setTokens(tokens);
    },
  });
}
