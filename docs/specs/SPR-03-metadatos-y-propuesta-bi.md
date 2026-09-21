# SPR-03: metadatos y propuesta BI supervisada

- Estado: **implementado y verificado localmente; pendiente de validación del usuario y PR**.
- Sprint: SPR-03.
- Responsable de especificación: equipo del proyecto.
- Rama prevista de implementación: `feature/sprint-03-metadata-copilot`.
- Fecha de creación: 2026-09-14.
- PR de implementación: pendiente.
- Dependencias: Sprint 2 integrado en `develop`, configuración LLM activa y RBAC operativo.

## 1. Propósito y relación con la investigación

El Sprint 3 inicia el núcleo funcional del proyecto titulado **“Prueba de concepto de un prototipo funcional de BI asistido por IA para la construcción semiautomatizada y supervisada de un datamart de ventas”**.

Su propósito es transformar una necesidad expresada en lenguaje de negocio y una fuente relacional parametrizada desde la web en una propuesta BI estructurada y verificable. La aplicación controla la conexión, introspección, compactación, validación y trazabilidad; el LLM interpreta dinámicamente los metadatos técnicos, propone equivalencias de negocio en español y diseña la propuesta; una persona autorizada decide si representa correctamente la necesidad comercial y puede utilizarse como entrada del Sprint 4.

El producto no exige que un programador prepare consultas para cada análisis. Las programadoras construyen una sola vez el motor, los catálogos de operaciones y los validadores. En tiempo de uso, una persona de negocio describe qué desea analizar, la aplicación prepara el alcance técnico y el LLM presenta una propuesta comprensible en español. La generación y ejecución determinística de SQL corresponderá al módulo ETL del Sprint 4 y no será una tarea manual del usuario final.

Este sprint no construye todavía el datamart ni ejecuta el ETL. Su resultado observable es una propuesta de modelo dimensional, KPIs y plan ETL que referencia únicamente metadatos reales de AdventureWorks, supera validaciones determinísticas y queda aprobada o rechazada con trazabilidad.

## 2. Capacidades normativas

| Capacidad | Especificación | Resultado esperado |
|---|---|---|
| Configuración web y secretos | [SPR-03-04-configuracion-web-conexiones-y-secretos.md](SPR-03-04-configuracion-web-conexiones-y-secretos.md) | Una conexión SQL Server configurable, credenciales cifradas, cuatro parámetros numéricos y un catálogo de necesidades analíticas; la extensibilidad queda preparada, no implementada. |
| Conexión e introspección | [SPR-03-01-conexion-e-introspeccion-adventureworks.md](SPR-03-01-conexion-e-introspeccion-adventureworks.md) | Instantánea reproducible de tablas, columnas, claves y relaciones de la conexión SQL Server activa, validada con AdventureWorks y sin extraer filas del negocio. |
| Propuesta BI asistida | [SPR-03-02-propuesta-bi-asistida-por-ia.md](SPR-03-02-propuesta-bi-asistida-por-ia.md) | Solicitud de negocio guiada y propuesta JSON de hecho, dimensiones, medidas, KPIs y plan ETL, validada y sometida a aprobación humana. |
| Exploración y trazabilidad | [SPR-03-03-explorador-esquema-y-trazabilidad.md](SPR-03-03-explorador-esquema-y-trazabilidad.md) | Experiencia responsive con recorrido principal no técnico y explorador avanzado opcional, sin exigir tablas ni SQL al usuario de negocio. |
| Interfaz y experiencia | [SPR-03-05-ui-ux-profesional.md](SPR-03-05-ui-ux-profesional.md) | Sistema visual e interactivo, pantallas, estados, responsive y accesibilidad del recorrido profesional del Sprint 3. |

La decisión arquitectónica se registra en [ADR 0003](../decisions/0003-metadatos-y-propuesta-bi-supervisada.md).

### 2.1 Compromiso de implementación

Para mantener un trabajo de titulación sólido y alcanzable, el alcance se divide en tres niveles:

| Nivel | Compromiso |
|---|---|
| Obligatorio en Sprint 3 | Configuración web mínima, conexión SQL Server, instantánea de metadatos, solicitud de negocio, interpretación dinámica en español, propuesta estructurada, validación determinística y aprobación humana. |
| Preparado, no implementado | Interfaz interna para futuros conectores y posibilidad de sustituir el almacén local de secretos. No se muestran capacidades que aún no funcionan. |
| Sprints posteriores | Construcción física del datamart, ETL, KPIs calculados, dashboard, hallazgos y pronóstico. |

