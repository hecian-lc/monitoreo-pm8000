import { useEffect, useState } from 'react';
import { getReportConfig, updateReportConfig } from '../api/endpoints';
import { Save, ExternalLink } from 'lucide-react';

export default function Settings() {
  const [report, setReport] = useState<Record<string, string>>({});
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getReportConfig().then(r => setReport(r.data));
  }, []);

  const saveReport = async () => {
    await updateReportConfig(report);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-800">Configuracion</h1>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
        <div className="text-sm font-semibold text-slate-700">Accesos Rapidos</div>
        <div className="grid grid-cols-2 gap-3">
          <a href="/devices" className="flex items-center gap-2 p-3 rounded-lg border border-slate-200 hover:bg-slate-50 text-sm text-slate-700">
            <ExternalLink className="w-4 h-4 text-slate-400" />
            Gestionar Dispositivos
          </a>
          <a href="/reports" className="flex items-center gap-2 p-3 rounded-lg border border-slate-200 hover:bg-slate-50 text-sm text-slate-700">
            <ExternalLink className="w-4 h-4 text-slate-400" />
            Configuracion de Informes
          </a>
          <a href="http://localhost:8086" target="_blank" className="flex items-center gap-2 p-3 rounded-lg border border-slate-200 hover:bg-slate-50 text-sm text-slate-700">
            <ExternalLink className="w-4 h-4 text-slate-400" />
            InfluxDB UI
          </a>
          <a href="http://localhost:8000/docs" target="_blank" className="flex items-center gap-2 p-3 rounded-lg border border-slate-200 hover:bg-slate-50 text-sm text-slate-700">
            <ExternalLink className="w-4 h-4 text-slate-400" />
            API Docs (Swagger)
          </a>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="text-sm font-semibold text-slate-700">Imagenes del Informe</div>
        <p className="text-xs text-slate-500">
          Para personalizar portada, encabezado y pie de pagina, copie las imagenes a
          <code className="bg-slate-100 px-1.5 py-0.5 rounded text-xs ml-1">backend/app/reports/assets/</code>
        </p>
        <div className="grid grid-cols-3 gap-3 text-xs text-slate-500">
          <div className="p-3 bg-slate-50 rounded-lg">
            <div className="font-medium text-slate-700">portada.png</div>
            <div>A4 (21 x 29.7 cm)</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg">
            <div className="font-medium text-slate-700">encabezado.png</div>
            <div>21 x 5.28 cm</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg">
            <div className="font-medium text-slate-700">pie.png</div>
            <div>21 x 2.18 cm</div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
        <div className="text-sm font-semibold text-slate-700">Gemini AI</div>
        <p className="text-xs text-slate-500">API Key para generar observaciones con inteligencia artificial en los informes.</p>
        <input
          type="password"
          className="w-full border rounded-lg px-3 py-1.5 text-sm"
          placeholder="Ingrese su API Key de Google AI Studio"
          value={report.gemini_api_key || ''}
          onChange={e => setReport({ ...report, gemini_api_key: e.target.value })}
        />
        <button onClick={saveReport} className="flex items-center gap-1.5 bg-slate-800 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-slate-700">
          <Save className="w-3.5 h-3.5" /> Guardar
          {saved && <span className="text-green-300 ml-2">Guardado</span>}
        </button>
      </div>
    </div>
  );
}
