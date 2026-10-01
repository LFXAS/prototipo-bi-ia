import { useEffect, useMemo, useState, type KeyboardEvent } from 'react'

import {
  api,
  type AnalyticsCopilotAnswer,
  type AnalyticsDashboard,
  type AnalyticsExecutionOption,
  type AnalyticsPoint,
  type AnalyticsVisual,
} from './api/security'
import './analytics.css'

type Props = { token: string; connectionId: number; canExport: boolean; navigate: (path: string) => void }

function formatValue(value: number | undefined, unit: string, compact = false) {
  if (value === undefined || !Number.isFinite(value)) return 'Sin valor'
  const currency = unit.match(/^([A-Z]{3})(?: por unidad)?$/)
  const options: Intl.NumberFormatOptions = compact
    ? { notation: 'compact', maximumFractionDigits: 1 }
    : { maximumFractionDigits: currency ? 2 : /unidad|pedido|cliente|fila/i.test(unit) ? 0 : 2 }
  if (currency) {
    const formatted = new Intl.NumberFormat('es-EC', {
      ...options,
      style: 'currency',
      currency: currency[1],
      currencyDisplay: 'code',
    }).format(value)
    return unit.endsWith('por unidad') ? `${formatted} por unidad` : formatted
  }
  const formatted = new Intl.NumberFormat('es-EC', options).format(value)
  return /^(valor|razón)$/i.test(unit) ? formatted : `${formatted} ${unit}`
}

function metricCardPresentation(value: number | undefined, unit: string) {
  if (value === undefined || !Number.isFinite(value)) return { value: 'Sin valor', unit: '', exact: 'Sin valor' }
  const compact = Math.abs(value) >= 100_000
  const currency = unit.match(/^([A-Z]{3})(?: por unidad)?$/)
  if (currency) {
    const formatted = new Intl.NumberFormat('es-EC', {
      style: 'currency',
      currency: currency[1],
      currencyDisplay: 'code',
      notation: compact ? 'compact' : 'standard',
      minimumFractionDigits: compact ? 0 : 2,
      maximumFractionDigits: compact ? 1 : 2,
    }).format(value)
    return { value: formatted, unit: unit.endsWith('por unidad') ? 'promedio por unidad vendida' : '', exact: formatValue(value, unit) }
  }
  if (/porcentaje/i.test(unit)) {
    return { value: `${new Intl.NumberFormat('es-EC', { maximumFractionDigits: 2 }).format(value)}%`, unit: '', exact: formatValue(value, unit) }
  }
  return {
    value: new Intl.NumberFormat('es-EC', { notation: compact ? 'compact' : 'standard', maximumFractionDigits: compact ? 1 : 2 }).format(value),
    unit,
    exact: formatValue(value, unit),
  }
}

type InteractiveVisualProps = {
  visual: AnalyticsVisual
  unit: string
  showData: boolean
  selectedKey: string | null
  onSelect: (point: AnalyticsPoint) => void
}

function activatePoint(event: KeyboardEvent, point: AnalyticsPoint, onSelect: (point: AnalyticsPoint) => void) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    onSelect(point)
  }
}

