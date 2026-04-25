import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Copy, Eye, EyeOff } from "lucide-react";
import { authApi, voicesApi } from "../api/client";
import type { APIKey, Voice } from "../types";

interface CreatedKey extends APIKey {
  raw_key: string;
}

export default function ApiKeysPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [voiceId, setVoiceId] = useState("");
  const [newKey, setNewKey] = useState<CreatedKey | null>(null);
  const [showKey, setShowKey] = useState(false);

  const { data: keys = [] } = useQuery<APIKey[]>({
    queryKey: ["api-keys"],
    queryFn: authApi.listKeys,
  });

  const { data: voices = [] } = useQuery<Voice[]>({
    queryKey: ["voices"],
    queryFn: voicesApi.list,
  });

  const createMutation = useMutation({
    mutationFn: () => authApi.createKey({ name, voice_id: voiceId || undefined }),
    onSuccess: (key: CreatedKey) => {
      qc.invalidateQueries({ queryKey: ["api-keys"] });
      setNewKey(key);
      setName("");
      setVoiceId("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => authApi.deleteKey(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["api-keys"] }),
  });

  const copy = (text: string) => navigator.clipboard.writeText(text);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">API Keys</h1>
      <p className="text-gray-400 text-sm">
        Use these keys to access the public <code className="text-indigo-400">/v1/</code> API from external apps.
      </p>

      {/* Create new key */}
      <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-3">
        <h2 className="font-semibold text-sm">Create New Key</h2>
        <input
          className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm border border-gray-700 focus:border-indigo-500 focus:outline-none"
          placeholder="Key name (e.g. e-book reader app)"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <select
          className="w-full bg-gray-800 rounded-lg px-3 py-2 text-sm border border-gray-700 focus:border-indigo-500 focus:outline-none"
          value={voiceId}
          onChange={(e) => setVoiceId(e.target.value)}
        >
          <option value="">All voices (global key)</option>
          {voices.map((v) => (
            <option key={v.id} value={v.id}>{v.name}</option>
          ))}
        </select>
        <button
          disabled={!name.trim() || createMutation.isPending}
          onClick={() => createMutation.mutate()}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
        >
          <Plus size={14} /> Generate Key
        </button>
      </div>

      {/* Newly created key — show once */}
      {newKey && (
        <div className="bg-green-950/30 border border-green-800 rounded-xl p-4 space-y-2">
          <p className="text-sm text-green-400 font-medium">
            Key created — copy it now, it won&apos;t be shown again.
          </p>
          <div className="flex items-center gap-2 bg-gray-900 rounded-lg px-3 py-2 font-mono text-sm">
            <span className="flex-1 truncate">
              {showKey ? newKey.raw_key : "wfv_" + "•".repeat(32)}
            </span>
            <button onClick={() => setShowKey((v) => !v)} className="text-gray-400">
              {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
            <button onClick={() => copy(newKey.raw_key)} className="text-gray-400 hover:text-white">
              <Copy size={14} />
            </button>
          </div>
          <button
            onClick={() => setNewKey(null)}
            className="text-xs text-gray-500 hover:text-gray-300"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Key list */}
      <div className="space-y-2">
        {keys.map((key) => (
          <div
            key={key.id}
            className="flex items-center justify-between bg-gray-900 rounded-lg px-4 py-3 border border-gray-800"
          >
            <div>
              <p className="text-sm font-medium">{key.name}</p>
              <p className="text-xs text-gray-500">
                {key.voice_id
                  ? `Scoped to voice ${voices.find((v) => v.id === key.voice_id)?.name ?? key.voice_id}`
                  : "All voices"}{" "}
                · Created {new Date(key.created_at).toLocaleDateString()}
              </p>
            </div>
            <button
              onClick={() => deleteMutation.mutate(key.id)}
              className="text-gray-600 hover:text-red-400 transition-colors"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
        {keys.length === 0 && (
          <p className="text-gray-500 text-sm text-center py-8">No API keys yet.</p>
        )}
      </div>

      {/* API reference */}
      <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 space-y-2">
        <h3 className="font-semibold text-sm">Quick Reference</h3>
        <pre className="text-xs text-gray-300 overflow-auto bg-gray-800 rounded p-3">
{`# Synthesize speech via the public API
curl -X POST https://your-host/v1/voices/{voice_id}/tts \\
  -H "X-API-Key: wfv_..." \\
  -H "Content-Type: application/json" \\
  -d '{"text":"Hello world","speed":1.0}' \\
  --output speech.wav`}
        </pre>
      </div>
    </div>
  );
}
