"""Auto-generated observations and recommendations.
Ported from circutor-report-generator."""


def generar_observaciones_auto(stats: dict) -> str:
    """Generate observations comparing data against ANDE/IEEE 519 norms.

    Args:
        stats: Dict with keys like voltage_an, current_a, etc.
              Each has {min, max, mean, last} values.
    """
    obs = []
    rec = []

    # Tension de Fase (220V +/- 10% -> 198-242V)
    v_phases = ["voltage_an", "voltage_bn", "voltage_cn"]
    v_mins = [stats.get(k, {}).get("min", 0) for k in v_phases if k in stats]
    v_maxs = [stats.get(k, {}).get("max", 0) for k in v_phases if k in stats]
    if v_mins and v_maxs:
        v_min = min(v_mins)
        v_max = max(v_maxs)
        if v_min >= 198 and v_max <= 242:
            obs.append(f"Tensión de fase dentro del rango permitido ({v_min:.1f}-{v_max:.1f}V). Norma ANDE: 220V ± 10%.")
        else:
            obs.append(f"Tensión de fase fuera de rango ({v_min:.1f}-{v_max:.1f}V). Norma ANDE: 198-242V.")
            rec.append("Verificar regulación de tensión de fase. Considerar regulador de tensión.")

    # Tension de Linea (380V +/- 10% -> 342-418V)
    vl_phases = ["voltage_ab", "voltage_bc", "voltage_ca"]
    vl_mins = [stats.get(k, {}).get("min", 0) for k in vl_phases if k in stats]
    vl_maxs = [stats.get(k, {}).get("max", 0) for k in vl_phases if k in stats]
    if vl_mins and vl_maxs:
        vl_min = min(vl_mins)
        vl_max = max(vl_maxs)
        if vl_min >= 342 and vl_max <= 418:
            obs.append(f"Tensión de línea dentro del rango permitido ({vl_min:.1f}-{vl_max:.1f}V). Norma ANDE: 380V ± 10%.")
        else:
            obs.append(f"Tensión de línea fuera de rango ({vl_min:.1f}-{vl_max:.1f}V). Norma ANDE: 342-418V.")
            rec.append("Verificar regulación de tensión de línea.")

    # Corriente (desbalance)
    i_phases = ["current_a", "current_b", "current_c"]
    i_means = [stats.get(k, {}).get("mean", 0) for k in i_phases if k in stats]
    if len(i_means) == 3 and sum(i_means) > 0:
        avg_i = sum(i_means) / 3
        desb = max(abs(v - avg_i) for v in i_means) / avg_i * 100 if avg_i > 0 else 0
        if desb > 10:
            obs.append(f"Desbalance de corriente del {desb:.1f}%, superior al 10% recomendado.")
            rec.append("Redistribuir cargas entre fases para equilibrar corrientes.")
        else:
            obs.append(f"Corriente equilibrada entre fases (desbalance: {desb:.1f}%).")

    # Factor de Potencia (>0.92 Pliego N°21 ANDE)
    fp_stats = stats.get("power_factor_total", {})
    if fp_stats:
        fp_mean = abs(fp_stats.get("mean", 0))
        fp_min = abs(fp_stats.get("min", 0))
        if fp_min >= 0.92:
            obs.append(f"Factor de potencia cumple con Pliego N° 21 ANDE (cos φ = {fp_mean:.2f}, mín: {fp_min:.2f}). Norma: ≥ 0,92.")
        else:
            obs.append(f"Factor de potencia por debajo de lo exigido (cos φ = {fp_mean:.2f}, mín: {fp_min:.2f}). Norma ANDE: ≥ 0,92.")
            rec.append("Instalar banco de capacitores automático para corrección del factor de potencia.")

    # THD Tension (<8% IEEE 519)
    thd_v_phases = ["thd_voltage_an", "thd_voltage_bn", "thd_voltage_cn"]
    thd_v_maxs = [stats.get(k, {}).get("max", 0) for k in thd_v_phases if k in stats]
    if thd_v_maxs:
        thd_v = max(thd_v_maxs)
        if thd_v < 8:
            obs.append(f"Distorsión armónica de tensión dentro de norma (máx: {thd_v:.1f}% THD). IEEE 519: < 8%.")
        else:
            obs.append(f"Distorsión armónica de tensión fuera de norma ({thd_v:.1f}% THD). IEEE 519: < 8%.")
            rec.append("Instalar filtros de armónicos para reducir THD de tensión.")

    # THD Corriente
    thd_i_phases = ["thd_current_a", "thd_current_b", "thd_current_c"]
    thd_i_maxs = [stats.get(k, {}).get("max", 0) for k in thd_i_phases if k in stats]
    if thd_i_maxs:
        thd_i = max(thd_i_maxs)
        if thd_i > 20:
            obs.append(f"Distorsión armónica de corriente elevada (máx: {thd_i:.1f}% THD).")
            rec.append("Evaluar fuentes de armónicos y considerar filtros activos o pasivos.")
        else:
            obs.append(f"Distorsión armónica de corriente en niveles aceptables (máx: {thd_i:.1f}% THD).")

    # Frecuencia (50Hz +/- 2%)
    freq_stats = stats.get("frequency", {})
    if freq_stats:
        f_min = freq_stats.get("min", 50)
        f_max = freq_stats.get("max", 50)
        if 49 <= f_min and f_max <= 51:
            obs.append(f"Frecuencia estable ({f_min:.2f}-{f_max:.2f} Hz). Norma: 50 Hz ± 2%.")
        else:
            obs.append(f"Frecuencia fuera de rango ({f_min:.2f}-{f_max:.2f} Hz). Norma: 49-51 Hz.")

    # Recomendaciones generales
    rec.append("Instalar un analizador de redes permanente para monitoreo continuo de calidad de energía.")
    rec.append("Implementar un sistema de monitoreo remoto con software de gestión energética.")

    texto = "OBSERVACIONES:\n" + "\n".join(f"- {o}" for o in obs)
    texto += "\n\nRECOMENDACIONES:\n" + "\n".join(f"- {r}" for r in rec)
    return texto


