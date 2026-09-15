# SPR-03-03: asistente de análisis, explorador avanzado y trazabilidad

- Estado: **borrador para revisión y aprobación**.
- Pertenece a: [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md).
- Fecha de creación: 2026-09-14.
- Rama prevista de implementación: `feature/sprint-03-metadata-copilot`.
- PR de implementación: pendiente.

## 1. Problema y objetivo

La introspección y la propuesta BI requieren una experiencia que permita comprender qué leyó la aplicación, qué información recibió la IA y qué decidió una persona. Mostrar primero listas técnicas, exigir una selección de tablas o presentar una respuesta cruda del LLM convertiría el prototipo en una herramienta para especialistas y no en un asistente útil para un gerente o analista de negocio.

El objetivo es definir dos niveles de experiencia: un recorrido principal que parte de una necesidad comercial expresada en español y una vista avanzada para inspeccionar la trazabilidad técnica. Ningún usuario de negocio necesita escribir SQL, seleccionar tablas o interpretar JSON para completar el recorrido principal.

## 2. Arquitectura de información

### 2.1 Navegación

| Grupo | Opción | Permiso mínimo | Propósito |
|---|---|---|---|
| Datos | Fuente AdventureWorks | `metadata.read` | Estado de conexión e instantánea; uso administrativo o de diagnóstico. |
| Datos | Explorador de esquema | `metadata.read` | Vista avanzada de tablas, columnas, claves, relaciones y alcance derivado. |
| IA | Asistente de análisis | `copilot.proposals.read` | Solicitud de negocio, propuesta, validación y revisión supervisada. |

No se mostrarán todavía ETL, Datamart, Dashboard, Reportes ni Predicciones como rutas funcionales. La barra superior mostrará **Fuente activa: AdventureWorks2022** y un estado textual `Disponible`, `Iniciando`, `No disponible` o `Sin comprobar`, sin selector de múltiples fuentes. El inicio del gerente destacará **Preparar análisis de ventas**; los accesos técnicos sólo aparecerán cuando sus permisos lo permitan.

### 2.2 Pantalla Fuente AdventureWorks

- Identidad: SQL Server, AdventureWorks2022 y finalidad de sólo lectura.
- Estado de conexión y fecha de última prueba.
- Última instantánea, hash abreviado y totales.
- Acciones: **Probar conexión** y **Actualizar metadatos**, según permiso.
- Explicación visible: actualizar metadatos no carga ventas ni modifica la fuente.

### 2.3 Asistente de análisis: recorrido principal

- Plantilla inicial **Analizar ventas**, con una explicación breve del resultado esperado.
- Campo **¿Qué desea conocer?**, limitado y acompañado por ejemplos de negocio.
- Preguntas sugeridas mediante casillas: ventas por periodo, productos destacados, clientes y territorios.
- Periodo y dimensiones de interés mediante controles de negocio; no se solicitan tablas ni columnas.
- Resumen del alcance sugerido: Venta, Fecha, Producto, Cliente y Territorio, con explicación de por qué se incluyó cada concepto.
- Confirmación visible de que se enviarán únicamente metadatos y la solicitud normalizada, nunca ventas, clientes, credenciales o SQL.
- Acción **Generar propuesta BI** y acceso secundario **Ver detalles técnicos** para quien tenga permiso.

### 2.4 Explorador de esquema avanzado

- Buscador por esquema, tabla o columna.
- Filtro de esquema y resumen de resultados.
- Lista jerárquica esquema > tabla.
- Detalle de tabla con columnas, tipo, nulabilidad, PK y referencias.
- Relaciones entrantes y salientes expresadas como `Esquema.Tabla.columna`.
- Identificación del alcance preseleccionado por `adventureworks-sales-v1`, diferenciando tablas ancla y dependencias añadidas.
- Ajuste opcional mediante casillas para un analista autorizado; no se permite escribir identificadores técnicos libres.
- Resumen persistente del alcance: conceptos solicitados, tablas derivadas, dependencias y advertencias.
- Acción **Volver al asistente**, que conserva la solicitud no sensible; ningún ajuste llama al LLM sin confirmación.

