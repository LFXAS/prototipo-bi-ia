import { afterEach, describe, expect, it } from 'vitest'

import { initialWorkspaceNavigation, readWorkspaceNavigation, tokenExpirationTime, workspaceNavigation, workspaceNavigationKey } from './workspaceNavigation'
import { reconcileAssistantQuestions } from './assistantRecovery'

afterEach(() => sessionStorage.clear())

describe('workspace recovery', () => {
  it('restores only registered routes and validates the contextual return independently', () => {
    const current = { page: '/llm', setupStep: 2, returnTo: { page: '/', setupStep: 2 } }
    sessionStorage.setItem(workspaceNavigationKey, JSON.stringify(current))
    expect(readWorkspaceNavigation(['/', '/llm'])).toEqual(current)
    expect(workspaceNavigation(current, ['/'])).toEqual(initialWorkspaceNavigation)
    expect(workspaceNavigation({ ...current, returnTo: { page: '/usuarios', setupStep: 9 } }, ['/', '/llm'])).toEqual({ ...current, returnTo: null })
  })

  it('ignores malformed storage without preventing login', () => {
    sessionStorage.setItem(workspaceNavigationKey, '{broken')
    expect(readWorkspaceNavigation(['/'])).toEqual(initialWorkspaceNavigation)
  })

  it('reads the declared expiration without treating frontend decoding as authentication', () => {
    const token = `header.${btoa(JSON.stringify({ exp: 123456 }))}.signature`
    expect(tokenExpirationTime(token)).toBe(123456000)
    expect(tokenExpirationTime('test-token')).toBeNull()
    expect(tokenExpirationTime(`header.${btoa(JSON.stringify({ exp: '123456' }))}.signature`)).toBeNull()
  })

  it('retains the valid choice and removes deleted or unavailable questions in any source language', () => {
    expect(reconcileAssistantQuestions(['custom_old', 'ventas_mes', 'sales_product', 'ventas_mes'], [
      { code: 'ventas_mes', available: true }, { code: 'sales_product', available: false },
    ])).toEqual({ questions: ['ventas_mes'], removed: ['custom_old', 'sales_product'] })
  })
})
