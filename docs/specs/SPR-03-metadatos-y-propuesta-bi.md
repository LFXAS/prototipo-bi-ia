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

Su propósito es transformar una necesidad expresada en lenguaje de negocio y una fuente relacional pública en una propuesta BI estructurada y verificable. La aplicación controla la conexión, introspección, preselección del alcance técnico, validación y trazabilidad; el LLM interpreta metadatos y propone; una persona autorizada decide si la propuesta representa correctamente la necesidad comercial y puede utilizarse como entrada del Sprint 4.

El producto no exige que un programador prepare consultas para cada análisis. Las programadoras construyen una sola vez el motor, los catálogos de operaciones y los validadores. En tiempo de uso, una persona de negocio describe qué desea analizar, la aplicación prepara el alcance técnico y el LLM presenta una propuesta comprensible en español. La generación y ejecución determinística de SQL corresponderá al módulo ETL del Sprint 4 y no será una tarea manual del usuario final.

Este sprint no construye todavía el datamart ni ejecuta el ETL. Su resultado observable es una propuesta de modelo dimensional, KPIs y plan ETL que referencia únicamente metadatos reales de AdventureWorks, supera validaciones determinísticas y queda aprobada o rechazada con trazabilidad.

## 2. Capacidades normativas

| Capacidad | Especificación | Resultado esperado |
|---|---|---|
| Conexión e introspección | [SPR-03-01-conexion-e-introspeccion-adventureworks.md](SPR-03-01-conexion-e-introspeccion-adventureworks.md) | Instantánea reproducible de tablas, columnas, claves y relaciones de AdventureWorks sin extraer filas del negocio. |
| Propuesta BI asistida | [SPR-03-02-propuesta-bi-asistida-por-ia.md](SPR-03-02-propuesta-bi-asistida-por-ia.md) | Solicitud de negocio guiada y propuesta JSON de hecho, dimensiones, medidas, KPIs y plan ETL, validada y sometida a aprobación humana. |
| Exploración y trazabilidad | [SPR-03-03-explorador-esquema-y-trazabilidad.md](SPR-03-03-explorador-esquema-y-trazabilidad.md) | Experiencia responsive con recorrido principal no técnico y explorador avanzado opcional, sin exigir tablas ni SQL al usuario de negocio. |

La decisión arquitectónica se registra en [ADR 0003](../decisions/0003-metadatos-y-propuesta-bi-supervisada.md).

## 3. Actores y responsabilidades

| Actor | Responsabilidad |
|---|---|
| Persona administradora técnica | Configura una vez el entorno, la fuente, el proveedor LLM, los usuarios y los permisos. No crea consultas para cada análisis. |
| Gerente comercial o solicitante de negocio | Expresa el objetivo y las preguntas de ventas en español, revisa el resumen, dimensiones y KPIs propuestos y, en sprints posteriores, consume los resultados. No selecciona tablas ni escribe SQL en el recorrido principal. |
| Analista BI o responsable de datos | Usa la vista avanzada cuando sea necesario, revisa supuestos y advertencias y puede aprobar, rechazar o solicitar una nueva versión. Debe conocer el negocio, pero no necesita programar. |
| FastAPI | Autoriza, consulta catálogos SQL Server, normaliza metadatos, preselecciona un alcance técnico, llama al proveedor activo, valida la respuesta y audita. |
| LLM activo | Interpreta exclusivamente el paquete de metadatos permitido y devuelve una propuesta estructurada; no ejecuta operaciones. |
| SQL Server/AdventureWorks | Fuente pública principal y de sólo lectura. |
| PostgreSQL | Conserva instantáneas, propuestas, validaciones, decisiones y auditoría; no recibe todavía tablas del datamart. |

### 3.1 Momento de uso por el usuario final

