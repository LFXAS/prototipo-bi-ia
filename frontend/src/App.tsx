import { FormEvent, useEffect, useMemo, useState } from 'react'

import {
  api,
  type AuditEvent,
  type LlmConfiguration,
  type Menu,
  type Page,
  type Parameter,
  type Permission,
  type Role,
  type Session,
  type User,
} from './api/security'
import { roleChoicesForUserAssignment } from './roleChoices'

type PageData =
  | Page<User>
  | Page<Role>
  | Page<Permission>
  | Page<Menu>
  | Page<Parameter>
  | Page<LlmConfiguration>
  | Page<AuditEvent>
  | null
type Row = Record<string, unknown>
type Values = Record<string, string>

const tokenKey = 'bi_ia_access_token'
const pageSize = 10
const labels: Record<string, string> = {
  '/': 'Inicio',
  '/usuarios': 'Usuarios',
  '/roles': 'Roles',
  '/permisos': 'Permisos',
  '/menus': 'Menús',
  '/parametros': 'Parámetros',
  '/llm': 'Configuración LLM',
  '/auditoria': 'Auditoría',
}

const writePermissions: Record<string, string> = {
  '/usuarios': 'security.users.write',
  '/roles': 'security.roles.write',
  '/permisos': 'security.permissions.write',
  '/menus': 'security.menus.write',
  '/parametros': 'parameters.write',
  '/llm': 'parameters.write',
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

  useEffect(() => {
    if (!token) return
    api.session(token)
      .then(setSession)
      .catch(() => {
        localStorage.removeItem(tokenKey)
        setToken('')
        setMessage('La sesión terminó. Inicie sesión nuevamente.')
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
      '/auditoria': () => api.audit(token, pageSize, offset),
    }
    setData(null)
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
            ? <Home session={session} />
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

function Home({ session }: { session: Session }) {
  return <><p className="lead">Bienvenido. Desde aquí se administra el acceso, la parametrización y la trazabilidad técnica del prototipo.</p><div className="cards"><article><strong>{session.user.roles.length}</strong><span>roles asignados</span></article><article><strong>{session.permissions.length}</strong><span>permisos efectivos</span></article><article><strong>{session.menus.length}</strong><span>opciones visibles</span></article></div><p className="notice">Los módulos BI, ETL, reportes y predicción continúan fuera del alcance de este sprint.</p></>
}

function ResourcePage({ page, data, message, token, canWrite, onSaved, onChangePage }: { page: string; data: PageData; message: string; token: string; canWrite: boolean; onSaved: () => void; onChangePage: (offset: number) => void }) {
  const [selected, setSelected] = useState<Row | null>(null)
  const [feedback, setFeedback] = useState<{ message: string; kind: 'success' | 'error' } | null>(null)
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
      else if (page === '/llm') await api.upsert(`/llm-configurations/${row.id}`, token, { name: row.name, provider_kind: row.provider_kind, base_url: row.base_url, model_id: row.model_id, is_active: !isActive })
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
    {page === '/parametros' && <p className="notice">No hay parámetros operativos habilitados todavía. Esta pantalla mostrará únicamente valores aprobados por un módulo que los consuma.</p>}
    {feedback && <p className={`notice ${feedback.kind}`} role={feedback.kind === 'error' ? 'alert' : 'status'}>{feedback.message}</p>}
    <div className="table-wrap">
      <table>
        <thead><tr><th>Elemento</th><th>Detalle</th><th>Estado</th>{canWrite && page !== '/auditoria' && <th>Acciones</th>}</tr></thead>
        <tbody>{rows.map((row) => <tr key={String(row.id)}><td>{readLabel(row)}</td><td>{String(row.actor_label ?? row.email ?? row.description ?? row.provider_kind ?? row.resource_type ?? '—')}</td><td>{String(row.is_active ?? row.last_test_status ?? row.resource_type ?? 'Registrado')}</td>{canWrite && !['/auditoria', '/permisos', '/parametros'].includes(page) && <td><div className="row-actions"><button className="table-action" onClick={() => setSelected(row)}>Editar</button>{row.is_system_protected === true ? <span className="protected-label">Protegido</span> : <><button className="table-action secondary" onClick={() => toggleActive(row)}>{row.is_active === true ? 'Desactivar' : 'Activar'}</button><button className="table-action danger" onClick={() => remove(row)}>Eliminar</button></>}{page === '/llm' && <button className="table-action secondary" onClick={() => testLlm(row)}>Probar conexión</button>}</div></td>}</tr>)}</tbody>
      </table>
      {page === '/llm' && <p className="notice">Las credenciales se leen por referencia desde el entorno y nunca se almacenan aquí.</p>}
      {page === '/auditoria' && <p className="notice">La auditoría es de consulta: registra las acciones críticas, no se modifica desde la interfaz.</p>}
      <Pagination page={data} onChange={onChangePage} />
    </div>
  </>
}

function Pagination({ page, onChange }: { page: Exclude<PageData, null>; onChange: (offset: number) => void }) {
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
    <div className="form-grid">{config.fields.map((field) => field.kind === 'checks' ? <CheckboxTable key={field.key} field={field} value={values[field.key] ?? ''} onChange={(value) => setValues({ ...values, [field.key]: value })} /> : <label key={field.key}>{field.label}{field.kind === 'select' ? <select required={field.required ?? true} value={values[field.key] ?? ''} onChange={(event) => setValues({ ...values, [field.key]: event.target.value })}>{field.options?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select> : <input required={(field.required ?? true) && !(selected && field.secret)} type={field.secret ? 'password' : field.inputType ?? 'text'} placeholder={selected && field.secret ? 'Déjela vacía para conservar la contraseña actual' : field.placeholder} value={values[field.key] ?? ''} onChange={(event) => setValues({ ...values, [field.key]: event.target.value })} />}</label>)}</div>
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
    singular: 'configuración LLM', createTitle: 'Crear configuración LLM', help: 'Seleccione proveedor y modelo. La clave se conserva sólo en el entorno. Para Ollama Docker use http://ollama:11434 y descargue el modelo antes de probar la conexión.',
    fields: [{ key: 'name', label: 'Nombre de configuración' }, { key: 'provider_kind', label: 'Proveedor', kind: 'select', options: [{ value: '', label: 'Seleccione un proveedor' }, { value: 'gemini', label: 'Gemini Cloud — usa GEMINI_API_KEY' }, { value: 'qwen-cloud', label: 'Qwen Cloud — usa DASHSCOPE_API_KEY' }, { value: 'ollama-local', label: 'Ollama local — red interna Docker' }] }, { key: 'base_url', label: 'URL del servicio', placeholder: 'Ollama Docker: http://ollama:11434' }, { key: 'model_id', label: 'Modelo', placeholder: 'Ejemplo local recomendado: qwen2.5:3b' }],
    empty: { name: '', provider_kind: '', base_url: '', model_id: '' }, read: (row) => ({ name: String(row.name), provider_kind: String(row.provider_kind), base_url: String(row.base_url), model_id: String(row.model_id) }),
    create: (v) => api.create('/llm-configurations', token, { ...v, is_active: false }),
    update: (row, v) => api.upsert(`/llm-configurations/${row.id}`, token, { ...v, is_active: active(row) === 'true' }),
  }
}
