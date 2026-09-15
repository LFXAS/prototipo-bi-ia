# Alcance técnico vigente

Fuente: anteproyecto corregido `A15_E25 (LVelásquez - ERobles) (ANTEPROYECTO).pdf`, 11 páginas, revisado el 24 de agosto de 2026.

## Identificación vigente de la investigación

Título acordado el 14 de septiembre de 2026:

> **Prototipo web de inteligencia de negocios asistido por IA para la construcción semiautomatizada y supervisada de un datamart de ventas con datos públicos y sintéticos.**

La fuente pública funcional es AdventureWorks. Los datos sintéticos se utilizan únicamente para pruebas controladas y valores faltantes; no representan una segunda fuente que el prototipo deba conectar o validar.

### Objetivo general

Desarrollar un prototipo web de inteligencia de negocios asistido por IA que permita la construcción semiautomatizada y supervisada de un datamart de ventas, utilizando datos públicos y sintéticos para generar KPIs, hallazgos analíticos y pronósticos de ventas.

### Objetivos específicos

1. Analizar los requisitos funcionales, técnicos y de calidad de datos necesarios para construir un datamart de ventas a partir de AdventureWorks, considerando datos sintéticos únicamente para pruebas controladas.
2. Diseñar la arquitectura y el flujo de trabajo del prototipo, integrando conexión de sólo lectura, introspección del esquema, interpretación de metadatos mediante un LLM, validación humana y ejecución controlada del proceso ETL.
3. Desarrollar una aplicación web que permita obtener los metadatos de la fuente relacional y generar propuestas supervisadas de modelo dimensional, KPIs y plan ETL mediante inteligencia artificial.
4. Implementar un proceso ETL trazable que construya y cargue un datamart de ventas desde una base destino vacía, y que genere KPIs, visualizaciones, hallazgos analíticos explicables y un pronóstico de ventas mediante regresión lineal.
5. Validar el funcionamiento del prototipo mediante consultas y resultados de referencia, controles de calidad de datos y las métricas MAPE y RMSE para evaluar el pronóstico de ventas.

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

## Aclaración sobre el LLM configurable

El anteproyecto requiere un LLM que proponga artefactos BI, siempre con validación determinística y aprobación humana. Para evitar depender de un único proveedor, el Sprint 2 preparará una configuración segura para elegir una sola conexión activa entre Gemini Cloud, Qwen Cloud y Ollama local. Esta preparación incluye administración de valores no secretos y una prueba limitada de conectividad desde FastAPI; no adelanta la generación de propuestas BI, la introspección, el ETL ni la ejecución de SQL.

## Objetivo de esta fase

- Repositorio y flujo Git preparados.
- Frontend y backend ejecutados íntegramente con Docker.
- Configuración reproducible y sin secretos versionados.
- PostgreSQL interno/datamart y SQL Server externo configurables.
- Endpoints de salud, OpenAPI y pantalla técnica inicial.
- CI/CD preparado en GitHub Actions.
- Ningún módulo de negocio implementado todavía.

## Límite aprobado para especificar el Sprint 3

Sprint 3 cubre la conexión de sólo lectura, introspección determinística, exploración del esquema y generación de una propuesta BI estructurada por el LLM activo. FastAPI valida las referencias contra una instantánea inmutable y una persona autorizada aprueba o rechaza la propuesta.

La creación física del datamart, ejecución del ETL, KPIs calculados, visualizaciones, hallazgos y pronóstico permanecen fuera de Sprint 3. La propuesta aprobada será la entrada controlada del Sprint 4.
