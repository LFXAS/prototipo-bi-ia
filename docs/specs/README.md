# Especificaciones del producto

Este directorio conserva las especificaciones funcionales del prototipo. Cada archivo describe una capacidad antes de implementarla y se versiona junto con el código que la satisface.

## Convención de nombres

Usar `SPR-XX-nombre-corto.md`, donde `XX` es el sprint. Cuando un sprint tenga capacidades independientes, usar además un sufijo numérico (`SPR-02-01-seguridad-rbac.md`) y mantener un archivo índice del sprint.

## Uso rápido

1. Copiar `TEMPLATE.md`.
2. Completar todos los apartados aplicables y marcar el estado `borrador`.
3. Acordar los criterios de aceptación antes de abrir el PR de código.
4. Definir también el flujo UI/UX, la adaptación responsive, los estados y la accesibilidad de la capacidad; no se acepta dejar la interfaz como un detalle posterior.
5. Enlazar el archivo desde el PR y actualizar el estado durante el ciclo.
6. Conservar el documento después de la entrega; no se sustituye por el README ni por la bitácora.

Consulta [`../sdd-workflow.md`](../sdd-workflow.md) para el proceso completo.

## Índice inicial

| Especificación | Estado | Propósito |
|---|---|---|
| [SPR-02-rbac-y-parametros.md](SPR-02-rbac-y-parametros.md) | revisión correctiva | Índice y alcance integrado del módulo administrativo del Sprint 2. |
| [SPR-02-01-seguridad-rbac.md](SPR-02-01-seguridad-rbac.md) | revisión correctiva | Usuarios, roles, permisos, menús, auditoría y protecciones de recuperación. |
| [SPR-02-02-navegacion-y-experiencia.md](SPR-02-02-navegacion-y-experiencia.md) | revisión correctiva | Sidebar, plegado de grupos, responsive, paginación y aislamiento de estado. |
| [SPR-02-03-parametros-y-llm.md](SPR-02-03-parametros-y-llm.md) | revisión correctiva | Parámetros aprobados y configuración/probación segura de LLM. |
| [SPR-02-04-identidad-visual-y-shell-bi.md](SPR-02-04-identidad-visual-y-shell-bi.md) | borrador para aprobación | Dirección visual y cascarón común del prototipo BI asistido por IA. |
| [SPR-02-matriz-correcciones.md](SPR-02-matriz-correcciones.md) | pendiente de evidencia | Trazabilidad entre observaciones funcionales, requisito y prueba. |
| [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md) | borrador para aprobación | Índice de configuración web, introspección e interpretación BI supervisada. |
| [SPR-03-01-conexion-e-introspeccion-adventureworks.md](SPR-03-01-conexion-e-introspeccion-adventureworks.md) | borrador para aprobación | Adaptador SQL Server, sólo lectura e instantáneas canónicas; AdventureWorks como validación. |
| [SPR-03-02-propuesta-bi-asistida-por-ia.md](SPR-03-02-propuesta-bi-asistida-por-ia.md) | borrador para aprobación | Solicitud guiada, interpretación dinámica, contrato LLM, validación, versiones y aprobación. |
| [SPR-03-03-explorador-esquema-y-trazabilidad.md](SPR-03-03-explorador-esquema-y-trazabilidad.md) | borrador para aprobación | Conexiones, asistente para negocio, explorador avanzado, revisión y experiencia responsive. |
| [SPR-03-04-configuracion-web-conexiones-y-secretos.md](SPR-03-04-configuracion-web-conexiones-y-secretos.md) | borrador para aprobación | CRUD web de conexiones, parámetros y secretos cifrados con interfaz extensible de conectores. |
