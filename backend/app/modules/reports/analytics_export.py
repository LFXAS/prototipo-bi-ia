from __future__ import annotations

from html import escape
from io import BytesIO
from typing import Literal

import xlsxwriter  # type: ignore[import-untyped]
from reportlab.graphics.shapes import (  # type: ignore[import-untyped]
    Circle,
    Drawing,
    Line,
    Path,
    String,
)
from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import A4, landscape  # type: ignore[import-untyped]
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore[import-untyped]
from reportlab.lib.units import mm  # type: ignore[import-untyped]
from reportlab.pdfgen.canvas import Canvas  # type: ignore[import-untyped]
from reportlab.platypus import (  # type: ignore[import-untyped]
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.doctemplate import BaseDocTemplate  # type: ignore[import-untyped]

from app.modules.analytics.schemas import (
    AnalyticsDashboardRead,
    AnalyticsVisualRead,
)

ReportView = Literal["executive", "analyst"]
_NAVY = colors.HexColor("#09254D")
_BLUE = colors.HexColor("#2166E8")
_TEAL = colors.HexColor("#078B75")
_MUTED = colors.HexColor("#5C718A")
_BORDER = colors.HexColor("#D8E2EF")
_LIGHT = colors.HexColor("#F3F7FC")


def _visible_visuals(
    dashboard: AnalyticsDashboardRead, view: ReportView
) -> list[AnalyticsVisualRead]:
    if view == "executive":
        return [item for item in dashboard.visuals if item.code != "customers"]
    return dashboard.visuals


def _format_value(value: float | None, unit: str) -> str:
    if value is None:
        return "Sin valor"
    if len(unit) == 3 and unit.isupper():
        return f"{value:,.2f} {unit}"
    if any(item in unit.casefold() for item in ("unidad", "pedido", "cliente", "fila")):
        return f"{value:,.0f} {unit}"
    return f"{value:,.2f} {unit}" if unit not in {"valor", "razón"} else f"{value:,.2f}"


def _line_drawing(visual: AnalyticsVisualRead, unit: str) -> Drawing:
    width, height = 720, 275
    drawing = Drawing(width, height)
    left, right, bottom, top = 38, 16, 28, 16
    plot_width = width - left - right
    plot_height = height - bottom - top
    for row in range(4):
        y = bottom + (plot_height * row / 3)
        drawing.add(Line(left, y, width - right, y, strokeColor=_BORDER, strokeWidth=0.6))
    if not visual.points:
        drawing.add(
            String(width / 2, height / 2, "Sin datos para la selección", textAnchor="middle")
        )
        return drawing
    values = [item.value for item in visual.points]
    maximum = max(max(values), 1)
    minimum = min(min(values), 0)
    spread = maximum - minimum or 1

    def point_x(index: int) -> float:
        return left + (index / max(len(visual.points) - 1, 1)) * plot_width

    def point_y(value: float) -> float:
        return bottom + ((value - minimum) / spread) * plot_height

    path = Path()
    for index, item in enumerate(visual.points):
        x, y = point_x(index), point_y(item.value)
        if index:
            path.lineTo(x, y)
        else:
            path.moveTo(x, y)
    path.strokeColor = _BLUE
    path.strokeWidth = 2
    path.fillColor = None
    drawing.add(path)
    peak_index = max(range(len(visual.points)), key=lambda index: visual.points[index].value)
    peak = visual.points[peak_index]
    drawing.add(
        Circle(
            point_x(peak_index), point_y(peak.value), 4, fillColor=_TEAL, strokeColor=colors.white
        )
    )
    drawing.add(
        String(
            point_x(peak_index),
            min(point_y(peak.value) + 10, height - 10),
            _format_value(peak.value, unit),
            fontSize=7,
            fillColor=_MUTED,
            textAnchor="middle",
        )
    )
    indexes = sorted({0, (len(visual.points) - 1) // 2, len(visual.points) - 1})
    for index in indexes:
        anchor = "start" if index == 0 else "end" if index == len(visual.points) - 1 else "middle"
        drawing.add(
            String(
                point_x(index),
                7,
                visual.points[index].label,
                fontSize=7,
                fillColor=_MUTED,
                textAnchor=anchor,
            )
        )
    return drawing


def _ranking_table(visual: AnalyticsVisualRead, unit: str) -> Table:
    data = [[visual.dimension, "Valor", "Participación"]]
    for item in visual.points:
        data.append(
            [
                Paragraph(
                    escape(item.label),
                    ParagraphStyle("RankingLabel", fontSize=8, leading=10),
                ),
                _format_value(item.value, unit),
                f"{item.share:.1f}%" if item.share is not None else "-",
            ]
        )
    table = Table(
        data,
        colWidths=[148 * mm, 58 * mm, 39 * mm],
        repeatRows=1,
        splitByRow=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), _NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.35, _BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def build_analytics_pdf(dashboard: AnalyticsDashboardRead, view: ReportView) -> bytes:
    output = BytesIO()
    page_width, _ = landscape(A4)
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=27,
        textColor=_NAVY,
        alignment=0,
        spaceAfter=7,
    )
    section = ParagraphStyle(
        "ReportSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=_NAVY,
        spaceBefore=8,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "ReportBody", parent=styles["BodyText"], fontSize=9, leading=13, textColor=_MUTED
    )
    small = ParagraphStyle("ReportSmall", parent=body, fontSize=7.5, leading=10, textColor=_MUTED)

    def footer(canvas: Canvas, document: BaseDocTemplate) -> None:
        canvas.saveState()
        canvas.setStrokeColor(_BORDER)
        canvas.line(14 * mm, 10 * mm, page_width - 14 * mm, 10 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(_MUTED)
        canvas.drawString(
            14 * mm, 6 * mm, f"Ejecución ETL #{dashboard.execution_id} - datos conciliados"
        )
        canvas.drawRightString(page_width - 14 * mm, 6 * mm, f"Página {document.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=13 * mm,
        bottomMargin=14 * mm,
        title="Resumen ejecutivo de ventas" if view == "executive" else dashboard.title,
        author="Prototipo BI asistido por IA",
    )
    story: list[object] = []
    report_title = "Resumen ejecutivo de ventas" if view == "executive" else dashboard.title
    story.append(Paragraph(report_title, title))
    story.append(Paragraph(escape(dashboard.description), body))
    context = [
        ["Período", dashboard.period_label, "Moneda", dashboard.currency_code],
        ["Propuesta", f"#{dashboard.proposal_id}", "Ejecución", f"#{dashboard.execution_id}"],
        [
            "Actualización",
            dashboard.refreshed_at.strftime("%d/%m/%Y %H:%M"),
            "Vista",
            "Ejecutiva" if view == "executive" else "Analítica",
        ],
    ]
    context_table = Table(context, colWidths=[25 * mm, 75 * mm, 25 * mm, 70 * mm])
    context_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _LIGHT),
                ("TEXTCOLOR", (0, 0), (-1, -1), _NAVY),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, _BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend([Spacer(1, 5 * mm), context_table, Spacer(1, 5 * mm)])
    story.append(Paragraph("Indicadores", section))
    kpi_cells = [
        Paragraph(
            f"<font size='7' color='#5C718A'>{escape(item.name.upper())}</font><br/>"
            "<font size='13' color='#09254D'><b>"
            f"{escape(_format_value(item.value, item.unit))}</b></font>",
            body,
        )
        for item in dashboard.kpis
    ]
    columns = 3
    kpi_rows = [kpi_cells[index : index + columns] for index in range(0, len(kpi_cells), columns)]
    if kpi_rows and len(kpi_rows[-1]) < columns:
        kpi_rows[-1].extend([""] * (columns - len(kpi_rows[-1])))
    kpi_table = Table(kpi_rows, colWidths=[page_width / columns - 13 * mm] * columns)
    kpi_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, _BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, _BORDER),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(kpi_table)
    visuals = _visible_visuals(dashboard, view)
    unit = next(
        (item.unit for item in dashboard.kpis if item.code == dashboard.metric_code), "valor"
    )
    trend = next((item for item in visuals if item.code == "trend"), None)
    if trend:
        story.extend(
            [
                PageBreak(),
                Paragraph("Tendencia del indicador", title),
                Paragraph(escape(trend.title), section),
                Paragraph(escape(trend.subtitle), small),
                Spacer(1, 3 * mm),
                _line_drawing(trend, unit),
                Spacer(1, 3 * mm),
                Paragraph(
                    "El gráfico representa exclusivamente el indicador y los filtros indicados "
                    "en la portada del reporte.",
                    small,
                ),
            ]
        )
    rankings = [item for item in visuals if item.code != "trend"]
    for visual in rankings:
        story.extend(
            [
                PageBreak(),
                Paragraph("Composición de los resultados", title),
                Paragraph(escape(visual.title), section),
                Paragraph(escape(visual.subtitle), small),
                Spacer(1, 3 * mm),
                _ranking_table(visual, unit),
            ]
        )
    if dashboard.insights:
        story.append(PageBreak())
        story.append(Paragraph("Hallazgos explicables", title))
        insight_data = [["Hallazgo", "Lectura", "Evidencia"]]
        for item in dashboard.insights:
            insight_data.append(
                [
                    Paragraph(escape(item.title), small),
                    Paragraph(escape(item.statement), small),
                    Paragraph(escape(item.evidence), small),
                ]
            )
        insights = Table(insight_data, colWidths=[43 * mm, 82 * mm, 70 * mm], repeatRows=1)
        insights.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _TEAL),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.4, _BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _LIGHT]),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(insights)
    if view == "analyst":
        if not dashboard.insights:
            story.append(PageBreak())
        story.extend(
            [
                Spacer(1, 4 * mm),
                Paragraph("Calidad y trazabilidad", section),
                Paragraph(
                    (
                        f"Filas de origen: {dashboard.quality.source_rows:,}. "
                        f"Filas cargadas: {dashboard.quality.datamart_rows:,}. "
                        f"Diferencia: {dashboard.quality.difference_rows:,}. "
                        f"Tablas cargadas: {dashboard.quality.tables_loaded}."
                    ),
                    body,
                ),
            ]
        )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()


