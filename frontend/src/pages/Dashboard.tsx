import { useRealtimeData } from '../hooks/useRealtimeData';
import GaugeCard from '../components/Dashboard/GaugeCard';
import PhaseGrid from '../components/Dashboard/PhaseGrid';

export default function Dashboard() {
  const { connected, data } = useRealtimeData();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>

      {!connected && (
        <div className="bg-amber-50 border border-amber-200 text-amber-700 px-4 py-3 rounded-lg text-sm">
          Sin conexi&oacute;n al medidor PM8000. Verifique la conexi&oacute;n Modbus.
        </div>
      )}

      {/* Voltage Phase */}
      <PhaseGrid
        title="Tensi&oacute;n de Fase"
        unit="V"
        phaseA={data.voltage_an}
        phaseB={data.voltage_bn}
        phaseC={data.voltage_cn}
        total={data.voltage_avg_ln}
      />

      {/* Voltage Line */}
      <PhaseGrid
        title="Tensi&oacute;n de L&iacute;nea"
        unit="V"
        phaseA={data.voltage_ab}
        phaseB={data.voltage_bc}
        phaseC={data.voltage_ca}
        total={data.voltage_avg_ll}
      />

      {/* Current */}
      <PhaseGrid
        title="Corriente"
        unit="A"
        phaseA={data.current_a}
        phaseB={data.current_b}
        phaseC={data.current_c}
        total={data.current_avg}
      />

      {/* Power */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <GaugeCard label="Potencia Activa Total" value={data.active_power_total ? data.active_power_total / 1000 : undefined} unit="kW" color="#8E44AD" />
        <GaugeCard label="Potencia Reactiva Total" value={data.reactive_power_total ? data.reactive_power_total / 1000 : undefined} unit="kVAR" color="#E67E22" />
        <GaugeCard label="Potencia Aparente Total" value={data.apparent_power_total ? data.apparent_power_total / 1000 : undefined} unit="kVA" color="#2980B9" />
        <GaugeCard label="Factor de Potencia" value={data.power_factor_total ? Math.abs(data.power_factor_total) : undefined} unit="cos&phi;" color={data.power_factor_total && Math.abs(data.power_factor_total) < 0.92 ? '#E74C3C' : '#27AE60'} decimals={3} />
      </div>

      {/* Misc */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <GaugeCard label="Frecuencia" value={data.frequency} unit="Hz" />
        <GaugeCard label="THD Tensi&oacute;n A" value={data.thd_voltage_an} unit="%" color={data.thd_voltage_an && data.thd_voltage_an > 8 ? '#E74C3C' : '#27AE60'} />
        <GaugeCard label="THD Corriente A" value={data.thd_current_a} unit="%" />
        <GaugeCard label="Energ&iacute;a Activa" value={data.active_energy_delivered ? data.active_energy_delivered / 1000 : undefined} unit="kWh" decimals={1} />
      </div>

      {/* Power Factor per phase */}
      <PhaseGrid
        title="Factor de Potencia por Fase"
        unit=""
        phaseA={data.power_factor_a ? Math.abs(data.power_factor_a) : undefined}
        phaseB={data.power_factor_b ? Math.abs(data.power_factor_b) : undefined}
        phaseC={data.power_factor_c ? Math.abs(data.power_factor_c) : undefined}
        total={data.power_factor_total ? Math.abs(data.power_factor_total) : undefined}
        decimals={3}
      />

      {/* THD */}
      <PhaseGrid
        title="THD Tensi&oacute;n"
        unit="%"
        phaseA={data.thd_voltage_an}
        phaseB={data.thd_voltage_bn}
        phaseC={data.thd_voltage_cn}
      />
    </div>
  );
}
