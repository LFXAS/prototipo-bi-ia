import { FormEvent, useEffect, useState } from 'react'

import { api, type AuditEvent, type LlmConfiguration, type Menu, type Parameter, type Permission, type Role, type Session, type User } from './api/security'

type PageData = User[] | Role[] | Permission[] | Menu[] | Parameter[] | LlmConfiguration[] | AuditEvent[] | null
const tokenKey = 'bi_ia_access_token'
const labels: Record<string, string> = { '/': 'Inicio', '/usuarios': 'Usuarios', '/roles': 'Roles', '/permisos': 'Permisos', '/menus': 'Menús', '/parametros': 'Parámetros', '/llm': 'Configuración LLM', '/auditoria': 'Auditoría' }

function readLabel(item: Record<string, unknown>) { return String(item.full_name ?? item.name ?? item.label ?? item.key ?? item.action ?? item.code ?? '') }

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem(tokenKey) ?? '')
  const [session, setSession] = useState<Session | null>(null)
  const [page, setPage] = useState('/')
  const [data, setData] = useState<PageData>(null)
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('admin@bi.local')
  const [password, setPassword] = useState('')

  useEffect(() => { if (token) api.session(token).then(setSession).catch(() => { localStorage.removeItem(tokenKey); setToken(''); setMessage('La sesión terminó. Inicie sesión nuevamente.') }) }, [token])
  useEffect(() => {
    if (!token || !session) return
    const loads: Record<string, () => Promise<PageData>> = { '/usuarios': () => api.users(token), '/roles': () => api.roles(token), '/permisos': () => api.permissions(token), '/menus': () => api.menus(token), '/parametros': () => api.parameters(token), '/llm': () => api.llm(token), '/auditoria': () => api.audit(token) }
    setData(null); loads[page]?.().then(setData).catch((error: Error) => setMessage(error.message))
  }, [page, token, session])

  async function submitLogin(event: FormEvent) { event.preventDefault(); setMessage(''); try { const result = await api.login(email, password); localStorage.setItem(tokenKey, result.access_token); setToken(result.access_token) } catch (error) { setMessage(error instanceof Error ? error.message : 'No fue posible iniciar sesión.') } }
  function logout() { localStorage.removeItem(tokenKey); setToken(''); setSession(null); setData(null); setPage('/') }
  if (!session) return <main className="login-page"><section className="login-card"><p className="eyebrow">Prototipo académico</p><h1>BI asistido por IA</h1><p>Ingrese con una cuenta autorizada. La interfaz y la API validan los permisos reales.</p><form onSubmit={submitLogin}><label>Correo<input value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoComplete="email" required /></label><label>Contraseña<input value={password} onChange={(e) => setPassword(e.target.value)} type="password" autoComplete="current-password" required /></label><button>Iniciar sesión</button></form>{message && <p className="notice error">{message}</p>}<small>La clave inicial se define únicamente en el archivo de entorno local.</small></section></main>
  return <main className="app-shell"><header><div><p className="eyebrow">BI asistido por IA</p><strong>{session.user.full_name}</strong></div><button className="secondary" onClick={logout}>Cerrar sesión</button></header><div className="workspace"><nav aria-label="Navegación principal">{session.menus.map((menu) => <button className={page === menu.path ? 'active' : ''} onClick={() => setPage(menu.path)} key={menu.id}>{menu.label}</button>)}</nav><section className="content"><h1>{labels[page]}</h1>{page === '/' ? <Home session={session} /> : <List page={page} data={data} message={message} />}</section></div></main>
}

function Home({ session }: { session: Session }) { return <><p className="lead">Bienvenido. Desde aquí se administra el acceso, la parametrización y la trazabilidad técnica del prototipo.</p><div className="cards"><article><strong>{session.user.roles.length}</strong><span>roles asignados</span></article><article><strong>{session.permissions.length}</strong><span>permisos efectivos</span></article><article><strong>{session.menus.length}</strong><span>opciones visibles</span></article></div><p className="notice">Los módulos BI, ETL, reportes y predicción continúan fuera del alcance de este sprint.</p></> }
function List({ page, data, message }: { page: string; data: PageData; message: string }) { if (message) return <p className="notice error">{message}</p>; if (!data) return <p className="notice">Cargando información…</p>; return <div className="table-wrap"><table><thead><tr><th>Elemento</th><th>Detalle</th><th>Estado</th></tr></thead><tbody>{data.map((item) => { const row = item as Record<string, unknown>; return <tr key={String(row.id)}><td>{readLabel(row)}</td><td>{String(row.email ?? row.code ?? row.provider_kind ?? row.resource_type ?? '—')}</td><td>{String(row.is_active ?? row.last_test_status ?? 'Registrado')}</td></tr> })}</tbody></table>{page === '/llm' && <p className="notice">Las credenciales se leen por referencia desde el entorno y nunca se almacenan aquí.</p>}</div> }
