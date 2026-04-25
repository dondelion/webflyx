import { useState, useRef } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Play, Download, Loader2 } from "lucide-react";
import { voicesApi } from "../api/client";
import type { Voice } from "../types";

export default function SynthesizePage() {
  const { voiceId } = useParams<{ voiceId: string }>();
  const [text, setText] = useState("");
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0);
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  const { data: voice } = useQuery<Voice>({
    queryKey: ["voice", voiceId],
    queryFn: () => voicesApi.get(voiceId!),
  });

  const synthesize = async () => {
    if (!text.trim() || !voiceId) return;
    setLoading(true);
    setAudioUrl(null);

    const res = await fetch(`/api/voices/${voiceId}/synthesize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, speed, pitch_semitones: pitch, format: "wav" }),
    });

    if (res.ok) {
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      setTimeout(() => audioRef.current?.play(), 100);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Synthesize Speech</h1>
        <p className="text-gray-400 text-sm mt-1">Voice: {voice?.name}</p>
      </div>

      <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
        <textarea
          className="w-full bg-gray-800 rounded-lg px-4 py-3 text-sm border border-gray-700 focus:border-indigo-500 focus:outline-none resize-none"
          rows={5}
          placeholder="Enter text to synthesize…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={5000}
        />
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{text.length}/5000</span>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-400 block mb-1">Speed: {speed.toFixed(1)}x</label>
            <input
              type="range" min={0.25} max={4} step={0.05}
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="w-full accent-indigo-500"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 block mb-1">
              Pitch: {pitch > 0 ? "+" : ""}{pitch} semitones
            </label>
            <input
              type="range" min={-12} max={12} step={1}
              value={pitch}
              onChange={(e) => setPitch(parseInt(e.target.value))}
              className="w-full accent-indigo-500"
            />
          </div>
        </div>

        <button
          onClick={synthesize}
          disabled={loading || !text.trim()}
          className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded-lg font-medium transition-colors"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
          {loading ? "Generating…" : "Synthesize"}
        </button>
      </div>

      {audioUrl && (
        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-3">
          <p className="text-sm font-medium text-green-400">Audio ready</p>
          <audio ref={audioRef} controls src={audioUrl} className="w-full" />
          <a
            href={audioUrl}
            download="synthesis.wav"
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
          >
            <Download size={14} /> Download WAV
          </a>
        </div>
      )}
    </div>
  );
}