def generar_observaciones_gemini(stats: dict, api_key: str) -> str:
    """Generate observations using Gemini AI."""
    try:
        from google import genai
    except ImportError:
        return "Error: Instale el SDK de Gemini con: pip install google-genai"

    resumen = _preparar_resumen(stats)
    client = genai.Client(api_key=api_key)

    prompt = f"""Eres un ingeniero eléctrico especialista en calidad de energía eléctrica en Paraguay.
Analiza los siguientes datos de un análisis de redes eléctricas y genera observaciones técnicas y recomendaciones profesionales.

Las normas de referencia son:
- Reglamento de Baja Tensión de la ANDE: tensión fase 220V ± 10%, tensión línea 380V ± 10%
- Pliego N° 21 de ANDE: factor de potencia > 0,92
- Norma IEEE 519: THD de tensión < 8%
- Frecuencia: 50 Hz ± 2%

DATOS MEDIDOS:
{resumen}

FORMATO DE RESPUESTA:
Sé BREVE y CONCISO. Máximo 7-8 observaciones y 5-6 recomendaciones.

OBSERVACIONES:
- Una observación por parámetro medido.

RECOMENDACIONES:
- Recomendaciones técnicas orientadas a mejorar la instalación.

IMPORTANTE: No uses markdown, asteriscos, negritas ni numeración. Solo texto plano con guiones.
Escribe en español, profesional y conciso."""

    import time
    modelos = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
    for intento in range(3):
        for modelo in modelos:
            try:
                response = client.models.generate_content(model=modelo, contents=prompt)
                return response.text
            except Exception:
                continue
        if intento < 2:
            time.sleep(10)

    return generar_observaciones_auto(stats)


def _preparar_resumen(stats: dict) -> str:
    """Prepare text summary of stats for AI prompt."""
    lineas = []
    for key, data in stats.items():
        if isinstance(data, dict) and "mean" in data:
            lineas.append(
                f"{key}: min={data.get('min', 0):.2f}, "
                f"max={data.get('max', 0):.2f}, "
                f"mean={data.get('mean', 0):.2f}"
            )
    return "\n".join(lineas)