function LineVisual({ visual, unit, showData, selectedKey, onSelect }: InteractiveVisualProps) {
  const width = 840
  const height = 270
  const padding = { left: 24, right: 24, top: 22, bottom: 38 }
  const values = visual.points.map((point) => point.value)
  const maximum = Math.max(...values, 1)
  const minimum = Math.min(...values, 0)
  const spread = maximum - minimum || 1
  const x = (index: number) => padding.left + (index / Math.max(visual.points.length - 1, 1)) * (width - padding.left - padding.right)
  const y = (value: number) => padding.top + ((maximum - value) / spread) * (height - padding.top - padding.bottom)
  const path = visual.points.map((point, index) => `${index ? 'L' : 'M'} ${x(index)} ${y(point.value)}`).join(' ')
  const area = visual.points.length ? `${path} L ${x(visual.points.length - 1)} ${height - padding.bottom} L ${padding.left} ${height - padding.bottom} Z` : ''
  const labelIndexes = [...new Set([0, Math.floor((visual.points.length - 1) / 2), visual.points.length - 1])].filter((item) => item >= 0)
  return (
    <>
      <div className="analytics-line-chart" role="group" aria-label={`${visual.title}. Seleccione uno de ${visual.points.length} períodos para consultar el detalle.`}>
        {visual.points.length
          ? <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
              <defs>
                <linearGradient id="analytics-area" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#2870e8" stopOpacity=".3" />
                  <stop offset="100%" stopColor="#2870e8" stopOpacity=".02" />
                </linearGradient>
              </defs>
              {[0, 1, 2, 3].map((row) => <line className="chart-grid" key={row} x1={padding.left} x2={width - padding.right} y1={padding.top + row * 62} y2={padding.top + row * 62} />)}
              <path className="chart-area" d={area} />
              <path className="chart-line" d={path} />
              {visual.points.map((point, index) => <g key={point.key} className={selectedKey === point.key ? 'interactive-chart-point selected' : 'interactive-chart-point'} role="button" tabIndex={0} aria-label={`${point.label}: ${formatValue(point.value, unit)}`} onClick={() => onSelect(point)} onKeyDown={(event) => activatePoint(event, point, onSelect)}><circle className="chart-hit" cx={x(index)} cy={y(point.value)} r="12" /><circle className="chart-point" cx={x(index)} cy={y(point.value)} r="4"><title>{`${point.label}: ${formatValue(point.value, unit)}`}</title></circle></g>)}
              {labelIndexes.map((index) => <text key={visual.points[index].key} x={x(index)} y={height - 10} textAnchor={index === 0 ? 'start' : index === visual.points.length - 1 ? 'end' : 'middle'}>{visual.points[index].label}</text>)}
            </svg>
          : <p className="analytics-empty">No hay períodos para la selección actual.</p>}
      </div>
      {showData && <AccessibleData visual={visual} unit={unit} />}
    </>
  )
}

function BarVisual({ visual, unit, showData, selectedKey, onSelect }: InteractiveVisualProps) {
  const maximum = Math.max(...visual.points.map((point) => point.value), 1)
  return (
    <>
      <div className="analytics-bars" role="group" aria-label={`${visual.title}. Seleccione una de ${visual.points.length} barras para consultar el detalle.`}>
        {visual.points.map((point, index) => <button type="button" className={selectedKey === point.key ? 'analytics-bar-row selected' : 'analytics-bar-row'} key={point.key} aria-pressed={selectedKey === point.key} onClick={() => onSelect(point)}>
          <span className="bar-rank">{String(index + 1).padStart(2, '0')}</span>
          <div><div className="bar-label"><strong title={point.label}>{point.label}</strong><span>{formatValue(point.value, unit, true)}</span></div><div className="bar-track"><span style={{ width: `${Math.max((point.value / maximum) * 100, 2)}%` }} /></div></div>
        </button>)}
      </div>
      {showData && <AccessibleData visual={visual} unit={unit} />}
    </>
  )
}

function DonutVisual({ visual, unit, showData, selectedKey, onSelect }: InteractiveVisualProps) {
  const colors = ['#2166e8', '#14a37f', '#f5a524', '#7b61d1', '#e55353', '#38a3db', '#718096', '#bd5ca8']
  const total = visual.points.reduce((sum, point) => sum + point.value, 0)
  let cursor = 0
  const stops = visual.points.map((point, index) => {
    const start = cursor
    cursor += total ? (point.value / total) * 100 : 0
    return `${colors[index % colors.length]} ${start}% ${cursor}%`
  }).join(', ')
  return (
    <>
      <div className="analytics-donut-layout">
        <div className="analytics-donut" style={{ background: `conic-gradient(${stops || '#dfe6ef 0 100%'})` }} role="img" aria-label={`${visual.title}. Distribución de ${formatValue(total, unit)}.`}><div><strong>{formatValue(total, unit, true)}</strong><span>Total filtrado</span></div></div>
        <ul className="analytics-legend">{visual.points.map((point, index) => <li key={point.key}><button type="button" className={selectedKey === point.key ? 'selected' : ''} aria-pressed={selectedKey === point.key} onClick={() => onSelect(point)}><span style={{ background: colors[index % colors.length] }} /><div><strong>{point.label}</strong><small>{(point.share ?? 0).toFixed(1)}% · {formatValue(point.value, unit, true)}</small></div></button></li>)}</ul>
      </div>
      {showData && <AccessibleData visual={visual} unit={unit} />}
    </>
  )
}

