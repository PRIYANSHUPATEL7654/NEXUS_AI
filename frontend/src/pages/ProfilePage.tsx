import { API_BASE_URL } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function ProfilePage() {
  const { user, logout } = useAuth();
  return (
    <section>
      <header className="page-heading compact"><div><p className="eyebrow">ACCOUNT</p><h1>Your profile</h1><p>One identity across every NEXUS module.</p></div></header>
      <div className="profile-grid">
        <div className="panel profile-card"><span className="large-avatar">{user?.name.slice(0, 1).toUpperCase()}</span><h2>{user?.name}</h2><p>{user?.email}</p><span className="status-pill"><i /> Active account</span></div>
        <div className="panel details-card"><h2>Connection</h2><dl><div><dt>User ID</dt><dd>{user?.id}</dd></div><div><dt>Age</dt><dd>{user?.age}</dd></div><div><dt>API</dt><dd>{API_BASE_URL}</dd></div></dl><button className="secondary-button" onClick={logout}>Sign out</button></div>
      </div>
    </section>
  );
}
