# SPR-03-03: explorador de esquema y trazabilidad de la propuesta

- Estado: **borrador para revisión y aprobación**.
- Pertenece a: [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md).
- Fecha de creación: 2026-09-14.
- Rama prevista de implementación: `feature/sprint-03-metadata-copilot`.
- PR de implementación: pendiente.

## 1. Problema y objetivo

La introspección y la propuesta BI requieren una experiencia que permita comprender qué leyó la aplicación, qué información recibió la IA y qué decidió una persona. Mostrar listas técnicas o una respuesta cruda del LLM impediría verificar el carácter semiautomatizado y supervisado del prototipo.

El objetivo es definir la navegación y las pantallas de Fuente, Explorador y Propuesta BI para que una persona pueda seguir el proceso completo, distinguir procedencia y estado, revisar relaciones y tomar una decisión informada en móvil, tableta y escritorio.

## 2. Arquitectura de información

### 2.1 Navegación

| Grupo | Opción | Permiso mínimo | Propósito |
|---|---|---|---|
| Datos | Fuente AdventureWorks | `metadata.read` | Estado de conexión e instantánea. |
| Datos | Explorador de esquema | `metadata.read` | Tablas, columnas, claves, relaciones y selección de alcance. |
| IA | Propuesta BI | `copilot.proposals.read` | Generación, validación y revisión supervisada. |

No se mostrarán todavía ETL, Datamart, Dashboard, Reportes ni Predicciones como rutas funcionales. La barra superior mostrará **Fuente activa: AdventureWorks2022** y un estado textual `Disponible`, `Iniciando`, `No disponible` o `Sin comprobar`, sin selector de múltiples fuentes.

### 2.2 Pantalla Fuente AdventureWorks

- Identidad: SQL Server, AdventureWorks2022 y finalidad de sólo lectura.
- Estado de conexión y fecha de última prueba.
- Última instantánea, hash abreviado y totales.
- Acciones: **Probar conexión** y **Actualizar metadatos**, según permiso.
- Explicación visible: actualizar metadatos no carga ventas ni modifica la fuente.

### 2.3 Explorador de esquema

- Buscador por esquema, tabla o columna.
- Filtro de esquema y resumen de resultados.
- Lista jerárquica esquema > tabla.
- Detalle de tabla con columnas, tipo, nulabilidad, PK y referencias.
- Relaciones entrantes y salientes expresadas como `Esquema.Tabla.columna`.
- Selección mediante casillas para preparar un alcance de análisis.
- Resumen persistente del alcance: tablas seleccionadas, dependencias añadidas y advertencias.
- Acción **Preparar propuesta BI**, que navega al paso de confirmación; no llama al LLM sin confirmación.

### 2.4 Propuesta BI

- Barra de pasos: Fuente, Metadatos, Alcance, Generación, Validación y Revisión.
- Encabezado con id, estado, fecha, snapshot, proveedor/modelo y versión del contrato.
- Secciones de hecho, granularidad, dimensiones, relaciones, medidas, KPIs, plan ETL, calidad, supuestos y advertencias.
- Cada referencia técnica permite volver al detalle de la tabla correspondiente.
- Bloques visuales diferenciados:
  - **Propuesta de IA**;
  - **Validación de la aplicación**;
  - **Decisión humana**.
- Acciones finales condicionadas por estado y permiso: aprobar, rechazar o solicitar nueva propuesta.

## 3. Reglas de interacción y estado

1. Seleccionar otra instantánea limpia el alcance anterior después de confirmación; nunca mezcla objetos de snapshots diferentes.
2. Cambiar de pantalla no reutiliza errores, selección ni propuesta de otro módulo.
3. Una tabla puede seleccionarse desde la lista o detalle; ambos controles reflejan el mismo estado.
4. Las dependencias añadidas automáticamente se explican y pueden revisarse; no aparecen como selecciones ocultas.
5. Si se intenta retirar una tabla requerida por una FK seleccionada, la interfaz ofrece retirar también la relación o conservar la dependencia.
6. La generación requiere una confirmación que resume proveedor, modelo, cantidad de tablas y política “sólo metadatos”.
7. La acción Aprobar repite granularidad, cantidad de dimensiones, KPIs, advertencias y efecto: habilitar como entrada de Sprint 4, sin ejecutar ETL.
8. Rechazar o solicitar otra versión usa un comentario con longitud mínima y máxima; el comentario se conserva en la revisión.
9. Una operación en progreso impide dobles envíos y conserva una clave de idempotencia.
10. Si la sesión vence, se conserva localmente sólo la selección no sensible y se solicita iniciar sesión; nunca se guarda una credencial o respuesta del LLM en almacenamiento del navegador.

## 4. Estados obligatorios por pantalla

| Pantalla | Estados mínimos |
|---|---|
| Fuente | Sin comprobar, probando, disponible, no disponible, sin captura, capturando, sin cambios, captura actualizada, 403. |
| Explorador | Cargando, vacío real, resultados, búsqueda sin coincidencias, detalle, selección incompleta, error recuperable, 403. |
| Propuesta | Prerrequisitos pendientes, listo, generando, proveedor fallido, validación fallida, lista para revisión, aprobada, rechazada, sustituida, 403. |

