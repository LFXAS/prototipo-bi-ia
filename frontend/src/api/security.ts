const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

export type Permission = { id: number; code: string; name: string; description?: string; is_active: boolean }
export type Role = { id: number; code: string; name: string; description?: string; is_active: boolean; permissions: Permission[] }
export type Menu = { id: number; code: string; label: string; path: string; position: number; is_active: boolean; permissions: Permission[] }
export type User = { id: number; email: string; full_name: string; is_active: boolean; roles: Role[] }
export type Session = { user: User; permissions: string[]; menus: Menu[] }
export type Parameter = { id: number; key: string; value: string; description?: string; is_active: boolean }
export type LlmConfiguration = { id: number; name: string; provider_kind: string; base_url: string; model_id: string; credential_reference: string; is_active: boolean; last_test_status?: string; last_test_message?: string }
export type AuditEvent = { id: number; action: string; resource_type: string; resource_id?: string; created_at: string }

async function request<T>(path: string, token?: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init?.headers },
  })
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail ?? 'No fue posible completar la solicitud.')
  }
  return (await response.json()) as T
}

export const api = {
  login: (email: string, password: string) => request<{ access_token: string }>('/auth/login', undefined, { method: 'POST', body: JSON.stringify({ email, password }) }),
  session: (token: string) => request<Session>('/auth/me', token),
  users: (token: string) => request<User[]>('/users', token),
  roles: (token: string) => request<Role[]>('/roles', token),
  permissions: (token: string) => request<Permission[]>('/permissions', token),
  menus: (token: string) => request<Menu[]>('/menus', token),
  parameters: (token: string) => request<Parameter[]>('/parameters', token),
  llm: (token: string) => request<LlmConfiguration[]>('/llm-configurations', token),
  audit: (token: string) => request<AuditEvent[]>('/audit-events', token),
  create: <T>(path: string, token: string, body: object) => request<T>(path, token, { method: 'POST', body: JSON.stringify(body) }),
  update: <T>(path: string, token: string, body: object) => request<T>(path, token, { method: 'PATCH', body: JSON.stringify(body) }),
  upsert: <T>(path: string, token: string, body: object) => request<T>(path, token, { method: 'PUT', body: JSON.stringify(body) }),
}
