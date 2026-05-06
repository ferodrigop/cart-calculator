export const authKeys = {
  all: ["auth"] as const,
  me: () => [...authKeys.all, "me"] as const,
};

export const checkoutKeys = {
  all: ["checkout"] as const,
  last: () => [...checkoutKeys.all, "last"] as const,
};
