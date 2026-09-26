import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from 'react'

import {
  api,
  type ActiveSource,
  type AnalysisCatalogConfiguration,
  type AnalysisCatalogDomain,
  type AnalysisCatalogPeriodicity,
  type AuditEvent,
  type BiProposal,
  type CopilotCatalog,
  type CopilotReadiness,
  type ControlledRelationCatalog,
  type DataConnection,
  type EtlExecution,
  type EtlKpiRecipe,
  type EtlProposalCandidate,
  type EtlTransformation,
  type LlmConfiguration,
  type Menu,
  type MetadataSnapshot,
  type MetadataTable,
  type MetadataTableDetail,
  type NeedFormulation,
  type NeedViability,
  type Page,
  type Parameter,
  type Permission,
  type ProposalVerification,
  type ProposalRevision,
  type Role,
  type SemanticAdvice,
  type SemanticCandidate,
  type SemanticPreview,
  type Session,
  type User,
  sessionExpiredEvent,
} from './api/security'
import { roleChoicesForUserAssignment } from './roleChoices'
import { AnalyticsPage } from './AnalyticsPage'
import { assistantDraftKey, readAssistantDraft, type AssistantDraft } from './assistantRecovery'

type PageData =
  | Page<User>
  | Page<Role>
  | Page<Permission>
  | Page<Menu>
  | Page<Parameter>
  | Page<LlmConfiguration>
  | Page<DataConnection>
  | Page<MetadataSnapshot>
  | Page<MetadataTable>
  | Page<AuditEvent>
  | null
type Row = Record<string, unknown>
type Values = Record<string, string>

const tokenKey = 'bi_ia_access_token'
const resumePageKey = 'bi_ia_resume_page'
const pageSize = 10
const labels: Record<string, string> = {
  '/': 'Inicio',
  '/usuarios': 'Usuarios',
  '/roles': 'Roles',
  '/permisos': 'Permisos',
  '/menus': 'Menús',
  '/parametros': 'Parámetros',
  '/llm': 'Configuración LLM',
  '/conexiones': 'Conexiones de datos',
  '/esquema': 'Explorador de esquema',
  '/catalogo-analitico': 'Catálogo analítico',
  '/asistente': 'Asistente de datamart',
  '/datamart-ventas': 'Datamart de ventas',
  '/analitica-ventas': 'Analítica de ventas',
  '/auditoria': 'Auditoría',
}

const writePermissions: Record<string, string> = {
  '/usuarios': 'security.users.write',
  '/roles': 'security.roles.write',
  '/permisos': 'security.permissions.write',
  '/menus': 'security.menus.write',
  '/parametros': 'parameters.write',
  '/llm': 'parameters.llm.write',
  '/conexiones': 'connections.write',
  '/catalogo-analitico': 'copilot.catalog.write',
}

const auditActionLabels: Record<string, string> = {
  'auth.login': 'Inicio de sesión',
  'security.user.create': 'Creación de usuario',
  'security.user.update': 'Actualización de usuario',
  'security.user.delete': 'Eliminación de usuario',
  'security.user.protected_change_rejected': 'Cambio rechazado en usuario protegido',
  'security.role.create': 'Creación de rol',
  'security.role.update': 'Actualización de rol',
  'security.role.delete': 'Eliminación de rol',
  'security.role.permissions.update': 'Actualización de permisos del rol',
  'security.role.protected_change_rejected': 'Cambio rechazado en rol protegido',
  'security.permission.update': 'Actualización de permiso',
  'security.permission.protected_change_rejected': 'Cambio rechazado en permiso protegido',
  'security.permission.create_rejected': 'Creación manual de permiso rechazada',
  'security.menu.update': 'Actualización de menú',
  'security.menu.delete': 'Eliminación de menú',
  'parameters.llm.delete': 'Eliminación de configuración LLM',
  'parameters.llm.credential.register': 'Registro de credencial LLM',
  'parameters.llm.credential.replace': 'Reemplazo de credencial LLM',
  'metadata.snapshot.create': 'Creación de instantánea de metadatos',
  'metadata.snapshot.unchanged': 'Comprobación de metadatos sin cambios',
  'metadata.snapshot.failed': 'Fallo controlado al actualizar metadatos',
  'copilot.proposal.ready_for_review': 'Generación de propuesta BI',
  'copilot.proposal.provider_failed': 'Fallo controlado del proveedor IA',
  'copilot.proposal.invalid': 'Propuesta BI con errores de validación',
  'copilot.proposal.revise': 'Personalización supervisada de propuesta BI',
  'copilot.proposal.verify': 'Verificación de evidencia de propuesta BI',
  'copilot.proposal.approve': 'Aprobación de propuesta BI',
  'copilot.proposal.reject': 'Rechazo de propuesta BI',
  'copilot.catalog.update': 'Actualización del catálogo analítico',
  'copilot.catalog.reset': 'Restauración del catálogo analítico',
  'security.menu.protected_change_rejected': 'Cambio rechazado en menú protegido',
  'security.menu.create_rejected': 'Creación manual de menú rechazada',
}

function readLabel(item: Row) {
  if (typeof item.action === 'string') return auditActionLabels[item.action] ?? item.action
  return String(item.full_name ?? item.name ?? item.label ?? item.key ?? item.code ?? '')
}

function parseSelectedIds(value: string) {
  if (!value.trim()) return []
  return value.split(',').map((item) => Number(item.trim())).filter((item) => Number.isInteger(item) && item > 0)
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(tokenKey) ?? '')
  const [session, setSession] = useState<Session | null>(null)
  const [page, setPage] = useState('/')
  const [data, setData] = useState<PageData>(null)
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('admin@bi.local')
  const [password, setPassword] = useState('')
  const [revision, setRevision] = useState(0)
  const [offset, setOffset] = useState(0)
  const [menuOpen, setMenuOpen] = useState(false)
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({})
  const [sidebarHidden, setSidebarHidden] = useState(false)
  const loadedPage = useRef(page)

  useEffect(() => {
    function handleSessionExpired() {
      const resumePage = page !== '/'
        ? page
        : localStorage.getItem(assistantDraftKey) ? '/asistente' : '/'
      localStorage.setItem(resumePageKey, resumePage)
      localStorage.removeItem(tokenKey)
      setToken('')
      setSession(null)
      setData(null)
      setMessage('La sesión venció. Inicie sesión nuevamente para retomar el punto guardado.')
    }
    window.addEventListener(sessionExpiredEvent, handleSessionExpired)
    return () => window.removeEventListener(sessionExpiredEvent, handleSessionExpired)
  }, [page])

  useEffect(() => {
    if (!token) return
    api.session(token)
      .then((activeSession) => {
        setSession(activeSession)
        const resumePage = localStorage.getItem(resumePageKey)
        if (resumePage && activeSession.menus.some((menu) => menu.path === resumePage)) {
          setPage(resumePage)
          setMessage('Sesión recuperada. Restauramos el módulo y el avance guardado.')
        }
        localStorage.removeItem(resumePageKey)
      })
      .catch(() => {
        localStorage.removeItem(tokenKey)
        setToken('')
        setMessage('La sesión venció. Inicie sesión nuevamente para retomar el punto guardado.')
      })
  }, [token, revision])

  useEffect(() => {
    if (!token || !session || page === '/') return
    const loads: Record<string, () => Promise<PageData>> = {
      '/usuarios': () => api.users(token, pageSize, offset),
      '/roles': () => api.roles(token, pageSize, offset),
      '/permisos': () => api.permissions(token, pageSize, offset),
      '/menus': () => api.menus(token, pageSize, offset),
      '/parametros': () => api.parameters(token, pageSize, offset),
      '/llm': () => api.llm(token, pageSize, offset),
      '/conexiones': () => api.connections(token, pageSize, offset),
      '/esquema': () => api.metadataSnapshots(token, pageSize, offset),
      '/auditoria': () => api.audit(token, pageSize, offset),
    }
    if (loadedPage.current !== page) {
      loadedPage.current = page
      setData(null)
    }
    setMessage('')
    loads[page]?.().then(setData).catch((error: Error) => setMessage(error.message))
  }, [offset, page, revision, session, token])

  async function submitLogin(event: FormEvent) {
    event.preventDefault()
    setMessage('')
    try {
      const result = await api.login(email, password)
      localStorage.setItem(tokenKey, result.access_token)
      setToken(result.access_token)
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No fue posible iniciar sesión.')
    }
  }

  function logout() {
    localStorage.removeItem(tokenKey)
    localStorage.removeItem(resumePageKey)
    localStorage.removeItem(assistantDraftKey)
    setToken('')
    setSession(null)
    setData(null)
    setPage('/')
  }

  function isGroupExpanded(group: { code: string; items: Menu[] }) {
    return expandedGroups[group.code] ?? group.items.some((menu) => menu.path === page)
  }

  function toggleGroup(group: { code: string; items: Menu[] }) {
    setExpandedGroups((current) => ({ ...current, [group.code]: !isGroupExpanded(group) }))
  }

  if (!session) {
    return (
      <main className="login-page">
        <section className="login-card">
          <p className="eyebrow">Prototipo académico</p>
          <h1>BI asistido por IA</h1>
          <p>Ingrese con una cuenta autorizada. La interfaz y la API validan los permisos reales.</p>
          <form onSubmit={submitLogin}>
            <label>Correo<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" autoComplete="email" required /></label>
            <label>Contraseña<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="current-password" required /></label>
            <button>Iniciar sesión</button>
          </form>
          {message && <p className="notice error">{message}</p>}
          <small>La clave inicial se define únicamente en el archivo de entorno local.</small>
        </section>
      </main>
    )
  }

  return (
    <main className="app-shell">
      <header>
        <div><p className="eyebrow">BI asistido por IA</p><strong>{session.user.full_name}</strong></div>
        <div className="header-actions"><button className="menu-toggle secondary" aria-expanded={menuOpen} aria-controls="main-navigation" onClick={() => setMenuOpen((open) => !open)}>☰ Menú</button><button className="secondary" onClick={logout}>Cerrar sesión</button></div>
      </header>
      <div className={`workspace ${sidebarHidden ? 'sidebar-hidden' : ''}`}>
        <aside className={`navigation-panel ${menuOpen ? 'open' : ''}`}><nav id="main-navigation" aria-label="Navegación principal">
          {session.menus.filter((menu) => menu.path === '/').map((menu) => <button className={page === menu.path ? 'active direct-menu' : 'direct-menu'} onClick={() => { setPage(menu.path); setOffset(0); setMenuOpen(false) }} key={menu.id}>{menu.label}</button>)}
          {Object.values(groupMenus(session.menus.filter((menu) => menu.path !== '/'))).map((group) => <div className="navigation-group" key={group.code}><button className="module-toggle" aria-expanded={isGroupExpanded(group)} aria-controls={`menu-group-${group.code}`} onClick={() => toggleGroup(group)}><span>{group.label}</span><span aria-hidden="true">{isGroupExpanded(group) ? '⌄' : '›'}</span></button><div className="submenu" id={`menu-group-${group.code}`} hidden={!isGroupExpanded(group)}>{group.items.map((menu) => <button className={page === menu.path ? 'active' : ''} onClick={() => { setPage(menu.path); setOffset(0); setMenuOpen(false) }} key={menu.id}>{menu.label}</button>)}</div></div>)}
        </nav></aside>
        <button className="sidebar-rail-toggle" aria-expanded={!sidebarHidden} aria-label={sidebarHidden ? 'Mostrar navegación lateral' : 'Ocultar navegación lateral'} title={sidebarHidden ? 'Mostrar navegación lateral' : 'Ocultar navegación lateral'} onClick={() => setSidebarHidden((hidden) => !hidden)}><span aria-hidden="true">{sidebarHidden ? '›' : '‹'}</span></button>
        <section className="content">
          <h1>{labels[page]}</h1>
          {page === '/'
            ? <Home session={session} token={token} navigate={setPage} />
            : page === '/conexiones'
              ? <ConnectionsPage data={data as Page<DataConnection> | null} message={message} token={token} canWrite={session.permissions.includes('connections.write')} canTest={session.permissions.includes('connections.test')} canRefresh={session.permissions.includes('metadata.refresh')} onSaved={() => { setOffset(0); setRevision((value) => value + 1) }} onChangePage={setOffset} />
              : page === '/esquema'
                ? <SchemaExplorerPage snapshots={data as Page<MetadataSnapshot> | null} message={message} token={token} canRefresh={session.permissions.includes('metadata.refresh')} onSaved={() => { setOffset(0); setRevision((value) => value + 1) }} onChangePage={setOffset} />
                : page === '/asistente'
                  ? <AnalysisAssistantPage token={token} canGenerate={session.permissions.includes('copilot.proposals.generate')} canReview={session.permissions.includes('copilot.proposals.review')} canPreviewSemantics={session.permissions.includes('metadata.semantic_resolution.read')} navigate={setPage} />
                : page === '/datamart-ventas'
                  ? <SalesDatamartPage token={token} canWrite={session.permissions.includes('etl.executions.write')} navigate={setPage} />
                : page === '/analitica-ventas'
                  ? <AnalyticsPage token={token} canExport={session.permissions.includes('reports.analytics.export')} navigate={setPage} />
                : page === '/catalogo-analitico'
                  ? <AnalysisCatalogPage token={token} canWrite={session.permissions.includes('copilot.catalog.write')} />
              : page === '/parametros'
                ? <ParametersPage data={data as Page<Parameter> | null} message={message} token={token} canWrite={session.permissions.includes('parameters.write')} onSaved={() => { setOffset(0); setRevision((value) => value + 1) }} onChangePage={setOffset} />
                : <ResourcePage key={page} page={page} data={data} message={message} token={token} canWrite={session.permissions.includes(writePermissions[page])} onSaved={() => { setOffset(0); setRevision((value) => value + 1) }} onChangePage={setOffset} />}
        </section>
      </div>
    </main>
  )
}

function groupMenus(menus: Menu[]) {
  return menus.reduce<Record<string, { code: string; label: string; items: Menu[] }>>((groups, menu) => {
    const key = menu.module_code
    groups[key] ??= { code: key, label: menu.module_label, items: [] }
    groups[key].items.push(menu)
    return groups
  }, {})
}

function Home({ session, token, navigate }: { session: Session; token: string; navigate: (path: string) => void }) {
  const [readiness, setReadiness] = useState<CopilotReadiness | null>(null)
  const [setupOpen, setSetupOpen] = useState(false)
  const canReadCopilot = session.permissions.includes('copilot.proposals.read')

  useEffect(() => {
    if (!canReadCopilot) return
    api.copilotReadiness(token).then(setReadiness).catch(() => setReadiness(null))
  }, [canReadCopilot, token])

  return <>
    <p className="lead">Prepare la fuente y el asistente para convertir una necesidad comercial en una propuesta supervisada de datamart.</p>
    {canReadCopilot && readiness
      ? <>
        <div className="readiness-grid">{[readiness.source, readiness.metadata, readiness.llm].map((item) => <article className={item.ready ? 'ready' : 'pending'} key={item.label}><span className="status-dot" aria-hidden="true" /><div><h2>{item.label}</h2><p>{item.detail}</p></div></article>)}</div>
        <section className="home-action-card"><div><p className="eyebrow">Preparación del datamart</p><h2>{readiness.ready ? 'Todo está listo' : 'Faltan prerrequisitos'}</h2><p>{readiness.ready ? 'Puede escoger un dominio y crear una propuesta BI. La aprobación no ejecutará el ETL ni creará tablas todavía.' : 'Use la preparación guiada para completar los componentes pendientes.'}</p></div><div className="form-actions">{readiness.ready && <button onClick={() => navigate('/asistente')}>Crear propuesta de datamart</button>}<button className="secondary" onClick={() => setSetupOpen((value) => !value)}>{setupOpen ? 'Cerrar preparación' : readiness.ready ? 'Revisar configuración' : 'Completar configuración inicial'}</button></div></section>
        {setupOpen && <SetupWizard readiness={readiness} navigate={navigate} />}
      </>
      : <div className="cards"><article><strong>{session.user.roles.length}</strong><span>roles asignados</span></article><article><strong>{session.permissions.length}</strong><span>permisos efectivos</span></article><article><strong>{session.menus.length}</strong><span>opciones visibles</span></article></div>}
    <p className="notice">El asistente prepara y valida la propuesta. Después de aprobarla podrá materializar el datamart desde el espacio de generación.</p>
  </>
}

function SetupWizard({ readiness, navigate }: { readiness: CopilotReadiness; navigate: (path: string) => void }) {
  const [step, setStep] = useState(1)
  const items = [
    { title: 'Bienvenida y comprobación', text: 'Verificaremos el proveedor de IA, la fuente y sus metadatos.', ready: true },
    { title: 'Proveedor de IA', text: readiness.llm.detail, ready: readiness.llm.ready, path: '/llm' },
    { title: 'Fuente de ventas', text: readiness.source.detail, ready: readiness.source.ready, path: '/conexiones' },
    { title: 'Activación y metadatos', text: readiness.metadata.detail, ready: readiness.metadata.ready, path: '/esquema' },
    { title: 'Resumen', text: readiness.ready ? 'La plataforma está preparada para crear una propuesta de datamart.' : 'Complete los pasos pendientes antes de continuar.', ready: readiness.ready, path: readiness.ready ? '/asistente' : undefined },
  ]
  const current = items[step - 1]
  return <section className="setup-wizard" aria-label="Preparación inicial">
    <div className="wizard-progress" aria-label={`Paso ${step} de 5`}>{items.map((item, index) => <span className={index + 1 === step ? 'current' : item.ready ? 'complete' : ''} key={item.title}>{index + 1}</span>)}</div>
    <p className="eyebrow">Paso {step} de 5</p><h2>{current.title}</h2><p>{current.text}</p>
    {current.path && <button onClick={() => navigate(current.path!)}>{step === 5 ? 'Elegir datamart' : current.ready ? 'Revisar este paso' : 'Completar este paso'}</button>}
    <div className="wizard-actions"><button className="secondary" disabled={step === 1} onClick={() => setStep((value) => Math.max(1, value - 1))}>Atrás</button><button disabled={step === 5} onClick={() => setStep((value) => Math.min(5, value + 1))}>Continuar</button></div>
  </section>
}

const proposalStatusLabels: Record<BiProposal['status'], string> = {
  generating: 'Generando', provider_failed: 'Proveedor no disponible', validation_failed: 'Validación fallida', ready_for_review: 'Lista para revisar', approved: 'Aprobada', rejected: 'Rechazada', invalidated: 'Aprobación retirada', discarded: 'Descartada',
}
const providerLabels: Record<string, string> = {
  gemini: 'Gemini Cloud',
  'groq-cloud': 'Groq Cloud',
  'qwen-cloud': 'Qwen Cloud',
  'ollama-local': 'Ollama local',
}
function providerLabel(value: string) { return providerLabels[value] ?? value }

function defaultExcludedConcepts(item: BiProposal) {
  const persisted = [
    ...(item.semantic_map_document.excluded_by_analyst ?? []),
    ...(item.semantic_map_document.excluded_by_system ?? []),
  ]
  const automatic = (item.semantic_map_document.candidates ?? [])
    .filter((candidate) => candidate.selected === false || candidate.evidence?.recommended_action === 'exclude' || candidate.confidence === 'low')
    .map((candidate) => candidate.business_concept)
  return [...new Set([...persisted, ...automatic])]
}

const historyPageSize = 5
const historyFilterOptions = [
  { value: 'ready_for_review', label: 'Por revisar', statuses: ['ready_for_review'] },
  { value: 'approved', label: 'Aprobadas', statuses: ['approved'] },
  { value: 'rejected', label: 'Rechazadas', statuses: ['rejected'] },
  { value: 'issues', label: 'Con inconvenientes', statuses: ['provider_failed', 'validation_failed'] },
  { value: 'archived', label: 'Retiradas o descartadas', statuses: ['invalidated', 'discarded'] },
  { value: 'all', label: 'Todas', statuses: [] },
]

function revisionFromProposal(item: BiProposal): ProposalRevision {
  const decisions = objectValue(item.proposal_document.ai_decisions)
  const measures = arrayValue(decisions.measures)
  const includedKpis = new Set(arrayValue(item.proposal_document.kpis).map((kpi) => stringValue(kpi.code, '')).filter(Boolean))
  const decisionKpis = arrayValue(decisions.kpis)
  const storedCalculations = Object.fromEntries(measures.map((measure) => {
    const calculation = objectValue(measure.calculation)
    const operation = stringValue(calculation.operation, '')
    const inputs = stringArrayValue(calculation.inputs)
    return operation && inputs.length >= 2 ? [stringValue(measure.name, ''), { operation, inputs }] : []
  }).filter((entry) => entry.length === 2)) as ProposalRevision['measure_calculations']
  const factSource = stringValue(decisions.fact_source, '')
  const factColumns = (item.scope_document.tables ?? []).find((table) => table.ref === factSource)?.columns ?? []
  const numericNames = factColumns.filter((column) => /tinyint|smallint|int|bigint|decimal|numeric|money|float|real/i.test(column.type)).map((column) => column.name)
  const derivedCalculations = Object.fromEntries(measures.flatMap((measure) => {
    const name = stringValue(measure.name, '')
    const source = stringValue(measure.source_column, '')
    if (!/(discount|descuento)/i.test(source) || /(amount|importe|monto|total|value|valor)/i.test(source)) return []
    const discount = numericNames.filter((column) => /(discount|descuento)/i.test(column) && !/(amount|importe|monto|total|value|valor)/i.test(column))
    const price = numericNames.filter((column) => /(price|precio)/i.test(column) && !/(discount|descuento)/i.test(column))
    const quantity = numericNames.filter((column) => /(qty|quantity|cantidad|units|unidades)/i.test(column))
    return discount.length === 1 && price.length === 1 && quantity.length === 1
      ? [[name, { operation: 'multiply' as const, inputs: [price[0], discount[0], quantity[0]] }]]
      : []
  }))
  return {
    summary: stringValue(decisions.summary, stringValue(item.proposal_document.summary, 'Propuesta dimensional')),
    grain_description: stringValue(decisions.grain_description, stringValue(objectValue(item.proposal_document.grain).description, 'Una fila por operación de negocio.')),
    dimension_names: arrayValue(decisions.dimensions).map((dimension) => stringValue(dimension.name, '')).filter(Boolean),
    measure_names: measures.map((measure) => stringValue(measure.name, '')).filter(Boolean),
    kpi_codes: decisionKpis.map((kpi) => stringValue(kpi.code, '')).filter((code) => code && includedKpis.has(code)),
    kpi_measure_names: Object.fromEntries(decisionKpis.map((kpi) => {
      const index = Number(kpi.measure_index ?? 0)
      return [stringValue(kpi.code, ''), stringValue(measures[index]?.name, '')]
    }).filter(([code, measure]) => code && measure)),
    measure_aggregations: Object.fromEntries(measures.map((measure) => [stringValue(measure.name, ''), stringValue(measure.aggregation, 'sum')])) as ProposalRevision['measure_aggregations'],
    measure_calculations: { ...derivedCalculations, ...storedCalculations },
    comment: '',
  }
}

