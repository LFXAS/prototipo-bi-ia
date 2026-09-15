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

Su propósito es transformar una necesidad expresada en lenguaje de negocio y una fuente relacional parametrizada desde la web en una propuesta BI estructurada y verificable. La aplicación controla la conexión, introspección, compactación, validación y trazabilidad; el LLM interpreta dinámicamente los metadatos técnicos, propone equivalencias de negocio en español y diseña la propuesta; una persona autorizada decide si representa correctamente la necesidad comercial y puede utilizarse como entrada del Sprint 4.

El producto no exige que un programador prepare consultas para cada análisis. Las programadoras construyen una sola vez el motor, los catálogos de operaciones y los validadores. En tiempo de uso, una persona de negocio describe qué desea analizar, la aplicación prepara el alcance técnico y el LLM presenta una propuesta comprensible en español. La generación y ejecución determinística de SQL corresponderá al módulo ETL del Sprint 4 y no será una tarea manual del usuario final.

Este sprint no construye todavía el datamart ni ejecuta el ETL. Su resultado observable es una propuesta de modelo dimensional, KPIs y plan ETL que referencia únicamente metadatos reales de AdventureWorks, supera validaciones determinísticas y queda aprobada o rechazada con trazabilidad.

## 2. Capacidades normativas

| Capacidad | Especificación | Resultado esperado |
|---|---|---|
| Configuración web y secretos | [SPR-03-04-configuracion-web-conexiones-y-secretos.md](SPR-03-04-configuracion-web-conexiones-y-secretos.md) | CRUD web de conexiones y credenciales cifradas, con interfaz extensible de conectores y SQL Server como primer motor funcional. |
| Conexión e introspección | [SPR-03-01-conexion-e-introspeccion-adventureworks.md](SPR-03-01-conexion-e-introspeccion-adventureworks.md) | Instantánea reproducible de tablas, columnas, claves y relaciones de la conexión SQL Server activa, validada con AdventureWorks y sin extraer filas del negocio. |
| Propuesta BI asistida | [SPR-03-02-propuesta-bi-asistida-por-ia.md](SPR-03-02-propuesta-bi-asistida-por-ia.md) | Solicitud de negocio guiada y propuesta JSON de hecho, dimensiones, medidas, KPIs y plan ETL, validada y sometida a aprobación humana. |
| Exploración y trazabilidad | [SPR-03-03-explorador-esquema-y-trazabilidad.md](SPR-03-03-explorador-esquema-y-trazabilidad.md) | Experiencia responsive con recorrido principal no técnico y explorador avanzado opcional, sin exigir tablas ni SQL al usuario de negocio. |

La decisión arquitectónica se registra en [ADR 0003](../decisions/0003-metadatos-y-propuesta-bi-supervisada.md).

## 3. Actores y responsabilidades

| Actor | Responsabilidad |
|---|---|
| Persona administradora técnica | Registra y prueba desde la web la fuente, las credenciales, el proveedor LLM, los usuarios y los permisos. No edita archivos ni crea consultas para cada análisis. |
| Gerente comercial o solicitante de negocio | Expresa el objetivo y las preguntas de ventas en español, revisa el resumen, dimensiones y KPIs propuestos y, en sprints posteriores, consume los resultados. No selecciona tablas ni escribe SQL en el recorrido principal. |
| Analista BI o responsable de datos | Usa la vista avanzada cuando sea necesario, revisa supuestos y advertencias y puede aprobar, rechazar o solicitar una nueva versión. Debe conocer el negocio, pero no necesita programar. |
| FastAPI | Autoriza, protege secretos, usa el conector activo, normaliza y compacta metadatos, valida referencias, llama al proveedor activo y audita. |
| LLM activo | Interpreta los nombres técnicos en su idioma original, propone conceptos comprensibles en español y devuelve una propuesta estructurada; no ejecuta operaciones. |
| SQL Server/AdventureWorks | Primer conector y fuente pública de validación, registrados desde la plataforma y utilizados en modo de sólo lectura. |
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

