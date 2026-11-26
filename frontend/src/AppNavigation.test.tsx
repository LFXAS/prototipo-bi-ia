import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import { api, type Session } from './api/security'
import { workspaceNavigationKey } from './workspaceNavigation'

vi.mock('./AnalyticsPage', () => ({ AnalyticsPage: ({ navigate }: { navigate: (path: string) => void }) => <button onClick={() => navigate('/datamart-ventas')}>Consultar respaldo</button> }))

const paths = ['/', '/llm', '/conexiones', '/esquema', '/asistente', '/analitica-ventas', '/datamart-ventas']
const routeLabels = ['Inicio', 'Configuración LLM', 'Conexiones de datos', 'Explorador de esquema', 'Asistente de datamart', 'Analítica de ventas', 'Datamart de ventas']
const session: Session = {
  user: { id: 1, email: 'analista@example.test', full_name: 'Analista', is_active: true, roles: [] },
  permissions: ['copilot.proposals.read', 'copilot.proposals.generate', 'parameters.llm.write'],
  menus: paths.map((path, index) => ({ id: index + 1, path, code: `menu-${index}`, label: routeLabels[index], position: index, module_code: 'test', module_label: 'Prueba', is_active: true, permissions: [] })),
}
const ready = { ready: true, source: { ready: true, label: 'Fuente', detail: 'Lista.' }, metadata: { ready: true, label: 'Metadatos', detail: 'Lista.' }, llm: { ready: true, label: 'IA', detail: 'Lista.' } }

beforeEach(() => {
  vi.stubGlobal('scrollTo', vi.fn())
  localStorage.setItem('bi_ia_access_token', 'test-token')
  vi.spyOn(api, 'session').mockResolvedValue(session)
  vi.spyOn(api, 'sources').mockResolvedValue([{ status: 'ready', connection: { id: 1, name: 'Fuente', connector_kind: 'sqlserver', database_name: 'Base', last_test_status: 'ok' }, latest_snapshot: { id: 1, data_connection_id: 1, connector_code: 'sqlserver', database_name: 'Base', contract_version: 1, content_hash: 'hash', schema_count: 1, table_count: 1, column_count: 1, relationship_count: 0, captured_by_label: 'Analista', captured_at: '2026-11-25T12:00:00Z' } }])
  vi.spyOn(api, 'copilotReadiness').mockResolvedValue(ready)
  vi.spyOn(api, 'llm').mockResolvedValue({ items: [], total: 0, limit: 10, offset: 0 })
  vi.spyOn(api, 'connections').mockResolvedValue({ items: [], total: 0, limit: 10, offset: 0 })
  vi.spyOn(api, 'metadataSnapshots').mockResolvedValue({ items: [], total: 0, limit: 10, offset: 0 })
  vi.spyOn(api, 'copilotCatalog').mockResolvedValue({ metadata_snapshot_id: 1, domains: [] })
  vi.spyOn(api, 'etlProposals').mockResolvedValue({ items: [], blocked_items: [], guidance: ['Revise las propuestas disponibles.'] })
  vi.spyOn(api, 'etlExecutions').mockResolvedValue({ items: [], total: 0, limit: 5, offset: 0 })
})

