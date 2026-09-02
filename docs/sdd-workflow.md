# Desarrollo guiado por especificaciones (SDD)

## Propósito

SDD significa que el equipo acuerda y versiona **qué se construirá** antes de programarlo. No es una herramienta adicional ni reemplaza Docker, GitHub Actions o las pruebas. Es un contrato sencillo para que una funcionalidad de BI, IA, seguridad o datos tenga un alcance claro y una forma objetiva de comprobarse.

Esta regla comienza en el Sprint 2. No reescribe retrospectivamente el Sprint 1, cuyo objetivo fue dejar una plataforma técnica reproducible.

## Regla obligatoria

Toda capacidad funcional nueva debe tener una especificación Markdown en `docs/specs/` antes de que se abra el pull request de implementación. La excepción son cambios puramente editoriales, de formato o de mantenimiento sin efecto funcional; estos deben explicar su motivación en el PR.

La especificación es la fuente de verdad para alcance y aceptación. Si el código y la especificación discrepan, el PR no se fusiona hasta resolver la diferencia.

## Ciclo paso a paso

1. Copiar `docs/specs/TEMPLATE.md` a `docs/specs/SPR-XX-nombre-corto.md`.
2. Completar problema, objetivo, alcance, exclusiones, reglas, datos, seguridad, criterios de aceptación y pruebas.
3. Revisar el documento con las autoras. Si altera una decisión permanente, añadir además un ADR en `docs/decisions/`.
4. Crear la rama desde `develop`, por ejemplo `feature/rbac-inicial`.
5. Implementar código y pruebas sólo dentro del alcance aprobado; enlazar la especificación en la descripción del PR.
6. Actualizar arquitectura, README, guía de réplica, manual técnico y bitácora cuando el cambio los afecte.
7. Ejecutar `make verify`; CI repetirá sus controles al abrir el PR.
8. Tras aprobación y CI verde, fusionar hacia `develop`. Registrar el resultado en la bitácora.
9. Cuando el conjunto integrado esté listo, promover `develop` hacia `main`; CD publicará las imágenes de la entrega.

## Estructura y estados

Los archivos se conservan en Git junto con el código:

- `docs/specs/README.md`: índice y convenciones.
- `docs/specs/TEMPLATE.md`: plantilla obligatoria.
- `docs/specs/SPR-02-rbac-y-parametros.md`: primera especificación preparada para el siguiente sprint.

El encabezado de cada especificación debe indicar uno de estos estados: `borrador`, `aprobada`, `en implementación`, `verificada`, `entregada` o `cancelada`. No se borra una especificación cancelada; se conserva con una explicación para mantener la trazabilidad.

## Relación con IA y datos

Las propuestas del LLM no pueden modificar bases ni ejecutar SQL de forma directa. Una especificación debe declarar quién aprueba una propuesta, qué validaciones determinísticas se aplican, qué datos pueden usarse y qué evidencia queda en auditoría. Para modificaciones de PostgreSQL se deben definir migraciones; nunca se transportan volúmenes Docker como si fueran una versión del sistema.

## Definition of Done documental

Un cambio queda listo para solicitar revisión cuando: la especificación está actualizada, las pruebas correspondientes pasan en Docker, los documentos afectados están actualizados, los PDF cambiados se regeneraron con `make docs`, no hay secretos en el cambio y el PR enlaza evidencia verificable.
