import { useEffect, useState } from 'react';
import { useMeasurementStore } from '../store/measurementStore';
import { createMeasurement, measurementAction, deleteMeasurement } from '../api/endpoints';
import { Play, Square, Archive, Trash2, Plus } from 'lucide-react';
import { format } from 'date-fns';

export default function Measurements() {
  const { measurements, loading, fetch } = useMeasurementStore();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [pointName, setPointName] = useState('T.G.');

  useEffect(() => { fetch(); }, []);

  const handleCreate = async () => {
    if (!name.trim()) return;
    await createMeasurement({ name, description, point_name: pointName });
    setName('');
    setDescription('');
    setShowCreate(false);
    fetch();
  };

  const handleAction = async (id: string, action: 'start' | 'stop' | 'compress') => {
    await measurementAction(id, action);
    fetch();
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Eliminar medici\u00f3n "${name}" y todos sus datos?`)) return;
    await deleteMeasurement(id);
    fetch();
  };

  const statusBadge = (status: string) => {
    const styles: Record<string, string> = {
      idle: 'bg-slate-100 text-slate-600',
      recording: 'bg-red-100 text-red-700',
      stopped: 'bg-amber-100 text-amber-700',
      compressed: 'bg-blue-100 text-blue-700',
    };
    const labels: Record<string, string> = {
      idle: 'Inactiva',
      recording: 'Grabando',
      stopped: 'Detenida',
      compressed: 'Comprimida',
    };
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || ''}`}>
        {labels[status] || status}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Mediciones</h1>
        <button onClick={() => setShowCreate(true)} className="flex items-center gap-1.5 bg-slate-800 text-white px-4 py-2 rounded-lg text-sm hover:bg-slate-700">
          <Plus className="w-4 h-4" /> Nueva Medici&oacute;n
        </button>
      </div>

      {showCreate && (
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
          <div className="text-sm font-semibold text-slate-700">Nueva Medici&oacute;n</div>
          <input placeholder="Nombre (ej: TG Principal - Marzo 2026)" className="w-full border rounded-lg px-3 py-2 text-sm" value={name} onChange={(e) => setName(e.target.value)} />
          <input placeholder="Descripci&oacute;n (opcional)" className="w-full border rounded-lg px-3 py-2 text-sm" value={description} onChange={(e) => setDescription(e.target.value)} />
          <input placeholder="Punto de medici&oacute;n" className="w-full border rounded-lg px-3 py-2 text-sm" value={pointName} onChange={(e) => setPointName(e.target.value)} />
          <div className="flex gap-2">
            <button onClick={handleCreate} className="bg-slate-800 text-white px-4 py-1.5 rounded-lg text-sm">Crear</button>
            <button onClick={() => setShowCreate(false)} className="text-slate-500 px-4 py-1.5 text-sm">Cancelar</button>
          </div>
        </div>
      )}

      {loading && <div className="text-slate-400 text-sm">Cargando...</div>}

      <div className="space-y-3">
        {measurements.map((m) => (
          <div key={m.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-800">{m.name}</span>
                  {statusBadge(m.status)}
                  <span className="text-xs text-slate-400">({m.resolution})</span>
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {m.point_name} &middot; Creada: {format(new Date(m.created_at), 'dd/MM/yyyy HH:mm')}
                  {m.started_at && ` \u00b7 Inicio: ${format(new Date(m.started_at), 'dd/MM HH:mm')}`}
                  {m.stopped_at && ` \u00b7 Fin: ${format(new Date(m.stopped_at), 'dd/MM HH:mm')}`}
                </div>
                {m.description && <div className="text-xs text-slate-500 mt-1">{m.description}</div>}
              </div>
              <div className="flex gap-1.5">
                {(m.status === 'idle' || m.status === 'stopped') && (
                  <button onClick={() => handleAction(m.id, 'start')} className="p-2 rounded-lg bg-green-50 text-green-600 hover:bg-green-100" title="Iniciar">
                    <Play className="w-4 h-4" />
                  </button>
                )}
                {m.status === 'recording' && (
                  <button onClick={() => handleAction(m.id, 'stop')} className="p-2 rounded-lg bg-red-50 text-red-600 hover:bg-red-100" title="Detener">
                    <Square className="w-4 h-4" />
                  </button>
                )}
                {m.status === 'stopped' && (
                  <button onClick={() => handleAction(m.id, 'compress')} className="p-2 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100" title="Comprimir">
                    <Archive className="w-4 h-4" />
                  </button>
                )}
                <button onClick={() => handleDelete(m.id, m.name)} className="p-2 rounded-lg bg-slate-50 text-slate-400 hover:bg-red-50 hover:text-red-500" title="Eliminar">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
        {measurements.length === 0 && !loading && (
          <div className="text-center text-slate-400 py-12">
            No hay mediciones. Cree una nueva para comenzar a grabar datos.
          </div>
        )}
      </div>
    </div>
  );
}
