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
- `analytics`: KPIs, gráficos e insights.
- `forecasting`: regresión lineal y métricas MAPE/RMSE.
- `reports`: evidencias y reportes académicos.

En el Sprint 2, `system`, `security` y `parameters` contienen comportamiento. Los demás módulos siguen siendo límites arquitectónicos reservados para sprints posteriores.

## Contrato de evolución (SDD)

Desde el Sprint 2, cada módulo sólo incorpora capacidad funcional a partir de una especificación versionada en `docs/specs/`. La especificación define el contrato funcional y de datos; la arquitectura, el ADR cuando exista una decisión duradera, las pruebas y el PR demuestran cómo se cumplió. Este control evita que una propuesta del LLM, un cambio de esquema o una integración externa aparezcan sin aprobación humana, criterios verificables y trazabilidad.

## RBAC previsto

Entidades implementadas hasta el primer incremento del Sprint 3: `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `menus`, `menu_permissions`, `audit_events`, `parameters`, `llm_configurations`, `secrets` y `data_connections`, todas bajo el esquema `app`. `parameters` ya conserva tipo, módulo, valor predeterminado y rango. Las siguientes migraciones del Sprint 3 añadirán `metadata_snapshots` y `bi_proposals`.

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

La administración técnica configura desde la web fuente, credenciales, proveedor LLM y permisos. El gerente comercial aporta objetivos, preguntas y criterios de utilidad y consume posteriormente los resultados. El analista BI o responsable de datos es el usuario operativo del asistente: registra la necesidad, revisa conceptos y detalles cuando corresponda, resuelve ambigüedades y aprueba o rechaza la propuesta sin escribir SQL. Las programadoras mantienen el motor y sus plantillas, pero no intervienen en cada análisis de operación.

## Contrato de configuración LLM

El módulo `parameters` conserva una única configuración LLM activa con tipo de proveedor, URL base, modelo, límites y referencia opaca de credencial. La corrección final del Sprint 2 incorpora un almacén cifrado para registrar o reemplazar la clave desde la web. PostgreSQL conserva exclusivamente el valor cifrado; React y auditoría no reciben el secreto. `GEMINI_API_KEY` y `DASHSCOPE_API_KEY` ya no forman parte de la configuración operativa.

La raíz criptográfica se genera automáticamente en el primer arranque local y se conserva con permisos restrictivos en un volumen Docker separado de PostgreSQL. Una instalación productiva deberá sustituir ese proveedor por un gestor de secretos externo. Puertos, redes, imágenes, volúmenes y credenciales internas siguen siendo infraestructura de despliegue y no se modifican desde la aplicación.

FastAPI encapsula las diferencias de cada servicio en adaptadores internos y sólo habilita uno a la vez. En Sprint 2 permite probar de forma real y limitada la conexión configurada, sin enviar datos de negocio ni conservar contenido de respuesta. El perfil Docker opcional `local-llm` inicia Ollama aislado de la red pública; `qwen2.5:3b` es el modelo local inicial recomendado por su equilibrio entre agilidad, uso de memoria y respuestas directas en español. `qwen3:4b` es una alternativa de mayor capacidad, pero puede tardar más por el razonamiento interno. La prueba verifica tanto el servicio como que el modelo configurado esté descargado. Gemini y Qwen Cloud conservan la elección de modelo en configuración porque su catálogo y sus cuotas pueden cambiar.

El módulo `copilot` posterior consumirá este contrato mediante una interfaz interna y será el único que pueda solicitar propuestas sobre metadatos o planes BI; ningún SQL asistido por IA se ejecutará automáticamente. La decisión se detalla en [`decisions/0002-configuracion-proveedor-llm.md`](decisions/0002-configuracion-proveedor-llm.md).

## Contrato de Sprint 3

Sprint 3 separa configuración, introspección y razonamiento asistido. La administración ya puede registrar desde la web una conexión `sqlserver`, cifrar su contraseña, comprobar conectividad y ausencia de permisos de escritura, y dejar una sola fuente activa; AdventureWorks valida este recorrido. El siguiente incremento del módulo `metadata` consultará el conector activo, normalizará una instantánea inmutable y calculará su hash.

El módulo `copilot` recibe una solicitud guiada de negocio y procesa la instantánea en bloques compactos. El LLM interpreta dinámicamente nombres técnicos en inglés u otro idioma, propone conceptos y explicaciones de negocio en español y conserva las referencias originales. FastAPI descarta cualquier tabla, columna o relación que no exista antes de construir el paquete dimensional final. No se utiliza un glosario codificado exclusivamente para AdventureWorks.

FastAPI valida que todas las tablas, columnas, claves, relaciones y operaciones propuestas existan o pertenezcan a catálogos aprobados. Sólo después un permiso independiente permite aprobar o rechazar el significado de negocio. Una aprobación no genera ni ejecuta SQL: conserva una entrada inmutable para el módulo `etl` de Sprint 4. Ese módulo deberá construir consultas parametrizadas mediante operaciones tipadas y plantillas autorizadas, presentar una vista previa y ejecutarlas desde el backend con permisos mínimos. Este límite se detalla en [`decisions/0003-metadatos-y-propuesta-bi-supervisada.md`](decisions/0003-metadatos-y-propuesta-bi-supervisada.md).

## Datos

PostgreSQL alojará dos responsabilidades lógicamente separadas:

- esquema `app`: seguridad, parámetros, auditoría y ejecuciones;
- esquema `mart`: hechos y dimensiones analíticas.

La separación física en bases distintas no es necesaria para la prueba de concepto y puede revisarse si las mediciones lo justifican.

### Evolución reproducible de PostgreSQL

Los volúmenes Docker contienen estado local y no se comparten por GitHub. Cada cambio de esquema se incorpora mediante una migración Alembic inmutable y versionada. Después de aplicar las migraciones, el servicio Compose `seed` ejecuta el catálogo base aprobado de manera idempotente: permisos, menús, rol administrador y cuenta inicial de recuperación.

El sembrado sólo crea o actualiza registros protegidos del sistema y no duplica catálogos. Tampoco distribuye cuentas temporales, eventos de auditoría, claves, tokens, configuraciones LLM ni datos de negocio. Los datos demostrativos futuros deberán declararse como semillas opcionales, anonimizadas y aprobadas por su especificación; nunca como copias de un volumen local.
