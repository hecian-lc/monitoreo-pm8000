import { useEffect } from 'react';
import { wsManager } from '../api/websocket';
import { useRealtimeStore } from '../store/realtimeStore';

export function useRealtimeData() {
  const { connected, data, timestamp, measurementId, setReadings } = useRealtimeStore();

  useEffect(() => {
    wsManager.connect();
    const unsub = wsManager.subscribe(setReadings);
    return () => {
      unsub();
    };
  }, [setReadings]);

  return { connected, data, timestamp, measurementId };
}
