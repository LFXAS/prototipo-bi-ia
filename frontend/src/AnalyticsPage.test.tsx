import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { AnalyticsPage } from './AnalyticsPage'
import { api, type AnalyticsDashboard } from './api/security'

const dashboard: AnalyticsDashboard = {
  execution_id: 9,
  proposal_id: 73,
  title: 'Análisis de ventas',
  description: 'Resultados conciliados del datamart.',
  grain: 'Una fila por detalle de venta.',
  refreshed_at: '2026-09-25T22:36:00Z',
  currency_code: 'USD',
  currency_status: 'verified',
  reconciliation_passed: true,
  period_label: 'Todos los períodos',
  metric_code: 'total_units',
  available_metrics: [{ value: 'total_units', label: 'Total unidades vendidas' }],
  filters: { years: [], territories: [{ value: 'Europe', label: 'Europa' }] },
  kpis: [
    { code: 'total_units', name: 'Total unidades vendidas', value: 274_914, unit: 'unidades', status: 'reconciled' },
    { code: 'gross_sales', name: 'Ventas brutas totales', value: 110_373_889.31, unit: 'USD', status: 'reconciled' },
    { code: 'cost_per_unit', name: 'Costo promedio por unidad vendida', value: 365.48, unit: 'USD por unidad', status: 'reconciled' },
    { code: 'sale_per_unit', name: 'Venta promedio por unidad vendida', value: 401.48, unit: 'USD por unidad', status: 'reconciled' },
  ],
  visuals: [
    {
      code: 'products', title: 'Productos líderes', subtitle: 'Total unidades vendidas; principales 1 categoría',
      kind: 'bar', dimension: 'Producto', points: [{ key: '1', label: 'Mountain-200', value: 8_250, share: 100 }],
    },
    {
      code: 'territories', title: 'Distribución territorial', subtitle: 'Total unidades vendidas; principales 1 categoría',
      kind: 'donut', dimension: 'Territorio', points: [{ key: '1', label: 'Europa', value: 53_148, share: 100 }],
    },
  ],
  insights: [],
  quality: { source_rows: 121_317, datamart_rows: 121_317, difference_rows: 0, reconciliation_passed: true, tables_loaded: 5 },
  guidance: ['Los resultados provienen del expediente conciliado.'],
}

