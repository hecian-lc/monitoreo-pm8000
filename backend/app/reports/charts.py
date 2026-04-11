"""Matplotlib chart generation for PDF/DOCX reports.
Ported from circutor-report-generator with InfluxDB data source."""

import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker


def _set_graph_font(font_name: str = "Century Gothic"):
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = [font_name, "Calibri", "Arial", "Helvetica"]


def _downsample_for_chart(timestamps: list, values: list, max_points: int = 3000) -> tuple[list, list]:
    """Downsample data if too many points for chart rendering."""
    if len(timestamps) <= max_points:
        return timestamps, values
    step = len(timestamps) // max_points
    return timestamps[::step], values[::step]


def crear_grafico_tension_fase(datos: dict, colores: dict | None = None) -> bytes | None:
    """Grafico de tension de fase (V L-N)."""
    ts = datos.get("timestamps", [])
    vl1 = datos.get("voltage_an", [])
    vl2 = datos.get("voltage_bn", [])
    vl3 = datos.get("voltage_cn", [])
    if not ts or not vl1:
        return None

    c = colores or {}
    cr, cs, ct = c.get("r", "#E74C3C"), c.get("s", "#3498DB"), c.get("t", "#2ECC71")

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ts_d, vl1_d = _downsample_for_chart(ts, vl1)
    _, vl2_d = _downsample_for_chart(ts, vl2)
    _, vl3_d = _downsample_for_chart(ts, vl3)

    ax.plot(ts_d, vl1_d, label="Fase R (L1)", color=cr, linewidth=1.2)
    if vl2_d: ax.plot(ts_d, vl2_d, label="Fase S (L2)", color=cs, linewidth=1.2)
    if vl3_d: ax.plot(ts_d, vl3_d, label="Fase T (L3)", color=ct, linewidth=1.2)
    ax.set_ylabel("Tensión (V)", fontsize=10)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def crear_grafico_tension_linea(datos: dict, colores: dict | None = None) -> bytes | None:
    """Grafico de tension de linea (V L-L)."""
    ts = datos.get("timestamps", [])
    vl12 = datos.get("voltage_ab", [])
    vl23 = datos.get("voltage_bc", [])
    vl31 = datos.get("voltage_ca", [])
    if not ts or not vl12:
        return None

    c = colores or {}
    cr, cs, ct = c.get("r", "#E74C3C"), c.get("s", "#3498DB"), c.get("t", "#2ECC71")

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ts_d, vl12_d = _downsample_for_chart(ts, vl12)
    _, vl23_d = _downsample_for_chart(ts, vl23)
    _, vl31_d = _downsample_for_chart(ts, vl31)

    ax.plot(ts_d, vl12_d, label="Línea RS (L1-L2)", color=cr, linewidth=1.2)
    if vl23_d: ax.plot(ts_d, vl23_d, label="Línea ST (L2-L3)", color=cs, linewidth=1.2)
    if vl31_d: ax.plot(ts_d, vl31_d, label="Línea TR (L3-L1)", color=ct, linewidth=1.2)
    ax.set_ylabel("Tensión (V)", fontsize=10)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def crear_grafico_corriente(datos: dict, colores: dict | None = None) -> bytes | None:
    """Grafico de corriente."""
    ts = datos.get("timestamps", [])
    il1 = datos.get("current_a", [])
    il2 = datos.get("current_b", [])
    il3 = datos.get("current_c", [])
    if not ts or not il1:
        return None

    c = colores or {}
    cr, cs, ct = c.get("r", "#E74C3C"), c.get("s", "#3498DB"), c.get("t", "#2ECC71")

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ts_d, il1_d = _downsample_for_chart(ts, il1)
    _, il2_d = _downsample_for_chart(ts, il2)
    _, il3_d = _downsample_for_chart(ts, il3)

    ax.plot(ts_d, il1_d, label="Fase R (L1)", color=cr, linewidth=1.2)
    if il2_d: ax.plot(ts_d, il2_d, label="Fase S (L2)", color=cs, linewidth=1.2)
    if il3_d: ax.plot(ts_d, il3_d, label="Fase T (L3)", color=ct, linewidth=1.2)
    ax.set_ylabel("Corriente (A)", fontsize=10)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def crear_grafico_potencia(datos: dict, colores: dict | None = None) -> bytes | None:
    """Grafico de potencia activa."""
    ts = datos.get("timestamps", [])
    p_total = datos.get("active_power_total", [])
    if not ts or not p_total:
        return None

    c = colores or {}
    ctr = c.get("trif", "#8E44AD")

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ts_d, pt_d = _downsample_for_chart(ts, [v / 1000 for v in p_total])

    ax.plot(ts_d, pt_d, label="Trifásica", color=ctr, linewidth=1.5)

    # Per-phase if available
    for key, label, color_key in [
        ("active_power_a", "Fase R (L1)", "r"),
        ("active_power_b", "Fase S (L2)", "s"),
        ("active_power_c", "Fase T (L3)", "t"),
    ]:
        vals = datos.get(key, [])
        if vals and len(vals) == len(ts):
            _, vd = _downsample_for_chart(ts, [v / 1000 for v in vals])
            ax.plot(ts_d, vd, label=label, color=c.get(color_key, "#999"), linewidth=1, alpha=0.7)

    ax.set_ylabel("Potencia Activa (kW)", fontsize=10)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def crear_grafico_fp(datos: dict, colores: dict | None = None) -> bytes | None:
    """Grafico de factor de potencia."""
    ts = datos.get("timestamps", [])
    fp_total = datos.get("power_factor_total", [])
    if not ts or not fp_total:
        return None

    c = colores or {}
    cr, cs, ct, ctr = c.get("r", "#E74C3C"), c.get("s", "#3498DB"), c.get("t", "#2ECC71"), c.get("trif", "#8E44AD")

    fig, ax = plt.subplots(figsize=(10, 4))
    fp_abs = [abs(v) for v in fp_total]
    ts_d, fp_d = _downsample_for_chart(ts, fp_abs)

    for key, label, col in [
        ("power_factor_a", "Fase R (L1)", cr),
        ("power_factor_b", "Fase S (L2)", cs),
        ("power_factor_c", "Fase T (L3)", ct),
    ]:
        vals = datos.get(key, [])
        if vals and len(vals) == len(ts):
            _, vd = _downsample_for_chart(ts, [abs(v) for v in vals])
            ax.plot(ts_d, vd, label=label, color=col, linewidth=1)

    ax.plot(ts_d, fp_d, label="Trifásico", color=ctr, linewidth=1.5)
    ax.axhline(y=0.92, color="red", linestyle="--", alpha=0.5, label="Mínimo (0,92)")
    ax.set_ylabel("cos(φ)", fontsize=10)
    ax.legend(loc="lower right", fontsize=8)
    ax.set_ylim(0.85, 1.02)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%H:%M"))
    fig.autofmt_xdate()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def crear_grafico_thd(datos: dict, colores: dict | None = None) -> bytes | None:
    """Grafico de THD de tension y corriente."""
    ts = datos.get("timestamps", [])
    v_thd_a = datos.get("thd_voltage_an", [])
    i_thd_a = datos.get("thd_current_a", [])
    if not ts or (not v_thd_a and not i_thd_a):
        return None

    c = colores or {}
    cr, cs, ct = c.get("r", "#E74C3C"), c.get("s", "#3498DB"), c.get("t", "#2ECC71")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    # Voltage THD
    for key, label, col in [
        ("thd_voltage_an", "L1", cr),
        ("thd_voltage_bn", "L2", cs),
        ("thd_voltage_cn", "L3", ct),
    ]:
        vals = datos.get(key, [])
        if vals:
            ts_d, vd = _downsample_for_chart(ts, vals)
            ax1.plot(ts_d, vd, label=label, color=col, linewidth=1.2)
    ax1.axhline(y=8, color="red", linestyle="--", alpha=0.5, label="Límite 8%")
    ax1.set_ylabel("% V THD", fontsize=10)
    ax1.legend(loc="upper right", fontsize=8)
    ax1.grid(True, alpha=0.3)

    # Current THD
    for key, label, col in [
        ("thd_current_a", "L1", cr),
        ("thd_current_b", "L2", cs),
        ("thd_current_c", "L3", ct),
    ]:
        vals = datos.get(key, [])
        if vals:
            ts_d, vd = _downsample_for_chart(ts, vals)
            ax2.plot(ts_d, vd, label=label, color=col, linewidth=1.2)
    ax2.set_ylabel("% I THD", fontsize=10)
    ax2.legend(loc="upper right", fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%H:%M"))

    fig.autofmt_xdate()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def generar_todos_los_graficos(datos: dict, colores: dict | None = None, fuente: str = "Century Gothic") -> list[tuple[str, bytes]]:
    """Generate all charts and return as list of (title, png_bytes)."""
    _set_graph_font(fuente)

    graficos = [
        ("Tensión de Fase", crear_grafico_tension_fase),
        ("Tensión de Línea", crear_grafico_tension_linea),
        ("Corriente", crear_grafico_corriente),
        ("Potencia Activa", crear_grafico_potencia),
        ("Factor de Potencia", crear_grafico_fp),
        ("Distorsión Armónica (THD)", crear_grafico_thd),
    ]

    resultado = []
    for titulo, func in graficos:
        png = func(datos, colores=colores)
        if png:
            resultado.append((titulo, png))

    return resultado
