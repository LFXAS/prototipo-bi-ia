import { useEffect, useState } from 'react'

import { getLiveHealth, type HealthStatus } from './api/health'

type ApiState =
  | { kind: 'loading' }
  | { kind: 'online'; health: HealthStatus }
  | { kind: 'offline' }

const plannedModules = [
  'Seguridad RBAC',
  'Parámetros',
  'Metadatos',
  'Copiloto IA',
  'ETL y datamart',
  'KPIs e insights',
  'Pronóstico',
  'Reportes',
]

export default function App() {
  const [apiState, setApiState] = useState<ApiState>({ kind: 'loading' })

  useEffect(() => {
    const controller = new AbortController()

    getLiveHealth(controller.signal)
      .then((health) => setApiState({ kind: 'online', health }))
      .catch(() => setApiState({ kind: 'offline' }))

    return () => controller.abort()
  }, [])

  const statusLabel =
    apiState.kind === 'loading'
      ? 'Comprobando API'
      : apiState.kind === 'online'
        ? `API disponible · v${apiState.health.version}`
        : 'API no disponible'

  return (
    <main>
      <section className="hero">
        <p className="eyebrow">Universidad de Guayaquil · Proyecto de titulación</p>
        <h1>BI asistido por IA</h1>
        <p className="lead">
          Entorno base para construir un datamart, KPIs, insights y un pronóstico con
          AdventureWorks.
        </p>
        <div className={`status status--${apiState.kind}`} role="status">
          <span aria-hidden="true" />
          {statusLabel}
        </div>
      </section>

      <section className="panel" aria-labelledby="phase-title">
        <div>
          <p className="phase">Fase 01</p>
          <h2 id="phase-title">Ambiente y arquitectura</h2>
          <p>
            React, FastAPI y controladores de datos ejecutándose en Docker. Los módulos de negocio
            permanecen deliberadamente sin implementar.
          </p>
        </div>
        <ol className="checks">
          <li>Frontend React + TypeScript</li>
          <li>API FastAPI y OpenAPI</li>
          <li>PostgreSQL interno/datamart</li>
          <li>SQL Server de solo lectura preparado</li>
          <li>Pruebas e imágenes CI/CD</li>
        </ol>
      </section>

      <section aria-labelledby="modules-title">
        <p className="phase">Arquitectura prevista</p>
        <h2 id="modules-title">Módulos del prototipo</h2>
        <div className="modules">
          {plannedModules.map((module) => (
            <article key={module}>
              <span>Próximamente</span>
              <h3>{module}</h3>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}
