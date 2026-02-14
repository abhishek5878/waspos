import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useDealMemos(dealId: string) {
  return useQuery({
    queryKey: ["memos", dealId],
    queryFn: () => api.getDealMemos(dealId),
    enabled: !!dealId,
  });
}

export function useMemo(memoId: string) {
  return useQuery({
    queryKey: ["memo", memoId],
    queryFn: () => api.getMemo(memoId),
    enabled: !!memoId,
  });
}

export function useGenerateMemo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: {
      deal_id: string;
      template_id?: string;
      additional_context?: string;
      check_contradictions?: boolean;
    }) => api.generateMemo(request),
    onSuccess: (_, { deal_id }) => {
      queryClient.invalidateQueries({ queryKey: ["memos", deal_id] });
    },
  });
}
