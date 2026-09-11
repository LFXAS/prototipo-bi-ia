import type { Role } from './api/security'

export type RoleChoice = { value: string; label: string; detail?: string }

export function roleChoicesForUserAssignment(
  roles: Role[],
  assignedRoleIds: Iterable<number | string> = [],
): RoleChoice[] {
  const assignedIds = new Set(Array.from(assignedRoleIds, String))

  return roles
    .filter((role) => role.is_active || assignedIds.has(String(role.id)))
    .map((role) => ({
      value: String(role.id),
      label: role.is_active ? role.name : `${role.name} (inactivo)`,
      detail: role.is_active
        ? role.description
        : `${role.description ?? 'Sin descripción.'} Rol inactivo: puede retirarse, pero no asignarse.`,
    }))
}