La contribución académica no consiste en ofrecer muchos motores ni controles empresariales. Consiste en demostrar un proceso reproducible donde el LLM interpreta metadatos, el software comprueba que no invente objetos y una persona de negocio supervisa el resultado antes de materializarlo.

### 2.2 Valor observable para el usuario principal

El analista BI o responsable de datos no administra infraestructura ni escribe consultas por cada análisis. En Sprint 3 recoge la necesidad comercial, la expresa mediante un flujo guiado, recibe conceptos comprensibles en español y revisa qué modelo, dimensiones y KPIs propone el asistente. El gerente comercial aporta la necesidad y será el consumidor principal de los resultados calculados en los sprints posteriores. Esta continuidad reduce la distancia entre la fuente técnica y la decisión de negocio sin eliminar el control humano especializado.

### 2.3 Evidencia académica

La demostración del sprint conservará la instantánea y su hash, la solicitud usada, los conceptos propuestos, las referencias rechazadas por el validador y la decisión humana. La evaluación reportará:

- porcentaje de referencias técnicas válidas antes y después del validador;
- cumplimiento del contrato estructurado;
- trazabilidad completa entre concepto español y tabla/columna real;
- valoración humana de claridad, coherencia y utilidad mediante una rúbrica breve.

La plataforma incorpora desde este sprint una sección **Validación estructural de la propuesta - Sprint 3** para la versión seleccionada. Recalcula integridad de metadatos, validez referencial y contrato, y reconstruye determinísticamente la propuesta desde las decisiones persistidas. Presenta el estado de cada control y enumera las validaciones aún pendientes. La conciliación de cifras contra el OLTP no se simula: se agregará al expediente acumulativo cuando Sprint 4 pueda ejecutar consultas de referencia sobre la fuente y el datamart materializado, conforme a `docs/validation-plan.md`.

Estas evidencias permiten evaluar el aporte de IA y el control del software sin añadir motores, dashboards ni algoritmos fuera del sprint.

### 2.4 Avance frente a los objetivos del anteproyecto

| Objetivo | Evidencia al cierre de Sprint 3 | Estado acumulado |
|---|---|---|
| 1. Analizar requisitos funcionales, técnicos y de calidad | Alcance, contratos, permisos, reglas de seguridad, metadatos y plan de validación especificados. | Cumplido para el alcance de Sprint 3; continúa refinándose con el ETL. |
| 2. Diseñar arquitectura y flujo | Arquitectura Docker, conexión de sólo lectura, introspección, LLM supervisado, versionado y validación determinística implementados. | Cumplimiento sustancial; falta incorporar el ejecutor ETL. |
| 3. Desarrollar la aplicación que obtiene metadatos y genera propuestas | Flujo funcional desde fuente activa hasta propuesta versionada, personalizable, validada y aprobable con Ollama y Gemini. | Cumplido para la propuesta; la materialización pertenece al objetivo 4. |
| 4. Implementar ETL, datamart, KPIs, visualizaciones, hallazgos y pronóstico | Sólo existe la vista previa declarativa del plan; no se ejecutan operaciones. | Pendiente de los sprints posteriores. |
| 5. Validar exactitud, reproducibilidad y utilidad | Se validan estructura, referencias, contrato y reproducción del artefacto aprobado sin volver a invocar al LLM. | Parcial y correctamente delimitado; conciliación OLTP-datamart, contraste con AdventureWorksDW, juicio de expertos, MAPE y RMSE siguen pendientes. |

## 3. Actores y responsabilidades

| Actor | Responsabilidad |
|---|---|
| Persona administradora técnica | Registra y prueba desde la web la fuente, las credenciales, el proveedor LLM, los usuarios y los permisos. No edita archivos ni crea consultas para cada análisis. |
| Gerente comercial o solicitante de negocio | Aporta el objetivo, las preguntas y los criterios de utilidad del negocio. Puede revisar el resumen comprensible y, en sprints posteriores, consume KPIs, visualizaciones, hallazgos y pronósticos. No valida relaciones, granularidad ni el plan ETL. |
| Analista BI o responsable de datos | Es el usuario principal del Asistente de datamart: selecciona el dominio habilitado, registra la necesidad comercial, resuelve ambigüedades, revisa conceptos, personaliza dimensiones, medidas, agregaciones y KPIs dentro del alcance comprobado, y aprueba o rechaza. Debe comprender el negocio y los datos, pero no necesita programar ni escribir SQL. |
| FastAPI | Autoriza, protege secretos, usa el conector activo, normaliza y compacta metadatos, valida referencias, llama al proveedor activo y audita. |
| LLM activo | Interpreta los nombres técnicos en su idioma original, propone conceptos comprensibles en español y devuelve una propuesta estructurada; no ejecuta operaciones. |
| SQL Server/AdventureWorks | Primer conector y fuente pública de validación, registrados desde la plataforma y utilizados en modo de sólo lectura. |
| PostgreSQL | Conserva instantáneas, propuestas, validaciones, decisiones y auditoría; no recibe todavía tablas del datamart. |

