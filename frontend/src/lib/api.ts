import { Deal, InvestmentMemo, ConvictionPoll, DivergenceView } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}/api/v1${endpoint}`;
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options.headers,
    };

    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API error: ${response.status}`);
    }

    return response.json();
  }

  // Deals
  async getDeals(params?: {
    stage?: string;
    sector?: string;
    search?: string;
    page?: number;
    per_page?: number;
  }): Promise<{ deals: Deal[]; total: number; page: number; per_page: number; total_pages: number }> {
    const searchParams = new URLSearchParams();
    if (params?.stage) searchParams.set("stage", params.stage);
    if (params?.sector) searchParams.set("sector", params.sector);
    if (params?.search) searchParams.set("search", params.search);
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.per_page) searchParams.set("per_page", params.per_page.toString());

    return this.fetch(`/deals?${searchParams}`);
  }

  async getDeal(id: string): Promise<Deal> {
    return this.fetch(`/deals/${id}`);
  }

  async createDeal(data: Partial<Deal>): Promise<Deal> {
    return this.fetch("/deals/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateDeal(id: string, data: Partial<Deal>): Promise<Deal> {
    return this.fetch(`/deals/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async updateDealStage(id: string, stage: string): Promise<Deal> {
    return this.fetch(`/deals/${id}/stage/${stage}`, {
      method: "POST",
    });
  }

  // Documents
  async uploadDocument(
    file: File,
    dealId?: string,
    documentType: string = "pitch_deck"
  ): Promise<{ id: string }> {
    const formData = new FormData();
    formData.append("file", file);
    if (dealId) formData.append("deal_id", dealId);
    formData.append("document_type", documentType);

    const response = await fetch(`${this.baseUrl}/api/v1/documents/upload`, {
      method: "POST",
      headers: {
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Upload failed");
    }

    return response.json();
  }

  async processDocument(documentId: string): Promise<any> {
    return this.fetch(`/documents/${documentId}/process`, {
      method: "POST",
    });
  }

  async searchDocuments(
    query: string,
    limit: number = 10
  ): Promise<{ results: any[]; query: string; count: number }> {
    return this.fetch("/documents/search", {
      method: "POST",
      body: JSON.stringify({ query, limit }),
    });
  }

  // Ghostwriter
  async generateMemo(request: {
    deal_id: string;
    template_id?: string;
    additional_context?: string;
    check_contradictions?: boolean;
  }): Promise<{
    memo_id: string;
    memo: InvestmentMemo;
    contradictions: any[];
    generation_time_seconds: number;
    tokens_used: number;
    model_used: string;
  }> {
    return this.fetch("/ghostwriter/generate", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getMemo(memoId: string): Promise<InvestmentMemo> {
    return this.fetch(`/ghostwriter/memos/${memoId}`);
  }

  async getDealMemos(
    dealId: string
  ): Promise<{ memos: InvestmentMemo[] }> {
    return this.fetch(`/ghostwriter/deals/${dealId}/memos`);
  }

  // Polling
  async createPoll(data: {
    deal_id: string;
    title: string;
    description?: string;
    closes_at?: string;
    ic_meeting_date?: string;
    reveal_threshold?: number;
  }): Promise<ConvictionPoll> {
    return this.fetch("/polls/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getPoll(pollId: string): Promise<ConvictionPoll> {
    return this.fetch(`/polls/${pollId}`);
  }

  async submitVote(
    pollId: string,
    data: {
      conviction_score: number;
      red_flags?: string[];
      green_flags?: string[];
      red_flag_notes?: string;
      green_flag_notes?: string;
      private_notes?: string;
    }
  ): Promise<any> {
    return this.fetch(`/polls/${pollId}/vote`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getMyVote(pollId: string): Promise<any> {
    return this.fetch(`/polls/${pollId}/my-vote`);
  }

  async revealPoll(pollId: string): Promise<ConvictionPoll> {
    return this.fetch(`/polls/${pollId}/reveal`, {
      method: "POST",
    });
  }

  async getDivergenceView(pollId: string): Promise<DivergenceView> {
    return this.fetch(`/polls/${pollId}/divergence`);
  }

  async getDealPolls(
    dealId: string
  ): Promise<{ polls: ConvictionPoll[] }> {
    return this.fetch(`/polls/deal/${dealId}`);
  }
}

export const api = new ApiClient(API_BASE);