afterEach(() => {
  cleanup()
  localStorage.clear()
  sessionStorage.clear()
  window.history.replaceState(null, '')
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

describe('workspace navigation', () => {
  it('keeps the module after remount and removes contextual back on direct navigation', async () => {
    const app = render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Preparación del entorno' }))
    fireEvent.click(screen.getByRole('button', { name: 'Configuración LLM' }))
    await screen.findByRole('heading', { name: 'Crear configuración LLM' })
    expect(screen.queryByRole('button', { name: '← Atrás' })).not.toBeInTheDocument()
    app.unmount()
    render(<App />)
    expect(await screen.findByRole('heading', { name: 'Crear configuración LLM' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Configuración LLM' })).toBeInTheDocument()
  })

  it.each([2, 3, 4, 5])('returns to the same guided step %i and persists its origin across refresh', async (step) => {
    const app = render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Revisar configuración' }))
    for (let index = 1; index < step; index += 1) fireEvent.click(screen.getByRole('button', { name: 'Continuar' }))
    fireEvent.click(screen.getByRole('button', { name: step === 5 ? 'Elegir datamart' : 'Revisar este paso' }))
    await screen.findByRole('button', { name: '← Atrás' })
    app.unmount()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: '← Atrás' }))
    expect(await screen.findByText(`Paso ${step} de 5`)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '← Atrás' })).not.toBeInTheDocument()
  })

  it('returns from home proposal creation and from analytics evidence without a browser Back', async () => {
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Crear propuesta de datamart' }))
    fireEvent.click(await screen.findByRole('button', { name: '← Atrás' }))
    expect(await screen.findByRole('button', { name: 'Revisar configuración' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Análisis y decisiones' }))
    fireEvent.click(screen.getByRole('button', { name: 'Analítica de ventas' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Consultar respaldo' }))
    fireEvent.click(await screen.findByRole('button', { name: '← Atrás' }))
    expect(await screen.findByRole('button', { name: 'Consultar respaldo' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Diseño y transformación BI' }))
    fireEvent.click(screen.getByRole('button', { name: 'Datamart de ventas' }))
    expect(screen.queryByRole('button', { name: '← Atrás' })).not.toBeInTheDocument()
  })

  it('restores browser navigation only to a route authorized by the current session', async () => {
    sessionStorage.setItem(workspaceNavigationKey, JSON.stringify({ page: '/usuarios', setupStep: null, returnTo: null }))
    const users = vi.spyOn(api, 'users')
    render(<App />)
    await screen.findByRole('button', { name: 'Revisar configuración' })
    expect(users).not.toHaveBeenCalled()
    act(() => window.dispatchEvent(new PopStateEvent('popstate', { state: { biWorkspace: { page: '/llm', setupStep: null, returnTo: null } } })))
    expect(await screen.findByRole('heading', { name: 'Crear configuración LLM' })).toBeInTheDocument()
  })

  it('revalidates the origin permission before returning from an evidence screen', async () => {
    sessionStorage.setItem(workspaceNavigationKey, JSON.stringify({ page: '/analitica-ventas', setupStep: null, returnTo: null }))
    render(<App />)
    await screen.findByRole('option', { name: 'Fuente · Base' })
    fireEvent.click(await screen.findByRole('button', { name: 'Consultar respaldo' }))
    await screen.findByRole('button', { name: '← Atrás' })
    vi.mocked(api.session).mockResolvedValue({ ...session, menus: session.menus.filter((menu) => menu.path !== '/analitica-ventas') })
    fireEvent.click(screen.getByRole('button', { name: '← Atrás' }))
    expect(await screen.findByRole('button', { name: 'Revisar configuración' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Inicio' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Consultar respaldo' })).not.toBeInTheDocument()
  })

  it('does not replace a newer sidebar choice with a late contextual return', async () => {
    sessionStorage.setItem(workspaceNavigationKey, JSON.stringify({ page: '/analitica-ventas', setupStep: null, returnTo: null }))
    render(<App />)
    await screen.findByRole('option', { name: 'Fuente · Base' })
    fireEvent.click(await screen.findByRole('button', { name: 'Consultar respaldo' }))
    await screen.findByRole('button', { name: '← Atrás' })
    let finishPermissionCheck!: (value: Session) => void
    vi.mocked(api.session).mockImplementationOnce(() => new Promise((resolve) => { finishPermissionCheck = resolve }))
    fireEvent.click(screen.getByRole('button', { name: '← Atrás' }))
    fireEvent.click(screen.getByRole('button', { name: 'Preparación del entorno' }))
    fireEvent.click(screen.getByRole('button', { name: 'Configuración LLM' }))
    await screen.findByRole('heading', { name: 'Crear configuración LLM' })
    await act(async () => finishPermissionCheck(session))
    expect(screen.getByRole('heading', { name: 'Crear configuración LLM' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Consultar respaldo' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '← Atrás' })).not.toBeInTheDocument()
  })

  it('shows login at the JWT deadline even without another API call', async () => {
    vi.useFakeTimers()
    const now = Date.now()
    localStorage.setItem('bi_ia_access_token', `header.${btoa(JSON.stringify({ exp: (now + 600000) / 1000 }))}.signature`)
    render(<App />)
    await act(async () => { await Promise.resolve() })
    expect(screen.queryByRole('button', { name: 'Iniciar sesión' })).not.toBeInTheDocument()
    act(() => { vi.advanceTimersByTime(599999) })
    expect(screen.queryByRole('button', { name: 'Iniciar sesión' })).not.toBeInTheDocument()
    act(() => { vi.advanceTimersByTime(1) })
    expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument()
    expect(localStorage.getItem('bi_ia_access_token')).toBeNull()
  })

  it('offers an economical OpenAI preset with low reasoning and keeps the model editable', async () => {
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Preparación del entorno' }))
    fireEvent.click(screen.getByRole('button', { name: 'Configuración LLM' }))
    fireEvent.change(await screen.findByRole('combobox', { name: 'Proveedor' }), { target: { value: 'openai-cloud' } })
    expect(screen.getByLabelText('URL del servicio')).toHaveValue('https://api.openai.com/v1')
    expect(screen.getByLabelText('Modelo')).toHaveValue('gpt-6-luna')
    expect(screen.getByLabelText('Modelo')).toBeEnabled()
    expect(screen.getByLabelText('Nivel de razonamiento')).toHaveValue('low')
    await waitFor(() => expect(api.llm).toHaveBeenCalled())
  })

  it('preserves a saved OpenAI model and reasoning level when opening its editor', async () => {
    vi.mocked(api.llm).mockResolvedValue({ items: [{ id: 13, name: 'Configuración anterior', provider_kind: 'openai-cloud', base_url: 'https://api.openai.com/v1', model_id: 'gpt-6.2-sol', reasoning_level: 'medium', credential_configured: true, is_active: false }], total: 1, limit: 10, offset: 0 })
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Preparación del entorno' }))
    fireEvent.click(screen.getByRole('button', { name: 'Configuración LLM' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Editar' }))
    expect(screen.getByLabelText('Modelo')).toHaveValue('gpt-6.2-sol')
    expect(screen.getByLabelText('Nivel de razonamiento')).toHaveValue('medium')
  })
})
