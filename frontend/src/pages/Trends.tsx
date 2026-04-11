import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Brush } from 'recharts';
import { useMeasurementStore } from '../store/measurementStore';
import { useHistoricalData } from '../hooks/useHistoricalData';
import { format, subHours, subDays } from 'date-fns';

const CATEGORIES = [
  { value: 'voltage', label: 'Tensi\u00f3n' },
  { value: 'current', label: 'Corriente' },
  { value: 'active_power', label: 'Potencia Activa' },
  { value: 'reactive_power', label: 'Potencia Reactiva' },
  { value: 'apparent_power', label: 'Potencia Aparente' },
  { value: 'power_factor', label: 'Factor de Potencia' },
  { value: 'thd', label: 'THD' },
  { value: 'frequency', label: 'Frecuencia' },
];

const RANGES = [
  { label: '1h', fn: () => subHours(new Date(), 1) },
  { label: '6h', fn: () => subHours(new Date(), 6) },
  { label: '24h', fn: () => subDays(new Date(), 1) },
  { label: '7d', fn: () => subDays(new Date(), 7) },
  { label: '30d', fn: () => subDays(new Date(), 30) },
];

const COLORS = ['#E74C3C', '#3498DB', '#2ECC71', '#8E44AD', '#E67E22', '#1ABC9C'];

export default function Trends() {
  const { measurements, fetch: fetchMeasurements } = useMeasurementStore();
  const { data, loading, fetch: fetchData } = useHistoricalData();
  const [measurementId, setMeasurementId] = useState('');
  const [category, setCategory] = useState('voltage');
  const [rangeIdx, setRangeIdx] = useState(2); // 24h default

  useEffect(() => { fetchMeasurements(); }, []);
  useEffect(() => {
    if (measurements.length > 0 && !measurementId) {
      setMeasurementId(measurements[0].id);
    }
  }, [measurements]);

  useEffect(() => {
    if (!measurementId) return;
    const start = RANGES[rangeIdx].fn();
    fetchData({
      measurement_id: measurementId,
      start: start.toISOString(),
      end: new Date().toISOString(),
      categories: [category],
    });
  }, [measurementId, category, rangeIdx]);

  // Transform data for Recharts: group by timestamp, each field becomes a series
  const fieldsSet = new Set<string>();
  const byTime: Record<string, Record<string, number>> = {};

  for (const record of data) {
    const key = record.time;
    if (!byTime[key]) byTime[key] = { time: new Date(record.time).getTime() } as any;
    const label = `${record.field} (${record.phase})`;
    byTime[key][label] = record.value ?? 0;
    fieldsSet.add(label);
  }
  const fields = Array.from(fieldsSet);
  const sortedData = Object.values(byTime).sort((a: any, b: any) => a.time - b.time);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Tendencias</h1>

      <div className="flex flex-wrap items-center gap-3">
        <select
          className="border rounded-lg px-3 py-1.5 text-sm"
          value={measurementId}
          onChange={(e) => setMeasurementId(e.target.value)}
        >
          <option value="">Seleccionar medici&oacute;n...</option>
          {measurements.map((m) => (
            <option key={m.id} value={m.id}>{m.name}</option>
          ))}
        </select>

        <select
          className="border rounded-lg px-3 py-1.5 text-sm"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          {CATEGORIES.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>

        <div className="flex gap-1">
          {RANGES.map((r, i) => (
            <button
              key={r.label}
              onClick={() => setRangeIdx(i)}
              className={`px-3 py-1 rounded text-sm ${
                i === rangeIdx ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="text-slate-400 text-sm">Cargando datos...</div>}

      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <ResponsiveContainer width="100%" height={450}>
          <LineChart data={sortedData}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis
              dataKey="time"
              type="number"
              domain={['auto', 'auto']}
              tickFormatter={(v) => format(new Date(v), 'dd/MM HH:mm')}
              fontSize={11}
            />
            <YAxis fontSize={11} />
            <Tooltip
              labelFormatter={(v) => format(new Date(v as number), 'dd/MM/yyyy HH:mm:ss')}
              formatter={(v) => typeof v === 'number' ? v.toFixed(2) : String(v)}
            />
            <Legend />
            {fields.map((field, i) => (
              <Line
                key={field}
                type="monotone"
                dataKey={field}
                stroke={COLORS[i % COLORS.length]}
                dot={false}
                strokeWidth={1.5}
              />
            ))}
            <Brush dataKey="time" height={30} stroke="#94a3b8" tickFormatter={(v) => format(new Date(v), 'HH:mm')} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
