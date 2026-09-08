import { useEffect, useState } from "react";

import { useAuth } from "./auth/AuthContext";
import { Shell, type RouteKey } from "./components/Shell";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ModulePage } from "./pages/ModulePage";
import { ProfilePage } from "./pages/ProfilePage";

const validRoutes = new Set<RouteKey>(["dashboard", "knowledge", "learn", "money", "work", "intelligence", "profile"]);

function readRoute(): RouteKey {
  const value = window.location.hash.replace(/^#\//, "") as RouteKey;
  return validRoutes.has(value) ? value : "dashboard";
}

export default function App() {
  const { user, loading } = useAuth();
  const [route, setRoute] = useState<RouteKey>(readRoute);

  useEffect(() => {
    if (!window.location.hash) window.location.hash = "#/dashboard";
    const handler = () => setRoute(readRoute());
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  }, []);

  if (loading) return <main className="splash"><span className="brand-mark large">N</span><p>Opening NEXUS AI…</p></main>;
  if (!user) return <LoginPage />;

  let page = <DashboardPage />;
  if (route === "profile") page = <ProfilePage />;
  else if (route !== "dashboard") page = <ModulePage module={route} />;

  return <Shell route={route}>{page}</Shell>;
}
