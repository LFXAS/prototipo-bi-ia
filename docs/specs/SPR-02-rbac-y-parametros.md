# SPR-02: seguridad RBAC, parámetros, configuración LLM y experiencia base responsive

- Estado: borrador
- Sprint: SPR-02
- Responsable de especificación: equipo del proyecto
- Rama prevista: `feature/rbac-y-parametros`
- Fecha de creación: 2026-09-01
- Última revisión funcional: 2026-09-04
- PR de implementación: pendiente

## 1. Problema y objetivo

El prototipo necesita un módulo mínimo de seguridad exigido académicamente, un mecanismo auditable para parametrizar conexiones y la futura configuración del LLM que asistirá el proceso BI. El objetivo es que un administrador pueda gestionar usuarios, roles, permisos, menús y parámetros aprobados, mientras FastAPI autoriza todas las operaciones relevantes.

React debe presentar estas capacidades mediante una interfaz clara, accesible y adaptable. El diseño visual nunca sustituye los controles de seguridad del backend: sólo ayuda a que cada persona entienda qué puede hacer y complete su tarea sin errores evitables.

## 2. Alcance y exclusiones

- Incluido: migración inicial PostgreSQL, usuarios, roles, permisos, asignaciones, menús, auditoría, autenticación y autorización mínima; parámetros de conexión sin secretos visibles en la interfaz; prueba controlada de acceso lector a AdventureWorks; configuración de un proveedor LLM activo mediante parámetros no secretos; cascarón de aplicación responsive, navegación por permisos, vistas de acceso y administración, componentes visuales reutilizables y estados de carga, vacío, error y acceso denegado.
- Excluido: SSO institucional, recuperación de contraseña por correo, administración avanzada multiempresa, conectores universales, varios proveedores LLM ejecutándose simultáneamente, generación de propuestas BI por LLM con metadatos de negocio, introspección automática, ETL, dashboard BI completo, temas visuales configurables por usuario y una biblioteca de diseño independiente.

## 3. Actores, flujo y reglas

- Administrador: crea o desactiva usuarios, asigna roles y permisos, administra menús y parámetros permitidos.
- Usuario autenticado: sólo ve menús autorizados y sólo puede llamar endpoints cuyo permiso posea.
- Persona no autenticada: al abrir una ruta protegida se le dirige al inicio de sesión; no ve datos, menús administrativos ni detalles internos del error.
- Backend: deniega por defecto. Ocultar un menú en React nunca sustituye la autorización del backend.
- Fuente SQL Server: se usa exclusivamente con la cuenta lectora; ningún endpoint permitirá ejecutar escritura en AdventureWorks.
- Configuración LLM: el administrador autorizado mantiene una única configuración activa; elige uno de los tres proveedores iniciales aprobados, define el modelo y límites permitidos. La clave se obtiene exclusivamente de una variable de entorno o gestor de secretos identificado por referencia, no de la base ni de la interfaz.

### 3.1 Flujos de experiencia de usuario

1. **Acceso.** La persona ingresa usuario y contraseña. Mientras se valida, el botón queda bloqueado y comunica que la operación está en curso. Si es correcto, llega a la página inicial autorizada y recibe solamente su menú; si falla, ve un mensaje claro sin revelar si el usuario existe.
2. **Navegación autorizada.** El cascarón consulta la sesión y el menú autorizado. En escritorio el menú lateral puede permanecer visible; en tableta se contrae; en móvil se abre mediante un control accesible y se cierra al seleccionar una opción o al volver al contenido.
3. **Administración de usuarios.** El administrador consulta una lista paginable, busca, crea o edita un usuario y confirma acciones sensibles, como desactivar una cuenta. Los cambios exitosos se comunican y se reflejan sin dejar la pantalla en un estado ambiguo.
4. **Administración de roles y permisos.** El administrador asigna roles a usuarios y permisos a roles mediante controles que expliquen su efecto. Antes de guardar se muestra qué cambiará; al guardar se registra auditoría y se actualiza el menú en la próxima obtención de sesión.
5. **Parámetros y conexión.** El administrador visualiza únicamente metadatos permitidos de una conexión. Puede crear o actualizar una configuración aprobada y ejecutar una prueba lectora. La contraseña nunca se vuelve a presentar, ni siquiera parcialmente, y el resultado informa éxito o causa técnica segura.
6. **Configuración LLM.** El administrador con permiso específico configura un único proveedor activo, revisa sus valores no secretos y ejecuta una prueba real, limitada y sin datos del negocio. La prueba confirma conectividad, credencial y disponibilidad del modelo mediante el adaptador correspondiente; no envía metadatos, no propone modelos dimensionales ni ejecuta SQL. Esas capacidades pertenecen al módulo `copilot` posterior.

