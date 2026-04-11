import { create } from 'zustand';
import type { RealtimeMessage } from '../types/meter';

interface RealtimeState {
  connected: boolean;
  measurementId: string | null;
  data: Record<string, number>;
  timestamp: string | null;
  setReadings: (msg: RealtimeMessage) => void;
}

export const useRealtimeStore = create<RealtimeState>((set) => ({
  connected: false,
  measurementId: null,
  data: {},
  timestamp: null,
  setReadings: (msg) => {
    if (msg.type === 'readings') {
      set({
        connected: msg.connected,
        measurementId: msg.measurement_id,
        data: msg.data,
        timestamp: msg.timestamp,
      });
    } else if (msg.type === 'status') {
      set({ connected: (msg as any).status === 'connected' });
    }
  },
}));
