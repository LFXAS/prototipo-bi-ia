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
- `backend`: FastAPI con recarga en desarrollo; Uvicorn sin recarga y usuario no privilegiado en producción.
- `postgres`: instancia aislada del proyecto, con esquemas `app` y `mart` inicializados en un volumen nombrado.
- `sqlserver`: instancia aislada del proyecto; descarga y restaura AdventureWorks de forma idempotente en un volumen nombrado.

## Modos de ejecución

1. **Desarrollo:** `compose.yaml` inicia Vite, FastAPI y las dos bases bajo `bi-ia-prototype`.
2. **Vista local de entrega:** el perfil `delivery` añade Nginx al mismo proyecto; no duplica datos ni detiene Vite.
3. **Entrega completa:** `compose.release.yaml` consume las cinco imágenes GHCR bajo `bi-ia-prototype-release`, con puertos y volúmenes distintos. Puede ejecutarse al mismo tiempo que desarrollo si el equipo dispone de memoria suficiente.

Las ramas no representan servidores. `develop` integra cambios y `main` identifica código publicable; CI usa contenedores temporales y CD convierte `main` o una etiqueta `v*` en imágenes versionadas. El despliegue conserva una etiqueta explícita y no comparte volúmenes entre ambientes.

## Despliegue académico propuesto

Para completar DevOps se propone una VM Linux x64 en Azure for Students. El diseño usa una sola entrega remota para controlar consumo: desarrollo permanece local, CI crea contenedores efímeros y la VM ejecuta únicamente una etiqueta aprobada de GHCR. GitHub Actions accederá a Azure con OIDC y permisos limitados al recurso; la VM realizará `pull`, `up -d` y comprobaciones de salud. La infraestructura se añadirá como código después de activar la suscripción y fijar región, presupuesto y nombres.

No se recomienda una VM ARM para este conjunto porque SQL Server para Linux requiere un procesador compatible con x64. La capacidad objetivo para la demostración es 2 vCPU y 8 GiB, con apagado o desasignación fuera de las ventanas de prueba.

## Límites modulares previstos

- `system`: salud y diagnóstico técnico mínimo.
- `security`: autenticación y RBAC mínimo.
- `parameters`: parámetros del prototipo, conexiones aprobadas y configuración no secreta del proveedor LLM activo.
- `metadata`: introspección determinística de AdventureWorks.
- `copilot`: propuestas estructuradas del LLM, nunca ejecución directa.
- `etl`: vista previa, validación, ejecución y trazabilidad de cargas.
- `analytics`: KPIs, gráficos e insights.
- `forecasting`: regresión lineal y métricas MAPE/RMSE.
- `reports`: evidencias y reportes académicos.

Sólo `system` contiene comportamiento en esta entrega.

## Contrato de evolución (SDD)

Desde el Sprint 2, cada módulo sólo incorpora capacidad funcional a partir de una especificación versionada en `docs/specs/`. La especificación define el contrato funcional y de datos; la arquitectura, el ADR cuando exista una decisión duradera, las pruebas y el PR demuestran cómo se cumplió. Este control evita que una propuesta del LLM, un cambio de esquema o una integración externa aparezcan sin aprobación humana, criterios verificables y trazabilidad.

## RBAC previsto

Entidades mínimas: `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `menus`, `menu_permissions` y `audit_events`.

Reglas arquitectónicas:

1. React puede ocultar opciones, pero FastAPI autoriza cada operación.
2. Denegar por defecto cuando un permiso no esté asignado.
3. Los tokens no almacenan secretos ni reemplazan el estado activo del usuario.
4. Las aprobaciones de propuestas/SQL quedan auditadas.
5. Menús y permisos comparten códigos estables, no nombres visibles.

## Contrato UI/UX responsive

Desde Sprint 2, cada módulo que incorpore interfaz se integra en un cascarón React reutilizable con encabezado, navegación autorizada, contenido principal y avisos globales. La interfaz debe ser utilizable en móvil desde 320 px, tableta, escritorio y pantalla amplia; no puede depender de un tamaño fijo ni generar desplazamiento horizontal involuntario.

Los menús son una representación de permisos ya autorizados por FastAPI. En escritorio pueden permanecer visibles; en móvil deben abrirse y cerrarse con teclado o táctil. Formularios, tablas y acciones administrativas definen estados de carga, vacío, éxito, error, sesión vencida y acceso denegado. La accesibilidad mínima incluye foco visible, etiquetas de campos, mensajes que no dependan sólo del color y contraste suficiente para lectura.

## Contrato de configuración LLM

El módulo `parameters` conserva una única configuración LLM activa con valores no secretos: tipo de proveedor, URL base, modelo, límites y referencia de credencial. El catálogo inicial es `gemini` (referencia `GEMINI_API_KEY`), `qwen-cloud` (referencia `DASHSCOPE_API_KEY`) y `ollama-local` (referencia `none`, servicio interno). La clave real vive sólo en variables de entorno o en el mecanismo de secretos del despliegue; ni PostgreSQL, ni React, ni los eventos de auditoría la almacenan o la devuelven.

FastAPI encapsula las diferencias de cada servicio en adaptadores internos y sólo habilita uno a la vez. En Sprint 2 permite probar de forma real y limitada la conexión configurada, sin enviar datos de negocio ni conservar contenido de respuesta. Un perfil Docker opcional de Ollama se agregará junto con su implementación y permanecerá aislado de la red pública; `qwen3:4b` es el modelo local inicial recomendado. Gemini y Qwen Cloud conservan la elección de modelo en configuración porque su catálogo y sus cuotas pueden cambiar.

El módulo `copilot` posterior consumirá este contrato mediante una interfaz interna y será el único que pueda solicitar propuestas sobre metadatos o planes BI; ningún SQL asistido por IA se ejecutará automáticamente. La decisión se detalla en [`decisions/0002-configuracion-proveedor-llm.md`](decisions/0002-configuracion-proveedor-llm.md).

## Datos

PostgreSQL alojará dos responsabilidades lógicamente separadas:

- esquema `app`: seguridad, parámetros, auditoría y ejecuciones;
- esquema `mart`: hechos y dimensiones analíticas.

La separación física en bases distintas no es necesaria para la prueba de concepto y puede revisarse si las mediciones lo justifican.
