# Alcance técnico vigente

Fuente: anteproyecto corregido `A15_E25 (LVelásquez - ERobles) (ANTEPROYECTO).pdf`, 11 páginas, revisado el 24 de agosto de 2026.

## Incluido por el anteproyecto

- Una sola fuente activa de sólo lectura: SQL Server con AdventureWorks.
- Introspección de tablas, columnas, tipos, claves primarias, claves foráneas y relaciones declaradas.
- Metadatos estructurados enviados a un LLM para sugerir dominio, hecho, dimensiones, medidas, KPIs y plan ETL.
- Aprobación humana y validación determinística antes de ejecutar SQL o transformaciones.
- Datamart PostgreSQL con `fact_ventas`, `dim_fecha`, `dim_producto`, `dim_cliente` y `dim_territorio`.
- ETL de carga completa con uniones simples, fechas/tipos, nulos e importes.
- Cinco KPIs, tres visualizaciones, insights explicables y pronóstico mensual por regresión lineal con MAPE y RMSE.
- Datos sintéticos únicamente para pruebas controladas y valores faltantes.

## Excluido por el anteproyecto

- Conectores universales, fuentes simultáneas, alta disponibilidad y despliegue empresarial.
- CDC, cargas incrementales y dimensiones lentamente cambiantes complejas.
- Selección automática entre múltiples modelos predictivos.
- SQL del LLM ejecutado sin revisión humana.
- Datos productivos de terceros y operación continua posterior a la demostración.
- Multiusuario avanzado y permisos granulares dentro del dashboard.

## Aclaración sobre el módulo de seguridad

El anexo institucional exige evidencia de un módulo de seguridad, parámetros, negocio y reportes. Además, la decisión técnica del equipo exige RBAC con usuarios, roles, permisos y menús por rol. Esto no convierte el prototipo en una plataforma multiusuario avanzada: se implementará un RBAC mínimo, controlado y suficiente para la demostración académica.

En esta fase sólo existe su límite modular y la documentación del contrato. La implementación funcional se realizará en una migración y entrega posteriores.

## Objetivo de esta fase

- Repositorio y flujo Git preparados.
- Frontend y backend ejecutados íntegramente con Docker.
- Configuración reproducible y sin secretos versionados.
- PostgreSQL interno/datamart y SQL Server externo configurables.
- Endpoints de salud, OpenAPI y pantalla técnica inicial.
- CI/CD preparado en GitHub Actions.
- Ningún módulo de negocio implementado todavía.
