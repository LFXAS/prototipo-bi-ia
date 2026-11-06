from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from io import BytesIO
from xml.etree import ElementTree
from zipfile import ZipFile

import pytest
from reportlab import rl_config

from app.modules.analytics.schemas import (
    AnalyticsDashboardRead,
    AnalyticsFiltersRead,
    AnalyticsInsightRead,
    AnalyticsMetricRead,
    AnalyticsOptionRead,
    AnalyticsPointRead,
    AnalyticsQualityRead,
    AnalyticsVisualRead,
)
from app.modules.reports.analytics_export import (
    _excel_number_format,
    _excel_wrapped_height,
    _format_value,
    _ranking_table,
    _report_timestamp,
    build_analytics_pdf,
    build_analytics_xlsx,
)


def _dashboard() -> AnalyticsDashboardRead:
    return AnalyticsDashboardRead(
        execution_id=7,
        proposal_id=53,
        data_connection_id=1,
        source_name="AdventureWorks local",
        database_name="AdventureWorks2022",
        title="Panel ejecutivo de ventas",
        description="Resultados conciliados para decisiones comerciales.",
        grain="Una fila por detalle de venta",
        refreshed_at=datetime(2026, 9, 25, 1, 0, tzinfo=UTC),
        currency_code="USD",
        currency_status="verified",
        reconciliation_passed=True,
        period_label="2014 · Norteamérica",
        metric_code="ventas_netas",
        available_metrics=[AnalyticsOptionRead(value="ventas_netas", label="Ventas netas")],
        filters=AnalyticsFiltersRead(
            years=[AnalyticsOptionRead(value="2014", label="2014")],
            territories=[AnalyticsOptionRead(value="Norteamérica", label="Norteamérica")],
            selected_year=2014,
            selected_territory="Norteamérica",
        ),
        kpis=[
            AnalyticsMetricRead(
                code="ventas_netas",
                name="Ventas netas",
                value=125000.5,
                unit="USD",
                status="reconciled",
            )
        ],
        visuals=[
            AnalyticsVisualRead(
                code="trend",
                title="Evolución en el tiempo",
                subtitle="Ventas netas por mes",
                kind="line",
                dimension="Fecha",
                points=[AnalyticsPointRead(key="2014-01", label="Ene 2014", value=125000.5)],
            ),
            AnalyticsVisualRead(
                code="customers",
                title="Clientes principales",
                subtitle="Ventas netas; principales categorías",
                kind="bar",
                dimension="Cliente",
                points=[
                    AnalyticsPointRead(key="1", label="Comercial Andina", value=25000, share=20)
                ],
            ),
        ],
        insights=[
            AnalyticsInsightRead(
                code="peak",
                title="Período principal",
                statement="Enero concentra el mayor valor.",
                evidence="Valor conciliado: 125.000,50 USD.",
            )
        ],
        quality=AnalyticsQualityRead(
            source_rows=100,
            datamart_rows=100,
            difference_rows=0,
            reconciliation_passed=True,
            tables_loaded=5,
        ),
    )


def test_pdf_export_is_a_real_pdf() -> None:
    result = build_analytics_pdf(_dashboard(), "executive")

    assert result.startswith(b"%PDF")
    assert len(result) > 1_000


def test_pdf_ranking_wraps_generic_currency_without_invading_share_column() -> None:
    visual = AnalyticsVisualRead(
        code="territories",
        title="Distribución territorial",
        subtitle="Resultados por territorio",
        kind="donut",
        dimension="Territorio",
        points=[
            AnalyticsPointRead(
                key="Texas",
                label="Texas",
                value=12_328_671.15,
                share=19.6,
            )
        ],
    )

    table = _ranking_table(visual, "Moneda")

    assert table._cellvalues[1][1].getPlainText() == "12,328,671.15 Moneda"
    assert table._cellvalues[1][2].getPlainText() == "19.6%"


def test_excel_export_respects_executive_and_analyst_visibility() -> None:
    executive = build_analytics_xlsx(_dashboard(), "executive")
    analyst = build_analytics_xlsx(_dashboard(), "analyst")

    with ZipFile(BytesIO(executive)) as workbook:
        document = workbook.read("xl/workbook.xml").decode()
        assert "Resumen" in document
        assert "Evolución en el tiempo" in document
        assert "Clientes principales" not in document
        assert "Trazabilidad" not in document
    with ZipFile(BytesIO(analyst)) as workbook:
        document = workbook.read("xl/workbook.xml").decode()
        assert "Clientes principales" in document
        assert "Trazabilidad" in document


def test_excel_number_format_preserves_currency_and_integer_semantics() -> None:
    assert _excel_number_format("USD") == '#,##0.00 "USD"'
    assert _excel_number_format("pedidos") == "#,##0"
    assert _excel_number_format("clientes") == "#,##0"
    assert _excel_number_format("porcentaje") == '0.0"%"'