### 3.1 Momento de uso por el usuario final

| Etapa | Valor para el usuario |
|---|---|
| Sprint 2 | Administración técnica; todavía no existe una función analítica para el gerente. |
| Sprint 3 | El analista BI crea una solicitud guiada a partir de la necesidad comercial, comprende la propuesta y revisa sus conceptos; todavía no existen indicadores calculados. |
| Sprint 4 | La propuesta aprobada podrá materializarse mediante un motor ETL controlado y entregar los primeros KPIs y visualizaciones. |
| Analítica y pronóstico posteriores | El gerente consumirá dashboard, hallazgos explicables, preguntas al copiloto y pronóstico de ventas. |

El Sprint 3 debe probar la participación real del usuario final sin presentar como terminado un producto que aún no calcula resultados.

## 4. Flujo de negocio de extremo a extremo

1. La persona administradora abre **Parámetros generales > Conexiones de datos**, registra SQL Server/AdventureWorks y su credencial mediante un formulario y ejecuta la prueba de sólo lectura.
   En una instalación incompleta puede realizar esta preparación mediante el wizard inicial, que reutiliza las mismas pantallas y operaciones junto con la configuración LLM.
2. FastAPI valida los campos, cifra el secreto, construye internamente la conexión mediante el adaptador `sqlserver` y nunca devuelve la credencial al navegador.
3. La persona activa la fuente y solicita actualizar metadatos. FastAPI consulta catálogos del sistema, normaliza el resultado, calcula un hash y crea o reutiliza una instantánea inmutable.
4. El analista BI abre **IA > Asistente de datamart**. Primero selecciona un dominio de un catálogo calculado desde la instantánea y los perfiles disponibles. En Sprint 3 sólo **Datamart de ventas** está habilitado; inventario u otros dominios aparecerán cuando incorporen perfil y validadores propios, sin rediseñar la pantalla.
5. El backend combina el dominio, el catálogo dinámico de preguntas y las periodicidades soportadas con la instantánea vigente. El analista escribe en español el objetivo de cada análisis. No selecciona dimensiones en este paso: el LLM debe proponerlas desde los metadatos y el backend comprobarlas.
6. FastAPI divide los metadatos en bloques de tamaño parametrizado. El LLM interpreta cada bloque según la solicitud y propone candidatos y nombres de negocio en español.
7. FastAPI descarta toda referencia inexistente y combina únicamente candidatos relacionados mediante claves declaradas.
8. La aplicación presenta dinámicamente el alcance sugerido y su mapa semántico: concepto español, descripción y origen técnico. El usuario confirma los conceptos; los identificadores permanecen en una sección avanzada.
9. La persona solicita la propuesta dimensional. FastAPI exige una configuración LLM activa y probada, prepara el paquete compacto final y registra su huella, no la credencial.
10. El LLM devuelve una propuesta JSON en español de modelo dimensional, KPIs y plan ETL declarativo.
11. FastAPI valida tablas, columnas, tipos, claves, relaciones, granularidad, medidas, KPIs y operaciones permitidas.
12. Si la propuesta es válida, el analista puede aceptarla sin cambios o crear una versión derivada modificando resumen, granularidad, dimensiones, medidas, agregaciones y KPIs ya comprobados. No puede inventar objetos ni fórmulas; cada ajuste se vuelve a validar y queda enlazado a su versión de origen.
13. Las versiones se consultan con filtro de estado y paginación. Por defecto se muestran las que están **Listas para revisar**; también se pueden consultar aprobadas, rechazadas, fallidas o todas sin volver a consumir el LLM.
14. Un analista BI o responsable autorizado revisa significado, supuestos, advertencias y validaciones; puede aprobar o rechazar con comentario.
15. Una aprobación genera el artefacto de entrada del Sprint 4; no crea tablas ni ejecuta cargas.

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
11. La validación determinística y la revisión del analista BI son obligatorias y diferentes: superar reglas técnicas no equivale a representar correctamente la necesidad comercial.
12. Una propuesta aprobada es inmutable. Un nuevo intento crea otro registro y conserva el anterior.
13. Los datos sintéticos se limitan a pruebas automatizadas y escenarios controlados; no constituyen una segunda fuente funcional.
14. Los límites de tiempo, tamaño del paquete y reintentos son controlados por FastAPI; una falla de proveedor no debe bloquear el resto de la plataforma.
15. El catálogo de dominios y capacidades se obtiene desde el backend a partir de la instantánea vigente. React no contiene una lista fija de preguntas o dimensiones de AdventureWorks.
16. La personalización del analista sólo puede reutilizar decisiones y referencias ya verificadas. Cada ajuste crea una versión inmutable, conserva el vínculo de origen y vuelve a ejecutar el mismo validador determinístico.
17. Un perfil con `copilot.catalog.write` puede administrar por dominio preguntas de negocio y varias periodicidades soportadas mediante CRUD. El objetivo no se parametriza y las dimensiones no pertenecen al catálogo. Los adaptadores, relaciones semánticas, destinos y validadores continúan protegidos en el perfil implementado.
18. La verificación distingue errores bloqueantes de diferencias por evolución del motor. Una propuesta anterior válida no pierde su aprobación únicamente por pertenecer a otra versión; una restauración posterior exige revisión y queda auditada.

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
- **Datos**: Explorador de esquema, orientado a diagnóstico y trazabilidad avanzada de sólo lectura.
- **IA**: Asistente de datamart, entrada genérica para seleccionar un dominio habilitado, formular la necesidad, personalizar y revisar la propuesta BI.

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