Cada estado incluye explicación y siguiente acción cuando exista. No se presentan códigos HTTP, trazas, objetos JSON sin formato ni mensajes como `undefined` o `[object Object]`.

## 5. Responsive

| Ancho | Comportamiento |
|---|---|
| 320-767 px | Sidebar en hamburguesa; ficha y acciones apiladas; explorador como lista seguida de vista de detalle; secciones de propuesta en acordeones; acciones finales en bloque visible. |
| 768-1023 px | Sidebar temporal; lista y detalle alternan sin reducir columnas; resumen del alcance permanece accesible. |
| 1024-1439 px | Sidebar contraíble; explorador en dos paneles; propuesta en área principal con resumen lateral cuando haya espacio. |
| Desde 1440 px | Lista, detalle y resumen pueden coexistir; el ancho de lectura permanece limitado y el espacio adicional no estira párrafos. |

Las tablas internas pueden tener desplazamiento horizontal contenido cuando sea imprescindible, pero nunca provocan desplazamiento horizontal de toda la página. Las columnas secundarias se transforman en etiquetas en móvil.

## 6. Accesibilidad y lenguaje

- Interfaz, mensajes y propuestas visibles en español; se conservan nombres técnicos de origen sin traducir.
- Árbol, acordeones, casillas, pestañas y diálogos operables con teclado.
- Foco visible y orden lógico; al abrir detalle o diálogo, el foco se mueve y se restaura al cerrar.
- Estructura semántica con encabezados, etiquetas y descripciones asociadas.
- Estados no dependen sólo de color o icono; incluyen texto.
- Las relaciones se expresan también como texto, incluso si después se añade un diagrama visual.
- Avisos del LLM distinguen “propuesta”, “advertencia” y “error de validación”.
- Una alternativa tabular acompaña cualquier diagrama futuro del esquema.

## 7. Seguridad, privacidad y auditoría visible

- React oculta acciones no autorizadas, pero FastAPI aplica los permisos.
- No se muestran host, puerto interno, usuario SQL, contraseña ni cadena ODBC.
- La interfaz indica qué metadatos se enviarán antes de generar.
- No se permite editar el JSON de entrada, instrucciones del sistema o URL del proveedor desde Propuesta BI.
- La sección de trazabilidad muestra actor, fecha, estado y comentario seguro; la auditoría completa sigue siendo de sólo consulta bajo `audit.read`.
- Las descargas de evidencia, si se implementan, contienen metadatos/propuesta sin secretos y requieren permiso de lectura.

## 8. Criterios de aceptación verificables

- [ ] Los tres accesos aparecen sólo con permiso y dentro de los grupos Datos e IA.
- [ ] La barra superior muestra AdventureWorks como única fuente, sin un selector engañoso.
- [ ] La ficha explica que probar o actualizar no modifica ni carga datos.
- [ ] El explorador permite localizar una tabla y comprender sus columnas, PK, FK y relaciones sin leer JSON.
- [ ] La selección y dependencias son visibles y no se mezclan entre instantáneas.
- [ ] La confirmación previa a IA identifica modelo, alcance y política de sólo metadatos.
- [ ] La propuesta diferencia contenido del LLM, validación determinística y decisión humana.
- [ ] Aprobar declara expresamente que no ejecuta ETL ni crea el datamart.
- [ ] Los estados de carga, vacío, error, éxito, sesión vencida y 403 tienen mensajes y acciones coherentes.
- [ ] Los flujos principales funcionan con teclado y tienen foco visible.
- [ ] No existe desplazamiento horizontal involuntario en 320, 768, 1024 y 1440 px.
- [ ] No se muestran secretos, trazas o representaciones técnicas sin formato.

## 9. Plan de pruebas y evidencia

- Componentes: árbol/lista, detalle, casillas, dependencias, pasos, secciones, diálogos y avisos.
- Integración UI-API: carga, búsqueda, selección, cambio de snapshot, generación y revisión.
- Accesibilidad: teclado, foco, nombres accesibles y anuncio de estados.
- Responsive: capturas y pruebas en 320, 768, 1024 y 1440 px.
- Autorización: menú oculto más respuesta 403 del backend.
- Evidencia académica: secuencia de capturas Fuente > Explorador > Propuesta > Validación > Aprobación/Rechazo.

## 10. Riesgos y decisiones

- Un diagrama completo de 71 tablas sería ilegible; Sprint 3 prioriza lista, detalle y relaciones del alcance seleccionado. Un grafo interactivo queda como mejora posterior.
- El panel de Copiloto de la referencia visual no será un chat general; en este sprint se usa una experiencia guiada y verificable.
- Depende de SPR-03-01, SPR-03-02 y del cascarón definido en SPR-02-04.

## 11. Resultado de implementación

Pendiente. Al cierre se registrarán capturas, pruebas, SHA, desviaciones y estado final.
