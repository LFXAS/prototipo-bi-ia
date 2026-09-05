# Especificaciones del producto

Este directorio conserva las especificaciones funcionales del prototipo. Cada archivo describe una capacidad antes de implementarla y se versiona junto con el código que la satisface.

## Convención de nombres

Usar `SPR-XX-nombre-corto.md`, donde `XX` es el sprint. Ejemplo: `SPR-02-rbac-y-parametros.md`.

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
| [SPR-02-rbac-y-parametros.md](SPR-02-rbac-y-parametros.md) | borrador | Base de seguridad RBAC, parámetros de conexión y experiencia responsive aprobada. |
