# Alcance técnico vigente

Fuente: anteproyecto corregido `A15_E25 (LVelásquez - ERobles) (ANTEPROYECTO).pdf`, 11 páginas, revisado el 24 de agosto de 2026.

## Identificación vigente de la investigación

Título acordado el 14 de septiembre de 2026:

> **Prueba de concepto de un prototipo funcional de BI asistido por IA para la construcción semiautomatizada y supervisada de un datamart de ventas.**

La fuente pública funcional es AdventureWorks. Los datos sintéticos se utilizan únicamente para pruebas controladas y valores faltantes; no representan una segunda fuente que el prototipo deba conectar o validar.

### Usuarios previstos

El usuario operativo principal del Sprint 3 es el analista BI o responsable de datos. Registra la necesidad del área comercial, utiliza el asistente, resuelve ambigüedades y revisa la propuesta sin programar ni escribir SQL. Una persona administradora configura desde la plataforma las conexiones, credenciales, proveedor LLM y permisos. El equipo de desarrollo construye el motor general y no prepara consultas por cada análisis.

El gerente comercial, gerente general o directivo es usuario final de la información: aporta preguntas y criterios de utilidad y, después de la materialización del datamart y el ETL, consume KPIs, visualizaciones, hallazgos, reportes y un copiloto contextual para apoyar decisiones. No valida relaciones, granularidad ni el plan ETL. El analista BI dispone además de calidad, trazabilidad y evidencia detallada sin recurrir a una herramienta SQL externa.

### Objetivo general

Desarrollar un prototipo web de inteligencia de negocios asistido por IA que permita la construcción semiautomatizada y supervisada de un datamart de ventas, utilizando datos públicos y sintéticos para generar KPIs, visualizaciones, hallazgos analíticos explicables y reportes orientados a decisiones.

### Objetivos específicos

1. Analizar los requisitos funcionales, técnicos y de calidad de datos necesarios para construir un datamart de ventas a partir de AdventureWorks, considerando datos sintéticos únicamente para pruebas controladas.
2. Diseñar la arquitectura y el flujo de trabajo del prototipo, integrando conexión de sólo lectura, introspección del esquema, interpretación de metadatos mediante un LLM, validación humana y ejecución controlada del proceso ETL.
3. Desarrollar una aplicación web que permita obtener los metadatos de la fuente relacional y generar propuestas supervisadas de modelo dimensional, KPIs y plan ETL mediante inteligencia artificial.
4. Implementar un proceso ETL trazable que construya y cargue un datamart de ventas desde una base destino vacía y que publique KPIs, visualizaciones, hallazgos analíticos explicables y reportes fieles a la selección autorizada.
5. Validar la exactitud, reproducibilidad, calidad semántica y utilidad del prototipo mediante consultas de referencia, conciliación OLTP--datamart, reejecución determinística de la propuesta aprobada, pruebas de usabilidad y juicio de expertos.

## Incluido por el anteproyecto

- Una conexión SQL Server parametrizable desde la web y una sola fuente activa, validada con AdventureWorks; la interfaz interna permite añadir adaptadores futuros sin implementarlos ahora.
- Credenciales de fuente y LLM ingresadas desde la plataforma y almacenadas mediante referencia cifrada, sin exposición posterior.
- Introspección de tablas, columnas, tipos, claves primarias, claves foráneas y relaciones declaradas.
- Metadatos estructurados enviados por bloques a un LLM para interpretar nombres técnicos en inglés y generar conceptos comprensibles en español sin inventar referencias.
- Solicitud guiada en español y descubrimiento dinámico del alcance técnico, con explorador de sólo lectura para trazabilidad.
- Aprobación humana del significado de negocio y validación determinística antes de ejecutar SQL o transformaciones.
- Datamart PostgreSQL con `fact_ventas`, `dim_fecha`, `dim_producto`, `dim_cliente` y `dim_territorio`.
- ETL de carga completa con uniones simples, fechas/tipos, nulos e importes.
- Una cantidad variable de KPIs sugeridos por IA y calculados mediante recetas controladas, visualizaciones profesionales, hallazgos explicables, copiloto contextual y exportaciones PDF/Excel.
- Datos sintéticos únicamente para pruebas controladas y valores faltantes.

## Excluido por el anteproyecto

- Implementación funcional de múltiples motores, fuentes simultáneas, alta disponibilidad y despliegue empresarial; la interfaz queda preparada para adaptadores futuros.
- CDC, cargas incrementales y dimensiones lentamente cambiantes complejas.
- Pronóstico de ventas y selección de modelos predictivos. El tutor retiró este componente porque el problema de investigación es la construcción semiautomatizada y supervisada del datamart, no el pronóstico.
- SQL del LLM ejecutado sin revisión humana.
- Programador dedicado a escribir consultas para cada solicitud o selección técnica obligatoria de tablas por parte del gerente.
- Datos productivos de terceros y operación continua posterior a la demostración.
- Multiusuario avanzado y permisos granulares dentro del dashboard.

## Aclaración sobre el módulo de seguridad

El anexo institucional exige evidencia de un módulo de seguridad, parámetros, negocio y reportes. Además, la decisión técnica del equipo exige RBAC con usuarios, roles, permisos y menús por rol. Esto no convierte el prototipo en una plataforma multiusuario avanzada: se implementará un RBAC mínimo, controlado y suficiente para la demostración académica.

En esta fase sólo existe su límite modular y la documentación del contrato. La implementación funcional se realizará en una migración y entrega posteriores.

## Aclaración sobre el LLM configurable

