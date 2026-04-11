"""Data export endpoints (CSV / XLSX)."""

import csv
import io
from datetime import datetime

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from ...db.queries import query_data
from ..deps import get_influx

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/csv")
async def export_csv(
    measurement_id: str,
    start: datetime,
    end: datetime,
    variables: list[str] | None = Query(None),
    phases: list[str] | None = Query(None),
    categories: list[str] | None = Query(None),
    max_points: int = Query(50000, le=100000),
):
    """Export data as CSV file."""
    client = get_influx()
    data = await query_data(
        client,
        measurement_id=measurement_id,
        start=start,
        end=end,
        variables=variables,
        phases=phases,
        categories=categories,
        max_points=max_points,
    )

    def generate():
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")
        writer.writerow(["Timestamp", "Variable", "Phase", "Category", "Value"])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        for record in data:
            writer.writerow([
                record["time"],
                record["field"],
                record["phase"],
                record["category"],
                record["value"],
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    filename = f"medicion_{measurement_id}_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/xlsx")
async def export_xlsx(
    measurement_id: str,
    start: datetime,
    end: datetime,
    variables: list[str] | None = Query(None),
    phases: list[str] | None = Query(None),
    categories: list[str] | None = Query(None),
    max_points: int = Query(50000, le=100000),
):
    """Export data as Excel file."""
    from openpyxl import Workbook

    client = get_influx()
    data = await query_data(
        client,
        measurement_id=measurement_id,
        start=start,
        end=end,
        variables=variables,
        phases=phases,
        categories=categories,
        max_points=max_points,
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Datos"
    ws.append(["Timestamp", "Variable", "Fase", "Categoría", "Valor"])

    for record in data:
        ws.append([
            record["time"],
            record["field"],
            record["phase"],
            record["category"],
            record["value"],
        ])

    # Auto-fit columns
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"medicion_{measurement_id}_{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
