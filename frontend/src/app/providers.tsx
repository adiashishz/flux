import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { TooltipProvider } from "@/components/ui/tooltip"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 min — single user, data only changes when you change it
      gcTime: 10 * 60 * 1000,         // 10 min — keep in memory for smooth back-navigation
      refetchOnWindowFocus: false,     // don't re-fetch when switching tabs (common while writing)
      retry: 1,                        // fail fast, don't hammer the API on errors
    },
  },
})

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        {children}
      </TooltipProvider>
    </QueryClientProvider>
  )
}
