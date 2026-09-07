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

function readLabel(item: Row) {
  return String(item.full_name ?? item.name ?? item.label ?? item.key ?? item.action ?? item.code ?? '')
}

function parseIdentifiers(value: string) {
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
    return group.items.some((menu) => menu.path === page) || expandedGroups[group.code] === true
  }

  function toggleGroup(group: { code: string; items: Menu[] }) {
    setExpandedGroups((current) => ({ ...current, [group.code]: !current[group.code] }))
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
      <div className="workspace">
        <aside className={`navigation-panel ${menuOpen ? 'open' : ''}`}><nav id="main-navigation" aria-label="Navegación principal">
          {Object.values(groupMenus(session.menus)).map((group) => <div className="navigation-group" key={group.code}><button className="module-toggle" aria-expanded={isGroupExpanded(group)} aria-controls={`menu-group-${group.code}`} onClick={() => toggleGroup(group)}><span>{group.label}</span><span aria-hidden="true">{isGroupExpanded(group) ? '⌄' : '›'}</span></button><div className="submenu" id={`menu-group-${group.code}`} hidden={!isGroupExpanded(group)}>{group.items.map((menu) => <button className={page === menu.path ? 'active' : ''} onClick={() => { setPage(menu.path); setOffset(0); setMenuOpen(false) }} key={menu.id}>{menu.label}</button>)}</div></div>)}
        </nav></aside>
        <section className="content">
          <h1>{labels[page]}</h1>
          {page === '/'
            ? <Home session={session} />
            : <ResourcePage page={page} data={data} message={message} token={token} canWrite={session.permissions.includes(writePermissions[page])} onSaved={() => { setOffset(0); setRevision((value) => value + 1) }} onChangePage={setOffset} />}
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
  const [actionError, setActionError] = useState('')
  const rows = (data?.items ?? []) as unknown as Row[]

  async function toggleActive(row: Row) {
    const isActive = row.is_active === true
    setActionError('')
    try {
      if (page === '/usuarios') await api.update(`/users/${row.id}`, token, { is_active: !isActive })
      else if (page === '/roles') await api.update(`/roles/${row.id}`, token, { is_active: !isActive })
      else if (page === '/permisos') await api.update(`/permissions/${row.id}`, token, { is_active: !isActive })
      else if (page === '/menus') await api.update(`/menus/${row.id}`, token, { is_active: !isActive })
      else if (page === '/parametros') await api.upsert(`/parameters/${row.key}`, token, { key: row.key, value: row.value, description: row.description ?? null, is_active: !isActive })
      else if (page === '/llm') await api.upsert(`/llm-configurations/${row.id}`, token, { name: row.name, provider_kind: row.provider_kind, base_url: row.base_url, model_id: row.model_id, is_active: !isActive })
      onSaved()
    } catch (caught) {
      setActionError(caught instanceof Error ? caught.message : 'No fue posible cambiar el estado.')
    }
  }

  if (message) return <p className="notice error">{message}</p>
  if (!data) return <p className="notice">Cargando información…</p>

  return <>
    {canWrite && page !== '/auditoria' && <CrudForm page={page} token={token} selected={selected} onSaved={() => { setSelected(null); onSaved() }} />}
    {actionError && <p className="notice error">{actionError}</p>}
    <div className="table-wrap">
      <table>
        <thead><tr><th>Elemento</th><th>Detalle</th><th>Estado</th>{canWrite && page !== '/auditoria' && <th>Acciones</th>}</tr></thead>
        <tbody>{rows.map((row) => <tr key={String(row.id)}><td>{readLabel(row)}</td><td>{String(row.email ?? row.code ?? row.provider_kind ?? row.resource_type ?? '—')}</td><td>{String(row.is_active ?? row.last_test_status ?? 'Registrado')}</td>{canWrite && page !== '/auditoria' && <td><div className="row-actions"><button className="table-action" onClick={() => setSelected(row)}>Editar</button><button className="table-action secondary" onClick={() => toggleActive(row)}>{row.is_active === true ? 'Desactivar' : 'Activar'}</button></div></td>}</tr>)}</tbody>
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
  const config = useMemo(() => formConfig(page, token), [page, token])
  const [values, setValues] = useState<Values>(config.empty)
  const [error, setError] = useState('')

  useEffect(() => {
    setValues(selected ? config.read(selected) : config.empty)
    setError('')
  }, [config, selected])
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
    <div className="form-grid">{config.fields.map((field) => <label key={field.key}>{field.label}<input required={field.required ?? true} type={field.secret ? 'password' : 'text'} placeholder={field.placeholder} value={values[field.key] ?? ''} onChange={(event) => setValues({ ...values, [field.key]: event.target.value })} /></label>)}</div>
    <div className="form-actions"><button>{selected ? 'Guardar cambios' : 'Crear registro'}</button>{selected && <button type="button" className="secondary" onClick={onSaved}>Cancelar</button>}</div>
    {error && <p className="notice error">{error}</p>}
  </form>
}

