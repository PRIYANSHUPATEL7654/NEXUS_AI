import { useEffect, useState } from "react";

import { useAuth } from "./auth/AuthContext";
import { Shell, type RouteKey } from "./components/Shell";
import { DashboardPage } from "./pages/DashboardPage";
import { KnowledgePage } from "./pages/KnowledgePage";
import { LearnPage } from "./pages/LearnPage";
import { LoginPage } from "./pages/LoginPage";
import { MoneyPage } from "./pages/MoneyPage";
import { ModulePage } from "./pages/ModulePage";
import { ProfilePage } from "./pages/ProfilePage";
import { SearchPage } from "./pages/SearchPage";
import { WorkPage } from "./pages/WorkPage";

const validRoutes = new Set<RouteKey>(["dashboard", "knowledge", "learn", "money", "work", "intelligence", "search", "profile"]);

function readRoute(): RouteKey {
  const value = window.location.hash.replace(/^#\//, "").split("?")[0] as RouteKey;
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
  else if (route === "search") page = <SearchPage />;
  else if (route === "knowledge") page = <KnowledgePage />;
  else if (route === "learn") page = <LearnPage />;
  else if (route === "money") page = <MoneyPage />;
  else if (route === "work") page = <WorkPage />;
  else if (route === "intelligence") page = <ModulePage module="intelligence" />;

  return <Shell route={route}>{page}</Shell>;
}
