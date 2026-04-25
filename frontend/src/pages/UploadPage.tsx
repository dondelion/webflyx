import { useCallback, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, FileAudio, ArrowRight, Trash2 } from "lucide-react";
import { voicesApi, samplesApi } from "../api/client";
import type { Voice, AudioSample } from "../types";

export default function UploadPage() {
  const { voiceId } = useParams<{ voiceId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);

  const { data: voice } = useQuery<Voice>({
    queryKey: ["voice", voiceId],
    queryFn: () => voicesApi.get(voiceId!),
  });

  const { data: samples = [] } = useQuery<AudioSample[]>({
    queryKey: ["samples", voiceId],
    queryFn: () => samplesApi.list(voiceId!),
  });

  const deleteMutation = useMutation({
    mutationFn: (sampleId: string) => samplesApi.delete(voiceId!, sampleId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["samples", voiceId] }),
  });

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || !voiceId) return;
      setUploading(true);
      for (const file of Array.from(files)) {
        await samplesApi.upload(voiceId, file);
      }
      qc.invalidateQueries({ queryKey: ["samples", voiceId] });
      setUploading(false);
    },
    [voiceId, qc]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const fmtDuration = (s: number | null) => {
    if (!s) return "–";
    return `${Math.floor(s / 60)}m ${Math.floor(s % 60)}s`;
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{voice?.name ?? "Voice"}</h1>
        <p className="text-gray-400 text-sm mt-1">Upload audio or video samples</p>
      </div>

      {/* Drop zone */}
      <div
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer ${
          dragging ? "border-indigo-500 bg-indigo-950/20" : "border-gray-700 hover:border-gray-500"
        }`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <Upload size={36} className="mx-auto mb-3 text-gray-500" />
        <p className="text-gray-300 font-medium">Drop audio or video files here</p>
        <p className="text-xs text-gray-500 mt-1">
          WAV, MP3, FLAC, MP4, MKV, MOV — audio is extracted from video automatically
        </p>
        {uploading && <p className="text-indigo-400 text-sm mt-3 animate-pulse">Uploading…</p>}
        <input
          id="file-input"
          type="file"
          accept=".wav,.mp3,.flac,.ogg,.m4a,.aac,.mp4,.mkv,.avi,.mov,.webm"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {/* Uploaded samples */}
      {samples.length > 0 && (
        <div className="space-y-2">
          <h2 className="font-semibold text-sm text-gray-400 uppercase tracking-wider">
            Uploaded Samples ({samples.length})
          </h2>
          {samples.map((s) => (
            <div
              key={s.id}
              className="flex items-center gap-3 bg-gray-900 rounded-lg px-4 py-3 border border-gray-800"
            >
              <FileAudio size={18} className="text-indigo-400 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{s.original_filename}</p>
                <p className="text-xs text-gray-500">
                  {fmtDuration(s.duration_sec)} · {s.sample_rate ? `${s.sample_rate / 1000}kHz` : ""} · {s.format?.toUpperCase()}
                </p>
              </div>
              <button
                onClick={() => deleteMutation.mutate(s.id)}
                className="text-gray-600 hover:text-red-400 transition-colors"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}

      {samples.length > 0 && (
        <button
          onClick={() => navigate(`/voices/${voiceId}/chunks`)}
          className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg font-medium transition-colors"
        >
          Select Chunks <ArrowRight size={16} />
        </button>
      )}
    </div>
  );
}
