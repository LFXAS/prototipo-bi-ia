import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import { api, sessionExpiredEvent } from './api/security'
import { readAssistantDraft } from './assistantRecovery'
import { roleChoicesForUserAssignment } from './roleChoices'

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

    localStorage.setItem('bi_ia_assistant_draft_v1', JSON.stringify({
      version: 1,
      domainCode: 'ventas',
      step: 3,
      goal: 'Analizar ventas y margen por producto.',
      questions: ['top_products'],
      periodicity: 'month',
      proposalId: 54,
      credential: 'no-debe-restaurarse',
    }))
    expect(readAssistantDraft()).toEqual({
      version: 1,
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
    fireEvent.click(await screen.findByRole('button', { name: 'Parámetros generales' }))
    fireEvent.click(screen.getByRole('button', { name: 'Configuración LLM' }))
    fireEvent.change(await screen.findByLabelText('Nombre de configuración'), { target: { value: 'Groq para análisis BI' } })
    fireEvent.change(screen.getByLabelText('Proveedor'), { target: { value: 'groq-cloud' } })

    expect(screen.getByLabelText('URL del servicio')).toHaveValue('https://api.groq.com/openai/v1')
    expect(screen.getByLabelText('Modelo')).toHaveValue('openai/gpt-oss-120b')
    expect(screen.getByLabelText('Nivel de razonamiento')).toHaveValue('low')
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
      scope_document: { origin: 'semantic-discovery:v1', tables: [{ ref: 'Sales.SalesOrderDetail', columns: [{ name: 'UnitPrice', type: 'money' }, { name: 'UnitPriceDiscount', type: 'money' }, { name: 'OrderQty', type: 'smallint' }] }] },
      semantic_map_document: { candidates: [{ business_concept: 'venta', business_name_es: 'Detalle de venta', description_es: 'Cada registro representa una línea vendida.', technical_refs: ['Sales.SalesOrderDetail'], confidence: 'high', reason: 'Contiene cantidad e importe.', references_validated: true }, { business_concept: 'sales_reason', business_name_es: 'Motivo de venta', description_es: 'Razón asociada al pedido.', technical_refs: ['Sales.SalesReason'], confidence: 'low', reason: 'La relación puede ser opcional o múltiple.', references_validated: true, selected: false, evidence: { status: 'decision_required', recommended_action: 'exclude', guidance: 'Se excluyó preventivamente porque la evidencia semántica es débil.', checks: [{ code: 'reference_exists', passed: true, label: 'Referencia comprobada', detail: 'Sales.SalesReason existe en la instantánea vigente.' }] } }] },
      status: 'ready_for_review', input_hash: 'a'.repeat(64), prompt_version: 'sales-bi-v1', contract_version: 1,
      provider_kind: 'ollama-local', model_id: 'qwen2.5:3b',
      proposal_document: { contract_version: 1, domain: 'ventas', summary: 'Modelo de ventas', business_explanation: 'Una fila por línea vendida.', grain: { description: 'Una fila por línea.' }, fact: { name: 'fact_ventas', measures: [{ name: 'importe_venta', aggregation: 'sum', semantic_role: 'sales_amount', source_columns: ['UnitPrice', 'UnitPriceDiscount', 'OrderQty'], calculation: { operation: 'multiply', inputs: ['UnitPrice', 'UnitPriceDiscount', 'OrderQty'] } }] }, dimensions: [{ name: 'dim_producto', attributes: ['Name'] }, { name: 'dim_cliente', attributes: ['PersonID', 'StoreID', 'AccountNumber'], display_label: { target_name: 'nombre_cliente', type_target_name: 'tipo_cliente', fallback_column: 'AccountNumber', minimum_descriptive_coverage: 0.95, variants: [] } }], kpis: [{ name: 'Ventas totales', code: 'ventas_totales', semantic_role: 'sales_amount' }], etl_plan: [{ operation: 'extract', description: 'Extraer campos aprobados.' }], automatic_adjustments: ['La medida importe_venta se derivará mediante multiply usando exclusivamente columnas verificadas.'], decision_diagnostics: [{ kind: 'kpi', code: 'clientes_activos', status: 'excluded', reason: 'Clientes activos requiere una medida de clientes.', compatible_measures: [] }], ai_decisions: { summary: 'Modelo de ventas', grain_description: 'Una fila por línea vendida.', fact_source: 'Sales.SalesOrderDetail', measures: [{ name: 'importe_venta', source_column: 'UnitPrice', aggregation: 'sum', semantic_role: 'sales_amount', calculation: { operation: 'multiply', inputs: ['UnitPrice', 'UnitPriceDiscount', 'OrderQty'] } }], dimensions: [{ name: 'dim_producto', source_table: 'Production.Product' }], kpis: [{ code: 'ventas_totales', name: 'Ventas totales', measure_index: 0, operation: 'sum', unit: 'moneda', semantic_role: 'sales_amount' }, { code: 'clientes_activos', name: 'Clientes activos', measure_index: 0, operation: 'count_distinct', unit: 'clientes', semantic_role: 'customer_count' }] } },
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
      if (url.endsWith('/copilot/needs/formulate') && init?.method === 'POST') return { ok: true, status: 200, json: async () => ({ original_goal: 'Analizar las ventas mensuales por producto y cliente.', suggested_goal: 'Analizar las ventas netas mensuales por producto y cliente para identificar variaciones.', rationale: 'Hace explícito el indicador y la comparación temporal.', improvements: ['Confirme si venta neta es el indicador esperado.'], provider_kind: 'groq-cloud', model_id: 'openai/gpt-oss-120b' }) }
      if (url.endsWith('/copilot/needs/viability') && init?.method === 'POST') return { ok: true, status: 200, json: async () => ({ assessment_hash: 'd'.repeat(64), requirements: [{ code: 'question:sales_over_time', label: 'Evolución de ventas en el tiempo', request_text: 'Compara períodos.', status: 'derivable', evidence: ['Sales.SalesOrderDetail.LineTotal', 'Sales.SalesOrderHeader.OrderDate', 'Ruta declarada: Sales.SalesOrderDetail → Sales.SalesOrderHeader'], resolution: 'Puede resolverse con relaciones declaradas.' }, { code: 'goal:sales_amount', label: 'Ventas o ingresos', request_text: 'Analizar las ventas mensuales por producto y cliente.', status: 'direct', evidence: ['Sales.SalesOrderDetail.LineTotal'], resolution: 'Puede resolverse directamente.' }, { code: 'goal:definition', label: 'Definición de venta neta', request_text: 'Venta neta', status: 'ambiguous', evidence: ['Sales.SalesOrderDetail.LineTotal', 'Sales.SalesOrderHeader.TotalDue'], resolution: 'Confirme qué componentes incluye la venta neta.' }], counts: { direct: 1, derivable: 1, ambiguous: 1, unavailable: 0 }, requires_acknowledgement: ['goal:definition'], can_continue: true, summary: 'La necesidad tiene respaldo suficiente para continuar, con decisiones pendientes.' }) }
      if (url.endsWith('/copilot/proposals/12/relation-options')) return { ok: true, status: 200, json: async () => ({ proposal_id: 12, dimension_names: ['dim_producto'], options: [{ option_id: 'r'.repeat(64), left_table: 'Sales.SalesOrderDetail', right_table: 'Production.Product', left_columns: ['ProductID'], right_columns: ['ProductID'], left_types: ['int'], right_types: ['int'], cardinality: 'many_to_one', target_unique: true, nullable_source: false, duplication_risk: false, eligible: true, guidance: 'Relación declarada hacia una clave única; conserva la granularidad.' }, { option_id: 'x'.repeat(64), left_table: 'Sales.SalesOrderDetail', right_table: 'Sales.SpecialOfferProduct', left_columns: ['ProductID'], right_columns: ['ProductID'], left_types: ['int'], right_types: ['int'], cardinality: 'unknown', target_unique: false, nullable_source: false, duplication_risk: true, eligible: false, guidance: 'No se puede seleccionar: la clave destino no es única.' }] }) }
      if (url.endsWith('/copilot/proposals/12/revisions') && init?.method === 'POST') return { ok: true, status: 201, json: async () => revisedProposal }
      if (url.endsWith('/copilot/proposals/11/verify') && init?.method === 'POST') return { ok: true, status: 200, json: async () => ({ proposal_id: 11, verified: true, approval_safe: true, compatibility_warning: false, approval_invalidated: false, checks: [{ code: 'snapshot.integrity', label: 'Integridad de los metadatos', passed: true, detail: 'La huella coincide con la instantánea estructural persistida.' }, { code: 'proposal.replay', label: 'Reproducción determinística del contrato', passed: true, detail: 'Las decisiones persistidas reconstruyen exactamente el mismo contrato.' }], snapshot_hash: 'b'.repeat(64), proposal_hash: 'c'.repeat(64), replay_hash: 'c'.repeat(64), validated_reference_count: 1, rejected_reference_count: 0, validation_errors: 0, validation_warnings: 0, pending_validations: ['Contraste de cifras después de materializar el datamart.'] }) }
      if (url.endsWith('/copilot/proposals/11/invalidate') && init?.method === 'POST') return { ok: true, status: 200, json: async () => ({ ...previousProposal, status: 'invalidated', review_comment: 'La versión contiene una asociación semántica que debe corregirse.' }) }
      if (url.includes('/copilot/proposals/12/semantic-advice?')) return { ok: true, status: 200, json: async () => [] }
      if (url.endsWith('/copilot/proposals/12/semantic-advice') && init?.method === 'POST') return { ok: true, status: 201, json: async () => ({ id: 1, proposal_id: 12, concept_code: 'sales_reason', question: '¿Qué riesgo tendría incluir este concepto en el datamart?', response_document: { conclusion: 'exclude', answer_es: 'Puede existir más de un motivo por pedido.', evidence: [{ technical_ref: 'Sales.SalesReason', detail_es: 'La referencia existe y requiere una relación intermedia.' }], risk_es: 'Podría multiplicar las ventas.', include_consequence_es: 'Requiere una tabla puente.', exclude_consequence_es: 'No se analizarán motivos.', recommended_action_es: 'Mantener excluido salvo necesidad expresa.', confidence: 'medium', selection_changed: false }, provider_kind: 'groq-cloud', model_id: 'openai/gpt-oss-120b', created_by_label: 'Administradora', created_at: '2026-09-23T10:00:00Z' }) }
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
    const needTextarea = screen.getByLabelText(/^Objetivo del análisis/)
    expect(needTextarea).toHaveAttribute('rows', '12')
    expect(needTextarea).toHaveAttribute('maxlength', '2000')
    fireEvent.change(needTextarea, { target: { value: 'Analizar las ventas mensuales por producto y cliente.' } })
    await waitFor(() => expect(readAssistantDraft()?.goal).toBe('Analizar las ventas mensuales por producto y cliente.'))
    fireEvent.click(screen.getByLabelText(/Evolución de ventas en el tiempo/))
    fireEvent.click(screen.getByRole('button', { name: 'Ayúdame a formular la necesidad' }))
    expect(await screen.findByRole('heading', { name: 'Redacción propuesta' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Usar esta redacción' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Validar viabilidad' }))
    expect(await screen.findByRole('heading', { name: 'Viabilidad contra los metadatos' })).toBeInTheDocument()
    expect(screen.getByText('Derivable')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Generar conceptos y propuesta' })).toBeDisabled()
    fireEvent.click(screen.getByLabelText(/Comprendo esta limitación/))
    fireEvent.click(screen.getByRole('button', { name: 'Generar conceptos y propuesta' }))

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
    const creationRequest = fetchMock.mock.calls.find(([input, init]) => String(input).endsWith('/copilot/proposals') && init?.method === 'POST')
    expect(JSON.parse(String(creationRequest?.[1]?.body))).toMatchObject({ viability_hash: 'd'.repeat(64), accepted_limitations: ['goal:definition'] })
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
      if (url.endsWith('/etl/proposals')) return { ok: true, status: 200, json: async () => ({ items: [candidate, executedCandidate], blocked_items: [], recommended_proposal_id: 21, guidance: [] }) }
      if (url.endsWith('/etl/executions/5/verify-currency')) return { ok: true, status: 200, json: async () => currencyVerifiedExecution }
      if (url.includes('/etl/executions')) return { ok: true, status: 200, json: async () => ({ items: [execution], total: 1, limit: 5, offset: 0 }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    }))

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Datos' }))
    fireEvent.click(screen.getByRole('button', { name: 'Datamart de ventas' }))

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
      if (url.endsWith('/etl/proposals')) return { ok: true, status: 200, json: async () => ({ items: [candidate], blocked_items: [], recommended_proposal_id: null, guidance: [] }) }
      if (url.includes('/etl/executions')) return { ok: true, status: 200, json: async () => ({ items: [execution], total: 1, limit: 5, offset: 0 }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    }))

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Datos' }))
    fireEvent.click(screen.getByRole('button', { name: 'Datamart de ventas' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Abrir expediente #9' }))

    expect(await screen.findByRole('heading', { name: 'Datamart materializado y conciliado' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Conciliación OLTP–datamart' })).toBeInTheDocument()
    expect(screen.getByText('Revisión publicada')).toBeInTheDocument()
    expect(screen.getByText('Norteamérica')).toBeInTheDocument()
    expect(screen.getByText(/USD.*110\.373\.889,31/)).toBeInTheDocument()
    expect(screen.getByText('8,97 porcentaje')).toBeInTheDocument()
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
      if (url.endsWith('/etl/proposals')) return { ok: true, status: 200, json: async () => ({ items: [], blocked_items: [blockedCandidate], recommended_proposal_id: null, guidance: [] }) }
      if (url.includes('/etl/executions')) return { ok: true, status: 200, json: async () => ({ items: [execution], total: 1, limit: 5, offset: 0 }) }
      throw new Error(`Solicitud inesperada: ${url}`)
    }))

    render(<App />)
    fireEvent.click(await screen.findByRole('button', { name: 'Datos' }))
    fireEvent.click(screen.getByRole('button', { name: 'Datamart de ventas' }))

    expect(await screen.findByRole('heading', { name: 'No hay propuestas habilitadas para una ejecución nueva' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Expedientes recientes' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Abrir expediente #6' }))
    expect(await screen.findByRole('heading', { name: 'Expediente histórico conservado' })).toBeInTheDocument()
    expect(screen.getByText('Sólo lectura')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Materializar y cargar datamart' })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Conciliación OLTP–datamart' })).toBeInTheDocument()
  })
})
