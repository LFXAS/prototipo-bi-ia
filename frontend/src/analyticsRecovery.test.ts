import { afterEach, describe, expect, it } from 'vitest'

import { analyticsContextKey, clearAnalyticsContext, readAnalyticsContext, saveAnalyticsContext, type AnalyticsContext } from './analyticsRecovery'

const first: AnalyticsContext = { connectionId: 12, executionId: 8, metricCode: 'importe_neto', year: '2023', territory: 'Norte', viewMode: 'analyst' }
const second: AnalyticsContext = { connectionId: 31, executionId: 22, metricCode: 'sold_units', year: '2024', territory: 'South', viewMode: 'executive' }

afterEach(() => sessionStorage.clear())

describe('per-source analytics recovery', () => {
  it('preserves each source selection through repeated round trips, including an older execution', () => {
    saveAnalyticsContext(first)
    saveAnalyticsContext(second)
    expect(readAnalyticsContext(first.connectionId)).toEqual(first)
    expect(readAnalyticsContext(second.connectionId)).toEqual(second)
    saveAnalyticsContext({ ...first, year: '2022', territory: 'Centro' })
    expect(readAnalyticsContext(second.connectionId)).toEqual(second)
    saveAnalyticsContext({ ...second, metricCode: 'invoice_count' })
    expect(readAnalyticsContext(first.connectionId)).toEqual({ ...first, year: '2022', territory: 'Centro' })
    expect(readAnalyticsContext(first.connectionId)?.executionId).toBe(8)
    expect(readAnalyticsContext(second.connectionId)).toEqual({ ...second, metricCode: 'invoice_count' })
    expect(readAnalyticsContext(99)).toBeNull()
  })

  it('reads the previous single-source format and retains it when another source is first saved', () => {
    sessionStorage.setItem(analyticsContextKey, JSON.stringify(first))
    expect(readAnalyticsContext(first.connectionId)).toEqual(first)
    saveAnalyticsContext(second)
    expect(JSON.parse(sessionStorage.getItem(analyticsContextKey)!)).toMatchObject({ version: 2 })
    expect(readAnalyticsContext(first.connectionId)).toEqual(first)
    expect(readAnalyticsContext(second.connectionId)).toEqual(second)
  })

  it('resets only the requested source and allows logout to remove the complete map', () => {
    saveAnalyticsContext(first)
    saveAnalyticsContext(second)
    clearAnalyticsContext(first.connectionId)
    expect(readAnalyticsContext(first.connectionId)).toBeNull()
    expect(readAnalyticsContext(second.connectionId)).toEqual(second)
    sessionStorage.removeItem(analyticsContextKey)
    expect(readAnalyticsContext(first.connectionId)).toBeNull()
    expect(readAnalyticsContext(second.connectionId)).toBeNull()
  })

  it('isolates malformed or mismatched entries and serializes only the allowed selection fields', () => {
    sessionStorage.setItem(analyticsContextKey, JSON.stringify({ version: 2, byConnection: {
      '12': { ...first, data: [{ amount: 999 }], token: 'do-not-store', chat: 'do-not-store' },
      '31': { ...second, connectionId: 12 },
      '13': { ...first, connectionId: 13, executionId: -1 },
      '14': { ...first, connectionId: 14, year: 'bad' },
    } }))
    expect(readAnalyticsContext(12)).toEqual(first)
    expect(readAnalyticsContext(31)).toBeNull()
    expect(readAnalyticsContext(13)).toBeNull()
    expect(readAnalyticsContext(14)).toBeNull()
    saveAnalyticsContext(second)
    expect(sessionStorage.getItem(analyticsContextKey)).not.toContain('do-not-store')
    expect(sessionStorage.getItem(analyticsContextKey)).not.toContain('999')
    expect(readAnalyticsContext(31)).toEqual(second)
    sessionStorage.setItem(analyticsContextKey, '{broken')
    expect(readAnalyticsContext(12)).toBeNull()
  })
})
