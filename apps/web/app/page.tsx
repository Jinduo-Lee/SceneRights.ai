export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-background-primary text-text-primary">
      <div className="max-w-3xl w-full bg-panel border border-border rounded-xl p-8 shadow-2xl">
        <div className="flex items-center justify-between mb-6 border-b border-border pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-text-primary">
              SceneRights AI
            </h1>
            <p className="text-sm text-text-secondary mt-1">
              Agentic Production Compliance, Continuity & Visual Review
            </p>
          </div>
          <span className="px-3 py-1 text-xs font-mono font-medium rounded-full bg-accent-primary/10 text-accent-primary border border-accent-primary/20">
            v6.2.2 Baseline
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
          <div className="bg-background-secondary p-4 rounded-lg border border-border">
            <h2 className="text-xs font-mono uppercase text-text-muted mb-2">Track & System Status</h2>
            <div className="flex items-center space-x-2">
              <span className="h-2.5 w-2.5 rounded-full bg-status-success"></span>
              <span className="text-sm font-medium">ClickHouse Track Active</span>
            </div>
            <p className="text-xs text-text-secondary mt-2">
              Two-lane architecture: Write Lane (FastAPI) & Read Lane (ClickHouse MCP).
            </p>
          </div>

          <div className="bg-background-secondary p-4 rounded-lg border border-border">
            <h2 className="text-xs font-mono uppercase text-text-muted mb-2">Permitted AI</h2>
            <div className="flex items-center space-x-2">
              <span className="h-2.5 w-2.5 rounded-full bg-status-info"></span>
              <span className="text-sm font-medium">Google Gemini / ADK</span>
            </div>
            <p className="text-xs text-text-secondary mt-2">
              Strictly Google Cloud AI runtime baseline (§1).
            </p>
          </div>
        </div>

        <div className="text-xs text-text-muted border-t border-border pt-4 flex justify-between items-center">
          <span>Agentic Cinema: The Blockbuster Hackathon</span>
          <span>Milestone 1A Skeleton</span>
        </div>
      </div>
    </main>
  );
}

