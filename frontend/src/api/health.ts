export type HealthStatus = {
  status: 'ok' | 'not_ready'
  service: string
  version: string
  postgres: 'not_checked' | 'ok' | 'unavailable'
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

export async function getLiveHealth(signal?: AbortSignal): Promise<HealthStatus> {
  const response = await fetch(`${apiBaseUrl}/api/v1/health/live`, { signal })

  if (!response.ok) {
    throw new Error(`La API respondió con estado ${response.status}`)
  }

  return (await response.json()) as HealthStatus
}
