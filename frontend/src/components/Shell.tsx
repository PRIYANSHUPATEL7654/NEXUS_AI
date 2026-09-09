import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from "react";

import { notificationApi } from "../api/modules";
import { useAuth } from "../auth/AuthContext";
import type { Notification } from "../types";

export type RouteKey = "dashboard" | "knowledge" | "learn" | "money" | "work" | "intelligence" | "search" | "profile";

type ModuleIcon = "today" | "knowledge" | "learn" | "money" | "work" | "intelligence";

const items: { key: RouteKey; label: string; icon: ModuleIcon }[] = [
  { key: "dashboard", label: "Today", icon: "today" },
  { key: "knowledge", label: "Knowledge", icon: "knowledge" },
  { key: "learn", label: "Learn", icon: "learn" },
  { key: "money", label: "Money", icon: "money" },
  { key: "work", label: "Work", icon: "work" },
  { key: "intelligence", label: "AI", icon: "intelligence" },
];

function NavIcon({ icon }: { icon: ModuleIcon }) {
  if (icon === "today") return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 10.5 12 4l8 6.5V20H4z"/><path d="M9 20v-6h6v6"/></svg>;
  if (icon === "knowledge") return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4.5 5.5A3.5 3.5 0 0 1 8 2h4v17H8a3.5 3.5 0 0 0-3.5 3z"/><path d="M19.5 5.5A3.5 3.5 0 0 0 16 2h-4v17h4a3.5 3.5 0 0 1 3.5 3z"/></svg>;
  if (icon === "learn") return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 9 9-5 9 5-9 5z"/><path d="M7 12.5V17c2.8 2 7.2 2 10 0v-4.5M21 9v6"/></svg>;
  if (icon === "money") return <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 9h18M7 15h4"/></svg>;
  if (icon === "work") return <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V4h6v3M3 12h18M10 12v2h4v-2"/></svg>;
  return <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/><circle cx="12" cy="12" r="4"/></svg>;
}

type InstallPrompt = Event & { prompt: () => Promise<void>; userChoice: Promise<{ outcome: string }> };

export function Shell({ route, children }: { route: RouteKey; children: ReactNode }) {
  const { user, token, logout } = useAuth();
  const [installPrompt, setInstallPrompt] = useState<InstallPrompt | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const handler = (event: Event) => {
      event.preventDefault();
      setInstallPrompt(event as InstallPrompt);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const loadNotifications = useCallback(async () => {
    if (!token) return;
    try {
      await notificationApi.sync(token);
      const [itemsResult, countResult] = await Promise.all([notificationApi.list(token), notificationApi.count(token)]);
      setNotifications(itemsResult); setUnreadCount(countResult.unread_count);
    } catch {
      // Notification availability must not block the primary workflows.
    }
  }, [token]);

  useEffect(() => { void loadNotifications(); }, [loadNotifications, route]);

  async function install() {
    if (!installPrompt) return;
    await installPrompt.prompt();
    await installPrompt.userChoice;
    setInstallPrompt(null);
  }

  function submitSearch(event: FormEvent) {
    event.preventDefault();
    const value=search.trim();
    if (value.length >= 2) window.location.hash=`#/search?q=${encodeURIComponent(value)}`;
  }

  async function openNotification(item: Notification) {
    if (!token) return;
    if (!item.is_read) {
      await notificationApi.read(token,item.id);
      setUnreadCount((count)=>Math.max(0,count-1));
      setNotifications((current)=>current.map((value)=>value.id===item.id?{...value,is_read:true}:value));
    }
    setNotificationsOpen(false);
    if (item.route) window.location.hash=`#${item.route}`;
  }

  async function readAll() {
    if (!token) return;
    await notificationApi.readAll(token);
    setUnreadCount(0); setNotifications((current)=>current.map((item)=>({...item,is_read:true})));
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <aside className="sidebar">
        <a className="brand-lockup sidebar-brand" href="#/dashboard"><span className="brand-mark">N</span><span>NEXUS AI</span></a>
        <nav className="main-nav" aria-label="Main navigation">
          {items.map((item) => (
            <a key={item.key} className={route === item.key ? "active" : ""} href={`#/${item.key}`}>
              <span className="nav-icon"><NavIcon icon={item.icon}/></span><span>{item.label}</span>
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
          <div className="mobile-actions"><a className="header-icon" href="#/search" aria-label="Search">⌕</a><button className="header-icon" onClick={()=>setNotificationsOpen(!notificationsOpen)} aria-label={`Notifications, ${unreadCount} unread`}>●{unreadCount>0&&<b>{unreadCount}</b>}</button><a className="avatar" href="#/profile">{user?.name.slice(0, 1).toUpperCase()}</a></div>
        </header>
        <header className="utility-header">
          <form role="search" onSubmit={submitSearch}><label className="sr-only" htmlFor="global-search">Search your Nexus</label><input id="global-search" value={search} onChange={(event)=>setSearch(event.target.value)} placeholder="Search your Nexus…" minLength={2}/></form>
          <div className="notification-wrap"><button className="notification-button" onClick={()=>setNotificationsOpen(!notificationsOpen)} aria-expanded={notificationsOpen} aria-label={`Notifications, ${unreadCount} unread`}>Notifications{unreadCount>0&&<b>{unreadCount}</b>}</button></div>
        </header>
        {notificationsOpen&&<section className="notification-panel" aria-label="Notifications">
          <div className="notification-heading"><div><strong>Notifications</strong><small>{unreadCount} unread</small></div>{unreadCount>0&&<button className="text-button" onClick={()=>void readAll()}>Mark all read</button>}</div>
          <div className="notification-list">{notifications.length===0?<p className="empty-state">You are all caught up.</p>:notifications.map((item)=><button className={item.is_read?"read":""} onClick={()=>void openNotification(item)} key={item.id}><i className={item.severity}/><span><strong>{item.title}</strong><small>{item.message}</small><time>{new Date(item.created_at).toLocaleString()}</time></span></button>)}</div>
        </section>}
        <main className="page-content" id="main-content" tabIndex={-1}>{children}</main>
      </div>

      <nav className="bottom-nav" aria-label="Mobile navigation">
        {items.map((item) => (
          <a key={item.key} className={route === item.key ? "active" : ""} href={`#/${item.key}`} aria-current={route === item.key ? "page" : undefined}>
            <span><NavIcon icon={item.icon}/></span><small>{item.label}</small>
          </a>
        ))}
      </nav>
    </div>
  );
}
