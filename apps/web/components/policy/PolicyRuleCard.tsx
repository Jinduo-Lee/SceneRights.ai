"use client";

import React, { useState } from "react";
import { PolicyRule } from "../../lib/types";
import { approvePolicyRule, rejectPolicyRule } from "../../lib/api";

interface PolicyRuleCardProps {
  rule: PolicyRule;
  onRuleUpdated?: (updatedRule: PolicyRule) => void;
}

export const PolicyRuleCard: React.FC<PolicyRuleCardProps> = ({
  rule,
  onRuleUpdated,
}) => {
  const [currentRule, setCurrentRule] = useState<PolicyRule>(rule);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleApprove = async () => {
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const updated = await approvePolicyRule(
        currentRule.policy_id,
        currentRule.policy_rule_id,
        currentRule.project_id
      );
      setCurrentRule(updated);
      if (onRuleUpdated) onRuleUpdated(updated);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to approve rule.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const updated = await rejectPolicyRule(
        currentRule.policy_id,
        currentRule.policy_rule_id,
        currentRule.project_id
      );
      setCurrentRule(updated);
      if (onRuleUpdated) onRuleUpdated(updated);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to reject rule.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Status color styles matching v6.2.2 tokens
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "approved":
        return "bg-[#5EA876]/20 text-[#5EA876] border-[#5EA876]/40";
      case "rejected":
        return "bg-[#D9544D]/20 text-[#D9544D] border-[#D9544D]/40";
      default:
        return "bg-[#D89B3C]/20 text-[#D89B3C] border-[#D89B3C]/40";
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "high":
        return "text-[#D9544D]";
      case "medium":
        return "text-[#D89B3C]";
      default:
        return "text-[#A5ACB8]";
    }
  };

  return (
    <div className="bg-[#15181D] hover:bg-[#1B1F25] border border-[#262B33] rounded-xl p-5 transition-colors text-[#F5F7FA]">
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-[#262B33] text-[#A5ACB8]">
            {currentRule.policy_type}
          </span>
          <span className={`text-xs font-semibold uppercase ${getPriorityBadge(currentRule.priority)}`}>
            {currentRule.priority} Priority
          </span>
        </div>
        <span
          className={`text-xs font-semibold px-2.5 py-1 rounded-full border uppercase tracking-wider ${getStatusBadge(
            currentRule.status
          )}`}
        >
          {currentRule.status}
        </span>
      </div>

      {/* Generated Enforceable Rule Text */}
      <div className="mb-4">
        <div className="text-xs font-medium text-[#707782] uppercase mb-1">
          Enforceable Rule Interpretation
        </div>
        <p className="text-base font-semibold text-[#F5F7FA] leading-snug">
          {currentRule.rule_text}
        </p>
      </div>

      {/* Exact Source Quote Evidence Block (Spec §45) */}
      <div className="bg-[#090A0C] border border-[#262B33] rounded-lg p-3 mb-4">
        <div className="text-xs font-medium text-[#E3A544] uppercase mb-1 flex items-center gap-1">
          <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
            <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
          </svg>
          Verbatim Source Quote Evidence
        </div>
        <p className="text-xs italic text-[#A5ACB8] font-mono leading-relaxed">
          "{currentRule.source_quote}"
        </p>
      </div>

      {errorMsg && (
        <div className="text-xs text-[#D9544D] mb-3 bg-[#D9544D]/10 p-2 rounded border border-[#D9544D]/30">
          {errorMsg}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-2 border-t border-[#262B33]">
        <button
          onClick={handleReject}
          disabled={isSubmitting || currentRule.status === "rejected"}
          className="px-4 py-1.5 rounded-lg text-xs font-medium border border-[#D9544D]/40 text-[#D9544D] hover:bg-[#D9544D]/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Reject Rule
        </button>
        <button
          onClick={handleApprove}
          disabled={isSubmitting || currentRule.status === "approved"}
          className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-[#E3A544] hover:bg-[#F0B65B] text-[#090A0C] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Approve Rule
        </button>
      </div>
    </div>
  );
};

