import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, BarChart2 } from "lucide-react";
import { samplesApi, chunksApi } from "../api/client";
import WaveformEditor from "../components/WaveformEditor/WaveformEditor";
import ChunkList from "../components/WaveformEditor/ChunkList";
import PhonemeChecklist from "../components/PhonemeChecklist/PhonemeChecklist";
import type { AudioSample, Chunk, CoverageReport } from "../types";

export default function ChunkEditorPage() {
  const { voiceId } = useParams<{ voiceId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [activeSampleId, setActiveSampleId] = useState<string | null>(null);
  const [highlightChunkId, setHighlightChunkId] = useState<string | null>(null);
  const [showCoverage, setShowCoverage] = useState(false);

  const { data: samples = [] } = useQuery<AudioSample[]>({
    queryKey: ["samples", voiceId],
    queryFn: () => samplesApi.list(voiceId!),
  });

  useEffect(() => {
    if (samples.length > 0 && !activeSampleId) {
      setActiveSampleId(samples[0].id);
    }
  }, [samples, activeSampleId]);

  const activeSample = samples.find((s) => s.id === activeSampleId) ?? samples[0] ?? null;

  const { data: chunks = [] } = useQuery<Chunk[]>({
    queryKey: ["chunks", voiceId, activeSample?.id],
    queryFn: () => chunksApi.listForSample(voiceId!, activeSample!.id),
    enabled: !!activeSample,
  });

  const { data: coverage } = useQuery<CoverageReport>({
    queryKey: ["coverage", voiceId],
    queryFn: () => chunksApi.coverage(voiceId!),
    enabled: showCoverage,
    refetchInterval: showCoverage ? 5000 : false,
  });

  const createMutation = useMutation({
    mutationFn: ({ start, end }: { start: number; end: number }) =>
      chunksApi.create(voiceId!, activeSample!.id, { start_sec: start, end_sec: end }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["chunks", voiceId] }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { transcript?: string; selected?: boolean } }) =>
      chunksApi.update(voiceId!, id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["chunks", voiceId] });
      qc.invalidateQueries({ queryKey: ["coverage", voiceId] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => chunksApi.delete(voiceId!, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["chunks", voiceId] }),
  });

  const transcribeMutation = useMutation({
    mutationFn: (id: string) => chunksApi.transcribe(voiceId!, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["chunks", voiceId] }),
  });

  const selectedCount = chunks.filter((c) => c.selected).length;

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Chunk Editor</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowCoverage((v) => !v)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
              showCoverage ? "bg-indigo-700 text-white" : "bg-gray-800 text-gray-300 hover:bg-gray-700"
            }`}
          >
            <BarChart2 size={15} /> Coverage
          </button>
          <button
            disabled={selectedCount === 0}
            onClick={() => navigate(`/voices/${voiceId}/train`)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded-lg text-sm font-medium transition-colors"
          >
            Train ({selectedCount} chunks) <ArrowRight size={15} />
          </button>
        </div>
      </div>

      {/* Sample selector */}
      {samples.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {samples.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSampleId(s.id)}
              className={`shrink-0 px-3 py-1.5 rounded-lg text-sm transition-colors ${
                s.id === activeSample?.id
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
              }`}
            >
              {s.original_filename}
            </button>
          ))}
        </div>
      )}

      <div className={`grid gap-5 ${showCoverage ? "grid-cols-[1fr_300px]" : "grid-cols-1"}`}>
        <div className="space-y-4">
          {activeSample && (
            <WaveformEditor
              audioUrl={`/api/voices/${voiceId}/samples/${activeSample.id}/stream`}
              existingChunks={chunks}
              highlightChunkId={highlightChunkId ?? undefined}
              onChunkCreate={(start, end) => createMutation.mutate({ start, end })}
              onChunkDelete={(id) => deleteMutation.mutate(id)}
            />
          )}
          <ChunkList
            voiceId={voiceId!}
            chunks={chunks}
            onUpdate={(id, data) => updateMutation.mutate({ id, data })}
            onDelete={(id) => deleteMutation.mutate(id)}
            onTranscribe={(id) => transcribeMutation.mutate(id)}
            onHover={(id) => setHighlightChunkId(id)}
          />
        </div>

        {showCoverage && coverage && (
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 self-start sticky top-0">
            <PhonemeChecklist
              report={coverage}
              onSuggestionClick={(chunkId) => setHighlightChunkId(chunkId)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
