const moduleCopy = {
  knowledge: ["Knowledge", "Documents, extraction, summaries and search", "Your backend Knowledge workflow is ready. The full document library screen arrives on Day 17."],
  learn: ["Learn", "Goals, progress, skill gaps and quizzes", "Your Learn records remain available. The button-based goals and quiz interface arrives on Day 17."],
  money: ["Money", "Private transaction imports and analytics", "Your Money data remains protected in PostgreSQL. Import review and charts arrive on Day 18."],
  work: ["Work", "Projects, task plans and completion estimates", "Your projects and tasks are connected. Full planning controls arrive on Day 18."],
  intelligence: ["Intelligence", "One controlled orchestrator across every module", "Ask Nexus is active on Today. Advanced search and tool-history screens will be expanded after the module pages."],
} as const;

export function ModulePage({ module }: { module: keyof typeof moduleCopy }) {
  const [title, subtitle, description] = moduleCopy[module];
  return (
    <section>
      <header className="page-heading compact"><div><p className="eyebrow">NEXUS MODULE</p><h1>{title}</h1><p>{subtitle}</p></div></header>
      <div className="module-coming panel">
        <span className={`module-orb ${module}`}>{title.slice(0, 1)}</span>
        <h2>Connected foundation</h2><p>{description}</p>
        <a className="secondary-button" href="#/dashboard">Return to Today</a>
      </div>
    </section>
  );
}
