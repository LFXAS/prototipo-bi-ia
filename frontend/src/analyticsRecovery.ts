export const analyticsContextKey = 'bi_ia_analytics_context_v1'

export type AnalyticsContext = {
  connectionId: number
  executionId: number
  metricCode: string
  year: string
  territory: string
  viewMode: 'executive' | 'analyst'
}

type AnalyticsContexts = { version: 2; byConnection: Record<string, AnalyticsContext> }

function context(value: unknown, connectionId: number): AnalyticsContext | null {
  if (!value || typeof value !== 'object' || !Number.isInteger(connectionId) || connectionId <= 0) return null
  const candidate = value as Partial<AnalyticsContext>
  if (candidate.connectionId !== connectionId || !Number.isInteger(candidate.executionId) || Number(candidate.executionId) <= 0) return null
  if (typeof candidate.metricCode !== 'string' || candidate.metricCode.length > 100 || typeof candidate.year !== 'string' || !/^(\d{4})?$/.test(candidate.year) || typeof candidate.territory !== 'string' || candidate.territory.length > 200) return null
  return { connectionId, executionId: Number(candidate.executionId), metricCode: candidate.metricCode, year: candidate.year, territory: candidate.territory, viewMode: candidate.viewMode === 'analyst' ? 'analyst' : 'executive' }
}

function readContexts(): AnalyticsContexts {
  const empty: AnalyticsContexts = { version: 2, byConnection: {} }
  try {
    const stored = JSON.parse(sessionStorage.getItem(analyticsContextKey) ?? 'null') as unknown
    if (!stored || typeof stored !== 'object') return empty
    const value = stored as Partial<AnalyticsContexts & AnalyticsContext>
    if (value.version === 2 && value.byConnection && typeof value.byConnection === 'object' && !Array.isArray(value.byConnection)) {
      for (const [id, raw] of Object.entries(value.byConnection)) {
        const valid = context(raw, Number(id))
        if (valid && String(valid.connectionId) === id) empty.byConnection[id] = valid
      }
    } else {
      // Preserve the single-source selection written by the previous format.
      const legacy = context(value, Number(value.connectionId))
      if (legacy) empty.byConnection[String(legacy.connectionId)] = legacy
    }
    return empty
  } catch {
    return empty
  }
}

export function readAnalyticsContext(connectionId: number): AnalyticsContext | null {
  return readContexts().byConnection[String(connectionId)] ?? null
}

export function saveAnalyticsContext(value: AnalyticsContext) {
  const valid = context(value, value.connectionId)
  if (!valid) return
  const stored = readContexts()
  stored.byConnection[String(valid.connectionId)] = valid
  sessionStorage.setItem(analyticsContextKey, JSON.stringify(stored))
}

export function clearAnalyticsContext(connectionId: number) {
  const stored = readContexts()
  delete stored.byConnection[String(connectionId)]
  if (Object.keys(stored.byConnection).length) sessionStorage.setItem(analyticsContextKey, JSON.stringify(stored))
  else sessionStorage.removeItem(analyticsContextKey)
}
