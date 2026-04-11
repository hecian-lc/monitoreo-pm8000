import api from './client';
import type { Measurement, HealthStatus, DeviceConfig, DataRecord } from '../types/meter';
import type { Report } from '../types/report';

// Health
export const getHealth = () => api.get<HealthStatus>('/health');

// Measurements
export const getMeasurements = () => api.get<Measurement[]>('/measurements');
export const createMeasurement = (data: { name: string; description?: string; point_name?: string }) =>
  api.post<Measurement>('/measurements', data);
export const getMeasurement = (id: string) => api.get<Measurement>(`/measurements/${id}`);
export const measurementAction = (id: string, action: 'start' | 'stop' | 'compress') =>
  api.post(`/measurements/${id}/action`, { action });
export const deleteMeasurement = (id: string) => api.delete(`/measurements/${id}`);

// Historical Data
export const queryData = (params: {
  measurement_id: string;
  start: string;
  end: string;
  variables?: string[];
  categories?: string[];
  max_points?: number;
}) => api.get<{ count: number; data: DataRecord[] }>('/data/query', { params });

export const queryStats = (params: {
  measurement_id: string;
  start: string;
  end: string;
}) => api.get('/data/stats', { params });

// Export
export const exportCsv = (params: {
  measurement_id: string;
  start: string;
  end: string;
}) => api.get('/export/csv', { params, responseType: 'blob' });

export const exportXlsx = (params: {
  measurement_id: string;
  start: string;
  end: string;
}) => api.get('/export/xlsx', { params, responseType: 'blob' });

// Reports
export const getReports = (measurement_id?: string) =>
  api.get<Report[]>('/reports', { params: measurement_id ? { measurement_id } : {} });
export const generateReport = (data: {
  measurement_id: string;
  name?: string;
  format?: string;
  observaciones_mode?: string;
}) => api.post('/reports/generate', data);
export const downloadReport = (id: string) =>
  api.get(`/reports/${id}/download`, { responseType: 'blob' });

// Device Config
export const getDeviceConfig = () => api.get<DeviceConfig>('/device/config');
export const updateDeviceConfig = (data: Partial<DeviceConfig>) =>
  api.put('/device/config', data);
export const getReportConfig = () => api.get('/device/report-config');
export const updateReportConfig = (data: Record<string, string>) =>
  api.put('/device/report-config', data);
