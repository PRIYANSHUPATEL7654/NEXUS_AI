import { useState, type FormEvent } from "react";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function LoginPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [age, setAge] = useState("22");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "register") {
        await register({ name, email, age: Number(age), password });
      } else {
        await login(email, password);
      }
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Could not complete authentication.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-story">
        <div className="brand-lockup"><span className="brand-mark">N</span><span>NEXUS AI</span></div>
        <div className="auth-copy">
          <p className="eyebrow">ONE PRIVATE WORKSPACE</p>
          <h1>Your knowledge, learning, money and work—finally connected.</h1>
          <p>NEXUS turns the information you intentionally save into a useful daily plan. Your account controls every record.</p>
          <div className="feature-row">
            <span>Knowledge</span><span>Learn</span><span>Money</span><span>Work</span>
          </div>
        </div>
        <p className="auth-footnote">Responsive web app · Installable PWA · Free-tier MVP</p>
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <div className="mobile-brand"><span className="brand-mark">N</span><strong>NEXUS AI</strong></div>
          <p className="eyebrow">WELCOME</p>
          <h2>{mode === "login" ? "Continue to your Nexus" : "Create your Nexus account"}</h2>
          <p className="muted">{mode === "login" ? "Use the account you created in the backend." : "One account for every NEXUS module."}</p>

          <div className="auth-tabs" role="tablist">
            <button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")} type="button">Sign in</button>
            <button className={mode === "register" ? "active" : ""} onClick={() => setMode("register")} type="button">Register</button>
          </div>

          <form onSubmit={submit}>
            {mode === "register" && (
              <div className="form-grid two">
                <label><span>Name</span><input value={name} onChange={(event) => setName(event.target.value)} minLength={2} required autoComplete="name" /></label>
                <label><span>Age</span><input value={age} onChange={(event) => setAge(event.target.value)} type="number" min={1} max={120} required /></label>
              </div>
            )}
            <label><span>Email</span><input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required autoComplete="email" placeholder="you@example.com" /></label>
            <label><span>Password</span><input value={password} onChange={(event) => setPassword(event.target.value)} type="password" minLength={8} required autoComplete={mode === "login" ? "current-password" : "new-password"} /></label>
            {error && <div className="error-banner" role="alert">{error}</div>}
            <button className="primary-button full" disabled={busy} type="submit">
              {busy ? "Connecting…" : mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>
          <p className="cold-start-note">The local API must be running. On free hosting, the first connection may need a short cold start.</p>
        </div>
      </section>
    </main>
  );
}
