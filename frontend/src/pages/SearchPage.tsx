import { useEffect, useMemo, useState, type FormEvent } from "react";

import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { IntelligenceSearchResult } from "../types";

function currentQuery() {
  return new URLSearchParams(window.location.hash.split("?")[1] || "").get("q")?.trim() || "";
}

export function SearchPage() {
  const { token } = useAuth();
  const [query, setQuery] = useState(currentQuery);
  const [submitted, setSubmitted] = useState(currentQuery);
  const [results, setResults] = useState<IntelligenceSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || submitted.length < 2) return;
    let active = true;
    setLoading(true); setError("");
    api.search(token, submitted)
      .then((response) => active && setResults(response.results))
      .catch((caught) => active && setError(caught instanceof ApiError ? caught.message : "Search failed."))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [submitted, token]);

  const grouped = useMemo(() => results.reduce<Record<string, IntelligenceSearchResult[]>>((result, item) => {
    (result[item.module] ||= []).push(item); return result;
  }, {}), [results]);

  function search(event: FormEvent) {
    event.preventDefault();
    const value = query.trim();
    if (value.length < 2) { setError("Enter at least two characters."); return; }
    window.location.hash = `#/search?q=${encodeURIComponent(value)}`;
    setSubmitted(value);
  }

  return <section className="module-workspace">
    <header className="page-heading compact"><div><p className="eyebrow">ALL MODULES</p><h1>Search your Nexus</h1><p>Find your own documents, topics, transactions, projects and tasks.</p></div></header>
    <form className="panel search-hero" onSubmit={search} role="search">
      <label htmlFor="nexus-search">Search terms</label>
      <div><input id="nexus-search" value={query} onChange={(event)=>setQuery(event.target.value)} placeholder="Try a project, topic, merchant or document title" maxLength={200}/><button className="primary-button">Search</button></div>
    </form>
    {error && <div className="notice error" role="alert">{error}</div>}
    {loading ? <div className="inline-busy"><span className="loader"/>Searching only your records…</div> : submitted.length >= 2 && results.length === 0 && !error ? <div className="panel empty-state">No results for “{submitted}”. Try a broader term.</div> : null}
    {Object.entries(grouped).map(([module, items]) => <section className="panel search-group" key={module}>
      <div className="panel-heading"><h2>{module[0].toUpperCase()+module.slice(1)}</h2><span>{items.length}</span></div>
      <div className="search-results">{items.map((item)=><a href={`#/${item.module}`} key={`${item.module}-${item.record_type}-${item.record_id}`}>
        <span className={`module-badge ${item.module}`}>{item.module[0].toUpperCase()}</span><div><strong>{item.title}</strong><small>{item.record_type.replaceAll("_", " ")}</small><p>{item.snippet || "Open the module to view this record."}</p></div><span className="arrow">↗</span>
      </a>)}</div>
    </section>)}
  </section>;
}
