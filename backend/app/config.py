"""Application configuration via environment variables."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # InfluxDB
    influxdb_url: str = "http://localhost:8086"
    influxdb_token: str = "monitoreo-pm8000-token"
    influxdb_org: str = "monitoreo"
    influxdb_bucket: str = "pm_raw"
    influxdb_bucket_1min: str = "pm_1min"
    influxdb_bucket_15min: str = "pm_15min"
    influxdb_bucket_1hour: str = "pm_1hour"

    # Modbus
    modbus_host: str = "192.168.1.100"
    modbus_port: int = 502
    modbus_unit_id: int = 1
    poll_interval: float = 1.0

    # Register map
    register_map_path: str = "registers/pm8000_default.yaml"

    # SQLite
    sqlite_path: str = "data/monitoreo.db"

    # Reports output
    reports_output_dir: str = "reports-output"

    # Gemini AI (optional)
    gemini_api_key: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    @property
    def base_dir(self) -> Path:
        return Path(__file__).parent.parent

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
