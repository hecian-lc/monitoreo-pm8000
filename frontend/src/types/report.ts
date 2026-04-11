export interface Report {
  id: string;
  measurement_id: string;
  name: string;
  status: 'pending' | 'generating' | 'completed' | 'error';
  format: 'docx' | 'pdf';
  file_path: string | null;
  created_at: string;
  completed_at: string | null;
  error_message: string | null;
}

export interface ReportSchedule {
  id: string;
  name: string;
  measurement_id: string | null;
  cron_expression: string;
  config_json: string;
  enabled: number;
  last_run_at: string | null;
  created_at: string;
}

export interface ReportConfig {
  cliente: string;
  num_informe: string;
  atencion: string;
  objetivo: string;
  equipo: string;
  periodicidad: string;
  firma_nombre: string;
  firma_cargo: string;
  fuente: string;
  color_principal: string;
  color_encabezado_tabla: string;
  color_fase_r: string;
  color_fase_s: string;
  color_fase_t: string;
  color_trif: string;
  img_portada: string;
  img_encabezado: string;
  img_pie: string;
}
