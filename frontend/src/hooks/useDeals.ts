import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Deal, DealStage } from "@/types";

export function useDeals(params?: {
  stage?: DealStage;
  sector?: string;
  search?: string;
  page?: number;
  per_page?: number;
}) {
  return useQuery({
    queryKey: ["deals", params],
    queryFn: () => api.getDeals(params),
  });
}

export function useDeal(id: string) {
  return useQuery({
    queryKey: ["deal", id],
    queryFn: () => api.getDeal(id),
    enabled: !!id,
  });
}

export function useCreateDeal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Deal>) => api.createDeal(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deals"] });
    },
  });
}

export function useUpdateDeal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Deal> }) =>
      api.updateDeal(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["deals"] });
      queryClient.invalidateQueries({ queryKey: ["deal", id] });
    },
  });
}

export function useUpdateDealStage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, stage }: { id: string; stage: DealStage }) =>
      api.updateDealStage(id, stage),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["deals"] });
      queryClient.invalidateQueries({ queryKey: ["deal", id] });
    },
  });
}
