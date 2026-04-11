interface PhaseGridProps {
  title: string;
  unit: string;
  phaseA?: number;
  phaseB?: number;
  phaseC?: number;
  total?: number;
  decimals?: number;
}

const fmt = (v: number | undefined, d: number) =>
  v !== undefined && !isNaN(v)
    ? v.toLocaleString('es-PY', { minimumFractionDigits: d, maximumFractionDigits: d })
    : '---';

export default function PhaseGrid({ title, unit, phaseA, phaseB, phaseC, total, decimals = 2 }: PhaseGridProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <div className="text-sm font-semibold text-slate-700 mb-3">{title}</div>
      <div className="grid grid-cols-4 gap-2 text-center">
        <div>
          <div className="text-xs text-slate-400">Fase R</div>
          <div className="text-lg font-bold text-red-500">{fmt(phaseA, decimals)}</div>
          <div className="text-xs text-slate-400">{unit}</div>
        </div>
        <div>
          <div className="text-xs text-slate-400">Fase S</div>
          <div className="text-lg font-bold text-blue-500">{fmt(phaseB, decimals)}</div>
          <div className="text-xs text-slate-400">{unit}</div>
        </div>
        <div>
          <div className="text-xs text-slate-400">Fase T</div>
          <div className="text-lg font-bold text-green-500">{fmt(phaseC, decimals)}</div>
          <div className="text-xs text-slate-400">{unit}</div>
        </div>
        {total !== undefined && (
          <div>
            <div className="text-xs text-slate-400">Total</div>
            <div className="text-lg font-bold text-purple-600">{fmt(total, decimals)}</div>
            <div className="text-xs text-slate-400">{unit}</div>
          </div>
        )}
      </div>
    </div>
  );
}
