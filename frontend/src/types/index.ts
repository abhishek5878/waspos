export type DealStage =
  | "inbound"
  | "screening"
  | "first_meeting"
  | "deep_dive"
  | "ic_review"
  | "term_sheet"
  | "due_diligence"
  | "closed"
  | "passed";

export type DealSource =
  | "inbound"
  | "referral"
  | "portfolio_intro"
  | "outbound"
  | "conference"
  | "other";

export interface Deal {
  id: string;
  firm_id: string;
  lead_partner_id?: string;
  company_name: string;
  website?: string;
  description?: string;
  one_liner?: string;
  team_summary?: string;
  tam_analysis?: string;
  moat_description?: string;
  traction_metrics?: TractionMetrics;
  stage: DealStage;
  source: DealSource;
  sector?: string;
  sub_sector?: string;
  asking_valuation?: number;
  proposed_check?: number;
  round_size?: number;
  referrer?: string;
  notes?: string;
  pass_reason?: string;
  first_contact_date?: string;
  ic_date?: string;
  close_date?: string;
  created_at: string;
  updated_at: string;
}

export interface TractionMetrics {
  mrr?: number;
  arr?: number;
  growth_rate?: number;
  customers?: number;
  gmv?: number;
  dau?: number;
  mau?: number;
  nrr?: number;
}

export interface InvestmentMemo {
  id: string;
  deal_id: string;
  firm_id: string;
  author_id?: string;
  title: string;
  status: "draft" | "in_review" | "final" | "archived";
  executive_summary?: string;
  company_overview?: string;
  team_assessment?: string;
  market_analysis?: string;
  product_analysis?: string;
  business_model?: string;
  traction_analysis?: string;
  competitive_landscape?: string;
  investment_thesis?: string;
  key_risks?: string;
  deal_terms?: string;
  recommendation?: string;
  is_ai_generated: string;
  ai_model_used?: string;
  contradictions?: ContradictionFlag[];
  created_at: string;
  updated_at: string;
}

export interface ContradictionFlag {
  historical_memo_id: string;
  historical_memo_title: string;
  section: string;
  historical_stance: string;
  current_stance: string;
  contradiction_summary: string;
  severity: "low" | "medium" | "high";
}

export interface ConvictionPoll {
  id: string;
  deal_id: string;
  firm_id: string;
  title: string;
  description?: string;
  is_active: boolean;
  is_revealed: boolean;
  reveal_threshold: number;
  opens_at: string;
  closes_at?: string;
  ic_meeting_date?: string;
  vote_count?: number;
  average_score?: number;
  divergence_score?: number;
  created_at: string;
}

export interface PollVote {
  id: string;
  poll_id: string;
  conviction_score: number;
  red_flags?: string[];
  green_flags?: string[];
  submitted_at: string;
  user_id?: string;
  user_name?: string;
  red_flag_notes?: string;
  green_flag_notes?: string;
}

export interface DivergenceView {
  poll_id: string;
  deal_id: string;
  company_name: string;
  total_votes: number;
  average_score: number;
  min_score: number;
  max_score: number;
  divergence: number;
  std_deviation: number;
  score_distribution: Record<number, number>;
  top_red_flags: { flag: string; count: number }[];
  top_green_flags: { flag: string; count: number }[];
  has_consensus: boolean;
  needs_discussion: boolean;
  votes?: PollVote[];
}
