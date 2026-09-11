"use client";

import { useEffect, useRef, useState } from "react";
import { Camera, ScanFace, UploadCloud } from "lucide-react";

interface SelfieCaptureProps {
  onCaptured: (photo: Blob) => void;
  onBack: () => void;
}

export default function SelfieCapture({ onCaptured, onBack }: SelfieCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    navigator.mediaDevices
      ?.getUserMedia({ video: { facingMode: "user" }, audio: false })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        setReady(true);
      })
      .catch(() => setError("Camera unavailable. Upload a selfie photo instead."));

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  function capture() {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => blob && onCaptured(blob), "image/jpeg", 0.92);
  }

  return (
    <div className="flex h-full flex-col items-center justify-center gap-6 p-10">
      <div className="flex items-center gap-3 text-slate-400">
        <ScanFace className="h-5 w-5" />
        <span className="text-xs font-medium uppercase tracking-wide">
          Live Selfie Capture
        </span>
      </div>

      <div className="relative aspect-square w-full max-w-xs overflow-hidden rounded-xl border border-slate-300 bg-slate-900">
        {ready ? (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="h-full w-full scale-x-[-1] object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center px-6 text-center text-xs text-slate-400">
            {error ?? "Requesting camera access…"}
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={onBack}
          className="rounded-md border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
        >
          Back
        </button>
        <button
          onClick={capture}
          disabled={!ready}
          className="flex items-center gap-1.5 rounded-md bg-slate-900 px-4 py-2 text-xs font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Camera className="h-3.5 w-3.5" />
          Capture Selfie
        </button>
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
        >
          <UploadCloud className="h-3.5 w-3.5" />
          Upload instead
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png"
          capture="user"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onCaptured(file);
          }}
        />
      </div>
    </div>
  );
}
