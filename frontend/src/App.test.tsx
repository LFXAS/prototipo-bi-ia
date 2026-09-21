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

    fireEvent.click(await screen.findByRole('button', { name: 'Parámetros generales' }))
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
      if (url.endsWith('/analysis-catalog/domains')) return { ok: true, status: 200, json: async () => [{ code: 'ventas', label: 'Datamart de ventas', description: 'Modelo comercial.', enabled: true, implementation_status: 'implemented' }] }
      if (url.endsWith('/analysis-catalog/domains/ventas') && init?.method === 'PUT') return { ok: true, status: 200, json: async () => JSON.parse(String(init.body)) }
      if (url.endsWith('/analysis-catalog/domains/ventas')) return { ok: true, status: 200, json: async () => catalog }
      throw new Error(`Solicitud inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'IA' }))
    fireEvent.click(screen.getByRole('button', { name: 'Catálogo analítico' }))
    expect(await screen.findByText('Identificador interno: sales_over_time')).toBeInTheDocument()
    expect(screen.queryByText(/Dimensiones de interés/i)).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/Objetivo del análisis/i)).not.toBeInTheDocument()
    fireEvent.change(screen.getAllByLabelText('Etiqueta')[0], { target: { value: 'Tendencia comercial mensual' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar catálogo' }))

    expect(await screen.findByText(/catálogo analítico fue actualizado/i)).toBeInTheDocument()
    const updateRequest = fetchMock.mock.calls.find(([input, init]) => String(input).endsWith('/analysis-catalog/domains/ventas') && init?.method === 'PUT')
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
    fireEvent.click(await screen.findByRole('button', { name: 'Parámetros generales' }))
    fireEvent.click(screen.getByRole('button', { name: 'Conexiones de datos' }))

    expect(await screen.findByText('Sólo lectura validada')).toBeInTheDocument()
    expect(screen.getByText('Activa')).toBeInTheDocument()
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
      if (url.endsWith('/sources/active')) return {
        ok: true, status: 200, json: async () => ({ status: 'ready', connection: { id: 1, name: 'AdventureWorks local', connector_kind: 'sqlserver', database_name: 'AdventureWorks2022', last_test_status: 'ok' }, latest_snapshot: snapshot }),
      }
      if (url.endsWith('/metadata/snapshots') && init?.method === 'POST') return {
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
    fireEvent.click(await screen.findByRole('button', { name: 'Datos' }))
    fireEvent.click(screen.getByRole('button', { name: 'Explorador de esquema' }))

    expect(await screen.findByText('SalesOrderHeader')).toBeInTheDocument()
    expect(await screen.findByText('SalesOrderID')).toBeInTheDocument()
    expect(screen.getByText('PK')).toBeInTheDocument()
    expect(screen.getByText(/Sales\.Customer/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Actualizar metadatos' }))
    expect(await screen.findByText(/La estructura no cambió/)).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([input, init]) => String(input).endsWith('/metadata/snapshots') && init?.method === 'POST')).toBe(true)
    expect(screen.queryByText(/contraseña|password/i)).not.toBeInTheDocument()
  })

  it('guía el análisis y distingue la propuesta de la validación', async () => {
    localStorage.setItem('bi_ia_access_token', 'test-token')
    const proposal = {
      id: 12, metadata_snapshot_id: 4,
      business_goal: 'Analizar las ventas mensuales por producto y cliente.',
      business_questions: ['sales_over_time'], requested_dimensions: ['date', 'product'], periodicity: 'month', domain_code: 'ventas',
      scope_document: { origin: 'semantic-discovery:v1', tables: [{ ref: 'Sales.SalesOrderDetail' }] },
      semantic_map_document: { candidates: [{ business_concept: 'venta', business_name_es: 'Detalle de venta', description_es: 'Cada registro representa una línea vendida.', technical_refs: ['Sales.SalesOrderDetail'], confidence: 'high', reason: 'Contiene cantidad e importe.', references_validated: true }] },
      status: 'ready_for_review', input_hash: 'a'.repeat(64), prompt_version: 'sales-bi-v1', contract_version: 1,
      provider_kind: 'ollama-local', model_id: 'qwen2.5:3b',
      proposal_document: { contract_version: 1, domain: 'ventas', summary: 'Modelo de ventas', business_explanation: 'Una fila por línea vendida.', grain: { description: 'Una fila por línea.' }, fact: { name: 'fact_ventas', measures: [{ name: 'importe_venta', aggregation: 'sum', semantic_role: 'sales_amount' }] }, dimensions: [{ name: 'dim_producto', attributes: ['Name'] }], kpis: [{ name: 'Ventas totales', code: 'ventas_totales', semantic_role: 'sales_amount' }], etl_plan: [{ operation: 'extract', description: 'Extraer campos aprobados.' }], automatic_adjustments: ['La medida importe_venta se vinculó con LineTotal.'], decision_diagnostics: [{ kind: 'kpi', code: 'clientes_activos', status: 'excluded', reason: 'Clientes activos requiere una medida de clientes.', compatible_measures: [] }], ai_decisions: { summary: 'Modelo de ventas', grain_description: 'Una fila por línea vendida.', fact_source: 'Sales.SalesOrderDetail', measures: [{ name: 'importe_venta', source_column: 'LineTotal', aggregation: 'sum', semantic_role: 'sales_amount' }], dimensions: [{ name: 'dim_producto', source_table: 'Production.Product' }], kpis: [{ code: 'ventas_totales', name: 'Ventas totales', measure_index: 0, operation: 'sum', unit: 'moneda', semantic_role: 'sales_amount' }, { code: 'clientes_activos', name: 'Clientes activos', measure_index: 0, operation: 'count_distinct', unit: 'clientes', semantic_role: 'customer_count' }] } },
      validation_document: { valid: true, errors: 0, warnings: 0, issues: [] }, warnings_confirmed: false,
      created_by_label: 'Administradora', created_at: '2026-09-19T10:00:00Z',
    }
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
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/auth/me')) return { ok: true, status: 200, json: async () => ({ user: { id: 1, email: 'admin@example.test', full_name: 'Administradora', is_active: true, roles: [] }, permissions: ['copilot.proposals.read', 'copilot.proposals.generate', 'copilot.proposals.review'], menus: [{ id: 11, code: 'analysis-assistant', label: 'Asistente de datamart', path: '/asistente', position: 10, module_code: 'ai', module_label: 'IA', is_active: true, permissions: [] }] }) }
      if (url.endsWith('/copilot/readiness')) return { ok: true, status: 200, json: async () => ({ ready: true, source: { ready: true, label: 'Fuente de ventas', detail: 'AdventureWorks activa.' }, metadata: { ready: true, label: 'Metadatos', detail: 'Instantánea disponible.' }, llm: { ready: true, label: 'Asistente de IA', detail: 'Ollama listo.' } }) }
      if (url.endsWith('/sources/active')) return { ok: true, status: 200, json: async () => ({ status: 'ready', connection: { id: 1, name: 'AdventureWorks local', connector_kind: 'sqlserver', database_name: 'AdventureWorks2022', last_test_status: 'ok' }, latest_snapshot: { id: 4, data_connection_id: 1, connector_code: 'sqlserver', database_name: 'AdventureWorks2022', contract_version: 1, content_hash: 'b'.repeat(64), schema_count: 6, table_count: 71, column_count: 444, relationship_count: 90, captured_by_label: 'Administradora', captured_at: '2026-09-19T09:00:00Z' } }) }
      if (url.includes('/copilot/catalog?')) return { ok: true, status: 200, json: async () => ({ metadata_snapshot_id: 4, domains: [{ code: 'ventas', label: 'Datamart de ventas', description: 'Modelo dimensional comercial.', available: true, reason: 'La fuente permite iniciar una propuesta.', questions: [{ code: 'sales_over_time', label: 'Evolución de ventas en el tiempo', description: 'Compara períodos.', available: true, reason: 'Disponible.', evidence: ['Sales.SalesOrderHeader'] }, { code: 'top_products', label: 'Productos con mayor desempeño', description: 'Compara productos.', available: true, reason: 'Disponible.', evidence: ['Production.Product'] }], periodicities: [{ code: 'month', label: 'Mensual', description: 'Agrupación mensual.', available: true, reason: 'Disponible.', evidence: ['Sales.SalesOrderHeader'] }] }] }) }
      if (url.endsWith('/copilot/proposals/12/revisions') && init?.method === 'POST') return { ok: true, status: 201, json: async () => revisedProposal }
      if (url.endsWith('/copilot/proposals/11/verify') && init?.method === 'POST') return { ok: true, status: 200, json: async () => ({ proposal_id: 11, verified: true, approval_safe: true, compatibility_warning: false, approval_invalidated: false, checks: [{ code: 'snapshot.integrity', label: 'Integridad de los metadatos', passed: true, detail: 'La huella coincide con la instantánea estructural persistida.' }, { code: 'proposal.replay', label: 'Reproducción determinística del contrato', passed: true, detail: 'Las decisiones persistidas reconstruyen exactamente el mismo contrato.' }], snapshot_hash: 'b'.repeat(64), proposal_hash: 'c'.repeat(64), replay_hash: 'c'.repeat(64), validated_reference_count: 1, rejected_reference_count: 0, validation_errors: 0, validation_warnings: 0, pending_validations: ['Contraste de cifras después de materializar el datamart.'] }) }
      if (url.endsWith('/copilot/proposals/11/invalidate') && init?.method === 'POST') return { ok: true, status: 200, json: async () => ({ ...previousProposal, status: 'invalidated', review_comment: 'La versión contiene una asociación semántica que debe corregirse.' }) }
      if (url.includes('/copilot/proposals') && init?.method === 'POST') return { ok: true, status: 201, json: async () => proposal }
      if (url.includes('/copilot/proposals')) return { ok: true, status: 200, json: async () => ({ items: [previousProposal], total: 6, limit: 5, offset: 0 }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'IA' }))
    fireEvent.click(screen.getByRole('button', { name: 'Asistente de datamart' }))
    expect(await screen.findByText('Dominio habilitado')).toBeInTheDocument()
    fireEvent.click(await screen.findByRole('button', { name: 'Crear propuesta' }))
    expect(await screen.findByText('Mostrando 1-5 de 6 registros')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText(/^Objetivo del análisis/), { target: { value: 'Analizar las ventas mensuales por producto y cliente.' } })
    fireEvent.click(screen.getByLabelText(/Evolución de ventas en el tiempo/))
    fireEvent.click(await screen.findByRole('button', { name: 'Analizar metadatos' }))

    expect(await screen.findByRole('heading', { name: 'Conceptos encontrados' })).toBeInTheDocument()
    expect(screen.getByText('Detalle de venta')).toBeInTheDocument()
    expect(screen.getByText(/referencias ya fueron comprobadas/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Generar propuesta BI' }))
    expect(await screen.findByText('Referencias y contrato validados')).toBeInTheDocument()
    expect(screen.getByText('Decisiones que requieren intervención')).toBeInTheDocument()
    expect(screen.getByText('Ajustes automáticos aplicados')).toBeInTheDocument()
    expect(screen.getByText(/Ninguna operación se ejecuta/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Personalizar propuesta' }))
    expect(await screen.findByRole('heading', { name: 'Personalizar sin escribir SQL' })).toBeInTheDocument()
    expect(screen.getByText(/no existe una medida seleccionada con la misma función semántica/i)).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Justificación del ajuste'), { target: { value: 'Ajuste validado por el analista BI.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar como nueva versión' }))
    expect(await screen.findByText(/personalización creó la versión #13/i)).toBeInTheDocument()
    const revisionRequest = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/copilot/proposals/12/revisions'))
    expect(JSON.parse(String(revisionRequest?.[1]?.body))).toMatchObject({ comment: 'Ajuste validado por el analista BI.', dimension_names: ['dim_producto'], measure_names: ['importe_venta'], kpi_codes: ['ventas_totales'], kpi_measure_names: { ventas_totales: 'importe_venta' } })
    fireEvent.click(screen.getByRole('button', { name: 'Abrir resultado' }))
    expect(await screen.findByRole('heading', { name: 'Revisión supervisada' })).toBeInTheDocument()
    expect(screen.getByText(/Versión #11 seleccionada: Gemini Cloud \/ gemini-3.6-flash/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Verificar evidencia' }))
    expect(await screen.findByText('Integridad de los metadatos')).toBeInTheDocument()
    expect(screen.getByText('Reproducción determinística del contrato')).toBeInTheDocument()
    expect(screen.getByText(/superó las validaciones disponibles/i)).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Motivo'), { target: { value: 'La versión contiene una asociación semántica que debe corregirse.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Retirar aprobación' }))
    expect(await screen.findByText(/Se retiró la aprobación de la versión #11/)).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith('/copilot/proposals/11/invalidate'))).toBe(true)
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('status=ready_for_review'))).toBe(true)
  })
})