type Field = { key: string; label: string; placeholder?: string; secret?: boolean; required?: boolean }
type FormConfig = { singular: string; createTitle: string; help: string; fields: Field[]; empty: Values; read: (row: Row) => Values; create: (values: Values) => Promise<unknown>; update: (row: Row, values: Values) => Promise<unknown> }

function formConfig(page: string, token: string): FormConfig {
  const active = (row: Row) => String(row.is_active ?? true)
  if (page === '/usuarios') return {
    singular: 'usuario', createTitle: 'Crear usuario', help: 'Ingrese roles como identificadores separados por comas (ejemplo: 1,2).',
    fields: [{ key: 'email', label: 'Correo' }, { key: 'full_name', label: 'Nombre completo' }, { key: 'password', label: 'Contraseña', secret: true }, { key: 'role_ids', label: 'Identificadores de roles', required: false }],
    empty: { email: '', full_name: '', password: '', role_ids: '' }, read: (row) => ({ email: String(row.email), full_name: String(row.full_name), password: '', role_ids: ((row.roles as Row[] | undefined) ?? []).map((role) => role.id).join(',') }),
    create: (v) => api.create('/users', token, { email: v.email, full_name: v.full_name, password: v.password, role_ids: parseIdentifiers(v.role_ids) }),
    update: (row, v) => api.update(`/users/${row.id}`, token, { full_name: v.full_name, ...(v.password ? { password: v.password } : {}), role_ids: parseIdentifiers(v.role_ids) }),
  }
  if (page === '/roles') return {
    singular: 'rol', createTitle: 'Crear rol', help: 'Asocie permisos mediante identificadores separados por comas.',
    fields: [{ key: 'code', label: 'Código' }, { key: 'name', label: 'Nombre' }, { key: 'description', label: 'Descripción', required: false }, { key: 'permission_ids', label: 'Identificadores de permisos', required: false }],
    empty: { code: '', name: '', description: '', permission_ids: '' }, read: (row) => ({ code: String(row.code), name: String(row.name), description: String(row.description ?? ''), permission_ids: ((row.permissions as Row[] | undefined) ?? []).map((permission) => permission.id).join(',') }),
    create: (v) => api.create('/roles', token, { code: v.code, name: v.name, description: v.description || null, permission_ids: parseIdentifiers(v.permission_ids) }),
    update: async (row, v) => { await api.update(`/roles/${row.id}`, token, { name: v.name, description: v.description || null }); return api.update(`/roles/${row.id}/permissions`, token, { permission_ids: parseIdentifiers(v.permission_ids) }) },
  }
  if (page === '/permisos') return {
    singular: 'permiso', createTitle: 'Crear permiso', help: 'Los permisos se asignan después a roles o menús.',
    fields: [{ key: 'code', label: 'Código' }, { key: 'name', label: 'Nombre' }, { key: 'description', label: 'Descripción', required: false }],
    empty: { code: '', name: '', description: '' }, read: (row) => ({ code: String(row.code), name: String(row.name), description: String(row.description ?? '') }),
    create: (v) => api.create('/permissions', token, { code: v.code, name: v.name, description: v.description || null }),
    update: (row, v) => api.update(`/permissions/${row.id}`, token, { name: v.name, description: v.description || null }),
  }
  if (page === '/menus') return {
    singular: 'menú', createTitle: 'Crear menú', help: 'Use una ruta existente y asocie permisos con identificadores separados por comas.',
    fields: [{ key: 'code', label: 'Código' }, { key: 'label', label: 'Etiqueta' }, { key: 'path', label: 'Ruta', placeholder: '/mi-modulo' }, { key: 'position', label: 'Posición' }, { key: 'module_code', label: 'Código de módulo', placeholder: 'seguridad' }, { key: 'module_label', label: 'Nombre del módulo', placeholder: 'Seguridad' }, { key: 'permission_ids', label: 'Identificadores de permisos', required: false }],
    empty: { code: '', label: '', path: '', position: '99', module_code: 'general', module_label: 'General', permission_ids: '' }, read: (row) => ({ code: String(row.code), label: String(row.label), path: String(row.path), position: String(row.position), module_code: String(row.module_code), module_label: String(row.module_label), permission_ids: ((row.permissions as Row[] | undefined) ?? []).map((permission) => permission.id).join(',') }),
    create: (v) => api.create('/menus', token, { code: v.code, label: v.label, path: v.path, position: Number(v.position), module_code: v.module_code, module_label: v.module_label, permission_ids: parseIdentifiers(v.permission_ids) }),
    update: (row, v) => api.update(`/menus/${row.id}`, token, { label: v.label, path: v.path, position: Number(v.position), module_code: v.module_code, module_label: v.module_label, permission_ids: parseIdentifiers(v.permission_ids) }),
  }
  if (page === '/parametros') return {
    singular: 'parámetro', createTitle: 'Guardar parámetro', help: 'Las claves son únicas y no deben incluir contraseñas ni secretos.',
    fields: [{ key: 'key', label: 'Clave' }, { key: 'value', label: 'Valor' }, { key: 'description', label: 'Descripción', required: false }],
    empty: { key: '', value: '', description: '' }, read: (row) => ({ key: String(row.key), value: String(row.value), description: String(row.description ?? '') }),
    create: (v) => api.upsert(`/parameters/${v.key}`, token, { key: v.key, value: v.value, description: v.description || null, is_active: true }),
    update: (row, v) => api.upsert(`/parameters/${row.key}`, token, { key: row.key, value: v.value, description: v.description || null, is_active: active(row) === 'true' }),
  }
  return {
    singular: 'configuración LLM', createTitle: 'Crear configuración LLM', help: 'Use gemini, qwen-cloud u ollama-local. La referencia de credencial pertenece al entorno.',
    fields: [{ key: 'name', label: 'Nombre' }, { key: 'provider_kind', label: 'Proveedor', placeholder: 'gemini, qwen-cloud u ollama-local' }, { key: 'base_url', label: 'URL base' }, { key: 'model_id', label: 'Modelo' }, { key: 'credential_reference', label: 'Referencia de credencial', required: false }],
    empty: { name: '', provider_kind: '', base_url: '', model_id: '', credential_reference: '' }, read: (row) => ({ name: String(row.name), provider_kind: String(row.provider_kind), base_url: String(row.base_url), model_id: String(row.model_id), credential_reference: String(row.credential_reference ?? '') }),
    create: (v) => api.create('/llm-configurations', token, { ...v, credential_reference: v.credential_reference || null, is_active: false }),
    update: (row, v) => api.upsert(`/llm-configurations/${row.id}`, token, { ...v, credential_reference: v.credential_reference || null, is_active: active(row) === 'true' }),
  }
}
