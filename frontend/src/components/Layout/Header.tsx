import { useRealtimeData } from '../../hooks/useRealtimeData';
import { Wifi, WifiOff, Circle } from 'lucide-react';

export default function Header() {
  const { connected, measurementId, timestamp } = useRealtimeData();

  return (
    <header className="h-12 bg-white border-b border-slate-200 flex items-center justify-between px-4">
      <div />
      <div className="flex items-center gap-4 text-sm">
        {measurementId && (
          <span className="flex items-center gap-1.5 text-slate-600">
            <Circle className="w-2 h-2 fill-red-500 text-red-500 animate-pulse" />
            Grabando
          </span>
        )}
        <span className={`flex items-center gap-1.5 ${connected ? 'text-green-600' : 'text-red-500'}`}>
          {connected ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
          {connected ? 'Conectado' : 'Desconectado'}
        </span>
        {timestamp && (
          <span className="text-slate-400 text-xs">
            {new Date(timestamp).toLocaleTimeString()}
          </span>
        )}
      </div>
    </header>
  );
}
