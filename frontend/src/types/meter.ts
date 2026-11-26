export interface Measurement {
  id: string;
  name: string;
  description: string;
  point_name: string;
  status: 'idle' | 'recording' | 'stopped' | 'compressed';
  resolution: string;
  created_at: string;
  started_at: string | null;
  stopped_at: string | null;
  compressed_at: string | null;
}

// Lo que manda el backend por /ws/realtime (collector/broadcast.py)
export interface ReadingsMessage {
  type: 'readings';
  timestamp: string;
  connected: boolean;
  measurement_id: string | null;
  data: Record<string, number>;
}

export interface StatusMessage {
  type: 'status';
  timestamp: string;
  status: string;
  message: string;
}

export type RealtimeMessage = ReadingsMessage | StatusMessage;

export interface DataRecord {
  time: string;
  field: string;
  value: number | null;
  phase: string;
  category: string;
}

export interface HealthStatus {
  status: string;
  running: boolean;
  connected: boolean;
  active_measurement_id: string | null;
  poll_interval: number;
  cycle_time_ms: number;
  total_cycles: number;
  error_count: number;
  ws_clients: number;
}

export interface DeviceConfig {
  host: string;
  port: number;
  unit_id: number;
  poll_interval: number;
  register_map: string;
  byte_order: string;
  word_order: string;
}
