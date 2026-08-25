"use client";

import React, { useState } from "react";
import { PolicyDocument, PolicyRule } from "../../lib/types";
import { uploadPolicy, processPolicy } from "../../lib/api";

interface PolicyUploadCardProps {
  onPolicyProcessed?: (policy: PolicyDocument, rules: PolicyRule[]) => void;
}

export const PolicyUploadCard: React.FC<PolicyUploadCardProps> = ({
  onPolicyProcessed,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [currentDoc, setCurrentDoc] = useState<PolicyDocument | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [statusText, setStatusText] = useState<string>("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setErrorMsg(null);
      setCurrentDoc(null);
    }
  };

  const handleUploadAndProcess = async () => {
    if (!file) return;
    setUploading(true);
    setErrorMsg(null);
    setStatusText("Uploading document to private GCS storage...");

    try {
      // Step 1: Upload document
      const doc = await uploadPolicy(file);
      setCurrentDoc(doc);
      setUploading(false);

      // Step 2: Trigger Gemini extraction & exact quote grounding
      setProcessing(true);
      setStatusText("Gemini is extracting policy rules and validating exact source quotes...");

      const res = await processPolicy(doc.policy_id, doc.project_id);
      setProcessing(false);
      setStatusText(`Extraction completed! ${res.rules_extracted} rules ready for review.`);

      if (onPolicyProcessed) {
        onPolicyProcessed({ ...doc, status: "ready" }, res.rules);
      }
    } catch (err: any) {
      setUploading(false);
      setProcessing(false);
      setErrorMsg(err.message || "Failed to upload and process policy document.");
    }
  };

  return (
    <div className="bg-[#15181D] border border-[#262B33] rounded-xl p-6 text-[#F5F7FA]">
      <h2 className="text-lg font-semibold mb-1 text-[#F5F7FA]">
        Upload Studio Policy Document
      </h2>
      <p className="text-xs text-[#A5ACB8] mb-4">
        Supported formats: PDF, DOCX, TXT, Markdown (Max 10MB). Gemini will extract candidate rules with exact verbatim source quotes.
      </p>

      {/* File Dropzone / Selector */}
      <div className="border-2 border-dashed border-[#262B33] hover:border-[#E3A544]/50 rounded-lg p-6 text-center cursor-pointer transition-colors bg-[#090A0C]">
        <input
          type="file"
          accept=".txt,.md,.pdf,.docx"
          onChange={handleFileChange}
          className="hidden"
          id="policy-file-input"
        />
        <label htmlFor="policy-file-input" className="cursor-pointer block">
          <svg
            className="w-10 h-10 mx-auto mb-2 text-[#707782]"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          {file ? (
            <span className="text-sm font-semibold text-[#E3A544]">
              {file.name} ({(file.size / 1024).toFixed(1)} KB)
            </span>
          ) : (
            <span className="text-xs text-[#A5ACB8]">
              Click to browse or drop your policy file here
            </span>
          )}
        </label>
      </div>

      {errorMsg && (
        <div className="mt-3 text-xs text-[#D9544D] bg-[#D9544D]/10 p-3 rounded-lg border border-[#D9544D]/30">
          {errorMsg}
        </div>
      )}

      {statusText && !errorMsg && (
        <div className="mt-3 text-xs text-[#5F8EC9] bg-[#5F8EC9]/10 p-3 rounded-lg border border-[#5F8EC9]/30 flex items-center gap-2">
          {(uploading || processing) && (
            <svg className="animate-spin h-3.5 w-3.5 text-[#5F8EC9]" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          )}
          <span>{statusText}</span>
        </div>
      )}

      <div className="mt-5 flex justify-end">
        <button
          onClick={handleUploadAndProcess}
          disabled={!file || uploading || processing}
          className="px-5 py-2.5 rounded-lg text-xs font-semibold bg-[#E3A544] hover:bg-[#F0B65B] text-[#090A0C] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {uploading
            ? "Uploading..."
            : processing
            ? "Processing with Gemini..."
            : "Upload & Extract Rules"}
        </button>
      </div>
    </div>
  );
};

