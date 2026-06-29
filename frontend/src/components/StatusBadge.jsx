import { ShieldAlert, ShieldCheck } from 'lucide-react';

export default function StatusBadge({ blocked }) {
  if (blocked) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/10 px-3 py-1 text-sm font-medium text-red-500 ring-1 ring-inset ring-red-500/20">
        <ShieldAlert className="h-4 w-4" />
        Blocked: Injection
      </span>
    );
  }
  
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-sm font-medium text-emerald-500 ring-1 ring-inset ring-emerald-500/20">
      <ShieldCheck className="h-4 w-4" />
      Clean
    </span>
  );
}
