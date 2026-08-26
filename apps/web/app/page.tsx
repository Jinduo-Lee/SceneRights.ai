import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-[#090A0C] text-[#F5F7FA]">
      <div className="max-w-3xl w-full bg-[#15181D] border border-[#262B33] rounded-xl p-8 shadow-2xl space-y-6">
        <div className="flex items-center justify-between border-b border-[#262B33] pb-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-[#F5F7FA]">
              SceneRights AI
            </h1>
            <p className="text-sm text-[#A5ACB8] mt-1">
              Agentic Production Compliance, Continuity & Visual Review
            </p>
          </div>
          <span className="px-3 py-1 text-xs font-mono font-medium rounded-full bg-[#E3A544]/10 text-[#E3A544] border border-[#E3A544]/20">
            v6.2.2 Master Spec
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-[#090A0C] p-4 rounded-lg border border-[#262B33]">
            <h2 className="text-xs font-mono uppercase text-[#707782] mb-2">Track & System Status</h2>
            <div className="flex items-center space-x-2">
              <span className="h-2.5 w-2.5 rounded-full bg-[#5EA876]"></span>
              <span className="text-sm font-medium">ClickHouse Track Active</span>
            </div>
            <p className="text-xs text-[#A5ACB8] mt-2">
              Two-lane architecture: Write Lane (FastAPI) & Read Lane (ClickHouse MCP).
            </p>
          </div>

          <div className="bg-[#090A0C] p-4 rounded-lg border border-[#262B33]">
            <h2 className="text-xs font-mono uppercase text-[#707782] mb-2">Milestone 3 Workflow</h2>
            <div className="flex items-center space-x-2">
              <span className="h-2.5 w-2.5 rounded-full bg-[#5EA876]"></span>
              <span className="text-sm font-medium">Video Ingestion & Continuity Analysis</span>
            </div>
            <p className="text-xs text-[#A5ACB8] mt-2">
              FFmpeg keyframe extraction, Gemini paired-frame comparison, occlusion logic active.
            </p>
          </div>
        </div>

        {/* Workflow Navigation Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="bg-[#090A0C] p-5 rounded-xl border border-[#262B33] flex flex-col justify-between space-y-4">
            <div>
              <span className="text-[10px] font-mono uppercase text-[#E3A544] tracking-wider block mb-1">
                Screen B — Policy Review
              </span>
              <h3 className="text-base font-semibold text-[#F5F7FA]">Company Policy Intelligence</h3>
              <p className="text-xs text-[#A5ACB8] mt-1">
                Upload studio policies & approve extracted rules with exact verbatim source evidence.
              </p>
            </div>
            <Link
              href="/policies"
              className="px-4 py-2 rounded-lg text-xs font-semibold bg-[#15181D] hover:bg-[#262B33] text-[#E3A544] border border-[#E3A544]/30 text-center transition-colors"
            >
              Open Policy Manager &rarr;
            </Link>
          </div>

          <div className="bg-[#090A0C] p-5 rounded-xl border border-[#262B33] flex flex-col justify-between space-y-4">
            <div>
              <span className="text-[10px] font-mono uppercase text-[#5F8EC9] tracking-wider block mb-1">
                Screen C — Continuity Compare
              </span>
              <h3 className="text-base font-semibold text-[#F5F7FA]">Cross-Shot Continuity Analysis</h3>
              <p className="text-xs text-[#A5ACB8] mt-1">
                Compare reference/comparison video takes, evaluate necklace & mug, and inspect grounded findings.
              </p>
            </div>
            <Link
              href="/scenes"
              className="px-4 py-2 rounded-lg text-xs font-semibold bg-[#E3A544] hover:bg-[#F0B65B] text-[#090A0C] text-center transition-colors"
            >
              Open Continuity Compare &rarr;
            </Link>
          </div>
        </div>

        <div className="text-xs text-[#707782] border-t border-[#262B33] pt-4 flex justify-between items-center">
          <span>Agentic Cinema: The Blockbuster Hackathon</span>
          <span>Milestone 3 Active</span>
        </div>
      </div>
    </main>
  );
}