function measureCalculationExplanation(item: Record<string, unknown>) {
  const calculation = objectValue(item.calculation)
  const operation = stringValue(calculation.operation, '')
  const inputs = stringArrayValue(calculation.inputs)
  if (!operation || inputs.length < 2) return ''
  const symbols: Record<string, string> = { multiply: '×', add: '+', subtract: '−', divide: '÷' }
  return `Cálculo por fila: ${inputs.join(` ${symbols[operation] ?? operation} `)}`
}

function localizedAdjustment(value: string) {
  return value
    .replace('mediante multiply', 'mediante multiplicación')
    .replace('mediante add', 'mediante suma por fila')
    .replace('mediante subtract', 'mediante resta por fila')
    .replace('mediante divide', 'mediante división protegida por fila')
}

function MeasureRevisionEditor({
  measures,
  draft,
  numericColumns,
  onChange,
}: {
  measures: Record<string, unknown>[]
  draft: ProposalRevision
  numericColumns: string[]
  onChange: (value: ProposalRevision) => void
}) {
  const operationLabels = {
    multiply: 'Multiplicar factores',
    add: 'Sumar componentes',
    subtract: 'Restar segundo valor al primero',
    divide: 'Dividir el primero para el segundo',
  }
  return <fieldset><legend>Medidas, agregaciones y cálculos controlados</legend>
    <p className="field-help">La plataforma aplica automáticamente las correcciones inequívocas. Si debe intervenir, sólo puede usar columnas numéricas existentes y operaciones seguras; nunca SQL libre.</p>
    <div className="revision-grid">{measures.map((item) => {
      const name = stringValue(item.name, '')
      const selected = draft.measure_names.includes(name)
      const calculation = draft.measure_calculations[name]
      const orderedOperation = calculation?.operation === 'subtract' || calculation?.operation === 'divide'
      const recommended = calculation && /(discount|descuento)/i.test(`${name} ${stringValue(item.source_column, '')}`)
      const updateCalculation = (next?: ProposalRevision['measure_calculations'][string]) => {
        const calculations = { ...draft.measure_calculations }
        if (next) calculations[name] = next
        else delete calculations[name]
        onChange({ ...draft, measure_calculations: calculations })
      }
      return <article className={calculation ? 'calculated-measure-card' : ''} key={name}>
        <label><input type="checkbox" checked={selected} onChange={() => {
          const dependentKpis = Object.entries(draft.kpi_measure_names).filter(([, measure]) => measure === name).map(([code]) => code)
          onChange({ ...draft, measure_names: selected ? draft.measure_names.filter((value) => value !== name) : [...draft.measure_names, name], kpi_codes: selected ? draft.kpi_codes.filter((code) => !dependentKpis.includes(code)) : draft.kpi_codes })
        }} /><span>{name}<small>{semanticRoleLabel(semanticRole(item))}</small></span></label>
        <label>Agregación<select aria-label={`Agregación de ${name}`} disabled={!selected} value={draft.measure_aggregations[name] ?? 'sum'} onChange={(event) => onChange({ ...draft, measure_aggregations: { ...draft.measure_aggregations, [name]: event.target.value as ProposalRevision['measure_aggregations'][string] } })}><option value="sum">Suma</option><option value="count">Conteo</option><option value="count_distinct">Conteo distinto</option><option value="average">Promedio</option><option value="min">Mínimo</option><option value="max">Máximo</option></select></label>
        {calculation ? <div className="controlled-calculation">
          <div><strong>{recommended ? 'Corrección automática recomendada' : 'Columna calculada controlada'}</strong><button className="secondary compact" type="button" onClick={() => updateCalculation()}>Usar columna directa</button></div>
          {recommended && <p>Se detectó una tasa usada como importe. La receta precio × tasa × cantidad produce el descuento monetario por fila.</p>}
          <label>Operación<select value={calculation.operation} onChange={(event) => updateCalculation({ operation: event.target.value as typeof calculation.operation, inputs: [] })}>{Object.entries(operationLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          {orderedOperation ? <div className="formula-operands">
            <label>Primer valor<select value={calculation.inputs[0] ?? ''} onChange={(event) => updateCalculation({ ...calculation, inputs: [event.target.value, calculation.inputs[1] ?? ''].filter(Boolean) })}><option value="">Seleccione una columna</option>{numericColumns.map((column) => <option key={column} value={column}>{column}</option>)}</select></label>
            <label>Segundo valor<select value={calculation.inputs[1] ?? ''} onChange={(event) => updateCalculation({ ...calculation, inputs: [calculation.inputs[0] ?? '', event.target.value].filter(Boolean) })}><option value="">Seleccione una columna</option>{numericColumns.filter((column) => column !== calculation.inputs[0]).map((column) => <option key={column} value={column}>{column}</option>)}</select></label>
          </div> : <fieldset className="formula-inputs"><legend>Factores o componentes, en orden</legend>{numericColumns.map((column) => <label key={column}><input type="checkbox" checked={calculation.inputs.includes(column)} disabled={!calculation.inputs.includes(column) && calculation.inputs.length >= 4} onChange={() => updateCalculation({ ...calculation, inputs: calculation.inputs.includes(column) ? calculation.inputs.filter((value) => value !== column) : [...calculation.inputs, column] })} />{column}</label>)}</fieldset>}
          <small>El sistema verificará tipo, existencia, cantidad de entradas y trazabilidad antes de crear la versión.</small>
        </div> : <button className="secondary compact" type="button" disabled={!selected || numericColumns.length < 2} onClick={() => updateCalculation({ operation: 'multiply', inputs: [] })}>Definir cálculo controlado</button>}
      </article>
    })}</div>
  </fieldset>
}

function SemanticCopilotPanel({
  token,
  proposal,
  concept,
  canAsk,
  onClose,
  onApply,
}: {
  token: string
  proposal: BiProposal
  concept: SemanticCandidate
  canAsk: boolean
  onClose: () => void
  onApply: (conclusion: SemanticAdvice['response_document']['conclusion']) => void
}) {
  const [messages, setMessages] = useState<SemanticAdvice[]>([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(true)
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState('')
  const quickQuestions = [
    '¿Por qué se recomienda incluir o excluir este concepto?',
    '¿Qué riesgo tendría incluir este concepto en el datamart?',
    'Explícame las claves y relaciones detectadas en lenguaje sencillo.',
  ]

  useEffect(() => {
    setLoading(true); setError(''); setQuestion('')
    void api.semanticAdvice(token, proposal.id, concept.business_concept)
      .then(setMessages)
      .catch((caught: Error) => setError(caught.message))
      .finally(() => setLoading(false))
  }, [concept.business_concept, proposal.id, token])

  async function ask() {
    if (question.trim().length < 10) return
    setAsking(true); setError('')
    try {
      const response = await api.askSemanticAdvice(token, proposal.id, { concept_code: concept.business_concept, question })
      setMessages((current) => [...current, response])
      setQuestion('')
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'No fue posible consultar al copiloto.')
    } finally { setAsking(false) }
  }

  return <section className="semantic-copilot" aria-label={`Copiloto para ${concept.business_name_es}`}>
    <div className="semantic-copilot-heading"><div><p className="eyebrow">Copiloto contextual</p><h3>{concept.business_name_es}</h3><p>Pregunta con el objetivo y el expediente de esta propuesta. La conversación no modifica selecciones por sí sola.</p></div><button type="button" className="secondary compact" onClick={onClose}>Cerrar</button></div>
    <div className="semantic-copilot-context"><span>Propuesta #{proposal.id}</span><span>{concept.technical_refs.join(', ')}</span><span>Sin filas, credenciales ni SQL libre</span></div>
    {loading && <p className="notice">Recuperando la conversación de este expediente…</p>}
    {!loading && messages.length === 0 && <p className="field-help">Todavía no hay consultas. Puede comenzar con una pregunta sugerida.</p>}
    <div className="semantic-conversation">{messages.map((message) => {
      const response = message.response_document
      const conclusionLabel = response.conclusion === 'include' ? 'Recomienda incluir' : response.conclusion === 'exclude' ? 'Recomienda excluir' : 'Requiere definición del negocio'
      return <article key={message.id}>
        <div className="analyst-question"><small>Pregunta del analista</small><p>{message.question}</p></div>
        <div className="copilot-answer"><div><strong>{conclusionLabel}</strong><span>Confianza {response.confidence === 'high' ? 'alta' : response.confidence === 'medium' ? 'media' : 'baja'}</span></div><p>{response.answer_es}</p>
          <dl><div><dt>Riesgo</dt><dd>{response.risk_es}</dd></div><div><dt>Si se incluye</dt><dd>{response.include_consequence_es}</dd></div><div><dt>Si se excluye</dt><dd>{response.exclude_consequence_es}</dd></div><div><dt>Acción sugerida</dt><dd>{response.recommended_action_es}</dd></div></dl>
          <details><summary>Evidencia citada</summary><ul>{response.evidence.map((item, index) => <li key={`${item.technical_ref}-${index}`}><strong>{item.technical_ref}</strong><span>{item.detail_es}</span></li>)}</ul></details>
          {response.conclusion !== 'define_business' && <button type="button" onClick={() => onApply(response.conclusion)}>Aplicar recomendación</button>}
          <small>{providerLabel(message.provider_kind)} · {message.model_id} · {new Date(message.created_at).toLocaleString('es-EC')}</small>
        </div>
      </article>
    })}</div>
    {error && <p className="notice error" role="alert">{error}</p>}
    <div className="semantic-quick-questions">{quickQuestions.map((item) => <button type="button" className="secondary compact" key={item} onClick={() => setQuestion(item)}>{item}</button>)}</div>
    <form onSubmit={(event) => { event.preventDefault(); void ask() }}><label>Pregunta para el copiloto<textarea rows={3} minLength={10} maxLength={500} value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ejemplo: ¿esta relación podría duplicar las ventas?" /></label><button disabled={!canAsk || asking || question.trim().length < 10}>{asking ? 'Analizando evidencia…' : 'Preguntar al copiloto'}</button></form>
    {!canAsk && <p className="field-help">Su perfil puede leer la conversación, pero no crear nuevas consultas.</p>}
  </section>
}

function AnalysisAssistantPage({ token, canGenerate, canReview, canPreviewSemantics, navigate }: { token: string; canGenerate: boolean; canReview: boolean; canPreviewSemantics: boolean; navigate: (path: string) => void }) {
  const recoveryDraft = useMemo(readAssistantDraft, [])
  const [readiness, setReadiness] = useState<CopilotReadiness | null>(null)
  const [source, setSource] = useState<ActiveSource | null>(null)
  const [catalog, setCatalog] = useState<CopilotCatalog | null>(null)
  const [selectedDomainCode, setSelectedDomainCode] = useState<string | null>(recoveryDraft?.domainCode ?? null)
  const [historyPage, setHistoryPage] = useState<Page<BiProposal>>({ items: [], total: 0, limit: historyPageSize, offset: 0 })
  const [historyFilter, setHistoryFilter] = useState('ready_for_review')
  const [historyOffset, setHistoryOffset] = useState(0)
  const [step, setStep] = useState(recoveryDraft?.step ?? 1)
  const [goal, setGoal] = useState(recoveryDraft?.goal ?? '')
  const [questions, setQuestions] = useState<string[]>(recoveryDraft?.questions ?? [])
  const [periodicity, setPeriodicity] = useState(recoveryDraft?.periodicity ?? 'month')
  const [needFormulation, setNeedFormulation] = useState<NeedFormulation | null>(null)
  const [viability, setViability] = useState<NeedViability | null>(null)
  const [acceptedLimitations, setAcceptedLimitations] = useState<string[]>([])
  const [formulatingNeed, setFormulatingNeed] = useState(false)
  const [validatingNeed, setValidatingNeed] = useState(false)
  const [proposal, setProposal] = useState<BiProposal | null>(null)
  const [draftProposalId, setDraftProposalId] = useState<number | undefined>(recoveryDraft?.proposalId)
  const [excludedConcepts, setExcludedConcepts] = useState<string[]>([])
  const [confirmedConcepts, setConfirmedConcepts] = useState<string[]>([])
  const [adviceConceptCode, setAdviceConceptCode] = useState<string | null>(null)
  const [revisionDraft, setRevisionDraft] = useState<ProposalRevision | null>(null)
  const [generating, setGenerating] = useState(false)
  const [savingRevision, setSavingRevision] = useState(false)
  const [relationCatalog, setRelationCatalog] = useState<ControlledRelationCatalog | null>(null)
  const [relationDimension, setRelationDimension] = useState('')
  const [relationOptionId, setRelationOptionId] = useState('')
  const [relationComment, setRelationComment] = useState('')
  const [savingRelation, setSavingRelation] = useState(false)
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'warning' | 'error'; message: string } | null>(null)
  const [reviewComment, setReviewComment] = useState('')
  const [warningsConfirmed, setWarningsConfirmed] = useState(false)
  const [cleanupReason, setCleanupReason] = useState('')
  const [restoreReason, setRestoreReason] = useState('')
  const [restoreWarningsConfirmed, setRestoreWarningsConfirmed] = useState(false)
  const [verification, setVerification] = useState<ProposalVerification | null>(null)
  const [verifying, setVerifying] = useState(false)
  const [semanticPreview, setSemanticPreview] = useState<SemanticPreview | null>(null)
  const [previewingSemantics, setPreviewingSemantics] = useState(false)
  const [recoveryNotice, setRecoveryNotice] = useState(recoveryDraft ? 'Recuperamos el borrador local. Compruebe la necesidad y continúe desde el paso guardado.' : '')
  const restoredProposal = useRef(false)

  useEffect(() => {
    if (!selectedDomainCode) return
    const draft: AssistantDraft = {
      version: 1,
      domainCode: selectedDomainCode,
      step,
      goal,
      questions,
      periodicity,
      proposalId: proposal?.id ?? draftProposalId,
    }
    localStorage.setItem(assistantDraftKey, JSON.stringify(draft))
  }, [draftProposalId, goal, periodicity, proposal?.id, questions, selectedDomainCode, step])

  useEffect(() => {
    if (!catalog || !recoveryDraft?.proposalId || restoredProposal.current) return
    restoredProposal.current = true
    void api.proposal(token, recoveryDraft.proposalId).then((savedProposal) => {
      setProposal(savedProposal)
      setDraftProposalId(savedProposal.id)
      setExcludedConcepts(defaultExcludedConcepts(savedProposal))
      setReviewComment(savedProposal.review_comment ?? '')
      setWarningsConfirmed(savedProposal.warnings_confirmed)
      setRevisionDraft(revisionFromProposal(savedProposal))
      setStep(recoveryDraft.step)
    }).catch(() => {
      setDraftProposalId(undefined)
      setStep(1)
      setRecoveryNotice('La versión guardada ya no está disponible. Conservamos la necesidad para que pueda validarla nuevamente.')
    })
  }, [catalog, recoveryDraft, token])

  async function refreshHistory(domainCode = selectedDomainCode, offset = historyOffset, filter = historyFilter) {
    if (!domainCode) return
    const statuses = historyFilterOptions.find((item) => item.value === filter)?.statuses ?? []
    const attempts = await api.proposals(token, historyPageSize, offset, statuses, domainCode)
    setHistoryPage(attempts)
  }

  useEffect(() => {
    Promise.all([api.copilotReadiness(token), api.activeSource(token)])
      .then(async ([ready, active]) => {
        setReadiness(ready)
        setSource(active)
        if (active.latest_snapshot) setCatalog(await api.copilotCatalog(token, active.latest_snapshot.id))
      })
      .catch((error: Error) => setFeedback({ kind: 'error', message: error.message }))
  }, [token])

  useEffect(() => {
    if (!selectedDomainCode) return
    const statuses = historyFilterOptions.find((item) => item.value === historyFilter)?.statuses ?? []
    void api.proposals(token, historyPageSize, historyOffset, statuses, selectedDomainCode)
      .then(setHistoryPage)
      .catch((error: Error) => setFeedback({ kind: 'error', message: error.message }))
  }, [historyFilter, historyOffset, selectedDomainCode, token])

  const selectedDomain = catalog?.domains.find((domain) => domain.code === selectedDomainCode)

  function selectDomain(code: string) {
    const domain = catalog?.domains.find((item) => item.code === code)
    if (!domain?.available) return
    setSelectedDomainCode(code)
    setGoal('')
    setQuestions([])
    setPeriodicity(domain.periodicities.find((item) => item.available)?.code ?? 'month')
    setNeedFormulation(null)
    setViability(null)
    setAcceptedLimitations([])
    setHistoryFilter('ready_for_review')
    setHistoryOffset(0)
    setProposal(null)
    setDraftProposalId(undefined)
    setSemanticPreview(null)
    setRevisionDraft(null)
    setConfirmedConcepts([])
    setAdviceConceptCode(null)
    setStep(1)
    setFeedback(null)
  }

  function changeDomain() {
    localStorage.removeItem(assistantDraftKey)
    setRecoveryNotice('')
    setSelectedDomainCode(null)
  }

  function toggleValue(value: string, values: string[], update: (items: string[]) => void) {
    update(values.includes(value) ? values.filter((item) => item !== value) : [...values, value])
  }

  function invalidateNeedAssessment() {
    setViability(null)
    setAcceptedLimitations([])
  }

  function needInput() {
    if (!source?.latest_snapshot || !selectedDomainCode) return null
    return {
      metadata_snapshot_id: source.latest_snapshot.id,
      business_goal: goal,
      business_questions: questions,
      periodicity,
      domain_code: selectedDomainCode as 'ventas',
    }
  }

  async function formulateNeed() {
    const payload = needInput()
    if (!payload) return
    setFormulatingNeed(true); setFeedback(null)
    try {
      setNeedFormulation(await api.formulateNeed(token, payload))
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible ayudar a formular la necesidad.' })
    } finally { setFormulatingNeed(false) }
  }

  async function validateNeed() {
    const payload = needInput()
    if (!payload) return
    setValidatingNeed(true); setFeedback(null)
    try {
      const assessment = await api.validateNeed(token, payload)
      setViability(assessment)
      setAcceptedLimitations([])
      setFeedback({ kind: assessment.can_continue ? (assessment.requires_acknowledgement.length ? 'warning' : 'success') : 'error', message: assessment.summary })
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible validar la viabilidad.' })
    } finally { setValidatingNeed(false) }
  }

  async function generate(exclusions = excludedConcepts) {
    if (!source?.latest_snapshot) return
    if (!viability) {
      setStep(1)
      setFeedback({ kind: 'warning', message: 'Valide la viabilidad de la necesidad antes de invocar a la IA.' })
      return
    }
    const unresolved = viability.requires_acknowledgement.filter((code) => !acceptedLimitations.includes(code))
    if (unresolved.length) {
      setFeedback({ kind: 'warning', message: 'Confirme cada requisito ambiguo o no disponible antes de continuar.' })
      return
    }
    setGenerating(true); setFeedback(null)
    try {
      const result = await api.createProposal(token, {
        metadata_snapshot_id: source.latest_snapshot.id,
        business_goal: goal,
        business_questions: questions,
        requested_dimensions: [],
        periodicity,
        domain_code: selectedDomainCode,
        excluded_concepts: exclusions,
        source_proposal_id: proposal?.id,
        viability_hash: viability.assessment_hash,
        accepted_limitations: acceptedLimitations,
      })
      setProposal(result)
      setSemanticPreview(null)
      setVerification(null)
      setExcludedConcepts(defaultExcludedConcepts(result))
      setConfirmedConcepts([])
      setAdviceConceptCode(null)
      setStep(2)
      await refreshHistory(selectedDomainCode, 0, historyFilter)
      setHistoryOffset(0)
      if (result.status === 'provider_failed') setFeedback({ kind: 'error', message: result.validation_document.issues[0]?.message ?? 'El proveedor no respondió.' })
    } catch (caught) {
      const networkFailure = caught instanceof TypeError && /fetch|network/i.test(caught.message)
      setFeedback({
        kind: 'error',
        message: networkFailure
          ? 'Se perdió la conexión del navegador mientras Ollama procesaba la propuesta. No la envíe de nuevo de inmediato: espere unos minutos y revise las versiones guardadas; el servidor puede haber terminado y conservado el resultado.'
          : caught instanceof Error ? caught.message : 'No fue posible generar la propuesta.',
      })
      await refreshHistory().catch(() => undefined)
    } finally { setGenerating(false) }
  }

  async function continueWithConcepts() {
    const originalExcluded = proposal ? defaultExcludedConcepts(proposal) : []
    if (proposal && [...originalExcluded].sort().join('|') !== [...excludedConcepts].sort().join('|')) await generate(excludedConcepts)
    else setStep(3)
  }

  async function decide(decision: 'approve' | 'reject') {
    if (!proposal) return
    setFeedback(null)
    try {
      const updated = decision === 'approve'
        ? await api.approveProposal(token, proposal.id, { comment: reviewComment || undefined, warnings_confirmed: warningsConfirmed })
        : await api.rejectProposal(token, proposal.id, reviewComment)
      setProposal(updated); setVerification(null); setStep(5)
      setSemanticPreview(null)
      await refreshHistory(selectedDomainCode, 0, historyFilter)
      setHistoryOffset(0)
      setFeedback({ kind: 'success', message: decision === 'approve' ? 'Propuesta aprobada. Quedó habilitada para la generación del datamart; todavía no se ejecutó ningún ETL.' : 'Propuesta rechazada. Puede ajustar la necesidad y crear una nueva versión.' })
    } catch (caught) { setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible registrar la decisión.' }) }
  }

  async function cleanVersion(action: 'invalidate' | 'discard') {
    if (!proposal || cleanupReason.trim().length < 10) return
    setFeedback(null)
    try {
      const updated = action === 'invalidate'
        ? await api.invalidateProposal(token, proposal.id, cleanupReason)
        : await api.discardProposal(token, proposal.id, cleanupReason)
      setProposal(updated); setVerification(null); setCleanupReason(''); setStep(5)
      setSemanticPreview(null)
      await refreshHistory(selectedDomainCode, 0, historyFilter)
      setHistoryOffset(0)
      setFeedback({ kind: 'success', message: action === 'invalidate' ? `Se retiró la aprobación de la versión #${updated.id}. Ya no podrá utilizarse en nuevas ejecuciones ETL.` : `La versión #${updated.id} quedó descartada y se conserva únicamente para auditoría.` })
    } catch (caught) { setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible depurar la versión.' }) }
  }

  function selectSavedProposal(item: BiProposal) {
    setProposal(item)
    setViability(null)
    setAcceptedLimitations([])
    setNeedFormulation(null)
    setVerification(null)
    setSemanticPreview(null)
    setGoal(item.business_goal)
    setQuestions(item.business_questions)
    setExcludedConcepts(defaultExcludedConcepts(item))
    setConfirmedConcepts([])
    setAdviceConceptCode(null)
    setReviewComment(item.review_comment ?? '')
    setWarningsConfirmed(item.warnings_confirmed)
    setCleanupReason('')
    setRestoreReason('')
    setRestoreWarningsConfirmed(false)
    setRevisionDraft(revisionFromProposal(item))
    setStep(['approved', 'rejected', 'invalidated', 'discarded'].includes(item.status) ? 5 : 3)
    setFeedback({
      kind: 'success',
      message: `Versión #${item.id} seleccionada: ${providerLabel(item.provider_kind)} / ${item.model_id}.`,
    })
  }

  async function verifyEvidence() {
    if (!proposal) return
    setVerifying(true); setFeedback(null)
    try {
      const result = await api.verifyProposal(token, proposal.id)
      setVerification(result)
      if (result.approval_invalidated && proposal.status === 'approved') {
        setProposal({ ...proposal, status: 'invalidated', review_comment: 'Aprobación retirada automáticamente porque la versión no supera las reglas vigentes.' })
        await refreshHistory(selectedDomainCode, 0, historyFilter)
      }
      setFeedback({
        kind: result.approval_safe ? (result.compatibility_warning ? 'warning' : 'success') : 'error',
        message: result.approval_safe
          ? result.compatibility_warning
            ? `La versión #${proposal.id} no presenta errores bloqueantes; las diferencias corresponden a compatibilidad entre versiones del motor.`
            : `La versión #${proposal.id} superó las validaciones disponibles en este sprint.`
          : `La versión #${proposal.id} presenta diferencias bloqueantes que deben revisarse.`,
      })
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible verificar la evidencia.' })
    } finally { setVerifying(false) }
  }

  async function previewSemanticIdentity() {
    if (!proposal) return
    setPreviewingSemantics(true); setFeedback(null)
    try {
      const result = await api.semanticPreview(token, proposal.id)
      setSemanticPreview(result)
      setFeedback({
        kind: result.all_passed ? 'success' : 'error',
        message: result.message,
      })
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible comprobar los nombres descriptivos.' })
    } finally { setPreviewingSemantics(false) }
  }

  async function restoreApproval() {
    if (!proposal || restoreReason.trim().length < 10) return
    setFeedback(null)
    try {
      const updated = await api.restoreProposalApproval(token, proposal.id, {
        comment: restoreReason,
        warnings_confirmed: restoreWarningsConfirmed,
      })
      setProposal(updated)
      setRestoreReason('')
      setRestoreWarningsConfirmed(false)
      await refreshHistory(selectedDomainCode, 0, historyFilter)
      setFeedback({ kind: 'success', message: `Se restauró de forma auditada la aprobación de la versión #${updated.id}.` })
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible restaurar la aprobación.' })
    }
  }

  function openPersonalization(item = proposal) {
    if (!item) return
    setRevisionDraft(revisionFromProposal(item))
    setRelationCatalog(null)
    setRelationDimension('')
    setRelationOptionId('')
    setRelationComment('')
    void api.relationOptions(token, item.id).then((catalog) => {
      setRelationCatalog(catalog)
      setRelationDimension(catalog.dimension_names[0] ?? '')
      setRelationOptionId(catalog.options.find((option) => option.eligible)?.option_id ?? '')
    }).catch((caught: Error) => setFeedback({ kind: 'error', message: caught.message }))
    setFeedback(null)
    setStep(4)
  }

  async function saveControlledRelation() {
    if (!proposal || !relationDimension || !relationOptionId || relationComment.trim().length < 10) return
    setSavingRelation(true); setFeedback(null)
    try {
      const revised = await api.reviseRelation(token, proposal.id, { dimension_name: relationDimension, option_id: relationOptionId, comment: relationComment })
      setProposal(revised)
      setRevisionDraft(revisionFromProposal(revised))
      setVerification(null)
      setRelationCatalog(null)
      setStep(3)
      await refreshHistory(selectedDomainCode, 0, historyFilter)
      setFeedback({ kind: revised.status === 'ready_for_review' ? 'success' : 'error', message: revised.status === 'ready_for_review' ? `La relación fue corregida en la versión #${revised.id} y volvió a superar todas las reglas.` : `La versión #${revised.id} conserva observaciones bloqueantes; revise la matriz de cobertura.` })
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible corregir la relación.' })
    } finally { setSavingRelation(false) }
  }

  async function saveRevision() {
    if (!proposal || !revisionDraft) return
    setSavingRevision(true); setFeedback(null)
    try {
      const revised = await api.reviseProposal(token, proposal.id, revisionDraft)
      setProposal(revised)
      setRevisionDraft(revisionFromProposal(revised))
      setVerification(null)
      setStep(3)
      setFeedback({ kind: revised.status === 'ready_for_review' ? 'success' : 'error', message: revised.status === 'ready_for_review' ? `La personalización creó la versión #${revised.id} y superó la validación estructural.` : `La versión #${revised.id} requiere correcciones antes de aprobarse.` })
      await refreshHistory(selectedDomainCode, 0, historyFilter)
      setHistoryOffset(0)
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible guardar la personalización.' })
    } finally { setSavingRevision(false) }
  }

  if (!readiness || !source) return <p className="notice">Comprobando fuente, metadatos y asistente de IA…</p>
  if (!readiness.ready) return <><p className="lead">Antes de analizar, complete los componentes pendientes.</p><div className="readiness-grid">{[readiness.source, readiness.metadata, readiness.llm].map((item) => <article className={item.ready ? 'ready' : 'pending'} key={item.label}><span className="status-dot" /><div><h2>{item.label}</h2><p>{item.detail}</p>{!item.ready && item.path && <button onClick={() => navigate(item.path!)}>Resolver</button>}</div></article>)}</div></>
  if (!catalog) return <p className="notice">Analizando las capacidades disponibles en la instantánea vigente…</p>
  if (!selectedDomain) return <>
    <p className="lead">Seleccione el tipo de datamart que desea diseñar. La plataforma sólo habilita dominios con perfil, metadatos y validadores implementados.</p>
    <section className="domain-catalog" aria-label="Tipos de datamart disponibles">
      {catalog.domains.map((domain) => <article className={domain.available ? 'available' : 'unavailable'} key={domain.code}>
        <p className="eyebrow">Dominio habilitado</p><h2>{domain.label}</h2><p>{domain.description}</p><p className="field-help">{domain.reason}</p>
        <button disabled={!domain.available} onClick={() => selectDomain(domain.code)}>{domain.available ? (canGenerate ? 'Crear propuesta' : 'Consultar versiones') : 'No disponible'}</button>
      </article>)}
    </section>
    <p className="notice">Actualmente se valida el datamart de ventas. Un nuevo dominio aparecerá aquí cuando incorpore su perfil y reglas, sin modificar esta pantalla.</p>
  </>

  const concepts = proposal?.semantic_map_document.candidates ?? []
  const adviceConcept = concepts.find((concept) => concept.business_concept === adviceConceptCode)
  const pendingConceptDecisions = concepts.filter((concept) => {
    const included = !excludedConcepts.includes(concept.business_concept)
    const needsDecision = concept.confidence === 'low' || ['review_required', 'decision_required'].includes(concept.evidence?.status ?? '')
    return included && needsDecision && !confirmedConcepts.includes(concept.business_concept)
  })
  const document = proposal?.proposal_document ?? {}
  const fact = objectValue(document.fact)
  const grain = objectValue(document.grain)
  const dimensionsDocument = arrayValue(document.dimensions)
  const kpis = arrayValue(document.kpis)
  const etlPlan = arrayValue(document.etl_plan)
  const automaticAdjustments = stringArrayValue(document.automatic_adjustments)
  const providerObservations = stringArrayValue(document.provider_observations)
  const decisionDiagnostics = arrayValue(document.decision_diagnostics)
  const requirementCoverage = arrayValue(document.requirement_coverage)
  const semanticQuality = arrayValue(document.semantic_quality)
  const validation = proposal?.validation_document
  const revisionDecisions = objectValue(proposal?.proposal_document.ai_decisions)
  const revisionDimensions = arrayValue(revisionDecisions.dimensions)
  const revisionMeasures = arrayValue(revisionDecisions.measures)
  const revisionKpis = arrayValue(revisionDecisions.kpis)
  const revisionFactSource = stringValue(revisionDecisions.fact_source, '')
  const revisionNumericColumns = (proposal?.scope_document.tables ?? [])
    .find((table) => table.ref === revisionFactSource)?.columns
    ?.filter((column) => /tinyint|smallint|int|bigint|decimal|numeric|money|float|real/i.test(column.type))
    .map((column) => column.name) ?? []
  const selectedRelationOption = relationCatalog?.options?.find((item) => item.option_id === relationOptionId)
  return <>
    <div className="assistant-context"><div><p className="eyebrow">Dominio seleccionado</p><strong>{selectedDomain.label}</strong><span>{source.connection?.name} · instantánea #{source.latest_snapshot?.id}</span></div><button className="secondary" onClick={changeDomain}>Cambiar tipo de datamart</button></div>
    <p className="lead">Describa una necesidad comercial. La IA interpretará metadatos, propondrá el modelo y la aplicación comprobará cada referencia antes de su revisión.</p>
    <ol className="assistant-stepper" aria-label={`Paso ${step} de 5`}>{['Necesidad', 'Conceptos', 'Propuesta', 'Personalización', 'Revisión'].map((label, index) => <li className={step === index + 1 ? 'current' : step > index + 1 ? 'complete' : ''} key={label}><span>{index + 1}</span>{label}</li>)}</ol>
    {recoveryNotice && <p className="notice success" role="status"><strong>Avance restaurado.</strong> {recoveryNotice}</p>}
    {feedback && <p className={`notice ${feedback.kind}`} role={feedback.kind === 'error' ? 'alert' : 'status'}>{feedback.message}</p>}
    {step === 1 && <form className="analysis-panel" onSubmit={(event) => { event.preventDefault(); if (viability) void generate([]); else void validateNeed() }}>
      <div className="form-title"><div><p className="eyebrow">Paso 1</p><h2>Necesidad de negocio</h2></div><span>Se enviarán la necesidad y metadatos estructurales; nunca filas ni credenciales.</span></div>
      <label className="need-goal-field">Objetivo del análisis<textarea required minLength={20} maxLength={2000} rows={12} value={goal} placeholder="Ejemplo: analizar ventas netas, costos y margen por producto y territorio, comparando su evolución mensual." onChange={(event) => { setGoal(event.target.value); setNeedFormulation(null); invalidateNeedAssessment() }} /><span className="character-counter" aria-live="polite">{goal.length.toLocaleString('es-EC')} / 2.000 caracteres</span><small className="field-help">Explique qué decisión desea apoyar, qué indicadores espera y cómo necesita compararlos. No escriba SQL.</small></label>
      <div className="need-assistance-actions"><button type="button" className="secondary" disabled={!canGenerate || formulatingNeed || goal.trim().length < 20 || questions.length === 0} onClick={() => void formulateNeed()}>{formulatingNeed ? 'Preparando una redacción…' : 'Ayúdame a formular la necesidad'}</button><small>La IA sólo propone una redacción; usted decide si la usa.</small></div>
      {needFormulation && <section className="need-formulation" aria-label="Propuesta de redacción"><div><p className="eyebrow">Sugerencia de la IA</p><h3>Redacción propuesta</h3><p>{needFormulation.suggested_goal}</p></div><p className="field-help">{needFormulation.rationale}</p>{needFormulation.improvements.length > 0 && <ul>{needFormulation.improvements.map((item) => <li key={item}>{item}</li>)}</ul>}<div className="form-actions"><button type="button" onClick={() => { setGoal(needFormulation.suggested_goal); setNeedFormulation(null); invalidateNeedAssessment() }}>Usar esta redacción</button><button type="button" className="secondary" onClick={() => setNeedFormulation(null)}>Mantener mi redacción</button></div></section>}
      <fieldset><legend>Preguntas de negocio disponibles</legend><p className="field-help">Seleccione las preguntas que orientarán a la IA. No fijan tablas, columnas ni dimensiones.</p><div className="choice-grid">{selectedDomain.questions.map((item) => <label className={!item.available ? 'unavailable-choice' : ''} title={item.reason} key={item.code}><input type="checkbox" disabled={!item.available} checked={questions.includes(item.code)} onChange={() => { toggleValue(item.code, questions, setQuestions); setNeedFormulation(null); invalidateNeedAssessment() }} /><span>{item.label}<small>{item.description}</small></span></label>)}</div></fieldset>
      <p className="notice">La IA propondrá las dimensiones, medidas, granularidad, KPIs y plan ETL a partir del objetivo, las preguntas seleccionadas y los metadatos verificados. Usted podrá revisarlos y personalizarlos sin escribir SQL.</p>
      <label>Periodicidad<select value={periodicity} onChange={(event) => { setPeriodicity(event.target.value); setNeedFormulation(null); invalidateNeedAssessment() }}>{selectedDomain.periodicities.filter((item) => item.available).map((item) => <option value={item.code} key={item.code}>{item.label}</option>)}</select></label>
      {viability && <section className="need-viability" aria-label="Cobertura de la necesidad"><div className="need-viability-heading"><div><p className="eyebrow">Comprobación previa</p><h3>Viabilidad contra los metadatos</h3></div><span>{viability.counts.direct ?? 0} directos · {viability.counts.derivable ?? 0} derivables · {(viability.counts.ambiguous ?? 0) + (viability.counts.unavailable ?? 0)} por decidir</span></div><div className="need-requirement-list">{viability.requirements.map((item) => { const pending = item.status === 'ambiguous' || item.status === 'unavailable'; return <article className={`need-requirement ${item.status}`} key={item.code}><div><span className="need-status">{item.status === 'direct' ? 'Directo' : item.status === 'derivable' ? 'Derivable' : item.status === 'ambiguous' ? 'Ambiguo' : 'No disponible'}</span><h4>{item.label}</h4></div>{item.formula && <p><strong>Fórmula controlada:</strong> {item.formula}</p>}<p>{item.resolution}</p>{item.evidence.length > 0 && <details><summary>Ver evidencia técnica</summary><ul>{item.evidence.map((evidence) => <li key={evidence}>{evidence}</li>)}</ul></details>}{pending && <label className="confirmation"><input type="checkbox" checked={acceptedLimitations.includes(item.code)} onChange={() => toggleValue(item.code, acceptedLimitations, setAcceptedLimitations)} />Comprendo esta limitación y acepto continuar sin que el sistema invente una solución.</label>}</article> })}</div></section>}
      {!viability && <button disabled={!canGenerate || validatingNeed || questions.length === 0 || goal.trim().length < 20}>{validatingNeed ? 'Contrastando con la fuente…' : 'Validar viabilidad'}</button>}
      {viability && <div className="form-actions"><button disabled={!canGenerate || generating || !viability.can_continue || viability.requires_acknowledgement.some((code) => !acceptedLimitations.includes(code))}>{generating ? 'Preparando e interpretando metadatos…' : 'Generar conceptos y propuesta'}</button><button type="button" className="secondary" onClick={() => { setViability(null); setAcceptedLimitations([]) }}>Volver a editar</button></div>}
      {!canGenerate && <p className="field-help">Su perfil puede consultar propuestas, pero no generar nuevos intentos.</p>}
    </form>}
    {step === 2 && proposal && <section className="analysis-panel">
      <div className="form-title"><div><p className="eyebrow">Paso 2 · Propuesto por IA</p><h2>Conceptos encontrados</h2></div><span>Las referencias ya fueron comprobadas contra la instantánea.</span></div>
      <p className="notice">La plataforma valida primero la estructura. Los conceptos con evidencia débil quedan excluidos preventivamente; puede incluirlos mediante una decisión guiada, sin abrir DBeaver ni escribir SQL.</p>
      {concepts.length === 0 ? <p className="notice error">No se encontró un alcance verificable. Modifique la necesidad y cree otro intento.</p> : <div className="concept-grid">{concepts.map((concept) => {
        const excluded = excludedConcepts.includes(concept.business_concept)
        const evidenceStatus = concept.evidence?.status ?? (concept.confidence === 'low' ? 'decision_required' : concept.confidence === 'medium' ? 'review_required' : 'confirmed')
        const needsDecision = ['review_required', 'decision_required'].includes(evidenceStatus)
        const confirmed = confirmedConcepts.includes(concept.business_concept)
        const evidenceLabel = evidenceStatus === 'confirmed' ? 'Confirmado automáticamente' : evidenceStatus === 'structurally_supported' ? 'Estructura respaldada' : evidenceStatus === 'review_required' ? 'Evidencia insuficiente' : 'Decisión de negocio requerida'
        return <article className={`${excluded ? 'excluded' : ''} concept-decision-card`} key={`${concept.business_concept}-${concept.technical_refs.join('-')}`}>
          <div className="concept-heading"><label><input type="checkbox" checked={!excluded} onChange={() => {
            toggleValue(concept.business_concept, excludedConcepts, setExcludedConcepts)
            setConfirmedConcepts((current) => current.filter((item) => item !== concept.business_concept))
          }} />Incluir</label><span className={`confidence ${concept.confidence}`}>{concept.confidence === 'high' ? 'Confianza alta' : concept.confidence === 'medium' ? 'Confianza media' : 'Revisar'}</span></div>
          <h3>{concept.business_name_es}</h3><p>{concept.description_es}</p>
          <div className={`semantic-decision-status ${evidenceStatus}`}><strong>{evidenceLabel}</strong><span>{concept.evidence?.guidance ?? concept.reason}</span></div>
          <details className="semantic-evidence" open={needsDecision}><summary>Ver evidencia y cómo resolver</summary>
            <div className="semantic-origin"><strong>Origen técnico comprobado</strong><span>{concept.technical_refs.join(', ')}</span><p>{concept.reason}</p></div>
            {(concept.evidence?.checks ?? []).map((check, index) => <div className={`semantic-check ${check.passed ? 'pass' : 'review'}`} key={`${check.code}-${index}`}><span aria-hidden="true">{check.passed ? '✓' : '!'}</span><div><strong>{check.label}</strong><small>{check.detail}</small></div></div>)}
            {!concept.evidence?.checks?.length && <p className="field-help">La referencia existe, pero esta versión fue creada antes del expediente visual. Puede excluirla o generar un nuevo análisis para obtener comprobaciones detalladas.</p>}
          </details>
          {!excluded && needsDecision && <button type="button" className={confirmed ? 'secondary compact decision-confirmed' : 'secondary compact'} onClick={() => setConfirmedConcepts((current) => confirmed ? current.filter((item) => item !== concept.business_concept) : [...current, concept.business_concept])}>{confirmed ? 'Inclusión confirmada' : 'Confirmar inclusión excepcional'}</button>}
          <button type="button" className="secondary compact" onClick={() => setAdviceConceptCode(concept.business_concept)}>Consultar al copiloto</button>
          {excluded && needsDecision && <p className="field-help safe-exclusion">Excluido de la propuesta. No afecta la fuente ni elimina información.</p>}
        </article>
      })}</div>}
      {proposal && adviceConcept && <SemanticCopilotPanel token={token} proposal={proposal} concept={adviceConcept} canAsk={canGenerate} onClose={() => setAdviceConceptCode(null)} onApply={(conclusion) => {
        if (conclusion === 'include') {
          setExcludedConcepts((current) => current.filter((item) => item !== adviceConcept.business_concept))
          setConfirmedConcepts((current) => current.includes(adviceConcept.business_concept) ? current : [...current, adviceConcept.business_concept])
          setFeedback({ kind: 'success', message: `${adviceConcept.business_name_es} quedó incluido por decisión explícita. La nueva propuesta volverá a validar el alcance.` })
        } else if (conclusion === 'exclude') {
          setExcludedConcepts((current) => current.includes(adviceConcept.business_concept) ? current : [...current, adviceConcept.business_concept])
          setConfirmedConcepts((current) => current.filter((item) => item !== adviceConcept.business_concept))
          setFeedback({ kind: 'success', message: `${adviceConcept.business_name_es} quedó excluido de esta propuesta; la fuente permanece intacta.` })
        }
      }} />}
      {pendingConceptDecisions.length > 0 && <p className="notice warning">Antes de continuar, confirme la inclusión de: {pendingConceptDecisions.map((item) => item.business_name_es).join(', ')}. También puede volver a desmarcarlos.</p>}
      <div className="form-actions"><button disabled={!concepts.length || excludedConcepts.length === concepts.length || generating || pendingConceptDecisions.length > 0} onClick={() => void continueWithConcepts()}>{generating ? 'Generando nueva versión…' : 'Generar propuesta BI'}</button>{Boolean(proposal.proposal_document.summary) && <button className="secondary" onClick={() => { setAdviceConceptCode(null); setStep(3) }}>Volver a la propuesta actual</button>}<button className="secondary" onClick={() => setStep(1)}>Modificar necesidad</button></div>
    </section>}
    {step === 3 && proposal && <section className="analysis-panel">
      <div className="proposal-heading"><div><p className="eyebrow">Paso 3 · Propuesta de IA + comprobación automática</p><h2>{stringValue(document.summary, 'Propuesta BI de ventas')}</h2></div><span className={`proposal-status ${proposal.status}`}>{proposalStatusLabels[proposal.status]}</span></div>
      <p className="business-explanation">{stringValue(document.business_explanation, 'El proveedor no entregó una explicación de negocio utilizable.')}</p>
      {validation && <div className={`validation-summary ${validation.valid ? 'success' : 'error'}`}><strong>{validation.valid ? 'Referencias y contrato validados' : 'No puede aprobarse'}</strong><span>{validation.errors} errores · {validation.warnings} advertencias</span></div>}
      <div className="proposal-grid"><article><h3>Granularidad</h3><p>{stringValue(grain.description, '—')}</p>{stringArrayValue(grain.business_keys).length > 0 && <small><b>Clave del grano:</b> {stringArrayValue(grain.business_keys).join(' + ')}</small>}</article><article><h3>Hecho y medidas</h3><p><strong>{stringValue(fact.name, '—')}</strong></p>{arrayValue(fact.measures).map((item, index) => { const provenance = objectValue(item.provenance); return <div className="measure-contract" key={index}><strong>{stringValue(item.name, 'Medida')}</strong><span>{stringValue(item.aggregation, '')}</span>{measureCalculationExplanation(item) && <small className="calculation-summary">{measureCalculationExplanation(item)}</small>}<small><b>Origen:</b> {stringArrayValue(provenance.source_references).join(', ') || 'Pendiente de comprobar'}</small><small><b>Fórmula:</b> {stringValue(provenance.formula, 'Pendiente de comprobar')}</small></div> })}</article><article><h3>Dimensiones</h3>{dimensionsDocument.map((item, index) => {
        const displayLabel = objectValue(item.display_label)
        const generatedLabel = stringValue(displayLabel.target_name, '')
        const defaultTypeField = `tipo_${stringValue(item.name, 'entidad').replace(/^dim_/, '')}`
        const generatedType = stringValue(displayLabel.type_target_name, defaultTypeField)
        const sourceAttributes = stringArrayValue(item.attributes)
        return <div className="dimension-contract" key={index}>
          <strong>{stringValue(item.name, 'Dimensión')}</strong>
          <small><b>Columnas de origen:</b> {sourceAttributes.join(', ') || 'Sin atributos propuestos'}</small>
          {generatedLabel && <div className="generated-fields"><span>Campos que creará el ETL</span><strong>{generatedLabel}</strong><strong>{generatedType}</strong><small>Nombre descriptivo y tipo derivados mediante relaciones verificadas.</small></div>}
        </div>
      })}</article><article><h3>KPIs propuestos</h3>{kpis.map((item, index) => <p key={index}><strong>{stringValue(item.name, 'KPI')}</strong><br /><small>{stringValue(item.code, '')}</small></p>)}</article></div>
      {requirementCoverage.length > 0 && <section className="requirement-coverage-panel" aria-label="Cobertura de la necesidad"><div><p className="eyebrow">Trazabilidad funcional</p><h3>De la necesidad al datamart</h3><p>Ningún requisito se descarta silenciosamente. Cada fila indica qué salida lo resuelve o qué decisión permanece pendiente.</p></div><div className="requirement-coverage-list">{requirementCoverage.map((item, index) => { const status = stringValue(item.coverage_status, 'not_covered'); return <article className={status} key={`${stringValue(item.requirement_code, '')}-${index}`}><div><span>{status === 'covered' ? 'Cubierto' : status === 'accepted_limitation' ? 'Limitación aceptada' : status === 'human_decision' ? 'Decisión humana' : 'No cubierto'}</span><h4>{stringValue(item.label, 'Requisito')}</h4></div><p>{stringValue(item.explanation, '')}</p>{stringArrayValue(item.outputs).length > 0 && <small><b>Salidas:</b> {stringArrayValue(item.outputs).join(', ')}</small>}</article> })}</div></section>}
      {semanticQuality.length > 0 && <section className="semantic-resolution-panel" aria-label="Calidad descriptiva de las dimensiones">
        <div className="semantic-resolution-heading"><div><p className="eyebrow">Control de identidad descriptiva</p><h3>Nombres reconocibles antes de materializar</h3><p>La plataforma recorre relaciones verificadas y comprueba que cada entidad pueda mostrarse con un nombre, no sólo con una clave técnica.</p></div>{canPreviewSemantics && <button type="button" className="secondary" disabled={previewingSemantics} onClick={() => void previewSemanticIdentity()}>{previewingSemantics ? 'Comprobando la fuente…' : 'Comprobar nombres y cobertura'}</button>}</div>
        <div className="semantic-resolution-grid">{semanticQuality.map((item, index) => <article className={stringValue(item.status, '') === 'resolved' ? 'passed' : 'review'} key={`${stringValue(item.dimension, '')}-${index}`}><span>{stringValue(item.status, '') === 'resolved' ? 'Ruta resuelta' : 'Revisión necesaria'}</span><h4>{businessTechnicalLabel(stringValue(item.dimension, 'Dimensión'))}</h4><p>{stringValue(item.message, '')}</p>{arrayValue(item.variants).map((variant, variantIndex) => <div className="semantic-route" key={`${stringValue(variant.source_table, '')}-${variantIndex}`}><strong>{stringValue(variant.kind, 'entity') === 'person' ? 'Persona' : stringValue(variant.kind, '') === 'organization' ? 'Organización' : 'Entidad base'}</strong><small>{stringValue(variant.source_table, '')} · {stringArrayValue(variant.columns).join(' + ')}</small></div>)}</article>)}</div>
        {!canPreviewSemantics && <p className="field-help">Su rol puede revisar el contrato, pero no consultar muestras de la fuente.</p>}
        {semanticPreview && <div className="semantic-preview-results"><div className={`validation-summary ${semanticPreview.all_passed ? 'success' : 'error'}`}><strong>{semanticPreview.all_passed ? 'Cobertura descriptiva aprobada' : 'La publicación debe bloquearse'}</strong><span>{semanticPreview.message}</span></div>{semanticPreview.dimensions.map((item) => <article key={item.dimension}><div className="semantic-preview-metrics"><div><small>Dimensión</small><strong>{businessTechnicalLabel(item.dimension)}</strong></div><div><small>Cobertura</small><strong>{(item.coverage * 100).toLocaleString('es-EC', { maximumFractionDigits: 1 })}%</strong></div><div><small>Entidades</small><strong>{item.total_entities.toLocaleString('es-EC')}</strong></div><div><small>Sin nombre descriptivo</small><strong>{item.fallback_entities.toLocaleString('es-EC')}</strong></div></div><details><summary>Ver muestra controlada y origen</summary><p className="field-help">Origen: {item.source_table} · columna destino: {item.label_column}. La muestra permanece dentro de la plataforma y no se envía al LLM.</p><div className="table-wrap"><table><thead><tr><th>Clave de negocio</th><th>Tipo</th><th>Nombre resultante</th></tr></thead><tbody>{item.samples.map((sample) => <tr key={`${item.dimension}-${sample.business_key}`}><td>{sample.business_key}</td><td>{sample.entity_type}</td><td><strong>{sample.display_label}</strong></td></tr>)}</tbody></table></div></details></article>)}</div>}
      </section>}
      <section className="etl-preview" aria-label="Vista previa del plan ETL"><h3>Plan ETL declarativo</h3><div>{etlPlan.map((item, index) => <article key={index}><span>{index + 1}</span><strong>{etlLabel(stringValue(item.operation, ''))}</strong><small>{stringValue(item.description, '')}</small></article>)}</div><p className="field-help">Vista de sólo lectura. La carga se ejecutará únicamente después de aprobar y confirmar la propuesta en Generación de datamart.</p></section>
      {automaticAdjustments.length > 0 && <details className="technical-details adjustments" open><summary>Ajustes automáticos aplicados</summary><p className="field-help">El sistema corrigió estas decisiones antes de validar; no requieren confirmación.</p>{automaticAdjustments.map((item) => <p className="adjustment" key={item}><strong>Ajuste:</strong> {localizedAdjustment(item)}</p>)}</details>}
      {validation && validation.issues.length > 0 && <details className="technical-details"><summary>Validaciones y advertencias</summary>{validation.issues.map((issue, index) => <p className={issue.level} key={`${issue.code}-${index}`}><strong>{issue.level === 'error' ? 'Error' : 'Advertencia'}:</strong> {issue.message}</p>)}</details>}
      {decisionDiagnostics.some((item) => item.status === 'excluded') && <section className="remediation-panel"><h3>Decisiones que requieren intervención</h3>{decisionDiagnostics.filter((item) => item.status === 'excluded').map((item) => <article key={stringValue(item.code, '')}><strong>{stringValue(item.code, 'KPI')}</strong><p>{stringValue(item.reason, 'La decisión no es compatible con el contrato validado.')}</p><p><b>Acción:</b> abra <em>Personalizar propuesta</em> para excluirla o reasignarla a una medida compatible. Si no aparece una medida compatible, genere una nueva versión solicitando expresamente esa medida.</p></article>)}</section>}
      <details className="technical-details"><summary>Detalles técnicos y trazabilidad</summary><p>Instantánea #{proposal.metadata_snapshot_id} · huella {proposal.input_hash.slice(0, 12)} · {providerLabel(proposal.provider_kind)} / {proposal.model_id}</p><p>Tablas incluidas: {(proposal.scope_document.tables ?? []).map((item) => item.ref).join(', ')}</p>{providerObservations.length > 0 && <><h3>Observaciones originales del proveedor</h3><p className="field-help">Se conservan sólo para trazabilidad. No se consideran comprobaciones hasta que las reglas del sistema las confirmen.</p>{providerObservations.map((item) => <p key={item}>{item}</p>)}</>}</details>
      <div className="form-actions">{proposal.status === 'ready_for_review' && <><button onClick={() => openPersonalization()}>Personalizar propuesta</button><button className="secondary" onClick={() => setStep(5)}>Continuar a revisión</button></>}<button className="secondary" onClick={() => setStep(2)}>Ajustar conceptos</button><button className="secondary" onClick={() => setStep(1)}>Crear nueva versión con IA</button></div>
    </section>}
    {step === 4 && proposal && revisionDraft && <section className="analysis-panel revision-panel">
      <div className="form-title"><div><p className="eyebrow">Paso 4 · Supervisión del analista BI</p><h2>Personalizar sin escribir SQL</h2></div><span>Los ajustes crean una nueva versión y vuelven a pasar por las reglas determinísticas.</span></div>
      <label>Resumen de negocio<input maxLength={160} value={revisionDraft.summary} onChange={(event) => setRevisionDraft({ ...revisionDraft, summary: event.target.value })} /></label>
      <label>Granularidad propuesta<textarea rows={2} maxLength={240} value={revisionDraft.grain_description} onChange={(event) => setRevisionDraft({ ...revisionDraft, grain_description: event.target.value })} /></label>
      <fieldset><legend>Dimensiones incluidas</legend><div className="choice-grid">{revisionDimensions.map((item) => { const name = stringValue(item.name, ''); return <label key={name}><input type="checkbox" checked={revisionDraft.dimension_names.includes(name)} onChange={() => setRevisionDraft({ ...revisionDraft, dimension_names: revisionDraft.dimension_names.includes(name) ? revisionDraft.dimension_names.filter((value) => value !== name) : [...revisionDraft.dimension_names, name] })} />{name}</label> })}</div></fieldset>
      <MeasureRevisionEditor measures={revisionMeasures} draft={revisionDraft} numericColumns={revisionNumericColumns} onChange={setRevisionDraft} />
      <fieldset><legend>KPIs incluidos y medida asociada</legend><div className="kpi-revision-grid">{revisionKpis.map((item) => { const code = stringValue(item.code, ''); const role = semanticRole(item); const compatible = revisionMeasures.filter((measure) => semanticRole(measure) === role && revisionDraft.measure_names.includes(stringValue(measure.name, ''))); const selectedMeasure = revisionDraft.kpi_measure_names[code] ?? ''; const unavailable = compatible.length === 0; const selected = revisionDraft.kpi_codes.includes(code); return <article className={unavailable ? 'unavailable-choice' : ''} key={code}><label><input type="checkbox" disabled={unavailable} checked={!unavailable && selected} onChange={() => { const nextSelected = !selected; const fallback = compatible.some((measure) => stringValue(measure.name, '') === selectedMeasure) ? selectedMeasure : stringValue(compatible[0]?.name, ''); setRevisionDraft({ ...revisionDraft, kpi_codes: nextSelected ? [...revisionDraft.kpi_codes, code] : revisionDraft.kpi_codes.filter((value) => value !== code), kpi_measure_names: { ...revisionDraft.kpi_measure_names, [code]: fallback } }) }} /><span>{stringValue(item.name, code)}<small>{semanticRoleLabel(role)}</small></span></label>{unavailable ? <p><strong>No disponible:</strong> no existe una medida seleccionada con la misma función semántica. Excluya este KPI o genere una versión que incluya esa medida.</p> : <label>Medida compatible<select aria-label={`Medida para ${stringValue(item.name, code)}`} disabled={!selected} value={compatible.some((measure) => stringValue(measure.name, '') === selectedMeasure) ? selectedMeasure : stringValue(compatible[0]?.name, '')} onChange={(event) => setRevisionDraft({ ...revisionDraft, kpi_measure_names: { ...revisionDraft.kpi_measure_names, [code]: event.target.value } })}>{compatible.map((measure) => { const name = stringValue(measure.name, ''); return <option value={name} key={name}>{name}</option> })}</select></label>}</article> })}</div></fieldset>
      <section className="relation-correction-panel" aria-labelledby="relation-correction-title">
        <div className="relation-correction-heading">
          <div><p className="eyebrow">Corrección guiada opcional</p><h3 id="relation-correction-title">Resolver una relación con evidencia</h3></div>
          <span>Sin SQL libre</span>
        </div>
        <p>Use esta herramienta sólo si una dimensión apunta al origen equivocado. La plataforma ofrece exclusivamente relaciones declaradas en la instantánea, descarta las que podrían multiplicar filas y vuelve a validar toda la propuesta.</p>
        {!relationCatalog && <p className="notice">Comprobando claves, tipos, cardinalidad y unicidad de las relaciones disponibles…</p>}
        {relationCatalog && <>
          <div className="relation-selector-grid">
            <label>Dimensión que desea corregir<select value={relationDimension} onChange={(event) => setRelationDimension(event.target.value)}>{relationCatalog.dimension_names.map((name) => <option value={name} key={name}>{businessTechnicalLabel(name)}</option>)}</select></label>
            <label>Ruta de relación comprobada<select value={relationOptionId} onChange={(event) => setRelationOptionId(event.target.value)}><option value="">Seleccione una relación segura</option>{relationCatalog.options.map((option) => <option disabled={!option.eligible} value={option.option_id} key={option.option_id}>{option.left_table}.{option.left_columns.join(' + ')} → {option.right_table}.{option.right_columns.join(' + ')}{option.eligible ? '' : ' — no habilitada'}</option>)}</select></label>
          </div>
          {selectedRelationOption && <article className={`relation-evidence ${selectedRelationOption.eligible ? 'eligible' : 'blocked'}`}>
            <div className="relation-evidence-title"><strong>{selectedRelationOption.eligible ? 'Relación apta para revalidar' : 'Relación bloqueada'}</strong><span>{selectedRelationOption.cardinality === 'many_to_one' ? 'Muchos a uno' : selectedRelationOption.cardinality === 'one_to_one' ? 'Uno a uno' : selectedRelationOption.cardinality === 'one_to_many' ? 'Uno a muchos' : 'Cardinalidad no demostrada'}</span></div>
            <div className="relation-evidence-grid"><div><small>Tipos de origen</small><b>{selectedRelationOption.left_types.join(', ')}</b></div><div><small>Tipos de destino</small><b>{selectedRelationOption.right_types.join(', ')}</b></div><div><small>Destino único</small><b>{selectedRelationOption.target_unique ? 'Sí' : 'No'}</b></div><div><small>Riesgo de duplicación</small><b>{selectedRelationOption.duplication_risk ? 'Bloqueante' : 'No detectado'}</b></div></div>
            <p>{selectedRelationOption.guidance}</p>
          </article>}
          {relationCatalog.options.some((option) => !option.eligible) && <details className="technical-details"><summary>Por qué otras relaciones están bloqueadas</summary>{relationCatalog.options.filter((option) => !option.eligible).map((option) => <p key={option.option_id}><strong>{option.left_table} → {option.right_table}:</strong> {option.guidance}</p>)}</details>}
          <label>Justificación de esta corrección<textarea rows={3} minLength={10} maxLength={500} value={relationComment} onChange={(event) => setRelationComment(event.target.value)} placeholder="Explique qué concepto de negocio debe representar la dimensión y por qué esta ruta es la correcta." /></label>
          <button type="button" disabled={savingRelation || !selectedRelationOption?.eligible || !relationDimension || relationComment.trim().length < 10} onClick={() => void saveControlledRelation()}>{savingRelation ? 'Creando y revalidando la versión…' : 'Crear versión con relación corregida'}</button>
          <p className="field-help">Esta acción es independiente de los cambios generales de la sección inferior. Si la utiliza, se creará inmediatamente una nueva versión auditable.</p>
        </>}
      </section>
      <label>Justificación del ajuste<textarea required minLength={10} maxLength={500} rows={3} value={revisionDraft.comment} onChange={(event) => setRevisionDraft({ ...revisionDraft, comment: event.target.value })} placeholder="Explique por qué este ajuste representa mejor la necesidad del negocio." /></label>
      <p className="notice">No puede inventar tablas, columnas, relaciones ni fórmulas. Si una selección deja de ser coherente, el backend rechazará o bloqueará la nueva versión.</p>
      <div className="form-actions"><button disabled={savingRevision || revisionDraft.comment.trim().length < 10 || revisionDraft.dimension_names.length === 0 || revisionDraft.measure_names.length === 0 || revisionDraft.kpi_codes.length === 0} onClick={() => void saveRevision()}>{savingRevision ? 'Validando nueva versión…' : 'Guardar como nueva versión'}</button><button className="secondary" onClick={() => setStep(5)}>Continuar sin cambios</button><button className="secondary" onClick={() => setStep(3)}>Cancelar</button></div>
    </section>}
    {step === 5 && proposal && <section className="analysis-panel review-panel">
      <p className="eyebrow">Paso 5 · Decisión humana</p><h2>Revisión supervisada</h2><p><strong>Necesidad:</strong> {proposal.business_goal}</p><p><strong>Dominio:</strong> {selectedDomain.label}</p><p><strong>Fuente:</strong> {source.connection?.name} · instantánea #{proposal.metadata_snapshot_id}</p><p><strong>Validación:</strong> {proposal.validation_document.valid ? 'Aprobada por reglas estructurales' : 'Con errores'}</p>
      {proposal.status === 'ready_for_review' && canReview ? <><label>Comentario de revisión<textarea rows={3} maxLength={500} value={reviewComment} onChange={(event) => setReviewComment(event.target.value)} placeholder="Obligatorio para rechazar; opcional para aprobar." /></label>{proposal.validation_document.warnings > 0 && <label className="confirmation"><input type="checkbox" checked={warningsConfirmed} onChange={(event) => setWarningsConfirmed(event.target.checked)} />Leí y comprendí las advertencias y las acciones indicadas.</label>}<p className="notice">Aprobar vuelve a ejecutar las reglas vigentes, registra la decisión y habilita la propuesta en Generación de datamart. No crea tablas ni ejecuta ETL.</p><div className="form-actions"><button disabled={proposal.validation_document.warnings > 0 && !warningsConfirmed} onClick={() => void decide('approve')}>Aprobar propuesta</button><button className="danger" disabled={reviewComment.trim().length < 10} onClick={() => void decide('reject')}>Rechazar propuesta</button>{canGenerate && <button className="secondary" onClick={() => openPersonalization()}>Personalizar antes de decidir</button>}<button className="secondary" onClick={() => setStep(3)}>Volver</button></div></> : <><div className={`decision-receipt ${proposal.status}`}><h3>{proposalStatusLabels[proposal.status]}</h3><p>{proposal.reviewed_by_label} · {proposal.reviewed_at ? new Date(proposal.reviewed_at).toLocaleString('es-EC') : ''}</p>{proposal.review_comment && <p>{proposal.review_comment}</p>}</div>{canGenerate && proposal.proposal_document.ai_decisions && proposal.status !== 'discarded' && <button className="secondary" onClick={() => openPersonalization()}>Crear versión corregida desde ésta</button>}{proposal.status === 'invalidated' && canReview && <section className="restore-panel"><h3>Restaurar aprobación</h3><p>La aplicación volverá a comprobar errores bloqueantes. Una diferencia causada únicamente por la versión del motor quedará registrada como advertencia de compatibilidad.</p><label>Justificación<textarea rows={2} minLength={10} maxLength={500} value={restoreReason} onChange={(event) => setRestoreReason(event.target.value)} placeholder="Explique por qué corresponde restaurar esta aprobación." /></label>{proposal.validation_document.warnings > 0 && <label className="confirmation"><input type="checkbox" checked={restoreWarningsConfirmed} onChange={(event) => setRestoreWarningsConfirmed(event.target.checked)} />Revisé las advertencias vigentes de esta versión.</label>}<button disabled={restoreReason.trim().length < 10 || (proposal.validation_document.warnings > 0 && !restoreWarningsConfirmed)} onClick={() => void restoreApproval()}>Restaurar aprobación</button></section>}{proposal.status !== 'discarded' && ((proposal.status === 'approved' && canReview) || (proposal.status !== 'approved' && canGenerate)) && <section className="cleanup-panel"><h3>Depurar esta versión</h3><p>{proposal.status === 'approved' ? 'Retire la aprobación para impedir que esta versión se use en nuevas ejecuciones ETL.' : 'Descártela de las listas operativas. La auditoría y la trazabilidad no se eliminan.'}</p><label>Motivo<textarea rows={2} minLength={10} maxLength={500} value={cleanupReason} onChange={(event) => setCleanupReason(event.target.value)} placeholder="Explique la inconsistencia o el motivo del descarte." /></label><button className="danger" disabled={cleanupReason.trim().length < 10} onClick={() => void cleanVersion(proposal.status === 'approved' ? 'invalidate' : 'discard')}>{proposal.status === 'approved' ? 'Retirar aprobación' : 'Descartar versión'}</button></section>}</>}
    </section>}
    {proposal && Object.keys(proposal.proposal_document).length > 0 && <section className="validation-evidence" aria-label="Validación del resultado">
      <div className="proposal-heading"><div><p className="eyebrow">Evidencia de validación técnica</p><h2>Validación estructural de la propuesta</h2></div><button className="secondary" disabled={verifying} onClick={() => void verifyEvidence()}>{verifying ? 'Verificando…' : 'Verificar evidencia'}</button></div>
      <p>Comprueba metadatos, referencias, contrato y reproducción determinística de la versión seleccionada. No vuelve a llamar al LLM, no consulta filas y no ejecuta el ETL.</p>
      <p className="notice">Esta etapa comprueba la estructura, no la igualdad de filas, unidades o importes. La conciliación OLTP–datamart se añadirá automáticamente al expediente después de materializar y ejecutar el ETL.</p>
      {verification && <><div className="evidence-grid">{verification.checks.map((check) => { const compatibilityOnly = verification.compatibility_warning && ['validation.consistency', 'proposal.replay'].includes(check.code); return <article className={check.passed ? 'passed' : compatibilityOnly ? 'warning' : 'failed'} key={check.code}><span>{check.passed ? 'Cumple' : compatibilityOnly ? 'Compatibilidad' : 'Revisar'}</span><h3>{check.label}</h3><p>{check.detail}</p></article> })}</div>{verification.compatibility_warning && <p className="notice warning">La propuesta pertenece a una versión anterior del motor. Esta diferencia se conserva para trazabilidad, pero no invalida una propuesta sin errores bloqueantes.</p>}<details className="technical-details"><summary>Validaciones que se habilitarán posteriormente</summary><p>Estas comprobaciones aparecerán cuando exista el incremento correspondiente:</p><ul>{verification.pending_validations.map((item) => <li key={item}>{item}</li>)}</ul></details><p className="field-help">Huella de propuesta: {verification.proposal_hash.slice(0, 12)} · Huella de reejecución: {verification.replay_hash.slice(0, 12) || 'no disponible'}</p></>}
    </section>}
    <section className="attempt-history"><div className="history-heading"><div><h2>Versiones generadas</h2><p className="field-help">Abra un resultado conservado para revisarlo o aprobarlo sin volver a ejecutar el modelo.</p></div><label>Mostrar<select value={historyFilter} onChange={(event) => { setHistoryFilter(event.target.value); setHistoryOffset(0) }}>{historyFilterOptions.map((item) => <option value={item.value} key={item.value}>{item.label}</option>)}</select></label></div>{historyPage.items.length > 0 ? <><div className="table-wrap"><table><thead><tr><th>Versión</th><th>Necesidad</th><th>Proveedor y modelo</th><th>Estado</th><th>Fecha</th><th>Resultado</th></tr></thead><tbody>{historyPage.items.map((item) => <tr className={proposal?.id === item.id ? 'selected-attempt' : ''} key={item.id}><td>#{item.id}{item.source_proposal_id && <small>Derivada de #{item.source_proposal_id}</small>}</td><td>{item.business_goal}</td><td>{providerLabel(item.provider_kind)} / {item.model_id}</td><td>{proposalStatusLabels[item.status]}</td><td>{new Date(item.created_at).toLocaleString('es-EC')}</td><td><button className="secondary compact" disabled={proposal?.id === item.id} onClick={() => selectSavedProposal(item)}>{proposal?.id === item.id ? 'Seleccionada' : 'Abrir resultado'}</button></td></tr>)}</tbody></table></div><Pagination page={historyPage} onChange={setHistoryOffset} /></> : <p className="notice">No hay versiones en este estado para el dominio seleccionado.</p>}</section>
  </>
}

const etlStepLabels = ['Elegir propuesta', 'Revisar indicadores', 'Confirmar ejecución', 'Materializar y cargar', 'Validar resultados']
const executionStatusLabels: Record<EtlExecution['status'], string> = {
  prepared: 'Preparada', running: 'En ejecución', succeeded: 'Validada', validation_warning: 'Revisión pendiente', failed: 'Fallida',
}
const etlStageLabels: Record<EtlTransformation['stage'], string> = {
  extract: 'Extracción controlada',
  clean: 'Limpieza y calidad',
  transform: 'Transformación y enriquecimiento',
  load: 'Carga dimensional',
  validate: 'Conciliación y evidencia',
}
const recipeOperationLabels: Record<string, string> = {
  sum: 'Suma', count: 'Conteo', count_distinct: 'Conteo distinto', average: 'Promedio', min: 'Mínimo', max: 'Máximo',
}
const periodicityLabels: Record<string, string> = {
  day: 'Diaria', week: 'Semanal', month: 'Mensual', quarter: 'Trimestral', year: 'Anual',
}

function kpiRecipeExplanation(kpi: EtlKpiRecipe) {
  if (kpi.kind === 'aggregate') {
    const operation = stringValue(kpi.recipe.operation, 'agregación')
    return `${recipeOperationLabels[operation] ?? operation} de ${stringValue(kpi.recipe.measure, kpi.inputs[0] ?? 'la medida validada')}.`
  }
  const numerator = stringValue(kpi.recipe.numerator, kpi.inputs[0] ?? 'numerador')
  const denominator = stringValue(kpi.recipe.denominator, kpi.inputs[1] ?? 'denominador')
  return kpi.kind === 'share'
    ? `${numerator} dividido para ${denominator}, expresado como porcentaje.`
    : `${numerator} dividido para ${denominator}; si el divisor es cero se informa sin valor.`
}

function businessTechnicalLabel(value: string) {
  const normalized = value.replace(/^dim_|^fact_/, '').replaceAll('_', ' ').trim()
  const words: Record<string, string> = {
    sales: 'ventas', amount: 'importe', quantity: 'cantidad', customer: 'cliente', customers: 'clientes',
    product: 'producto', products: 'productos', territory: 'territorio', date: 'fecha', order: 'pedido', orders: 'pedidos',
  }
  return normalized.split(' ').map((word) => words[word.toLowerCase()] ?? word).join(' ').replace(/^./, (letter) => letter.toUpperCase())
}

function formatInteger(value: unknown) {
  const number = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(number) ? new Intl.NumberFormat('es-EC', { maximumFractionDigits: 0 }).format(number) : '—'
}

function formatKpiValue(value: unknown, unit: string) {
  const number = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(number)) return '—'
  if (/^[A-Z]{3}$/.test(unit)) {
    return new Intl.NumberFormat('es-EC', {
      style: 'currency', currency: unit, currencyDisplay: 'code', minimumFractionDigits: 2, maximumFractionDigits: 2,
    }).format(number)
  }
  const isCount = /(unidad|pedido|cliente|registro|fila)/i.test(unit)
  const isMoney = /moneda/i.test(unit)
  return new Intl.NumberFormat('es-EC', {
    minimumFractionDigits: isMoney ? 2 : 0,
    maximumFractionDigits: isCount ? 0 : 2,
  }).format(number)
}

function formatKpiDisplay(value: unknown, unit: string) {
  const formatted = formatKpiValue(value, unit)
  return /^[A-Z]{3}$/.test(unit) || formatted === '—' ? formatted : `${formatted} ${unit}`
}

function SalesDatamartPage({ token, canWrite, navigate }: { token: string; canWrite: boolean; navigate: (path: string) => void }) {
  const [catalog, setCatalog] = useState<{ items: EtlProposalCandidate[]; blocked_items: EtlProposalCandidate[]; recommended_proposal_id?: number; guidance: string[] } | null>(null)
  const [executions, setExecutions] = useState<Page<EtlExecution>>({ items: [], total: 0, limit: 5, offset: 0 })
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [compareIds, setCompareIds] = useState<number[]>([])
  const [selectedKpis, setSelectedKpis] = useState<string[]>([])
  const [step, setStep] = useState(1)
  const [comment, setComment] = useState('Revisé la necesidad, la granularidad, las transformaciones y los indicadores seleccionados.')
  const [confirmed, setConfirmed] = useState(false)
  const [preparing, setPreparing] = useState(false)
  const [running, setRunning] = useState(false)
  const [execution, setExecution] = useState<EtlExecution | null>(null)
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'warning' | 'error'; message: string } | null>(null)

  const loadWorkspace = useCallback(async () => {
    try {
      const [available, history] = await Promise.all([api.etlProposals(token), api.etlExecutions(token, 5, 0)])
      setCatalog(available)
      setExecutions(history)
      const proposedId = available.recommended_proposal_id ?? available.items[0]?.proposal_id ?? null
      setSelectedId((current) => current && available.items.some((item) => item.proposal_id === current) ? current : proposedId)
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible preparar el espacio de trabajo.' })
    }
  }, [token])

  useEffect(() => { void loadWorkspace() }, [loadWorkspace])

  const selected = catalog
    ? [...catalog.items, ...catalog.blocked_items].find((item) => item.proposal_id === selectedId) ?? null
    : null
  const historicalReadOnly = Boolean(selected && !selected.eligible)
  const latestExecutionMatchesSelection = Boolean(
    selected?.latest_execution_id
    && [...(selected.latest_execution_kpi_codes ?? [])].sort().join('|') === [...selectedKpis].sort().join('|'),
  )

  useEffect(() => {
    if (!selected) return
    setSelectedKpis(selected.kpi_recipes.map((item) => item.code))
    setConfirmed(false)
  }, [selected])

  function chooseProposal(id: number) {
    setSelectedId(id)
    setExecution(null)
    setConfirmed(false)
    setStep(1)
    setFeedback(null)
  }

  function openExecution(item: EtlExecution) {
    const proposal = catalog
      ? [...catalog.items, ...catalog.blocked_items].find((candidate) => candidate.proposal_id === item.proposal_id)
      : undefined
    if (!proposal) {
      setFeedback({
        kind: 'error',
        message: `No se encontró el contrato de la ejecución #${item.id}. El expediente permanece registrado para auditoría, pero no puede reconstruirse en esta vista.`,
      })
      return
    }
    setSelectedId(item.proposal_id)
    setSelectedKpis(proposal.kpi_recipes.map((kpi) => kpi.code))
    setExecution(item)
    setStep(item.status === 'prepared' && proposal.eligible ? 4 : 5)
    setFeedback({
      kind: !proposal.eligible || item.status === 'validation_warning' ? 'warning' : 'success',
      message: !proposal.eligible
        ? `Ejecución #${item.id} abierta en modo histórico de sólo lectura. Su contrato no puede volver a ejecutarse con las reglas actuales.`
        : `Ejecución #${item.id} abierta. Continúe desde el estado conservado en su expediente.`,
    })
  }

  async function openLatestExecution() {
    if (!selected?.latest_execution_id) return
    const cached = executions.items.find((item) => item.id === selected.latest_execution_id)
    if (cached) {
      openExecution(cached)
      return
    }
    try {
      openExecution(await api.etlExecution(token, selected.latest_execution_id))
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible abrir el expediente existente.' })
    }
  }

  function toggleCompare(id: number) {
    setCompareIds((current) => current.includes(id) ? current.filter((item) => item !== id) : current.length < 2 ? [...current, id] : [current[1], id])
  }

  function toggleKpi(code: string) {
    setSelectedKpis((current) => current.includes(code) ? current.filter((item) => item !== code) : [...current, code])
  }

  async function prepareExecution() {
    if (!selected) return
    setPreparing(true); setFeedback(null)
    try {
      const created = await api.prepareEtlExecution(token, {
        proposal_id: selected.proposal_id,
        selected_kpi_codes: selectedKpis,
        confirmation: confirmed,
        analyst_comment: comment,
      })
      setExecution(created)
      setStep(4)
      setFeedback({ kind: 'success', message: `La ejecución #${created.id} quedó preparada y trazable. No se ha consultado ni alterado la fuente durante esta confirmación.` })
      setExecutions((current) => ({ ...current, items: [created, ...current.items].slice(0, current.limit), total: current.total + 1 }))
      await loadWorkspace()
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible preparar la ejecución.' })
    } finally { setPreparing(false) }
  }

  async function runExecution() {
    if (!execution) return
    setRunning(true); setFeedback({ kind: 'warning', message: 'Materializando el datamart. Mantenga esta pantalla abierta; la fuente permanece en sólo lectura.' })
    try {
      const result = await api.runEtlExecution(token, execution.id)
      setExecution(result)
      setStep(5)
      setFeedback({
        kind: result.status === 'succeeded' ? 'success' : result.status === 'validation_warning' ? 'warning' : 'error',
        message: stringValue(result.validation_document.message, 'La ejecución terminó. Revise el expediente.'),
      })
      setExecutions((current) => ({ ...current, items: current.items.map((item) => item.id === result.id ? result : item) }))
      await loadWorkspace()
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible ejecutar el ETL.' })
    } finally { setRunning(false) }
  }

  async function retrySpanishInterpretation() {
    if (!execution) return
    setRunning(true); setFeedback({ kind: 'warning', message: 'Interpretando categorías seguras. El ETL y los valores originales no se modificarán.' })
    try {
      const result = await api.retryEtlSpanishInterpretation(token, execution.id)
      setExecution(result)
      setFeedback({ kind: 'success', message: stringValue(result.validation_document.message, 'La interpretación española quedó actualizada.') })
      setExecutions((current) => ({ ...current, items: current.items.map((item) => item.id === result.id ? result : item) }))
      await loadWorkspace()
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible completar la interpretación española.' })
    } finally { setRunning(false) }
  }

  async function verifyCurrency() {
    if (!execution) return
    setRunning(true); setFeedback({ kind: 'warning', message: 'Comprobando la divisa directamente en la fuente, sin repetir el ETL ni modificar sus datos.' })
    try {
      const result = await api.verifyEtlCurrency(token, execution.id)
      const context = objectValue(result.metrics_document.currency_context)
      setExecution(result)
      setFeedback({
        kind: context.status === 'verified' ? 'success' : 'warning',
        message: stringValue(context.message, 'La comprobación monetaria quedó registrada en el expediente.'),
      })
      setExecutions((current) => ({ ...current, items: current.items.map((item) => item.id === result.id ? result : item) }))
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible comprobar la divisa.' })
    } finally { setRunning(false) }
  }

  async function applySpanishInterpretation(groups: Array<{ dimension: string; target_column: string; mappings: Array<{ original: string; label_es: string }> }>, analystComment: string) {
    if (!execution) return
    setRunning(true); setFeedback({ kind: 'warning', message: 'Publicando únicamente las etiquetas revisadas; los valores originales permanecen intactos.' })
    try {
      const result = await api.applyEtlSpanishInterpretation(token, execution.id, { confirmation: true, analyst_comment: analystComment, groups })
      setExecution(result)
      setFeedback({ kind: 'success', message: stringValue(result.validation_document.message, 'La interpretación revisada quedó publicada.') })
      setExecutions((current) => ({ ...current, items: current.items.map((item) => item.id === result.id ? result : item) }))
      await loadWorkspace()
    } catch (caught) {
      setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible publicar las etiquetas revisadas.' })
    } finally { setRunning(false) }
  }

  const historyPanel = <section className="etl-history"><div className="etl-section-heading"><div><h2>Expedientes recientes</h2><p>Abra una ejecución para consultar su materialización, conciliación y decisiones sin repetir el ETL.</p></div><span>{executions.total} registros</span></div>{executions.items.length === 0 ? <p className="notice">Todavía no se ha preparado ninguna ejecución.</p> : <div className="table-wrap"><table><thead><tr><th>Ejecución</th><th>Propuesta</th><th>Estado</th><th>Responsable</th><th>Fecha</th><th>Acción</th></tr></thead><tbody>{executions.items.map((item) => <tr key={item.id}><td>#{item.id}</td><td>Versión #{item.proposal_id}</td><td><span className={`execution-status ${item.status}`}>{executionStatusLabels[item.status]}</span></td><td>{item.created_by_label}</td><td>{new Date(item.created_at).toLocaleString('es-EC')}</td><td><button type="button" className="secondary compact" onClick={() => openExecution(item)}>Abrir expediente #{item.id}</button></td></tr>)}</tbody></table></div>}</section>

  if (!catalog) return <><p className="lead">Convierta una propuesta aprobada en un datamart trazable mediante un recorrido guiado.</p>{feedback && <p className={`notice ${feedback.kind}`}>{feedback.message}</p>}<p className="notice">Comprobando propuestas, fuente y reglas vigentes…</p></>
  if (catalog.items.length === 0 && !execution) return <div className="etl-workspace"><section className="etl-empty-state"><div className="etl-empty-icon" aria-hidden="true">!</div><p className="eyebrow">Preparación requerida</p><h2>No hay propuestas habilitadas para una ejecución nueva</h2><p>Las versiones siguientes se conservaron para auditoría y no pueden materializarse de nuevo. Puede corregir la propuesta o abrir abajo un expediente ya ejecutado sin repetir el ETL.</p>{catalog.blocked_items.map((item) => <article className="blocked-proposal" key={item.proposal_id}><h3>Versión #{item.proposal_id}: {item.summary}</h3><ul>{item.blocking_reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></article>)}<div className="form-actions"><button onClick={() => navigate('/asistente')}>Corregir o generar una propuesta</button><button className="secondary" onClick={() => void loadWorkspace()}>Volver a comprobar</button></div>{feedback && <p className={`notice ${feedback.kind}`}>{feedback.message}</p>}</section>{historyPanel}</div>

  const compared = compareIds.map((id) => catalog.items.find((item) => item.proposal_id === id)).filter((item): item is EtlProposalCandidate => Boolean(item))
  const groupedTransformations = selected ? Object.entries(etlStageLabels).map(([stage, label]) => ({
    stage: stage as EtlTransformation['stage'], label, items: selected.transformation_plan.filter((item) => item.stage === stage),
  })).filter((group) => group.items.length > 0) : []

  return <div className="etl-workspace">
    <section className="etl-hero">
      <div><p className="eyebrow">Espacio de trabajo del analista BI</p><h2>Materialización controlada del datamart</h2><p>Revise el contrato aprobado, los indicadores sugeridos por la IA y cada transformación antes de crear datos analíticos.</p></div>
      <dl><div><dt>Dominio</dt><dd>Ventas</dd></div><div><dt>Fuente</dt><dd>SQL Server · sólo lectura</dd></div><div><dt>Modo</dt><dd>Supervisado y auditable</dd></div></dl>
    </section>
    <ol className="etl-stepper" aria-label={`Paso ${step} de 5`}>{etlStepLabels.map((label, index) => <li className={index + 1 === step ? 'current' : index + 1 < step ? 'complete' : ''} key={label}><span>{index + 1}</span><div><small>Paso {index + 1}</small><strong>{label}</strong></div></li>)}</ol>
    {feedback && <p className={`notice ${feedback.kind}`} role={feedback.kind === 'error' ? 'alert' : 'status'}>{feedback.message}</p>}

    {step === 1 && <section className="etl-stage-panel">
      <div className="etl-section-heading"><div><p className="eyebrow">Decisión 1 de 3</p><h2>Elija la propuesta que desea materializar</h2><p>Se muestran únicamente versiones aprobadas que todavía superan las reglas, conservan su instantánea y poseen KPI calculables.</p></div><span className="etl-help-badge">Sugerencia automática, decisión humana</span></div>
      <div className="analyst-guidance"><strong>Qué debe revisar</strong><p>Confirme que la necesidad, la granularidad y las medidas correspondan al resultado que espera el negocio. La versión más reciente compatible aparece recomendada, pero no se ejecuta sola.</p></div>
      <div className="etl-proposal-grid">{catalog.items.map((item) => <article className={`etl-proposal-card ${selectedId === item.proposal_id ? 'selected' : ''}`} key={item.proposal_id}>
        <div className="etl-card-top"><span>Versión #{item.proposal_id}</span>{item.latest_execution_id ? <strong>Ya ejecutada · expediente #{item.latest_execution_id}</strong> : item.recommended && <strong>Recomendada</strong>}</div><h3>{item.summary}</h3><p>{item.business_goal}</p>
        <dl><div><dt>Granularidad</dt><dd>{item.grain}</dd></div><div><dt>Indicadores</dt><dd>{item.kpi_count} sugeridos por IA</dd></div><div><dt>Aprobación</dt><dd>{item.reviewed_at ? new Date(item.reviewed_at).toLocaleString('es-EC') : 'Fecha no disponible'}</dd></div>{item.latest_execution_status && <div><dt>Última ejecución</dt><dd>{executionStatusLabels[item.latest_execution_status]}{item.latest_execution_at ? ` · ${new Date(item.latest_execution_at).toLocaleString('es-EC')}` : ''}</dd></div>}</dl>
        <div className="etl-card-actions"><button className={selectedId === item.proposal_id ? 'secondary' : ''} disabled={selectedId === item.proposal_id} onClick={() => chooseProposal(item.proposal_id)}>{selectedId === item.proposal_id ? 'Seleccionada' : 'Seleccionar'}</button><label><input type="checkbox" checked={compareIds.includes(item.proposal_id)} onChange={() => toggleCompare(item.proposal_id)} />Comparar</label></div>
      </article>)}</div>
      {compared.length > 0 && <section className="etl-comparison"><div className="etl-section-heading"><div><h3>Comparación de propuestas</h3><p>Puede contrastar hasta dos versiones antes de decidir.</p></div><button className="secondary compact" onClick={() => setCompareIds([])}>Cerrar comparación</button></div><div className="etl-comparison-grid">{compared.map((item) => <article key={item.proposal_id}><strong>Versión #{item.proposal_id}</strong><h3>{item.summary}</h3><p><b>Grano:</b> {item.grain}</p><p><b>Medidas:</b> {item.measures.map(businessTechnicalLabel).join(', ')}</p><p><b>KPI:</b> {item.kpi_recipes.map((kpi) => kpi.name).join(', ')}</p></article>)}</div></section>}
      {catalog.blocked_items.length > 0 && <details className="blocked-versions"><summary>{catalog.blocked_items.length} versiones aprobadas fueron bloqueadas por controles actuales</summary>{catalog.blocked_items.map((item) => <article key={item.proposal_id}><h3>Versión #{item.proposal_id}</h3><ul>{item.blocking_reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul></article>)}</details>}
      {latestExecutionMatchesSelection && selected?.latest_execution_id && <p className="notice success"><strong>Este contrato ya fue ejecutado.</strong> La ejecución #{selected.latest_execution_id} conserva la materialización y sus validaciones. No se habilita otra ejecución idéntica.</p>}
      <div className="etl-footer-actions"><span>{selected ? latestExecutionMatchesSelection && selected.latest_execution_id ? `Versión #${selected.proposal_id} ya materializada en la ejecución #${selected.latest_execution_id}` : `Versión #${selected.proposal_id} seleccionada` : 'Seleccione una propuesta'}</span>{latestExecutionMatchesSelection && selected?.latest_execution_id ? <button onClick={() => void openLatestExecution()}>Abrir expediente #{selected.latest_execution_id}</button> : <button disabled={!selected} onClick={() => setStep(2)}>Revisar indicadores</button>}</div>
    </section>}

    {step === 2 && selected && <section className="etl-stage-panel">
      <div className="etl-section-heading"><div><p className="eyebrow">Decisión 2 de 3</p><h2>Revise los indicadores sugeridos por la IA</h2><p>La cantidad es variable. Cada indicador debe tener una receta permitida y fuentes comprobadas; la IA sugiere, pero el motor controla el cálculo.</p></div><span className="etl-count-badge">{selectedKpis.length} de {selected.kpi_recipes.length} seleccionados</span></div>
      <div className="analyst-guidance"><strong>Cómo decidir</strong><p>Conserve sólo los indicadores que responden a la necesidad. Si un indicador no aporta a la decisión, retírelo aquí; no cambie su fórmula ni escriba SQL.</p></div>
      <div className="etl-kpi-grid">{selected.kpi_recipes.map((kpi) => { const included = selectedKpis.includes(kpi.code); const periodicity = kpi.periodicity === 'inherit' ? selected.periodicity : kpi.periodicity; return <article className={included ? 'selected' : ''} key={kpi.code}><div className="etl-kpi-heading"><label><input type="checkbox" checked={included} onChange={() => toggleKpi(kpi.code)} /><span>Incluir indicador</span></label><span>{kpi.kind === 'aggregate' ? 'Agregación' : kpi.kind === 'ratio' ? 'Razón' : 'Participación'}</span></div><h3>{kpi.name}</h3><p>{kpi.description || 'Indicador propuesto para responder a la necesidad aprobada.'}</p><div className="etl-formula"><small>Cálculo controlado</small><strong>{kpiRecipeExplanation(kpi)}</strong></div><dl><div><dt>Unidad</dt><dd>{kpi.unit}</dd></div><div><dt>Período</dt><dd>{periodicityLabels[periodicity] ?? periodicity}</dd></div></dl>{(kpi.adjustments?.length ?? 0) > 0 && <div className="kpi-adjustment"><strong>Ajuste de seguridad</strong>{kpi.adjustments?.map((adjustment) => <p key={adjustment}>{adjustment}</p>)}</div>}<details><summary>Ver trazabilidad técnica</summary><p>Entradas verificadas: {kpi.inputs.join(', ')}.</p><p>Definición: {kpi.definition_version}.</p>{kpi.declared_unit && kpi.declared_unit !== kpi.unit && <p>Unidad sugerida originalmente: {kpi.declared_unit}.</p>}</details></article> })}</div>
      {selectedKpis.length === 0 && <p className="notice error">Seleccione al menos un indicador. Un datamart sin resultado analítico verificable no puede prepararse.</p>}
      <div className="etl-footer-actions"><button className="secondary" onClick={() => setStep(1)}>Volver a propuestas</button><button disabled={selectedKpis.length === 0} onClick={() => setStep(3)}>Revisar transformaciones</button></div>
    </section>}

    {step === 3 && selected && <section className="etl-stage-panel">
      <div className="etl-section-heading"><div><p className="eyebrow">Decisión 3 de 3</p><h2>Confirme el plan de preparación de datos</h2><p>Esta vista explica limpieza, columnas derivadas, carga y controles sin exponer SQL. Nada se ejecuta hasta su confirmación.</p></div><span className="etl-help-badge">{selected.transformation_plan.length} operaciones controladas</span></div>
      <section className="etl-model-summary"><article><small>Tabla de hechos</small><strong>{businessTechnicalLabel(selected.fact_name)}</strong><span>Referencia técnica: {selected.fact_name}</span></article><article><small>Granularidad</small><strong>{selected.grain}</strong></article><article><small>Dimensiones</small><strong>{selected.dimensions.map(businessTechnicalLabel).join(', ')}</strong><span>{selected.dimensions.length} estructuras conformadas</span></article><article><small>Medidas</small><strong>{selected.measures.map(businessTechnicalLabel).join(', ')}</strong><span>{selected.measures.length} valores calculables</span></article></section>
      <div className="semantic-safety"><div aria-hidden="true">ES</div><section><h3>Interpretación dinámica en español</h3><p>Los nombres técnicos en inglés se explicarán en español. Los valores categóricos aptos podrán recibir una etiqueta española sin reemplazar el valor original.</p><ul><li>Si el contenido ya está en español, se conserva sin reinterpretarlo.</li><li>No se traducen identificadores, nombres de personas, direcciones, texto libre, credenciales ni categorías de alta cardinalidad.</li><li>Todo mapeo conserva original, etiqueta, idioma detectado, versión y aprobación del analista.</li></ul></section></div>
      <div className="analyst-guidance"><strong>No requiere acción en esta pantalla</strong><p>Las operaciones marcadas como “Revisar en el paso 5” sólo buscan y preparan posibles etiquetas en español. Después de pulsar “Materializar y cargar datamart” y terminar la conciliación, esta misma pantalla avanzará a “Paso 5 · Validar resultados”. Allí, en “Interpretación semántica”, podrá publicar, corregir o excluir cada mapeo encontrado. Si no se encuentra ninguno, no habrá nada que revisar.</p></div>
      <div className="etl-pipeline">{groupedTransformations.map((group, groupIndex) => <section key={group.stage}><div className="etl-pipeline-heading"><span>{groupIndex + 1}</span><div><small>Etapa</small><h3>{group.label}</h3></div></div><div>{group.items.map((item) => <article key={item.code}><div><strong>{item.label}</strong>{item.severity === 'optional' && <span>Revisar en el paso 5</span>}</div><p>{item.detail}</p></article>)}</div></section>)}</div>
      {selected.warnings.length > 0 && <div className="notice warning"><strong>Advertencias heredadas</strong><ul>{selected.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></div>}
      <div className="etl-confirmation-box"><label>Registro de decisión<textarea rows={3} minLength={10} maxLength={500} value={comment} onChange={(event) => setComment(event.target.value)} /></label><label className="confirmation"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />Confirmo el plan de ejecución y comprendo que las etiquetas candidatas se revisarán individualmente después de la carga.</label><p>Esta confirmación crea un expediente inmutable de preparación, pero no publica ninguna etiqueta. La materialización física sólo podrá usar este contrato validado.</p></div>
      <div className="etl-footer-actions"><button className="secondary" onClick={() => setStep(2)}>Volver a indicadores</button><button disabled={!canWrite || !confirmed || comment.trim().length < 10 || preparing} onClick={() => void prepareExecution()}>{preparing ? 'Registrando preparación…' : 'Preparar materialización'}</button></div>
      {!canWrite && <p className="notice warning">Puede revisar el plan, pero su rol no posee permiso para preparar una ejecución.</p>}
    </section>}

    {step >= 4 && selected && execution && <section className="etl-stage-panel">
      <div className={`etl-execution-receipt ${step === 5 ? execution.status : ''}`}><span aria-hidden="true">{execution.status === 'failed' ? '!' : '✓'}</span><div><p className="eyebrow">Ejecución #{execution.id}</p><h2>{historicalReadOnly ? 'Expediente histórico conservado' : step === 4 ? 'Contrato preparado correctamente' : execution.status === 'succeeded' ? 'Datamart materializado y conciliado' : execution.status === 'validation_warning' && objectValue(execution.metrics_document.reconciliation).passed === true ? 'Datamart conciliado; interpretación pendiente' : execution.status === 'validation_warning' ? 'Carga completada con diferencias' : 'La materialización fue revertida'}</h2><p>{historicalReadOnly ? 'Puede consultar la evidencia obtenida en su momento. Las reglas actuales impiden reutilizar este contrato para una ejecución nueva.' : step === 4 ? 'La selección quedó persistida con las huellas de la propuesta y la instantánea. Revise el comprobante antes de iniciar la lectura.' : stringValue(execution.validation_document.message, 'Revise el expediente de la ejecución.')}</p></div><strong>{historicalReadOnly ? 'Sólo lectura' : step === 4 ? 'Preparada' : execution.status === 'succeeded' ? 'Validada' : execution.status === 'validation_warning' && objectValue(execution.metrics_document.reconciliation).passed === true ? 'Interpretar' : execution.status === 'validation_warning' ? 'Revisar' : 'Fallida'}</strong></div>
      {historicalReadOnly && <div className="analyst-guidance"><strong>No tiene que repetir el ETL</strong><p>Este expediente conserva la propuesta, las huellas y los resultados originales. Para materializar un contrato corregido, genere y apruebe una versión nueva desde el asistente.</p></div>}
      {!historicalReadOnly && <div className="etl-progress-list"><article className="complete"><span>1</span><div><strong>Contrato y fuente revalidados</strong><p>La propuesta continúa aprobada, la fuente está activa y las referencias son compatibles.</p></div></article><article className="complete"><span>2</span><div><strong>Plan determinístico fijado</strong><p>{selectedKpis.length} indicadores y {selected.transformation_plan.length} operaciones quedaron versionados.</p></div></article><article className={step === 5 && execution.status !== 'failed' ? 'complete' : ''}><span>3</span><div><strong>{running ? 'Materializando y cargando…' : 'Materialización física'}</strong><p>{step === 4 ? 'Creará las dimensiones y el hecho en una transacción; un fallo no dejará tablas parciales.' : execution.status === 'failed' ? 'La transacción se revirtió y las tablas publicadas anteriormente no fueron sustituidas.' : 'Extracción, limpieza, claves sustitutas y carga transaccional completadas.'}</p></div></article><article className={step === 5 && objectValue(execution.metrics_document.reconciliation).passed === true ? 'complete' : ''}><span>4</span><div><strong>Conciliación cuantitativa</strong><p>{step === 4 ? 'Contrastará filas, unidades, importes e indicadores con el origen.' : 'El expediente conserva conteos, diferencias, medidas e indicadores calculados.'}</p></div></article></div>}
      {step === 4 && <div className="analyst-guidance"><strong>Antes de iniciar</strong><p>La operación leerá sólo las columnas aprobadas de SQL Server y reemplazará transaccionalmente el esquema analítico de ventas. Si un control bloqueante falla, el datamart publicado no cambia.</p></div>}
      {step === 5 && execution.status !== 'prepared' && <EtlValidationResult execution={execution} canRetry={canWrite && !running && !historicalReadOnly} onVerifyCurrency={() => void verifyCurrency()} onRetry={() => void retrySpanishInterpretation()} onApply={(groups, analystComment) => void applySpanishInterpretation(groups, analystComment)} />}
      {step === 5 && execution.status === 'prepared' && historicalReadOnly && <p className="notice warning">Esta preparación histórica no llegó a materializarse. Se conserva para auditoría y no puede iniciarse con un contrato actualmente bloqueado.</p>}
      <details className="technical-details"><summary>Ver trazabilidad técnica</summary><p>Constructor: {execution.builder_version}</p><p>Huella de propuesta: {execution.proposal_hash.slice(0, 12)} · Huella de instantánea: {execution.snapshot_hash.slice(0, 12)}</p><p>Registrada por: {execution.created_by_label} · {new Date(execution.created_at).toLocaleString('es-EC')}</p></details>
      <div className="etl-footer-actions"><button className="secondary" disabled={running} onClick={() => { setStep(1); setExecution(null); setConfirmed(false); setSelectedId(catalog.recommended_proposal_id ?? catalog.items[0]?.proposal_id ?? null) }}>{catalog.items.length > 0 ? 'Volver a propuestas' : 'Volver al estado del datamart'}</button>{step === 4 && !historicalReadOnly && <button disabled={running} onClick={() => void runExecution()}>{running ? 'Materializando…' : 'Materializar y cargar datamart'}</button>}</div>
    </section>}

    {historyPanel}
  </div>
}

type SpanishDecisionGroup = { dimension: string; target_column: string; mappings: Array<{ original: string; label_es: string }> }

function EtlValidationResult({ execution, canRetry, onVerifyCurrency, onRetry, onApply }: { execution: EtlExecution; canRetry: boolean; onVerifyCurrency: () => void; onRetry: () => void; onApply: (groups: SpanishDecisionGroup[], analystComment: string) => void }) {
  const reconciliation = objectValue(execution.metrics_document.reconciliation)
  const tables = arrayValue(execution.metrics_document.tables)
  const kpis = arrayValue(execution.metrics_document.kpis)
  if (execution.status === 'failed') return <div className="notice error"><strong>No se publicaron cambios parciales.</strong><p>Revise la conexión, regenere la propuesta si cambió la instantánea y prepare una nueva ejecución. El código técnico queda disponible sólo en los registros del servidor.</p></div>
  const semantic = objectValue(execution.metrics_document.semantic_interpretation)
  const currency = objectValue(execution.metrics_document.currency_context)
  const requiresCurrencyCheck = currency.status !== 'verified' && kpis.some((kpi) => /^(moneda|moneda de origen|currency)$/i.test(stringValue(kpi.unit, '')))
  return <section className="etl-validation-result"><div className="etl-section-heading"><div><p className="eyebrow">Evidencia cuantitativa</p><h2>Conciliación OLTP–datamart</h2><p>Origen y destino se consultaron de forma independiente durante la misma ejecución y quedaron asociados a este expediente.</p></div><span className={reconciliation.passed === true ? 'validation-pass' : 'validation-review'}>{reconciliation.passed === true ? 'Conciliada' : 'Revisar diferencias'}</span></div><div className="reconciliation-metrics"><article><small>Filas de origen</small><strong>{formatInteger(reconciliation.source_rows)}</strong></article><article><small>Filas cargadas</small><strong>{formatInteger(reconciliation.datamart_rows)}</strong></article><article><small>Diferencia</small><strong>{formatInteger(reconciliation.difference_rows)}</strong></article><article><small>Tablas creadas</small><strong>{formatInteger(tables.length)}</strong></article></div>{currency.status === 'verified' && <div className="currency-evidence"><div><strong>Divisa comprobada: {stringValue(currency.currency_code, '')}</strong><span>{stringValue(currency.message, 'La unidad monetaria fue verificada en la fuente.')}</span></div><small>Referencia: {stringValue(currency.source_reference, 'metadatos de la fuente')}</small></div>}{requiresCurrencyCheck && <div className="currency-evidence review"><div><strong>Divisa pendiente de comprobación</strong><span>Los importes están conciliados, pero el sistema todavía no debe asumir un símbolo o código monetario.</span></div><button type="button" className="secondary compact" disabled={!canRetry} onClick={onVerifyCurrency}>Comprobar divisa sin repetir el ETL</button></div>}<div className="etl-result-grid"><section><h3>Calidad por tabla</h3>{tables.map((table) => <article key={stringValue(table.table, '')}><strong>{businessTechnicalLabel(stringValue(table.table, 'Tabla'))}</strong><span>{formatInteger(table.loaded_rows)} cargadas de {formatInteger(table.source_rows)}</span>{Number(table.deduplicated_rows ?? 0) > 0 && <small>{formatInteger(table.deduplicated_rows)} duplicados controlados</small>}</article>)}</section><section><h3>Indicadores calculados</h3>{kpis.length === 0 ? <p>No se calculó un indicador compatible.</p> : kpis.map((kpi) => { const unit = stringValue(kpi.unit, ''); return <article key={stringValue(kpi.code, '')}><strong>{stringValue(kpi.name, 'Indicador')}</strong><span title={`Valor exacto: ${String(kpi.value ?? '—')}`}>{formatKpiDisplay(kpi.value, unit)}</span><small>{kpi.status === 'reconciled' ? 'Conciliado' : 'Requiere revisión'}</small></article> })}</section></div><SemanticInterpretationReview semantic={semantic} canAct={canRetry} onRetry={onRetry} onApply={onApply} /></section>
}

function SemanticInterpretationReview({ semantic, canAct, onRetry, onApply }: { semantic: Record<string, unknown>; canAct: boolean; onRetry: () => void; onApply: (groups: SpanishDecisionGroup[], analystComment: string) => void }) {
  const groups = useMemo(() => arrayValue(semantic.mappings), [semantic.mappings])
  const initial = useMemo(() => groups.flatMap((group, groupIndex) => arrayValue(group.mappings).map((mapping, mappingIndex) => ({
    key: `${groupIndex}:${mappingIndex}`,
    groupIndex,
    enabled: true,
    original: stringValue(mapping.original, ''),
    label: stringValue(mapping.label_es, ''),
  }))), [groups])
  const [decisions, setDecisions] = useState(initial)
  const [comment, setComment] = useState('Revisé las etiquetas propuestas y confirmé que representan las categorías originales.')
  const [confirmed, setConfirmed] = useState(false)
  useEffect(() => { setDecisions(initial); setConfirmed(false) }, [initial])
  const status = stringValue(semantic.status, '')
  const reviewedAt = stringValue(semantic.reviewed_at, '')
  const reviewedAtLabel = reviewedAt ? new Date(reviewedAt).toLocaleString('es-EC') : ''
  const publish = () => {
    const reviewed = groups.map((group, groupIndex) => ({
      dimension: stringValue(group.dimension, ''),
      target_column: stringValue(group.target_column, ''),
      mappings: decisions.filter((item) => item.groupIndex === groupIndex && item.enabled).map((item) => ({ original: item.original, label_es: item.label.trim() })),
    })).filter((group) => group.mappings.length > 0)
    onApply(reviewed, comment)
  }
  return <div className="semantic-safety compact"><div aria-hidden="true">ES</div><section><h3>Interpretación semántica</h3><p>{stringValue(semantic.message, 'Los originales permanecen conservados para trazabilidad.')}</p>{status === 'pending' && <><p className="field-help">{stringValue(semantic.failure_detail, '')}</p><p className="field-help">{stringValue(semantic.resolution, 'Pruebe un proveedor activo y vuelva a intentarlo.')}</p><button type="button" className="secondary" disabled={!canAct} onClick={onRetry}>Reintentar interpretación sin repetir el ETL</button></>}{status === 'applied' && <div className="semantic-publication-receipt"><div className="semantic-publication-heading"><strong>Revisión publicada</strong><span>Decisión humana registrada</span></div><dl><div><dt>Responsable</dt><dd>{stringValue(semantic.reviewed_by, 'No disponible')}</dd></div>{reviewedAtLabel && <div><dt>Fecha</dt><dd>{reviewedAtLabel}</dd></div>}<div><dt>Comentario del analista</dt><dd>{stringValue(semantic.analyst_comment, 'Sin comentario registrado.')}</dd></div></dl><div className="semantic-applied-groups">{groups.map((group) => <article key={`${stringValue(group.dimension, '')}:${stringValue(group.label_column, '')}`}><div><strong>{businessTechnicalLabel(stringValue(group.dimension, 'Dimensión'))}</strong><small>{stringValue(group.source_column, 'categoría')} → {stringValue(group.label_column, 'etiqueta española')}</small></div><ul>{arrayValue(group.mappings).map((mapping) => <li key={`${stringValue(mapping.original, '')}:${stringValue(mapping.label_es, '')}`}><span>{stringValue(mapping.original, '')}</span><span aria-hidden="true">→</span><strong>{stringValue(mapping.label_es, '')}</strong></li>)}</ul></article>)}</div><p className="field-help">Los valores originales siguen disponibles; las etiquetas se publicaron como columnas adicionales y auditables.</p></div>}{status === 'review_required' && <div className="semantic-review"><p className="field-help">Compare cada original con su etiqueta. Puede corregir la etiqueta o excluirla; ninguna elección modifica el valor de origen.</p>{groups.map((group, groupIndex) => <fieldset key={`${stringValue(group.dimension, '')}:${stringValue(group.target_column, '')}`}><legend>{businessTechnicalLabel(stringValue(group.dimension, 'Dimensión'))} · {stringValue(group.target_column, 'categoría')}</legend>{decisions.filter((item) => item.groupIndex === groupIndex).map((item) => <div className="semantic-mapping-row" key={item.key}><label><input type="checkbox" checked={item.enabled} onChange={(event) => setDecisions((current) => current.map((decision) => decision.key === item.key ? { ...decision, enabled: event.target.checked } : decision))} />Publicar</label><span>{item.original}</span><span aria-hidden="true">→</span><label>Etiqueta en español<input value={item.label} maxLength={100} disabled={!item.enabled} onChange={(event) => setDecisions((current) => current.map((decision) => decision.key === item.key ? { ...decision, label: event.target.value } : decision))} /></label></div>)}</fieldset>)}<label>Comentario de revisión<textarea rows={2} minLength={10} maxLength={500} value={comment} onChange={(event) => setComment(event.target.value)} /></label><label className="confirmation"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />Confirmo que revisé los mapeos que se publicarán.</label><button type="button" disabled={!canAct || !confirmed || comment.trim().length < 10 || decisions.some((item) => item.enabled && !item.label.trim())} onClick={publish}>Publicar etiquetas revisadas</button></div>}</section></div>
}

function objectValue(value: unknown): Record<string, unknown> { return typeof value === 'object' && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : {} }
function arrayValue(value: unknown): Array<Record<string, unknown>> { return Array.isArray(value) ? value.map(objectValue) : [] }
function stringArrayValue(value: unknown): string[] { return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [] }
function stringValue(value: unknown, fallback: string) { return typeof value === 'string' && value.trim() ? value : fallback }
function semanticRole(item: Record<string, unknown>) { const declared = stringValue(item.semantic_role, ''); if (declared) return declared; const text = `${stringValue(item.name, '')} ${stringValue(item.code, '')}`.toLocaleLowerCase('es'); if (/cliente|customer/.test(text)) return 'customer_count'; if (/cantidad|unidades|quantity|qty/.test(text)) return 'quantity'; if (/conteo|pedido|transacci|order/.test(text)) return 'transaction_count'; return 'sales_amount' }
function semanticRoleLabel(value: string) { return ({ sales_amount: 'Importe de ventas', quantity: 'Cantidad vendida', customer_count: 'Conteo de clientes', transaction_count: 'Conteo de transacciones' } as Record<string, string>)[value] ?? value }
function etlLabel(value: string) { return ({ extract: 'Extracción', join: 'Unión validada', filter: 'Filtro', derive: 'Derivación', aggregate: 'Agregación', load: 'Carga controlada' } as Record<string, string>)[value] ?? value }

function ResourcePage({ page, data, message, token, canWrite, onSaved, onChangePage }: { page: string; data: PageData; message: string; token: string; canWrite: boolean; onSaved: () => void; onChangePage: (offset: number) => void }) {
  const [selected, setSelected] = useState<Row | null>(null)
  const [feedback, setFeedback] = useState<{ message: string; kind: 'success' | 'error' } | null>(null)
  const [credentialTarget, setCredentialTarget] = useState<Row | null>(null)
  const [credentialValue, setCredentialValue] = useState('')
  const [credentialError, setCredentialError] = useState('')
  const rows = (data?.items ?? []) as unknown as Row[]

  async function toggleActive(row: Row) {
    const isActive = row.is_active === true
    setFeedback(null)
    try {
      if (page === '/usuarios') await api.update(`/users/${row.id}`, token, { is_active: !isActive })
      else if (page === '/roles') await api.update(`/roles/${row.id}`, token, { is_active: !isActive })
      else if (page === '/permisos') await api.update(`/permissions/${row.id}`, token, { is_active: !isActive })
      else if (page === '/menus') await api.update(`/menus/${row.id}`, token, { is_active: !isActive })
      else if (page === '/parametros') await api.upsert(`/parameters/${row.key}`, token, { key: row.key, value: row.value, description: row.description ?? null, is_active: !isActive })
      else if (page === '/llm') await api.upsert(`/llm-configurations/${row.id}`, token, { name: row.name, provider_kind: row.provider_kind, base_url: row.base_url, model_id: row.model_id, reasoning_level: row.reasoning_level ?? 'minimal', is_active: !isActive })
      onSaved()
    } catch (caught) {
      setFeedback({ message: caught instanceof Error ? caught.message : 'No fue posible cambiar el estado.', kind: 'error' })
    }
  }

  async function testLlm(row: Row) {
    setFeedback(null)
    try {
      const result = await api.testLlm(token, Number(row.id))
      setFeedback({ message: result.message, kind: result.ok ? 'success' : 'error' })
      onSaved()
    } catch (caught) {
      setFeedback({ message: caught instanceof Error ? caught.message : 'No fue posible probar la conexión LLM.', kind: 'error' })
    }
  }

  async function saveCredential(event: FormEvent) {
    event.preventDefault()
    if (!credentialTarget) return
    setCredentialError('')
    setFeedback(null)
    try {
      const result = await api.saveLlmCredential(token, Number(credentialTarget.id), credentialValue)
      setCredentialValue('')
      setCredentialTarget(null)
      setFeedback({ message: result.message, kind: 'success' })
      onSaved()
    } catch (caught) {
      setCredentialError(caught instanceof Error ? caught.message : 'No fue posible proteger la credencial.')
    }
  }

  function cancelCredential() {
    setCredentialValue('')
    setCredentialError('')
    setCredentialTarget(null)
  }

  async function remove(row: Row) {
    const label = readLabel(row)
    if (!window.confirm(`Eliminar definitivamente “${label}”? Esta acción no se puede deshacer.`)) return
    setFeedback(null)
    try {
      if (page === '/usuarios') await api.remove(`/users/${row.id}`, token)
      else if (page === '/roles') await api.remove(`/roles/${row.id}`, token)
      else if (page === '/menus') await api.remove(`/menus/${row.id}`, token)
      else if (page === '/llm') await api.remove(`/llm-configurations/${row.id}`, token)
      else return
      setSelected(null)
      onSaved()
    } catch (caught) {
      setFeedback({ message: caught instanceof Error ? caught.message : 'No fue posible eliminar el registro.', kind: 'error' })
    }
  }

  if (message) return <p className="notice error">{message}</p>
  if (!data) return <p className="notice">Cargando información…</p>

  return <>
    {canWrite && !['/auditoria', '/permisos', '/parametros'].includes(page) && (page !== '/menus' || selected) && <CrudForm page={page} token={token} selected={selected} onSaved={() => { setSelected(null); onSaved() }} />}
    {canWrite && page === '/menus' && !selected && <p className="notice">Seleccione Editar en un menú registrado para ajustar su etiqueta, orden o permisos. Las rutas y claves internas las administra el sistema.</p>}
    {page === '/permisos' && <p className="notice">Este catálogo explica los permisos registrados por los módulos del sistema. Los permisos técnicos no se crean desde el navegador.</p>}
    {credentialTarget && <form className="crud-form credential-form" onSubmit={saveCredential}>
      <div className="form-title"><h2>{credentialTarget.credential_configured === true ? 'Reemplazar credencial' : 'Registrar credencial'}</h2><span>{String(credentialTarget.name)}</span></div>
      <p>La clave se enviará una sola vez, se almacenará cifrada y no volverá a mostrarse.</p>
      <label>API key<input type="password" autoComplete="new-password" minLength={8} maxLength={4096} value={credentialValue} onChange={(event) => setCredentialValue(event.target.value)} required autoFocus /></label>
      <div className="form-actions"><button>Guardar credencial</button><button type="button" className="secondary" onClick={cancelCredential}>Cancelar</button></div>
      {credentialError && <p className="notice error" role="alert">{credentialError}</p>}
    </form>}
    {feedback && <p className={`notice ${feedback.kind}`} role={feedback.kind === 'error' ? 'alert' : 'status'}>{feedback.message}</p>}
    <div className="table-wrap">
      <table>
        <thead><tr><th>Elemento</th><th>Detalle</th><th>Estado</th>{canWrite && page !== '/auditoria' && <th>Acciones</th>}</tr></thead>
        <tbody>{rows.map((row) => <tr key={String(row.id)}><td>{readLabel(row)}</td><td>{page === '/llm' ? <><span>{String(row.provider_kind)} · razonamiento {reasoningLabel(String(row.reasoning_level ?? 'minimal'))}</span><br /><small>{row.provider_kind === 'ollama-local' ? 'No requiere credencial' : row.credential_configured === true ? 'Credencial configurada' : 'Credencial pendiente'}</small></> : String(row.actor_label ?? row.email ?? row.description ?? row.resource_type ?? '—')}</td><td>{String(row.is_active ?? row.last_test_status ?? row.resource_type ?? 'Registrado')}</td>{canWrite && !['/auditoria', '/permisos', '/parametros'].includes(page) && <td><div className="row-actions"><button className="table-action" onClick={() => setSelected(row)}>Editar</button>{row.is_system_protected === true ? <span className="protected-label">Protegido</span> : <><button className="table-action secondary" onClick={() => toggleActive(row)}>{row.is_active === true ? 'Desactivar' : 'Activar'}</button><button className="table-action danger" onClick={() => remove(row)}>Eliminar</button></>}{page === '/llm' && row.provider_kind !== 'ollama-local' && <button className="table-action secondary" onClick={() => { setCredentialTarget(row); setCredentialValue(''); setCredentialError('') }}>{row.credential_configured === true ? 'Reemplazar credencial' : 'Registrar credencial'}</button>}{page === '/llm' && <button className="table-action secondary" onClick={() => testLlm(row)}>Probar conexión</button>}</div></td>}</tr>)}</tbody>
      </table>
      {page === '/llm' && <p className="notice">Las credenciales cloud se registran desde esta pantalla, se almacenan cifradas y nunca se muestran nuevamente. Ollama local no requiere API key.</p>}
      {page === '/auditoria' && <p className="notice">La auditoría es de consulta: registra las acciones críticas, no se modifica desde la interfaz.</p>}
      <Pagination page={data} onChange={onChangePage} />
    </div>
  </>
}

const emptyConnection = {
  name: '', host: '', port: '1433', database_name: '', username: '', password: '', encrypt: true, trust_server_certificate: true,
}

function ConnectionsPage({ data, message, token, canWrite, canTest, canRefresh, onSaved, onChangePage }: { data: Page<DataConnection> | null; message: string; token: string; canWrite: boolean; canTest: boolean; canRefresh: boolean; onSaved: () => void; onChangePage: (offset: number) => void }) {
  const [selected, setSelected] = useState<DataConnection | null>(null)
  const [values, setValues] = useState(emptyConnection)
  const [feedback, setFeedback] = useState<{ message: string; kind: 'success' | 'error' } | null>(null)
  const [activeSource, setActiveSource] = useState<ActiveSource | null>(null)
  const [capturing, setCapturing] = useState(false)

  useEffect(() => {
    api.activeSource(token).then(setActiveSource).catch(() => setActiveSource(null))
  }, [data, token])

  function beginEdit(item: DataConnection) {
    setSelected(item)
    setValues({ name: item.name, host: item.host, port: String(item.port), database_name: item.database_name, username: item.username, password: '', encrypt: item.encrypt, trust_server_certificate: item.trust_server_certificate })
    setFeedback(null)
  }

  function cancelEdit() {
    setSelected(null)
    setValues(emptyConnection)
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    setFeedback(null)
    const body = { connector_kind: 'sqlserver', name: values.name, host: values.host, port: Number(values.port), database_name: values.database_name, username: values.username, encrypt: values.encrypt, trust_server_certificate: values.trust_server_certificate, ...(!selected || values.password ? { password: values.password } : {}) }
    try {
      if (selected) await api.upsert(`/connections/${selected.id}`, token, body)
      else await api.create('/connections', token, body)
      cancelEdit()
      onSaved()
    } catch (caught) {
      setFeedback({ message: caught instanceof Error ? caught.message : 'No fue posible guardar la conexión.', kind: 'error' })
    }
  }

  async function perform(item: DataConnection, action: 'test' | 'activate' | 'deactivate' | 'delete') {
    if (action === 'delete' && !window.confirm(`Eliminar definitivamente “${item.name}”?`)) return
    setFeedback(null)
    try {
      if (action === 'test') {
        const result = await api.testConnection(token, item.id)
        setFeedback({ message: result.message, kind: result.ok ? 'success' : 'error' })
      } else if (action === 'activate') {
        await api.activateConnection(token, item.id)
        setFeedback({ message: 'La fuente quedó activa para los siguientes pasos del flujo de análisis.', kind: 'success' })
      } else if (action === 'deactivate') {
        await api.deactivateConnection(token, item.id)
        setFeedback({ message: 'La fuente fue desactivada.', kind: 'success' })
      } else {
        await api.remove(`/connections/${item.id}`, token)
        setFeedback({ message: 'La conexión y su contraseña cifrada fueron eliminadas.', kind: 'success' })
      }
      onSaved()
    } catch (caught) {
      setFeedback({ message: caught instanceof Error ? caught.message : 'No fue posible completar la acción.', kind: 'error' })
    }
  }

  async function captureMetadata() {
    setFeedback(null)
    setCapturing(true)
    try {
      const result = await api.captureMetadata(token)
      setFeedback({ message: result.message, kind: 'success' })
      setActiveSource(await api.activeSource(token))
      onSaved()
    } catch (caught) {
      setFeedback({ message: caught instanceof Error ? caught.message : 'No fue posible actualizar los metadatos.', kind: 'error' })
    } finally {
      setCapturing(false)
    }
  }

  if (message) return <p className="notice error">{message}</p>
  if (!data) return <p className="notice">Cargando información…</p>
  return <>
    <p className="lead">Registre una fuente SQL Server sin editar archivos. La contraseña se cifra y nunca vuelve a mostrarse.</p>
    {activeSource?.connection && <section className="source-summary" aria-label="Fuente activa">
      <div><p className="eyebrow">Fuente activa</p><h2>{activeSource.connection.name}</h2><p>{activeSource.connection.database_name} · Sólo lectura validada</p></div>
      <div className="source-metrics"><span><strong>{activeSource.latest_snapshot?.table_count ?? '—'}</strong> tablas</span><span><strong>{activeSource.latest_snapshot?.column_count ?? '—'}</strong> columnas</span><span><strong>{activeSource.latest_snapshot?.relationship_count ?? '—'}</strong> relaciones</span></div>
      {canRefresh && <button onClick={captureMetadata} disabled={capturing}>{capturing ? 'Leyendo estructura…' : 'Actualizar metadatos'}</button>}
      <small>{activeSource.latest_snapshot ? `Última instantánea: ${new Date(activeSource.latest_snapshot.captured_at).toLocaleString('es-EC')}` : 'Todavía no existe una instantánea. Esta acción lee estructura, nunca filas.'}</small>
    </section>}
    {canWrite && <form className="crud-form" onSubmit={submit}>
      <div className="form-title"><h2>{selected ? 'Editar conexión' : 'Registrar conexión'}</h2><span>En este sprint se admite una única fuente activa y sólo el motor SQL Server.</span></div>
      <div className="form-grid">
        <label>Nombre visible<input required minLength={3} maxLength={120} value={values.name} onChange={(event) => setValues({ ...values, name: event.target.value })} /></label>
        <label>Motor<select value="sqlserver" disabled><option value="sqlserver">SQL Server</option></select></label>
        <label>Servidor<input required placeholder="sqlserver o servidor.empresa.local" value={values.host} onChange={(event) => setValues({ ...values, host: event.target.value })} /></label>
        <label>Puerto<input required type="number" min="1" max="65535" value={values.port} onChange={(event) => setValues({ ...values, port: event.target.value })} /></label>
        <label>Base de datos<input required placeholder="AdventureWorks2022" value={values.database_name} onChange={(event) => setValues({ ...values, database_name: event.target.value })} /></label>
        <label>Usuario de sólo lectura<input required value={values.username} onChange={(event) => setValues({ ...values, username: event.target.value })} /></label>
        <label>Contraseña<input required={!selected} type="password" minLength={8} autoComplete="new-password" placeholder={selected ? 'Déjela vacía para conservarla' : ''} value={values.password} onChange={(event) => setValues({ ...values, password: event.target.value })} /></label>
      </div>
      <div className="connection-options"><label><input type="checkbox" checked={values.encrypt} onChange={(event) => setValues({ ...values, encrypt: event.target.checked })} /> Cifrar transporte</label><label><input type="checkbox" checked={values.trust_server_certificate} onChange={(event) => setValues({ ...values, trust_server_certificate: event.target.checked })} /> Confiar en certificado local</label></div>
      <div className="form-actions"><button>{selected ? 'Guardar cambios' : 'Registrar conexión'}</button>{selected && <button type="button" className="secondary" onClick={cancelEdit}>Cancelar</button>}</div>
    </form>}
    {feedback && <p className={`notice ${feedback.kind}`} role={feedback.kind === 'error' ? 'alert' : 'status'}>{feedback.message}</p>}
    <div className="table-wrap"><table><thead><tr><th>Fuente</th><th>Destino</th><th>Validación</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{data.items.map((item) => <tr key={item.id}><td><strong>{item.name}</strong><br /><small>SQL Server</small></td><td>{item.host}:{item.port}<br /><small>{item.database_name} · {item.username}</small></td><td>{item.last_test_status === 'ok' ? 'Sólo lectura validada' : item.last_test_status === 'error' ? 'Prueba fallida' : 'Pendiente'}{item.last_tested_at && <><br /><small>{new Date(item.last_tested_at).toLocaleString('es-EC')}</small></>}</td><td>{item.is_active ? 'Activa' : 'Inactiva'}</td><td><div className="row-actions">{canWrite && !item.is_active && <button className="table-action" onClick={() => beginEdit(item)}>Editar</button>}{canTest && <button className="table-action secondary" onClick={() => perform(item, 'test')}>Probar conexión</button>}{canWrite && (item.is_active ? <button className="table-action secondary" onClick={() => perform(item, 'deactivate')}>Desactivar</button> : <button className="table-action secondary" disabled={item.last_test_status !== 'ok'} onClick={() => perform(item, 'activate')}>Activar</button>)}{canWrite && !item.is_active && <button className="table-action danger" onClick={() => perform(item, 'delete')}>Eliminar</button>}</div></td></tr>)}</tbody></table>{data.items.length === 0 && <p className="notice">Todavía no hay conexiones registradas.</p>}<Pagination page={data} onChange={onChangePage} /></div>
  </>
}

function SchemaExplorerPage({ snapshots, message, token, canRefresh, onSaved, onChangePage }: { snapshots: Page<MetadataSnapshot> | null; message: string; token: string; canRefresh: boolean; onSaved: () => void; onChangePage: (offset: number) => void }) {
  const [activeSource, setActiveSource] = useState<ActiveSource | null>(null)
  const [snapshotId, setSnapshotId] = useState<number | null>(null)
  const [searchDraft, setSearchDraft] = useState('')
  const [schemaDraft, setSchemaDraft] = useState('')
  const [filters, setFilters] = useState({ search: '', schema: '' })
  const [tables, setTables] = useState<Page<MetadataTable> | null>(null)
  const [tableOffset, setTableOffset] = useState(0)
  const [selectedTable, setSelectedTable] = useState<MetadataTable | null>(null)
  const [detail, setDetail] = useState<MetadataTableDetail | null>(null)
  const [localFeedback, setLocalFeedback] = useState<{ message: string; kind: 'success' | 'error' } | null>(null)
  const [capturing, setCapturing] = useState(false)

  useEffect(() => {
    api.activeSource(token).then(setActiveSource).catch((caught: Error) => setLocalFeedback({ message: caught.message, kind: 'error' }))
  }, [snapshots, token])

  useEffect(() => {
    const availableIds = new Set(snapshots?.items.map((item) => item.id) ?? [])
    const firstId = snapshots?.items[0]?.id ?? null
    setSnapshotId((current) => (current !== null && availableIds.has(current) ? current : firstId))
  }, [snapshots])

  useEffect(() => {
    if (!snapshotId) return
    let currentRequest = true
    setTables(null)
    setDetail(null)
    setLocalFeedback(null)
    api.metadataTables(token, snapshotId, filters.search, filters.schema, pageSize, tableOffset)
      .then((result) => {
        if (!currentRequest) return
        setTables(result)
        setSelectedTable((current) => result.items.find((item) => item.schema_name === current?.schema_name && item.table_name === current?.table_name) ?? result.items[0] ?? null)
      })
      .catch((caught: Error) => {
        if (currentRequest) setLocalFeedback({ message: caught.message, kind: 'error' })
      })
    return () => { currentRequest = false }
  }, [filters, snapshotId, tableOffset, token])

  useEffect(() => {
    if (!snapshotId || !selectedTable) {
      setDetail(null)
      return
    }
    let currentRequest = true
    setDetail(null)
    api.metadataTable(token, snapshotId, selectedTable.schema_name, selectedTable.table_name)
      .then((result) => { if (currentRequest) setDetail(result) })
      .catch((caught: Error) => {
        if (currentRequest) setLocalFeedback({ message: caught.message, kind: 'error' })
      })
    return () => { currentRequest = false }
  }, [selectedTable, snapshotId, token])

  async function capture() {
    setCapturing(true)
    setLocalFeedback(null)
    try {
      const result = await api.captureMetadata(token)
      setLocalFeedback({ message: result.message, kind: 'success' })
      setSnapshotId(result.snapshot.id)
      setTableOffset(0)
      onSaved()
    } catch (caught) {
      setLocalFeedback({ message: caught instanceof Error ? caught.message : 'No fue posible actualizar los metadatos.', kind: 'error' })
    } finally {
      setCapturing(false)
    }
  }

  function applyFilters(event: FormEvent) {
    event.preventDefault()
    setTableOffset(0)
    setFilters({ search: searchDraft.trim(), schema: schemaDraft.trim() })
  }

  if (message) return <p className="notice error">{message}</p>
  if (!snapshots) return <p className="notice">Cargando instantáneas…</p>
  if (!activeSource?.connection) return <div className="empty-state"><h2>No hay una fuente activa</h2><p>Un administrador debe probar y activar una conexión SQL Server antes de leer su estructura.</p></div>
  if (snapshots.items.length === 0) return <div className="empty-state"><h2>Todavía no hay metadatos</h2><p>La instantánea incluirá tablas, columnas y relaciones declaradas, pero nunca filas ni credenciales.</p>{canRefresh && <button onClick={capture} disabled={capturing}>{capturing ? 'Leyendo estructura…' : 'Crear primera instantánea'}</button>}{localFeedback && <p className={`notice ${localFeedback.kind}`} role={localFeedback.kind === 'error' ? 'alert' : 'status'}>{localFeedback.message}</p>}</div>

  const currentSnapshot = snapshots.items.find((item) => item.id === snapshotId) ?? snapshots.items[0]
  return <>
    <div className="explorer-header"><div><p className="lead">Consulte la estructura capturada de <strong>{activeSource.connection.name}</strong>. Esta vista no lee filas del negocio.</p><p className="snapshot-meta">Instantánea #{currentSnapshot.id} · {new Date(currentSnapshot.captured_at).toLocaleString('es-EC')} · huella {currentSnapshot.content_hash.slice(0, 12)}</p></div>{canRefresh && <button onClick={capture} disabled={capturing}>{capturing ? 'Leyendo estructura…' : 'Actualizar metadatos'}</button>}</div>
    <div className="snapshot-metrics" aria-label="Resumen de la instantánea"><article><strong>{currentSnapshot.schema_count}</strong><span>esquemas</span></article><article><strong>{currentSnapshot.table_count}</strong><span>tablas</span></article><article><strong>{currentSnapshot.column_count}</strong><span>columnas</span></article><article><strong>{currentSnapshot.relationship_count}</strong><span>relaciones</span></article></div>
    {snapshots.items.length > 1 && <label className="snapshot-selector">Versión de metadatos<select value={currentSnapshot.id} onChange={(event) => { setSnapshotId(Number(event.target.value)); setTableOffset(0); setSelectedTable(null); setLocalFeedback(null) }}>{snapshots.items.map((item) => <option key={item.id} value={item.id}>#{item.id} · {new Date(item.captured_at).toLocaleString('es-EC')} · {item.content_hash.slice(0, 8)}</option>)}</select></label>}
    <form className="explorer-filters" onSubmit={applyFilters}><label>Buscar tabla o columna<input value={searchDraft} maxLength={120} placeholder="Ejemplo: pedido, SalesOrderID" onChange={(event) => setSearchDraft(event.target.value)} /></label><label>Esquema<input value={schemaDraft} maxLength={128} placeholder="Ejemplo: Sales" onChange={(event) => setSchemaDraft(event.target.value)} /></label><button>Buscar</button></form>
    {localFeedback && <p className={`notice ${localFeedback.kind}`} role={localFeedback.kind === 'error' ? 'alert' : 'status'}>{localFeedback.message}</p>}
    <div className="schema-explorer">
      <section className="schema-table-list" aria-label="Tablas de la instantánea"><h2>Tablas</h2>{!tables ? <p>Cargando tablas…</p> : tables.items.length === 0 ? <p className="notice">No se encontraron coincidencias.</p> : <>{tables.items.map((item) => <button key={`${item.schema_name}.${item.table_name}`} title={`${item.schema_name}.${item.table_name}`} className={selectedTable?.schema_name === item.schema_name && selectedTable?.table_name === item.table_name ? 'selected' : ''} onClick={() => setSelectedTable(item)}><span><small>{item.schema_name}</small><strong>{item.table_name}</strong></span><span>{item.column_count} columnas<br /><small>{item.relationship_count} relaciones salientes</small></span></button>)}<Pagination page={tables} onChange={setTableOffset} /></>}</section>
      <section className="schema-table-detail" aria-live="polite">{!selectedTable ? <div className="empty-state"><h2>Seleccione una tabla</h2><p>Verá columnas, claves y relaciones declaradas.</p></div> : !detail ? <p>Cargando detalle…</p> : <><div className="detail-title"><div><p className="eyebrow">{detail.schema_name}</p><h2>{detail.table_name}</h2></div><span>{detail.columns.length} columnas</span></div><div className="table-wrap"><table><thead><tr><th>Columna</th><th>Tipo</th><th>Permite nulos</th><th>Clave</th></tr></thead><tbody>{detail.columns.map((column) => <tr key={column.name}><td><strong>{column.name}</strong><br /><small>Posición {column.ordinal}</small></td><td>{column.data_type}{column.max_length > 0 && !['int', 'date', 'datetime', 'datetime2', 'bit'].includes(column.data_type) ? ` (${column.max_length})` : ''}</td><td>{column.nullable ? 'Sí' : 'No'}</td><td>{column.primary_key ? 'PK' : '—'}</td></tr>)}</tbody></table></div><div className="relationship-grid"><article><h3>Relaciones salientes</h3>{detail.foreign_keys.length === 0 ? <p>No registra claves foráneas salientes.</p> : detail.foreign_keys.map((relation) => <p key={relation.name}><strong>{relation.columns.join(', ')}</strong> → {relation.referenced_schema}.{relation.referenced_table} ({relation.referenced_columns.join(', ')})</p>)}</article><article><h3>Relaciones entrantes</h3>{detail.incoming_relationships.length === 0 ? <p>No registra relaciones entrantes.</p> : detail.incoming_relationships.map((relation) => <p key={`${relation.source_schema}.${relation.source_table}.${relation.name}`}><strong>{relation.source_schema}.{relation.source_table}</strong> ({relation.source_columns.join(', ')}) → {relation.referenced_columns.join(', ')}</p>)}</article></div></>}</section>
    </div>
    <Pagination page={snapshots} onChange={onChangePage} />
  </>
}

const supportedPeriodicities: AnalysisCatalogPeriodicity[] = [
  { code: 'day', label: 'Diaria', description: 'Agrupa resultados por día cuando existe una fecha de negocio verificable.', enabled: true },
  { code: 'week', label: 'Semanal', description: 'Agrupa resultados por semana cuando existe una fecha de negocio verificable.', enabled: true },
  { code: 'month', label: 'Mensual', description: 'Agrupa resultados por mes cuando existe una fecha de negocio verificable.', enabled: true },
  { code: 'quarter', label: 'Trimestral', description: 'Agrupa resultados por trimestre cuando existe una fecha de negocio verificable.', enabled: true },
  { code: 'year', label: 'Anual', description: 'Agrupa resultados por año cuando existe una fecha de negocio verificable.', enabled: true },
]

function AnalysisCatalogPage({ token, canWrite }: { token: string; canWrite: boolean }) {
  const [domains, setDomains] = useState<AnalysisCatalogDomain[]>([])
  const [domainCode, setDomainCode] = useState('')
  const [draft, setDraft] = useState<AnalysisCatalogConfiguration | null>(null)
  const [periodicityToAdd, setPeriodicityToAdd] = useState<AnalysisCatalogPeriodicity['code']>('day')
  const [loading, setLoading] = useState(true)
  const [feedback, setFeedback] = useState<{ kind: 'success' | 'error'; message: string } | null>(null)

  useEffect(() => {
    api.analysisCatalogDomains(token)
      .then((items) => { setDomains(items); setDomainCode((current) => current || items[0]?.code || '') })
      .catch((error: Error) => setFeedback({ kind: 'error', message: error.message }))
  }, [token])

  useEffect(() => {
    if (!domainCode) return
    setLoading(true); setFeedback(null)
    api.analysisCatalog(token, domainCode)
      .then(setDraft)
      .catch((error: Error) => setFeedback({ kind: 'error', message: error.message }))
      .finally(() => setLoading(false))
  }, [domainCode, token])

  function changeQuestion(index: number, field: 'label' | 'description' | 'prompt_instruction' | 'enabled', value: string | boolean) {
    setDraft((current) => {
      if (!current) return current
      const questions = [...current.questions]
      questions[index] = { ...questions[index], [field]: value }
      return { ...current, questions }
    })
  }

  function changePeriodicity(index: number, field: 'label' | 'description' | 'enabled', value: string | boolean) {
    setDraft((current) => {
      if (!current) return current
      const periodicities = [...current.periodicities]
      periodicities[index] = { ...periodicities[index], [field]: value }
      return { ...current, periodicities }
    })
  }

  function addQuestion() {
    setDraft((current) => current ? { ...current, questions: [...current.questions, { code: `custom_${Date.now()}`, label: 'Nueva pregunta de negocio', description: 'Describa qué decisión de negocio ayudará a responder.', prompt_instruction: 'Interprete los metadatos para responder esta pregunta sin inventar referencias técnicas.', enabled: true }] } : current)
  }

  function addPeriodicity() {
    const option = supportedPeriodicities.find((item) => item.code === periodicityToAdd)
    if (!option) return
    setDraft((current) => current && !current.periodicities.some((item) => item.code === option.code) ? { ...current, periodicities: [...current.periodicities, option] } : current)
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    if (!draft) return
    setFeedback(null)
    try {
      const saved = await api.saveAnalysisCatalog(token, domainCode, draft)
      setDraft(saved)
      setFeedback({ kind: 'success', message: 'El catálogo analítico fue actualizado. Los nuevos análisis usarán esta configuración.' })
    } catch (caught) { setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible guardar el catálogo.' }) }
  }

  async function reset() {
    setFeedback(null)
    try {
      const restored = await api.resetAnalysisCatalog(token, domainCode)
      setDraft(restored)
      setFeedback({ kind: 'success', message: 'Se restauró el catálogo validado del dominio.' })
    } catch (caught) { setFeedback({ kind: 'error', message: caught instanceof Error ? caught.message : 'No fue posible restaurar el catálogo.' }) }
  }

  const missingPeriodicities = supportedPeriodicities.filter((option) => !draft?.periodicities.some((item) => item.code === option.code))
  const firstMissingPeriodicityCode = missingPeriodicities[0]?.code
  useEffect(() => {
    if (firstMissingPeriodicityCode) setPeriodicityToAdd(firstMissingPeriodicityCode)
  }, [firstMissingPeriodicityCode])

  return <>
    <p className="lead">Administre las guías de negocio que orientan al copiloto para cada dominio implementado. Aquí no se fija el objetivo de un análisis ni se define el modelo dimensional.</p>
    <section className="catalog-boundary"><strong>Responsabilidades separadas</strong><p>Las preguntas expresan necesidades del negocio y las periodicidades ofrecen estrategias temporales soportadas. La IA descubre dimensiones, hechos, medidas, granularidad, KPIs y el plan ETL desde los metadatos; el analista los supervisa y puede corregirlos sin SQL.</p></section>
    <label className="domain-selector">Dominio habilitado<select value={domainCode} onChange={(event) => setDomainCode(event.target.value)}>{domains.map((domain) => <option value={domain.code} key={domain.code}>{domain.label}</option>)}</select></label>
    {feedback && <p className={`notice ${feedback.kind}`} role={feedback.kind === 'error' ? 'alert' : 'status'}>{feedback.message}</p>}
    {loading || !draft ? <p className="notice">Cargando catálogo…</p> : <form className="analysis-catalog-editor" onSubmit={save}>
      <section><div className="catalog-section-heading"><div><p className="eyebrow">Orientación para la IA</p><h2>Preguntas de negocio</h2><p>El analista las seleccionará junto con un objetivo escrito para cada análisis.</p></div>{canWrite && <button type="button" onClick={addQuestion} disabled={draft.questions.length >= 12}>Agregar pregunta</button>}</div>
        <div className="catalog-options">{draft.questions.map((question, index) => <article key={question.code}><div className="catalog-item-heading"><strong>Pregunta {index + 1}</strong><label className="confirmation"><input type="checkbox" checked={question.enabled} disabled={!canWrite} onChange={(event) => changeQuestion(index, 'enabled', event.target.checked)} />Habilitada</label></div><label>Etiqueta<input required minLength={3} maxLength={120} value={question.label} disabled={!canWrite} onChange={(event) => changeQuestion(index, 'label', event.target.value)} /></label><label>Explicación para el analista<textarea required rows={2} minLength={10} maxLength={300} value={question.description} disabled={!canWrite} onChange={(event) => changeQuestion(index, 'description', event.target.value)} /></label><label>Instrucción funcional para la IA<textarea required rows={3} minLength={10} maxLength={500} value={question.prompt_instruction} disabled={!canWrite} onChange={(event) => changeQuestion(index, 'prompt_instruction', event.target.value)} /></label><small>Identificador interno: {question.code}</small>{canWrite && <button type="button" className="danger compact" disabled={draft.questions.length === 1} onClick={() => setDraft({ ...draft, questions: draft.questions.filter((_, itemIndex) => itemIndex !== index) })}>Retirar pregunta</button>}</article>)}</div>
      </section>
      <section><div className="catalog-section-heading"><div><p className="eyebrow">Estrategias soportadas</p><h2>Periodicidades</h2><p>Puede habilitar varias opciones. Sólo se ofrecen estrategias que la aplicación podrá validar y materializar.</p></div></div>
        <div className="catalog-options compact-catalog">{draft.periodicities.map((option, index) => <article key={option.code}><div className="catalog-item-heading"><strong>{option.label}</strong><label className="confirmation"><input type="checkbox" checked={option.enabled} disabled={!canWrite} onChange={(event) => changePeriodicity(index, 'enabled', event.target.checked)} />Habilitada</label></div><label>Etiqueta<input required minLength={3} maxLength={100} value={option.label} disabled={!canWrite} onChange={(event) => changePeriodicity(index, 'label', event.target.value)} /></label><label>Explicación<textarea required rows={2} minLength={10} maxLength={240} value={option.description} disabled={!canWrite} onChange={(event) => changePeriodicity(index, 'description', event.target.value)} /></label>{canWrite && <button type="button" className="danger compact" disabled={draft.periodicities.length === 1} onClick={() => setDraft({ ...draft, periodicities: draft.periodicities.filter((_, itemIndex) => itemIndex !== index) })}>Retirar periodicidad</button>}</article>)}</div>
        {canWrite && missingPeriodicities.length > 0 && <div className="catalog-add-row"><label>Agregar periodicidad<select value={periodicityToAdd} onChange={(event) => setPeriodicityToAdd(event.target.value as AnalysisCatalogPeriodicity['code'])}>{missingPeriodicities.map((item) => <option value={item.code} key={item.code}>{item.label}</option>)}</select></label><button type="button" onClick={addPeriodicity}>Agregar</button></div>}
      </section>
      {canWrite ? <div className="form-actions"><button>Guardar catálogo</button><button type="button" className="secondary" onClick={() => void reset()}>Restaurar catálogo validado</button></div> : <p className="notice">Su perfil puede consultar este catálogo, pero no modificarlo.</p>}
    </form>}
  </>
}

function ParametersPage({ data, message, token, canWrite, onSaved, onChangePage }: { data: Page<Parameter> | null; message: string; token: string; canWrite: boolean; onSaved: () => void; onChangePage: (offset: number) => void }) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [feedback, setFeedback] = useState<{ message: string; kind: 'success' | 'error' } | null>(null)
  const dirtyKeys = useRef(new Set<string>())
  useEffect(() => {
    if (!data) return
    setValues((current) => Object.fromEntries(data.items.map((item) => [item.key, dirtyKeys.current.has(item.key) ? current[item.key] ?? item.value : item.value])))
  }, [data])

  async function save(item: Parameter) {
    setFeedback(null)
    try {
      await api.upsert(`/parameters/${item.key}`, token, { value: values[item.key] })
      dirtyKeys.current.delete(item.key)
      setFeedback({ message: `${item.name} fue actualizado.`, kind: 'success' })
      onSaved()
    } catch (caught) { setFeedback({ message: caught instanceof Error ? caught.message : 'No fue posible guardar el parámetro.', kind: 'error' }) }
  }
  async function reset(item: Parameter) {
    setFeedback(null)
    try {
      await api.resetParameter(token, item.key)
      dirtyKeys.current.delete(item.key)
      setFeedback({ message: `${item.name} volvió a su valor predeterminado.`, kind: 'success' })
      onSaved()
    } catch (caught) { setFeedback({ message: caught instanceof Error ? caught.message : 'No fue posible restaurar el parámetro.', kind: 'error' }) }
  }
  if (message) return <p className="notice error">{message}</p>
  if (!data) return <p className="notice">Cargando información…</p>
  return <>
    <p className="lead">Estos son los únicos parámetros operativos aprobados. No se pueden crear claves libres ni guardar secretos aquí.</p>
    {feedback && <p className={`notice ${feedback.kind}`} role={feedback.kind === 'error' ? 'alert' : 'status'}>{feedback.message}</p>}
    <div className="parameter-grid">{data.items.map((item) => <article className="parameter-card" key={item.id}><div><p className="eyebrow">{item.module_code}</p><h2>{item.name}</h2><p>{item.description}</p><small>{item.key}</small></div><label>Valor<input type="number" min={item.min_value} max={item.max_value} value={values[item.key] ?? item.value} disabled={!canWrite} onChange={(event) => { dirtyKeys.current.add(item.key); setValues((current) => ({ ...current, [item.key]: event.target.value })) }} /></label><p className="parameter-range">Rango: {item.min_value}–{item.max_value} · Predeterminado: {item.default_value}</p>{canWrite && <div className="row-actions"><button onClick={() => void save(item)}>Guardar</button><button className="secondary" onClick={() => void reset(item)} disabled={item.value === item.default_value}>Restaurar</button></div>}</article>)}</div>
    <Pagination page={data} onChange={onChangePage} />
  </>
}

function Pagination({ page, onChange }: { page: { total: number; limit: number; offset: number }; onChange: (offset: number) => void }) {
  if (page.total <= page.limit) return null
  const from = page.offset + 1
  const to = Math.min(page.offset + page.limit, page.total)
  return <div className="pagination" aria-label="Paginación"><span>Mostrando {from}-{to} de {page.total} registros</span><div><button className="secondary" disabled={page.offset === 0} onClick={() => onChange(Math.max(0, page.offset - page.limit))}>Anterior</button><button disabled={page.offset + page.limit >= page.total} onClick={() => onChange(page.offset + page.limit)}>Siguiente</button></div></div>
}

function CrudForm({ page, token, selected, onSaved }: { page: string; token: string; selected: Row | null; onSaved: () => void }) {
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const config = useMemo(() => formConfig(page, token, roles, permissions, selected), [page, permissions, roles, selected, token])
  const [values, setValues] = useState<Values>(config.empty)
  const [error, setError] = useState('')

  useEffect(() => {
    setValues(selected ? config.read(selected) : config.empty)
    setError('')
  }, [config, selected])
  useEffect(() => {
    if (page === '/usuarios') api.roles(token, 100, 0).then((result) => setRoles(result.items)).catch(() => setRoles([]))
    if (page === '/roles' || page === '/menus') api.permissions(token, 100, 0).then((result) => setPermissions(result.items)).catch(() => setPermissions([]))
  }, [page, token])
  if (!config) return null

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    try {
      if (selected) await config.update(selected, values)
      else await config.create(values)
      onSaved()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'No fue posible guardar el cambio.')
    }
  }

  return <form className="crud-form" onSubmit={submit}>
    <div className="form-title"><h2>{selected ? `Editar ${config.singular}` : config.createTitle}</h2><span>{selected ? 'Actualice los datos y guarde los cambios.' : config.help}</span></div>
    <div className="form-grid">{config.fields.map((field) => field.kind === 'checks' ? <CheckboxTable key={field.key} field={field} value={values[field.key] ?? ''} onChange={(value) => setValues({ ...values, [field.key]: value })} /> : <label key={field.key}>{field.label}{field.kind === 'select' ? <select required={field.required ?? true} value={values[field.key] ?? ''} onChange={(event) => {
      const value = event.target.value
      if (page === '/llm' && field.key === 'provider_kind') setValues({ ...values, provider_kind: value, ...(llmProviderPresets[value] ?? {}) })
      else setValues({ ...values, [field.key]: value })
    }}>{field.options?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select> : <input required={(field.required ?? true) && !(selected && field.secret)} type={field.secret ? 'password' : field.inputType ?? 'text'} placeholder={selected && field.secret ? 'Déjela vacía para conservar la contraseña actual' : field.placeholder} value={values[field.key] ?? ''} onChange={(event) => setValues({ ...values, [field.key]: event.target.value })} />}</label>)}</div>
    <div className="form-actions"><button>{selected ? 'Guardar cambios' : 'Crear registro'}</button>{selected && <button type="button" className="secondary" onClick={onSaved}>Cancelar</button>}</div>
    {error && <p className="notice error">{error}</p>}
  </form>
}

function CheckboxTable({ field, value, onChange }: { field: Field; value: string; onChange: (value: string) => void }) {
  const selected = new Set(value.split(',').filter(Boolean))
  const toggle = (option: Choice) => {
    if (selected.has(option.value)) selected.delete(option.value)
    else selected.add(option.value)
    onChange(Array.from(selected).join(','))
  }
  return <fieldset className="checkbox-table-field"><legend>{field.label}</legend><p>{field.help ?? 'Marque las opciones que correspondan.'}</p><div className="checkbox-table-wrap"><table><thead><tr><th>Asignar</th><th>Nombre</th><th>Descripción</th></tr></thead><tbody>{field.options?.map((option) => <tr key={option.value}><td><input type="checkbox" aria-label={`Asignar ${option.label}`} checked={selected.has(option.value)} onChange={() => toggle(option)} /></td><td>{option.label}</td><td>{option.detail ?? '—'}</td></tr>)}</tbody></table></div></fieldset>
}

type Choice = { value: string; label: string; detail?: string }
type Field = { key: string; label: string; placeholder?: string; secret?: boolean; inputType?: 'email' | 'text'; required?: boolean; kind?: 'select' | 'checks'; options?: Choice[]; help?: string }
type FormConfig = { singular: string; createTitle: string; help: string; fields: Field[]; empty: Values; read: (row: Row) => Values; create: (values: Values) => Promise<unknown>; update: (row: Row, values: Values) => Promise<unknown> }

const llmProviderPresets: Record<string, Partial<Values>> = {
  gemini: { base_url: 'https://generativelanguage.googleapis.com', model_id: 'gemini-3.6-flash', reasoning_level: 'minimal' },
  'groq-cloud': { base_url: 'https://api.groq.com/openai/v1', model_id: 'openai/gpt-oss-120b', reasoning_level: 'low' },
  'qwen-cloud': { base_url: 'https://dashscope-intl.aliyuncs.com', model_id: 'qwen-plus', reasoning_level: 'minimal' },
  'ollama-local': { base_url: 'http://ollama:11434', model_id: 'qwen2.5:3b', reasoning_level: 'minimal' },
}

function formConfig(page: string, token: string, roles: Role[], permissions: Permission[], selected: Row | null): FormConfig {
  const active = (row: Row) => String(row.is_active ?? true)
  if (page === '/usuarios') return {
    singular: 'usuario', createTitle: 'Crear usuario', help: 'Seleccione uno o varios roles activos. La contraseña nunca se muestra después de guardarla.',
    fields: [{ key: 'email', label: 'Correo', inputType: 'email', placeholder: 'operador@empresa.com' }, { key: 'full_name', label: 'Nombre completo' }, { key: 'password', label: 'Contraseña', secret: true }, { key: 'role_ids', label: 'Roles asignados', required: false, kind: 'checks', help: 'Marque uno o varios roles. Al editar, cambiar roles no modifica la contraseña. Los roles inactivos ya asignados se muestran sólo para poder retirarlos.', options: roleChoicesForUserAssignment(roles, ((selected?.roles as Row[] | undefined) ?? []).map((role) => String(role.id))) }],
    empty: { email: '', full_name: '', password: '', role_ids: '' }, read: (row) => ({ email: String(row.email), full_name: String(row.full_name), password: '', role_ids: ((row.roles as Row[] | undefined) ?? []).map((role) => role.id).join(',') }),
    create: (v) => api.create('/users', token, { email: v.email, full_name: v.full_name, password: v.password, role_ids: parseSelectedIds(v.role_ids) }),
    update: (row, v) => api.update(`/users/${row.id}`, token, { full_name: v.full_name, ...(v.password ? { password: v.password } : {}), role_ids: parseSelectedIds(v.role_ids) }),
  }
  if (page === '/roles') return {
    singular: 'rol', createTitle: 'Crear rol', help: 'La plataforma genera la clave interna. Seleccione los permisos por nombre y descripción.',
    fields: [{ key: 'name', label: 'Nombre' }, { key: 'description', label: 'Descripción', required: false }, { key: 'permission_ids', label: 'Permisos otorgados', required: false, kind: 'checks', help: 'Marque los privilegios que recibirá el rol. Puede retirar una casilla y guardar.', options: permissions.filter((permission) => permission.is_active).map((permission) => ({ value: String(permission.id), label: permission.name, detail: permission.description })) }],
    empty: { name: '', description: '', permission_ids: '' }, read: (row) => ({ name: String(row.name), description: String(row.description ?? ''), permission_ids: ((row.permissions as Row[] | undefined) ?? []).map((permission) => permission.id).join(',') }),
    create: (v) => api.create('/roles', token, { name: v.name, description: v.description || null, permission_ids: parseSelectedIds(v.permission_ids) }),
    update: async (row, v) => { await api.update(`/roles/${row.id}`, token, { name: v.name, description: v.description || null }); return api.upsert(`/roles/${row.id}/permissions`, token, { permission_ids: parseSelectedIds(v.permission_ids) }) },
  }
  if (page === '/permisos') return {
    singular: 'permiso', createTitle: 'Crear permiso', help: 'Los permisos se asignan después a roles o menús.',
    fields: [{ key: 'code', label: 'Código' }, { key: 'name', label: 'Nombre' }, { key: 'description', label: 'Descripción', required: false }],
    empty: { code: '', name: '', description: '' }, read: (row) => ({ code: String(row.code), name: String(row.name), description: String(row.description ?? '') }),
    create: (v) => api.create('/permissions', token, { code: v.code, name: v.name, description: v.description || null }),
    update: (row, v) => api.update(`/permissions/${row.id}`, token, { name: v.name, description: v.description || null }),
  }
  if (page === '/menus') return {
    singular: 'menú', createTitle: 'Seleccionar menú', help: 'Los menús corresponden a pantallas registradas por el sistema. Puede ajustar su etiqueta, orden y permisos.',
    fields: [{ key: 'label', label: 'Etiqueta visible' }, { key: 'position', label: 'Posición' }, { key: 'permission_ids', label: 'Permisos requeridos', required: false, kind: 'checks', help: 'Marque los permisos necesarios para visualizar esta opción de menú.', options: permissions.filter((permission) => permission.is_active).map((permission) => ({ value: String(permission.id), label: permission.name, detail: permission.description })) }],
    empty: { label: '', position: '99', permission_ids: '' }, read: (row) => ({ label: String(row.label), position: String(row.position), permission_ids: ((row.permissions as Row[] | undefined) ?? []).map((permission) => permission.id).join(',') }),
    create: async () => { throw new Error('Los menús se registran al implementar una pantalla aprobada.') },
    update: (row, v) => api.update(`/menus/${row.id}`, token, { label: v.label, position: Number(v.position), permission_ids: parseSelectedIds(v.permission_ids) }),
  }
  return {
    singular: 'configuración LLM', createTitle: 'Crear configuración LLM', help: 'Seleccione un proveedor para completar su URL y modelo recomendados. Después de guardar, registre aquí la credencial cloud cifrada. Puede revisar los valores antes de crear la configuración.',
    fields: [{ key: 'name', label: 'Nombre de configuración' }, { key: 'provider_kind', label: 'Proveedor', kind: 'select', options: [{ value: '', label: 'Seleccione un proveedor' }, { value: 'groq-cloud', label: 'Groq Cloud — rápido, recomendado para continuar' }, { value: 'gemini', label: 'Gemini Cloud' }, { value: 'qwen-cloud', label: 'Qwen Cloud' }, { value: 'ollama-local', label: 'Ollama local — no requiere API key' }] }, { key: 'base_url', label: 'URL del servicio', placeholder: 'Se completa al seleccionar el proveedor' }, { key: 'model_id', label: 'Modelo', placeholder: 'Se completa al seleccionar el proveedor' }, { key: 'reasoning_level', label: 'Nivel de razonamiento', kind: 'select', options: [{ value: 'automatic', label: 'Automático del proveedor' }, { value: 'minimal', label: 'Mínimo — demostración rápida' }, { value: 'low', label: 'Bajo — rápido y económico' }, { value: 'medium', label: 'Medio — análisis equilibrado' }, { value: 'high', label: 'Alto — mayor tiempo y consumo' }] }],
    empty: { name: '', provider_kind: '', base_url: '', model_id: '', reasoning_level: 'minimal' }, read: (row) => ({ name: String(row.name), provider_kind: String(row.provider_kind), base_url: String(row.base_url), model_id: String(row.model_id), reasoning_level: String(row.reasoning_level ?? 'minimal') }),
    create: (v) => api.create('/llm-configurations', token, { ...v, is_active: false }),
    update: (row, v) => api.upsert(`/llm-configurations/${row.id}`, token, { ...v, is_active: active(row) === 'true' }),
  }
}

function reasoningLabel(value: string) {
  return ({ automatic: 'automático', minimal: 'mínimo', low: 'bajo', medium: 'medio', high: 'alto' } as Record<string, string>)[value] ?? value
}
