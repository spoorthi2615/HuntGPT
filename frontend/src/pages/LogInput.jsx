import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Terminal, ArrowRight, Loader2 } from 'lucide-react';
import client from '../api/client';
import { useStore } from '../store';

export default function LogInput() {
  const [logs, setLogs] = useState('');
  const [status, setStatus] = useState('idle'); // idle, loading, done
  const [loadingMsg, setLoadingMsg] = useState('');
  const setResults = useStore((state) => state.setResults);
  const navigate = useNavigate();

  const handleAnalyze = async () => {
    if (!logs.trim()) return;
    
    setStatus('loading');
    setLoadingMsg('Running PromptGuard filter...');
    
    // Simulate progression of steps for UX
    const steps = ['Running PromptGuard filter...', 'Running ThreatHunter LLM inference...', 'Calculating self-consistency scores...'];
    let stepIdx = 0;
    const interval = setInterval(() => {
      stepIdx++;
      if (stepIdx < steps.length) {
        setLoadingMsg(steps[stepIdx]);
      }
    }, 2000);

    try {
      const logBatch = logs.split('\n').filter(l => l.trim().length > 0);
      const response = await client.post('/analyze', { log_batch: logBatch });
      
      clearInterval(interval);
      setResults(response.data.results.map((res, i) => ({ ...res, raw_log: logBatch[i] })));
      setStatus('done');
      navigate('/pipeline');
    } catch (error) {
      clearInterval(interval);
      console.error(error);
      alert('Analysis failed. Check console for details.');
      setStatus('idle');
    }
  };

  return (
    <div className="h-full flex flex-col max-w-4xl mx-auto pt-10">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-50 mb-3">Threat Analysis Input</h2>
        <p className="text-slate-400 text-lg">Paste your Zeek log batch below. The pipeline will automatically filter prompt injections before hunting for threats.</p>
      </div>

      <div className="flex-1 bg-slate-900/80 rounded-2xl border border-slate-700/50 shadow-2xl overflow-hidden flex flex-col backdrop-blur-sm relative">
        <div className="flex items-center px-4 py-3 border-b border-slate-800 bg-slate-800/30">
          <Terminal className="h-5 w-5 text-slate-500 mr-2" />
          <span className="text-sm font-medium text-slate-400">Raw Logs (Zeek format)</span>
        </div>
        
        <textarea 
          value={logs}
          onChange={(e) => setLogs(e.target.value)}
          placeholder="1592398284.456	C123	192.168.1.5	12345	10.0.0.8	80	tcp	http..."
          className="flex-1 w-full bg-transparent p-6 text-slate-300 font-mono text-sm focus:outline-none resize-none"
          disabled={status !== 'idle'}
        />

        {status === 'loading' && (
          <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm flex flex-col items-center justify-center z-10">
            <Loader2 className="h-10 w-10 text-blue-500 animate-spin mb-4" />
            <p className="text-lg font-medium text-blue-100">{loadingMsg}</p>
          </div>
        )}
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={handleAnalyze}
          disabled={status !== 'idle' || !logs.trim()}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 text-white px-6 py-3 rounded-xl font-medium transition-all shadow-lg shadow-blue-900/20"
        >
          {status === 'loading' ? 'Analyzing...' : 'Analyze Logs'}
          {status === 'idle' && <ArrowRight className="h-5 w-5" />}
        </button>
      </div>
    </div>
  );
}
