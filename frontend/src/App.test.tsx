import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import { api, sessionExpiredEvent } from './api/security'
import { readAssistantDraft } from './assistantRecovery'
import { roleChoicesForUserAssignment } from './roleChoices'

const sourceConnection = {
  id: 1,
  name: 'Fuente comercial de prueba',
  connector_kind: 'sqlserver',
  database_name: 'BaseComercial',
  last_test_status: 'ok',
}

function sourceWorkspace(latestSnapshot: Record<string, unknown> | null = null) {
  return [{ status: latestSnapshot ? 'ready' : 'metadata_pending', connection: sourceConnection, latest_snapshot: latestSnapshot }]
}

async function openNeedAssistant() {
  localStorage.setItem('bi_ia_access_token', 'test-token')
  const snapshot = { id: 4, data_connection_id: 1, connector_code: 'sqlserver', database_name: 'BaseComercial', content_hash: 'b'.repeat(64) }
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.includes('/auth/me')) return { ok: true, status: 200, json: async () => ({ user: { id: 1, email: 'admin@example.test', full_name: 'Analista', is_active: true, roles: [] }, permissions: ['copilot.proposals.read', 'copilot.proposals.generate'], menus: [{ id: 11, code: 'analysis-assistant', label: 'Asistente de datamart', path: '/asistente', position: 10, module_code: 'ai', module_label: 'IA', is_active: true, permissions: [] }] }) }
    if (url.endsWith('/sources')) return { ok: true, status: 200, json: async () => [...sourceWorkspace(snapshot), { status: 'ready', connection: { ...sourceConnection, id: 2, name: 'Segunda fuente', database_name: 'OtraBase' }, latest_snapshot: { ...snapshot, id: 5, data_connection_id: 2, database_name: 'OtraBase', content_hash: 'c'.repeat(64) } }] }
    if (url.includes('/copilot/readiness?')) return { ok: true, status: 200, json: async () => ({ ready: true, source: { ready: true, label: 'Fuente', detail: 'Fuente lista.' }, metadata: { ready: true, label: 'Metadatos', detail: 'Instantánea disponible.' }, llm: { ready: true, label: 'IA', detail: 'Proveedor listo.', metadata_consent_target: 'approved-target', metadata_consent_label: 'Proveedor de prueba · modelo-prueba · https://example.test' } }) }
    if (url.includes('/copilot/catalog?')) return { ok: true, status: 200, json: async () => ({ metadata_snapshot_id: url.includes('snapshot_id=5') ? 5 : 4, domains: [{ code: 'ventas', label: 'Datamart de ventas', description: 'Análisis comercial.', available: true, reason: 'Estructura disponible.', questions: [{ code: 'sales_over_time', label: 'Evolución de ventas en el tiempo', description: 'Comparación temporal.', available: true, evidence: [], reason: 'Disponible.' }], periodicities: [{ code: 'month', label: 'Mensual', available: true }, { code: 'year', label: 'Anual', available: true }] }] }) }
    if (url.includes('/copilot/proposals?')) return { ok: true, status: 200, json: async () => ({ items: [], total: 0, limit: 5, offset: 0 }) }
    throw new Error(`Solicitud inesperada: ${url}`)
  }))
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Diseño y transformación BI' }))
  fireEvent.click(screen.getByRole('button', { name: 'Asistente de datamart' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Crear propuesta' }))
  return screen.getByRole('textbox', { name: /Objetivo del análisis/ })
}

const groundedSuggestions = {
  metadata_snapshot_id: 4, provider_kind: 'anthropic', model_id: 'modelo-prueba',
  notice: 'Sugerencias contrastadas con las relaciones declaradas.',
  suggestions: [{ suggested_goal: 'Comparar el importe de ventas por mes para revisar su evolución.', rationale: 'Existe importe de venta y fecha relacionada.', evidence: ['Comercial.Detalle.Importe', 'Comercial.Cabecera.Fecha'], limitations: ['No demuestra cobros ni moneda.'], usable: true }],
}

describe('App', () => {
  beforeEach(() => vi.stubGlobal('scrollTo', vi.fn()))

  afterEach(() => {
    cleanup()
    localStorage.clear()
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('presenta el acceso con un mensaje de orientación', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'BI asistido por IA' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Iniciar sesión' })).toBeInTheDocument()
    expect(screen.getByText(/interfaz y la API validan los permisos reales/i)).toBeInTheDocument()
  })

  it('sugiere necesidades sin texto previo y exige elección humana con evidencia y límites', async () => {
    const suggestion = vi.spyOn(api, 'suggestNeeds').mockResolvedValue({ ...groundedSuggestions, suggestions: [...groundedSuggestions.suggestions, { suggested_goal: 'Predecir ventas futuras sin una fuente adicional disponible.', rationale: 'No respaldada.', evidence: [], limitations: ['No existen datos para esa predicción.'], usable: false }] })
    const validate = vi.spyOn(api, 'validateNeed')
    const goal = await openNeedAssistant()
    expect(goal).toHaveValue('')
    expect(screen.getByRole('button', { name: 'Sugerir necesidades con esta fuente' })).toBeDisabled()
    expect(screen.getByText(/^La IA recibirá la necesidad/)).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText(/Autorizo enviar estos metadatos/))
    fireEvent.click(screen.getByRole('button', { name: 'Sugerir necesidades con esta fuente' }))
    expect(await screen.findByRole('heading', { name: 'Necesidades propuestas para revisar' })).toBeInTheDocument()
    expect(suggestion).toHaveBeenCalledWith('test-token', { metadata_snapshot_id: 4, domain_code: 'ventas', periodicity: 'month', business_questions: [], metadata_consent_target: 'approved-target' })
    expect(goal).toHaveValue('')
    expect(screen.getByText('Comercial.Detalle.Importe')).toBeInTheDocument()
    expect(screen.getByText('No demuestra cobros ni moneda.')).toBeInTheDocument()
    expect(screen.getByText(/respaldo estructural no garantiza la calidad/)).toBeInTheDocument()
    expect(within(screen.getByRole('article', { name: 'Necesidad sugerida 2' })).getByRole('button', { name: 'Usar esta necesidad' })).toBeDisabled()
    fireEvent.click(within(screen.getByRole('article', { name: 'Necesidad sugerida 1' })).getByRole('button', { name: 'Usar esta necesidad' }))
    expect(goal).toHaveValue(groundedSuggestions.suggestions[0].suggested_goal)
    expect(validate).not.toHaveBeenCalled()
    expect(screen.queryByRole('heading', { name: 'Necesidades propuestas para revisar' })).not.toBeInTheDocument()
    expect(screen.getByText(/Necesidad elegida. Revise las preguntas/)).toBeInTheDocument()
  })

  it.each(['texto', 'preguntas', 'periodicidad', 'autorización'])('descarta sugerencias antiguas al cambiar %s durante la consulta', async (change) => {
    let finish!: (value: Awaited<ReturnType<typeof api.suggestNeeds>>) => void
    vi.spyOn(api, 'suggestNeeds').mockImplementation(() => new Promise((resolve) => { finish = resolve }))
    const goal = await openNeedAssistant()
    fireEvent.click(screen.getByLabelText(/Autorizo enviar estos metadatos/))
    fireEvent.click(screen.getByRole('button', { name: 'Sugerir necesidades con esta fuente' }))
    if (change === 'texto') fireEvent.change(goal, { target: { value: 'Necesidad redactada mientras responde el proveedor.' } })
    if (change === 'preguntas') fireEvent.click(screen.getByLabelText(/Evolución de ventas/))
    if (change === 'periodicidad') fireEvent.change(screen.getByLabelText('Periodicidad'), { target: { value: 'year' } })
    if (change === 'autorización') fireEvent.click(screen.getByLabelText(/Autorizo enviar estos metadatos/))
    await act(async () => { finish(groundedSuggestions) })
    expect(screen.queryByRole('heading', { name: 'Necesidades propuestas para revisar' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sugerir necesidades con esta fuente' })).toBeDisabled()
    expect(screen.getByLabelText(/Autorizo enviar estos metadatos/)).not.toBeChecked()
    expect(goal).toHaveValue(change === 'texto' ? 'Necesidad redactada mientras responde el proveedor.' : '')
  })

  it('no envía metadatos si el proveedor no ofrece un destino comprobable para autorizar', async () => {
    vi.spyOn(api, 'copilotReadiness').mockResolvedValue({ ready: true, source: { ready: true, label: 'Fuente', detail: 'Lista.' }, metadata: { ready: true, label: 'Metadatos', detail: 'Disponibles.' }, llm: { ready: true, label: 'IA', detail: 'Proveedor sin huella de consentimiento.' } })
    const suggest = vi.spyOn(api, 'suggestNeeds')
    await openNeedAssistant()
    expect(screen.getByLabelText(/Autorizo enviar estos metadatos/)).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Sugerir necesidades con esta fuente' }))
    expect(suggest).not.toHaveBeenCalled()
    expect(screen.getByText(/Compruebe la configuración del proveedor/)).toBeInTheDocument()
  })

  it('no presenta en una fuente la sugerencia pendiente de otra', async () => {
    let finish!: (value: Awaited<ReturnType<typeof api.suggestNeeds>>) => void
    const suggest = vi.spyOn(api, 'suggestNeeds').mockImplementationOnce(() => new Promise((resolve) => { finish = resolve })).mockResolvedValue({ ...groundedSuggestions, metadata_snapshot_id: 5 })
    await openNeedAssistant()
    fireEvent.click(screen.getByLabelText(/Autorizo enviar estos metadatos/))
    fireEvent.click(screen.getByRole('button', { name: 'Sugerir necesidades con esta fuente' }))
    fireEvent.change(screen.getByLabelText('Cambiar fuente'), { target: { value: '2' } })
    fireEvent.click(await screen.findByRole('button', { name: 'Crear propuesta' }))
    await act(async () => { finish(groundedSuggestions) })
    expect(screen.queryByRole('heading', { name: 'Necesidades propuestas para revisar' })).not.toBeInTheDocument()
    expect(screen.getByLabelText(/Autorizo enviar estos metadatos/)).not.toBeChecked()
    fireEvent.click(screen.getByLabelText(/Autorizo enviar estos metadatos/))
    fireEvent.click(screen.getByRole('button', { name: 'Sugerir necesidades con esta fuente' }))
    expect(await screen.findByRole('heading', { name: 'Necesidades propuestas para revisar' })).toBeInTheDocument()
    expect(suggest).toHaveBeenLastCalledWith('test-token', { metadata_snapshot_id: 5, domain_code: 'ventas', periodicity: 'month', business_questions: [], metadata_consent_target: 'approved-target' })
  })

  it('impide usar redacciones no respaldadas y descarta una viabilidad anterior al editar', async () => {
    vi.spyOn(api, 'formulateNeed').mockResolvedValue({ original_goal: 'Comparar ventas mensuales para decidir prioridades.', suggested_goal: 'Comparar ventas y cobros mensuales.', rationale: 'Cobros no demostrados.', improvements: [], evidence: ['Comercial.Detalle.Importe'], limitations: ['No se comprobó una fuente de cobros.'], usable: false, provider_kind: 'anthropic', model_id: 'modelo-prueba' })
    let finish!: (value: Awaited<ReturnType<typeof api.validateNeed>>) => void
    vi.spyOn(api, 'validateNeed').mockImplementation(() => new Promise((resolve) => { finish = resolve }))
    const goal = await openNeedAssistant()
    fireEvent.change(goal, { target: { value: 'Comparar ventas mensuales para decidir prioridades.' } })
    fireEvent.click(screen.getByLabelText(/Evolución de ventas/))
    fireEvent.click(screen.getByLabelText(/Autorizo enviar estos metadatos/))
    fireEvent.click(screen.getByRole('button', { name: 'Ayúdame a formular la necesidad' }))
    expect(await screen.findByRole('heading', { name: 'Redacción propuesta' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Usar esta redacción' })).toBeDisabled()
    expect(screen.getByText('No se comprobó una fuente de cobros.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Mantener mi redacción' }))
    fireEvent.click(screen.getByRole('button', { name: 'Validar viabilidad' }))
    fireEvent.change(goal, { target: { value: 'Analizar las ventas por producto y territorio ahora.' } })
    await act(async () => { finish({ assessment_hash: 'old', requirements: [], counts: {}, requires_acknowledgement: [], can_continue: true, summary: 'Respuesta obsoleta.' }) })
    expect(screen.queryByText('Respuesta obsoleta.')).not.toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Viabilidad contra los metadatos' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Validar viabilidad' })).toBeDisabled()
  })

  it('distingue interpretaciones IA de reglas controladas y no da autoridad a fórmulas rechazadas', async () => {
    vi.spyOn(api, 'validateNeed').mockResolvedValue({
      assessment_hash: 'd'.repeat(64),
      requirements: [
        { code: 'ai:0', label: 'Importe sugerido', request_text: 'Importe', status: 'direct', evidence: ['Comercial.Detalle.Importe'], resolution: 'La referencia existe; su significado financiero requiere revisión.' },
        { code: 'ai:1', label: 'Descuento candidato', request_text: 'Descuento', status: 'derivable', evidence: [], formula: 'precio × tasa × cantidad', resolution: 'Operandos estructurales comprobados.' },
        { code: 'ai:2', label: 'Costo rechazado', request_text: 'Costo', status: 'unavailable', evidence: ['Comercial.Detalle.UnitPrice'], formula: 'precio de venta como costo', resolution: 'Precio de venta no acredita costo.' },
        { code: 'goal:sales_amount', label: 'Importe determinístico', request_text: 'Importe', status: 'direct', evidence: ['Comercial.Detalle.Importe'], resolution: 'Referencia verificada por reglas.' },
        { code: 'goal:discount_amount', label: 'Descuento determinístico', request_text: 'Descuento', status: 'derivable', evidence: [], formula: 'precio × tasa × cantidad', resolution: 'Receta controlada disponible.' },
      ],
      counts: { direct: 2, derivable: 2, ambiguous: 0, unavailable: 1 },
      requires_acknowledgement: ['ai:2'], can_continue: true,
      summary: 'Revise la interpretación antes de continuar.',
    })
    const goal = await openNeedAssistant()
    fireEvent.change(goal, { target: { value: 'Analizar el importe de ventas mensual con revisión supervisada.' } })
    fireEvent.click(screen.getByLabelText(/Evolución de ventas/))
    fireEvent.click(screen.getByLabelText(/Autorizo enviar estos metadatos/))
    fireEvent.click(screen.getByRole('button', { name: 'Validar viabilidad' }))
    await screen.findByRole('heading', { name: 'Viabilidad contra los metadatos' })

    const aiDirect = within(screen.getByRole('heading', { name: 'Importe sugerido' }).closest('article')!)
    expect(aiDirect.getByText('Referencia estructural comprobada')).toBeInTheDocument()
    expect(aiDirect.queryByText('Directo · fuente verificada')).not.toBeInTheDocument()
    const candidate = within(screen.getByRole('heading', { name: 'Descuento candidato' }).closest('article')!)
    expect(candidate.getByText('Derivación candidata')).toBeInTheDocument()
    expect(candidate.getByText('Interpretación propuesta por IA (no ejecutable):')).toBeInTheDocument()
    expect(candidate.getByText('Se validará al preparar la propuesta; esta descripción no se ejecuta.')).toBeInTheDocument()
    expect(candidate.queryByText('Fórmula controlada:')).not.toBeInTheDocument()
    const rejected = within(screen.getByRole('heading', { name: 'Costo rechazado' }).closest('article')!)
    expect(rejected.getByText('No disponible')).toBeInTheDocument()
    expect(rejected.getByText('Interpretación propuesta por IA (no ejecutable):')).toBeInTheDocument()
    expect(rejected.queryByText('Fórmula controlada:')).not.toBeInTheDocument()
    expect(rejected.queryByText(/Se resolverá/)).not.toBeInTheDocument()
    expect(rejected.getByRole('checkbox')).not.toBeChecked()
    const controlled = within(screen.getByRole('heading', { name: 'Descuento determinístico' }).closest('article')!)
    expect(controlled.getByText('Automático · fórmula')).toBeInTheDocument()
    expect(controlled.getByText('Fórmula controlada:')).toBeInTheDocument()
    expect(controlled.getByText('✓ Se resolverá y volverá a validar al generar la propuesta.')).toBeInTheDocument()
    expect(screen.getByText('Directo · fuente verificada')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Generar propuesta y resolver 2 derivables' })).toBeDisabled()
  })

  it('permite retirar un rol inactivo previamente asignado sin ofrecerlo a cuentas nuevas', () => {
    const roles = [
      { id: 1, code: 'administrator', name: 'Administrador', description: 'Rol inicial.', is_active: true, permissions: [] },
      { id: 2, code: 'operator', name: 'Operador', description: 'Consulta.', is_active: false, permissions: [] },
    ]

    expect(roleChoicesForUserAssignment(roles).map((role) => role.label)).toEqual(['Administrador'])
    expect(roleChoicesForUserAssignment(roles, [roles[1].id]).map((role) => role.label)).toEqual(['Administrador', 'Operador (inactivo)'])
  })

  it('clasifica una sesión vencida y conserva sólo un borrador recuperable', async () => {
    const expired = vi.fn()
    window.addEventListener(sessionExpiredEvent, expired)
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: false,
      status: 401,
      json: async () => ({ detail: 'Token vencido' }),
    })))

    await expect(api.copilotReadiness('expired-token')).rejects.toThrow(/sesión venció/i)
    expect(expired).toHaveBeenCalledOnce()

    localStorage.setItem('bi_ia_assistant_draft_v2', JSON.stringify({
      version: 2,
      sourceId: 7,
      domainCode: 'ventas',
      step: 3,
      goal: 'Analizar ventas y margen por producto.',
      questions: ['top_products'],
      periodicity: 'month',
      proposalId: 54,
      credential: 'no-debe-restaurarse',
    }))
    expect(readAssistantDraft()).toEqual({
      version: 2,
      sourceId: 7,
      domainCode: 'ventas',
      step: 3,
      goal: 'Analizar ventas y margen por producto.',
      questions: ['top_products'],
      periodicity: 'month',
      proposalId: 54,
    })
    window.removeEventListener(sessionExpiredEvent, expired)
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
    const security = await screen.findByRole('button', { name: 'Administración y seguridad' })
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

  it('mantiene en Inicio la fuente seleccionada y consulta su preparación explícita', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    localStorage.setItem('bi_ia_source_context', '2')
    const sources = [
      ...sourceWorkspace({ id: 2, data_connection_id: 1, content_hash: 'a'.repeat(64) }),
      {
        status: 'ready',
        connection: { ...sourceConnection, id: 2, name: 'WideWorldImporters local', database_name: 'WideWorldImporters' },
        latest_snapshot: { id: 3, data_connection_id: 2, content_hash: 'b'.repeat(64) },
      },
    ]
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/auth/me')) return {
        ok: true, status: 200, json: async () => ({
          user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
          permissions: ['copilot.proposals.read'],
          menus: [{ id: 1, code: 'home', label: 'Inicio', path: '/', position: 0, module_code: 'home', module_label: 'Inicio', is_active: true, permissions: [] }],
        }),
      }
      if (url.endsWith('/sources')) return { ok: true, status: 200, json: async () => sources }
      if (url.includes('/copilot/readiness?connection_id=')) {
        const isWideWorld = url.endsWith('connection_id=2')
        const name = isWideWorld ? 'WideWorldImporters local' : 'Fuente comercial de prueba'
        return { ok: true, status: 200, json: async () => ({
          ready: true,
          source: { ready: true, label: 'Fuente de ventas', detail: `${name} está habilitada y probada.` },
          metadata: { ready: true, label: 'Metadatos', detail: `Instantánea ${isWideWorld ? 'bbbbbbbbbbbb' : 'aaaaaaaaaaaa'} disponible.` },
          llm: { ready: true, label: 'Asistente de IA', detail: 'Proveedor listo.' },
        }) }
      }
      throw new Error(`Solicitud inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    const sourceSelector = await screen.findByLabelText('Cambiar fuente')
    expect(sourceSelector).toHaveValue('2')
    expect(await screen.findByText('WideWorldImporters local está habilitada y probada.')).toBeInTheDocument()

    fireEvent.change(sourceSelector, { target: { value: '1' } })

    expect(await screen.findByText('Fuente comercial de prueba está habilitada y probada.')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/copilot/readiness?connection_id=1'),
      expect.anything(),
    )
  })

  it('reinicia el explorador al cambiar de fuente y siempre muestra la versión de metadatos', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const snapshot = (id: number, connectionId: number, databaseName: string, hash: string) => ({
      id, data_connection_id: connectionId, connector_code: 'sqlserver', database_name: databaseName,
      contract_version: 1, content_hash: hash.repeat(64), schema_count: 1, table_count: 1,
      column_count: 2, relationship_count: 0, captured_by_label: 'Administradora', captured_at: '2026-10-01T09:00:00Z',
    })
    const awSnapshot = snapshot(2, 1, 'BaseComercial', 'a')
    const wwiSnapshot = snapshot(3, 2, 'WideWorldImporters', 'b')
    const sources = [
      ...sourceWorkspace(awSnapshot),
      { status: 'ready', connection: { ...sourceConnection, id: 2, name: 'WideWorldImporters local', database_name: 'WideWorldImporters' }, latest_snapshot: wwiSnapshot },
    ]
    let resolveOldDetail: ((response: { ok: boolean; status: number; json: () => Promise<object> }) => void) | undefined
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/auth/me')) return {
        ok: true, status: 200, json: async () => ({
          user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
          permissions: ['metadata.read'],
          menus: [{ id: 2, code: 'schema', label: 'Explorador de esquema', path: '/esquema', position: 1, module_code: 'parameters', module_label: 'Preparación del entorno', is_active: true, permissions: [] }],
        }),
      }
      if (url.endsWith('/sources')) return { ok: true, status: 200, json: async () => sources }
      if (url.includes('/metadata/snapshots?') && url.includes('connection_id=1')) return { ok: true, status: 200, json: async () => ({ items: [awSnapshot], total: 1, limit: 10, offset: 0 }) }
      if (url.includes('/metadata/snapshots?') && url.includes('connection_id=2')) return { ok: true, status: 200, json: async () => ({ items: [wwiSnapshot], total: 1, limit: 10, offset: 0 }) }
      if (url.includes('/metadata/snapshots/2/tables?')) return { ok: true, status: 200, json: async () => ({ items: [{ schema_name: 'HumanResources', table_name: 'Department', column_count: 2, relationship_count: 0 }], total: 1, limit: 10, offset: 0 }) }
      if (url.endsWith('/metadata/snapshots/2/tables/HumanResources/Department')) return new Promise((resolve) => { resolveOldDetail = resolve })
      if (url.includes('/metadata/snapshots/3/tables?')) return { ok: true, status: 200, json: async () => ({ items: [{ schema_name: 'Application', table_name: 'Cities', column_count: 2, relationship_count: 0 }], total: 1, limit: 10, offset: 0 }) }
      if (url.endsWith('/metadata/snapshots/3/tables/Application/Cities')) return { ok: true, status: 200, json: async () => ({ schema_name: 'Application', table_name: 'Cities', columns: [{ name: 'CityID', ordinal: 1, data_type: 'int', max_length: 4, nullable: false, primary_key: true }], foreign_keys: [], incoming_relationships: [] }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Preparación del entorno' }))
    fireEvent.click(screen.getByRole('button', { name: 'Explorador de esquema' }))

    expect(await screen.findByText('Department')).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /Versión de metadatos/ })).toBeDisabled()
    fireEvent.change(screen.getByLabelText('Cambiar fuente'), { target: { value: '2' } })

    expect(await screen.findByRole('heading', { name: 'Cities' })).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /Versión de metadatos/ })).toHaveValue('3')
    expect(screen.getByRole('combobox', { name: /Versión de metadatos/ })).toBeDisabled()
    resolveOldDetail?.({ ok: false, status: 404, json: async () => ({ detail: 'Tabla no encontrada en la instantánea.' }) })
    await waitFor(() => expect(screen.queryByText('Tabla no encontrada en la instantánea.')).not.toBeInTheDocument())
    expect(screen.queryByText('Department')).not.toBeInTheDocument()
  })

  it('no interpreta la respuesta de Roles como instantáneas al navegar al explorador', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const snapshot = {
      id: 2, data_connection_id: 1, connector_code: 'sqlserver', database_name: 'BaseComercial',
      contract_version: 1, content_hash: 'a'.repeat(64), schema_count: 1, table_count: 1,
      column_count: 2, relationship_count: 0, captured_by_label: 'Administradora', captured_at: '2026-10-01T09:00:00Z',
    }
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/auth/me')) return { ok: true, status: 200, json: async () => ({
        user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
        permissions: ['roles.read', 'metadata.read'],
        menus: [
          { id: 1, code: 'roles', label: 'Roles', path: '/roles', position: 1, module_code: 'security', module_label: 'Seguridad', is_active: true, permissions: [] },
          { id: 2, code: 'schema', label: 'Explorador de esquema', path: '/esquema', position: 2, module_code: 'parameters', module_label: 'Preparación del entorno', is_active: true, permissions: [] },
        ],
      }) }
      if (url.endsWith('/sources')) return { ok: true, status: 200, json: async () => sourceWorkspace(snapshot) }
      if (url.includes('/roles?')) return { ok: true, status: 200, json: async () => ({ items: [
        { id: 3, code: 'bi_analyst', name: 'Analista BI', description: 'Diseña modelos.', is_active: true, permissions: [] },
      ], total: 1, limit: 10, offset: 0 }) }
      if (url.includes('/metadata/snapshots?')) return { ok: true, status: 200, json: async () => ({ items: [snapshot], total: 1, limit: 10, offset: 0 }) }
      if (url.includes('/metadata/snapshots/2/tables?')) return { ok: true, status: 200, json: async () => ({ items: [], total: 0, limit: 10, offset: 0 }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    }))

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Administración y seguridad' }))
    fireEvent.click(screen.getByRole('button', { name: 'Roles' }))
    expect(await screen.findByText('Analista BI')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Preparación del entorno' }))
    fireEvent.click(screen.getByRole('button', { name: 'Explorador de esquema' }))

    expect(await screen.findByText(/Instantánea #2/)).toBeInTheDocument()
    expect(screen.queryByText(/El expediente sigue seguro/)).not.toBeInTheDocument()
  })

  it('ordena la navegación por flujo profesional sin ampliar las opciones autorizadas', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      json: async () => ({
        user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
        permissions: [],
        menus: [
          { id: 1, code: 'home', label: 'Inicio', path: '/', position: 0, module_code: 'home', module_label: 'Inicio', is_active: true, permissions: [] },
          { id: 2, code: 'users', label: 'Usuarios', path: '/usuarios', position: 10, module_code: 'security', module_label: 'Seguridad', is_active: true, permissions: [] },
          { id: 3, code: 'analytics', label: 'Analítica de ventas', path: '/analitica-ventas', position: 30, module_code: 'analytics', module_label: 'Análisis', is_active: true, permissions: [] },
          { id: 4, code: 'assistant', label: 'Asistente de datamart', path: '/asistente', position: 10, module_code: 'ai', module_label: 'IA', is_active: true, permissions: [] },
          { id: 5, code: 'connections', label: 'Conexiones de datos', path: '/conexiones', position: 65, module_code: 'parameters', module_label: 'Parámetros generales', is_active: true, permissions: [] },
        ],
      }),
    })))

    render(<App />)

    const categoryNames = [
      'Preparación del entorno',
      'Diseño y transformación BI',
      'Análisis y decisiones',
      'Administración y seguridad',
    ]
    const categories = await Promise.all(categoryNames.map((name) => screen.findByRole('button', { name })))
    expect(categories.map((item) => item.textContent?.replace('›', '').trim())).toEqual(categoryNames)
    for (let index = 1; index < categories.length; index += 1) {
      expect(categories[index - 1].compareDocumentPosition(categories[index]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    }
    expect(document.querySelectorAll('#main-navigation .navigation-icon').length).toBeGreaterThanOrEqual(5)
    expect(screen.queryByRole('button', { name: 'Roles' })).not.toBeInTheDocument()
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
          items: [{ id: 7, name: 'Gemini tesis', provider_kind: 'gemini', base_url: 'https://generativelanguage.googleapis.com', model_id: 'gemini-3.6-flash', reasoning_level: 'minimal', credential_configured: false, is_active: false }],
          total: 1,
          limit: 10,
          offset: 0,
        }),
      }
      throw new Error(`Solicitud inesperada: ${url} ${init?.method ?? 'GET'}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    fireEvent.click(await screen.findByRole('button', { name: 'Preparación del entorno' }))
    fireEvent.click(screen.getByRole('button', { name: 'Configuración LLM' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Editar' }))
    expect(screen.getByLabelText('Nivel de razonamiento')).toHaveValue('minimal')
    fireEvent.change(screen.getByLabelText('Nivel de razonamiento'), { target: { value: 'medium' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    await screen.findByRole('heading', { name: 'Crear configuración LLM' })
    const configurationRequest = fetchMock.mock.calls.find(([, init]) => init?.method === 'PUT')
    expect(JSON.parse(String(configurationRequest?.[1]?.body))).toMatchObject({ reasoning_level: 'medium' })
    fireEvent.click(await screen.findByRole('button', { name: 'Registrar credencial' }))
    fireEvent.change(screen.getByLabelText('API key'), { target: { value: 'gemini-key-de-prueba' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar credencial' }))

    expect(await screen.findByText('Credencial protegida correctamente.')).toBeInTheDocument()
    const secretRequest = fetchMock.mock.calls.find(([input]) => String(input).includes('/llm-configurations/7/secret'))
    expect(secretRequest?.[1]?.body).toBe(JSON.stringify({ api_key: 'gemini-key-de-prueba' }))
    expect(screen.queryByDisplayValue('gemini-key-de-prueba')).not.toBeInTheDocument()
  })

  it('preconfigura Groq Cloud con GPT-OSS 120B sin exponer la credencial', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/auth/me')) return { ok: true, status: 200, json: async () => ({
        user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
        permissions: ['parameters.llm.write'],
        menus: [{ id: 1, code: 'llm', label: 'Configuración LLM', path: '/llm', position: 60, module_code: 'parameters', module_label: 'Parámetros generales', is_active: true, permissions: [] }],
      }) }
      if (url.includes('/llm-configurations') && init?.method === 'POST') return { ok: true, status: 201, json: async () => ({ id: 8 }) }
      if (url.includes('/llm-configurations')) return { ok: true, status: 200, json: async () => ({ items: [], total: 0, limit: 10, offset: 0 }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Preparación del entorno' }))
    fireEvent.click(screen.getByRole('button', { name: 'Configuración LLM' }))
    fireEvent.change(await screen.findByLabelText('Nombre de configuración'), { target: { value: 'Groq para análisis BI' } })
    fireEvent.change(screen.getByLabelText('Proveedor'), { target: { value: 'groq-cloud' } })

    expect(screen.getByLabelText('URL del servicio')).toHaveValue('https://api.groq.com/openai/v1')
    expect(screen.getByLabelText('Modelo')).toHaveValue('openai/gpt-oss-120b')
    expect(screen.getByLabelText('Nivel de razonamiento')).toHaveValue('low')
    expect(screen.getByRole('option', { name: 'Medio — análisis equilibrado' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Alto — mayor tiempo y consumo' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Crear registro' }))

    await waitFor(() => expect(fetchMock.mock.calls.some(([input, init]) => String(input).includes('/llm-configurations') && init?.method === 'POST')).toBe(true))
    const request = fetchMock.mock.calls.find(([input, init]) => String(input).includes('/llm-configurations') && init?.method === 'POST')
    expect(JSON.parse(String(request?.[1]?.body))).toMatchObject({
      provider_kind: 'groq-cloud',
      base_url: 'https://api.groq.com/openai/v1',
      model_id: 'openai/gpt-oss-120b',
      reasoning_level: 'low',
      is_active: false,
    })
  })

  it('preconfigura Anthropic Claude con Haiku 4.5 y nivel mínimo', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/auth/me')) return { ok: true, status: 200, json: async () => ({
        user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
        permissions: ['parameters.llm.write'],
        menus: [{ id: 1, code: 'llm', label: 'Configuración LLM', path: '/llm', position: 60, module_code: 'parameters', module_label: 'Parámetros generales', is_active: true, permissions: [] }],
      }) }
      if (url.includes('/llm-configurations') && init?.method === 'POST') return { ok: true, status: 201, json: async () => ({ id: 9 }) }
      if (url.includes('/llm-configurations')) return { ok: true, status: 200, json: async () => ({ items: [], total: 0, limit: 10, offset: 0 }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Preparación del entorno' }))
    fireEvent.click(screen.getByRole('button', { name: 'Configuración LLM' }))
    fireEvent.change(await screen.findByLabelText('Nombre de configuración'), { target: { value: 'Claude Haiku económico' } })
    fireEvent.change(screen.getByLabelText('Proveedor'), { target: { value: 'anthropic-cloud' } })

    expect(screen.getByLabelText('URL del servicio')).toHaveValue('https://api.anthropic.com')
    expect(screen.getByLabelText('Modelo')).toHaveValue('claude-haiku-4-5-20251001')
    expect(screen.getByLabelText('Nivel de razonamiento')).toHaveValue('minimal')
    expect(screen.queryByRole('option', { name: 'Medio — análisis equilibrado' })).not.toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'Alto — mayor tiempo y consumo' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Crear registro' }))

    await waitFor(() => expect(fetchMock.mock.calls.some(([input, init]) => String(input).includes('/llm-configurations') && init?.method === 'POST')).toBe(true))
    const request = fetchMock.mock.calls.find(([input, init]) => String(input).includes('/llm-configurations') && init?.method === 'POST')
    expect(JSON.parse(String(request?.[1]?.body))).toMatchObject({
      provider_kind: 'anthropic-cloud',
      base_url: 'https://api.anthropic.com',
      model_id: 'claude-haiku-4-5-20251001',
      reasoning_level: 'minimal',
      is_active: false,
    })
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
    fireEvent.click(await screen.findByRole('button', { name: 'Preparación del entorno' }))
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

  it('administra preguntas y periodicidades por dominio sin predefinir dimensiones', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const catalog = {
      version: 2,
      domain_code: 'ventas',
      questions: [{ code: 'sales_over_time', label: 'Evolución de ventas', description: 'Compara el comportamiento comercial entre períodos.', prompt_instruction: 'Identifique tendencias verificables sin inventar referencias técnicas.', enabled: true }],
      periodicities: [{ code: 'month', label: 'Mensual', description: 'Agrupa los resultados comerciales por cada mes.', enabled: true }],
    }
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/auth/me')) return {
        ok: true, status: 200, json: async () => ({
          user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
          permissions: ['copilot.catalog.read', 'copilot.catalog.write'],
          menus: [{ id: 12, code: 'analysis-catalog', label: 'Catálogo analítico', path: '/catalogo-analitico', position: 5, module_code: 'ai', module_label: 'IA', is_active: true, permissions: [] }],
        }),
      }
      if (url.endsWith('/sources')) return { ok: true, status: 200, json: async () => sourceWorkspace({ id: 8, data_connection_id: 1, connector_code: 'sqlserver', database_name: 'BaseComercial', contract_version: 1, content_hash: 'c'.repeat(64), schema_count: 4, table_count: 20, column_count: 140, relationship_count: 22, captured_by_label: 'Administradora', captured_at: '2026-10-01T09:00:00Z' }) }
      if (url.endsWith('/analysis-catalog/domains')) return { ok: true, status: 200, json: async () => [{ code: 'ventas', label: 'Datamart de ventas', description: 'Modelo comercial.', enabled: true, implementation_status: 'implemented' }] }
      if (url.includes('/copilot/catalog?')) return { ok: true, status: 200, json: async () => ({ metadata_snapshot_id: 8, domains: [{ code: 'ventas', label: 'Datamart de ventas', description: 'Modelo comercial.', available: true, reason: 'Existe evidencia suficiente.', questions: [{ code: 'sales_over_time', label: 'Evolución de ventas', description: 'Compara períodos.', available: true, reason: 'Fecha comercial y medida verificadas.', evidence: ['Comercial.Pedidos', 'Comercial.DetallePedido'] }], periodicities: [{ code: 'month', label: 'Mensual', description: 'Agrupación mensual.', available: true, reason: 'Fecha verificable.', evidence: ['Comercial.Pedidos.FechaPedido'] }] }] }) }
      if (url.includes('/analysis-catalog/domains/ventas?') && init?.method === 'PUT') return { ok: true, status: 200, json: async () => JSON.parse(String(init.body)) }
      if (url.includes('/analysis-catalog/domains/ventas?')) return { ok: true, status: 200, json: async () => catalog }
      throw new Error(`Solicitud inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Diseño y transformación BI' }))
    fireEvent.click(screen.getByRole('button', { name: 'Catálogo analítico' }))
    expect(await screen.findByText('Identificador interno: sales_over_time')).toBeInTheDocument()
    expect(screen.getByText('Cobertura técnica de la fuente')).toBeInTheDocument()
    expect(screen.getByText('Comercial.Pedidos')).toBeInTheDocument()
    expect(screen.getByText(/nunca se copia desde otra base de datos/i)).toBeInTheDocument()
    expect(screen.queryByText(/Dimensiones de interés/i)).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/Objetivo del análisis/i)).not.toBeInTheDocument()
    fireEvent.change(screen.getAllByLabelText('Etiqueta')[0], { target: { value: 'Tendencia comercial mensual' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar catálogo' }))

    expect(await screen.findByText(/catálogo analítico fue actualizado/i)).toBeInTheDocument()
    const updateRequest = fetchMock.mock.calls.find(([input, init]) => String(input).includes('/analysis-catalog/domains/ventas?') && init?.method === 'PUT')
    const saved = JSON.parse(String(updateRequest?.[1]?.body)) as typeof catalog
    expect(saved.questions[0]).toMatchObject({ code: 'sales_over_time', label: 'Tendencia comercial mensual' })
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
    fireEvent.click(await screen.findByRole('button', { name: 'Preparación del entorno' }))
    fireEvent.click(screen.getByRole('button', { name: 'Conexiones de datos' }))

    expect(await screen.findByText('Sólo lectura validada')).toBeInTheDocument()
    expect(screen.getByText('Habilitada')).toBeInTheDocument()
    expect(screen.queryByText(/password|contraseña guardada/i)).not.toBeInTheDocument()
  })

  it('explora una instantánea sin consultar filas ni mostrar credenciales', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const snapshot = { id: 4, data_connection_id: 1, connector_code: 'sqlserver', database_name: 'AdventureWorks2022', contract_version: 1, content_hash: 'a'.repeat(64), schema_count: 6, table_count: 71, column_count: 444, relationship_count: 90, captured_by_label: 'Administradora', captured_at: '2026-09-18T20:00:00Z' }
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/auth/me')) return {
        ok: true, status: 200, json: async () => ({
          user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] },
          permissions: ['metadata.read', 'metadata.refresh'],
          menus: [{ id: 10, code: 'schema-explorer', label: 'Explorador de esquema', path: '/esquema', position: 10, module_code: 'data', module_label: 'Datos', is_active: true, permissions: [] }],
        }),
      }
      if (url.endsWith('/sources')) return {
        ok: true, status: 200, json: async () => sourceWorkspace(snapshot),
      }
      if (url.includes('/metadata/snapshots?connection_id=1') && init?.method === 'POST') return {
        ok: true, status: 200, json: async () => ({ created: false, message: 'La estructura no cambió; se mantiene la instantánea vigente.', snapshot }),
      }
      if (url.includes('/metadata/snapshots/4/tables/Sales/SalesOrderHeader')) return {
        ok: true, status: 200, json: async () => ({ schema_name: 'Sales', table_name: 'SalesOrderHeader', columns: [{ name: 'SalesOrderID', ordinal: 1, data_type: 'int', max_length: 4, precision: 10, scale: 0, nullable: false, primary_key: true }], foreign_keys: [{ name: 'FK_Customer', columns: ['CustomerID'], referenced_schema: 'Sales', referenced_table: 'Customer', referenced_columns: ['CustomerID'] }], incoming_relationships: [] }),
      }
      if (url.includes('/metadata/snapshots/4/tables?')) return {
        ok: true, status: 200, json: async () => ({ items: [{ schema_name: 'Sales', table_name: 'SalesOrderHeader', column_count: 9, relationship_count: 3 }], total: 1, limit: 10, offset: 0 }),
      }
      if (url.includes('/metadata/snapshots')) return {
        ok: true, status: 200, json: async () => ({ items: [snapshot], total: 1, limit: 10, offset: 0 }),
      }
      throw new Error(`Solicitud inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Preparación del entorno' }))
    fireEvent.click(screen.getByRole('button', { name: 'Explorador de esquema' }))

    expect(await screen.findByText('SalesOrderHeader')).toBeInTheDocument()
    expect(await screen.findByText('SalesOrderID')).toBeInTheDocument()
    expect(screen.getByText('PK')).toBeInTheDocument()
    expect(screen.getByText(/Sales\.Customer/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar metadatos' }))
    expect(await screen.findByText(/La estructura no cambió/)).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([input, init]) => String(input).includes('/metadata/snapshots?connection_id=1') && init?.method === 'POST')).toBe(true)
    expect(screen.queryByText(/contraseña|password/i)).not.toBeInTheDocument()
  })

  it('guía el análisis y distingue la propuesta de la validación', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const proposal = {
      id: 12, metadata_snapshot_id: 4,
      business_goal: 'Analizar las ventas mensuales por producto y cliente.',
      business_questions: ['sales_over_time'], requested_dimensions: ['date', 'product'], periodicity: 'month', domain_code: 'ventas',
      scope_document: { origin: 'semantic-discovery:v1', tables: [{ ref: 'Sales.SalesOrderDetail', columns: [{ name: 'UnitPrice', type: 'money' }, { name: 'UnitPriceDiscount', type: 'money' }, { name: 'OrderQty', type: 'smallint' }] }] },
      semantic_map_document: { candidates: [{ business_concept: 'venta', business_name_es: 'Detalle de venta', description_es: 'Cada registro representa una línea vendida.', technical_refs: ['Sales.SalesOrderDetail'], confidence: 'high', reason: 'Contiene cantidad e importe.', references_validated: true }, { business_concept: 'sales_reason', business_name_es: 'Motivo de venta', description_es: 'Razón asociada al pedido.', technical_refs: ['Sales.SalesReason'], confidence: 'low', reason: 'La relación puede ser opcional o múltiple.', references_validated: true, selected: false, evidence: { status: 'decision_required', recommended_action: 'exclude', guidance: 'Se excluyó preventivamente porque la evidencia semántica es débil.', checks: [{ code: 'reference_exists', passed: true, label: 'Referencia comprobada', detail: 'Sales.SalesReason existe en la instantánea vigente.' }] } }] },
      status: 'ready_for_review', input_hash: 'a'.repeat(64), prompt_version: 'sales-bi-v1', contract_version: 1,
      provider_kind: 'ollama-local', model_id: 'qwen2.5:3b',
      proposal_document: { contract_version: 1, domain: 'ventas', summary: 'Modelo de ventas', business_explanation: 'Una fila por línea vendida.', grain: { description: 'Una fila por línea.' }, fact: { name: 'fact_ventas', measures: [{ name: 'importe_venta', aggregation: 'sum', semantic_role: 'sales_amount', source_columns: ['UnitPrice', 'UnitPriceDiscount', 'OrderQty'], calculation: { operation: 'multiply', inputs: ['UnitPrice', 'UnitPriceDiscount', 'OrderQty'] } }] }, dimensions: [{ name: 'dim_producto', attributes: ['Name'] }, { name: 'dim_cliente', attributes: ['PersonID', 'StoreID', 'AccountNumber'], display_label: { target_name: 'nombre_cliente', type_target_name: 'tipo_cliente', fallback_column: 'AccountNumber', minimum_descriptive_coverage: 0.95, variants: [] } }], kpis: [{ name: 'Ventas totales', code: 'ventas_totales', semantic_role: 'sales_amount' }], etl_plan: [{ operation: 'extract', description: 'Extraer campos aprobados.' }], automatic_adjustments: ['La medida importe_venta se derivará mediante multiply usando exclusivamente columnas verificadas.'], decision_diagnostics: [{ kind: 'kpi', code: 'clientes_activos', status: 'excluded', reason: 'Clientes activos requiere una medida de clientes.', compatible_measures: [] }], ai_decisions: { summary: 'Modelo de ventas', grain_description: 'Una fila por línea vendida.', fact_source: 'Sales.SalesOrderDetail', measures: [{ name: 'importe_venta', source_column: 'UnitPrice', aggregation: 'sum', semantic_role: 'sales_amount', calculation: { operation: 'multiply', inputs: ['UnitPrice', 'UnitPriceDiscount', 'OrderQty'] } }], dimensions: [{ name: 'dim_producto', source_table: 'Production.Product' }], kpis: [{ code: 'ventas_totales', name: 'Ventas totales', measure_index: 0, operation: 'sum', unit: 'moneda', semantic_role: 'sales_amount' }, { code: 'clientes_activos', name: 'Clientes activos', measure_index: 0, operation: 'count_distinct', unit: 'clientes', semantic_role: 'customer_count' }] } },
      validation_document: { valid: true, errors: 0, warnings: 0, issues: [] }, warnings_confirmed: false,
      created_by_label: 'Administradora', created_at: '2026-09-19T10:00:00Z',
    }
    ;(proposal.proposal_document.ai_decisions.measures as Array<Record<string, unknown>>).push({
      name: 'numero_transacciones', source_column: 'SalesOrderID', aggregation: 'count_distinct', semantic_role: 'transaction_count',
    })
    const previousProposal = {
      ...proposal,
      id: 11,
      status: 'approved',
      provider_kind: 'gemini',
      model_id: 'gemini-3.6-flash',
      proposal_document: { ...proposal.proposal_document, summary: 'Modelo Gemini conservado' },
      reviewed_by_label: 'Analista BI',
      reviewed_at: '2026-09-19T09:40:00Z',
      created_at: '2026-09-19T09:30:00Z',
    }
    const revisedProposal = {
      ...proposal,
      id: 13,
      source_proposal_id: 12,
      created_at: '2026-09-19T10:05:00Z',
    }
    const providerFailedProposal = {
      ...proposal,
      id: 14,
      scope_document: {},
      semantic_map_document: { candidates: [] },
      status: 'provider_failed',
      proposal_document: {},
      validation_document: { valid: false, errors: 1, warnings: 0, issues: [{ code: 'provider.structured_contract', level: 'error', path: '$', message: 'Groq generó una respuesta que no cumplió el contrato estructurado. La plataforma la descartó automáticamente sin usarla.' }] },
    }
    let creationAttempts = 0
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/auth/me')) return { ok: true, status: 200, json: async () => ({ user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] }, permissions: ['copilot.proposals.read', 'copilot.proposals.generate', 'copilot.proposals.review'], menus: [{ id: 11, code: 'analysis-assistant', label: 'Asistente de datamart', path: '/asistente', position: 10, module_code: 'ai', module_label: 'IA', is_active: true, permissions: [] }] }) }
      if (url.endsWith('/sources')) return { ok: true, status: 200, json: async () => sourceWorkspace({ id: 4, data_connection_id: 1, connector_code: 'sqlserver', database_name: 'BaseComercial', contract_version: 1, content_hash: 'b'.repeat(64), schema_count: 6, table_count: 71, column_count: 444, relationship_count: 90, captured_by_label: 'Administradora', captured_at: '2026-09-19T09:00:00Z' }) }
      if (url.includes('/copilot/readiness?')) return { ok: true, status: 200, json: async () => ({ ready: true, source: { ready: true, label: 'Fuente de ventas', detail: 'Fuente habilitada.' }, metadata: { ready: true, label: 'Metadatos', detail: 'Instantánea disponible.' }, llm: { ready: true, label: 'Asistente de IA', detail: 'Proveedor listo.', metadata_consent_target: 'approved-target' } }) }
      if (url.includes('/copilot/catalog?')) return { ok: true, status: 200, json: async () => ({ metadata_snapshot_id: 4, domains: [{ code: 'ventas', label: 'Datamart de ventas', description: 'Modelo dimensional comercial.', available: true, reason: 'La fuente permite iniciar una propuesta.', questions: [{ code: 'sales_over_time', label: 'Evolución de ventas en el tiempo', description: 'Compara períodos.', available: true, reason: 'Disponible.', evidence: ['Sales.SalesOrderHeader'] }, { code: 'top_products', label: 'Productos con mayor desempeño', description: 'Compara productos.', available: true, reason: 'Disponible.', evidence: ['Production.Product'] }], periodicities: [{ code: 'month', label: 'Mensual', description: 'Agrupación mensual.', available: true, reason: 'Disponible.', evidence: ['Sales.SalesOrderHeader'] }] }] }) }
      if (url.endsWith('/copilot/needs/formulate') && init?.method === 'POST') return { ok: true, status: 200, json: async () => ({ original_goal: 'Analizar las ventas mensuales por producto y cliente.', suggested_goal: 'Analizar las ventas netas mensuales por producto y cliente para identificar variaciones.', rationale: 'Hace explícito el indicador y la comparación temporal.', improvements: ['Confirme si venta neta es el indicador esperado.'], provider_kind: 'groq-cloud', model_id: 'openai/gpt-oss-120b' }) }
      if (url.endsWith('/copilot/needs/viability') && init?.method === 'POST') return { ok: true, status: 200, json: async () => ({ assessment_hash: 'd'.repeat(64), requirements: [{ code: 'question:sales_over_time', label: 'Evolución de ventas en el tiempo', request_text: 'Compara períodos.', status: 'derivable', evidence: ['Sales.SalesOrderDetail.LineTotal', 'Sales.SalesOrderHeader.OrderDate', 'Ruta declarada: Sales.SalesOrderDetail → Sales.SalesOrderHeader'], resolution: 'Puede resolverse con relaciones declaradas.' }, { code: 'goal:sales_amount', label: 'Ventas o ingresos', request_text: 'Analizar las ventas mensuales por producto y cliente.', status: 'direct', evidence: ['Sales.SalesOrderDetail.LineTotal'], resolution: 'Puede resolverse directamente.' }, { code: 'goal:definition', label: 'Definición de venta neta', request_text: 'Venta neta', status: 'ambiguous', evidence: ['Sales.SalesOrderDetail.LineTotal', 'Sales.SalesOrderHeader.TotalDue'], resolution: 'Confirme qué componentes incluye la venta neta.' }], counts: { direct: 1, derivable: 1, ambiguous: 1, unavailable: 0 }, requires_acknowledgement: ['goal:definition'], can_continue: true, summary: 'La necesidad tiene respaldo suficiente para continuar, con decisiones pendientes.' }) }
      if (url.endsWith('/copilot/proposals/14')) return { ok: true, status: 200, json: async () => providerFailedProposal }
      if (url.endsWith('/copilot/proposals/12/relation-options')) return { ok: true, status: 200, json: async () => ({ proposal_id: 12, dimension_names: ['dim_producto'], options: [{ option_id: 'r'.repeat(64), left_table: 'Sales.SalesOrderDetail', right_table: 'Production.Product', left_columns: ['ProductID'], right_columns: ['ProductID'], left_types: ['int'], right_types: ['int'], cardinality: 'many_to_one', target_unique: true, nullable_source: false, duplication_risk: false, eligible: true, guidance: 'Relación declarada hacia una clave única; conserva la granularidad.' }, { option_id: 'x'.repeat(64), left_table: 'Sales.SalesOrderDetail', right_table: 'Sales.SpecialOfferProduct', left_columns: ['ProductID'], right_columns: ['ProductID'], left_types: ['int'], right_types: ['int'], cardinality: 'unknown', target_unique: false, nullable_source: false, duplication_risk: true, eligible: false, guidance: 'No se puede seleccionar: la clave destino no es única.' }] }) }
      if (url.endsWith('/copilot/proposals/12/revisions') && init?.method === 'POST') return { ok: true, status: 201, json: async () => revisedProposal }
      if (url.endsWith('/copilot/proposals/11/verify') && init?.method === 'POST') return { ok: true, status: 200, json: async () => ({ proposal_id: 11, verified: false, approval_safe: true, compatibility_warning: true, approval_invalidated: true, checks: [{ code: 'snapshot.integrity', label: 'Integridad de los metadatos', passed: true, detail: 'La huella coincide con la instantánea estructural persistida.' }, { code: 'proposal.replay', label: 'Reproducción determinística del contrato', passed: false, detail: 'La reconstrucción actual difiere de la huella persistida.' }], snapshot_hash: 'b'.repeat(64), proposal_hash: 'c'.repeat(64), replay_hash: 'd'.repeat(64), validated_reference_count: 1, rejected_reference_count: 0, validation_errors: 0, validation_warnings: 0, pending_validations: ['Contraste de cifras después de materializar el datamart.'] }) }
      if (url.endsWith('/copilot/proposals/11/invalidate') && init?.method === 'POST') return { ok: true, status: 200, json: async () => ({ ...previousProposal, status: 'invalidated', review_comment: 'La versión contiene una asociación semántica que debe corregirse.' }) }
      if (url.includes('/copilot/proposals/12/semantic-advice?')) return { ok: true, status: 200, json: async () => [] }
      if (url.endsWith('/copilot/proposals/12/semantic-advice') && init?.method === 'POST') return { ok: true, status: 201, json: async () => ({ id: 1, proposal_id: 12, concept_code: 'sales_reason', question: '¿Qué riesgo tendría incluir este concepto en el datamart?', response_document: { conclusion: 'exclude', answer_es: 'Puede existir más de un motivo por pedido.', evidence: [{ technical_ref: 'Sales.SalesReason', detail_es: 'La referencia existe y requiere una relación intermedia.' }], risk_es: 'Podría multiplicar las ventas.', include_consequence_es: 'Requiere una tabla puente.', exclude_consequence_es: 'No se analizarán motivos.', recommended_action_es: 'Mantener excluido salvo necesidad expresa.', confidence: 'medium', selection_changed: false }, provider_kind: 'groq-cloud', model_id: 'openai/gpt-oss-120b', created_by_label: 'Administradora', created_at: '2026-09-23T10:00:00Z' }) }
      if (url.includes('/copilot/proposals') && init?.method === 'POST') {
        creationAttempts += 1
        return { ok: true, status: 201, json: async () => creationAttempts === 1 ? providerFailedProposal : proposal }
      }
      if (url.includes('/copilot/proposals')) return { ok: true, status: 200, json: async () => ({ items: [previousProposal], total: 6, limit: 5, offset: 0 }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Diseño y transformación BI' }))
    fireEvent.click(screen.getByRole('button', { name: 'Asistente de datamart' }))
    expect(await screen.findByText('Dominio habilitado')).toBeInTheDocument()
    fireEvent.click(await screen.findByRole('button', { name: 'Crear propuesta' }))
    expect(await screen.findByText('Mostrando 1-5 de 6 registros')).toBeInTheDocument()
    const needTextarea = screen.getByLabelText(/^Objetivo del análisis/)
    expect(needTextarea).toHaveAttribute('rows', '12')
    expect(needTextarea).toHaveAttribute('maxlength', '2000')
    fireEvent.change(needTextarea, { target: { value: 'Analizar las ventas mensuales por producto y cliente.' } })
    await waitFor(() => expect(readAssistantDraft()?.goal).toBe('Analizar las ventas mensuales por producto y cliente.'))
    fireEvent.click(screen.getByLabelText(/Evolución de ventas en el tiempo/))
    fireEvent.click(screen.getByLabelText(/Autorizo enviar estos metadatos/))
    fireEvent.click(screen.getByRole('button', { name: 'Ayúdame a formular la necesidad' }))
    expect(await screen.findByRole('heading', { name: 'Redacción propuesta' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Usar esta redacción' }))
    fireEvent.click(screen.getByLabelText(/Autorizo enviar estos metadatos/))
    fireEvent.click(await screen.findByRole('button', { name: 'Validar viabilidad' }))
    expect(await screen.findByRole('heading', { name: 'Viabilidad contra los metadatos' })).toBeInTheDocument()
    expect(screen.getByText('Automático · relación')).toBeInTheDocument()
    expect(screen.getByText('¿Qué significa derivable automáticamente?')).toBeInTheDocument()
    expect(screen.getByText(/si alguno falta, bloquea la aprobación/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Generar propuesta y resolver 1 derivables' })).toBeDisabled()
    fireEvent.click(screen.getByLabelText(/Comprendo esta limitación/))
    fireEvent.click(screen.getByRole('button', { name: 'Generar propuesta y resolver 1 derivables' }))

    expect(await screen.findByRole('heading', { name: 'Generación interrumpida de forma segura' })).toBeInTheDocument()
    expect(screen.getByText('El problema fue del proveedor, no de su necesidad')).toBeInTheDocument()
    expect(screen.queryByText(/No se encontró un alcance verificable/)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reintentar la misma solicitud' })).toBeInTheDocument()
    await waitFor(() => expect(readAssistantDraft()?.proposalId).toBe(14))
    cleanup()
    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Diseño y transformación BI' }))
    fireEvent.click(screen.getByRole('button', { name: 'Asistente de datamart' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Volver a validar y reintentar' }))
    expect(screen.getByText(/Confirme el proveedor, autorice los metadatos/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Autorizo enviar estos metadatos/)).not.toBeChecked()
    expect(screen.getByRole('button', { name: 'Validar viabilidad' })).toBeDisabled()
    expect(creationAttempts).toBe(1)
    fireEvent.click(screen.getByLabelText(/Autorizo enviar estos metadatos/))
    fireEvent.click(screen.getByRole('button', { name: 'Validar viabilidad' }))
    expect(await screen.findByRole('heading', { name: 'Viabilidad contra los metadatos' })).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText(/Comprendo esta limitación/))
    fireEvent.click(screen.getByRole('button', { name: 'Generar propuesta y resolver 1 derivables' }))
    expect(await screen.findByRole('heading', { name: 'Conceptos encontrados' })).toBeInTheDocument()
    expect(screen.getByText('Detalle de venta')).toBeInTheDocument()
    expect(screen.getByText('Motivo de venta')).toBeInTheDocument()
    expect(screen.getByText('Decisión de negocio requerida')).toBeInTheDocument()
    expect(screen.getAllByLabelText('Incluir')[1]).not.toBeChecked()
    expect(screen.getByText(/referencias ya fueron comprobadas/i)).toBeInTheDocument()
    fireEvent.click(screen.getAllByRole('button', { name: 'Consultar al copiloto' })[1])
    expect(await screen.findByText(/Todavía no hay consultas/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '¿Qué riesgo tendría incluir este concepto en el datamart?' }))
    fireEvent.click(screen.getByRole('button', { name: 'Preguntar al copiloto' }))
    expect(await screen.findByText('Recomienda excluir')).toBeInTheDocument()
    expect(screen.getByText('Podría multiplicar las ventas.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Aplicar recomendación' }))
    expect(screen.getAllByLabelText('Incluir')[1]).not.toBeChecked()
    fireEvent.click(screen.getByRole('button', { name: 'Cerrar' }))
    fireEvent.click(screen.getByRole('button', { name: 'Generar propuesta BI' }))
    expect(await screen.findByText('Referencias y contrato validados')).toBeInTheDocument()
    expect(screen.getByText('nombre_cliente')).toBeInTheDocument()
    expect(screen.getByText('tipo_cliente')).toBeInTheDocument()
    expect(screen.getByText(/Nombre descriptivo y tipo derivados mediante relaciones verificadas/)).toBeInTheDocument()
    expect(screen.getByText('Cálculo por fila: UnitPrice × UnitPriceDiscount × OrderQty')).toBeInTheDocument()
    expect(screen.getByText('Decisiones que requieren intervención')).toBeInTheDocument()
    expect(screen.getByText('Ajustes automáticos aplicados')).toBeInTheDocument()
    expect(screen.getByText(/La carga se ejecutará únicamente después de aprobar/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Personalizar propuesta' }))
    expect(await screen.findByRole('heading', { name: 'Personalizar sin escribir SQL' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Resolver una relación con evidencia' })).toBeInTheDocument()
    expect(screen.getByText('Relación apta para revalidar')).toBeInTheDocument()
    expect(screen.getByText('No detectado')).toBeInTheDocument()
    expect(screen.getByText('Columna calculada controlada')).toBeInTheDocument()
    expect(screen.getByText('Sales.SalesOrderDetail.SalesOrderID')).toBeInTheDocument()
    expect(screen.getByText('COUNT(DISTINCT SalesOrderID)')).toBeInTheDocument()
    expect(screen.getByText('SUM(UnitPrice × UnitPriceDiscount × OrderQty)')).toBeInTheDocument()
    expect(screen.getByText(/no existe una medida seleccionada con la misma función semántica/i)).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Justificación del ajuste'), { target: { value: 'Ajuste validado por el analista BI.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar como nueva versión' }))
    expect(await screen.findByText(/personalización creó la versión #13/i)).toBeInTheDocument()
    const revisionRequest = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/copilot/proposals/12/revisions'))
    expect(JSON.parse(String(revisionRequest?.[1]?.body))).toMatchObject({ comment: 'Ajuste validado por el analista BI.', dimension_names: ['dim_producto'], measure_names: ['importe_venta', 'numero_transacciones'], kpi_codes: ['ventas_totales'], kpi_measure_names: { ventas_totales: 'importe_venta' } })
    fireEvent.click(screen.getByRole('button', { name: 'Abrir resultado' }))
    expect(await screen.findByRole('heading', { name: 'Revisión supervisada' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Crear nueva propuesta' })).toBeInTheDocument()
    fireEvent.click(screen.getAllByRole('button', { name: /Necesidad/ })[0])
    expect(await screen.findByRole('heading', { name: 'Necesidad de negocio' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: /Objetivo del análisis/ })).toBeDisabled()
    expect(screen.getByLabelText('Periodicidad')).toHaveValue('month')
    fireEvent.click(screen.getByRole('button', { name: 'Crear nueva propuesta' }))
    expect(screen.getByRole('textbox', { name: /Objetivo del análisis/ })).toBeEnabled()
    expect(screen.getByRole('textbox', { name: /Objetivo del análisis/ })).toHaveValue('')
    expect(screen.getByText(/Nuevo borrador preparado/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Abrir resultado' }))
    expect(await screen.findByRole('heading', { name: 'Revisión supervisada' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Propuesta/ }))
    expect(await screen.findByText('Referencias y contrato validados')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Revisión/ }))
    expect(await screen.findByRole('heading', { name: 'Revisión supervisada' })).toBeInTheDocument()
    expect(screen.getByText(/Versión #11 seleccionada: Gemini Cloud \/ gemini-3.6-flash/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Verificar evidencia' }))
    expect(await screen.findByText('Integridad de los metadatos')).toBeInTheDocument()
    expect(screen.getByText('Reproducción determinística del contrato')).toBeInTheDocument()
    expect(screen.getByText(/no cambia el estado de la propuesta/i)).toBeInTheDocument()
    expect(screen.queryByText('Validaciones que se habilitarán posteriormente')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retirar aprobación' })).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith('/copilot/proposals/11/invalidate'))).toBe(false)
    fireEvent.change(screen.getByLabelText('Motivo'), { target: { value: 'La versión contiene una asociación semántica que debe corregirse.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Retirar aprobación' }))
    expect(await screen.findByText(/Se retiró la aprobación de la versión #11/)).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith('/copilot/proposals/11/invalidate'))).toBe(true)
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('status=ready_for_review'))).toBe(true)
    const creationRequest = fetchMock.mock.calls.find(([input, init]) => String(input).endsWith('/copilot/proposals') && init?.method === 'POST')
    expect(JSON.parse(String(creationRequest?.[1]?.body))).toMatchObject({ viability_hash: 'd'.repeat(64), accepted_limitations: ['goal:definition'], metadata_consent_target: 'approved-target' })
    expect(creationAttempts).toBe(2)
    window.dispatchEvent(new Event(sessionExpiredEvent))
    expect(await screen.findByText(/retomar el punto guardado/i)).toBeInTheDocument()
    expect(readAssistantDraft()?.proposalId).toBe(11)
  })

  it('guía la preparación ETL con KPI variables e interpretación segura en español', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const candidate = {
      proposal_id: 21, metadata_snapshot_id: 2, business_goal: 'Analizar ventas por producto y período.', periodicity: 'month',
      provider_kind: 'gemini', model_id: 'gemini-3.6-flash', created_at: '2026-09-22T10:00:00Z', reviewed_at: '2026-09-22T10:10:00Z',
      reviewed_by_label: 'Analista BI', proposal_hash: 'a'.repeat(64), snapshot_hash: 'b'.repeat(64), summary: 'Modelo de ventas mensual',
      grain: 'Una fila por detalle vendido.', fact_name: 'fact_ventas', dimensions: ['dim_producto', 'dim_fecha'], measures: ['sales_amount'],
      kpi_count: 2, kpi_recipes: [{ code: 'ventas_netas', name: 'Ventas netas', description: 'Importe vendido.', kind: 'aggregate', unit: 'moneda de origen', declared_unit: 'EUR', adjustments: ['La unidad EUR no está comprobada en los metadatos.'], periodicity: 'inherit', definition_version: 'sales-kpi-v1', inputs: ['sales_amount'], recipe: { template: 'aggregate', measure: 'sales_amount', operation: 'sum' } }, { code: 'margen_bruto', name: 'Margen bruto', description: 'Ventas menos costo.', kind: 'difference', unit: 'moneda de origen', periodicity: 'inherit', definition_version: 'sales-kpi-v1', inputs: ['sales_amount', 'cost_amount'], recipe: { template: 'difference', minuend: 'sales_amount', subtrahend: 'cost_amount' } }],
      transformation_plan: [{ order: 1, code: 'extract.approved_columns', stage: 'extract', label: 'Extraer sólo columnas aprobadas', detail: 'Mantiene SQL Server en modo de sólo lectura.', severity: 'required', definition_version: 'sales-transform-v1' }, { order: 2, code: 'localize.dim_producto.labels', stage: 'transform', label: 'Preparar etiquetas españolas', detail: 'Conserva el valor original.', severity: 'optional', definition_version: 'sales-transform-v1' }],
      warnings: [], eligible: true, blocking_reasons: [], recommended: true,
    }
    const executedCandidate = {
      ...candidate,
      proposal_id: 22,
      summary: 'Modelo de ventas ya materializado',
      recommended: false,
      latest_execution_id: 5,
      latest_execution_status: 'validation_warning',
      latest_execution_at: '2026-09-22T10:20:00Z',
      latest_execution_kpi_codes: ['ventas_netas'],
    }
    const execution = {
      id: 5, proposal_id: 22, metadata_snapshot_id: 2, status: 'validation_warning', domain_code: 'ventas',
      builder_version: 'sales-etl-builder-v1', proposal_hash: 'a'.repeat(64), snapshot_hash: 'b'.repeat(64),
      selection_document: {}, plan_document: {},
      validation_document: { message: 'El datamart quedó conciliado; revise la interpretación española propuesta.' },
      metrics_document: {
        reconciliation: { passed: true, source_rows: 10, datamart_rows: 10, difference_rows: 0 },
        tables: [{ table: 'fact_ventas', source_rows: 10, loaded_rows: 10, deduplicated_rows: 0 }],
        kpis: [{ code: 'ventas_netas', name: 'Ventas netas', value: '100', unit: 'moneda de origen', status: 'reconciled' }],
        semantic_interpretation: { status: 'review_required', message: 'Revise las etiquetas.', mappings: [{ dimension: 'dim_territorio', target_column: 'group', mappings: [{ original: 'Europe', label_es: 'Europa' }] }] },
      },
      created_by_label: 'Analista BI', created_at: '2026-09-22T10:20:00Z', finished_at: '2026-09-22T10:21:00Z',
    }
    const currencyVerifiedExecution = {
      ...execution,
      metrics_document: {
        ...execution.metrics_document,
        currency_context: { status: 'verified', currency_code: 'USD', source_reference: 'Sales.CurrencyRate.FromCurrencyCode', message: 'La divisa USD fue comprobada como moneda de origen.' },
        kpis: [{ code: 'ventas_netas', name: 'Ventas netas', value: '100', unit: 'USD', status: 'reconciled' }],
      },
    }
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/auth/me')) return { ok: true, status: 200, json: async () => ({ user: { id: 1, email: 'analista@example.test', full_name: 'Analista BI', is_active: true, roles: [] }, permissions: ['etl.executions.read', 'etl.executions.write'], menus: [{ id: 20, code: 'sales-datamart', label: 'Datamart de ventas', path: '/datamart-ventas', position: 20, module_code: 'data', module_label: 'Datos', is_active: true, permissions: [] }] }) }
      if (url.endsWith('/sources')) return { ok: true, status: 200, json: async () => sourceWorkspace() }
      if (url.includes('/etl/proposals?')) return { ok: true, status: 200, json: async () => ({ items: [candidate, executedCandidate], blocked_items: [], recommended_proposal_id: 21, guidance: [] }) }
      if (url.endsWith('/etl/executions/5/verify-currency')) return { ok: true, status: 200, json: async () => currencyVerifiedExecution }
      if (url.includes('/etl/executions')) return { ok: true, status: 200, json: async () => ({ items: [execution], total: 1, limit: 5, offset: 0 }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    }))

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Diseño y transformación BI' }))
    fireEvent.click(screen.getByRole('button', { name: 'Datamart de ventas' }))

    expect(await screen.findByText('Datamart vigente: ejecución #5, propuesta #22. Es el mismo expediente publicado en Analítica de ventas.')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Conciliación OLTP–datamart' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Volver a propuestas' }))
    expect(await screen.findByText('Sugerencia automática, decisión humana')).toBeInTheDocument()
    expect(screen.getByText('Versión #21 seleccionada')).toBeInTheDocument()
    expect(screen.getByText('Ya ejecutada · expediente #5')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Revisar indicadores' }))
    expect(await screen.findByText('Ajuste de seguridad')).toBeInTheDocument()
    expect(screen.getByText(/unidad EUR no está comprobada/i)).toBeInTheDocument()
    expect(screen.getAllByText('Mensual')).toHaveLength(2)
    expect(screen.getByText('Diferencia')).toBeInTheDocument()
    expect(screen.getByText('sales_amount menos cost_amount.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Revisar transformaciones' }))
    expect(await screen.findByRole('heading', { name: 'Interpretación dinámica en español' })).toBeInTheDocument()
    expect(screen.getByText(/no se traducen identificadores, nombres de personas/i)).toBeInTheDocument()
    expect(screen.getByText('No requiere acción en esta pantalla')).toBeInTheDocument()
    expect(screen.getAllByText('Revisar en el paso 5')).not.toHaveLength(0)
    expect(screen.queryByText('Supervisada')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Abrir expediente #5' }))
    expect(await screen.findByRole('heading', { name: 'Conciliación OLTP–datamart' })).toBeInTheDocument()
    expect(window.scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' })
    expect(screen.getByText('100,00 moneda de origen')).toBeInTheDocument()
    expect(screen.getByText('Divisa pendiente de comprobación')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Comprobar divisa sin repetir el ETL' }))
    expect(await screen.findByText('Divisa comprobada: USD')).toBeInTheDocument()
    expect(screen.getByText(/Referencia: Sales\.CurrencyRate\.FromCurrencyCode/)).toBeInTheDocument()
    expect(screen.getByText(/USD.*100,00/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Interpretación semántica' })).toBeInTheDocument()
    expect(screen.getByDisplayValue('Europa')).toBeInTheDocument()
  })

  it('abre un expediente validado con interpretación publicada sin dejar la pantalla en blanco', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const candidate = {
      proposal_id: 73, metadata_snapshot_id: 2, business_goal: 'Analizar ventas, costos y rentabilidad.', periodicity: 'month',
      provider_kind: 'groq-cloud', model_id: 'openai/gpt-oss-120b', created_at: '2026-09-26T12:00:00Z', reviewed_at: '2026-09-26T12:30:00Z',
      reviewed_by_label: 'Analista BI', proposal_hash: 'a'.repeat(64), snapshot_hash: 'b'.repeat(64), summary: 'Modelo dimensional de ventas, costos y margen',
      grain: 'Una fila por detalle vendido.', fact_name: 'fact_ventas', dimensions: ['dim_fecha', 'dim_producto', 'dim_cliente', 'dim_territorio'],
      measures: ['cantidad', 'ventas_brutas', 'descuento_monetario', 'costo_total'], kpi_count: 9,
      kpi_recipes: [{ code: 'kpi_total_ventas', name: 'Ventas brutas totales', description: 'Importe bruto vendido.', kind: 'aggregate', unit: 'USD', periodicity: 'inherit', definition_version: 'sales-kpi-v1', inputs: ['ventas_brutas'], recipe: { template: 'aggregate', measure: 'ventas_brutas', operation: 'sum' } }],
      transformation_plan: [], warnings: [], eligible: true, blocking_reasons: [], recommended: false,
      latest_execution_id: 9, latest_execution_status: 'succeeded', latest_execution_at: '2026-09-26T13:30:59Z', latest_execution_kpi_codes: ['kpi_total_ventas'],
    }
    const execution = {
      id: 9, proposal_id: 73, metadata_snapshot_id: 2, status: 'succeeded', domain_code: 'ventas', builder_version: 'sales-etl-builder-v1',
      proposal_hash: 'a'.repeat(64), snapshot_hash: 'b'.repeat(64), selection_document: {}, plan_document: {},
      validation_document: { message: 'El datamart quedó materializado, conciliado e interpretado.' },
      metrics_document: {
        reconciliation: { passed: true, source_rows: 121317, datamart_rows: 121317, difference_rows: 0 },
        currency_context: { status: 'verified', currency_code: 'USD', source_reference: 'Sales.CurrencyRate.FromCurrencyCode', message: 'La divisa USD fue comprobada en la fuente.' },
        tables: [
          { table: 'dim_fecha', source_rows: 31465, loaded_rows: 1124, deduplicated_rows: 30341 },
          { table: 'dim_producto', source_rows: 504, loaded_rows: 504, deduplicated_rows: 0 },
          { table: 'dim_cliente', source_rows: 19820, loaded_rows: 19820, deduplicated_rows: 0 },
          { table: 'dim_territorio', source_rows: 10, loaded_rows: 10, deduplicated_rows: 0 },
          { table: 'fact_ventas', source_rows: 121317, loaded_rows: 121317, deduplicated_rows: 0 },
        ],
        kpis: [
          { code: 'kpi_total_ventas', name: 'Ventas brutas totales', unit: 'USD', value: '110373889.313400', status: 'reconciled' },
          { code: 'margen_porcentaje', name: 'Margen bruto %', unit: 'porcentaje', value: '8.968979530830175', status: 'reconciled' },
          { code: 'costo_por_unidad', name: 'Costo por unidad', unit: 'moneda de origen por unidad', value: '365.4760316808', status: 'reconciled' },
        ],
        semantic_interpretation: {
          status: 'applied', message: 'Las etiquetas españolas revisadas fueron publicadas sin reemplazar los valores originales.',
          reviewed_at: '2026-09-26T13:30:59Z', reviewed_by: 'Analista BI',
          analyst_comment: 'Se aprueban únicamente las etiquetas españolas de agrupación territorial; los códigos de país se conservan sin cambios.',
          mappings: [{ dimension: 'dim_territorio', source_column: 'group', label_column: 'group_es', mappings: [{ original: 'Europe', label_es: 'Europa' }, { original: 'North America', label_es: 'Norteamérica' }] }],
        },
      },
      created_by_label: 'Analista BI', created_at: '2026-09-26T13:00:00Z', finished_at: '2026-09-26T13:30:59Z',
    }
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/auth/me')) return { ok: true, status: 200, json: async () => ({ user: { id: 1, email: 'analista@example.test', full_name: 'Analista BI', is_active: true, roles: [] }, permissions: ['etl.executions.read'], menus: [{ id: 20, code: 'sales-datamart', label: 'Datamart de ventas', path: '/datamart-ventas', position: 20, module_code: 'data', module_label: 'Datos', is_active: true, permissions: [] }] }) }
      if (url.endsWith('/sources')) return { ok: true, status: 200, json: async () => sourceWorkspace() }
      if (url.includes('/etl/proposals?')) return { ok: true, status: 200, json: async () => ({ items: [candidate], blocked_items: [], recommended_proposal_id: null, guidance: [] }) }
      if (url.includes('/etl/executions')) return { ok: true, status: 200, json: async () => ({ items: [execution], total: 1, limit: 5, offset: 0 }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    }))

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Diseño y transformación BI' }))
    fireEvent.click(screen.getByRole('button', { name: 'Datamart de ventas' }))

    expect(await screen.findByText('Datamart vigente: ejecución #9, propuesta #73. Es el mismo expediente publicado en Analítica de ventas.')).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Datamart materializado y conciliado' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Conciliación OLTP–datamart' })).toBeInTheDocument()
    expect(screen.getByText('Revisión publicada')).toBeInTheDocument()
    expect(screen.getByText('Norteamérica')).toBeInTheDocument()
    expect(screen.getByText(/USD.*110\.373\.889,31/)).toBeInTheDocument()
    expect(screen.getByText('8,97 porcentaje')).toBeInTheDocument()
    expect(screen.getByText('Costo promedio por unidad vendida')).toBeInTheDocument()
    expect(screen.getByText(/USD.*365,48 por unidad/)).toBeInTheDocument()
    expect(screen.getByText(/Promedio ponderado: total monetario/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Revisar indicadores/ }))
    expect(await screen.findByRole('heading', { name: 'Revise los indicadores sugeridos por la IA' })).toBeInTheDocument()
    expect(screen.getByLabelText('Incluir indicador')).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: /Materializar y cargar/ }))
    expect(await screen.findByRole('heading', { name: 'Materialización ya ejecutada' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Materializar y cargar datamart' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Validar resultados/ }))
    expect(await screen.findByRole('heading', { name: 'Conciliación OLTP–datamart' })).toBeInTheDocument()
    expect(screen.queryByText('No fue posible mostrar esta pantalla')).not.toBeInTheDocument()
  })

  it('mantiene accesibles los expedientes cuando no hay propuestas habilitadas', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const blockedCandidate = {
      proposal_id: 61, metadata_snapshot_id: 2, business_goal: 'Analizar ventas.', periodicity: 'month',
      provider_kind: 'groq-cloud', model_id: 'openai/gpt-oss-120b', created_at: '2026-09-25T14:50:00Z', reviewed_at: '2026-09-25T15:00:00Z',
      reviewed_by_label: 'Analista BI', proposal_hash: 'a'.repeat(64), snapshot_hash: 'b'.repeat(64), summary: 'Modelo dimensional de ventas',
      grain: 'Una fila por detalle vendido.', fact_name: 'fact_ventas', dimensions: ['dim_producto'], measures: ['importe_venta'],
      kpi_count: 1, kpi_recipes: [{ code: 'ventas_netas', name: 'Ventas netas', description: 'Importe vendido.', kind: 'aggregate', unit: 'USD', periodicity: 'inherit', definition_version: 'sales-kpi-v1', inputs: ['importe_venta'], recipe: { template: 'aggregate', measure: 'importe_venta', operation: 'sum' } }],
      transformation_plan: [], warnings: [], eligible: false, blocking_reasons: ['El contrato requiere una versión nueva.'], recommended: false,
    }
    const execution = {
      id: 6, proposal_id: 61, metadata_snapshot_id: 2, status: 'succeeded', domain_code: 'ventas',
      builder_version: 'sales-etl-builder-v1', proposal_hash: 'a'.repeat(64), snapshot_hash: 'b'.repeat(64), selection_document: {}, plan_document: {},
      validation_document: { message: 'El datamart quedó conciliado.' },
      metrics_document: {
        reconciliation: { passed: true, source_rows: 10, datamart_rows: 10, difference_rows: 0 },
        tables: [{ table: 'fact_ventas', source_rows: 10, loaded_rows: 10, deduplicated_rows: 0 }],
        kpis: [{ code: 'ventas_netas', name: 'Ventas netas', value: '100', unit: 'USD', status: 'reconciled' }],
        semantic_interpretation: { status: 'not_required', message: 'No hubo categorías por revisar.', mappings: [] },
      },
      created_by_label: 'Analista BI', created_at: '2026-09-25T15:10:00Z', finished_at: '2026-09-25T15:11:00Z',
    }
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/auth/me')) return { ok: true, status: 200, json: async () => ({ user: { id: 1, email: 'analista@example.test', full_name: 'Analista BI', is_active: true, roles: [] }, permissions: ['etl.executions.read', 'etl.executions.write'], menus: [{ id: 20, code: 'sales-datamart', label: 'Datamart de ventas', path: '/datamart-ventas', position: 20, module_code: 'data', module_label: 'Datos', is_active: true, permissions: [] }] }) }
      if (url.endsWith('/sources')) return { ok: true, status: 200, json: async () => sourceWorkspace() }
      if (url.includes('/etl/proposals?')) return { ok: true, status: 200, json: async () => ({ items: [], blocked_items: [blockedCandidate], recommended_proposal_id: null, guidance: [] }) }
      if (url.includes('/etl/executions')) return { ok: true, status: 200, json: async () => ({ items: [execution], total: 1, limit: 5, offset: 0 }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    }))

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Diseño y transformación BI' }))
    fireEvent.click(screen.getByRole('button', { name: 'Datamart de ventas' }))

    expect(await screen.findByText('Datamart vigente: ejecución #6, propuesta #61. Es el mismo expediente publicado en Analítica de ventas.')).toBeInTheDocument()
    expect(await screen.findByRole('heading', { name: 'Expediente histórico conservado' })).toBeInTheDocument()
    expect(screen.getByText('Sólo lectura')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Materializar y cargar datamart' })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Conciliación OLTP–datamart' })).toBeInTheDocument()
  })
})
