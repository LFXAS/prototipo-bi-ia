# Plan mínimo de endurecimiento del asistente BI

Este plan traduce el diagnóstico del 25 de septiembre de 2026 en cambios pequeños, verificables y separados por commits. No autoriza SQL libre ni elimina controles de seguridad.

## Fase 1 — Proveedor Groq y observabilidad

| Archivo | Cambio mínimo |
|---|---|
| `backend/app/modules/parameters/providers.py` | Centralizar payload/capacidades, usar `include_reasoning`, presupuestos por nivel, clasificación precisa, metadatos sanitizados y retry sólo transitorio. |
| `backend/tests/test_parameters_providers.py` | Cubrir low/medium/high, 400 de parámetro, `json_validate_failed`, 401/403/404/429, timeout, 5xx, Structured Outputs y política de intentos. |
| `backend/app/modules/parameters/schemas.py` | Validar combinaciones conocidas de proveedor, modelo y razonamiento sin bloquear proveedores existentes. |
| `frontend/src/App.tsx` | Mostrar compatibilidad y mensajes accionables sin exponer detalles sensibles. |

## Fase 2 — Necesidad y viabilidad previa

| Archivo | Cambio mínimo |
|---|---|
| `backend/app/modules/copilot/schemas.py` | Elevar límite y definir contratos de reformulación, aprobación y cobertura. |
| `backend/app/modules/copilot/service.py` | Clasificar cada requisito como directo, derivable, ambiguo o no disponible usando sólo metadatos verificados. |
| `backend/app/modules/copilot/router.py` | Exponer reformulación y viabilidad como pasos separados del proveedor LLM. |
| `frontend/src/App.tsx` | Textarea amplio, contador, comparación original/propuesta, aprobación explícita y matriz de viabilidad. |
| pruebas backend/frontend | Necesidades completas, parciales, inviables y error de proveedor independiente. |

## Fase 3 — Cobertura, fuentes y relaciones controladas

| Archivo | Cambio mínimo |
|---|---|
| `backend/app/modules/copilot/service.py` | Matriz necesidad→concepto→medida/dimensión/KPI; fuentes físicas, fórmulas, granularidad y transacciones distintas. |
| `backend/app/modules/copilot/schemas.py` | Contratos para evidencia y edición de relaciones con objetos reales. |
| `backend/app/modules/copilot/router.py` | Catálogos controlados de tablas/columnas y revalidación versionada después de cada cambio. |
| `frontend/src/App.tsx` | Selectores guiados, ruta de join, cardinalidad, riesgo de duplicación y estado de revalidación. |
| pruebas | Relación válida/inválida, cambio de granularidad y ausencia de requisitos. |

## Fase 4 — Costos, margen y materialización

| Archivo | Cambio mínimo |
|---|---|
| `backend/app/modules/copilot/service.py` | Definir costo, margen, ratios por unidad y descuento monetario sólo si sus fuentes están verificadas. |
| `backend/app/modules/etl/materializer.py` | Materializar fórmulas aprobadas sin sumar porcentajes por fila. |
| `backend/app/modules/analytics/service.py` | Publicar KPIs cubiertos y declarar los no calculables. |
| pruebas ETL/analítica | Conciliación de costo total, margen bruto, margen %, ventas/unidades y descuento. |

## Fase 5 — Copiloto analítico seguro

| Archivo | Cambio mínimo |
|---|---|
| `backend/app/modules/analytics/service.py` | Motor de agregaciones permitidas por dimensión, métrica, filtro, orden y Top N. |
| `backend/app/modules/analytics/router.py` | Interpretar intención y solicitar al motor datos agregados, sin SQL libre. |
| `backend/app/modules/analytics/schemas.py` | Procedencia, denominador, universo, filtros y versión de datamart. |
| `frontend/src/AnalyticsPage.tsx` | Evidencia visible, preguntas guiadas y contraste accesible. |
| pruebas | Top 5 productos en Europa sin filtro visual previo y porcentajes reconstruibles. |

## Fase 6 — Sesión, UX y regresión

| Archivo | Cambio mínimo |
|---|---|
| `frontend/src/api/security.ts` | Distinguir expiración, recuperar sesión y reintentar sólo operaciones seguras. |
| `frontend/src/App.tsx` | Persistir borradores/versiones del wizard y restaurar el paso vigente. |
| `frontend/src/styles.css`, `frontend/src/analytics.css` | Contraste, foco, mensajes de recuperación y estados no ambiguos. |
| pruebas E2E | Expiración durante Personalización, recuperación sin pérdida y flujo integral. |

## Puertas de calidad por commit

1. pruebas unitarias del módulo modificado;
2. lint, formato y tipado;
3. build frontend cuando exista cambio visual;
4. `make verify` antes de publicar cada fase;
5. diff revisado sin `.env`, secretos ni reportes locales;
6. commit temático y publicación en `feature/bi-assistant-hardening`.
