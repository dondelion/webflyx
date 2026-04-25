import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Zap, Settings2, ArrowRight } from "lucide-react";
import { chunksApi, trainingApi } from "../api/client";
import TrainingStatus from "../components/TrainingStatus/TrainingStatus";
import type { Chunk, TrainingJob } from "../types";

export default function TrainPage() {
  const { voiceId } = useParams<{ voiceId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [mode, setMode] = useState<"zero_shot" | "finetune">("zero_shot");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const { data: chunks = [] } = useQuery<Chunk[]>({
    queryKey: ["chunks", voiceId, "all"],
    queryFn: () => chunksApi.listAll(voiceId!),
  });

  const { data: jobs = [] } = useQuery<TrainingJob[]>({
    queryKey: ["training-jobs", voiceId],
    queryFn: () => trainingApi.listJobs(voiceId!),
  });

  const trainMutation = useMutation({
    mutationFn: () => trainingApi.start(voiceId!, { mode }),
    onSuccess: (job: TrainingJob) => {
      qc.invalidateQueries({ queryKey: ["training-jobs", voiceId] });
      setActiveJobId(job.id);
    },
  });

  const selected = chunks.filter((c) => c.selected);
  const totalDuration = selected.reduce((sum, c) => sum + (c.end_sec - c.start_sec), 0);

  const latestJob = jobs[0];
  const displayJobId = activeJobId ?? latestJob?.id ?? null;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Train Voice</h1>

      <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
        <h2 className="font-semibold">Training Mode</h2>

        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => setMode("zero_shot")}
            className={`p-4 rounded-xl border text-left transition-colors ${
              mode === "zero_shot"
                ? "border-indigo-500 bg-indigo-950/40"
                : "border-gray-700 hover:border-gray-500"
            }`}
          >
            <Zap size={20} className="text-indigo-400 mb-2" />
            <p className="font-medium">Zero-Shot</p>
            <p className="text-xs text-gray-400 mt-1">
              Fast embedding from reference audio. Works with as little as 6 seconds.
            </p>
          </button>
          <button
            onClick={() => setMode("finetune")}
            className={`p-4 rounded-xl border text-left transition-colors ${
              mode === "finetune"
                ? "border-indigo-500 bg-indigo-950/40"
                : "border-gray-700 hover:border-gray-500"
            }`}
          >
            <Settings2 size={20} className="text-indigo-400 mb-2" />
            <p className="font-medium">Fine-tune</p>
            <p className="text-xs text-gray-400 mt-1">
              Full model fine-tuning. Higher quality but requires 2+ min of audio and a GPU.
            </p>
          </button>
        </div>

        <div className="text-sm text-gray-400 bg-gray-800 rounded-lg p-3">
          <span className="font-medium text-white">{selected.length}</span> chunks selected ·{" "}
          <span className="font-medium text-white">{totalDuration.toFixed(1)}s</span> total audio
          {mode === "zero_shot" && totalDuration < 6 && (
            <p className="text-yellow-400 mt-1 text-xs">Minimum 6 seconds recommended for zero-shot.</p>
          )}
          {mode === "finetune" && totalDuration < 120 && (
            <p className="text-yellow-400 mt-1 text-xs">Minimum 2 minutes recommended for fine-tuning.</p>
          )}
        </div>

        <button
          onClick={() => trainMutation.mutate()}
          disabled={trainMutation.isPending || selected.length === 0}
          className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 rounded-lg font-medium transition-colors"
        >
          Start Training <ArrowRight size={16} />
        </button>
      </div>

      {displayJobId && (
        <TrainingStatus
          voiceId={voiceId!}
          jobId={displayJobId}
          onComplete={() => navigate(`/voices/${voiceId}/synthesize`)}
        />
      )}

      {jobs.length > 1 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">Previous Jobs</h3>
          {jobs.slice(1).map((job) => (
            <div
              key={job.id}
              className="flex items-center justify-between bg-gray-900 rounded-lg px-4 py-2.5 border border-gray-800 text-sm"
            >
              <span className="text-gray-400 capitalize">{job.status}</span>
              <span className="text-gray-500 font-mono text-xs">
                {new Date(job.created_at).toLocaleDateString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
