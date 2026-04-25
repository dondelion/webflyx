import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle, XCircle, Loader2, Clock } from "lucide-react";
import { trainingApi } from "../../api/client";
import type { TrainingJob } from "../../types";

interface Props {
  voiceId: string;
  jobId: string;
  onComplete?: () => void;
}

const STATUS_ICONS = {
  queued: <Clock size={18} className="text-gray-400" />,
  running: <Loader2 size={18} className="text-indigo-400 animate-spin" />,
  completed: <CheckCircle size={18} className="text-green-400" />,
  failed: <XCircle size={18} className="text-red-400" />,
  cancelled: <XCircle size={18} className="text-gray-500" />,
};

export default function TrainingStatus({ voiceId, jobId, onComplete }: Props) {
  const { data: job } = useQuery<TrainingJob>({
    queryKey: ["training-job", voiceId, jobId],
    queryFn: () => trainingApi.getJob(voiceId, jobId),
    refetchInterval: (data) =>
      data?.status === "queued" || data?.status === "running" ? 3000 : false,
  });

  useEffect(() => {
    if (job?.status === "completed") {
      onComplete?.();
    }
  }, [job?.status, onComplete]);

  if (!job) return null;

  return (
    <div className="bg-gray-900 rounded-xl p-5 space-y-4">
      <div className="flex items-center gap-3">
        {STATUS_ICONS[job.status]}
        <div>
          <p className="font-medium capitalize">{job.status}</p>
          <p className="text-xs text-gray-400">{job.mode.replace("_", "-")} mode</p>
        </div>
        <span className="ml-auto text-sm font-mono text-gray-400">{job.progress}%</span>
      </div>

      {(job.status === "running" || job.status === "queued") && (
        <div className="w-full bg-gray-800 rounded-full h-2">
          <div
            className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      )}

      {job.status === "failed" && job.error_message && (
        <p className="text-sm text-red-400 bg-red-950/30 border border-red-900 rounded p-3 font-mono break-all">
          {job.error_message}
        </p>
      )}

      {job.status === "completed" && (
        <p className="text-sm text-green-400">
          Voice embedding created successfully. You can now synthesize speech.
        </p>
      )}
    </div>
  );
}