@pytest.mark.parametrize(
    ("unit", "expected"),
    [
        ("USD por unidad", "21.28 USD por unidad"),
        ("moneda de origen por unidad", "21.28 moneda de origen por unidad"),
        ("USD per unit", "21.28 USD per unit"),
        ("currency per unit", "21.28 currency per unit"),
        ("Unidades", "21.28 Unidades"),
        ("units", "21.28 units"),
        ("clientes por pedido", "21.28 clientes por pedido"),
        ("customers per order", "21.28 customers per order"),
        ("pedidos", "21 pedidos"),
        ("orders", "21 orders"),
        ("FACTURAS", "21 FACTURAS"),
        ("invoices", "21 invoices"),
        ("transacciones", "21 transacciones"),
        ("rows", "21 rows"),
        ("razón", "21.28"),
        ("ratio", "21.28"),
        ("unidad no clasificada", "21.28 unidad no clasificada"),
    ],
)
def test_pdf_value_precision_uses_the_complete_declared_unit(unit: str, expected: str) -> None:
    assert _format_value(21.28, unit) == expected


@pytest.mark.parametrize(
    ("unit", "expected"),
    [
        ("USD por unidad", '#,##0.00 "USD"'),
        ("USD per unit", '#,##0.00 "USD"'),
        ("moneda de origen por unidad", "#,##0.00"),
        ("currency per unit", "#,##0.00"),
        ("clientes por pedido", "#,##0.00"),
        ("customers per order", "#,##0.00"),
        ("Unidades", "#,##0.00"),
        ("units", "#,##0.00"),
        ("pedidos", "#,##0"),
        ("orders", "#,##0"),
        ("clientes", "#,##0"),
        ("invoices", "#,##0"),
        ("Transacción", "#,##0"),
        ("rows", "#,##0"),
        ("Ventas netas USD", "#,##0.00"),
        ("Clientes con compras clientes", "#,##0.00"),
        ("ratio", "#,##0.00"),
    ],
)
def test_excel_precision_uses_the_complete_declared_unit(unit: str, expected: str) -> None:
    assert _excel_number_format(unit) == expected


def test_generated_pdf_preserves_fractional_prices_and_quantities(monkeypatch) -> None:
    dashboard = _dashboard()
    dashboard.kpis = [
        AnalyticsMetricRead(
            code="price",
            name="Valor por unidad",
            value=21.28,
            unit="moneda de origen por unidad",
            status="reconciled",
        ),
        AnalyticsMetricRead(
            code="quantity_mean",
            name="Cantidad media",
            value=2.27,
            unit="Unidades",
            status="reconciled",
        ),
    ]
    # Keep the actual generated PDF text stream readable without a PDF-reader
    # dependency. Compression changes no values or layout.
    monkeypatch.setattr(rl_config, "pageCompression", 0)

    result = build_analytics_pdf(dashboard, "executive")

    assert result.startswith(b"%PDF")
    assert b"21.28" in result
    assert b"2.27" in result


def _cell_number_format(workbook: ZipFile, worksheet: str, reference: str) -> str:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    sheet = ElementTree.fromstring(workbook.read(worksheet))
    cell = sheet.find(f".//x:c[@r='{reference}']", ns)
    assert cell is not None
    styles = ElementTree.fromstring(workbook.read("xl/styles.xml"))
    cell_styles = styles.find("x:cellXfs", ns)
    assert cell_styles is not None
    number_id = int(cell_styles[int(cell.attrib["s"])].attrib["numFmtId"])
    formats = {
        int(item.attrib["numFmtId"]): item.attrib["formatCode"]
        for item in styles.findall("x:numFmts/x:numFmt", ns)
    }
    builtins = {3: "#,##0", 4: "#,##0.00"}
    return formats.get(number_id, builtins.get(number_id, "General"))


def test_generated_excel_uses_declared_unit_in_summary_and_visuals() -> None:
    dashboard = _dashboard()
    dashboard.kpis = [
        AnalyticsMetricRead(
            code="ventas_netas",
            name="Clientes y unidades por pedido",
            value=21.28,
            unit="moneda de origen por unidad",
            status="reconciled",
        ),
        AnalyticsMetricRead(
            code="count",
            name="Precio USD por cliente",
            value=321,
            unit="clientes",
            status="reconciled",
        ),
        AnalyticsMetricRead(
            code="quantity_mean",
            name="Cantidad media",
            value=2.27,
            unit="Unidades",
            status="reconciled",
        ),
    ]

    result = build_analytics_xlsx(dashboard, "executive")

    with ZipFile(BytesIO(result)) as workbook:
        assert _cell_number_format(workbook, "xl/worksheets/sheet1.xml", "B14") == "#,##0.00"
        assert _cell_number_format(workbook, "xl/worksheets/sheet1.xml", "E14") == "#,##0"
        assert _cell_number_format(workbook, "xl/worksheets/sheet1.xml", "H14") == "#,##0.00"
        assert _cell_number_format(workbook, "xl/worksheets/sheet2.xml", "C6") == "#,##0.00"


