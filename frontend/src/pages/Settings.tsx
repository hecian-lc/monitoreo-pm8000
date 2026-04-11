import { useEffect, useState } from 'react';
import { getDeviceConfig, updateDeviceConfig, getReportConfig, updateReportConfig } from '../api/endpoints';
import type { DeviceConfig } from '../types/meter';
import { Save } from 'lucide-react';

export default function Settings() {
  const [device, setDevice] = useState<DeviceConfig | null>(null);
  const [report, setReport] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState('');

  useEffect(() => {
    getDeviceConfig().then((r) => setDevice(r.data));
    getReportConfig().then((r) => setReport(r.data));
  }, []);

  const saveDevice = async () => {
    if (!device) return;
    await updateDeviceConfig(device);
    setSaved('device');
    setTimeout(() => setSaved(''), 2000);
  };

  const saveReport = async () => {
    await updateReportConfig(report);
    setSaved('report');
    setTimeout(() => setSaved(''), 2000);
  };

  if (!device) return <div className="text-slate-400">Cargando...</div>;

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-800">Configuraci&oacute;n</h1>

      {/* Device Config */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="text-sm font-semibold text-slate-700">Conexi&oacute;n Modbus</div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">IP del Gateway</label>
            <input className="w-full border rounded-lg px-3 py-1.5 text-sm" value={device.host} onChange={(e) => setDevice({ ...device, host: e.target.value })} />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Puerto</label>
            <input type="number" className="w-full border rounded-lg px-3 py-1.5 text-sm" value={device.port} onChange={(e) => setDevice({ ...device, port: +e.target.value })} />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Unit ID</label>
            <input type="number" className="w-full border rounded-lg px-3 py-1.5 text-sm" value={device.unit_id} onChange={(e) => setDevice({ ...device, unit_id: +e.target.value })} />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Intervalo (s)</label>
            <input type="number" step="0.1" className="w-full border rounded-lg px-3 py-1.5 text-sm" value={device.poll_interval} onChange={(e) => setDevice({ ...device, poll_interval: +e.target.value })} />
          </div>
        </div>
        <button onClick={saveDevice} className="flex items-center gap-1.5 bg-slate-800 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-slate-700">
          <Save className="w-3.5 h-3.5" /> Guardar
          {saved === 'device' && <span className="text-green-300 ml-2">Guardado</span>}
        </button>
      </div>

      {/* Report Config */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="text-sm font-semibold text-slate-700">Configuraci&oacute;n de Informes</div>
        <div className="grid grid-cols-2 gap-3">
          {[
            ['cliente', 'Cliente'],
            ['num_informe', 'N\u00b0 Informe'],
            ['atencion', 'Atenci\u00f3n'],
            ['objetivo', 'Objetivo'],
            ['equipo', 'Equipo'],
            ['periodicidad', 'Periodicidad'],
            ['firma_nombre', 'Nombre Firma'],
            ['firma_cargo', 'Cargo'],
          ].map(([key, label]) => (
            <div key={key}>
              <label className="block text-xs text-slate-500 mb-1">{label}</label>
              <input className="w-full border rounded-lg px-3 py-1.5 text-sm" value={report[key] || ''} onChange={(e) => setReport({ ...report, [key]: e.target.value })} />
            </div>
          ))}
        </div>

        <div className="text-xs font-medium text-slate-500 mt-2">Colores</div>
        <div className="flex flex-wrap gap-3">
          {[
            ['color_principal', 'Principal'],
            ['color_fase_r', 'Fase R'],
            ['color_fase_s', 'Fase S'],
            ['color_fase_t', 'Fase T'],
            ['color_trif', 'Trif\u00e1sico'],
          ].map(([key, label]) => (
            <div key={key} className="flex items-center gap-1.5">
              <label className="text-xs text-slate-500">{label}</label>
              <input type="color" className="w-8 h-6 border rounded cursor-pointer" value={report[key] || '#202E6B'} onChange={(e) => setReport({ ...report, [key]: e.target.value })} />
            </div>
          ))}
        </div>

        <button onClick={saveReport} className="flex items-center gap-1.5 bg-slate-800 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-slate-700">
          <Save className="w-3.5 h-3.5" /> Guardar
          {saved === 'report' && <span className="text-green-300 ml-2">Guardado</span>}
        </button>
      </div>
    </div>
  );
}
