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
