import { useEffect, useRef, useState, useCallback } from "react";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions";
import { Play, Pause, Plus, Trash2 } from "lucide-react";
import type { Chunk } from "../../types";

interface Props {
  audioUrl: string;
  existingChunks?: Chunk[];
  onChunkCreate: (start: number, end: number) => void;
  onChunkDelete?: (chunkId: string) => void;
  highlightChunkId?: string;
}

const REGION_COLOR = "rgba(79, 70, 229, 0.3)";
const REGION_BORDER = "rgba(79, 70, 229, 0.8)";

export default function WaveformEditor({
  audioUrl,
  existingChunks = [],
  onChunkCreate,
  onChunkDelete,
  highlightChunkId,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WaveSurfer | null>(null);
  const regionsRef = useRef<ReturnType<typeof RegionsPlugin.create> | null>(null);
  const [playing, setPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [pendingRegion, setPendingRegion] = useState<{ start: number; end: number } | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const regions = RegionsPlugin.create();
    regionsRef.current = regions;

    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: "#4b5563",
      progressColor: "#4f46e5",
      cursorColor: "#818cf8",
      barWidth: 2,
      barGap: 1,
      height: 80,
      plugins: [regions],
    });

    wsRef.current = ws;
    ws.load(audioUrl);

    ws.on("ready", () => setDuration(ws.getDuration()));
    ws.on("play", () => setPlaying(true));
    ws.on("pause", () => setPlaying(false));
    ws.on("finish", () => setPlaying(false));

    // Allow drag-to-create regions
    regions.enableDragSelection({ color: REGION_COLOR });
    regions.on("region-created", (region) => {
      region.setOptions({ color: REGION_COLOR, borderColor: REGION_BORDER });
      setPendingRegion({ start: region.start, end: region.end });
    });

    return () => {
      ws.destroy();
    };
  }, [audioUrl]);

  // Render existing chunks as regions
  useEffect(() => {
    const regions = regionsRef.current;
    if (!regions) return;
    regions.clearRegions();
    for (const chunk of existingChunks) {
      const isHighlight = chunk.id === highlightChunkId;
      regions.addRegion({
        id: chunk.id,
        start: chunk.start_sec,
        end: chunk.end_sec,
        color: isHighlight ? "rgba(234, 179, 8, 0.3)" : REGION_COLOR,
        drag: false,
        resize: false,
      });
    }
  }, [existingChunks, highlightChunkId]);

  const handleSavePending = useCallback(() => {
    if (pendingRegion) {
      onChunkCreate(pendingRegion.start, pendingRegion.end);
      setPendingRegion(null);
      regionsRef.current?.clearRegions();
    }
  }, [pendingRegion, onChunkCreate]);

  const handleDiscardPending = useCallback(() => {
    setPendingRegion(null);
    regionsRef.current?.clearRegions();
  }, []);

  const fmt = (s: number) =>
    `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

  return (
    <div className="bg-gray-900 rounded-xl p-4 space-y-3">
      <div ref={containerRef} className="w-full" />

      <div className="flex items-center gap-3 text-sm text-gray-400">
        <button
          onClick={() => wsRef.current?.playPause()}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-white transition-colors"
        >
          {playing ? <Pause size={14} /> : <Play size={14} />}
          {playing ? "Pause" : "Play"}
        </button>
        <span>Duration: {fmt(duration)}</span>

        {pendingRegion && (
          <div className="ml-auto flex items-center gap-2">
            <span className="text-indigo-400 text-xs">
              Selection: {fmt(pendingRegion.start)} → {fmt(pendingRegion.end)}
            </span>
            <button
              onClick={handleSavePending}
              className="flex items-center gap-1 px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 rounded text-white text-xs transition-colors"
            >
              <Plus size={12} /> Save Chunk
            </button>
            <button
              onClick={handleDiscardPending}
              className="flex items-center gap-1 px-2.5 py-1 bg-gray-700 hover:bg-gray-600 rounded text-gray-300 text-xs transition-colors"
            >
              <Trash2 size={12} /> Discard
            </button>
          </div>
        )}
      </div>

      {existingChunks.length > 0 && (
        <p className="text-xs text-gray-500">
          {existingChunks.length} chunk{existingChunks.length !== 1 ? "s" : ""} defined
          &mdash; drag on the waveform to add more
        </p>
      )}
    </div>
  );
}
