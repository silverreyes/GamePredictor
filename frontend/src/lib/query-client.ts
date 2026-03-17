import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes per UI-SPEC
      refetchOnWindowFocus: false, // per UI-SPEC
      retry: 2, // per UI-SPEC
    },
  },
});
