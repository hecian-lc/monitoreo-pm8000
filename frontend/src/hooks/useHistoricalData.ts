import { useState, useCallback } from 'react';
import { queryData } from '../api/endpoints';
import type { DataRecord } from '../types/meter';

export function useHistoricalData() {
  const [data, setData] = useState<DataRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async (params: {
    measurement_id: string;
    start: string;
    end: string;
    variables?: string[];
    categories?: string[];
    max_points?: number;
  }) => {
    setLoading(true);
    setError(null);
    try {
      const res = await queryData(params);
      setData(res.data.data);
    } catch (e: unknown) {
      setError(e instanceof Error && e.message ? e.message : 'Error fetching data');
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, fetch };
}
