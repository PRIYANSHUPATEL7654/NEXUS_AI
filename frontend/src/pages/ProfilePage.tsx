import { useEffect, useState, type FormEvent } from "react";

import { API_BASE_URL, api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import type { UserProfile } from "../types";

export function ProfilePage() {
  const { user, token, logout } = useAuth();
  const [profile, setProfile] = useState<UserProfile|null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<{kind:"success"|"error";text:string}|null>(null);

  useEffect(()=>{
    if (!token) return;
    api.profile(token).then(setProfile).catch((caught)=>setNotice({kind:"error",text:caught instanceof ApiError?caught.message:"Could not load profile."})).finally(()=>setLoading(false));
  },[token]);

  function preference(group:"ai_preferences"|"privacy_preferences"|"notification_preferences", key:string, fallback=true) {
    const value=profile?.[group]?.[key]; return typeof value === "boolean" ? value : fallback;
  }
  function toggle(group:"ai_preferences"|"privacy_preferences"|"notification_preferences", key:string, value:boolean) {
    if (!profile) return;
    setProfile({...profile,[group]:{...profile[group],[key]:value}});
  }
  async function save(event:FormEvent) {
    event.preventDefault(); if (!token || !profile) return;
    setSaving(true); setNotice(null);
    try {
      setProfile(await api.updateProfile(token,{
        timezone:profile.timezone,preferred_currency:profile.preferred_currency,
        learning_goals:profile.learning_goals,work_preferences:profile.work_preferences,
        ai_preferences:profile.ai_preferences,privacy_preferences:profile.privacy_preferences,
        notification_preferences:profile.notification_preferences,
      }));
      setNotice({kind:"success",text:"Preferences saved."});
    } catch(caught) { setNotice({kind:"error",text:caught instanceof ApiError?caught.message:"Could not save profile."}); }
    finally { setSaving(false); }
  }

  return <section className="module-workspace">
    <header className="page-heading compact"><div><p className="eyebrow">ACCOUNT & PREFERENCES</p><h1>Your profile</h1><p>Settings apply across every NEXUS module.</p></div></header>
    {notice&&<div className={`notice ${notice.kind}`} role={notice.kind==="error"?"alert":"status"}>{notice.text}</div>}
    {loading?<div className="inline-busy"><span className="loader"/>Loading preferences…</div>:profile&&<div className="profile-grid">
      <aside className="panel profile-card"><span className="large-avatar">{user?.name.slice(0,1).toUpperCase()}</span><h2>{user?.name}</h2><p>{user?.email}</p><span className="status-pill"><i/> Active account</span><dl className="connection-list"><div><dt>API</dt><dd>{API_BASE_URL}</dd></div><div><dt>Currency</dt><dd>{profile.preferred_currency}</dd></div></dl><button className="secondary-button" onClick={logout}>Sign out</button></aside>
      <form className="panel settings-form" onSubmit={save}>
        <h2>Personal defaults</h2><div className="form-grid two"><label>Timezone<input value={profile.timezone} onChange={(e)=>setProfile({...profile,timezone:e.target.value})} placeholder="Asia/Kolkata" required/></label><label>Currency<input value={profile.preferred_currency} onChange={(e)=>setProfile({...profile,preferred_currency:e.target.value.toUpperCase()})} minLength={3} maxLength={3} required/></label></div>
        <label>Learning goals<textarea rows={3} maxLength={5000} value={profile.learning_goals||""} onChange={(e)=>setProfile({...profile,learning_goals:e.target.value})}/></label>
        <label>Work preferences<textarea rows={3} maxLength={5000} value={profile.work_preferences||""} onChange={(e)=>setProfile({...profile,work_preferences:e.target.value})}/></label>
        <fieldset><legend>AI and privacy</legend><label className="check-label"><input type="checkbox" checked={preference("ai_preferences","local_first")} onChange={(e)=>toggle("ai_preferences","local_first",e.target.checked)}/>Prefer local, deterministic processing</label><label className="check-label"><input type="checkbox" checked={preference("privacy_preferences","minimal_retention")} onChange={(e)=>toggle("privacy_preferences","minimal_retention",e.target.checked)}/>Prefer minimal data retention</label></fieldset>
        <fieldset><legend>In-app notifications</legend><label className="check-label"><input type="checkbox" checked={preference("notification_preferences","in_app_enabled")} onChange={(e)=>toggle("notification_preferences","in_app_enabled",e.target.checked)}/>Enable notification records</label><label className="check-label"><input type="checkbox" checked={preference("notification_preferences","import_updates")} onChange={(e)=>toggle("notification_preferences","import_updates",e.target.checked)}/>Import review and failure notices</label><label className="check-label"><input type="checkbox" checked={preference("notification_preferences","work_reminders")} onChange={(e)=>toggle("notification_preferences","work_reminders",e.target.checked)}/>Overdue work reminders</label></fieldset>
        <button className="primary-button" disabled={saving}>{saving?"Saving…":"Save preferences"}</button>
      </form>
    </div>}
    <section className="panel install-guide"><h2>Install NEXUS AI</h2><p>In Chrome or Edge on Windows, use the install icon in the address bar. On Android, open the browser menu and choose <strong>Install app</strong> or <strong>Add to Home screen</strong>. Installation requires the production site to use HTTPS; localhost is allowed during development.</p></section>
  </section>;
}
