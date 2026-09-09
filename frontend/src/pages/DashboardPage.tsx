import { useCallback, useEffect, useState, type FormEvent } from "react";

import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { AskResponse, DailyBrief, Recommendation } from "../types";

export function DashboardPage() {
  const { token } = useAuth();
  const [brief, setBrief] = useState<DailyBrief | null>(null);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [slow, setSlow] = useState(false);
  const [error, setError] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AskResponse | null>(null);
  const [asking, setAsking] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    const timer = window.setTimeout(() => setSlow(true), 1800);
    try {
      const [briefResult, recommendationResult] = await Promise.all([
        api.dailyBrief(token), api.recommendations(token),
      ]);
      setBrief(briefResult);
      setRecommendations(recommendationResult.recommendations);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not load the dashboard.");
    } finally {
      window.clearTimeout(timer);
      setLoading(false);
      setSlow(false);
    }
  }, [token]);

  useEffect(() => { void load(); }, [load]);

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!token || question.trim().length < 2) return;
    setAsking(true);
    setAnswer(null);
    try {
      setAnswer(await api.ask(token, question.trim()));
    } catch (caught) {
      setAnswer({ run_id: 0, intent: "error", answer: caught instanceof ApiError ? caught.message : "Ask Nexus failed.", tools_used: [], data: {} });
    } finally {
      setAsking(false);
    }
  }

  if (loading) {
    return <section className="center-state"><span className="loader" /><h2>Preparing your daily Nexus</h2><p>{slow ? "The backend may be waking from a free-tier cold start…" : "Connecting your modules…"}</p></section>;
  }
  if (error) {
    return <section className="center-state"><div className="state-icon">!</div><h2>We could not reach your Nexus</h2><p>{error}</p><button className="primary-button" onClick={() => void load()}>Try again</button></section>;
  }

  return (
    <>
      <header className="page-heading">
        <div><p className="eyebrow">{brief?.local_date} · {brief?.timezone}</p><h1>{brief?.greeting}</h1><p>{brief?.summary}</p></div>
        <span className="status-pill"><i /> All modules connected</span>
      </header>

      <section className="brief-grid" aria-label="Daily brief">
        {brief?.sections.map((section) => (
          <a className={`brief-card ${section.severity}`} href={`#${section.route || "/dashboard"}`} key={section.title}>
            <div className="card-top"><span>{section.title}</span><span className="arrow">↗</span></div>
            <strong>{section.value}</strong><p>{section.detail}</p>
          </a>
        ))}
      </section>

      <section className="quick-actions" aria-label="Quick actions">
        <a href="#/knowledge"><span>K</span><div><strong>Add a document</strong><small>Knowledge upload</small></div></a>
        <a href="#/money"><span>M</span><div><strong>Add a transaction</strong><small>Manual or import</small></div></a>
        <a href="#/work"><span>W</span><div><strong>Add a task</strong><small>Choose a project</small></div></a>
        <a href="#/learn"><span>L</span><div><strong>Continue learning</strong><small>Goals and quizzes</small></div></a>
        <a href="#/search"><span>⌕</span><div><strong>Search everything</strong><small>All owned records</small></div></a>
      </section>

      <section className="dashboard-columns">
        <div className="panel recommendations-panel">
          <div className="panel-heading"><div><p className="eyebrow">EXPLAINABLE</p><h2>Recommended next actions</h2></div><span>{recommendations.length}</span></div>
          {recommendations.length === 0 ? <div className="empty-state">No urgent recommendation. Add goals or tasks to make the brief more useful.</div> : (
            <div className="recommendation-list">
              {recommendations.map((item) => (
                <a href={`#${item.route}`} className="recommendation" key={`${item.module}-${item.title}`}>
                  <span className={`module-badge ${item.module}`}>{item.module.slice(0, 1).toUpperCase()}</span>
                  <div><div className="recommendation-title"><strong>{item.title}</strong><small>P{item.priority}</small></div><p>{item.reason}</p><small>{item.action}</small></div>
                </a>
              ))}
            </div>
          )}
        </div>

        <div className="panel ask-panel">
          <div className="panel-heading"><div><p className="eyebrow">LOCAL ORCHESTRATOR</p><h2>Ask Nexus</h2></div><span className="ai-dot">AI</span></div>
          <p className="muted">Ask about today, pending work, learning progress, spending or saved records.</p>
          <form onSubmit={ask}>
            <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="What should I focus on today?" rows={3} maxLength={2000} />
            <div className="prompt-row">
              <button type="button" onClick={() => setQuestion("What did I spend this month?")}>Monthly spending</button>
              <button type="button" onClick={() => setQuestion("What work is pending?")}>Pending work</button>
            </div>
            <button className="primary-button full" disabled={asking || question.trim().length < 2}>{asking ? "Reasoning…" : "Ask Nexus"}</button>
          </form>
          {answer && <div className={`answer-box ${answer.intent === "error" ? "error" : ""}`}><p>{answer.answer}</p>{answer.tools_used.length > 0 && <small>Tool: {answer.tools_used.join(", ")} · Run {answer.run_id}</small>}</div>}
        </div>
      </section>
    </>
  );
}