### 3.2 Reglas de navegación

- La ruta inicial autenticada se determina por el primer menú permitido; si no existe, se muestra una pantalla de cuenta sin módulos asignados con una explicación para solicitar acceso.
- Las rutas deben tener título visible, una ubicación dentro de la navegación y una acción principal inequívoca cuando corresponda.
- La navegación no debe depender sólo de iconos, color, desplazamiento horizontal ni de mantener el cursor sobre un elemento.
- Al cambiar de ruta se conserva el foco lógico en el título principal; cuando se abre un diálogo, el foco queda dentro de él y vuelve al control que lo abrió al cerrarlo.
- Cerrar sesión estará siempre disponible para la persona autenticada y eliminará la sesión local antes de redirigir al acceso.

## 4. Datos, API e interfaz

- Migraciones: `app.users`, `app.roles`, `app.permissions`, `app.user_roles`, `app.role_permissions`, `app.menus`, `app.menu_permissions`, `app.audit_events`, parámetros de conexión y una configuración LLM no secreta.
- API prevista: autenticación, sesión actual, administración mínima RBAC, menú autorizado, prueba de conexión aprobada y administración de configuración LLM. Los contratos devolverán errores consistentes para validación, sesión vencida, falta de permiso, conflicto y fallo controlado de conexión.
- Interfaz prevista: inicio de sesión, página inicial autorizada, pantalla de cuenta sin módulos, administración de usuarios, roles, permisos, menús, parámetros y configuración LLM, además de menú dinámico. No incluye dashboard BI en este sprint.

### 4.1 Parámetro de proveedor LLM

La configuración persistida del proveedor LLM sólo contendrá valores no secretos y validados: `provider_kind`, `base_url`, `model_id`, `timeout_seconds`, `max_output_tokens`, `enabled` y `credential_reference`. Esta última identifica una variable de entorno o secreto de despliegue; no contiene ni permite recuperar la clave real.

El catálogo inicial y cerrado de `provider_kind` es el siguiente. Cada opción se implementará detrás de un adaptador interno de FastAPI, porque su autenticación y contrato de API no son idénticos:

| `provider_kind` | Servicio | Referencia de credencial | Configuración inicial prevista |
|---|---|---|---|
| `gemini` | Gemini API en la nube | `GEMINI_API_KEY` | URL oficial del proveedor y un modelo Gemini Flash disponible para la cuenta. |
| `qwen-cloud` | Qwen mediante Alibaba Cloud Model Studio / DashScope | `DASHSCOPE_API_KEY` | URL oficial de DashScope y un modelo Qwen habilitado para la cuenta. |
| `ollama-local` | Ollama ejecutado localmente en Docker | `none` | URL interna del servicio y `qwen3:4b` como modelo local inicial recomendado. |

La referencia `none` sólo significa que Ollama no suele requerir una clave en la red interna del entorno; no habilita exponer su servicio fuera de la red del proyecto. La interfaz muestra únicamente el tipo elegido, los valores no secretos y si la credencial requerida está disponible; nunca muestra el valor de una clave. Las cuotas, modelos sin costo y condiciones de los servicios cloud pueden cambiar, por lo que no son una garantía funcional ni se codifican en la aplicación.

Sólo existirá una configuración activa en la demostración. Cambiar de proveedor desactiva la configuración anterior de forma auditada; Sprint 2 no ejecutará varios proveedores al mismo tiempo ni balanceará solicitudes. El contrato permite cambiar entre servicio local y nube sin modificar los módulos de metadatos, ETL o analítica. La configuración no habilita URL arbitrarias sin validación: el backend verificará tipo, URL permitida para el adaptador, modelo, límites de tiempo y autorización antes de usarla.

La prueba de conexión se ejecuta desde FastAPI, nunca desde React. Cada adaptador realiza una comprobación de disponibilidad compatible con Gemini, Qwen Cloud u Ollama y, cuando corresponda, una solicitud mínima con límite estricto de salida y sin contexto del proyecto. Sólo se conservan el resultado, fecha, duración, proveedor/modelo y causa segura de fallo; el contenido de una respuesta de prueba se descarta. El perfil Docker de Ollama se añadirá cuando se implemente este requisito; no se crea en esta etapa de especificación.

### 4.2 Cascarón visual y adaptación a pantallas