| Etapa | Valor para el usuario |
|---|---|
| Sprint 2 | Administración técnica; todavía no existe una función analítica para el gerente. |
| Sprint 3 | El usuario de negocio puede crear una solicitud guiada, comprender la propuesta y revisar conceptos; todavía no recibe indicadores calculados. |
| Sprint 4 | La propuesta aprobada podrá materializarse mediante un motor ETL controlado y entregar los primeros KPIs y visualizaciones. |
| Analítica y pronóstico posteriores | El gerente consumirá dashboard, hallazgos explicables, preguntas al copiloto y pronóstico de ventas. |

El Sprint 3 debe probar la participación real del usuario final sin presentar como terminado un producto que aún no calcula resultados.

## 4. Flujo de negocio de extremo a extremo

1. La persona administradora prueba una vez **Fuente AdventureWorks** y actualiza sus metadatos con permisos controlados.
2. FastAPI usa la cadena del entorno y el usuario `bi_reader`; la interfaz nunca recibe secretos.
3. FastAPI consulta catálogos del sistema, normaliza el resultado, calcula un hash y crea o reutiliza una instantánea inmutable.
4. El gerente o analista abre **IA > Asistente de análisis** e indica en español el objetivo, preguntas comerciales, periodo y dimensiones de interés mediante controles guiados.
5. FastAPI aplica el perfil determinístico `adventureworks-sales-v1`: identifica tablas ancla de ventas, recorre exclusivamente relaciones declaradas e incorpora las dependencias técnicas necesarias.
6. La aplicación presenta un resumen de negocio del alcance sugerido. El usuario confirma conceptos como Venta, Fecha, Producto, Cliente y Territorio; los nombres técnicos permanecen en una sección avanzada.
7. La persona solicita una propuesta. FastAPI exige una configuración LLM activa y probada, prepara un paquete compacto y registra su huella, no la credencial.
8. El LLM devuelve una propuesta JSON en español de modelo dimensional, KPIs y plan ETL declarativo.
9. FastAPI valida tablas, columnas, tipos, claves, relaciones, granularidad, medidas, KPIs y operaciones permitidas.
10. Si hay errores, la propuesta queda en `validation_failed` y no puede aprobarse. Si no los hay, queda en `ready_for_review`.
11. Un analista BI o responsable autorizado revisa el significado de negocio, los supuestos, advertencias y validaciones; puede aprobar, rechazar con comentario o solicitar otra versión.
12. Una aprobación genera un artefacto inmutable para el Sprint 4; no crea tablas, no ejecuta SQL y no inicia cargas.

## 5. Reglas globales

1. Sólo existe una fuente activa en el Sprint 3: `AdventureWorks2022` en SQL Server.
2. AdventureWorks se consulta exclusivamente con intención de lectura y el usuario técnico sin permisos de escritura.
3. La introspección procesa metadatos, no filas de ventas, datos personales ni muestras de valores.
4. El recorrido principal parte de una solicitud de negocio; no exige escoger tablas, escribir identificadores ni comprender SQL.
5. La aplicación mantiene un glosario español versionado que vincula etiquetas de negocio con identificadores técnicos originales sin renombrar AdventureWorks.
6. El LLM recibe nombres y tipos técnicos, claves, relaciones, la solicitud de negocio y descripciones controladas; no recibe credenciales, auditoría, usuarios ni datos crudos.
7. Ningún texto o SQL producido por el LLM se ejecuta. El Sprint 4 deberá construir las consultas mediante un generador determinístico implementado una sola vez por el equipo y ejecutarlas desde el backend con permisos mínimos.
8. La salida del LLM debe cumplir el contrato JSON versionado; una respuesta libre, incompleta o inválida se rechaza.
9. La validación determinística y la aprobación de negocio son obligatorias y diferentes: superar reglas técnicas no equivale a que el resultado sea útil para el gerente.
10. Una propuesta aprobada es inmutable. Una revisión posterior crea una nueva versión y conserva la anterior como `superseded` sólo después de confirmación explícita.
11. Los datos sintéticos se limitan a pruebas automatizadas y escenarios controlados; no constituyen una segunda fuente funcional.
12. Los límites de tiempo, tamaño del paquete y reintentos son controlados por FastAPI; una falla de proveedor no debe bloquear el resto de la plataforma.

