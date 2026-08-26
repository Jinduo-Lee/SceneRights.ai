"use client";

import React, { useState } from "react";
import { Clip } from "../../lib/types";
import { uploadClip } from "../../lib/api";

interface ClipUploadCardProps {
  sceneId?: string;
  onClipUploaded?: (clip: Clip) => void;
}

export const ClipUploadCard: React.FC<ClipUploadCardProps> = ({
  sceneId = "scene_12",
  onClipUploaded,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [role, setRole] = useState<string>("comparison");
  const [uploading, setUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setErrorMsg(null);
      setSuccessMsg(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const clip = await uploadClip(file, sceneId, role);
      setUploading(false);
      setSuccessMsg(`Uploaded '${file.name}' as ${role.toUpperCase()} take.`);
      setFile(null);
      if (onClipUploaded) onClipUploaded(clip);
    } catch (err: any) {
      setUploading(false);
      setErrorMsg(err.message || "Failed to upload video clip.");
    }
  };

  return (
    <div className="bg-[#15181D] border border-[#262B33] rounded-xl p-6 text-[#F5F7FA]">
      <h2 className="text-lg font-semibold mb-1 text-[#F5F7FA]">
        Upload Original Video Take
      </h2>
      <p className="text-xs text-[#A5ACB8] mb-4">
        Supported formats: MP4, MOV, WEBM (Max 100MB, Max 60s duration). Keyframes are extracted deterministically via FFmpeg.
      </p>

      {/* Role Selection */}
      <div className="flex items-center gap-4 mb-4">
        <label className="text-xs font-medium text-[#707782] uppercase">
          Take Role:
        </label>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-xs text-[#F5F7FA] cursor-pointer">
            <input
              type="radio"
              name="clip-role"
              value="reference"
              checked={role === "reference"}
              onChange={() => setRole("reference")}
              className="accent-[#E3A544]"
            />
            Reference Take (Take A)
          </label>
          <label className="flex items-center gap-1.5 text-xs text-[#F5F7FA] cursor-pointer">
            <input
              type="radio"
              name="clip-role"
              value="comparison"
              checked={role === "comparison"}
              onChange={() => setRole("comparison")}
              className="accent-[#E3A544]"
            />
            Comparison Take (Take B / C)
          </label>
        </div>
      </div>

      {/* Dropzone */}
      <div className="border-2 border-dashed border-[#262B33] hover:border-[#E3A544]/50 rounded-lg p-6 text-center cursor-pointer transition-colors bg-[#090A0C]">
        <input
          type="file"
          accept=".mp4,.mov,.webm,.avi,.mkv"
          onChange={handleFileChange}
          className="hidden"
          id="video-file-input"
        />
        <label htmlFor="video-file-input" className="cursor-pointer block">
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
              d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          {file ? (
            <span className="text-sm font-semibold text-[#E3A544]">
              {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
            </span>
          ) : (
            <span className="text-xs text-[#A5ACB8]">
              Click to browse or drop your MP4 video take here
            </span>
          )}
        </label>
      </div>

      {errorMsg && (
        <div className="mt-3 text-xs text-[#D9544D] bg-[#D9544D]/10 p-3 rounded-lg border border-[#D9544D]/30">
          {errorMsg}
        </div>
      )}

      {successMsg && (
        <div className="mt-3 text-xs text-[#5EA876] bg-[#5EA876]/10 p-3 rounded-lg border border-[#5EA876]/30">
          {successMsg}
        </div>
      )}

      <div className="mt-5 flex justify-end">
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="px-5 py-2.5 rounded-lg text-xs font-semibold bg-[#E3A544] hover:bg-[#F0B65B] text-[#090A0C] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {uploading ? "Uploading Video..." : "Upload Take to GCS"}
        </button>
      </div>
    </div>
  );
};