La aplicación se construirá como un cascarón reutilizable: encabezado, navegación, área principal y avisos globales. No se diseñarán pantallas independientes con estilos incompatibles. El contenido debe poder ampliarse en los sprints de metadatos, ETL, analítica y reportes sin reemplazar esta estructura.

| Contexto | Ancho de referencia | Comportamiento esperado |
|---|---:|---|
| Móvil | 320--767 px | Una columna, márgenes legibles, controles táctiles, menú lateral oculto y activable, tablas convertidas en tarjetas o con columnas esenciales. |
| Tableta | 768--1023 px | Contenido flexible, navegación contraída y formularios que pueden usar dos columnas sólo si conservan legibilidad. |
| Escritorio | desde 1024 px | Navegación lateral disponible, área principal centrada y tablas administrativas completas sin depender de un ancho fijo de monitor. |
| Pantalla amplia | desde 1440 px | El contenido conserva un ancho máximo legible; el espacio adicional no agranda indefinidamente textos, formularios ni tablas. |

Los valores son umbrales de prueba, no restricciones rígidas. El criterio real es que no exista desplazamiento horizontal involuntario a partir de 320 px, que los controles sean utilizables con táctil y que la información prioritaria permanezca visible.

### 4.3 Componentes reutilizables previstos

| Componente | Uso y comportamiento mínimo |
|---|---|
| Cascarón de aplicación | Encabezado, navegación autorizada, zona principal y cierre de sesión. Debe adaptarse entre menú lateral visible, contraído y desplegable. |
| Formulario y campo | Etiqueta persistente, ayuda opcional, validación junto al campo y resumen de errores cuando aplique. No usar sólo un marcador de posición como etiqueta. |
| Botón y acción destructiva | Estado normal, foco visible, ocupado y deshabilitado. Las acciones de desactivar o borrar requieren confirmación explícita. |
| Tabla administrativa | Encabezados claros, estado vacío, carga y error. En móvil se priorizan datos esenciales mediante tarjetas o una presentación equivalente. |
| Diálogo de confirmación | Nombre de la acción, consecuencia, opción de cancelar, foco administrado y cierre con teclado. |
| Aviso o notificación | Comunica éxito, error o información sin depender exclusivamente del color; los errores que bloquean una acción permanecen visibles. |
| Pantallas de estado | Carga, sin resultados, acceso denegado, sesión vencida y error técnico seguro, con una siguiente acción comprensible. |

### 4.4 Accesibilidad y lenguaje

- El idioma visible inicial es español y los mensajes deben explicar qué ocurrió y qué puede hacer la persona después.
- Todo control interactivo es alcanzable con teclado y tiene foco visible.
- Los campos tienen etiquetas asociadas; los mensajes de error se anuncian de forma accesible y no dependen sólo de color o iconos.
- La combinación de texto y fondo debe tener contraste suficiente para lectura normal; se verificará con una herramienta de contraste antes del cierre del sprint.
- La interfaz respeta la preferencia de reducción de movimiento cuando se incorporen transiciones; las animaciones no deben ser necesarias para comprender ni completar una tarea.

## 5. Seguridad y auditoría

- Contraseñas con Argon2 o bcrypt; nunca texto plano.
- JWT de vida limitada; secretos sólo por variables de entorno.
- Autorización por códigos estables de permiso en FastAPI.
- Auditoría de inicio de sesión, cambios de roles/permisos, cambios de parámetros y pruebas de conexión.
- Los secretos de conexión no se devuelven por API ni se registran en texto claro.
- La configuración LLM nunca devuelve ni persiste la clave del proveedor. Las referencias de credencial permitidas se validan contra un catálogo controlado de variables de entorno.
- La URL y los límites configurados para un proveedor LLM se validan antes de persistirse; en el futuro, las llamadas sólo podrán ejecutarse desde el backend y con tiempos máximos definidos.
- La prueba de conexión LLM usa el backend, un tiempo máximo, una respuesta mínima y ningún dato de AdventureWorks, PostgreSQL, usuarios o metadatos. Su resultado queda auditado sin incluir claves ni contenido sensible.
- La interfaz no conserva contraseñas de usuarios ni secretos de conexión fuera del envío estrictamente necesario; los campos sensibles se limpian después de una operación exitosa o cancelada.
- Las respuestas de error visibles no exponen trazas, tokens, cadenas de conexión ni estructura interna de la base.

## 6. Criterios de aceptación verificables