### 2.5 Propuesta BI

- Barra de pasos: Necesidad, Alcance sugerido, Generación, Validación y Revisión.
- Encabezado con id, estado, fecha, snapshot, proveedor/modelo y versión del contrato.
- Resumen inicial en lenguaje de negocio: significado de la venta, nivel de detalle, dimensiones y preguntas que podrán responderse.
- Secciones de hecho, granularidad, dimensiones, medidas, KPIs, plan ETL, calidad, supuestos y advertencias, con etiquetas en español.
- Cada concepto ofrece **Ver origen técnico** para volver al detalle correspondiente, sin dominar visualmente el recorrido.
- Bloques visuales diferenciados:
  - **Propuesta de IA**;
  - **Validación de la aplicación**;
  - **Decisión humana**.
- Acciones finales condicionadas por estado y permiso: aprobar, rechazar o solicitar nueva propuesta.

## 3. Reglas de interacción y estado

1. El recorrido comienza con una solicitud de negocio; nunca obliga a visitar Fuente o Explorador si los prerrequisitos ya están saludables.
2. Seleccionar otra instantánea limpia el alcance anterior después de confirmación; nunca mezcla objetos de snapshots diferentes.
3. Cambiar de pantalla no reutiliza errores, selección ni propuesta de otro módulo.
4. La preselección automática explica conceptos incluidos, versión del perfil y advertencias; no presenta tablas como primera decisión del gerente.
5. En modo avanzado, una tabla puede ajustarse desde la lista o detalle y ambos controles reflejan el mismo estado.
6. Las dependencias añadidas automáticamente se explican y pueden revisarse; no aparecen como selecciones ocultas.
7. Si el analista intenta retirar una tabla requerida por una FK seleccionada, la interfaz ofrece retirar también la relación o conservar la dependencia.
8. La generación requiere una confirmación que resume objetivo, conceptos, proveedor, modelo y política “sólo metadatos”.
9. La acción Aprobar repite significado de la venta, granularidad, dimensiones, KPIs, advertencias y efecto: habilitar como entrada de Sprint 4, sin ejecutar ETL.
10. Rechazar o solicitar otra versión usa un comentario con longitud mínima y máxima; el comentario se conserva en la revisión.
11. Aprobar una sustitución requiere una segunda confirmación que identifica la versión anterior que quedará como `superseded`.
12. Una operación en progreso impide dobles envíos y conserva una clave de idempotencia.
13. Si la sesión vence, se conserva localmente sólo la solicitud y el alcance no sensibles y se solicita iniciar sesión; nunca se guarda una credencial o respuesta del LLM en almacenamiento del navegador.

## 4. Estados obligatorios por pantalla

| Pantalla | Estados mínimos |
|---|---|
| Fuente | Sin comprobar, probando, disponible, no disponible, sin captura, capturando, sin cambios, captura actualizada, 403. |
| Asistente | Nuevo análisis, solicitud incompleta, alcance preparando, alcance listo, aclaración requerida, prerrequisito pendiente y 403. |
| Explorador avanzado | Cargando, vacío real, resultados, búsqueda sin coincidencias, detalle, alcance derivado, ajuste incompleto, error recuperable, 403. |
| Propuesta | Lista para generar, generando, proveedor fallido, validación fallida, lista para revisión, aprobada, rechazada, sustituida, 403. |

Cada estado incluye explicación y siguiente acción cuando exista. No se presentan códigos HTTP, trazas, objetos JSON sin formato ni mensajes como `undefined` o `[object Object]`.

## 5. Responsive

| Ancho | Comportamiento |
|---|---|
| 320-767 px | Sidebar en hamburguesa; solicitud y acciones apiladas; conceptos en tarjetas; explorador avanzado como lista seguida de detalle; propuesta en acordeones; acciones finales en bloque visible. |
| 768-1023 px | Sidebar temporal; asistente en una columna legible; lista y detalle avanzado alternan sin reducir columnas; resumen del alcance permanece accesible. |
| 1024-1439 px | Sidebar contraíble; explorador en dos paneles; propuesta en área principal con resumen lateral cuando haya espacio. |
| Desde 1440 px | Lista, detalle y resumen pueden coexistir; el ancho de lectura permanece limitado y el espacio adicional no estira párrafos. |

