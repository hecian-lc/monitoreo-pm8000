import { useEffect, useState } from 'react';
import { useMeasurementStore } from '../store/measurementStore';
import { getReports, generateReport, downloadReport } from '../api/endpoints';
import type { Report } from '../types/report';
import { FileText, Download, Loader2 } from 'lucide-react';
import { format } from 'date-fns';

export default function Reports() {
  const { measurements, fetch: fetchMeasurements } = useMeasurementStore();
  const [reports, setReports] = useState<Report[]>([]);
  const [measurementId, setMeasurementId] = useState('');
  const [reportName, setReportName] = useState('Informe');
  const [reportFormat, setReportFormat] = useState('docx');
  const [obsMode, setObsMode] = useState('auto');
  const [generating, setGenerating] = useState(false);

  useEffect(() => { fetchMeasurements(); fetchReports(); }, []);

  const fetchReports = async () => {
    const { data } = await getReports();
    setReports(data);
  };

  const handleGenerate = async () => {
    if (!measurementId) return;
    setGenerating(true);
    try {
      await generateReport({
        measurement_id: measurementId,
        name: reportName,
        format: reportFormat,
        observaciones_mode: obsMode,
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

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="text-sm font-semibold text-slate-700">Generar Informe</div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Medici&oacute;n</label>
            <select className="w-full border rounded-lg px-3 py-1.5 text-sm" value={measurementId} onChange={(e) => setMeasurementId(e.target.value)}>
              <option value="">Seleccionar...</option>
              {measurements.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Nombre</label>
            <input className="w-full border rounded-lg px-3 py-1.5 text-sm" value={reportName} onChange={(e) => setReportName(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Formato</label>
            <select className="w-full border rounded-lg px-3 py-1.5 text-sm" value={reportFormat} onChange={(e) => setReportFormat(e.target.value)}>
              <option value="docx">DOCX (Word)</option>
              <option value="pdf">PDF</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Observaciones</label>
            <select className="w-full border rounded-lg px-3 py-1.5 text-sm" value={obsMode} onChange={(e) => setObsMode(e.target.value)}>
              <option value="auto">Autom&aacute;tico (Reglas)</option>
              <option value="gemini">Gemini AI</option>
              <option value="manual">Manual</option>
            </select>
          </div>
        </div>
        <button onClick={handleGenerate} disabled={!measurementId || generating} className="flex items-center gap-2 bg-slate-800 text-white px-5 py-2 rounded-lg text-sm hover:bg-slate-700 disabled:opacity-50">
          {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
          {generating ? 'Generando...' : 'Generar Informe'}
        </button>
      </div>

      <div className="space-y-3">
        <div className="text-sm font-semibold text-slate-700">Informes Generados</div>
        {reports.map((r) => (
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
    </div>
  );
}
