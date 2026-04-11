"""DOCX report generator - identical format to circutor-report-generator.
Generates a professional power quality analysis report."""

import io
import os
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, Cm, Emu, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml


# ─── Utilities (ported from circutor-report-generator) ───

def fmt(val, decimals=2):
    """Format number with comma as decimal separator."""
    if val is None:
        return "—"
    return f"{val:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def hex_to_rgb(hex_color: str) -> RGBColor:
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def set_cell_shading(cell, color_hex: str):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_borders(cell, top="single", bottom="single", left="single", right="single", sz=4, color="000000"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'  <w:top w:val="{top}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="{bottom}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="{left}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:right w:val="{right}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(tcBorders)


def set_cell_text(cell, text, bold=False, size=9, alignment=WD_ALIGN_PARAGRAPH.CENTER, color=None, font_name="Calibri"):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = alignment
    run = p.add_run(str(text))
    run.font.size = Pt(size)
    run.font.name = font_name
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    vAlign = parse_xml(f'<w:vAlign {nsdecls("w")} w:val="center"/>')
    tcPr.append(vAlign)


def _valor_color(valor, min_ok, max_ok, color_ok="E2EFD9", color_warn="FBE4D5"):
    if valor is None:
        return None
    if min_ok is not None and valor < min_ok:
        return color_warn
    if max_ok is not None and valor > max_ok:
        return color_warn
    return color_ok


def _inline_to_anchor_top_bottom(run, width_emu, height_emu, pos_h_offset=0, pos_v_offset=0,
                                  relative_from_h="page", relative_from_v="paragraph"):
    ns_wp = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
    ns_a = "http://schemas.openxmlformats.org/drawingml/2006/main"
    ns_w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

    drawing = run._element.find(f'{{{ns_w}}}drawing')
    if drawing is None:
        return
    inline = drawing.find(f'{{{ns_wp}}}inline')
    if inline is None:
        return

    graphic = inline.find(f'{{{ns_a}}}graphic')
    docPr = inline.find(f'{{{ns_wp}}}docPr')

    anchor_xml = f'''<wp:anchor distT="0" distB="0" distL="0" distR="0"
        simplePos="0" relativeHeight="0" behindDoc="0" locked="0"
        layoutInCell="1" allowOverlap="1"
        xmlns:wp="{ns_wp}" xmlns:a="{ns_a}">
        <wp:simplePos x="0" y="0"/>
        <wp:positionH relativeFrom="{relative_from_h}">
            <wp:posOffset>{pos_h_offset}</wp:posOffset>
        </wp:positionH>
        <wp:positionV relativeFrom="{relative_from_v}">
            <wp:posOffset>{pos_v_offset}</wp:posOffset>
        </wp:positionV>
        <wp:extent cx="{width_emu}" cy="{height_emu}"/>
        <wp:effectExtent l="0" t="0" r="0" b="0"/>
        <wp:wrapTopAndBottom/>
    </wp:anchor>'''

    anchor = parse_xml(anchor_xml)
    if docPr is not None:
        anchor.append(docPr)
    if graphic is not None:
        anchor.append(graphic)
    drawing.remove(inline)
    drawing.append(anchor)


# ─── Main report builder ───

def generar_informe(
    stats: dict,
    config: dict,
    chart_images: list[tuple[str, bytes]],
    observaciones: str,
    output_path: str,
) -> str:
    """Generate the DOCX report.

    Args:
        stats: Dict with keys like voltage_an -> {min, max, mean, last}
        config: Report config (cliente, num_informe, fuente, colors, images, etc.)
        chart_images: List of (title, png_bytes) tuples
        observaciones: Observations text (OBSERVACIONES: + RECOMENDACIONES:)
        output_path: Where to save the .docx file

    Returns:
        Path to the generated file
    """
    doc = Document()

    fuente = config.get("fuente", "Century Gothic")
    color_principal = config.get("color_principal", "#202E6B")
    color_enc_tabla = config.get("color_encabezado_tabla", "#DDEBF7")
    cp_rgb = hex_to_rgb(color_principal)
    enc_tabla_hex = color_enc_tabla.lstrip("#")

    img_encabezado = config.get("img_encabezado", "")
    img_pie = config.get("img_pie", "")

    # Page setup A4
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.left_margin = Cm(1.5)
        section.right_margin = Cm(1.7)
        section.top_margin = Cm(6.0)
        section.bottom_margin = Cm(2.54)
        section.header_distance = Cm(0.6)
        section.footer_distance = Cm(0.3)
        section.different_first_page_header_footer = True

    # ── PORTADA ──
    img_portada = config.get("img_portada", "")
    if img_portada and os.path.exists(img_portada):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run()
        run.add_picture(img_portada, width=Cm(21.0), height=Cm(29.7))
        # Note: anchor conversion simplified - works in most Word renderers
    else:
        for _ in range(6):
            doc.add_paragraph("")
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("Análisis de Redes")
        run.font.size = Pt(36)
        run.font.color.rgb = cp_rgb
        run.font.bold = True
        run.font.name = fuente

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(config.get("cliente", ""))
        run.font.size = Pt(28)
        run.font.color.rgb = RGBColor(0x2C, 0x3E, 0x50)
        run.font.name = fuente

    doc.add_page_break()

    # ── PAGE 2: Info + Table ──
    sz = 10
    fn = fuente

    # Date
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    fecha = config.get("fecha", datetime.now().strftime("%d/%m/%Y"))
    run = p.add_run(f"Asunción, {fecha}. –")
    run.font.size = Pt(10)
    run.font.name = fn

    doc.add_paragraph("")

    # AR N°
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(f"AR N° {config.get('num_informe', '')}")
    run.font.size = Pt(10.5)
    run.font.bold = True
    run.font.name = fn

    # Señores / Cliente
    for text, bold in [("Señores", False), (config.get("cliente", ""), True)]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(text)
        run.font.size = Pt(10.5)
        run.font.bold = bold
        run.font.name = fn

    if config.get("atencion"):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(f"At.: {config['atencion']}")
        run.font.size = Pt(10.5)
        run.font.name = fn

    # Presente
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Emu(76200)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run("Presente:")
    run.font.size = Pt(10.5)
    run.font.name = fn

    # INFORME TÉCNICO
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Emu(76200)
    run = p.add_run("INFORME TÉCNICO")
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = cp_rgb
    run.font.name = fn

    # Bullet items
    items = [
        f"Objetivo: {config.get('objetivo', 'Conocer la potencia utilizada y disponible en el punto de medición.')} –",
        f"Equipo utilizado: {config.get('equipo', 'Schneider Electric PM8000.')} –",
        f"Periodicidad de muestreo: {config.get('periodicidad', '1 segundo.')} –",
    ]
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(item)
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.color.rgb = cp_rgb
        run.font.name = fn

    doc.add_paragraph("")

    # ── SUMMARY TABLE (21 rows x 8 columns) ──
    _build_summary_table(doc, stats, config, fn, sz, cp_rgb, enc_tabla_hex)

    doc.add_page_break()

    # ── CHART PAGES ──
    graficos_por_pagina = 2
    for i, (titulo, png_bytes) in enumerate(chart_images):
        if i > 0 and i % graficos_por_pagina == 0:
            doc.add_page_break()

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Emu(76200)
        p.paragraph_format.space_after = Emu(38100)
        run = p.add_run(titulo)
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = cp_rgb
        run.font.name = fn

        doc.add_picture(io.BytesIO(png_bytes), width=Inches(6.5))
        p = doc.paragraphs[-1]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if chart_images:
        doc.add_page_break()

    # ── CONCLUSION ──
    texto_obs = observaciones
    texto_rec = ""
    for sep in ["RECOMENDACIONES:", "Recomendaciones:"]:
        if sep in observaciones:
            partes = observaciones.split(sep, 1)
            texto_obs = partes[0].strip()
            texto_rec = partes[1].strip() if len(partes) > 1 else ""
            break

    for etiqueta in ["OBSERVACIONES:", "Observaciones:"]:
        if texto_obs.startswith(etiqueta):
            texto_obs = texto_obs[len(etiqueta):].strip()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("CONCLUSIÓN")
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = cp_rgb
    run.font.name = fn

    doc.add_paragraph("")

    if texto_obs:
        for linea in texto_obs.split("\n"):
            linea = linea.strip().lstrip("-•").strip()
            if linea:
                p = doc.add_paragraph(style="List Bullet")
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.line_spacing = 1.15
                run = p.add_run(linea)
                run.font.size = Pt(10)
                run.font.name = fn

    if texto_rec:
        doc.add_page_break()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("RECOMENDACIONES")
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = cp_rgb
        run.font.name = fn

        doc.add_paragraph("")

        for linea in texto_rec.split("\n"):
            linea = linea.strip().lstrip("-•").strip()
            if linea:
                p = doc.add_paragraph(style="List Bullet")
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.line_spacing = 1.15
                run = p.add_run(linea)
                run.font.size = Pt(10)
                run.font.name = fn

    doc.add_paragraph("")

    # Firma
    for text in [
        config.get("firma_empresa", ""),
        config.get("firma_nombre", ""),
        config.get("firma_cargo", ""),
    ]:
        if text:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run(text)
            run.font.size = Pt(10)
            run.font.bold = True
            run.font.name = fn

    # ── HEADER / FOOTER ──
    for section in doc.sections:
        fp_header = section.first_page_header
        fp_header.is_linked_to_previous = False
        if fp_header.paragraphs:
            fp_header.paragraphs[0].text = ""
        fp_footer = section.first_page_footer
        fp_footer.is_linked_to_previous = False
        if fp_footer.paragraphs:
            fp_footer.paragraphs[0].text = ""

        header = section.header
        header.is_linked_to_previous = False
        if img_encabezado and os.path.exists(img_encabezado):
            p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run()
            run.add_picture(img_encabezado, width=Cm(20.98), height=Cm(5.28))
            _inline_to_anchor_top_bottom(run, width_emu=Cm(20.98), height_emu=Cm(5.28),
                                          pos_h_offset=0, pos_v_offset=-449992)

        footer = section.footer
        footer.is_linked_to_previous = False
        if img_pie and os.path.exists(img_pie):
            p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            run = p.add_run()
            run.add_picture(img_pie, width=Cm(21.0), height=Cm(2.18))
            _inline_to_anchor_top_bottom(run, width_emu=Cm(21.0), height_emu=Cm(2.18),
                                          pos_h_offset=0, pos_v_offset=0)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    doc.save(output_path)
    return output_path


def _build_summary_table(doc, stats, config, fn, sz, cp_rgb, enc_tabla_hex):
    """Build the 21-row x 8-column summary table."""
    from docx.enum.table import WD_ROW_HEIGHT_RULE

    CR = RGBColor(0xFF, 0x00, 0x00)
    CS = RGBColor(0x80, 0x80, 0x80)
    CT = RGBColor(0x30, 0x54, 0x96)

    # Extract values from stats
    def s(key, stat="mean"):
        return stats.get(key, {}).get(stat)

    def s_max(key):
        return s(key, "max")

    def s_min(key):
        return s(key, "min")

    def s_last(key):
        return s(key, "last")

    periodo_inicio = config.get("periodo_inicio", "—")
    periodo_fin = config.get("periodo_fin", "—")

    table = doc.add_table(rows=21, cols=8)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    for row in table.rows:
        row.height = Cm(0.5)
        row.height_rule = WD_ROW_HEIGHT_RULE.EXACTLY
        for cell in row.cells:
            set_cell_borders(cell, sz=4, color="808080")

    # ── Merges ──
    table.cell(0, 0).merge(table.cell(0, 2))
    table.cell(0, 3).merge(table.cell(0, 7))
    table.cell(1, 0).merge(table.cell(2, 2))
    table.cell(1, 4).merge(table.cell(1, 7))
    table.cell(2, 4).merge(table.cell(2, 7))
    table.cell(3, 0).merge(table.cell(3, 2))
    table.cell(3, 4).merge(table.cell(3, 6))
    table.cell(4, 0).merge(table.cell(4, 3))
    table.cell(5, 0).merge(table.cell(9, 0))
    table.cell(5, 1).merge(table.cell(6, 1))
    table.cell(7, 1).merge(table.cell(7, 3))
    table.cell(8, 1).merge(table.cell(9, 1))
    table.cell(10, 0).merge(table.cell(10, 3))
    table.cell(11, 0).merge(table.cell(12, 1))
    table.cell(13, 0).merge(table.cell(14, 1))
    table.cell(13, 4).merge(table.cell(13, 6))
    table.cell(14, 4).merge(table.cell(14, 6))
    table.cell(15, 0).merge(table.cell(15, 1))
    table.cell(15, 4).merge(table.cell(15, 6))
    table.cell(16, 0).merge(table.cell(16, 1))
    table.cell(16, 4).merge(table.cell(16, 6))
    table.cell(17, 0).merge(table.cell(17, 1))
    table.cell(17, 4).merge(table.cell(17, 6))
    table.cell(18, 0).merge(table.cell(18, 2))
    table.cell(18, 4).merge(table.cell(18, 6))
    table.cell(19, 0).merge(table.cell(19, 2))
    table.cell(19, 4).merge(table.cell(19, 6))
    table.cell(20, 0).merge(table.cell(20, 2))
    table.cell(20, 4).merge(table.cell(20, 6))

    # vAlign center for all
    for row in table.rows:
        for cell in row.cells:
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            if tcPr.find(qn('w:vAlign')) is None:
                tcPr.append(parse_xml(f'<w:vAlign {nsdecls("w")} w:val="center"/>'))

    # ── Content ──
    # R0: Header
    for ci in range(8):
        set_cell_shading(table.cell(0, ci), enc_tabla_hex)
    set_cell_text(table.cell(0, 0), "PUNTO DE MEDICIÓN", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(0, 3), config.get("punto_medicion", "T.G."), bold=True, size=sz, font_name=fn)

    # R1-R2: Period
    set_cell_text(table.cell(1, 0), "Periodo de Registro", size=sz, font_name=fn)
    set_cell_text(table.cell(1, 3), "Inicio", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(1, 4), periodo_inicio, size=sz, font_name=fn)
    set_cell_text(table.cell(2, 3), "Fin", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(2, 4), periodo_fin, size=sz, font_name=fn)

    # R3: Headers
    set_cell_text(table.cell(3, 0), "Magnitud", size=sz, font_name=fn)
    set_cell_text(table.cell(3, 3), "Unidad", size=sz, font_name=fn)
    set_cell_text(table.cell(3, 4), "Valores Obtenidos", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(3, 7), "Valores Normales", bold=True, size=sz, font_name=fn)

    # R4: Phase sub-headers
    set_cell_text(table.cell(4, 4), "Fase RN", bold=True, size=sz, font_name=fn, color=CR)
    set_cell_text(table.cell(4, 5), "Fase SN", bold=True, size=sz, font_name=fn, color=CS)
    set_cell_text(table.cell(4, 6), "Fase TN", bold=True, size=sz, font_name=fn, color=CT)

    # R5-R6: Phase Voltage
    set_cell_text(table.cell(5, 0), "Tensión", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(5, 1), "Fase", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(5, 2), "Máxima", size=sz, font_name=fn)
    set_cell_text(table.cell(5, 3), "(V)", size=sz, font_name=fn)
    set_cell_text(table.cell(5, 4), fmt(s_max("voltage_an")), size=sz, font_name=fn)
    set_cell_text(table.cell(5, 5), fmt(s_max("voltage_bn")), size=sz, font_name=fn)
    set_cell_text(table.cell(5, 6), fmt(s_max("voltage_cn")), size=sz, font_name=fn)
    c = _valor_color(max(s_max("voltage_an") or 0, s_max("voltage_bn") or 0, s_max("voltage_cn") or 0), None, 242)
    if c: set_cell_shading(table.cell(5, 7), c)
    set_cell_text(table.cell(5, 7), "< 220 + 10%", bold=True, size=sz, font_name=fn)

    set_cell_text(table.cell(6, 2), "Mínima", size=sz, font_name=fn)
    set_cell_text(table.cell(6, 3), "(V)", size=sz, font_name=fn)
    set_cell_text(table.cell(6, 4), fmt(s_min("voltage_an")), size=sz, font_name=fn)
    set_cell_text(table.cell(6, 5), fmt(s_min("voltage_bn")), size=sz, font_name=fn)
    set_cell_text(table.cell(6, 6), fmt(s_min("voltage_cn")), size=sz, font_name=fn)
    c = _valor_color(min(s_min("voltage_an") or 999, s_min("voltage_bn") or 999, s_min("voltage_cn") or 999), 198, None)
    if c: set_cell_shading(table.cell(6, 7), c)
    set_cell_text(table.cell(6, 7), "> 220 – 10%", bold=True, size=sz, font_name=fn)

    # R7: Line voltage sub-headers
    set_cell_text(table.cell(7, 4), "Línea RS", bold=True, size=sz, font_name=fn, color=CR)
    set_cell_text(table.cell(7, 5), "Línea ST", bold=True, size=sz, font_name=fn, color=CS)
    set_cell_text(table.cell(7, 6), "Línea TR", bold=True, size=sz, font_name=fn, color=CT)

    # R8-R9: Line Voltage
    set_cell_text(table.cell(8, 1), "Línea", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(8, 2), "Máxima", size=sz, font_name=fn)
    set_cell_text(table.cell(8, 3), "(V)", size=sz, font_name=fn)
    set_cell_text(table.cell(8, 4), fmt(s_max("voltage_ab")), size=sz, font_name=fn)
    set_cell_text(table.cell(8, 5), fmt(s_max("voltage_bc")), size=sz, font_name=fn)
    set_cell_text(table.cell(8, 6), fmt(s_max("voltage_ca")), size=sz, font_name=fn)
    c = _valor_color(max(s_max("voltage_ab") or 0, s_max("voltage_bc") or 0, s_max("voltage_ca") or 0), None, 418)
    if c: set_cell_shading(table.cell(8, 7), c)
    set_cell_text(table.cell(8, 7), "< 380 + 10%", bold=True, size=sz, font_name=fn)

    set_cell_text(table.cell(9, 2), "Mínima", size=sz, font_name=fn)
    set_cell_text(table.cell(9, 3), "(V)", size=sz, font_name=fn)
    set_cell_text(table.cell(9, 4), fmt(s_min("voltage_ab")), size=sz, font_name=fn)
    set_cell_text(table.cell(9, 5), fmt(s_min("voltage_bc")), size=sz, font_name=fn)
    set_cell_text(table.cell(9, 6), fmt(s_min("voltage_ca")), size=sz, font_name=fn)
    c = _valor_color(min(s_min("voltage_ab") or 999, s_min("voltage_bc") or 999, s_min("voltage_ca") or 999), 342, None)
    if c: set_cell_shading(table.cell(9, 7), c)
    set_cell_text(table.cell(9, 7), "> 380 – 10%", bold=True, size=sz, font_name=fn)

    # R10: Current sub-headers
    set_cell_text(table.cell(10, 4), "Fase R", bold=True, size=sz, font_name=fn, color=CR)
    set_cell_text(table.cell(10, 5), "Fase S", bold=True, size=sz, font_name=fn, color=CS)
    set_cell_text(table.cell(10, 6), "Fase T", bold=True, size=sz, font_name=fn, color=CT)

    # R11-R12: Current
    set_cell_text(table.cell(11, 0), "Corriente", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(11, 2), "Máxima", size=sz, font_name=fn)
    set_cell_text(table.cell(11, 3), "(A)", size=sz, font_name=fn)
    set_cell_text(table.cell(11, 4), fmt(s_max("current_a")), size=sz, font_name=fn)
    set_cell_text(table.cell(11, 5), fmt(s_max("current_b")), size=sz, font_name=fn)
    set_cell_text(table.cell(11, 6), fmt(s_max("current_c")), size=sz, font_name=fn)
    set_cell_text(table.cell(12, 2), "Instantánea", size=sz, font_name=fn)
    set_cell_text(table.cell(12, 3), "(A)", size=sz, font_name=fn)
    set_cell_text(table.cell(12, 4), fmt(s_last("current_a")), size=sz, font_name=fn)
    set_cell_text(table.cell(12, 5), fmt(s_last("current_b")), size=sz, font_name=fn)
    set_cell_text(table.cell(12, 6), fmt(s_last("current_c")), size=sz, font_name=fn)

    # R13-R14: Active Power
    p_max = (s_max("active_power_total") or 0) / 1000
    p_last = (s_last("active_power_total") or 0) / 1000
    set_cell_text(table.cell(13, 0), "Potencia Activa", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(13, 2), "Máxima", size=sz, font_name=fn)
    set_cell_text(table.cell(13, 3), "(kW)", size=sz, font_name=fn)
    set_cell_text(table.cell(13, 4), fmt(p_max), size=sz, font_name=fn)
    set_cell_text(table.cell(14, 2), "Instantánea", size=sz, font_name=fn)
    set_cell_text(table.cell(14, 3), "(kW)", size=sz, font_name=fn)
    set_cell_text(table.cell(14, 4), fmt(p_last), size=sz, font_name=fn)

    # R15: Reactive Power Capacitive
    q_cap = (s("reactive_power_total", "mean") or 0) / 1000
    set_cell_text(table.cell(15, 0), "P. Reactiva Cap.", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(15, 2), "Promedio", size=sz, font_name=fn)
    set_cell_text(table.cell(15, 3), "(kVAr)", size=sz, font_name=fn)
    set_cell_text(table.cell(15, 4), fmt(abs(q_cap) if q_cap < 0 else 0), size=sz, font_name=fn)

    # R16: Reactive Power Inductive
    set_cell_text(table.cell(16, 0), "P. Reactiva Ind.", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(16, 2), "Promedio", size=sz, font_name=fn)
    set_cell_text(table.cell(16, 3), "(kVAr)", size=sz, font_name=fn)
    set_cell_text(table.cell(16, 4), fmt(q_cap if q_cap > 0 else 0), size=sz, font_name=fn)

    # R17: Apparent Power
    s_max_va = (s_max("apparent_power_total") or 0) / 1000
    set_cell_text(table.cell(17, 0), "P. Aparente", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(17, 2), "Máxima", size=sz, font_name=fn)
    set_cell_text(table.cell(17, 3), "(kVA)", size=sz, font_name=fn)
    set_cell_text(table.cell(17, 4), fmt(s_max_va), size=sz, font_name=fn)

    # R18: Power Factor
    fp_val = abs(s("power_factor_total", "mean") or 0)
    set_cell_text(table.cell(18, 0), "Factor de Potencia", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(18, 3), "cos(ϕ)", size=sz, font_name=fn)
    set_cell_text(table.cell(18, 4), fmt(fp_val), size=sz, font_name=fn)
    c = _valor_color(fp_val, 0.92, None)
    if c: set_cell_shading(table.cell(18, 7), c)
    set_cell_text(table.cell(18, 7), "≥ 0,92", bold=True, size=sz, font_name=fn)

    # R19: THD
    v_thd = s("thd_voltage_an", "mean") or 0
    set_cell_text(table.cell(19, 0), "Distorsión Armónica", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(19, 3), "% V THD", size=sz, font_name=fn)
    set_cell_text(table.cell(19, 4), fmt(v_thd), size=sz, font_name=fn)
    c = _valor_color(v_thd, None, 8.0)
    if c: set_cell_shading(table.cell(19, 7), c)
    set_cell_text(table.cell(19, 7), "< 8% THD", bold=True, size=sz, font_name=fn)

    # R20: Frequency
    freq = s("frequency", "mean") or 50.0
    set_cell_text(table.cell(20, 0), "Frecuencia", bold=True, size=sz, font_name=fn)
    set_cell_text(table.cell(20, 3), "(Hz)", size=sz, font_name=fn)
    set_cell_text(table.cell(20, 4), fmt(freq), size=sz, font_name=fn)
    c = _valor_color(freq, 49.0, 51.0)
    if c: set_cell_shading(table.cell(20, 7), c)
    set_cell_text(table.cell(20, 7), "= 50 ± 2%", bold=True, size=sz, font_name=fn)
