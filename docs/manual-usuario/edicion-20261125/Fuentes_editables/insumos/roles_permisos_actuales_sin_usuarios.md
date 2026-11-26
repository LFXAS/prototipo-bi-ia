# Matriz de definiciones de roles observada

Consulta de solo lectura del 18 de noviembre de 2026. Se consultaron roles, permisos y su tabla de asociación; no se consultaron cuentas ni asignaciones de personas. Esta matriz no es una prueba de inicio de sesión con cada perfil. Una cuenta con varios roles puede acumular permisos; la autorización final se resuelve en el servidor.

| Operación | Código técnico | Administrador | Operador | Analista BI | Gerente comercial |
| --- | --- | --- | --- | --- | --- |
| Consultar análisis visual | analytics.dashboard.read | Sí | No | Sí | Sí |
| Consultar auditoría | audit.read | Sí | No | Sí | No |
| Consultar conexiones | connections.read | Sí | No | Sí | Sí |
| Probar conexiones | connections.test | Sí | Sí | No | No |
| Administrar conexiones | connections.write | Sí | No | No | No |
| Consultar catálogo analítico | copilot.catalog.read | Sí | No | Sí | No |
| Administrar catálogo analítico | copilot.catalog.write | Sí | No | Sí | No |
| Generar propuestas BI | copilot.proposals.generate | Sí | No | Sí | No |
| Consultar propuestas BI | copilot.proposals.read | Sí | No | Sí | No |
| Revisar propuestas BI | copilot.proposals.review | Sí | No | Sí | No |
| Consultar materializaciones | etl.executions.read | Sí | No | Sí | No |
| Preparar materializaciones | etl.executions.write | Sí | No | Sí | No |
| Consultar metadatos | metadata.read | Sí | No | Sí | Sí |
| Actualizar metadatos | metadata.refresh | Sí | No | Sí | No |
| Resolver identidad de dimensiones | metadata.semantic_resolution.manage | Sí | No | Sí | No |
| Revisar identidad de dimensiones | metadata.semantic_resolution.read | Sí | No | Sí | No |
| Consultar configuración LLM | parameters.llm.read | Sí | Sí | No | No |
| Administrar configuración LLM | parameters.llm.write | Sí | Sí | No | No |
| Consultar parámetros | parameters.read | Sí | No | No | No |
| Administrar parámetros | parameters.write | Sí | Sí | No | No |
| Exportar reportes analíticos | reports.analytics.export | Sí | No | Sí | Sí |
| Consultar menús | security.menus.read | Sí | No | No | No |
| Administrar menús | security.menus.write | Sí | No | No | No |
| Consultar permisos | security.permissions.read | Sí | No | No | No |
| Administrar permisos | security.permissions.write | Sí | No | No | No |
| Consultar roles | security.roles.read | Sí | No | No | No |
| Administrar roles | security.roles.write | Sí | No | No | No |
| Consultar usuarios | security.users.read | Sí | No | No | No |
| Administrar usuarios | security.users.write | Sí | No | No | No |

Gerente comercial: consultar análisis visual, consultar conexiones, consultar metadatos y exportar reportes analíticos. La consulta de metadatos es necesaria para el selector actual de fuentes y permite abrir el explorador; no incluye editar catálogos, aprobar diseños, crear conexiones ni ejecutar ETL.

Los nombres y códigos son los existentes en esta instalación. La matriz describe los permisos definidos del rol, sin inferir que haya cuentas asignadas o campañas de uso completo realizadas con todos ellos.