describe('AnalyticsPage', () => {
  function mockExecutionCatalog() {
    vi.spyOn(api, 'analyticsExecutions').mockResolvedValue([
      {
        execution_id: 9,
        proposal_id: 73,
        label: 'Ejecución #9 · propuesta #73 · cobertura completa',
        provider_kind: 'groq-cloud',
        model_id: 'openai/gpt-oss-120b',
        finished_at: '2026-09-25T22:36:00Z',
        coverage_status: 'complete',
        calculable_kpis: 4,
        total_kpis: 4,
      },
    ])
  }

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('presenta promedios por unidad, conserva el valor exacto y contrasta la pregunta del usuario', async () => {
    mockExecutionCatalog()
    vi.spyOn(api, 'analyticsDashboard').mockResolvedValue(dashboard)
    vi.spyOn(api, 'askAnalyticsCopilot').mockResolvedValue({
      answer: 'El resultado se calculó con los agregados conciliados.',
      evidence: ['Expediente #9 conciliado.'],
      suggested_questions: [],
      caveat: 'No implica causalidad.',
      provider_kind: 'groq-cloud',
      model_id: 'openai/gpt-oss-120b',
    })

    render(<AnalyticsPage token="test-token" canExport={false} navigate={vi.fn()} />)

    expect(await screen.findByText('Costo promedio por unidad vendida')).toBeInTheDocument()
    expect(screen.getByText('Venta promedio por unidad vendida')).toBeInTheDocument()
    expect(screen.getAllByText('promedio por unidad vendida')).toHaveLength(2)
    expect(screen.getByTitle(/Valor exacto: USD.*110\.373\.889,31/)).toBeInTheDocument()
    expect(screen.getByTitle(/Valor exacto: USD.*365,48 por unidad/)).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Escriba su pregunta'), { target: { value: 'Resume las unidades vendidas.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Preguntar al copiloto' }))

    const question = await screen.findByText('Resume las unidades vendidas.')
    expect(question.closest('article')).toHaveClass('user')
    await waitFor(() => expect(api.askAnalyticsCopilot).toHaveBeenCalledOnce())
  })

  it('permite explorar una barra y convertir una categoría territorial en filtro', async () => {
    mockExecutionCatalog()
    vi.spyOn(api, 'analyticsDashboard').mockResolvedValue(dashboard)

    render(<AnalyticsPage token="test-token" canExport={false} navigate={vi.fn()} />)

    fireEvent.click(await screen.findByRole('button', { name: /Mountain-200/i }))
    expect(screen.getByText('Detalle seleccionado')).toBeInTheDocument()
    expect(screen.getByText('8.250 unidades')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar detalle' }))
    expect(screen.queryByText('Detalle seleccionado')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /^Europa/i }))
    fireEvent.click(screen.getByRole('button', { name: 'Filtrar tablero por Europa' }))

    await waitFor(() => expect(api.analyticsDashboard).toHaveBeenLastCalledWith(
      'test-token',
      expect.objectContaining({ territory: 'Europe' }),
    ))
  })

  it('distingue un KPI no calculable y conserva la ejecución seleccionada', async () => {
    mockExecutionCatalog()
    vi.spyOn(api, 'analyticsDashboard').mockResolvedValue({
      ...dashboard,
      kpis: [
        ...dashboard.kpis,
        { code: 'average_sale', name: 'Venta promedio', unit: 'USD', status: 'not_calculable' },
      ],
    })

    render(<AnalyticsPage token="test-token" canExport={false} navigate={vi.fn()} />)

    expect(await screen.findByText('Venta promedio')).toBeInTheDocument()
    expect(screen.getByText('No calculable con esta ejecución')).toBeInTheDocument()
    expect(screen.getByLabelText('Datamart analizado')).toHaveValue('9')
    expect(api.analyticsDashboard).toHaveBeenCalledWith(
      'test-token',
      expect.objectContaining({ executionId: 9 }),
    )
  })

  it('cambia de ejecución sin materializar y reinicia el contexto de filtros', async () => {
    vi.spyOn(api, 'analyticsExecutions').mockResolvedValue([
      {
        execution_id: 10, proposal_id: 76,
        label: 'Ejecución #10 · propuesta #76 · cobertura parcial',
        provider_kind: 'anthropic-claude', model_id: 'claude-haiku-4-5-20251001',
        finished_at: '2026-09-26T22:02:00Z', coverage_status: 'partial',
        calculable_kpis: 8, total_kpis: 9,
      },
      {
        execution_id: 9, proposal_id: 73,
        label: 'Ejecución #9 · propuesta #73 · cobertura completa',
        provider_kind: 'groq-cloud', model_id: 'openai/gpt-oss-120b',
        finished_at: '2026-09-25T22:36:00Z', coverage_status: 'complete',
        calculable_kpis: 9, total_kpis: 9,
      },
    ])
    vi.spyOn(api, 'analyticsDashboard').mockImplementation(async (_token, filters = {}) => ({
      ...dashboard,
      execution_id: filters.executionId ?? 10,
    }))

    render(<AnalyticsPage token="test-token" canExport={false} navigate={vi.fn()} />)
    const selector = await screen.findByLabelText('Datamart analizado')
    expect(selector).toHaveValue('10')

    fireEvent.change(selector, { target: { value: '9' } })

    await waitFor(() => expect(api.analyticsDashboard).toHaveBeenLastCalledWith(
      'test-token',
      expect.objectContaining({ executionId: 9, year: '', territory: '' }),
    ))
  })
})
