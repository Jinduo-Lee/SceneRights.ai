"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { PolicyDocument, PolicyRule } from "../../lib/types";
import { getPolicies, getPolicyRules, DEFAULT_PROJECT_ID } from "../../lib/api";
import { PolicyUploadCard } from "../../components/policy/PolicyUploadCard";
import { PolicyRuleCard } from "../../components/policy/PolicyRuleCard";

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<PolicyDocument[]>([]);
  const [selectedPolicyId, setSelectedPolicyId] = useState<string | null>(null);
  const [rules, setRules] = useState<PolicyRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>("all");

  const loadPoliciesAndRules = async () => {
    setLoading(true);
    setError(null);
    try {
      const docs = await getPolicies(DEFAULT_PROJECT_ID);
      setPolicies(docs);
      if (docs.length > 0) {
        const targetId = selectedPolicyId || docs[0].policy_id;
        setSelectedPolicyId(targetId);
        const policyRules = await getPolicyRules(targetId, DEFAULT_PROJECT_ID);
        setRules(policyRules);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load policy documents");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPoliciesAndRules();
  }, []);

  const handlePolicySelect = async (policyId: string) => {
    setSelectedPolicyId(policyId);
    setLoading(true);
    try {
      const policyRules = await getPolicyRules(policyId, DEFAULT_PROJECT_ID);
      setRules(policyRules);
    } catch (err: any) {
      setError(err.message || "Failed to load policy rules");
    } finally {
      setLoading(false);
    }
  };

  const handlePolicyProcessed = (doc: PolicyDocument, newRules: PolicyRule[]) => {
    setPolicies((prev) => [doc, ...prev.filter((p) => p.policy_id !== doc.policy_id)]);
    setSelectedPolicyId(doc.policy_id);
    setRules(newRules);
  };

  const handleRuleUpdated = (updatedRule: PolicyRule) => {
    setRules((prev) =>
      prev.map((r) =>
        r.policy_rule_id === updatedRule.policy_rule_id ? updatedRule : r
      )
    );
  };

  const filteredRules = rules.filter((r) => {
    if (filterStatus === "all") return true;
    return r.status === filterStatus;
  });

  const approvedCount = rules.filter((r) => r.status === "approved").length;
  const extractedCount = rules.filter((r) => r.status === "extracted").length;
  const rejectedCount = rules.filter((r) => r.status === "rejected").length;

  return (
    <main className="min-h-screen bg-[#090A0C] text-[#F5F7FA] p-6 md:p-10 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Top Header Nav */}
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
                Screen B — Policy Rule Review
              </span>
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-[#F5F7FA]">
              Company Policy Intelligence
            </h1>
            <p className="text-sm text-[#A5ACB8]">
              Upload studio policy documents, inspect Gemini-extracted candidate rules with verbatim source evidence, and approve enforceable policy logic.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-3 py-1 text-xs font-mono rounded-lg bg-[#15181D] border border-[#262B33] text-[#A5ACB8]">
              Project: Scene 12 (Northstar)
            </span>
          </div>
        </div>

        {/* Upload Section */}
        <PolicyUploadCard onPolicyProcessed={handlePolicyProcessed} />

        {/* Policy Documents & Rules Review Queue */}
        <div className="space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#15181D] border border-[#262B33] rounded-xl p-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold text-[#F5F7FA]">
                Extracted Rules Queue
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-[#262B33] text-[#A5ACB8] font-mono">
                {rules.length} Rules Total
              </span>
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setFilterStatus("all")}
                className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors ${
                  filterStatus === "all"
                    ? "bg-[#E3A544] text-[#090A0C] font-semibold"
                    : "bg-[#090A0C] text-[#A5ACB8] border border-[#262B33] hover:text-[#F5F7FA]"
                }`}
              >
                All ({rules.length})
              </button>
              <button
                onClick={() => setFilterStatus("extracted")}
                className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors ${
                  filterStatus === "extracted"
                    ? "bg-[#D89B3C] text-[#090A0C] font-semibold"
                    : "bg-[#090A0C] text-[#A5ACB8] border border-[#262B33] hover:text-[#F5F7FA]"
                }`}
              >
                Pending ({extractedCount})
              </button>
              <button
                onClick={() => setFilterStatus("approved")}
                className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors ${
                  filterStatus === "approved"
                    ? "bg-[#5EA876] text-[#090A0C] font-semibold"
                    : "bg-[#090A0C] text-[#A5ACB8] border border-[#262B33] hover:text-[#F5F7FA]"
                }`}
              >
                Approved ({approvedCount})
              </button>
              <button
                onClick={() => setFilterStatus("rejected")}
                className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors ${
                  filterStatus === "rejected"
                    ? "bg-[#D9544D] text-[#090A0C] font-semibold"
                    : "bg-[#090A0C] text-[#A5ACB8] border border-[#262B33] hover:text-[#F5F7FA]"
                }`}
              >
                Rejected ({rejectedCount})
              </button>
            </div>
          </div>

          {/* Rule Cards List */}
          {loading ? (
            <div className="bg-[#15181D] border border-[#262B33] rounded-xl p-8 text-center text-xs text-[#A5ACB8] flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4 text-[#E3A544]" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Loading policy rules...
            </div>
          ) : filteredRules.length === 0 ? (
            <div className="bg-[#15181D] border border-[#262B33] rounded-xl p-12 text-center text-[#A5ACB8]">
              <p className="text-sm font-medium mb-1">No policy rules found in this queue.</p>
              <p className="text-xs text-[#707782]">
                Upload a policy document above or click "All" to view extracted candidate rules.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {filteredRules.map((rule) => (
                <PolicyRuleCard
                  key={rule.policy_rule_id}
                  rule={rule}
                  onRuleUpdated={handleRuleUpdated}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

