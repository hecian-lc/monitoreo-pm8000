import { useEffect, useState } from 'react';
import { useMeasurementStore } from '../store/measurementStore';
import { getReports, generateReport, downloadReport, getReportConfig, updateReportConfig } from '../api/endpoints';
import type { Report } from '../types/report';
import { FileText, Download, Loader2, Settings2, ChevronDown, ChevronUp, X } from 'lucide-react';
import { format } from 'date-fns';

export default function Reports() {
  const { measurements, fetch: fetchMeasurements } = useMeasurementStore();
  const [reports, setReports] = useState<Report[]>([]);
  const [config, setConfig] = useState<Record<string, string>>({});
  const [showConfig, setShowConfig] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [configSaved, setConfigSaved] = useState(false);

  // Generate form
  const [measurementId, setMeasurementId] = useState('');
  const [reportName, setReportName] = useState('Informe');
  const [reportFormat, setReportFormat] = useState('docx');
  const [obsMode, setObsMode] = useState('auto');
  const [generating, setGenerating] = useState(false);

  // Modal overrides
  const [modalCliente, setModalCliente] = useState('');
  const [modalNumInforme, setModalNumInforme] = useState('');
  const [modalAtencion, setModalAtencion] = useState('');

  useEffect(() => {
    fetchMeasurements();
    fetchReports();
    loadConfig();
  }, []);

  const loadConfig = async () => {
    const { data } = await getReportConfig();
    setConfig(data);
  };

  const fetchReports = async () => {
    const { data } = await getReports();
    setReports(data);
  };

  const saveConfig = async () => {
    await updateReportConfig(config);
    setConfigSaved(true);
    setTimeout(() => setConfigSaved(false), 2000);
  };

  const openGenerateModal = () => {
    if (!measurementId) return;
    setModalCliente(config.cliente || '');
    setModalNumInforme(config.num_informe || '');
    setModalAtencion(config.atencion || '');
    setShowModal(true);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setShowModal(false);
    try {
      await generateReport({
        measurement_id: measurementId,
        name: reportName,
        format: reportFormat,
        observaciones_mode: obsMode,
        cliente: modalCliente || undefined,
        num_informe: modalNumInforme || undefined,
        atencion: modalAtencion || undefined,
      });
      fetchReports();
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (report: Report) => {
    const res = await downloadReport(report.id);
    const url = URL.createObjectURL(res.data);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${report.name}.${report.format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const statusBadge = (status: string) => {
    const styles: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-700',
      generating: 'bg-blue-100 text-blue-700',
      completed: 'bg-green-100 text-green-700',
      error: 'bg-red-100 text-red-700',
    };
    return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] || ''}`}>{status}</span>;
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Informes</h1>

      {/* Generate Form */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="text-sm font-semibold text-slate-700">Generar Informe</div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Medicion</label>
            <select className="w-full border rounded-lg px-3 py-1.5 text-sm" value={measurementId} onChange={e => setMeasurementId(e.target.value)}>
              <option value="">Seleccionar...</option>
              {measurements.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Nombre</label>
            <input className="w-full border rounded-lg px-3 py-1.5 text-sm" value={reportName} onChange={e => setReportName(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Formato</label>
            <select className="w-full border rounded-lg px-3 py-1.5 text-sm" value={reportFormat} onChange={e => setReportFormat(e.target.value)}>
              <option value="docx">DOCX (Word)</option>
              <option value="pdf">PDF</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Observaciones</label>
            <select className="w-full border rounded-lg px-3 py-1.5 text-sm" value={obsMode} onChange={e => setObsMode(e.target.value)}>
              <option value="auto">Automatico (Reglas)</option>
              <option value="gemini">Gemini AI</option>
              <option value="manual">Manual</option>
            </select>
          </div>
        </div>
        <button onClick={openGenerateModal} disabled={!measurementId || generating} className="flex items-center gap-2 bg-slate-800 text-white px-5 py-2 rounded-lg text-sm hover:bg-slate-700 disabled:opacity-50">
          {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
          {generating ? 'Generando...' : 'Generar Informe'}
        </button>
      </div>

      {/* Report Config (collapsible) */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <button onClick={() => setShowConfig(!showConfig)} className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors">
          <div className="flex items-center gap-2">
            <Settings2 className="w-4 h-4 text-slate-500" />
            <span className="text-sm font-semibold text-slate-700">Configuracion del Informe</span>
            <span className="text-xs text-slate-400">(cliente, firma, colores)</span>
          </div>
          {showConfig ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </button>

        {showConfig && (
          <div className="p-5 pt-0 space-y-4 border-t border-slate-100">
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mt-4">
              {[
                ['cliente', 'Cliente'],
                ['num_informe', 'N\u00b0 Informe'],
                ['atencion', 'Atencion'],
                ['objetivo', 'Objetivo'],
                ['equipo', 'Equipo'],
                ['periodicidad', 'Periodicidad'],
                ['firma_nombre', 'Nombre Firma'],
                ['firma_cargo', 'Cargo'],
              ].map(([key, label]) => (
                <div key={key}>
                  <label className="block text-xs text-slate-500 mb-1">{label}</label>
                  <input className="w-full border rounded-lg px-3 py-1.5 text-sm" value={config[key] || ''} onChange={e => setConfig({ ...config, [key]: e.target.value })} />
                </div>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-4">
              <span className="text-xs font-medium text-slate-500">Colores:</span>
              {[
                ['color_principal', 'Principal'],
                ['color_fase_r', 'Fase R'],
                ['color_fase_s', 'Fase S'],
                ['color_fase_t', 'Fase T'],
                ['color_trif', 'Trifasico'],
              ].map(([key, label]) => (
                <div key={key} className="flex items-center gap-1.5">
                  <label className="text-xs text-slate-500">{label}</label>
                  <input type="color" className="w-7 h-5 border rounded cursor-pointer" value={config[key] || '#202E6B'} onChange={e => setConfig({ ...config, [key]: e.target.value })} />
                </div>
              ))}
            </div>

            <button onClick={saveConfig} className="flex items-center gap-1.5 bg-slate-700 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-slate-600">
              Guardar Configuracion
              {configSaved && <span className="text-green-300 ml-1">Guardado</span>}
            </button>
          </div>
        )}
      </div>

      {/* Generated Reports List */}
      <div className="space-y-3">
        <div className="text-sm font-semibold text-slate-700">Informes Generados</div>
        {reports.map(r => (
          <div key={r.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium text-slate-800">{r.name}</span>
                {statusBadge(r.status)}
                <span className="text-xs text-slate-400 uppercase">{r.format}</span>
              </div>
              <div className="text-xs text-slate-400 mt-1">
                {format(new Date(r.created_at), 'dd/MM/yyyy HH:mm')}
                {r.error_message && <span className="text-red-500 ml-2">{r.error_message}</span>}
              </div>
            </div>
            {r.status === 'completed' && (
              <button onClick={() => handleDownload(r)} className="p-2 rounded-lg bg-green-50 text-green-600 hover:bg-green-100">
                <Download className="w-4 h-4" />
              </button>
            )}
          </div>
        ))}
        {reports.length === 0 && <div className="text-center text-slate-400 py-8">No hay informes generados.</div>}
      </div>

      {/* Generate Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowModal(false)}>
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg mx-4 overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-5 border-b border-slate-100">
              <div className="text-lg font-bold text-slate-800">Confirmar Informe</div>
              <button onClick={() => setShowModal(false)} className="p-1 rounded-lg hover:bg-slate-100">
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <div className="bg-slate-50 rounded-lg p-3 text-sm space-y-1">
                <div><span className="text-slate-500">Medicion:</span> <span className="font-medium">{measurements.find(m => m.id === measurementId)?.name}</span></div>
                <div><span className="text-slate-500">Formato:</span> <span className="font-medium uppercase">{reportFormat}</span></div>
                <div><span className="text-slate-500">Observaciones:</span> <span className="font-medium">{obsMode === 'auto' ? 'Automatico (Reglas)' : obsMode === 'gemini' ? 'Gemini AI' : 'Manual'}</span></div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="block text-xs text-slate-500 mb-1">Cliente</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={modalCliente} onChange={e => setModalCliente(e.target.value)} placeholder="Nombre del cliente" />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">N&deg; Informe</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={modalNumInforme} onChange={e => setModalNumInforme(e.target.value)} placeholder="001-2026" />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 mb-1">Atencion</label>
                  <input className="w-full border rounded-lg px-3 py-2 text-sm" value={modalAtencion} onChange={e => setModalAtencion(e.target.value)} placeholder="Persona de contacto" />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 p-5 border-t border-slate-100 bg-slate-50">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-200 rounded-lg">Cancelar</button>
              <button onClick={handleGenerate} className="flex items-center gap-2 bg-slate-800 text-white px-5 py-2 rounded-lg text-sm hover:bg-slate-700">
                <FileText className="w-4 h-4" /> Generar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
