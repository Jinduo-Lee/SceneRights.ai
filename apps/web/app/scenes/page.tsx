"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Clip, Scene, AnalysisRun, Finding } from "../../lib/types";
import {
  getClips,
  getScene,
  setReferenceClip,
  analyzeScene,
  getAnalysisRun,
  getSceneFindings,
  DEFAULT_PROJECT_ID,
} from "../../lib/api";
import { ClipUploadCard } from "../../components/video/ClipUploadCard";
import { ContinuityCompare } from "../../components/continuity/ContinuityCompare";

export default function ScenesPage() {
  const [clips, setClips] = useState<Clip[]>([]);
  const [scene, setScene] = useState<Scene | null>(null);
  const [referenceClipId, setReferenceClipId] = useState<string>("take_a");
  const [comparisonClipId, setComparisonClipId] = useState<string>("take_b");
  const [analysisRun, setAnalysisRun] = useState<AnalysisRun | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [statusStep, setStatusStep] = useState<string>("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadSceneData = async () => {
    try {
      const fetchedClips = await getClips(DEFAULT_PROJECT_ID);
      setClips(fetchedClips);

      const fetchedScene = await getScene("scene_12", DEFAULT_PROJECT_ID);
      setScene(fetchedScene);
      if (fetchedScene.reference_clip_id) {
        setReferenceClipId(fetchedScene.reference_clip_id);
      }

      const existingFindings = await getSceneFindings("scene_12", DEFAULT_PROJECT_ID);
      setFindings(existingFindings);
    } catch (err: any) {
      // Non-blocking load error
    }
  };

  useEffect(() => {
    loadSceneData();
  }, []);

  const handleClipUploaded = (newClip: Clip) => {
    setClips((prev) => [newClip, ...prev]);
  };

  const handleSetReference = async (clipId: string) => {
    try {
      const updatedScene = await setReferenceClip("scene_12", clipId, DEFAULT_PROJECT_ID);
      setScene(updatedScene);
      setReferenceClipId(clipId);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to set reference take");
    }
  };

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    setErrorMsg(null);
    setStatusStep("Initiating async analysis (HTTP 202 Accepted)...");

    try {
      const initRes = await analyzeScene("scene_12", comparisonClipId, `idem_${Date.now()}`);
      const runId = initRes.analysis_run_id;

      // Poll analysis status until completed or failed
      let completed = false;
      let attempts = 0;

      while (!completed && attempts < 20) {
        attempts++;
        await new Promise((resolve) => setTimeout(resolve, 1000));
        const runData = await getAnalysisRun(runId, DEFAULT_PROJECT_ID);
        setAnalysisRun(runData);

        if (runData.step === "extracting_frames") {
          setStatusStep("FFmpeg extracting 3–5 keyframes at fixed deterministic timestamps...");
        } else if (runData.step === "comparing_frames") {
          setStatusStep("Gemini evaluating paired frames & matching approved policy rules...");
        }

        if (runData.status === "succeeded" || runData.status === "failed") {
          completed = true;
          if (runData.status === "failed") {
            setErrorMsg(runData.error_code || "Analysis job failed.");
          }
        }
      }

      // Fetch fresh findings from ClickHouse
      const freshFindings = await getSceneFindings("scene_12", DEFAULT_PROJECT_ID);
      setFindings(freshFindings);
      setStatusStep("Continuity analysis completed!");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to run continuity analysis.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#090A0C] text-[#F5F7FA] p-6 md:p-10 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Top Nav Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#262B33] pb-6">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <Link
                href="/"
                className="text-xs font-mono text-[#A5ACB8] hover:text-[#E3A544] transition-colors"
              >
                &larr; Return to Dashboard
              </Link>
              <span className="text-[#262B33]">|</span>
              <span className="text-xs font-mono text-[#E3A544] uppercase tracking-wider">
                Screen C — Continuity Compare
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[#F5F7FA]">
              Cross-Shot Continuity Analysis
            </h1>
            <p className="text-sm text-[#A5ACB8]">
              Compare paired keyframes between reference and comparison video takes, evaluate necklace presence & hero mug color, and enforce grounded policy logic.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-3 py-1 text-xs font-mono rounded-lg bg-[#15181D] border border-[#262B33] text-[#A5ACB8]">
              Scene 12 (Northstar)
            </span>
          </div>
        </div>

        {/* Video Upload Card */}
        <ClipUploadCard sceneId="scene_12" onClipUploaded={handleClipUploaded} />

        {/* Analysis Configuration & Trigger Bar */}
        <div className="bg-[#15181D] border border-[#262B33] rounded-xl p-6 space-y-4">
          <h2 className="text-base font-semibold text-[#F5F7FA]">
            Continuity Comparison Setup
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Reference Take Selection */}
            <div>
              <label className="text-xs font-medium text-[#707782] uppercase mb-1 block">
                Reference Take (Take A)
              </label>
              <select
                value={referenceClipId}
                onChange={(e) => handleSetReference(e.target.value)}
                className="w-full bg-[#090A0C] border border-[#262B33] rounded-lg p-2.5 text-xs text-[#F5F7FA] focus:border-[#E3A544] outline-none"
              >
                <option value="take_a">Take A (Silver Necklace, Blue Mug)</option>
                {clips.map((c) => (
                  <option key={c.clip_id} value={c.clip_id}>
                    {c.clip_id} ({c.role.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>

            {/* Comparison Take Selection */}
            <div>
              <label className="text-xs font-medium text-[#707782] uppercase mb-1 block">
                Comparison Take (Take B / C)
              </label>
              <select
                value={comparisonClipId}
                onChange={(e) => setComparisonClipId(e.target.value)}
                className="w-full bg-[#090A0C] border border-[#262B33] rounded-lg p-2.5 text-xs text-[#F5F7FA] focus:border-[#E3A544] outline-none"
              >
                <option value="take_b">Take B (No Necklace, Red Mug)</option>
                <option value="take_c">Take C (Necklace Occluded)</option>
                <option value="take_a">Take A (False Positive Control - Take A vs Take A)</option>
                {clips
                  .filter((c) => c.clip_id !== "take_a" && c.clip_id !== "take_b" && c.clip_id !== "take_c")
                  .map((c) => (
                    <option key={c.clip_id} value={c.clip_id}>
                      {c.clip_id} ({c.role.toUpperCase()})
                    </option>
                  ))}
              </select>
            </div>
          </div>

          {statusStep && (
            <div className="text-xs text-[#5F8EC9] bg-[#5F8EC9]/10 p-3 rounded-lg border border-[#5F8EC9]/30 flex items-center gap-2">
              {analyzing && (
                <svg className="animate-spin h-3.5 w-3.5 text-[#5F8EC9]" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
              )}
              <span>{statusStep}</span>
            </div>
          )}

          {errorMsg && (
            <div className="text-xs text-[#D9544D] bg-[#D9544D]/10 p-3 rounded-lg border border-[#D9544D]/30">
              {errorMsg}
            </div>
          )}

          <div className="flex justify-end pt-2">
            <button
              onClick={handleRunAnalysis}
              disabled={analyzing}
              className="px-6 py-2.5 rounded-lg text-xs font-semibold bg-[#E3A544] hover:bg-[#F0B65B] text-[#090A0C] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {analyzing ? "Running Continuity Analysis..." : "Run Continuity Analysis (Async 202)"}
            </button>
          </div>
        </div>

        {/* Continuity Compare View Component */}
        <ContinuityCompare
          referenceClipId={referenceClipId}
          comparisonClipId={comparisonClipId}
          findings={findings}
        />
      </div>
    </main>
  );
}

