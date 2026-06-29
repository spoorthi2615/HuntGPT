import { useMemo } from 'react';
import { useStore } from '../store';
import { LayoutGrid } from 'lucide-react';

const TACTICS = [
  'Initial Access', 'Execution', 'Persistence', 'Privilege Escalation', 
  'Defense Evasion', 'Credential Access', 'Discovery', 'Lateral Movement',
  'Collection', 'Command and Control', 'Exfiltration', 'Impact'
];

export default function AttackHeatmap() {
  const results = useStore((state) => state.results);

  // Group clean detections by technique ID
  const techniqueCounts = useMemo(() => {
    const counts = {};
    results.forEach(r => {
      if (!r.blocked && r.technique_id) {
        counts[r.technique_id] = (counts[r.technique_id] || 0) + 1;
      }
    });
    return counts;
  }, [results]);

  // For demo, we just assign techniques to random tactics 
  // In a real app, this would use the mapping from techniques.json
  const grid = useMemo(() => {
    const layout = TACTICS.map(t => ({ name: t, techniques: [] }));
    Object.entries(techniqueCounts).forEach(([tid, count], idx) => {
      layout[idx % TACTICS.length].techniques.push({ id: tid, count });
    });
    return layout;
  }, [techniqueCounts]);

  const getColor = (count) => {
    if (count === 0) return 'bg-slate-800 border-slate-700/50';
    if (count === 1) return 'bg-blue-900/40 border-blue-500/30 text-blue-200';
    if (count <= 3) return 'bg-blue-600/60 border-blue-400/50 text-white';
    return 'bg-blue-500 border-blue-400 text-white shadow-[0_0_15px_rgba(59,130,246,0.5)]';
  };

  return (
    <div className="h-full flex flex-col max-w-full">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-50 mb-3 flex items-center gap-3">
          <LayoutGrid className="text-blue-500 h-8 w-8" />
          ATT&CK Heatmap
        </h2>
        <p className="text-slate-400 text-lg">Technique occurrence matrix generated from current session pipeline results.</p>
      </div>

      <div className="flex-1 overflow-auto bg-slate-900/50 rounded-2xl border border-slate-800 p-6 shadow-xl backdrop-blur-sm">
        <div className="flex gap-4 min-w-max pb-4">
          {grid.map(tactic => (
            <div key={tactic.name} className="flex flex-col w-48 shrink-0">
              <div className="bg-slate-800/80 border border-slate-700 rounded-t-lg p-3 mb-2 text-center shadow-sm">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">{tactic.name}</span>
              </div>
              <div className="flex flex-col gap-2">
                {tactic.techniques.length === 0 ? (
                  <div className="h-12 rounded border border-dashed border-slate-700/50 opacity-20"></div>
                ) : (
                  tactic.techniques.map(tech => (
                    <div 
                      key={tech.id} 
                      className={`h-12 rounded border flex items-center justify-center text-sm font-bold transition-colors ${getColor(tech.count)}`}
                    >
                      {tech.id}
                      <span className="ml-2 px-1.5 py-0.5 rounded-full bg-black/20 text-[10px]">{tech.count}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
