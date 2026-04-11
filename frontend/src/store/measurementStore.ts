import { create } from 'zustand';
import type { Measurement } from '../types/meter';
import { getMeasurements } from '../api/endpoints';

interface MeasurementState {
  measurements: Measurement[];
  selected: Measurement | null;
  loading: boolean;
  fetch: () => Promise<void>;
  setSelected: (m: Measurement | null) => void;
}

export const useMeasurementStore = create<MeasurementState>((set) => ({
  measurements: [],
  selected: null,
  loading: false,
  fetch: async () => {
    set({ loading: true });
    try {
      const { data } = await getMeasurements();
      set({ measurements: data, loading: false });
    } catch {
      set({ loading: false });
    }
  },
  setSelected: (m) => set({ selected: m }),
}));
