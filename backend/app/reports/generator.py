"""Report generation orchestrator.
Queries InfluxDB, generates charts, builds DOCX, optionally converts to PDF."""

import logging
import os
import uuid
from datetime import datetime

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from ..config import settings
from ..db.queries import query_data, query_stats
from ..db.sqlite import Database
from .analysis import generar_observaciones_auto, generar_observaciones_gemini
from .charts import generar_todos_los_graficos
from .docx_builder import generar_informe

logger = logging.getLogger(__name__)


async def generate_report(
    report_id: str,
    measurement_id: str,
    influx_client: InfluxDBClientAsync,
    db: Database,
    report_config_overrides: dict | None = None,
):
    """Generate a complete DOCX report for a measurement.

    1. Query InfluxDB for stats (min/max/mean/last)
    2. Query time-series for charts
    3. Generate observations (auto/gemini)
    4. Generate matplotlib charts
    5. Build DOCX with python-docx
    6. Optionally convert to PDF
    """
    try:
        await db.update_report(report_id, status="generating")

        # Get measurement info
        measurement = await db.get_measurement(measurement_id)
        if not measurement:
            raise ValueError(f"Measurement {measurement_id} not found")

        # Determine time range
        started_at = measurement.get("started_at")
        stopped_at = measurement.get("stopped_at")
        if started_at:
            start = datetime.fromisoformat(started_at)
        else:
            start = datetime.fromisoformat(measurement["created_at"])
        end = datetime.fromisoformat(stopped_at) if stopped_at else datetime.utcnow()

        # Get report config from DB + overrides
        saved_config = await db.get_report_config()
        config = {**saved_config}
        if report_config_overrides:
            config.update({k: v for k, v in report_config_overrides.items() if v is not None})

        config["punto_medicion"] = config.get("punto_medicion") or measurement.get("point_name", "T.G.")
        config["periodo_inicio"] = start.strftime("%d/%m/%Y %H:%M")
        config["periodo_fin"] = end.strftime("%d/%m/%Y %H:%M")
        if not config.get("fecha"):
            config["fecha"] = datetime.now().strftime("%d/%m/%Y")

        # Resolve image paths
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        for img_key in ["img_portada", "img_encabezado", "img_pie"]:
            path = config.get(img_key, "")
            if path and not os.path.isabs(path):
                config[img_key] = os.path.join(assets_dir, path)

        # 1. Query stats
        logger.info(f"Querying stats for measurement {measurement_id}")
        stats = await query_stats(
            influx_client,
            measurement_id=measurement_id,
            start=start,
            end=end,
        )

        # 2. Query time-series data for charts (max 5000 points)
        logger.info("Querying time-series for charts")
        chart_vars = [
            "voltage_an", "voltage_bn", "voltage_cn",
            "voltage_ab", "voltage_bc", "voltage_ca",
            "current_a", "current_b", "current_c",
            "active_power_total", "active_power_a", "active_power_b", "active_power_c",
            "power_factor_total", "power_factor_a", "power_factor_b", "power_factor_c",
            "thd_voltage_an", "thd_voltage_bn", "thd_voltage_cn",
            "thd_current_a", "thd_current_b", "thd_current_c",
        ]
        raw_data = await query_data(
            influx_client,
            measurement_id=measurement_id,
            start=start,
            end=end,
            variables=chart_vars,
            max_points=3000,
        )

        # Transform to chart-friendly format: {field_name: [values], timestamps: [datetime]}
        chart_data: dict = {"timestamps": []}
        field_series: dict[str, dict[str, float]] = {}  # time -> field -> value

        for record in raw_data:
            t = record["time"]
            field = record["field"]
            val = record["value"]
            if t not in field_series:
                field_series[t] = {}
            field_series[t][field] = val

        sorted_times = sorted(field_series.keys())
        chart_data["timestamps"] = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t in sorted_times]

        for field in chart_vars:
            chart_data[field] = [field_series.get(t, {}).get(field, float("nan")) for t in sorted_times]

        # 3. Generate observations
        obs_mode = (report_config_overrides or {}).get("observaciones_mode", "auto")
        manual_obs = (report_config_overrides or {}).get("observaciones")

        if manual_obs:
            observaciones = manual_obs
        elif obs_mode == "gemini" and settings.gemini_api_key:
            logger.info("Generating observations with Gemini AI")
            observaciones = generar_observaciones_gemini(stats, settings.gemini_api_key)
        else:
            logger.info("Generating observations with rules")
            observaciones = generar_observaciones_auto(stats)

        # 4. Generate charts
        colores = {
            "r": config.get("color_fase_r", "#E74C3C"),
            "s": config.get("color_fase_s", "#3498DB"),
            "t": config.get("color_fase_t", "#2ECC71"),
            "trif": config.get("color_trif", "#8E44AD"),
        }
        logger.info("Generating charts")
        chart_images = generar_todos_los_graficos(
            chart_data,
            colores=colores,
            fuente=config.get("fuente", "Century Gothic"),
        )

        # 5. Build DOCX
        report_record = await db.get_report(report_id)
        fmt = report_record.get("format", "docx") if report_record else "docx"
        filename = f"{config.get('cliente', 'Informe')}_{measurement_id}_{report_id}.docx"
        output_path = os.path.join(settings.base_dir / settings.reports_output_dir, filename)

        logger.info(f"Building DOCX: {output_path}")
        generar_informe(
            stats=stats,
            config=config,
            chart_images=chart_images,
            observaciones=observaciones,
            output_path=output_path,
        )

        # 6. Convert to PDF if requested
        if fmt == "pdf":
            try:
                from docx2pdf import convert
                pdf_path = output_path.replace(".docx", ".pdf")
                convert(output_path, pdf_path)
                os.remove(output_path)
                output_path = pdf_path
                logger.info(f"Converted to PDF: {pdf_path}")
            except ImportError:
                logger.warning("docx2pdf not available, keeping DOCX format")

        # 7. Update report record
        await db.update_report(
            report_id,
            status="completed",
            file_path=output_path,
            completed_at=datetime.utcnow().isoformat(),
        )
        logger.info(f"Report {report_id} completed: {output_path}")

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        await db.update_report(
            report_id,
            status="error",
            error_message=str(e),
        )
