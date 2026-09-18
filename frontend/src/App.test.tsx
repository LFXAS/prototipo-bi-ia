import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import { roleChoicesForUserAssignment } from './roleChoices'

describe('App', () => {
  afterEach(() => {
    cleanup()
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('presenta el acceso con un mensaje de orientación', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'BI asistido por IA' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument()
    expect(screen.getByText(/interfaz y la API validan los permisos reales/i)).toBeInTheDocument()
  })

  it('permite retirar un rol inactivo previamente asignado sin ofrecerlo a cuentas nuevas', () => {
    const roles = [
      { id: 1, code: 'administrator', name: 'Administrador', description: 'Rol inicial.', is_active: true, permissions: [] },
      { id: 2, code: 'operator', name: 'Operador', description: 'Consulta.', is_active: false, permissions: [] },
    ]

    expect(roleChoicesForUserAssignment(roles).map((role) => role.label)).toEqual(['Administrador'])
    expect(roleChoicesForUserAssignment(roles, [roles[1].id]).map((role) => role.label)).toEqual(['Administrador', 'Operador (inactivo)'])
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

  it('registra una credencial LLM desde la plataforma sin volver a mostrarla', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/auth/me')) return {
        ok: true,
        status: 200,
        json: async () => ({
          user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
          permissions: ['parameters.llm.write'],
          menus: [{ id: 1, code: 'llm', label: 'Configuración LLM', path: '/llm', position: 60, module_code: 'parameters', module_label: 'Parámetros generales', is_active: true, permissions: [] }],
        }),
      }
      if (url.includes('/llm-configurations/7/secret')) return {
        ok: true,
        status: 200,
        json: async () => ({ credential_configured: true, message: 'Credencial protegida correctamente.' }),
      }
      if (url.includes('/llm-configurations')) return {
        ok: true,
        status: 200,
        json: async () => ({
          items: [{ id: 7, name: 'Gemini tesis', provider_kind: 'gemini', base_url: 'https://generativelanguage.googleapis.com', model_id: 'gemini-2.5-flash', credential_configured: false, is_active: false }],
          total: 1,
          limit: 10,
          offset: 0,
        }),
      }
      throw new Error(`Solicitud inesperada: ${url} ${init?.method ?? 'GET'}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    fireEvent.click(await screen.findByRole('button', { name: 'Parámetros generales' }))
    fireEvent.click(screen.getByRole('button', { name: 'Configuración LLM' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Registrar credencial' }))
    fireEvent.change(screen.getByLabelText('API key'), { target: { value: 'gemini-key-de-prueba' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar credencial' }))

    expect(await screen.findByText('Credencial protegida correctamente.')).toBeInTheDocument()
    const secretRequest = fetchMock.mock.calls.find(([input]) => String(input).includes('/llm-configurations/7/secret'))
    expect(secretRequest?.[1]?.body).toBe(JSON.stringify({ api_key: 'gemini-key-de-prueba' }))
    expect(screen.queryByDisplayValue('gemini-key-de-prueba')).not.toBeInTheDocument()
  })

  it('edita únicamente parámetros aprobados dentro de su rango visible', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/auth/me')) return {
        ok: true, status: 200, json: async () => ({
          user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
          permissions: ['parameters.write'],
          menus: [{ id: 6, code: 'parameters', label: 'Parámetros', path: '/parametros', position: 50, module_code: 'parameters', module_label: 'Parámetros generales', is_active: true, permissions: [] }],
        }),
      }
      if (url.includes('/parameters/UI_PAGE_SIZE') && init?.method === 'PUT') return {
        ok: true, status: 200, json: async () => ({ id: 1, key: 'UI_PAGE_SIZE', name: 'Registros por página', module_code: 'ui', value_type: 'integer', value: '25', default_value: '10', min_value: 10, max_value: 100, is_active: true }),
      }
      if (url.includes('/parameters')) return {
        ok: true, status: 200, json: async () => ({
          items: [{ id: 1, key: 'UI_PAGE_SIZE', name: 'Registros por página', module_code: 'ui', value_type: 'integer', value: '10', default_value: '10', min_value: 10, max_value: 100, description: 'Cantidad predeterminada.', is_active: true }],
          total: 1, limit: 10, offset: 0,
        }),
      }
      throw new Error(`Solicitud inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Parámetros generales' }))
    fireEvent.click(screen.getByRole('button', { name: 'Parámetros' }))
    const field = await screen.findByRole('spinbutton', { name: 'Valor' })
    expect(field).toHaveAttribute('min', '10')
    expect(field).toHaveAttribute('max', '100')
    fireEvent.change(field, { target: { value: '25' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(await screen.findByText('Registros por página fue actualizado.')).toBeInTheDocument()
    const updateRequest = fetchMock.mock.calls.find(([input, init]) => String(input).includes('/parameters/UI_PAGE_SIZE') && init?.method === 'PUT')
    expect(updateRequest?.[1]?.body).toBe(JSON.stringify({ value: '25' }))
  })

  it('muestra el estado de solo lectura de una conexión sin exponer contraseña', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/auth/me')) return {
        ok: true, status: 200, json: async () => ({
          user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
          permissions: ['connections.read', 'connections.write', 'connections.test'],
          menus: [{ id: 9, code: 'connections', label: 'Conexiones de datos', path: '/conexiones', position: 65, module_code: 'parameters', module_label: 'Parámetros generales', is_active: true, permissions: [] }],
        }),
      }
      if (url.includes('/connections')) return {
        ok: true, status: 200, json: async () => ({
          items: [{ id: 1, name: 'AdventureWorks local', connector_kind: 'sqlserver', host: 'sqlserver', port: 1433, database_name: 'AdventureWorks2022', username: 'bi_reader', encrypt: true, trust_server_certificate: true, is_active: true, last_test_status: 'ok', last_test_message: 'Conexión validada.' }],
          total: 1, limit: 10, offset: 0,
        }),
      }
      throw new Error(`Solicitud inesperada: ${url}`)
    }))

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Parámetros generales' }))
    fireEvent.click(screen.getByRole('button', { name: 'Conexiones de datos' }))

    expect(await screen.findByText('Sólo lectura validada')).toBeInTheDocument()
    expect(screen.getByText('Activa')).toBeInTheDocument()
    expect(screen.queryByText(/password|contraseña guardada/i)).not.toBeInTheDocument()
  })
})
