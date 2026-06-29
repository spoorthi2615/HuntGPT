import { useStore } from '../store';
import StatusBadge from '../components/StatusBadge';
import { AlertCircle, Target, Activity } from 'lucide-react';

export default function PipelineView() {
  const results = useStore((state) => state.results);

  if (!results.length) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500">
        No results available. Please run an analysis from the Log Input screen.
      </div>
    );
  }

  // Sort blocked to the top
  const sortedResults = [...results].sort((a, b) => {
    if (a.blocked === b.blocked) return 0;
    return a.blocked ? -1 : 1;
  });

  return (
    <div className="h-full flex flex-col max-w-5xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-50 mb-3">Pipeline Results</h2>
        <p className="text-slate-400 text-lg">Processed {results.length} log events.</p>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-4">
        {sortedResults.map((res, i) => (
          <div 
            key={i} 
            className={`rounded-xl border p-5 shadow-lg backdrop-blur-sm transition-all duration-300 hover:scale-[1.01] ${
              res.blocked 
                ? 'bg-red-950/20 border-red-900/30' 
                : 'bg-slate-800/40 border-slate-700/50'
            }`}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1 mr-4">
                <StatusBadge blocked={res.blocked} />
                <div className="mt-3 font-mono text-xs text-slate-400 bg-slate-900/50 p-2.5 rounded border border-slate-800 truncate">
                  {res.raw_log || 'N/A'}
                </div>
              </div>
              
              {!res.blocked && res.confidence != null && (
                <div className="flex flex-col items-end">
                  <span className="text-xs text-slate-400 font-medium uppercase tracking-wider mb-1">Confidence</span>
                  <div className="flex items-center gap-2">
                    <div className="h-2 w-16 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 rounded-full" 
                        style={{ width: `${res.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-lg font-bold text-blue-400">
                      {Math.round(res.confidence * 100)}%
                    </span>
                  </div>
                </div>
              )}
            </div>

            {res.blocked ? (
              <div className="flex items-start gap-3 mt-4 text-red-400 bg-red-500/5 p-3 rounded-lg border border-red-500/10">
                <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                <p className="text-sm">Malicious prompt injection instructions detected in payload. Pipeline execution halted for this event to protect SOC automation integrity.</p>
              </div>
            ) : (
              <div className="grid grid-cols-12 gap-6 mt-4">
                <div className="col-span-3 flex flex-col justify-center border-r border-slate-700/50 pr-4">
                  <span className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">Technique</span>
                  <div className="flex items-center gap-2">
                    <Target className="h-4 w-4 text-emerald-400" />
                    <span className="font-bold text-emerald-400">{res.technique_id || 'Unknown'}</span>
                  </div>
                </div>
                <div className="col-span-9 flex flex-col justify-center">
                  <span className="text-xs text-slate-500 font-medium uppercase tracking-wider mb-1">Hypothesis</span>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {res.hypothesis || 'No hypothesis generated.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
