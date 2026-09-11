import { fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from './App'

describe('App', () => {
  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('presenta el acceso con un mensaje de orientación', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'BI asistido por IA' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument()
    expect(screen.getByText(/interfaz y la API validan los permisos reales/i)).toBeInTheDocument()
  })

  it('mantiene Inicio directo y permite plegar el módulo activo', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      json: async () => ({
        user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
        permissions: [],
        menus: [
          { id: 1, code: 'home', label: 'Inicio', path: '/', position: 0, module_code: 'home', module_label: 'Inicio', is_active: true, permissions: [] },
          { id: 2, code: 'users', label: 'Usuarios', path: '/usuarios', position: 10, module_code: 'security', module_label: 'Seguridad', is_active: true, permissions: [] },
        ],
      }),
    })))

    render(<App />)

    expect(await screen.findByRole('button', { name: 'Inicio' })).toHaveClass('direct-menu')
    expect(screen.queryByRole('button', { name: 'Principal' })).not.toBeInTheDocument()
    const sidebarControl = screen.getByRole('button', { name: 'Ocultar navegación lateral' })
    fireEvent.click(sidebarControl)
    expect(screen.getByRole('button', { name: 'Mostrar navegación lateral' })).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(screen.getByRole('button', { name: 'Mostrar navegación lateral' }))
    const security = await screen.findByRole('button', { name: 'Seguridad' })
    const submenu = screen.getByText('Usuarios').closest('.submenu')
    expect(submenu).toHaveAttribute('hidden')

    fireEvent.click(security)
    expect(submenu).not.toHaveAttribute('hidden')

    fireEvent.click(security)
    expect(submenu).toHaveAttribute('hidden')

    fireEvent.click(security)
    fireEvent.click(screen.getByRole('button', { name: 'Usuarios' }))
    expect(screen.getByRole('heading', { name: 'Usuarios' })).toBeInTheDocument()
    fireEvent.click(security)
    expect(submenu).toHaveAttribute('hidden')
  })
})
