import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Plus, Mic, ChevronRight, Trash2 } from "lucide-react";
import { voicesApi } from "../api/client";
import type { Voice } from "../types";

const STATUS_COLORS: Record<string, string> = {
  created: "text-gray-400 bg-gray-800",
  training: "text-yellow-400 bg-yellow-900/30",
  ready: "text-green-400 bg-green-900/30",
  failed: "text-red-400 bg-red-900/30",
};

export default function VoiceLibraryPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const { data: voices = [] } = useQuery<Voice[]>({
    queryKey: ["voices"],
    queryFn: voicesApi.list,
  });

  const createMutation = useMutation({
    mutationFn: () => voicesApi.create({ name, description }),
    onSuccess: (voice: Voice) => {
      qc.invalidateQueries({ queryKey: ["voices"] });
      setShowCreate(false);
      setName("");
      setDescription("");
      navigate(`/voices/${voice.id}/upload`);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => voicesApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["voices"] }),
  });

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Voice Library</h1>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={16} /> New Voice
        </button>
      </div>

      {showCreate && (
        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-4">
          <h2 className="font-semibold">Create New Voice Profile</h2>
          <input
            className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm border border-gray-700 focus:border-indigo-500 focus:outline-none"
            placeholder="Voice name (e.g. Morgan Freeman)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm border border-gray-700 focus:border-indigo-500 focus:outline-none"
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <div className="flex gap-2">
            <button
              disabled={!name.trim() || createMutation.isPending}
              onClick={() => createMutation.mutate()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
            >
              Create & Upload Samples
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {voices.length === 0 && !showCreate && (
        <div className="text-center py-20 text-gray-500">
          <Mic size={48} className="mx-auto mb-4 opacity-30" />
          <p>No voices yet. Create your first voice profile to get started.</p>
        </div>
      )}

      <div className="space-y-3">
        {voices.map((voice) => (
          <div
            key={voice.id}
            className="bg-gray-900 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold">{voice.name}</h3>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[voice.status]}`}
                  >
                    {voice.status}
                  </span>
                </div>
                {voice.description && (
                  <p className="text-sm text-gray-400 mt-0.5">{voice.description}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                {voice.status === "ready" && (
                  <button
                    onClick={() => navigate(`/voices/${voice.id}/synthesize`)}
                    className="text-xs px-3 py-1.5 bg-green-800/40 hover:bg-green-700/40 text-green-400 rounded-lg border border-green-800 transition-colors"
                  >
                    Synthesize
                  </button>
                )}
                <button
                  onClick={() => navigate(`/voices/${voice.id}/chunks`)}
                  className="flex items-center gap-1 text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  Manage <ChevronRight size={12} />
                </button>
                <button
                  onClick={() => deleteMutation.mutate(voice.id)}
                  className="text-gray-600 hover:text-red-400 transition-colors p-1"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