def _workbook_cells(workbook: ZipFile, worksheet: str) -> dict[str, str]:
    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    strings = [
        "".join(value.itertext())
        for value in ElementTree.fromstring(workbook.read("xl/sharedStrings.xml"))
    ]
    values: dict[str, str] = {}
    for cell in ElementTree.fromstring(workbook.read(worksheet)).findall(".//x:c", ns):
        value = cell.find("x:v", ns)
        if value is not None and value.text is not None:
            values[cell.attrib["r"]] = (
                strings[int(value.text)] if cell.get("t") == "s" else value.text
            )
    return values


@pytest.mark.parametrize(
    ("source_name", "database_name"),
    [("Fuente Alfa", "Catalogo_Alfa"), ("Fuente <b>Beta</b> & Filial", "Catalogo_Beta")],
)
def test_pdf_and_excel_identify_each_source_and_database(
    monkeypatch, source_name: str, database_name: str
) -> None:
    from app.modules.reports import analytics_export

    dashboard = _dashboard()
    dashboard.source_name = source_name
    dashboard.database_name = database_name
    monkeypatch.setattr(rl_config, "pageCompression", 0)
    paragraph_class = analytics_export.Paragraph
    rendered_context = []

    def capture_paragraph(*args, **kwargs):
        paragraph = paragraph_class(*args, **kwargs)
        if len(args) > 1 and args[1].name == "ReportContextValue":
            rendered_context.append(paragraph.getPlainText())
        return paragraph

    monkeypatch.setattr(analytics_export, "Paragraph", capture_paragraph)

    pdf = build_analytics_pdf(dashboard, "executive")
    xlsx = build_analytics_xlsx(dashboard, "executive")

    assert pdf.startswith(b"%PDF")
    assert source_name in rendered_context
    assert database_name in rendered_context
    assert database_name.encode() in pdf
    with ZipFile(BytesIO(xlsx)) as workbook:
        values = _workbook_cells(workbook, "xl/worksheets/sheet1.xml")
        assert values["B10"] == "Fuente"
        assert values["C10"] == source_name
        assert values["E10"] == "Base de datos"
        assert values["F10"] == database_name
        assert values["C9"] == "#53"
        assert values["F9"] == "#7"


def test_pdf_wraps_long_context_values_without_interpreting_markup(monkeypatch) -> None:
    from app.modules.reports import analytics_export

    dashboard = _dashboard()
    dashboard.source_name = "Fuente <b>literal</b> & " + "W" * 95
    dashboard.database_name = "Data" + "W" * 124
    tables = []
    original_context_values = []
    table_class = analytics_export.Table

    def capture_table(*args, **kwargs):
        table = table_class(*args, **kwargs)
        if table._cellvalues and table._cellvalues[0][0] == "Fuente":
            original_context_values.append(
                (
                    table._cellvalues[0][1].getPlainText(),
                    table._cellvalues[0][3].getPlainText(),
                )
            )
            tables.append(table)
        return table

    monkeypatch.setattr(analytics_export, "Table", capture_table)

    pdf = build_analytics_pdf(dashboard, "executive")

    assert pdf.startswith(b"%PDF")
    assert len(tables) == 1
    assert original_context_values == [(dashboard.source_name, dashboard.database_name)]
    assert tables[0]._rowHeights[0] > tables[0]._rowHeights[1]
    with ZipFile(BytesIO(build_analytics_xlsx(dashboard, "executive"))) as workbook:
        values = _workbook_cells(workbook, "xl/worksheets/sheet1.xml")
        assert values["C10"] == dashboard.source_name
        assert values["F10"] == dashboard.database_name
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheet = ElementTree.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        merged = {cell.attrib["ref"] for cell in sheet.findall("x:mergeCells/x:mergeCell", ns)}
        assert {"C10:D10", "F10:I10"} <= merged


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        (datetime(2026, 11, 5, 4, 24, tzinfo=UTC), "2026-11-05 04:24+00:00"),
        (
            datetime(2026, 11, 4, 23, 24, tzinfo=timezone(timedelta(hours=-5))),
            "2026-11-04 23:24-05:00",
        ),
        (datetime(2026, 11, 5, 4, 24), "2026-11-05 04:24 (zona no informada)"),
    ],
)
def test_report_timestamp_preserves_aware_offset_and_discloses_naive_zone(
    monkeypatch, timestamp: datetime, expected: str
) -> None:
    dashboard = _dashboard()
    dashboard.refreshed_at = timestamp
    monkeypatch.setattr(rl_config, "pageCompression", 0)

    assert _report_timestamp(timestamp) == expected
    pdf = build_analytics_pdf(dashboard, "executive")
    assert expected.split()[0].encode() in pdf
    assert expected.split()[1].encode() in pdf
    with ZipFile(BytesIO(build_analytics_xlsx(dashboard, "executive"))) as workbook:
        assert _workbook_cells(workbook, "xl/worksheets/sheet1.xml")["I8"] == expected


