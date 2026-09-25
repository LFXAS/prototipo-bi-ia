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
- `frontend-delivery`: perfil opcional `delivery`; sirve con Nginx el frontend compilado en el puerto 8080 y comparte el backend y las bases de desarrollo. Permite validar el artefacto web sin reemplazar contenedores.
- `backend`: FastAPI con recarga en desarrollo; Uvicorn sin recarga y usuario no privilegiado en producción. El servicio `migrate` aplica Alembic antes de iniciar la API.
- `postgres`: instancia aislada del proyecto, con esquemas `app` y `mart` inicializados en un volumen nombrado.
- `sqlserver`: instancia aislada del proyecto; descarga y restaura AdventureWorks de forma idempotente en un volumen nombrado.
- `ollama`: perfil opcional `local-llm`; mantiene modelos locales en el volumen nombrado `ollama_models`, se comunica sólo dentro de la red Compose y no publica un puerto en el host.

El volumen nombrado `secret_key_data` conserva la raíz criptográfica local generada automáticamente. No contiene configuraciones de negocio, no se versiona y permanece separado de PostgreSQL; el backend lo usa únicamente para cifrar y descifrar secretos autorizados en memoria.

## Modos de ejecución

1. **Desarrollo:** `compose.yaml` inicia Vite, FastAPI y las dos bases bajo `bi-ia-prototype`.
2. **Vista local de entrega:** el perfil `delivery` añade Nginx al mismo proyecto; no duplica datos ni detiene Vite.
3. **Entrega completa:** `compose.release.yaml` consume las cinco imágenes GHCR bajo `bi-ia-prototype-release`, con puertos y volúmenes distintos. Puede ejecutarse al mismo tiempo que desarrollo si el equipo dispone de memoria suficiente.
4. **LLM local opcional:** el perfil `local-llm` añade Ollama al ambiente de desarrollo. No se activa con `make up`, no forma parte de la entrega GHCR y no descarga modelos en CI.

Las ramas no representan servidores. `develop` integra cambios y `main` identifica código publicable; CI usa contenedores temporales y CD convierte `main` o una etiqueta `v*` en imágenes versionadas. El despliegue conserva una etiqueta explícita y no comparte volúmenes entre ambientes.

## Despliegue académico propuesto

Para completar DevOps se propone una VM Linux x64 en Azure for Students. El diseño usa una sola entrega remota para controlar consumo: desarrollo permanece local, CI crea contenedores efímeros y la VM ejecuta únicamente una etiqueta aprobada de GHCR. GitHub Actions accederá a Azure con OIDC y permisos limitados al recurso; la VM realizará `pull`, `up -d` y comprobaciones de salud. La infraestructura se añadirá como código después de activar la suscripción y fijar región, presupuesto y nombres.

No se recomienda una VM ARM para este conjunto porque SQL Server para Linux requiere un procesador compatible con x64. La capacidad objetivo para la demostración es 2 vCPU y 8 GiB, con apagado o desasignación fuera de las ventanas de prueba.

## Límites modulares previstos

- `system`: salud y diagnóstico técnico mínimo.
- `security`: autenticación y RBAC mínimo.
- `parameters`: parámetros del prototipo, catálogo web de conexiones, referencias a secretos cifrados y configuración del proveedor LLM activo.
- `metadata`: introspección determinística mediante la interfaz del conector activo; SQL Server es el primer adaptador.
- `copilot`: solicitud guiada de negocio y propuestas estructuradas del LLM, nunca ejecución directa.
- `etl`: constructor determinístico, vista previa, validación, ejecución backend y trazabilidad de cargas; no depende de SQL escrito por cada usuario.
- `analytics`: KPIs, filtros, gráficos, hallazgos determinísticos y conversación contextual sobre agregados conciliados.
- `reports`: exportaciones PDF/Excel operativas y evidencias académicas.

Al cierre local del Sprint 5, `system`, `security`, `parameters`, `metadata`, `copilot`, `etl`, `analytics` y `reports` contienen comportamiento. `etl` incluye selección, compilación, materialización, conciliación, resolución descriptiva y expedientes recuperables. `analytics` consulta exclusivamente ejecuciones conciliadas; `reports` reconstruye en servidor la selección autorizada. El límite `forecasting` se retiró por decisión de alcance del tutor: el proyecto demuestra construcción supervisada de datamarts y analítica explicable, no predicción.

## Contrato de evolución (SDD)

