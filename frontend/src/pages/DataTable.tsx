import { useState, useEffect } from 'react';
import { useMeasurementStore } from '../store/measurementStore';
import { useHistoricalData } from '../hooks/useHistoricalData';
import { exportCsv, exportXlsx } from '../api/endpoints';
import { subDays, format } from 'date-fns';
import { Download } from 'lucide-react';

export default function DataTable() {
  const { measurements, fetch: fetchMeasurements } = useMeasurementStore();
  const { data, loading, fetch: fetchData } = useHistoricalData();
  // Hasta que se elija una, se usa la primera medición de la lista.
  const [elegida, setMeasurementId] = useState('');
  const measurementId = elegida || measurements[0]?.id || '';
  const [start, setStart] = useState(format(subDays(new Date(), 1), "yyyy-MM-dd'T'HH:mm"));
  const [end, setEnd] = useState(format(new Date(), "yyyy-MM-dd'T'HH:mm"));

  useEffect(() => { fetchMeasurements(); }, []);

  const handleQuery = () => {
    if (!measurementId) return;
    fetchData({
      measurement_id: measurementId,
      start: new Date(start).toISOString(),
      end: new Date(end).toISOString(),
      max_points: 10000,
    });
  };

  const handleExport = async (type: 'csv' | 'xlsx') => {
    if (!measurementId) return;
    const params = {
      measurement_id: measurementId,
      start: new Date(start).toISOString(),
      end: new Date(end).toISOString(),
    };
    const res = type === 'csv' ? await exportCsv(params) : await exportXlsx(params);
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `medicion_${measurementId}.${type}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">Tabla de Datos</h1>

      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="block text-xs text-slate-500 mb-1">Medici&oacute;n</label>
          <select className="border rounded-lg px-3 py-1.5 text-sm" value={measurementId} onChange={(e) => setMeasurementId(e.target.value)}>
            <option value="">Seleccionar...</option>
            {measurements.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Inicio</label>
          <input type="datetime-local" className="border rounded-lg px-3 py-1.5 text-sm" value={start} onChange={(e) => setStart(e.target.value)} />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Fin</label>
          <input type="datetime-local" className="border rounded-lg px-3 py-1.5 text-sm" value={end} onChange={(e) => setEnd(e.target.value)} />
        </div>
        <button onClick={handleQuery} className="bg-slate-800 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-slate-700">
          Consultar
        </button>
        <button onClick={() => handleExport('csv')} className="flex items-center gap-1 bg-green-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-green-500">
          <Download className="w-3.5 h-3.5" /> CSV
        </button>
        <button onClick={() => handleExport('xlsx')} className="flex items-center gap-1 bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm hover:bg-blue-500">
          <Download className="w-3.5 h-3.5" /> Excel
        </button>
      </div>

      {loading && <div className="text-slate-400 text-sm">Cargando...</div>}

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-auto max-h-[600px]">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 sticky top-0">
            <tr>
              <th className="text-left px-4 py-2 font-medium text-slate-600">Timestamp</th>
              <th className="text-left px-4 py-2 font-medium text-slate-600">Variable</th>
              <th className="text-left px-4 py-2 font-medium text-slate-600">Fase</th>
              <th className="text-left px-4 py-2 font-medium text-slate-600">Categor&iacute;a</th>
              <th className="text-right px-4 py-2 font-medium text-slate-600">Valor</th>
            </tr>
          </thead>
          <tbody>
            {data.slice(0, 1000).map((r, i) => (
              <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-4 py-1.5 text-slate-500">{new Date(r.time).toLocaleString()}</td>
                <td className="px-4 py-1.5">{r.field}</td>
                <td className="px-4 py-1.5">{r.phase}</td>
                <td className="px-4 py-1.5">{r.category}</td>
                <td className="px-4 py-1.5 text-right font-mono">{r.value?.toFixed(2) ?? '---'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {data.length > 1000 && (
          <div className="p-3 text-center text-xs text-slate-400">
            Mostrando 1000 de {data.length} registros. Exporte para ver todos.
          </div>
        )}
        {data.length === 0 && !loading && (
          <div className="p-8 text-center text-slate-400">Sin datos. Seleccione una medici&oacute;n y rango de fechas.</div>
        )}
      </div>
    </div>
  );
}