def _excel_number_format(unit: str) -> str:
    currency = next(
        (token for token in unit.replace("/", " ").split() if len(token) == 3 and token.isupper()),
        None,
    )
    if currency is not None:
        return f'#,##0.00 "{currency}"'
    if any(item in unit.casefold() for item in ("unidad", "pedido", "cliente", "fila")):
        return "#,##0"
    if "porcentaje" in unit.casefold() or unit == "%":
        return "0.0%"
    return "#,##0.00"


def _write_visual_sheet(
    workbook: xlsxwriter.Workbook,
    visual: AnalyticsVisualRead,
    unit: str,
) -> str:
    safe_name = visual.title[:31]
    worksheet = workbook.add_worksheet(safe_name)
    title_format = workbook.add_format({"bold": True, "font_size": 18, "font_color": "#09254D"})
    subtitle_format = workbook.add_format({"font_color": "#5C718A"})
    header_format = workbook.add_format(
        {"bold": True, "font_color": "#FFFFFF", "bg_color": "#09254D", "border": 1}
    )
    number_format = workbook.add_format({"num_format": _excel_number_format(unit)})
    percent_format = workbook.add_format({"num_format": "0.0%"})
    worksheet.hide_gridlines(2)
    worksheet.set_tab_color("#2166E8")
    worksheet.set_column("A:A", 4)
    worksheet.set_column("B:B", 34)
    worksheet.set_column("C:C", 20)
    worksheet.set_column("D:D", 16)
    worksheet.set_column("E:E", 3)
    worksheet.set_column("F:M", 12)
    worksheet.set_row(1, 28)
    worksheet.set_row(2, 23)
    worksheet.merge_range("B2:H2", visual.title, title_format)
    worksheet.merge_range("B3:H3", visual.subtitle, subtitle_format)
    worksheet.write_row("B5", [visual.dimension, "Valor", "Participación"], header_format)
    for row, item in enumerate(visual.points, start=5):
        worksheet.write(row, 1, item.label)
        worksheet.write_number(row, 2, item.value, number_format)
        if item.share is not None:
            worksheet.write_number(row, 3, item.share / 100, percent_format)
    if visual.points:
        chart_type = (
            "line" if visual.kind == "line" else "doughnut" if visual.kind == "donut" else "column"
        )
        chart = workbook.add_chart({"type": chart_type})
        series_options: dict[str, object] = {
            "name": visual.title,
            "categories": [safe_name, 5, 1, 4 + len(visual.points), 1],
            "values": [safe_name, 5, 2, 4 + len(visual.points), 2],
            "line": {"color": "#2166E8", "width": 2.25},
            "fill": {"color": "#2166E8"},
            **(
                {"data_labels": {"percentage": True, "leader_lines": True}}
                if visual.kind == "donut"
                else {}
            ),
        }
        if visual.kind == "donut":
            palette = ("#2166E8", "#078B75", "#F59E0B", "#7C3AED", "#DB2777")
            series_options["points"] = [
                {"fill": {"color": palette[index % len(palette)]}}
                for index, _ in enumerate(visual.points)
            ]
        chart.add_series(series_options)
        chart.set_title({"name": visual.title})
        chart.set_legend({"none": True})
        chart.set_chartarea({"border": {"none": True}})
        chart.set_plotarea({"border": {"color": "#D8E2EF"}})
        if visual.kind != "donut":
            chart.set_x_axis({"label_position": "low", "num_font": {"size": 8}})
            chart.set_y_axis(
                {
                    "major_gridlines": {"visible": True, "line": {"color": "#E8EEF5"}},
                    "num_format": _excel_number_format(unit),
                }
            )
        chart.set_size({"width": 690, "height": 365})
        worksheet.insert_chart("F5", chart)
    worksheet.freeze_panes(5, 1)
    worksheet.autofilter(4, 1, 4 + len(visual.points), 3)
    worksheet.set_landscape()
    worksheet.fit_to_pages(1, 0)
    worksheet.set_paper(9)
    worksheet.set_margins(0.3, 0.3, 0.45, 0.45)
    worksheet.print_area(1, 1, max(28, 5 + len(visual.points)), 12)
    worksheet.repeat_rows(4, 4)
    worksheet.set_header("&L&8Reporte analítico de ventas&C&8Datos conciliados")
    worksheet.set_footer("&L&8Ejecución ETL&C&8&P de &N&R&8Generado por la plataforma")
    return safe_name