El anteproyecto requiere un LLM que proponga artefactos BI, siempre con validación determinística y aprobación humana. Para evitar depender de un único proveedor, la plataforma permite elegir una sola conexión activa entre Gemini Cloud, Groq Cloud, Qwen Cloud y Ollama local. Groq se integra mediante su endpoint compatible con OpenAI y el modelo recomendado `openai/gpt-oss-120b`; las credenciales cloud se registran o reemplazan desde la web y se conservan cifradas, sin editar `.env` durante la operación ordinaria. Esta parametrización no permite enviar datos crudos ni ejecutar SQL del modelo.

## Objetivo de esta fase

- Repositorio y flujo Git preparados.
- Frontend y backend ejecutados íntegramente con Docker.
- Configuración reproducible y sin secretos versionados.
- PostgreSQL interno/datamart y SQL Server externo configurables.
- Endpoints de salud, OpenAPI y pantalla técnica inicial.
- CI/CD preparado en GitHub Actions.
- Ningún módulo de negocio implementado todavía.

## Límite aprobado para especificar el Sprint 3

Sprint 3 cubre el catálogo web de conexiones, secretos cifrados, el adaptador SQL Server, introspección determinística, solicitud guiada de negocio, interpretación dinámica del inglés al español, descubrimiento del alcance de ventas, exploración técnica opcional y generación de una propuesta BI estructurada por el LLM activo. Las preguntas y periodicidades se administran por dominio con permisos propios; el objetivo se escribe por análisis. Las dimensiones, hechos, medidas, KPIs y plan ETL no se predefinen en el catálogo: los propone la IA desde los metadatos, FastAPI valida las referencias contra una instantánea inmutable y una persona autorizada supervisa la decisión. El gerente no edita archivos, selecciona tablas ni escribe SQL en el recorrido principal.

La creación física del datamart, generación determinística de consultas, ejecución del ETL, KPIs calculados, visualizaciones y hallazgos permanecen fuera de Sprint 3. La propuesta aprobada será la entrada controlada del Sprint 4, donde un motor construido una sola vez deberá materializarla sin intervención de un programador por análisis.

Antes de implementar Sprint 4 se definió el contrato `sales-kpi-v1`, no un catálogo fijo: el LLM propondrá una cantidad variable de KPI según la necesidad, preguntas, periodicidad y metadatos comprobados. FastAPI calculará únicamente los KPI cuya receta declarativa, medidas, relaciones y filtros sean válidos, y los contrastará con AdventureWorks OLTP. Para la demostración final se seleccionarán y validarán al menos cinco KPI sugeridos por IA; esa meta no obliga a que cada propuesta contenga cinco ni a que repita indicadores. Esta precisión no convierte al LLM en ejecutor de fórmulas. Véase `docs/specs/SPR-04-02-kpis-controlados-y-calculables.md`.

La ejecución y validación de Sprint 4 seguirá una experiencia profesional para el analista BI: elegir propuesta, revisar indicadores, confirmar, materializar y validar. El recorrido preservará contexto, trazabilidad, recuperación y accesibilidad, pero no expondrá SQL ni metadatos técnicos como paso obligatorio. Véase `docs/specs/SPR-04-03-ui-ux-materializacion-y-validacion.md`.

Sprint 4 incorpora también una capa semántica española dinámica. Los nombres técnicos ingleses se explican sin sustituirlos y las categorías aptas de baja cardinalidad pueden recibir una etiqueta española separada. El dato original permanece disponible para conciliación; no se envían al LLM identificadores, nombres de personas, direcciones, texto libre, credenciales, filas completas ni columnas de alta cardinalidad. Los contenidos ya españoles se conservan. La limpieza, las columnas derivadas y la interpretación se ejecutan mediante operaciones tipadas, versionadas y supervisadas conforme a `docs/specs/SPR-04-04-limpieza-y-transformaciones-controladas.md`.

Al cierre del Sprint 4, la propuesta 52 originó la ejecución 6: cinco tablas, 121317 filas de origen y destino sin diferencia, seis KPI conciliados, etiquetas territoriales españolas publicadas con decisión humana y moneda USD comprobada desde la fuente. El expediente permanece recuperable y una selección idéntica no puede materializarse nuevamente por error.

Sprint 5 corrigió la identidad descriptiva de clientes mediante resolución relacional general, sin depender del nombre literal de una tabla. La propuesta 54 originó la ejecución 7, que conservó las 121317 líneas conciliadas y materializó 19820 clientes con `nombre_cliente` y `tipo_cliente`: 19119 personas y 701 organizaciones, sin etiquetas vacías. Sobre este expediente se publicaron vista ejecutiva y analítica, filtros, KPI variables, cuatro visualizaciones para el analista, hallazgos determinísticos, copiloto conversacional con datos agregados y reportes PDF/Excel fieles a la vista.

### Decisión de alcance sobre pronósticos

El 25 de septiembre de 2026 el tutor, responsable académico del proyecto, retiró el pronóstico mensual, MAPE y RMSE del alcance. La decisión evita mezclar la validación de construcción y calidad de un datamart con un problema predictivo distinto que requeriría hipótesis, tratamiento temporal, entrenamiento y evaluación propios. No se presenta como trabajo fallido ni pendiente: es una modificación controlada del anteproyecto y se conserva en especificaciones, bitácora, arquitectura, manual e informe del Sprint 5.

La validación se construye de forma acumulativa según `docs/validation-plan.md`. Sprint 3 comprueba integridad de la instantánea, referencias, contrato y reejecución determinística. Sprint 4 concilia cantidades, pedidos, unidades e importes OLTP--datamart. Sprint 5 agrega cobertura descriptiva, identidad de entidades, lectura analítica, seguridad del copiloto y fidelidad de exportaciones. Permanecen como cierre académico el contraste secundario cuando exista equivalencia semántica documentada, pruebas formales de usabilidad y juicio de expertos.
