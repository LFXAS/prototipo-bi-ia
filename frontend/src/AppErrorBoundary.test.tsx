import { render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'

import { AppErrorBoundary } from './AppErrorBoundary'

function BrokenView(): never {
  throw new Error('Fallo controlado de prueba')
}

afterEach(() => vi.restoreAllMocks())

it('sustituye una pantalla en blanco por una recuperación explícita', () => {
  vi.spyOn(console, 'error').mockImplementation(() => undefined)

  render(<AppErrorBoundary><BrokenView /></AppErrorBoundary>)

  expect(screen.getByRole('alert')).toHaveTextContent('El expediente sigue seguro')
  expect(screen.getByText(/no repitió el ETL/i)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Recargar la aplicación' })).toBeInTheDocument()
})