1. La persona administradora abre **Parámetros generales > Conexiones de datos**, registra SQL Server/AdventureWorks y su credencial mediante un formulario y ejecuta la prueba de sólo lectura.
2. FastAPI valida los campos, cifra el secreto, construye internamente la conexión mediante el adaptador `sqlserver` y nunca devuelve la credencial al navegador.
3. La persona activa la fuente y solicita actualizar metadatos. FastAPI consulta catálogos del sistema, normaliza el resultado, calcula un hash y crea o reutiliza una instantánea inmutable.
4. El gerente o analista abre **IA > Asistente de análisis** e indica en español el objetivo, preguntas comerciales, periodo y dimensiones de interés mediante controles guiados.
5. FastAPI crea resúmenes determinísticos por bloques de tablas, columnas, PK y FK. El LLM interpreta cada bloque según la solicitud y propone candidatos y nombres de negocio en español.
6. FastAPI descarta toda referencia inexistente, combina los candidatos válidos y exige que las relaciones procedan de la instantánea. Si el contexto requiere varios bloques, el proceso conserva sus etapas y huellas.
7. La aplicación presenta dinámicamente el alcance sugerido y su mapa semántico: concepto español, descripción y origen técnico. El usuario confirma los conceptos; los identificadores permanecen en una sección avanzada.
8. La persona solicita la propuesta dimensional. FastAPI exige una configuración LLM activa y probada, prepara el paquete compacto final y registra su huella, no la credencial.
9. El LLM devuelve una propuesta JSON en español de modelo dimensional, KPIs y plan ETL declarativo.
10. FastAPI valida tablas, columnas, tipos, claves, relaciones, granularidad, medidas, KPIs y operaciones permitidas.
11. Si hay errores, la propuesta queda en `validation_failed` y no puede aprobarse. Si no los hay, queda en `ready_for_review`.
12. Un analista BI o responsable autorizado revisa el significado de negocio, los supuestos, advertencias y validaciones; puede aprobar, rechazar con comentario o solicitar otra versión.
13. Una aprobación genera un artefacto inmutable para el Sprint 4; no crea tablas, no ejecuta SQL y no inicia cargas.

## 5. Reglas globales

1. Sólo existe una fuente activa en el Sprint 3. El único motor implementado es SQL Server y la validación académica se realiza con AdventureWorks2022.
2. La conexión se crea, prueba, activa y desactiva desde la plataforma. No se exige editar `.env`, Compose, código ni PostgreSQL para la operación ordinaria.
3. La fuente activa se consulta exclusivamente con intención de lectura y una cuenta sin permisos de escritura.
4. La introspección procesa metadatos, no filas de ventas, datos personales ni muestras de valores.
5. El recorrido principal parte de una solicitud de negocio; no exige escoger tablas, escribir identificadores ni comprender SQL.
6. El mapa semántico se genera para cada instantánea y solicitud. No contiene equivalencias codificadas exclusivamente para AdventureWorks; conserva concepto español, descripción, referencia técnica y evidencia de validación.
7. El LLM debe interpretar metadatos técnicos en inglés u otro idioma y convertirlos en conceptos de negocio comprensibles en español, sin inventar tablas o columnas.
8. El LLM recibe nombres y tipos técnicos, claves, relaciones y la solicitud de negocio; no recibe credenciales, auditoría, usuarios ni datos crudos.
9. Ningún texto o SQL producido por el LLM se ejecuta. El Sprint 4 deberá construir las consultas mediante un generador determinístico implementado una sola vez por el equipo y ejecutarlas desde el backend con permisos mínimos.
10. La salida del LLM debe cumplir el contrato JSON versionado; una respuesta libre, incompleta o inválida se rechaza.
11. La validación determinística y la aprobación de negocio son obligatorias y diferentes: superar reglas técnicas no equivale a que el resultado sea útil para el gerente.
12. Una propuesta aprobada es inmutable. Una revisión posterior crea una nueva versión y conserva la anterior como `superseded` sólo después de confirmación explícita.
13. Los datos sintéticos se limitan a pruebas automatizadas y escenarios controlados; no constituyen una segunda fuente funcional.
14. Los límites de tiempo, tamaño del paquete y reintentos son controlados por FastAPI; una falla de proveedor no debe bloquear el resto de la plataforma.

