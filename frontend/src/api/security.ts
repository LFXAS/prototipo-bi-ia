const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

export type Permission = { id: number; code: string; name: string; description?: string; is_active: boolean }
export type Role = { id: number; code: string; name: string; description?: string; is_active: boolean; is_system_protected?: boolean; permissions: Permission[] }
export type Menu = { id: number; code: string; label: string; path: string; position: number; module_code: string; module_label: string; is_active: boolean; is_system_protected?: boolean; permissions: Permission[] }
export type User = { id: number; email: string; full_name: string; is_active: boolean; is_system_protected?: boolean; roles: Role[] }
export type Session = { user: User; permissions: string[]; menus: Menu[] }
export type Parameter = { id: number; key: string; value: string; description?: string; is_active: boolean }
export type LlmConfiguration = { id: number; name: string; provider_kind: string; base_url: string; model_id: string; credential_reference: string; is_active: boolean; last_test_status?: string; last_test_message?: string }
export type AuditEvent = { id: number; action: string; resource_type: string; resource_id?: string; created_at: string }
export type Page<T> = { items: T[]; total: number; limit: number; offset: number }

type ValidationIssue = { loc?: (string | number)[]; msg?: string }
type ErrorBody = { detail?: string | ValidationIssue[] }

function readableError(detail: ErrorBody['detail']) {
  if (typeof detail === 'string') return detail
  if (!Array.isArray(detail)) return 'No fue posible completar la solicitud.'

  const labels: Record<string, string> = {
    email: 'Correo',
    full_name: 'Nombre completo',
    password: 'Contraseña',
    name: 'Nombre',
    provider_kind: 'Proveedor',
  }
  return detail.map((issue) => {
    const field = String(issue.loc?.at(-1) ?? '')
    if (field === 'email') return 'Correo: escriba una dirección válida, por ejemplo operador@empresa.com.'
    if (field === 'password') return 'Contraseña: debe contener al menos 12 caracteres.'
    return `${labels[field] ?? 'Dato'}: ${issue.msg ?? 'revise el valor ingresado.'}`
  }).join(' ')
}

async function request<T>(path: string, token?: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init?.headers },
  })
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ErrorBody
    throw new Error(readableError(body.detail))
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export const api = {
  login: (email: string, password: string) => request<{ access_token: string }>('/auth/login', undefined, { method: 'POST', body: JSON.stringify({ email, password }) }),
  session: (token: string) => request<Session>('/auth/me', token),
  users: (token: string, limit: number, offset: number) => request<Page<User>>(`/users?limit=${limit}&offset=${offset}`, token),
  roles: (token: string, limit: number, offset: number) => request<Page<Role>>(`/roles?limit=${limit}&offset=${offset}`, token),
  permissions: (token: string, limit: number, offset: number) => request<Page<Permission>>(`/permissions?limit=${limit}&offset=${offset}`, token),
  menus: (token: string, limit: number, offset: number) => request<Page<Menu>>(`/menus?limit=${limit}&offset=${offset}`, token),
  parameters: (token: string, limit: number, offset: number) => request<Page<Parameter>>(`/parameters?limit=${limit}&offset=${offset}`, token),
  llm: (token: string, limit: number, offset: number) => request<Page<LlmConfiguration>>(`/llm-configurations?limit=${limit}&offset=${offset}`, token),
  audit: (token: string, limit: number, offset: number) => request<Page<AuditEvent>>(`/audit-events?limit=${limit}&offset=${offset}`, token),
  testLlm: (token: string, id: number) => request<{ ok: boolean; message: string }>(`/llm-configurations/${id}/test`, token, { method: 'POST' }),
  create: <T>(path: string, token: string, body: object) => request<T>(path, token, { method: 'POST', body: JSON.stringify(body) }),
  update: <T>(path: string, token: string, body: object) => request<T>(path, token, { method: 'PATCH', body: JSON.stringify(body) }),
  upsert: <T>(path: string, token: string, body: object) => request<T>(path, token, { method: 'PUT', body: JSON.stringify(body) }),
  remove: (path: string, token: string) => request<void>(path, token, { method: 'DELETE' }),
}