function AccessibleData({ visual, unit }: { visual: AnalyticsVisual; unit: string }) {
  return <details className="analytics-data-table"><summary>Consultar los datos de este gráfico</summary><div className="table-wrap"><table><thead><tr><th>{visual.dimension}</th><th>Valor</th></tr></thead><tbody>{visual.points.map((point) => <tr key={point.key}><td>{point.label}</td><td>{formatValue(point.value, unit)}</td></tr>)}</tbody></table></div></details>
}

function VisualCard({ visual, unit, showData, territoryOptions, onTerritoryFilter }: { visual: AnalyticsVisual; unit: string; showData: boolean; territoryOptions?: Array<{ value: string; label: string }>; onTerritoryFilter?: (value: string) => void }) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null)
  const selected = visual.points.find((point) => point.key === selectedKey)
  const total = visual.points.reduce((sum, point) => sum + point.value, 0)
  const props: InteractiveVisualProps = { visual, unit, showData, selectedKey, onSelect: (point) => setSelectedKey(point.key) }
  const territoryFilter = selected ? territoryOptions?.find((option) => option.label === selected.label)?.value : undefined
  return <article className={`analytics-visual visual-${visual.code}`}><header><div><p>{visual.dimension}</p><h2>{visual.title}</h2><span>{visual.subtitle}</span></div><button className="icon-button" aria-label={`Más información sobre ${visual.title}`} title="Seleccione un dato para ver su valor exacto y contexto">ⓘ</button></header><p className="analytics-interaction-hint">Seleccione un punto, barra o categoría para consultar su detalle.</p>{visual.kind === 'line' ? <LineVisual {...props} /> : visual.kind === 'donut' ? <DonutVisual {...props} /> : <BarVisual {...props} />}{selected && <section className="analytics-point-detail" aria-live="polite"><div><small>Detalle seleccionado</small><strong>{selected.label}</strong></div><dl><div><dt>Valor</dt><dd>{formatValue(selected.value, unit)}</dd></div><div><dt>Participación visible</dt><dd>{(selected.share ?? (total ? selected.value / total * 100 : 0)).toFixed(1)}%</dd></div></dl><div>{visual.code === 'territories' && territoryFilter && onTerritoryFilter && <button type="button" onClick={() => onTerritoryFilter(territoryFilter)}>Filtrar tablero por {selected.label}</button>}<button type="button" className="secondary" onClick={() => setSelectedKey(null)}>Cerrar detalle</button></div></section>}</article>
}

function InterpretedQueryCard({ answer }: { answer: AnalyticsCopilotAnswer }) {
  const query = answer.interpreted_query
  if (!query) return null
  const filters = [query.year ? `Año ${query.year}` : 'Todos los años', query.territory ?? 'Todos los territorios']
  return <section className="chat-query-evidence" aria-label="Consulta analítica interpretada">
    <header><div><small>Consulta interpretada</small><strong>{query.metric_name} por {query.dimension_label.toLowerCase()}</strong></div><span>Top {query.top_n}</span></header>
    <dl><div><dt>Alcance</dt><dd>{filters.join(' · ')}</dd></div><div><dt>Orden</dt><dd>{query.order === 'desc' ? 'Mayor a menor' : 'Menor a mayor'}</dd></div></dl>
    <div className="chat-query-results" role="table" aria-label={`Resultados de ${query.metric_name}`}>
      {query.points.map((point, index) => <div role="row" key={`${point.label}-${index}`}><span role="cell">{index + 1}. {point.label}</span><strong role="cell">{formatValue(point.value, query.unit)}</strong><small role="cell">{point.share === undefined ? '—' : `${point.share.toFixed(1)}%`}</small></div>)}
    </div>
    <p><strong>Denominador:</strong> {query.denominator_definition} Total: {formatValue(query.denominator_value, query.unit)}.</p>
    <details><summary>Ver procedencia</summary><ul>{query.provenance.map((item) => <li key={item}>{item}</li>)}</ul></details>
  </section>
}

function metricUnit(dashboard: AnalyticsDashboard) {
  return dashboard.kpis.find((item) => item.code === dashboard.metric_code)?.unit ?? 'valor'
}

