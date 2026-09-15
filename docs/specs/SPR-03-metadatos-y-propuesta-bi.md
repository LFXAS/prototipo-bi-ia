# SPR-03: metadatos y propuesta BI supervisada

- Estado: **borrador para revisión y aprobación**.
- Sprint: SPR-03.
- Responsable de especificación: equipo del proyecto.
- Rama prevista de implementación: `feature/sprint-03-metadata-copilot`.
- Fecha de creación: 2026-09-14.
- PR de implementación: pendiente.
- Dependencias: Sprint 2 integrado en `develop`, configuración LLM activa y RBAC operativo.

## 1. Propósito y relación con la investigación

El Sprint 3 inicia el núcleo funcional del proyecto titulado **“Prototipo web de inteligencia de negocios asistido por IA para la construcción semiautomatizada y supervisada de un datamart de ventas con datos públicos y sintéticos”**.

Su propósito es transformar una fuente relacional pública en una representación técnica verificable y emplear un LLM para producir una propuesta BI estructurada. La aplicación controla la conexión, introspección, validación y trazabilidad; el LLM interpreta metadatos y propone; una persona autorizada decide si la propuesta puede utilizarse como entrada del Sprint 4.

Este sprint no construye todavía el datamart ni ejecuta el ETL. Su resultado observable es una propuesta de modelo dimensional, KPIs y plan ETL que referencia únicamente metadatos reales de AdventureWorks, supera validaciones determinísticas y queda aprobada o rechazada con trazabilidad.

## 2. Capacidades normativas

| Capacidad | Especificación | Resultado esperado |
|---|---|---|
| Conexión e introspección | [SPR-03-01-conexion-e-introspeccion-adventureworks.md](SPR-03-01-conexion-e-introspeccion-adventureworks.md) | Instantánea reproducible de tablas, columnas, claves y relaciones de AdventureWorks sin extraer filas del negocio. |
| Propuesta BI asistida | [SPR-03-02-propuesta-bi-asistida-por-ia.md](SPR-03-02-propuesta-bi-asistida-por-ia.md) | Propuesta JSON de hecho, dimensiones, medidas, KPIs y plan ETL, validada y sometida a aprobación humana. |
| Exploración y trazabilidad | [SPR-03-03-explorador-esquema-y-trazabilidad.md](SPR-03-03-explorador-esquema-y-trazabilidad.md) | Experiencia responsive para comprender la fuente, delimitar el análisis y revisar la propuesta sin mezclar estados. |

La decisión arquitectónica se registra en [ADR 0003](../decisions/0003-metadatos-y-propuesta-bi-supervisada.md).

## 3. Actores y responsabilidades

| Actor | Responsabilidad |
|---|---|
| Persona administradora | Conserva permisos de recuperación y puede otorgar los permisos controlados de Sprint 3. |
| Analista autorizado | Prueba la fuente, genera una instantánea, delimita tablas, solicita una propuesta y la revisa. |
| Revisor autorizado | Aprueba, rechaza o solicita una nueva versión de la propuesta; no modifica silenciosamente el resultado de IA. |
| FastAPI | Autoriza, consulta catálogos SQL Server, normaliza metadatos, llama al proveedor activo, valida la respuesta y audita. |
| LLM activo | Interpreta exclusivamente el paquete de metadatos permitido y devuelve una propuesta estructurada; no ejecuta operaciones. |
| SQL Server/AdventureWorks | Fuente pública principal y de sólo lectura. |
| PostgreSQL | Conserva instantáneas, propuestas, validaciones, decisiones y auditoría; no recibe todavía tablas del datamart. |

## 4. Flujo de negocio de extremo a extremo

1. La persona autorizada abre **Fuente AdventureWorks** y ejecuta una prueba de conexión.
2. FastAPI usa la cadena del entorno y el usuario `bi_reader`; la interfaz nunca recibe secretos.
3. La persona solicita **Actualizar metadatos**.
4. FastAPI consulta catálogos del sistema, normaliza el resultado, calcula un hash y crea una instantánea inmutable.
5. La persona explora tablas y relaciones, y selecciona un alcance de ventas para el análisis. La aplicación añade las claves necesarias y advierte relaciones faltantes.
6. La persona solicita una propuesta. FastAPI exige una configuración LLM activa y probada, prepara un paquete compacto y registra su huella, no la credencial.
7. El LLM devuelve una propuesta JSON de modelo dimensional, KPIs y plan ETL declarativo.
8. FastAPI valida tablas, columnas, tipos, claves, relaciones, granularidad, medidas, KPIs y operaciones permitidas.
9. Si hay errores, la propuesta queda en `validation_failed` y no puede aprobarse. Si no los hay, queda en `ready_for_review`.
10. Un revisor consulta el resultado, sus supuestos, advertencias y validaciones; puede aprobarlo, rechazarlo con comentario o solicitar otra versión.
11. Una aprobación genera un artefacto inmutable para el Sprint 4; no crea tablas, no ejecuta SQL y no inicia cargas.