Desde el Sprint 2, cada módulo sólo incorpora capacidad funcional a partir de una especificación versionada en `docs/specs/`. La especificación define el contrato funcional y de datos; la arquitectura, el ADR cuando exista una decisión duradera, las pruebas y el PR demuestran cómo se cumplió. Este control evita que una propuesta del LLM, un cambio de esquema o una integración externa aparezcan sin aprobación humana, criterios verificables y trazabilidad.

## RBAC previsto

Entidades implementadas hasta el cierre local del Sprint 5: `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `menus`, `menu_permissions`, `audit_events`, `parameters`, `llm_configurations`, `secrets`, `data_connections`, `metadata_snapshots`, `bi_proposals`, `semantic_advice` y `etl_executions`, todas bajo el esquema `app`. `parameters` conserva tipo, módulo, valor predeterminado y rango; `metadata_snapshots` conserva el documento canónico JSONB, su hash, totales y actor histórico; `bi_proposals` conserva solicitud, perfil, mapa semántico, alcance, propuesta, validación, proveedor/modelo y decisión humana; `semantic_advice` registra consultas contextuales; `etl_executions` fija selección, plan, huellas, validación, métricas y responsable. El chat analítico no almacena conversaciones completas: cada consulta deja una huella y contexto mínimo en auditoría.

Reglas arquitectónicas:

1. React puede ocultar opciones, pero FastAPI autoriza cada operación.
2. Denegar por defecto cuando un permiso no esté asignado.
3. Los tokens no almacenan secretos ni reemplazan el estado activo del usuario.
4. Las aprobaciones de propuestas y las futuras ejecuciones quedan auditadas.
5. Menús y permisos comparten códigos estables, no nombres visibles.
6. La cuenta inicial, su rol de recuperación, los permisos mínimos y los menús base quedan protegidos en datos persistidos; el sistema rechaza su desactivación para conservar una vía de administración.
7. Los permisos y menús técnicos se incorporan con un módulo aprobado y su migración/versionamiento, nunca como texto libre en la pantalla administrativa.

## Contrato UI/UX responsive

Desde Sprint 2, cada módulo que incorpore interfaz se integra en un cascarón React reutilizable con encabezado, navegación autorizada, contenido principal y avisos globales. La interfaz debe ser utilizable en móvil desde 320 px, tableta, escritorio y pantalla amplia; no puede depender de un tamaño fijo ni generar desplazamiento horizontal involuntario.

Los menús son una representación de permisos ya autorizados por FastAPI. En escritorio pueden permanecer visibles; en móvil deben abrirse y cerrarse con teclado o táctil. Formularios, tablas y acciones administrativas definen estados de carga, vacío, éxito, error, sesión vencida y acceso denegado. La accesibilidad mínima incluye foco visible, etiquetas de campos, mensajes que no dependan sólo del color y contraste suficiente para lectura.

### Perfiles de uso

La administración técnica configura desde la web fuente, credenciales, proveedor LLM y permisos. El gerente comercial aporta objetivos, preguntas y criterios de utilidad y consume posteriormente los resultados. El analista BI o responsable de datos es el usuario operativo del asistente: selecciona el dominio habilitado, registra la necesidad, revisa conceptos, personaliza decisiones de negocio ya verificadas y aprueba o rechaza la propuesta sin escribir SQL. Las programadoras mantienen el motor y sus plantillas, pero no intervienen en cada análisis de operación.

## Contrato de configuración LLM

El módulo `parameters` conserva una única configuración LLM activa con tipo de proveedor, URL base, modelo, nivel de razonamiento controlado, límites y referencia opaca de credencial. La corrección final del Sprint 2 incorpora un almacén cifrado para registrar o reemplazar la clave desde la web. PostgreSQL conserva exclusivamente el valor cifrado; React y auditoría no reciben el secreto. `GEMINI_API_KEY` y `DASHSCOPE_API_KEY` ya no forman parte de la configuración operativa. Un cambio de proveedor, URL, modelo o razonamiento invalida la prueba anterior para impedir que el copiloto use una combinación no verificada.

La raíz criptográfica se genera automáticamente en el primer arranque local y se conserva con permisos restrictivos en un volumen Docker separado de PostgreSQL. Una instalación productiva deberá sustituir ese proveedor por un gestor de secretos externo. Puertos, redes, imágenes, volúmenes y credenciales internas siguen siendo infraestructura de despliegue y no se modifican desde la aplicación.

FastAPI encapsula las diferencias de cada servicio en adaptadores internos y sólo habilita uno a la vez. La prueba de conexión realiza una generación mínima, sin datos de negocio ni conservación de la respuesta. Groq Cloud usa exclusivamente `https://api.groq.com/openai/v1`, recomienda `openai/gpt-oss-120b`, convierte el nivel común mínimo a `low` y usa JSON Schema estricto para los contratos BI. El perfil Docker opcional `local-llm` inicia Ollama aislado de la red pública; `qwen2.5:3b` es el modelo local inicial recomendado por su equilibrio entre agilidad, uso de memoria y respuestas directas en español. `qwen3:4b` es una alternativa de mayor capacidad, pero puede tardar más por el razonamiento interno. La prueba verifica tanto el servicio como que el modelo configurado esté descargado. Gemini, Groq y Qwen Cloud conservan la elección de modelo en configuración porque sus catálogos y cuotas pueden cambiar.

