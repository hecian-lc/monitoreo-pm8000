import { useEffect, useState } from 'react';
import { getDevices, createDevice, updateDevice, deleteDevice, testDeviceConnection } from '../api/endpoints';
import type { Device, MeterModel } from '../types/meter';
import { Plus, Pencil, Trash2, Wifi, WifiOff, Loader2, Check, X } from 'lucide-react';
import { format } from 'date-fns';

const METER_MODELS: { value: MeterModel; label: string }[] = [
  { value: 'PM8000', label: 'PowerLogic PM8000' },
  { value: 'PM5340', label: 'PowerLogic PM5340' },
  { value: 'PM2220', label: 'EasyLogic PM2220' },
];

export default function Devices() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Record<string, boolean>>({});

  const [name, setName] = useState('');
  const [meterModel, setMeterModel] = useState<MeterModel>('PM8000');
  const [host, setHost] = useState('192.168.1.100');
  const [port, setPort] = useState(502);
  const [unitId, setUnitId] = useState(1);
  const [pollInterval, setPollInterval] = useState(1.0);

  useEffect(() => { fetchDevices(); }, []);

  const fetchDevices = async () => {
    setLoading(true);
    const { data } = await getDevices();
    setDevices(data);
    setLoading(false);
  };

  const resetForm = () => {
    setName(''); setMeterModel('PM8000'); setHost('192.168.1.100');
    setPort(502); setUnitId(1); setPollInterval(1.0);
    setEditId(null); setShowForm(false);
  };

  const handleSubmit = async () => {
    if (!name.trim() || !host.trim()) return;
    if (editId) {
      await updateDevice(editId, { name, meter_model: meterModel, host, port, unit_id: unitId, poll_interval: pollInterval });
    } else {
      await createDevice({ name, meter_model: meterModel, host, port, unit_id: unitId, poll_interval: pollInterval });
    }
    resetForm();
    fetchDevices();
  };

  const handleEdit = (d: Device) => {
    setEditId(d.id); setName(d.name); setMeterModel(d.meter_model);
    setHost(d.host); setPort(d.port); setUnitId(d.unit_id);
    setPollInterval(d.poll_interval); setShowForm(true);
  };

  const handleDelete = async (d: Device) => {
    if (!confirm(`Eliminar dispositivo "${d.name}" y todas sus mediciones?`)) return;
    await deleteDevice(d.id);
    fetchDevices();
  };

  const handleTest = async (id: string) => {
    setTesting(id);
    try {
      const { data } = await testDeviceConnection(id);
      setTestResult(prev => ({ ...prev, [id]: data.connected }));
    } catch {
      setTestResult(prev => ({ ...prev, [id]: false }));
    }
    setTesting(null);
    setTimeout(() => setTestResult(prev => { const n = { ...prev }; delete n[id]; return n; }), 3000);
  };

  const modelBadge = (model: string) => {
    const colors: Record<string, string> = {
      PM8000: 'bg-indigo-100 text-indigo-700',
      PM5340: 'bg-teal-100 text-teal-700',
      PM2220: 'bg-orange-100 text-orange-700',
    };
    return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[model] || 'bg-slate-100'}`}>{model}</span>;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Dispositivos</h1>
        <button onClick={() => { resetForm(); setShowForm(true); }} className="flex items-center gap-1.5 bg-slate-800 text-white px-4 py-2 rounded-lg text-sm hover:bg-slate-700">
          <Plus className="w-4 h-4" /> Agregar Dispositivo
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
          <div className="text-sm font-semibold text-slate-700">{editId ? 'Editar' : 'Nuevo'} Dispositivo</div>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Nombre</label>
              <input placeholder="Ej: PM8000 Tablero General" className="w-full border rounded-lg px-3 py-2 text-sm" value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Modelo</label>
              <select className="w-full border rounded-lg px-3 py-2 text-sm" value={meterModel} onChange={e => setMeterModel(e.target.value as MeterModel)}>
                {METER_MODELS.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">IP / Host</label>
              <input placeholder="192.168.1.100" className="w-full border rounded-lg px-3 py-2 text-sm" value={host} onChange={e => setHost(e.target.value)} />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Puerto</label>
              <input type="number" className="w-full border rounded-lg px-3 py-2 text-sm" value={port} onChange={e => setPort(+e.target.value)} />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Unit ID</label>
              <input type="number" className="w-full border rounded-lg px-3 py-2 text-sm" value={unitId} onChange={e => setUnitId(+e.target.value)} />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Intervalo (s)</label>
              <input type="number" step="0.1" className="w-full border rounded-lg px-3 py-2 text-sm" value={pollInterval} onChange={e => setPollInterval(+e.target.value)} />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleSubmit} className="bg-slate-800 text-white px-4 py-1.5 rounded-lg text-sm">{editId ? 'Guardar' : 'Crear'}</button>
            <button onClick={resetForm} className="text-slate-500 px-4 py-1.5 text-sm">Cancelar</button>
          </div>
        </div>
      )}

      {loading && <div className="text-slate-400 text-sm">Cargando...</div>}

      <div className="space-y-3">
        {devices.map(d => (
          <div key={d.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  {d.connected
                    ? <Wifi className="w-4 h-4 text-green-500" />
                    : <WifiOff className="w-4 h-4 text-slate-300" />
                  }
                  <span className="font-semibold text-slate-800">{d.name}</span>
                  {modelBadge(d.meter_model)}
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${d.connected ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                    {d.connected ? 'Conectado' : 'Desconectado'}
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {d.host}:{d.port} &middot; Unit ID: {d.unit_id} &middot; Intervalo: {d.poll_interval}s
                  &middot; Creado: {format(new Date(d.created_at), 'dd/MM/yyyy')}
                </div>
              </div>
              <div className="flex gap-1.5">
                <button onClick={() => handleTest(d.id)} disabled={testing === d.id}
                  className="px-3 py-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 text-xs font-medium flex items-center gap-1">
                  {testing === d.id ? <Loader2 className="w-3 h-3 animate-spin" /> :
                   testResult[d.id] === true ? <Check className="w-3 h-3 text-green-500" /> :
                   testResult[d.id] === false ? <X className="w-3 h-3 text-red-500" /> :
                   <Wifi className="w-3 h-3" />}
                  Test
                </button>
                <button onClick={() => handleEdit(d)} className="p-2 rounded-lg bg-slate-50 text-slate-500 hover:bg-slate-100" title="Editar">
                  <Pencil className="w-4 h-4" />
                </button>
                <button onClick={() => handleDelete(d)} className="p-2 rounded-lg bg-slate-50 text-slate-400 hover:bg-red-50 hover:text-red-500" title="Eliminar">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
        {devices.length === 0 && !loading && (
          <div className="text-center text-slate-400 py-12">
            No hay dispositivos. Agregue un medidor PM8000, PM5340 o PM2220 para comenzar.
          </div>
        )}
      </div>
    </div>
  );
}
