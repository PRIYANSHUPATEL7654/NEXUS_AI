import { useEffect, useState, type ReactNode } from "react";

import { useAuth } from "../auth/AuthContext";

export type RouteKey = "dashboard" | "knowledge" | "learn" | "money" | "work" | "intelligence" | "profile";

const items: { key: RouteKey; label: string; short: string }[] = [
  { key: "dashboard", label: "Today", short: "T" },
  { key: "knowledge", label: "Knowledge", short: "K" },
  { key: "learn", label: "Learn", short: "L" },
  { key: "money", label: "Money", short: "M" },
  { key: "work", label: "Work", short: "W" },
  { key: "intelligence", label: "Intelligence", short: "AI" },
];

type InstallPrompt = Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: string }> };

export function Shell({ route, children }: { route: RouteKey; children: ReactNode }) {
  const { user, logout } = useAuth();
  const [installPrompt, setInstallPrompt] = useState<InstallPrompt | null>(null);

  useEffect(() => {
    const handler = (event: Event) => {
      event.preventDefault();
      setInstallPrompt(event as InstallPrompt);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  async function install() {
    if (!installPrompt) return;
    await installPrompt.prompt();
    await installPrompt.userChoice;
    setInstallPrompt(null);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand-lockup sidebar-brand" href="#/dashboard"><span className="brand-mark">N</span><span>NEXUS AI</span></a>
        <nav className="main-nav" aria-label="Main navigation">
          {items.map((item) => (
            <a key={item.key} className={route === item.key ? "active" : ""} href={`#/${item.key}`}>
              <span className="nav-icon">{item.short}</span><span>{item.label}</span>
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          {installPrompt && <button className="install-button" onClick={install}>Install app</button>}
          <a className={route === "profile" ? "profile-link active" : "profile-link"} href="#/profile">
            <span className="avatar">{user?.name.slice(0, 1).toUpperCase()}</span>
            <span><strong>{user?.name}</strong><small>{user?.email}</small></span>
          </a>
          <button className="text-button" onClick={logout}>Sign out</button>
        </div>
      </aside>

      <div className="content-column">
        <header className="mobile-header">
          <a className="brand-lockup" href="#/dashboard"><span className="brand-mark">N</span><span>NEXUS AI</span></a>
          <a className="avatar" href="#/profile">{user?.name.slice(0, 1).toUpperCase()}</a>
        </header>
        <main className="page-content">{children}</main>
      </div>

      <nav className="bottom-nav" aria-label="Mobile navigation">
        {items.slice(0, 5).map((item) => (
          <a key={item.key} className={route === item.key ? "active" : ""} href={`#/${item.key}`}>
            <span>{item.short}</span><small>{item.label}</small>
          </a>
        ))}
      </nav>
    </div>
  );
}
