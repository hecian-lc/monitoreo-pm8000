import api from './client';
import type { Device, Measurement, HealthStatus, DataRecord } from '../types/meter';
import type { Report } from '../types/report';

// Health
export const getHealth = () => api.get<HealthStatus>('/health');

// Devices
export const getDevices = () => api.get<Device[]>('/devices');
export const createDevice = (data: { name: string; host: string; port: number; unit_id?: number; poll_interval?: number }) =>
  api.post<Device>('/devices', data);
export const getDevice = (id: string) => api.get<Device>(`/devices/${id}`);
export const updateDevice = (id: string, data: Partial<Device>) =>
  api.put<Device>(`/devices/${id}`, data);
export const deleteDevice = (id: string) => api.delete(`/devices/${id}`);
export const testDeviceConnection = (id: string) => api.post<{ connected: boolean }>(`/devices/${id}/test`);

// Measurements
export const getMeasurements = (device_id?: string) =>
  api.get<Measurement[]>('/measurements', { params: device_id ? { device_id } : {} });
export const createMeasurement = (data: { device_id: string; name: string; description?: string; point_name?: string }) =>
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

// Report Config
export const getReportConfig = () => api.get('/reports/config');
export const updateReportConfig = (data: Record<string, string>) =>
  api.put('/reports/config', data);