El módulo `copilot` consume este contrato mediante una interfaz interna y es el único que puede solicitar interpretaciones de metadatos o propuestas BI; ningún SQL asistido por IA se ejecuta automáticamente. La decisión se detalla en [`decisions/0002-configuracion-proveedor-llm.md`](decisions/0002-configuracion-proveedor-llm.md).

## Contrato de Sprint 3

Sprint 3 separa configuración, introspección y razonamiento asistido. La administración puede registrar desde la web una conexión `sqlserver`, cifrar su contraseña, comprobar conectividad y ausencia de permisos de escritura, y dejar una sola fuente activa. El módulo `metadata` consulta catálogos del conector activo, normaliza una instantánea inmutable, calcula su hash y reutiliza la captura vigente cuando la estructura no cambió. El explorador consulta exclusivamente PostgreSQL y no vuelve a leer filas ni metadatos de la fuente por cada búsqueda.

El módulo `copilot` calcula primero un catálogo de dominios y capacidades desde la instantánea vigente. El frontend consume ese contrato y no conserva preguntas ni dimensiones de AdventureWorks codificadas. El perfil `ventas` es el único habilitado; incorporar otro dominio exige registrar sus capacidades y validadores.

La orientación funcional del perfil de ventas se desacopla de sus reglas mediante el catálogo estructurado interno `COPILOT_SALES_NEEDS_CATALOG`, administrado exclusivamente por la API y pantalla **Catálogo analítico**. Una persona autorizada puede crear, editar, habilitar o retirar preguntas de negocio y seleccionar varias periodicidades soportadas. El objetivo se escribe para cada análisis y las dimensiones no forman parte del catálogo: el LLM las propone desde los metadatos, FastAPI comprueba sus referencias y el analista las supervisa. Un nuevo dominio o motor sigue requiriendo un perfil o adaptador implementado y probado.

Después, `copilot` recibe una solicitud guiada de negocio y procesa la instantánea en bloques compactos. El LLM interpreta dinámicamente nombres técnicos en inglés u otro idioma, propone conceptos y explicaciones de negocio en español y conserva las referencias originales. En una segunda llamada toma decisiones analíticas compactas —hecho, medidas, dimensiones y KPI— restringidas por un esquema JSON derivado del alcance. FastAPI descarta referencias inexistentes y expande esas decisiones con PK, FK, atributos, reglas de calidad y operaciones ETL determinísticas. Así un modelo local pequeño no debe repetir información mecánica y queda explícita la frontera entre propuesta de IA y control de la aplicación. No se utiliza un glosario codificado exclusivamente para AdventureWorks.

FastAPI valida que todas las tablas, columnas, claves, relaciones y operaciones propuestas existan o pertenezcan a catálogos aprobados. El analista puede derivar una versión ajustando únicamente resumen, granularidad, dimensiones, medidas, agregaciones y KPIs ya verificados; el backend vuelve a validar, conserva el vínculo de origen y audita el cambio. Sólo después un permiso independiente permite aprobar o rechazar el significado de negocio. Una aprobación no genera ni ejecuta SQL: conserva una entrada inmutable para el módulo `etl` de Sprint 4. Ese módulo preseleccionará la propuesta aprobada compatible más reciente, exigirá confirmación explícita, permitirá comparar otras aprobadas y fijará el `proposal_id` en cada ejecución. Después construirá consultas parametrizadas mediante operaciones tipadas y plantillas autorizadas, presentará una vista previa y las ejecutará desde el backend con permisos mínimos. Este límite se detalla en [`decisions/0003-metadatos-y-propuesta-bi-supervisada.md`](decisions/0003-metadatos-y-propuesta-bi-supervisada.md) y [`specs/SPR-04-01-seleccion-propuesta-y-validacion-etl.md`](specs/SPR-04-01-seleccion-propuesta-y-validacion-etl.md).