- [ ] Una migración limpia crea todas las tablas RBAC y de parámetros en el esquema `app`.
- [ ] Un usuario con rol autorizado puede iniciar sesión y consultar sólo sus menús.
- [ ] Un usuario sin permiso recibe respuesta de autorización denegada aunque intente llamar el endpoint directamente.
- [ ] La interfaz no muestra menús sin permiso, pero la decisión real se toma en FastAPI.
- [ ] Una prueba de conexión usa el lector de AdventureWorks y no revela secretos.
- [ ] Los cambios administrativos y pruebas de conexión quedan en `audit_events`.
- [ ] Un administrador con permiso específico puede crear, actualizar, activar o desactivar una única configuración LLM no secreta, y cada acción queda en `audit_events`.
- [ ] La API y la interfaz nunca devuelven la clave del proveedor LLM; sólo exponen la referencia de credencial permitida y valores no secretos.
- [ ] La configuración LLM valida el catálogo `gemini`, `qwen-cloud` u `ollama-local`, su URL, modelo y límites permitidos; una prueba real desde FastAPI confirma conectividad y disponibilidad sin enviar datos del negocio.
- [ ] El resultado de la prueba LLM registra estado, fecha, duración y causa segura de fallo, sin claves ni contenido de respuesta; este sprint no ejecuta propuestas BI ni SQL producido por un LLM.
- [ ] Sólo una de las configuraciones Gemini Cloud, Qwen Cloud u Ollama local puede estar activa; cambiarla deja trazabilidad y no modifica la configuración de los demás módulos.
- [ ] Gemini usa exclusivamente la referencia `GEMINI_API_KEY`, Qwen Cloud `DASHSCOPE_API_KEY` y Ollama local `none`; la API sólo informa el estado de disponibilidad de la referencia, nunca su valor.
- [ ] La configuración local admite `qwen3:4b` como modelo inicial recomendado y su prueba se realiza contra la red interna Docker; el perfil de Ollama no se expone públicamente.
- [ ] Una persona no autenticada es dirigida al inicio de sesión al visitar una ruta protegida y el error de acceso no revela información sensible.
- [ ] Una persona autenticada sólo recibe las rutas y los menús asociados a sus permisos; intentar una URL no autorizada muestra una vista de acceso denegado y FastAPI responde con denegación.
- [ ] El inicio de sesión, el menú y las pantallas administrativas son utilizables desde 320 px, 768 px, 1024 px y 1440 px, sin desplazamiento horizontal involuntario ni pérdida de la acción principal.
- [ ] El menú autorizado se muestra de forma lateral en escritorio y puede abrirse/cerrarse con teclado y táctil en móvil; al navegar devuelve el foco al contenido principal.
- [ ] Formularios, tablas, diálogos y avisos cubren estados de carga, vacío, error y éxito, con texto comprensible y foco visible.
- [ ] Cada control relevante tiene etiqueta accesible; los errores no dependen exclusivamente de color; una comprobación de contraste documenta los resultados de las pantallas principales.
- [ ] Pruebas de backend, frontend, migraciones y CI pasan dentro de Docker.

## 7. Plan de pruebas y evidencia

Pruebas unitarias de hash, autorización, validación de parámetros y selección del adaptador LLM; integración con PostgreSQL para migraciones, auditoría y configuración LLM no secreta; pruebas controladas de los adaptadores con dobles de prueba y, cuando una credencial autorizada esté disponible, una evidencia manual sin datos del negocio; pruebas de interfaz para menú, redirección, acceso denegado, formularios y estados; pruebas visuales o manuales documentadas en 320 px, 768 px, 1024 px y 1440 px; una evidencia de CI verde y capturas sin secretos para la tesis. Antes de cerrar el PR se ejecutará `make verify` y los PDF/documentos afectados se regenerarán.

## 8. Riesgos, dependencias y decisiones

Depende de Alembic, del cascarón React existente y de los límites modulares definidos. El diseño exacto de JWT, hashes y entidades deberá documentarse en un ADR si introduce una decisión que afecte sprints posteriores. Las cuentas iniciales y sus credenciales no se versionarán.

Antes de implementar se definirá el conjunto inicial de permisos y la política de actualización de menú al cambiar permisos. El catálogo LLM aprobado queda registrado en el ADR 0002; sumar un cuarto proveedor requerirá actualizar la especificación, el ADR, los controles de secretos y las pruebas. El diseño visual debe privilegiar componentes nativos y CSS mantenible; no se incorporará una biblioteca de componentes si no se justifica por una necesidad concreta y se registra su impacto en tamaño, accesibilidad y mantenimiento.

## 9. Resultado de implementación

Pendiente. Se completará con PR, SHA, evidencia de CI, resultados de pruebas, resultados de las comprobaciones responsive y enlace a la bitácora cuando el sprint se ejecute.