## 6. Permisos y navegación previstos

| Código | Nombre visible | Uso |
|---|---|---|
| `metadata.read` | Consultar metadatos | Ver fuente, instantáneas, tablas, columnas y relaciones. |
| `metadata.refresh` | Actualizar metadatos | Probar la fuente y crear una nueva instantánea. |
| `copilot.proposals.read` | Consultar propuestas BI | Ver propuestas, validaciones y decisiones. |
| `copilot.proposals.generate` | Generar propuestas BI | Enviar metadatos aprobados al LLM activo. |
| `copilot.proposals.review` | Revisar propuestas BI | Aprobar, rechazar o solicitar una nueva versión. |

Se incorporan mediante migración y semilla idempotente. El rol Administrador protegido recibe los nuevos permisos. Los demás roles no los reciben automáticamente.

La navegación añade únicamente rutas funcionales y respeta los permisos del actor:

- **Datos**: Fuente AdventureWorks y Explorador de esquema, orientados a administración y revisión avanzada.
- **IA**: Asistente de análisis, recorrido principal para formular la necesidad y revisar la propuesta BI.

## 7. Exclusiones explícitas

- CRUD de fuentes universales, múltiples fuentes activas o credenciales ingresadas desde React.
- Extracción de filas, perfilado estadístico de valores o envío de datos del negocio al LLM.
- Creación física de `fact_ventas` o dimensiones.
- Ejecución de ETL, DDL, DML o SQL generado por IA.
- Dashboard, reportes, hallazgos calculados y pronóstico de ventas.
- Chat libre con el LLM o memoria conversacional general.
- Validación con una segunda fuente de datos.
- Dependencia de un programador para escribir o ajustar consultas por cada solicitud de negocio.
- Promesa de que el gerente administra conexiones, interpreta 71 tablas o valida detalles físicos del esquema.

## 8. Condición de cierre del Sprint 3

El sprint puede cerrarse cuando:

- las tres especificaciones hijas hayan sido aprobadas y reflejadas en código;
- una instalación limpia pueda introspeccionar AdventureWorks y crear una instantánea consistente;
- un proveedor simulado en CI y al menos un proveedor real local o cloud produzcan una propuesta contractual;
- un usuario de negocio pueda iniciar una propuesta desde un objetivo guiado sin seleccionar tablas ni escribir SQL;
- el perfil de ventas preseleccione únicamente objetos existentes y explique en español su alcance;
- las validaciones impidan aprobar referencias inventadas o relaciones inexistentes;
- la aprobación humana quede separada de la generación y registrada en auditoría;
- la UI funcione en 320, 768, 1024 y 1440 px sin desplazamiento horizontal involuntario;
- `make verify` y CI concluyan correctamente;
- bitácora, manual técnico e informe del Sprint 3 se actualicen al finalizar la implementación.

## 9. Decisiones incorporadas durante la revisión

- El recorrido predeterminado es guiado por objetivo de negocio y preselección determinística; la selección manual de tablas existe sólo como modo avanzado para el analista BI.
- La revisión usa el permiso independiente `copilot.proposals.review` y evalúa significado de negocio, advertencias y trazabilidad; no exige aprobar SQL.
- Una nueva propuesta aprobada sustituye a la anterior únicamente mediante confirmación explícita y conserva la versión previa como `superseded`.
- Las etiquetas y explicaciones visibles se presentan en español mediante un glosario controlado, conservando siempre los identificadores técnicos originales.
- La generación y ejecución de consultas no forman parte del Sprint 3. El Sprint 4 deberá especificar un constructor determinístico y un ejecutor backend; ningún programador redactará consultas por solicitud en la operación normal.
