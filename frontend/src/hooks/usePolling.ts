import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useDealPolls(dealId: string) {
  return useQuery({
    queryKey: ["polls", dealId],
    queryFn: () => api.getDealPolls(dealId),
    enabled: !!dealId,
  });
}

export function usePoll(pollId: string) {
  return useQuery({
    queryKey: ["poll", pollId],
    queryFn: () => api.getPoll(pollId),
    enabled: !!pollId,
  });
}

export function useMyVote(pollId: string) {
  return useQuery({
    queryKey: ["vote", pollId],
    queryFn: () => api.getMyVote(pollId),
    enabled: !!pollId,
  });
}

export function useDivergenceView(pollId: string) {
  return useQuery({
    queryKey: ["divergence", pollId],
    queryFn: () => api.getDivergenceView(pollId),
    enabled: !!pollId,
  });
}

export function useCreatePoll() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      deal_id: string;
      title: string;
      description?: string;
      closes_at?: string;
      ic_meeting_date?: string;
      reveal_threshold?: number;
    }) => api.createPoll(data),
    onSuccess: (_, { deal_id }) => {
      queryClient.invalidateQueries({ queryKey: ["polls", deal_id] });
    },
  });
}

export function useSubmitVote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      pollId,
      data,
    }: {
      pollId: string;
      data: {
        conviction_score: number;
        red_flags?: string[];
        green_flags?: string[];
        red_flag_notes?: string;
        green_flag_notes?: string;
        private_notes?: string;
      };
    }) => api.submitVote(pollId, data),
    onSuccess: (_, { pollId }) => {
      queryClient.invalidateQueries({ queryKey: ["poll", pollId] });
      queryClient.invalidateQueries({ queryKey: ["vote", pollId] });
      queryClient.invalidateQueries({ queryKey: ["divergence", pollId] });
    },
  });
}

export function useRevealPoll() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (pollId: string) => api.revealPoll(pollId),
    onSuccess: (_, pollId) => {
      queryClient.invalidateQueries({ queryKey: ["poll", pollId] });
      queryClient.invalidateQueries({ queryKey: ["divergence", pollId] });
    },
  });
}
