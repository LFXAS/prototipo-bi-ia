export const workspaceNavigationKey = 'bi_ia_workspace_navigation_v1'

export type WorkspaceLocation = { page: string; setupStep: number | null }
export type WorkspaceNavigation = WorkspaceLocation & { returnTo: WorkspaceLocation | null }

export const initialWorkspaceNavigation: WorkspaceNavigation = { page: '/', setupStep: null, returnTo: null }

function location(value: unknown, paths: string[]): WorkspaceLocation | null {
  if (!value || typeof value !== 'object') return null
  const candidate = value as Partial<WorkspaceLocation>
  if (typeof candidate.page !== 'string' || !paths.includes(candidate.page)) return null
  return {
    page: candidate.page,
    setupStep: Number.isInteger(candidate.setupStep) && Number(candidate.setupStep) >= 1 && Number(candidate.setupStep) <= 5 ? Number(candidate.setupStep) : null,
  }
}

export function workspaceNavigation(value: unknown, paths: string[]): WorkspaceNavigation {
  const current = location(value, paths)
  if (!current) return { ...initialWorkspaceNavigation }
  return { ...current, returnTo: location((value as Partial<WorkspaceNavigation>).returnTo, paths) }
}

export function readWorkspaceNavigation(paths: string[]): WorkspaceNavigation {
  try {
    return workspaceNavigation(JSON.parse(sessionStorage.getItem(workspaceNavigationKey) ?? 'null'), paths)
  } catch {
    return { ...initialWorkspaceNavigation }
  }
}

export function tokenExpirationTime(token: string): number | null {
  try {
    const encoded = token.split('.')[1]?.replace(/-/g, '+').replace(/_/g, '/')
    if (!encoded) return null
    const payload = JSON.parse(atob(encoded.padEnd(Math.ceil(encoded.length / 4) * 4, '='))) as { exp?: unknown }
    return typeof payload.exp === 'number' && Number.isFinite(payload.exp) ? payload.exp * 1000 : null
  } catch {
    return null
  }
}
