import type { CoverageReport } from "../../types";

interface Props {
  report: CoverageReport;
  onSuggestionClick?: (chunkId: string) => void;
}

const CATEGORY_LABELS: Record<string, string> = {
  stops: "Stops",
  affricates: "Affricates",
  fricatives: "Fricatives",
  nasals: "Nasals",
  approximants: "Approximants",
  short_vowels: "Short Vowels",
  long_vowels: "Long Vowels",
  diphthongs: "Diphthongs",
};

export default function PhonemeChecklist({ report, onSuggestionClick }: Props) {
  const pct = Math.round(report.score * 100);
  const circumference = 2 * Math.PI * 28;
  const offset = circumference * (1 - report.score);

  return (
    <div className="space-y-5">
      {/* Score arc */}
      <div className="flex items-center gap-5">
        <svg width={72} height={72} viewBox="0 0 72 72">
          <circle cx={36} cy={36} r={28} fill="none" stroke="#1f2937" strokeWidth={8} />
          <circle
            cx={36}
            cy={36}
            r={28}
            fill="none"
            stroke={pct >= 80 ? "#22c55e" : pct >= 50 ? "#eab308" : "#ef4444"}
            strokeWidth={8}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            transform="rotate(-90 36 36)"
          />
          <text x={36} y={40} textAnchor="middle" className="text-sm font-bold" fill="white" fontSize={14}>
            {pct}%
          </text>
        </svg>
        <div>
          <p className="font-semibold text-white">Phoneme Coverage</p>
          <p className="text-sm text-gray-400">
            {report.covered_count} / {report.total_count} phonemes covered
          </p>
        </div>
      </div>

      {/* By category */}
      <div className="space-y-3">
        {Object.entries(report.by_category).map(([cat, data]) => (
          <div key={cat}>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                {CATEGORY_LABELS[cat] ?? cat}
              </span>
              <span className="text-xs text-gray-500">
                {data.covered.length}/{data.covered.length + data.missing.length}
              </span>
            </div>
            <div className="flex flex-wrap gap-1">
              {data.covered.map((p) => (
                <span
                  key={p}
                  className="px-1.5 py-0.5 rounded text-[11px] font-mono bg-green-900/40 text-green-400 border border-green-800"
                  title="Covered"
                >
                  /{p}/
                </span>
              ))}
              {data.missing.map((p) => (
                <span
                  key={p}
                  className="px-1.5 py-0.5 rounded text-[11px] font-mono bg-red-900/30 text-red-400 border border-red-900"
                  title="Missing"
                >
                  /{p}/
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Suggestions */}
      {report.suggestions.length > 0 && (
        <div>
          <p className="text-xs font-medium text-yellow-400 uppercase tracking-wider mb-2">
            Suggested Chunks to Add
          </p>
          <div className="space-y-1.5">
            {report.suggestions.slice(0, 5).map((s) => (
              <button
                key={s.chunk_id}
                onClick={() => onSuggestionClick?.(s.chunk_id)}
                className="w-full text-left px-3 py-2 rounded-lg bg-yellow-900/20 border border-yellow-900/40 hover:border-yellow-600 transition-colors"
              >
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-xs text-yellow-300 font-medium">
                    +{s.gain} new phoneme{s.gain !== 1 ? "s" : ""}
                  </span>
                  <span className="text-[10px] text-gray-500 font-mono">
                    {s.start_sec.toFixed(1)}s – {s.end_sec.toFixed(1)}s
                  </span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {s.fills_phonemes.map((p) => (
                    <span
                      key={p}
                      className="px-1 py-0.5 rounded text-[10px] font-mono bg-yellow-800/40 text-yellow-300"
                    >
                      /{p}/
                    </span>
                  ))}
                </div>
                {s.transcript && (
                  <p className="text-xs text-gray-400 mt-0.5 truncate">{s.transcript}</p>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Suggested sentences when coverage is low */}
      {report.suggested_sentences.length > 0 && report.score < 0.8 && (
        <div>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
            Record These Sentences for Better Coverage
          </p>
          <ul className="space-y-1">
            {report.suggested_sentences.map((s, i) => (
              <li key={i} className="text-sm text-gray-300 italic bg-gray-800 rounded px-3 py-2">
                &ldquo;{s}&rdquo;
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