## 5. Reglas globales

1. Sólo existe una fuente activa en el Sprint 3: `AdventureWorks2022` en SQL Server.
2. AdventureWorks se consulta exclusivamente con intención de lectura y el usuario técnico sin permisos de escritura.
3. La introspección procesa metadatos, no filas de ventas, datos personales ni muestras de valores.
4. El LLM recibe nombres y tipos técnicos, claves, relaciones y descripciones controladas; no recibe credenciales, auditoría, usuarios ni datos crudos.
5. Ningún texto o SQL producido por el LLM se ejecuta.
6. La salida del LLM debe cumplir el contrato JSON versionado; una respuesta libre, incompleta o inválida se rechaza.
7. La validación determinística y la aprobación humana son obligatorias y diferentes: superar reglas técnicas no equivale a aprobación.
8. Una propuesta aprobada es inmutable. Una revisión posterior crea una nueva versión y conserva la anterior.
9. Los datos sintéticos se limitan a pruebas automatizadas y escenarios controlados; no constituyen una segunda fuente funcional.
10. Los límites de tiempo, tamaño del paquete y reintentos son controlados por FastAPI; una falla de proveedor no debe bloquear el resto de la plataforma.

## 6. Permisos y navegación previstos

| Código | Nombre visible | Uso |
|---|---|---|
| `metadata.read` | Consultar metadatos | Ver fuente, instantáneas, tablas, columnas y relaciones. |
| `metadata.refresh` | Actualizar metadatos | Probar la fuente y crear una nueva instantánea. |
| `copilot.proposals.read` | Consultar propuestas BI | Ver propuestas, validaciones y decisiones. |
| `copilot.proposals.generate` | Generar propuestas BI | Enviar metadatos aprobados al LLM activo. |
| `copilot.proposals.review` | Revisar propuestas BI | Aprobar, rechazar o solicitar una nueva versión. |

Se incorporan mediante migración y semilla idempotente. El rol Administrador protegido recibe los nuevos permisos. Los demás roles no los reciben automáticamente.

La navegación añade únicamente rutas funcionales:

- **Datos**: Fuente AdventureWorks y Explorador de esquema.
- **IA**: Propuesta BI.

## 7. Exclusiones explícitas

- CRUD de fuentes universales, múltiples fuentes activas o credenciales ingresadas desde React.
- Extracción de filas, perfilado estadístico de valores o envío de datos del negocio al LLM.
- Creación física de `fact_ventas` o dimensiones.
- Ejecución de ETL, DDL, DML o SQL generado por IA.
- Dashboard, reportes, hallazgos calculados y pronóstico de ventas.
- Chat libre con el LLM o memoria conversacional general.
- Validación con una segunda fuente de datos.

## 8. Condición de cierre del Sprint 3

El sprint puede cerrarse cuando:

- las tres especificaciones hijas hayan sido aprobadas y reflejadas en código;
- una instalación limpia pueda introspeccionar AdventureWorks y crear una instantánea consistente;
- un proveedor simulado en CI y al menos un proveedor real local o cloud produzcan una propuesta contractual;
- las validaciones impidan aprobar referencias inventadas o relaciones inexistentes;
- la aprobación humana quede separada de la generación y registrada en auditoría;
- la UI funcione en 320, 768, 1024 y 1440 px sin desplazamiento horizontal involuntario;
- `make verify` y CI concluyan correctamente;
- bitácora, manual técnico e informe del Sprint 3 se actualicen al finalizar la implementación.

## 9. Decisiones pendientes para la revisión humana

- Confirmar si el primer alcance de análisis se preselecciona con tablas conocidas de ventas o siempre lo selecciona la persona analista desde el explorador. La especificación propone selección humana asistida por relaciones.
- Confirmar quién podrá aprobar: inicialmente se propone un permiso independiente `copilot.proposals.review`.
- Confirmar si una nueva propuesta aprobada sustituye automáticamente a la anterior o requiere una confirmación adicional. Se propone confirmación explícita y estado `superseded` para la anterior.
