import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from './App'

describe('App', () => {
  afterEach(() => vi.restoreAllMocks())

  it('presenta el alcance de la fase inicial', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          status: 'ok',
          service: 'Prototipo BI asistido por IA',
          version: '0.1.0',
          postgres: 'not_checked',
        }),
      }),
    )

    render(<App />)

    expect(screen.getByRole('heading', { name: 'BI asistido por IA' })).toBeInTheDocument()
    expect(await screen.findByText('API disponible · v0.1.0')).toBeInTheDocument()
    expect(screen.getByText('Seguridad RBAC')).toBeInTheDocument()
  })
})
