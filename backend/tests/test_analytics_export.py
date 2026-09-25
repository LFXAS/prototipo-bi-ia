from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from zipfile import ZipFile

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
    build_analytics_pdf,
    build_analytics_xlsx,
)


def _dashboard() -> AnalyticsDashboardRead:
    return AnalyticsDashboardRead(
        execution_id=7,
        proposal_id=53,
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
    assert _excel_number_format("Ventas netas USD") == '#,##0.00 "USD"'
    assert _excel_number_format("Número de pedidos pedidos") == "#,##0"
    assert _excel_number_format("Clientes con compras clientes") == "#,##0"


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