def build_analytics_xlsx(dashboard: AnalyticsDashboardRead, view: ReportView) -> bytes:
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    workbook.set_properties(
        {
            "title": "Resumen ejecutivo de ventas" if view == "executive" else dashboard.title,
            "subject": f"Ejecución ETL #{dashboard.execution_id}",
            "author": "Prototipo BI asistido por IA",
            "comments": "Reporte generado desde datos conciliados y filtros visibles.",
        }
    )
    summary = workbook.add_worksheet("Resumen")
    summary.hide_gridlines(2)
    summary.set_tab_color("#078B75")
    summary.set_column("A:A", 3)
    summary.set_column("B:B", 26)
    summary.set_column("C:C", 19)
    summary.set_column("D:D", 3)
    summary.set_column("E:E", 26)
    summary.set_column("F:F", 19)
    summary.set_column("G:G", 3)
    summary.set_column("H:H", 26)
    summary.set_column("I:I", 19)
    title_format = workbook.add_format(
        {"bold": True, "font_size": 23, "font_color": "#09254D", "valign": "vcenter"}
    )
    subtitle_format = workbook.add_format(
        {"font_size": 10, "font_color": "#5C718A", "text_wrap": True, "valign": "top"}
    )
    eyebrow_format = workbook.add_format({"bold": True, "font_size": 8, "font_color": "#078B75"})
    label_format = workbook.add_format(
        {"bold": True, "font_size": 8, "font_color": "#5C718A", "bg_color": "#F3F7FC"}
    )
    value_format = workbook.add_format(
        {"font_size": 10, "font_color": "#09254D", "bg_color": "#F3F7FC"}
    )
    card_label = workbook.add_format(
        {
            "bold": True,
            "font_size": 8,
            "font_color": "#5C718A",
            "bg_color": "#FFFFFF",
            "border": 1,
            "border_color": "#D8E2EF",
        }
    )
    section_format = workbook.add_format(
        {"bold": True, "font_size": 14, "font_color": "#09254D", "top": 1, "top_color": "#D8E2EF"}
    )
    summary.merge_range(
        "B2:I2",
        "RESUMEN EJECUTIVO" if view == "executive" else "ANÁLISIS DE VENTAS",
        eyebrow_format,
    )
    summary.merge_range(
        "B3:I4",
        "Resumen ejecutivo de ventas" if view == "executive" else dashboard.title,
        title_format,
    )
    summary.merge_range("B5:I6", dashboard.description, subtitle_format)
    context = [
        ("Período", dashboard.period_label),
        ("Moneda", dashboard.currency_code),
        ("Actualización", dashboard.refreshed_at.strftime("%d/%m/%Y %H:%M")),
        ("Propuesta", f"#{dashboard.proposal_id}"),
        ("Ejecución", f"#{dashboard.execution_id}"),
        ("Vista", "Ejecutiva" if view == "executive" else "Analítica"),
    ]
    for index, (label, value) in enumerate(context):
        row = 7 + index // 3
        column = 1 + (index % 3) * 3
        summary.write(row, column, label, label_format)
        summary.write(row, column + 1, value, value_format)
    summary.merge_range("B11:I11", "Indicadores con los filtros visibles", section_format)
    for index, metric in enumerate(dashboard.kpis):
        row = 12 + (index // 3) * 3
        column = 1 + (index % 3) * 3
        summary.merge_range(row, column, row, column + 1, metric.name, card_label)
        number_format = workbook.add_format(
            {
                "bold": True,
                "font_size": 14,
                "font_color": "#09254D",
                "bg_color": "#FFFFFF",
                "border": 1,
                "border_color": "#D8E2EF",
                "num_format": _excel_number_format(f"{metric.name} {metric.unit}"),
            }
        )
        if metric.value is None:
            summary.merge_range(row + 1, column, row + 1, column + 1, "Sin valor", number_format)
        else:
            summary.merge_range(row + 1, column, row + 1, column + 1, metric.value, number_format)
    insight_start = 12 + ((len(dashboard.kpis) + 2) // 3) * 3 + 1
    summary.merge_range(insight_start, 1, insight_start, 8, "Hallazgos explicables", section_format)
    insight_header = workbook.add_format(
        {"bold": True, "font_color": "#FFFFFF", "bg_color": "#078B75", "border": 1}
    )
    insight_text = workbook.add_format(
        {
            "font_size": 9,
            "font_color": "#294C6F",
            "text_wrap": True,
            "valign": "top",
            "border": 1,
            "border_color": "#D8E2EF",
        }
    )
    summary.write_row(insight_start + 1, 1, ["Hallazgo", "Lectura", "Evidencia"], insight_header)
    summary.set_column("B:B", 28)
    summary.set_column("C:C", 48)
    summary.set_column("D:D", 48)
    for index, insight in enumerate(dashboard.insights, start=insight_start + 2):
        summary.write(index, 1, insight.title, insight_text)
        summary.write(index, 2, insight.statement, insight_text)
        summary.write(index, 3, insight.evidence, insight_text)
        summary.set_row(index, 34)
    summary.freeze_panes(10, 1)
    summary.set_landscape()
    summary.fit_to_pages(1, 0)
    summary.set_paper(9)
    summary.set_margins(0.35, 0.35, 0.5, 0.5)
    summary.print_area(1, 1, max(insight_start + len(dashboard.insights) + 3, 26), 8)
    summary.set_header("&L&8Resumen de ventas&C&8Datos conciliados")
    summary.set_footer(
        f"&L&8Ejecución #{dashboard.execution_id}&C&8&P de &N&R&8{dashboard.currency_code}"
    )

    unit = next(
        (item.unit for item in dashboard.kpis if item.code == dashboard.metric_code), "valor"
    )
    for visual in _visible_visuals(dashboard, view):
        _write_visual_sheet(workbook, visual, unit)
    if view == "analyst":
        trace = workbook.add_worksheet("Trazabilidad")
        trace.hide_gridlines(2)
        trace.set_tab_color("#718096")
        trace.set_column("A:A", 3)
        trace.set_column("B:B", 28)
        trace.set_column("C:C", 72)
        trace.merge_range("B2:C2", "Calidad y trazabilidad", title_format)
        trace.write_row("B4", ["Control", "Resultado"], insight_header)
        trace_rows: list[tuple[str, str | int]] = [
            ("Ejecución ETL", f"#{dashboard.execution_id}"),
            ("Propuesta BI", f"#{dashboard.proposal_id}"),
            ("Filas de origen", dashboard.quality.source_rows),
            ("Filas cargadas", dashboard.quality.datamart_rows),
            ("Diferencia", dashboard.quality.difference_rows),
            ("Tablas cargadas", dashboard.quality.tables_loaded),
            ("Conciliación", "Aprobada" if dashboard.quality.reconciliation_passed else "Revisar"),
            ("Granularidad", dashboard.grain),
        ]
        for row, (label, trace_value) in enumerate(trace_rows, start=4):
            trace.write(row, 1, label, label_format)
            if isinstance(trace_value, int):
                trace.write_number(row, 2, trace_value, value_format)
            else:
                trace.write(row, 2, trace_value, value_format)
        trace.set_landscape()
        trace.fit_to_pages(1, 1)
        trace.set_paper(9)
        trace.set_margins(0.35, 0.35, 0.5, 0.5)
        trace.print_area(1, 1, 13, 2)
        trace.set_header("&L&8Trazabilidad&C&8Datos conciliados")
        trace.set_footer(f"&L&8Ejecución #{dashboard.execution_id}&R&8&P de &N")
    workbook.close()
    return output.getvalue()
