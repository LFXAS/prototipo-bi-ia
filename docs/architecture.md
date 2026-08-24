# Arquitectura base

```text
Navegador
   |
   v
React + Vite / Nginx
   |
   v
FastAPI ---------------> SQL Server / AdventureWorks
   |                     fuente externa, usuario read-only
   v
PostgreSQL
configuración interna, RBAC, auditoría y datamart
```

## Contenedores

- `frontend`: Vite con recarga en desarrollo; Nginx en la imagen de producción.
- `backend`: FastAPI con recarga en desarrollo; Uvicorn sin recarga y usuario no privilegiado en producción.
- `postgres`: instancia aislada del proyecto, con esquemas `app` y `mart` inicializados en un volumen nombrado.
- `sqlserver`: instancia aislada del proyecto; descarga y restaura AdventureWorks de forma idempotente en un volumen nombrado.

## Límites modulares previstos

- `system`: salud y diagnóstico técnico mínimo.
- `security`: autenticación y RBAC mínimo.
- `parameters`: parámetros del prototipo y conexiones aprobadas.
- `metadata`: introspección determinística de AdventureWorks.
- `copilot`: propuestas estructuradas del LLM, nunca ejecución directa.
- `etl`: vista previa, validación, ejecución y trazabilidad de cargas.
- `analytics`: KPIs, gráficos e insights.
- `forecasting`: regresión lineal y métricas MAPE/RMSE.
- `reports`: evidencias y reportes académicos.

Sólo `system` contiene comportamiento en esta entrega.

## RBAC previsto

Entidades mínimas: `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `menus`, `menu_permissions` y `audit_events`.

Reglas arquitectónicas:

1. React puede ocultar opciones, pero FastAPI autoriza cada operación.
2. Denegar por defecto cuando un permiso no esté asignado.
3. Los tokens no almacenan secretos ni reemplazan el estado activo del usuario.
4. Las aprobaciones de propuestas/SQL quedan auditadas.
5. Menús y permisos comparten códigos estables, no nombres visibles.

## Datos

PostgreSQL alojará dos responsabilidades lógicamente separadas:

- esquema `app`: seguridad, parámetros, auditoría y ejecuciones;
- esquema `mart`: hechos y dimensiones analíticas.

La separación física en bases distintas no es necesaria para la prueba de concepto y puede revisarse si las mediciones lo justifican.