## 6. Permisos y navegación previstos

| Código | Nombre visible | Uso |
|---|---|---|
| `metadata.read` | Consultar metadatos | Ver fuente, instantáneas, tablas, columnas y relaciones. |
| `metadata.refresh` | Actualizar metadatos | Probar la fuente y crear una nueva instantánea. |
| `copilot.proposals.read` | Consultar propuestas BI | Ver propuestas, validaciones y decisiones. |
| `copilot.proposals.generate` | Generar propuestas BI | Enviar metadatos aprobados al LLM activo. |
| `copilot.proposals.review` | Revisar propuestas BI | Aprobar, rechazar o solicitar una nueva versión. |
| `connections.read` | Consultar conexiones | Ver configuraciones sin secretos. |
| `connections.write` | Administrar conexiones | Crear, editar, activar, desactivar y eliminar con validaciones. |
| `connections.test` | Probar conexiones | Validar conectividad, capacidades y sólo lectura. |

Se incorporan mediante migración y semilla idempotente. El rol Administrador protegido recibe los nuevos permisos. Los demás roles no los reciben automáticamente.

La navegación añade únicamente rutas funcionales y respeta los permisos del actor:

- **Parámetros generales**: Conexiones de datos y Configuración LLM.
- **Datos**: Fuente activa y Explorador de esquema, orientados a diagnóstico y revisión avanzada.
- **IA**: Asistente de análisis, recorrido principal para formular la necesidad y revisar la propuesta BI.

## 7. Exclusiones explícitas

- Uso simultáneo de varias fuentes o implementación funcional de motores distintos de SQL Server.
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

- las cuatro especificaciones hijas hayan sido aprobadas y reflejadas en código;
- una instalación limpia pueda introspeccionar AdventureWorks y crear una instantánea consistente;
- un proveedor simulado en CI y al menos un proveedor real local o cloud produzcan una propuesta contractual;
- un usuario de negocio pueda iniciar una propuesta desde un objetivo guiado sin seleccionar tablas ni escribir SQL;
- una persona administradora pueda registrar y probar AdventureWorks desde la web sin editar archivos ni la base interna;
- los parámetros operativos declarados por cada módulo puedan administrarse desde la web con tipo, rango, valor predeterminado y auditoría, sin aceptar claves arbitrarias;
- los secretos de fuente y LLM queden cifrados, no recuperables y excluidos de logs/auditoría;
- el LLM genere dinámicamente una correspondencia entre el concepto español y el origen técnico, y el backend descarte cualquier referencia inexistente;
- las validaciones impidan aprobar referencias inventadas o relaciones inexistentes;
- la aprobación humana quede separada de la generación y registrada en auditoría;
- la UI funcione en 320, 768, 1024 y 1440 px sin desplazamiento horizontal involuntario;
- `make verify` y CI concluyan correctamente;
- bitácora, manual técnico e informe del Sprint 3 se actualicen al finalizar la implementación.

## 9. Decisiones incorporadas durante la revisión

- El recorrido predeterminado es guiado por objetivo de negocio e interpretación semántica dinámica; la selección manual de tablas existe sólo como modo avanzado para el analista BI.
- La revisión usa el permiso independiente `copilot.proposals.review` y evalúa significado de negocio, advertencias y trazabilidad; no exige aprobar SQL.
- Una nueva propuesta aprobada sustituye a la anterior únicamente mediante confirmación explícita y conserva la versión previa como `superseded`.
- Las etiquetas y explicaciones visibles se generan dinámicamente en español desde los metadatos técnicos y conservan siempre los identificadores originales; toda referencia inventada se rechaza.
- Las conexiones y credenciales operativas se administran desde la plataforma. SQL Server es el único adaptador funcional de Sprint 3, pero el contrato permite incorporar otros motores sin rediseñar el flujo.
- La generación y ejecución de consultas no forman parte del Sprint 3. El Sprint 4 deberá especificar un constructor determinístico y un ejecutor backend; ningún programador redactará consultas por solicitud en la operación normal.
