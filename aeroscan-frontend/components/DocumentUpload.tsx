"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud, ScanFace, CreditCard } from "lucide-react";
import { cx } from "@/lib/utils";

interface DocumentUploadProps {
  onFileSelected: (file: File | null) => void;
}

export default function DocumentUpload({ onFileSelected }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files?.[0] ?? null;
      onFileSelected(file);
    },
    [onFileSelected]
  );

  return (
    <div className="flex h-full flex-col items-center justify-center gap-6 p-10">
      <div className="flex items-center gap-3 text-slate-400">
        <CreditCard className="h-5 w-5" />
        <span className="text-xs font-medium uppercase tracking-wide">
          Passport / Visa / National ID
        </span>
        <ScanFace className="h-5 w-5" />
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cx(
          "flex w-full max-w-md cursor-pointer flex-col items-center gap-3 rounded-xl border-2 border-dashed px-8 py-14 text-center transition-colors",
          isDragging
            ? "border-checkpoint-cyan bg-cyan-50/60"
            : "border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-slate-100"
        )}
      >
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white shadow-sm ring-1 ring-slate-200">
          <UploadCloud className="h-5 w-5 text-slate-500" strokeWidth={2} />
        </div>
        <div>
          <p className="text-sm font-medium text-slate-700">
            Drop document image here, or click to browse
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Supports JPG, PNG up to 10MB
          </p>
        </div>
        <button
          type="button"
          className="mt-2 rounded-md bg-slate-900 px-4 py-2 text-xs font-medium text-white hover:bg-slate-800"
        >
          Select File
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={(e) => onFileSelected(e.target.files?.[0] ?? null)}
        />
      </div>
    </div>
  );
}