function Skeleton() {
  return <div className="analytics-skeleton" aria-label="Cargando análisis" aria-busy="true"><div /><div className="skeleton-kpis">{[1, 2, 3, 4].map((item) => <span key={item} />)}</div><div className="skeleton-panels"><span /><span /><span /></div></div>
}

export function AnalyticsPage({ token, connectionId, canExport, navigate }: Props) {
  const [dashboard, setDashboard] = useState<AnalyticsDashboard | null>(null)
  const [executions, setExecutions] = useState<AnalyticsExecutionOption[]>([])
  const [executionId, setExecutionId] = useState(0)
  const [metricCode, setMetricCode] = useState('')
  const [year, setYear] = useState('')
  const [territory, setTerritory] = useState('')
  const [viewMode, setViewMode] = useState<'executive' | 'analyst'>('executive')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [exporting, setExporting] = useState<'pdf' | 'xlsx' | null>(null)
  const [chatQuestion, setChatQuestion] = useState('')
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string; answer?: AnalyticsCopilotAnswer }>>([])
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    setDashboard(null)
    setExecutions([])
    setExecutionId(0)
    setMetricCode('')
    setYear('')
    setTerritory('')
    setChatMessages([])
    setChatQuestion('')
    setChatError('')
    api.analyticsExecutions(token, connectionId || undefined)
      .then((items) => {
        if (cancelled) return
        if (items.some((item) => item.data_connection_id !== connectionId)) {
          throw new Error('La API devolvió ejecuciones de una fuente distinta al contexto seleccionado.')
        }
        setExecutions(items)
        setExecutionId(items[0]?.execution_id || 0)
        if (!items.length) {
          setError('No existe una ejecución conciliada con datos físicos disponibles para analizar.')
          setLoading(false)
        }
      })
      .catch((caught: Error) => {
        if (!cancelled) {
          setError(caught.message)
          setLoading(false)
        }
      })
    return () => { cancelled = true }
  }, [connectionId, token])

  useEffect(() => {
    const selectedExecution = executions.find((item) => item.execution_id === executionId)
    if (!executionId || selectedExecution?.data_connection_id !== connectionId) return
    let cancelled = false
    setLoading(true)
    setError('')
    api.analyticsDashboard(token, { connectionId, executionId, metricCode, year, territory })
      .then((result) => {
        if (cancelled) return
        if (result.data_connection_id !== connectionId || result.execution_id !== executionId) {
          throw new Error('El tablero recibido no corresponde a la fuente y ejecución seleccionadas.')
        }
        setDashboard(result)
        setMetricCode((current) => current || result.metric_code)
      })
      .catch((caught: Error) => { if (!cancelled) setError(caught.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [connectionId, executionId, executions, metricCode, territory, token, year])

  const unit = useMemo(() => dashboard ? metricUnit(dashboard) : 'valor', [dashboard])

  useEffect(() => {
    setChatMessages([])
    setChatQuestion('')
    setChatError('')
  }, [executionId, metricCode, territory, viewMode, year])
  if (loading && !dashboard) return <Skeleton />
  if (error && !dashboard) return <section className="analytics-blocked"><span aria-hidden="true">!</span><p className="eyebrow">Análisis no disponible</p><h2>Primero complete el expediente del datamart</h2><p>{error}</p><button onClick={() => navigate('/datamart-ventas')}>Abrir Generación de datamart</button></section>
  if (!dashboard) return null
  const activeDashboard = dashboard

  function clearFilters() {
    setYear('')
    setTerritory('')
  }

  async function exportReport(format: 'pdf' | 'xlsx') {
    setExporting(format)
    setError('')
    try {
      const file = await api.analyticsReport(token, format, {
        connectionId,
        executionId: activeDashboard.execution_id,
        metricCode: metricCode || activeDashboard.metric_code,
        year,
        territory,
        view: viewMode,
      })
      const url = URL.createObjectURL(file.blob)
      const link = document.createElement('a')
      link.href = url
      link.download = file.filename
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(url)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'No fue posible generar el reporte.')
    } finally {
      setExporting(null)
    }
  }

  function changeExecution(value: string) {
    setExecutionId(Number(value))
    setDashboard(null)
    setMetricCode('')
    setYear('')
    setTerritory('')
  }

  async function askCopilot(question = chatQuestion) {
    const normalized = question.trim()
    if (normalized.length < 5 || chatLoading) return
    const history = chatMessages.slice(-6).map((item) => ({ role: item.role, content: item.content }))
    setChatMessages((current) => [...current, { role: 'user', content: normalized }])
    setChatQuestion('')
    setChatLoading(true)
    setChatError('')
    try {
      const answer = await api.askAnalyticsCopilot(token, {
        question: normalized,
        history,
        view: viewMode,
        data_connection_id: connectionId,
        execution_id: activeDashboard.execution_id,
        metric_code: metricCode || activeDashboard.metric_code,
        year: year ? Number(year) : undefined,
        territory: territory || undefined,
      })
      setChatMessages((current) => [
        ...current,
        { role: 'assistant', content: answer.answer, answer },
      ])
    } catch (caught) {
      setChatError(caught instanceof Error ? caught.message : 'El copiloto no pudo responder.')
    } finally {
      setChatLoading(false)
    }
  }

  const visibleVisuals = viewMode === 'executive'
    ? dashboard.visuals.filter((item) => item.code !== 'customers')
    : dashboard.visuals
  const selectedMetricLabel = dashboard.available_metrics.find((item) => item.value === (metricCode || dashboard.metric_code))?.label ?? 'el indicador seleccionado'
  const selectedScope = [year || 'todos los años', territory || 'todos los territorios'].join(' y ')
  const promptGuide = viewMode === 'executive'
    ? [
        { category: 'Comprender', prompts: [`Resume ${selectedMetricLabel} para ${selectedScope}.`, '¿Qué resultado debería revisar primero y por qué?'] },
        { category: 'Decidir', prompts: ['¿Cuáles son los 5 productos con mayor resultado en el territorio líder?', 'Prepara tres puntos para una reunión de gerencia.'] },
        { category: 'Interpretar con cautela', prompts: ['¿Qué limitaciones tienen estos resultados y qué no puedo concluir?', '¿Qué pregunta adicional debería hacer antes de tomar una decisión?'] },
      ]
    : [
        { category: 'Comparar', prompts: [`Compara ${selectedMetricLabel} entre los períodos visibles.`, '¿Cuáles son los 5 productos con mayor resultado en el territorio líder?'] },
        { category: 'Investigar', prompts: ['¿Qué variación merece una revisión adicional?', 'Señala patrones atípicos sin atribuir causalidad.'] },
        { category: 'Validar', prompts: ['Explica la calidad y trazabilidad de esta selección.', '¿Qué dato agregado faltaría para responder preguntas que este panel no cubre?'] },
      ]
  const hasMultipleExecutions = executions.length > 1

  return <div className={`analytics-workspace mode-${viewMode}`}>
    <section className="analytics-hero">
      <div><div className="analytics-status"><span /> Datos conciliados y publicados</div><h2>{viewMode === 'executive' ? 'Resumen ejecutivo de ventas' : dashboard.title}</h2><p>{viewMode === 'executive' ? 'Indicadores y hallazgos principales para apoyar decisiones comerciales con datos verificados.' : dashboard.description}</p><div className="analytics-context"><span>{dashboard.source_name} · {dashboard.database_name}</span><span>Ejecución #{dashboard.execution_id}</span><span>Propuesta #{dashboard.proposal_id}</span><span>{dashboard.currency_code}</span><span>{dashboard.period_label}</span></div></div>
      <div className="analytics-hero-meta"><div className="analytics-view-switch" role="group" aria-label="Tipo de vista"><button className={viewMode === 'executive' ? 'active' : ''} aria-pressed={viewMode === 'executive'} onClick={() => setViewMode('executive')}>Vista ejecutiva</button><button className={viewMode === 'analyst' ? 'active' : ''} aria-pressed={viewMode === 'analyst'} onClick={() => setViewMode('analyst')}>Vista analítica</button></div><small>Última actualización</small><strong>{new Intl.DateTimeFormat('es-EC', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(dashboard.refreshed_at))}</strong><span>{viewMode === 'executive' ? 'Lectura resumida para dirección y gerencia.' : dashboard.grain}</span></div>
    </section>

    <section className="analytics-toolbar" aria-label="Filtros del análisis">
      <div><div className="analytics-execution-control">{hasMultipleExecutions ? <label>Datamart analizado<select aria-label="Datamart analizado" value={executionId} onChange={(event) => changeExecution(event.target.value)}>{executions.map((item) => <option key={item.execution_id} value={item.execution_id}>{item.label}</option>)}</select></label> : <div className="analytics-active-execution"><small>Datamart activo</small><strong>{executions[0]?.label ?? `Ejecución #${dashboard.execution_id}`}</strong></div>}{!hasMultipleExecutions && <p role="note">Sólo esta ejecución conserva datos físicos consultables. Los demás expedientes permanecen disponibles para auditoría. <button type="button" onClick={() => navigate('/datamart-ventas')}>Ver expedientes</button></p>}</div>{viewMode === 'analyst' && <label>Indicador de los gráficos<select value={metricCode || dashboard.metric_code} onChange={(event) => setMetricCode(event.target.value)}>{dashboard.available_metrics.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>}<label>Año<select value={year} onChange={(event) => setYear(event.target.value)}><option value="">Todos</option>{dashboard.filters.years.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label><label>Territorio<select value={territory} onChange={(event) => setTerritory(event.target.value)}><option value="">Todos</option>{dashboard.filters.territories.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label></div>
      <div className="analytics-toolbar-actions"><button className="secondary" disabled={!year && !territory} onClick={clearFilters}>Restablecer filtros</button>{canExport && <div className="analytics-export" aria-label="Exportar selección visible"><button className="secondary" disabled={exporting !== null} onClick={() => void exportReport('pdf')}>{exporting === 'pdf' ? 'Generando…' : 'Exportar PDF'}</button><button className="secondary" disabled={exporting !== null} onClick={() => void exportReport('xlsx')}>{exporting === 'xlsx' ? 'Generando…' : 'Exportar Excel'}</button></div>}</div>
    </section>
    {canExport && <p className="analytics-export-note">La exportación conserva la vista, el indicador y los filtros actuales. Excel incluye únicamente los datos que respaldan los gráficos visibles.</p>}
    {loading && <div className="analytics-refresh" role="status">Actualizando resultados…</div>}
    {error && <p className="notice error">{error}</p>}

    <section className="analytics-kpis" aria-label="Indicadores clave">
      {dashboard.kpis.map((kpi, index) => { const presentation = metricCardPresentation(kpi.value, kpi.unit); const reconciled = kpi.status === 'reconciled'; return <article className={reconciled ? '' : 'unavailable'} key={kpi.code}><div><span className="kpi-accent" data-index={index % 4} /><small>{kpi.name}</small></div><strong title={`Valor exacto: ${presentation.exact}`}>{presentation.value}</strong>{presentation.unit && <span className="analytics-kpi-unit">{presentation.unit}</span>}<p><span aria-hidden="true">{reconciled ? '✓' : '!'}</span> {reconciled ? 'Calculado con el filtro actual' : 'No calculable con esta ejecución'}</p></article> })}
    </section>

    <div className="analytics-layout">
      <section className="analytics-canvas" aria-label="Visualizaciones">
        {visibleVisuals.map((visual) => <VisualCard key={visual.code} visual={visual} unit={unit} showData={viewMode === 'analyst'} territoryOptions={visual.code === 'territories' ? dashboard.filters.territories : undefined} onTerritoryFilter={setTerritory} />)}
      </section>
      <aside className="analytics-insights" aria-label="Hallazgos explicables">
        <header><div className="spark-icon" aria-hidden="true">✦</div><div><p>Copiloto analítico</p><h2>Hallazgos explicables</h2></div></header>
        <p className="insight-intro">Lectura automática de los resultados visibles. No sustituye la interpretación del negocio.</p>
        {dashboard.insights.map((insight) => <article className={insight.tone} key={insight.code}><span className="insight-number" /><div><h3>{insight.title}</h3><p>{insight.statement}</p><small>{insight.evidence}</small></div></article>)}
        <details><summary>Cómo se generaron</summary><ul>{dashboard.guidance.map((item) => <li key={item}>{item}</li>)}</ul></details>
      </aside>
    </div>

    <section className="analytics-chat" aria-label="Conversación con el copiloto analítico">
      <header><div><p>Consulta contextual</p><h3>Preguntar sobre estos resultados</h3></div><span>IA</span></header>
      <p className="analytics-chat-intro">El copiloto interpreta indicador, dimensión, filtros y Top N. Puede consultar agregados permitidos aunque el filtro no esté seleccionado en pantalla; nunca recibe filas, credenciales ni SQL libre.</p>
      <details className="analytics-prompt-guide" open={chatMessages.length === 0}>
        <summary>Guía de preguntas sugeridas</summary>
        <p>Elija un ejemplo o úselo como modelo: indique qué quiere comprender, comparar o decidir y conserve el período o territorio relevante.</p>
        {promptGuide.map((group) => <div key={group.category}><strong>{group.category}</strong><div>{group.prompts.map((prompt) => <button type="button" key={prompt} onClick={() => void askCopilot(prompt)}>{prompt}</button>)}</div></div>)}
      </details>
      <div className="analytics-chat-conversation">
        {chatMessages.length === 0 && <div className="analytics-chat-empty"><span aria-hidden="true">✦</span><div><strong>Inicie con una pregunta concreta</strong><p>Seleccione una sugerencia o escriba qué necesita comprender, comparar o decidir.</p></div></div>}
        {chatMessages.length > 0 && <div className="analytics-chat-thread" aria-live="polite">{chatMessages.map((message, index) => <article className={message.role} key={`${message.role}-${index}`}><small>{message.role === 'user' ? 'Tu pregunta' : 'Copiloto analítico'}</small><p>{message.content}</p>{message.answer && <><InterpretedQueryCard answer={message.answer} /><ul>{message.answer.evidence.map((item) => <li key={item}>{item}</li>)}</ul><span>{message.answer.caveat}</span><div className="chat-followups">{message.answer.suggested_questions.map((item) => <button type="button" key={item} onClick={() => void askCopilot(item)}>{item}</button>)}</div><small>{message.answer.provider_kind} · {message.answer.model_id}</small></>}</article>)}</div>}
        {chatLoading && <p className="analytics-chat-status" role="status">Interpretando la pregunta y consultando agregados permitidos…</p>}
        {chatError && <p className="notice error" role="alert">{chatError}</p>}
        <form onSubmit={(event) => { event.preventDefault(); void askCopilot() }}><label htmlFor="analytics-chat-question">Escriba su pregunta</label><textarea id="analytics-chat-question" rows={3} minLength={5} maxLength={500} value={chatQuestion} onChange={(event) => setChatQuestion(event.target.value)} placeholder={viewMode === 'executive' ? 'Ejemplo: ¿qué resultado requiere atención directiva?' : 'Ejemplo: compara los productos principales y explica la evidencia.'} /><small>Una buena pregunta menciona el indicador, la comparación esperada y la decisión que desea apoyar.</small><button disabled={chatLoading || chatQuestion.trim().length < 5}>{chatLoading ? 'Consultando…' : 'Preguntar al copiloto'}</button></form>
      </div>
    </section>

    <section className="analytics-quality"><div><span className="quality-check" aria-hidden="true">✓</span><div><p className="eyebrow">Información confiable</p><h2>Resultados respaldados por el expediente #{dashboard.execution_id}</h2><p>{viewMode === 'executive' ? 'La plataforma comprobó los datos antes de publicar este resumen.' : 'Origen y datamart fueron contrastados antes de habilitar este panel.'}</p></div></div>{viewMode === 'analyst' && <dl><div><dt>Filas de origen</dt><dd>{formatValue(dashboard.quality.source_rows, 'filas')}</dd></div><div><dt>Filas cargadas</dt><dd>{formatValue(dashboard.quality.datamart_rows, 'filas')}</dd></div><div><dt>Diferencia</dt><dd>{formatValue(dashboard.quality.difference_rows, 'filas')}</dd></div><div><dt>Tablas</dt><dd>{dashboard.quality.tables_loaded}</dd></div></dl>}<button className="secondary" onClick={() => navigate('/datamart-ventas')}>{viewMode === 'executive' ? 'Consultar respaldo' : 'Ver expediente técnico'}</button></section>
  </div>
}
