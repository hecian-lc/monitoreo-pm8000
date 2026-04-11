interface GaugeCardProps {
  label: string;
  value: number | undefined;
  unit: string;
  color?: string;
  decimals?: number;
}

export default function GaugeCard({ label, value, unit, color = '#202E6B', decimals = 2 }: GaugeCardProps) {
  const formatted = value !== undefined && !isNaN(value)
    ? value.toLocaleString('es-PY', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
    : '---';

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
      <div className="text-xs text-slate-500 mb-1">{label}</div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold" style={{ color }}>{formatted}</span>
        <span className="text-sm text-slate-400">{unit}</span>
      </div>
    </div>
  );
}