Las tablas internas pueden tener desplazamiento horizontal contenido cuando sea imprescindible, pero nunca provocan desplazamiento horizontal de toda la página. Las columnas secundarias se transforman en etiquetas en móvil.

## 6. Accesibilidad y lenguaje

- Interfaz, mensajes y propuestas visibles en español; un glosario controlado presenta equivalencias y conserva los nombres técnicos originales en detalles.
- Las etiquetas **Venta**, **Fecha**, **Producto**, **Cliente** y **Territorio** no sustituyen ni alteran tablas o columnas de AdventureWorks.
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
- El texto del objetivo se presenta como contenido del usuario, no como instrucción privilegiada; se valida, limita y escapa.
- No se permite editar el JSON de entrada, instrucciones del sistema o URL del proveedor desde Propuesta BI.
- La sección de trazabilidad muestra actor, fecha, estado y comentario seguro; la auditoría completa sigue siendo de sólo consulta bajo `audit.read`.
- Las descargas de evidencia, si se implementan, contienen metadatos/propuesta sin secretos y requieren permiso de lectura.

## 8. Criterios de aceptación verificables

- [ ] Los tres accesos aparecen sólo con permiso y dentro de los grupos Datos e IA; Asistente de análisis es el acceso principal del usuario de negocio.
- [ ] La barra superior muestra AdventureWorks como única fuente, sin un selector engañoso.
- [ ] La ficha explica que probar o actualizar no modifica ni carga datos.
- [ ] El gerente puede expresar un objetivo y confirmar conceptos sin seleccionar tablas, escribir SQL ni leer JSON.
- [ ] El explorador avanzado permite localizar una tabla y comprender sus columnas, PK, FK y relaciones.
- [ ] El alcance derivado, ajustes y dependencias son visibles y no se mezclan entre instantáneas.
- [ ] La confirmación previa a IA identifica objetivo, modelo, conceptos, alcance técnico consultable y política de sólo metadatos.
- [ ] La propuesta diferencia contenido del LLM, validación determinística y decisión humana.
- [ ] Aprobar declara expresamente que no ejecuta ETL ni crea el datamart.
- [ ] Ninguna pantalla solicita que un programador prepare una consulta para continuar el análisis.
- [ ] Los estados de carga, vacío, error, éxito, sesión vencida y 403 tienen mensajes y acciones coherentes.
- [ ] Los flujos principales funcionan con teclado y tienen foco visible.
- [ ] No existe desplazamiento horizontal involuntario en 320, 768, 1024 y 1440 px.
- [ ] No se muestran secretos, trazas o representaciones técnicas sin formato.

## 9. Plan de pruebas y evidencia

- Componentes: solicitud guiada, conceptos, árbol/lista avanzada, detalle, casillas, dependencias, pasos, secciones, diálogos y avisos.
- Integración UI-API: solicitud, alcance automático, ajuste avanzado, cambio de snapshot, generación y revisión.
- Accesibilidad: teclado, foco, nombres accesibles y anuncio de estados.
- Responsive: capturas y pruebas en 320, 768, 1024 y 1440 px.
- Autorización: menú oculto más respuesta 403 del backend.
- Evidencia académica principal: secuencia Asistente > Necesidad de negocio > Alcance sugerido > Propuesta > Validación > Aprobación/Rechazo; Fuente y Explorador se documentan como soporte técnico.

## 10. Riesgos y decisiones

- Un diagrama completo de 71 tablas sería ilegible y no ayuda al gerente; Sprint 3 prioriza conceptos de negocio y conserva lista, detalle y relaciones en el modo avanzado. Un grafo interactivo queda como mejora posterior.
- El panel de Copiloto de la referencia visual no será un chat general; en este sprint se usa una experiencia guiada y verificable.
- Depende de SPR-03-01, SPR-03-02 y del cascarón definido en SPR-02-04.

## 11. Resultado de implementación

Pendiente. Al cierre se registrarán capturas, pruebas, SHA, desviaciones y estado final.