- una persona administradora configure y pruebe LLM y AdventureWorks desde la web;
- una instalación limpia cree una instantánea consistente de metadatos sin extraer filas;
- un analista BI registre la necesidad comercial y reciba conceptos en español sin seleccionar manualmente tablas ni escribir SQL;
- un proveedor simulado en CI y Ollama o un proveedor cloud real produzcan la propuesta contractual;
- cualquier tabla, columna o relación inventada sea rechazada por el backend;
- una persona autorizada pueda aprobar o rechazar y la decisión quede auditada;
- el catálogo de preguntas y dimensiones responda a los metadatos vigentes y no dependa de constantes del frontend;
- el analista pueda crear una versión personalizada y validada sin escribir SQL ni alterar una decisión final;
- el historial aplique por defecto el filtro **Lista para revisar**, permita cambiar de estado y paginar resultados;
- la evidencia permita calcular validez referencial y aplicar la rúbrica de claridad, coherencia y utilidad;
- la reejecución determinística visible produzca la misma huella para una propuesta no alterada y detecte cualquier diferencia;
- los cuatro parámetros numéricos funcionen dentro de sus rangos y el catálogo de necesidades sólo acepte la estructura y códigos protegidos;
- el recorrido sea usable en móvil y escritorio;
- `make verify`, CI, bitácora, manual técnico e informe del Sprint 3 queden aprobados.

## 9. Decisiones incorporadas durante la revisión

- El recorrido es guiado por objetivo de negocio e interpretación semántica dinámica. El explorador avanzado permite verificar referencias, pero no editar manualmente el alcance en Sprint 3.
- La revisión usa el permiso independiente `copilot.proposals.review` y evalúa significado de negocio, advertencias y trazabilidad; no exige aprobar SQL.
- Cada nuevo intento conserva el anterior; no se sobrescriben propuestas ni decisiones.
- Las etiquetas y explicaciones visibles se generan dinámicamente en español desde los metadatos técnicos y conservan siempre los identificadores originales; toda referencia inventada se rechaza.
- Las conexiones y credenciales operativas se administran desde la plataforma. SQL Server es el único adaptador funcional de Sprint 3, pero el contrato permite incorporar otros motores sin rediseñar el flujo.
- La generación y ejecución de consultas no forman parte del Sprint 3. El Sprint 4 deberá especificar un constructor determinístico y un ejecutor backend; ningún programador redactará consultas por solicitud en la operación normal.
- La entrada se denomina **Asistente de datamart** y empieza por un catálogo de dominios. Sólo ventas se habilita en la prueba de concepto, pero agregar inventario requiere un nuevo perfil, reglas y pruebas en backend, no una pantalla paralela.
- Las preguntas orientan al LLM sin imponer tablas ni dimensiones. Las periodicidades visibles deben tener una estrategia técnica soportada y una fecha verificable. Las dimensiones aparecen sólo como resultado de la interpretación de IA y de la comprobación determinística posterior.
- La persona administradora puede adaptar desde **Parámetros** el lenguaje y la disponibilidad del catálogo de necesidades sin editar archivos; esta parametrización no crea nuevos dominios ni capacidades técnicas.
- La supervisión no se limita a aprobar o rechazar: el analista puede derivar una versión modificando decisiones de negocio controladas. Las referencias técnicas y fórmulas libres permanecen fuera de su alcance.
- El historial se consulta en el servidor por dominio y estado, con paginación. El estado inicial es **Lista para revisar** para priorizar el trabajo pendiente.