@pytest.mark.parametrize("literal", ["=1+1", "https://example.test/source"])
def test_excel_context_and_visual_labels_remain_literal_text(literal: str) -> None:
    dashboard = _dashboard()
    dashboard.source_name = literal
    dashboard.database_name = literal
    dashboard.kpis[0].name = literal
    dashboard.visuals[0].subtitle = literal
    dashboard.visuals[0].points[0].label = literal

    result = build_analytics_xlsx(dashboard, "executive")

    with ZipFile(BytesIO(result)) as workbook:
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        for worksheet, references in (
            ("xl/worksheets/sheet1.xml", ["C10", "F10", "B13"]),
            ("xl/worksheets/sheet2.xml", ["B3", "B6"]),
        ):
            values = _workbook_cells(workbook, worksheet)
            xml = ElementTree.fromstring(workbook.read(worksheet))
            for reference in references:
                cell = xml.find(f".//x:c[@r='{reference}']", ns)
                assert cell is not None
                assert cell.get("t") == "s"
                assert cell.find("x:f", ns) is None
                assert values[reference] == literal
        for name in workbook.namelist():
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml"):
                xml = ElementTree.fromstring(workbook.read(name))
                assert not xml.findall(".//x:f", ns)
                assert not xml.findall(".//x:hyperlink", ns)


@pytest.mark.parametrize(
    "sentence",
    [
        "Los atributos describen el estado disponible durante la extracción y no prueban "
        "su vigencia en una fecha anterior ni la realización de una entrega. ",
        "Attributes describe the source state available during extraction and do not establish "
        "their historical validity or verify that a delivery actually occurred. ",
    ],
)
def test_excel_fits_long_insights_and_maximum_source_context_without_truncating(sentence) -> None:
    dashboard = _dashboard()
    dashboard.source_name = "W" * 120
    dashboard.database_name = "W" * 128
    dashboard.kpis[0].unit = "USD por unidad"
    dashboard.kpis[0].value = 21.28
    final_sentence = "La fecha del hecho no demuestra esas condiciones."
    statement = sentence * 4 + "\n" + final_sentence
    evidence = "Fuente y base de datos verificadas. " + "Identificador_" * 30
    dashboard.insights = [
        AnalyticsInsightRead(
            code="generic_limit",
            title="Límite de interpretación de los atributos descriptivos",
            statement=statement,
            evidence=evidence,
        )
    ]

    with ZipFile(BytesIO(build_analytics_xlsx(dashboard, "executive"))) as workbook:
        values = _workbook_cells(workbook, "xl/worksheets/sheet1.xml")
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        sheet = ElementTree.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        assert values["C19"] == statement
        assert values["C19"].endswith(final_sentence)
        assert values["D19"] == evidence
        assert float(sheet.find(".//x:row[@r='19']", ns).get("ht")) >= 100
        assert values["C10"] == "W" * 120
        assert values["F10"] == "W" * 128
        assert float(sheet.find(".//x:row[@r='10']", ns).get("ht")) >= 48
        assert values["B14"] == "21.28"
        assert _cell_number_format(workbook, "xl/worksheets/sheet1.xml", "B14") == '#,##0.00 "USD"'


def test_excel_wrapped_height_uses_glyph_width_and_explicit_lines() -> None:
    assert _excel_wrapped_height("W" * 100, 200, 9) > _excel_wrapped_height("i" * 100, 200, 9)
    assert _excel_wrapped_height("Texto\n\nfinal", 400, 9) >= 43
    assert _excel_wrapped_height("Identificador" * 50, 200, 9) > _excel_wrapped_height(
        "Identificador" * 50, 400, 9
    )


def test_excel_sheets_fit_their_printed_width() -> None:
    content = build_analytics_xlsx(_dashboard(), "analyst")

    with ZipFile(BytesIO(content)) as workbook:
        worksheets = [
            name
            for name in workbook.namelist()
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        ]
        assert worksheets
        for worksheet in worksheets:
            document = workbook.read(worksheet).decode()
            assert "fitToPage" in document
            assert 'orientation="landscape"' in document
        workbook_document = workbook.read("xl/workbook.xml").decode()
        assert workbook_document.count("_xlnm.Print_Area") == len(worksheets)
