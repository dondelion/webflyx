import { useState } from "react";
import { Check, X, Mic, Loader2, Trash2 } from "lucide-react";
import type { Chunk } from "../../types";

interface Props {
  voiceId: string;
  chunks: Chunk[];
  onUpdate: (chunkId: string, data: { transcript?: string; selected?: boolean }) => void;
  onDelete: (chunkId: string) => void;
  onTranscribe: (chunkId: string) => void;
  onHover: (chunkId: string | null) => void;
}

export default function ChunkList({
  chunks,
  onUpdate,
  onDelete,
  onTranscribe,
  onHover,
}: Props) {
  const [editing, setEditing] = useState<Record<string, string>>({});

  const fmt = (s: number) =>
    `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

  return (
    <div className="space-y-2">
      {chunks.length === 0 && (
        <p className="text-gray-500 text-sm text-center py-8">
          Drag on the waveform to create your first chunk
        </p>
      )}
      {chunks.map((chunk) => (
        <div
          key={chunk.id}
          className={`bg-gray-900 rounded-lg p-3 border transition-colors ${
            chunk.selected ? "border-indigo-500" : "border-gray-800"
          }`}
          onMouseEnter={() => onHover(chunk.id)}
          onMouseLeave={() => onHover(null)}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-400 font-mono">
              {fmt(chunk.start_sec)} → {fmt(chunk.end_sec)}{" "}
              <span className="ml-1 text-gray-600">
                ({(chunk.end_sec - chunk.start_sec).toFixed(1)}s)
              </span>
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => onUpdate(chunk.id, { selected: !chunk.selected })}
                className={`text-xs px-2 py-0.5 rounded font-medium transition-colors ${
                  chunk.selected
                    ? "bg-indigo-600 text-white"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
              >
                {chunk.selected ? "Selected" : "Select"}
              </button>
              <button
                onClick={() => onDelete(chunk.id)}
                className="text-gray-600 hover:text-red-400 transition-colors"
              >
                <Trash2 size={13} />
              </button>
            </div>
          </div>

          {/* Transcript */}
          {editing[chunk.id] !== undefined ? (
            <div className="flex items-start gap-2">
              <textarea
                className="flex-1 bg-gray-800 text-sm text-gray-100 rounded px-2 py-1 resize-none border border-gray-700 focus:border-indigo-500 focus:outline-none"
                rows={2}
                value={editing[chunk.id]}
                onChange={(e) =>
                  setEditing((prev) => ({ ...prev, [chunk.id]: e.target.value }))
                }
              />
              <div className="flex flex-col gap-1">
                <button
                  onClick={() => {
                    onUpdate(chunk.id, { transcript: editing[chunk.id] });
                    setEditing((prev) => {
                      const n = { ...prev };
                      delete n[chunk.id];
                      return n;
                    });
                  }}
                  className="p-1 text-green-400 hover:text-green-300"
                >
                  <Check size={14} />
                </button>
                <button
                  onClick={() =>
                    setEditing((prev) => {
                      const n = { ...prev };
                      delete n[chunk.id];
                      return n;
                    })
                  }
                  className="p-1 text-gray-500 hover:text-gray-300"
                >
                  <X size={14} />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-start justify-between gap-2">
              <p
                className="text-sm text-gray-300 flex-1 cursor-pointer hover:text-white min-h-[1.25rem]"
                onClick={() =>
                  setEditing((prev) => ({ ...prev, [chunk.id]: chunk.transcript ?? "" }))
                }
              >
                {chunk.transcript || (
                  <span className="text-gray-600 italic">No transcript — click to add</span>
                )}
              </p>
              {!chunk.transcript && (
                <button
                  onClick={() => onTranscribe(chunk.id)}
                  disabled={chunk.transcription_pending}
                  className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 disabled:opacity-50 shrink-0"
                >
                  {chunk.transcription_pending ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <Mic size={12} />
                  )}
                  Auto
                </button>
              )}
            </div>
          )}

          {chunk.phonemes && chunk.phonemes.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {chunk.phonemes.slice(0, 8).map((p, i) => (
                <span
                  key={i}
                  className="text-[10px] px-1 py-0.5 bg-gray-800 text-gray-400 rounded font-mono"
                >
                  {p}
                </span>
              ))}
              {chunk.phonemes.length > 8 && (
                <span className="text-[10px] text-gray-600">+{chunk.phonemes.length - 8} more</span>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
