export type User = {
  id: number;
  name: string;
  email: string;
  age: number;
  is_active: boolean;
};

export type BriefSection = {
  title: string;
  value: string;
  detail: string;
  severity: "info" | "success" | "warning" | "urgent";
  route: string | null;
};

export type DailyBrief = {
  local_date: string;
  timezone: string;
  greeting: string;
  summary: string;
  sections: BriefSection[];
};

export type Recommendation = {
  module: "knowledge" | "learn" | "money" | "work";
  priority: number;
  title: string;
  reason: string;
  evidence: string[];
  action: string;
  route: string;
};

export type AskResponse = {
  run_id: number;
  intent: string;
  answer: string;
  tools_used: string[];
  data: Record<string, unknown>;
};

export type UserProfile = {
  id: number; user_id: number; timezone: string; preferred_currency: string;
  learning_goals: string | null; work_preferences: string | null;
  ai_preferences: Record<string, unknown>; privacy_preferences: Record<string, unknown>;
  notification_preferences: Record<string, unknown>; created_at: string; updated_at: string;
};

export type IntelligenceSearchResult = {
  module: "knowledge" | "learn" | "money" | "work"; record_type: string;
  record_id: number; title: string; snippet: string; score: number; route: string;
};
export type IntelligenceSearchResponse = { query: string; total: number; results: IntelligenceSearchResult[] };

export type Notification = {
  id: number; user_id: number; kind: string;
  module: "knowledge" | "learn" | "money" | "work" | "system";
  title: string; message: string; severity: "info" | "success" | "warning" | "urgent";
  route: string | null; is_read: boolean; created_at: string; read_at: string | null;
};
