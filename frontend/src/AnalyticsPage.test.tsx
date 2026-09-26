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
  filters: { years: [], territories: [] },
  kpis: [
    { code: 'gross_sales', name: 'Ventas brutas totales', value: 110_373_889.31, unit: 'USD', status: 'reconciled' },
    { code: 'cost_per_unit', name: 'Costo promedio por unidad vendida', value: 365.48, unit: 'USD por unidad', status: 'reconciled' },
    { code: 'sale_per_unit', name: 'Venta promedio por unidad vendida', value: 401.48, unit: 'USD por unidad', status: 'reconciled' },
  ],
  visuals: [],
  insights: [],
  quality: { source_rows: 121_317, datamart_rows: 121_317, difference_rows: 0, reconciliation_passed: true, tables_loaded: 5 },
  guidance: ['Los resultados provienen del expediente conciliado.'],
}

describe('AnalyticsPage', () => {
  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('presenta promedios por unidad, conserva el valor exacto y contrasta la pregunta del usuario', async () => {
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
})
