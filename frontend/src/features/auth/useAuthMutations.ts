import { useMutation } from "@tanstack/react-query";

import type { LoginValues, RegisterValues } from "@/features/auth/schemas";
import { apiFetch } from "@/lib/api";
import { setTokens } from "@/lib/auth";

type TokenPair = {
  access_token: string;
  refresh_token: string;
};

export function useLogin() {
  return useMutation({
    mutationFn: (values: LoginValues) =>
      apiFetch<TokenPair>("/auth/login", { method: "POST", body: values, auth: false }),
    onSuccess: (tokens) => {
      setTokens(tokens);
    },
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: (values: RegisterValues) =>
      apiFetch<TokenPair>("/auth/register", { method: "POST", body: values, auth: false }),
    onSuccess: (tokens) => {
      setTokens(tokens);
    },
  });
}