Antes de materializar, el módulo `etl` aplica controles de aptitud analítica adicionales a la validación estructural: rechaza dimensiones basadas en tablas puente, claves ambiguas, ausencia de atributos descriptivos y contradicciones entre granularidad y claves del hecho. La capa semántica conserva siempre los nombres y valores originales. Puede agregar etiquetas españolas para metadatos y categorías no sensibles de baja cardinalidad; omite automáticamente identificadores, datos personales, texto libre y valores de alta cardinalidad. Si el contenido ya está en español no lo reinterpreta. Si el proveedor falla, la carga numérica permanece válida y el analista puede reintentar únicamente la interpretación con otro proveedor activo, sin repetir el ETL. Cada mapeo queda versionado y auditado.

### Extensibilidad por motor y dominio

La arquitectura no está cerrada a AdventureWorks ni a SQL Server. La instantánea usa un contrato canónico independiente del motor y registra `connector_code`; un registro interno despacha la introspección al adaptador habilitado. SQL Server es la implementación validada. Incorporar MySQL, PostgreSQL u otro motor exige implementar su prueba de sólo lectura, lectura de catálogo, normalización de tipos y relaciones, campos web y pruebas; después puede habilitarse como opción parametrizable sin cambiar el contrato del copiloto.

El razonamiento también se aísla por perfiles de dominio. Cada perfil declara código, preguntas, conceptos, dimensiones, periodicidades, destinos, prompt contractual y reglas determinísticas. `GET /copilot/catalog` cruza estas definiciones con los términos presentes en la instantánea y devuelve disponibilidad, causa y evidencia. Sprint 3 habilita y valida únicamente `ventas`. Un futuro datamart de inventario deberá incorporar el perfil `inventario`, sus reglas de existencias y movimientos y un conjunto de referencia antes de ofrecerse en la web. Autenticación, secretos, auditoría, versionado, flujo de revisión y adaptadores LLM se reutilizan.

La validación es un expediente acumulativo visible. En Sprint 3, `POST /copilot/proposals/{id}/verify` comprueba la huella de la instantánea, vuelve a ejecutar el validador y reconstruye la propuesta desde `ai_decisions` sin invocar al LLM. Sprint 4 agrega `app.etl_executions`: concilia conteos, unidades, pedidos e importes entre AdventureWorks OLTP y el datamart, conserva KPI y permite revisión semántica posterior sin repetir la carga. Sprint 5 añade cobertura de etiquetas descriptivas, paneles sobre agregados conciliados, chat acotado y reportes reconstruidos en servidor. La igualdad de hashes demuestra reproducibilidad del artefacto aprobado, no determinismo del proveedor probabilístico; el juicio de expertos se agrega en el cierre académico.

La comparación considera la versión del motor que creó el artefacto. En la versión vigente, una diferencia de huella o validación es bloqueante. Para una propuesta histórica, una diferencia causada únicamente por evolución del motor se muestra como advertencia de compatibilidad y no retira por sí sola una aprobación sin errores. Una aprobación previamente retirada puede restaurarse sólo después de superar los controles actuales, confirmar advertencias y registrar una justificación auditada.

Parametrizar significa seleccionar entre capacidades implementadas y validadas; no convertir un nombre libre en soporte automático. Esta restricción evita declarar portabilidad ficticia y permite ampliar el prototipo con evidencia técnica.

## Datos

PostgreSQL alojará dos responsabilidades lógicamente separadas:

- esquema `app`: seguridad, parámetros, auditoría y ejecuciones;
- esquema `mart`: hechos y dimensiones analíticas.

La separación física en bases distintas no es necesaria para la prueba de concepto y puede revisarse si las mediciones lo justifican.

### Evolución reproducible de PostgreSQL

Los volúmenes Docker contienen estado local y no se comparten por GitHub. Cada cambio de esquema se incorpora mediante una migración Alembic inmutable y versionada. Después de aplicar las migraciones, el servicio Compose `seed` ejecuta el catálogo base aprobado de manera idempotente: permisos, menús, rol administrador y cuenta inicial de recuperación.

El sembrado sólo crea o actualiza registros protegidos del sistema y no duplica catálogos. Tampoco distribuye cuentas temporales, eventos de auditoría, claves, tokens, configuraciones LLM ni datos de negocio. Los datos demostrativos futuros deberán declararse como semillas opcionales, anonimizadas y aprobadas por su especificación; nunca como copias de un volumen local.
