# SPR-03-03: experiencia del asistente y trazabilidad comprensible

- Estado: **implementado y verificado localmente; pendiente de validación del usuario**.
- Pertenece a: [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md).
- Su definición visual e interactiva normativa se encuentra en [SPR-03-05-ui-ux-profesional.md](SPR-03-05-ui-ux-profesional.md).
- Fecha de revisión: 2026-09-14.

## 1. Objetivo de experiencia

El usuario principal del Sprint 3 es el analista BI o responsable de datos. Su recorrido parte de una necesidad del área comercial y no puede comenzar con 71 tablas, identificadores en inglés, JSON o SQL. Debe comenzar con una pregunta de ventas y terminar con una propuesta comprensible que pueda aceptar o rechazar. El gerente comercial aporta la necesidad y consume los resultados en las fases analíticas posteriores.

El detalle técnico existe para trazabilidad y soporte, pero no constituye el recorrido principal ni una tarea obligatoria para el usuario final.

## 2. Valor para el usuario final

En Sprint 3, el usuario todavía no recibe un dashboard calculado, pero ya obtiene valor verificable:

1. expresa qué desea analizar en lenguaje cotidiano;
2. conoce qué conceptos de negocio encontró el asistente en la base;
3. recibe una explicación en español del posible datamart y sus KPIs;
4. puede revisar advertencias y decidir si la propuesta representa su necesidad;
5. deja una entrada aprobada para que Sprint 4 construya el datamart sin solicitar SQL manual.

Este recorrido diferencia el prototipo de un visor de base de datos y demuestra la asistencia semiautomatizada y supervisada indicada en el título de la investigación.

## 3. Navegación mínima

| Grupo | Opción | Usuario principal | Propósito |
|---|---|---|---|
| Parámetros generales | Conexiones de datos | Administrador | Configurar y probar SQL Server sin editar archivos. |
| Datos | Explorador de esquema | Administrador o analista BI | Consultar la instantánea y su trazabilidad técnica. |
| IA | Asistente de datamart | Analista BI o responsable de datos | Seleccionar un dominio habilitado, registrar la necesidad, personalizar y decidir sobre la propuesta. |

La barra superior muestra el nombre y estado de la fuente activa. No se crea una pantalla separada de **Fuente activa**: su estado, última prueba y acción **Actualizar metadatos** se integran en Conexiones de datos. Así se evita una ruta adicional sin valor propio.

ETL, Datamart, Dashboard y Pronóstico no se muestran como opciones funcionales hasta que sus sprints los implementen.

## 4. Pantallas obligatorias

Además de las vistas siguientes, una instalación incompleta ofrece el wizard de preparación inicial definido en SPR-03-05. El wizard orquesta la configuración LLM, la fuente y la instantánea sin duplicar los módulos administrativos.

### 4.1 Conexiones de datos

Contiene el formulario SQL Server, estado de credencial, acciones de prueba y activación, fecha de última prueba y fecha de última instantánea. La acción **Actualizar metadatos** aclara que sólo lee la estructura y no modifica ni carga datos.

### 4.2 Asistente de datamart

Antes del recorrido muestra un catálogo de dominios calculado desde la instantánea. Sólo ventas está habilitado en Sprint 3; esta entrada evita crear una pantalla distinta cuando se incorpore inventario u otro perfil.

Usa cinco pasos visibles:

1. **Necesidad:** objetivo, preguntas y periodo de análisis en español.
2. **Conceptos encontrados:** etiquetas de negocio, explicación y confianza; el origen técnico permanece plegado.
3. **Propuesta validada:** significado del hecho, granularidad, dimensiones, medidas, KPIs, plan ETL declarativo, supuestos y advertencias.
4. **Personalización:** ajustar dimensiones, medidas, agregaciones y KPIs ya verificados, con justificación y sin SQL.
5. **Revisión:** aprobar o rechazar con comentario y explicación de que aún no se ejecuta ETL.

El usuario no selecciona tablas, no escribe identificadores y no edita JSON. Las preguntas y dimensiones del paso 1 proceden del catálogo del backend y reflejan los metadatos vigentes. Si la interpretación es ambigua, la aplicación solicita precisar la necesidad en español.

La propuesta diferencia visualmente:

- **Propuesto por IA**;
- **Comprobado por la aplicación**;
- **Decidido por una persona**.

El plan ETL se explica mediante un flujo visual de sólo lectura. Sprint 3 no incorpora drag and drop ni edición manual del proceso.

### 4.3 Explorador de esquema

Es una vista avanzada de sólo lectura:

- búsqueda por esquema, tabla o columna;
- lista paginada de tablas;
- detalle de columnas, tipos, PK y FK;
- relaciones entrantes y salientes;
- etiquetas españolas propuestas y su correspondencia técnica.

En Sprint 3 el explorador no permite modificar manualmente el alcance. Esa edición se elimina para reducir complejidad y evitar trasladar decisiones técnicas al gerente.

## 5. Reglas de interacción

1. El Asistente es el acceso principal del analista BI.
2. Si falta fuente, instantánea o LLM probado, la pantalla explica qué debe resolver el administrador.
3. Sólo se envían al LLM metadatos y la solicitud normalizada; la confirmación lo indica antes de generar.
4. Una referencia descartada por el backend nunca aparece como concepto válido.
5. Cada concepto muestra una explicación española y permite consultar su origen técnico.
6. Los errores se presentan en lenguaje comprensible y ofrecen la siguiente acción.
7. Mientras una operación está en curso, se impiden envíos duplicados.
8. Aprobar y rechazar requieren confirmación; rechazar exige comentario.
9. Cambiar de pantalla no mezcla formularios, selecciones, errores ni resultados.
10. No se guardan credenciales ni respuestas LLM en el almacenamiento del navegador.
11. El historial muestra por defecto versiones listas para revisar, permite filtrar por estado y pagina en servidor.
12. Una personalización crea otra versión enlazada; nunca sobrescribe el resultado original ni una decisión final.

## 6. Estados mínimos

| Pantalla | Estados necesarios |
|---|---|
| Conexiones | Sin registros, editando, probando, disponible, error seguro y dependencia. |
| Asistente | Prerrequisito pendiente, listo, interpretando, propuesta inválida, listo para revisión, aprobado y rechazado. |
| Explorador | Cargando, sin instantánea, resultados, sin coincidencias, detalle y error recuperable. |

No se muestran códigos HTTP, trazas, objetos JSON sin formato, `undefined` ni `[object Object]`.

## 7. Responsive y accesibilidad

Esta sección conserva los requisitos funcionales mínimos. Los componentes, jerarquía, microcopy, estados, anchos y criterios verificables se detallan en SPR-03-05 y prevalecen para la implementación visual.

- En móvil, la navegación usa hamburguesa; formularios y secciones se apilan y la propuesta utiliza acordeones.
- En tableta, lista y detalle del explorador alternan sin comprimir el contenido.
- En escritorio, el asistente mantiene un ancho de lectura cómodo y puede mostrar un resumen lateral.
- Las tarjetas de tablas reservan una columna independiente para sus métricas; los nombres de esquema y tabla se ajustan en varias líneas cuando son extensos y nunca invaden el panel de detalle.
- Las tablas tienen paginación y su desplazamiento queda contenido; no desplazan toda la página.
- Casillas, acordeones, diálogos y acciones funcionan con teclado y foco visible.
- Los estados incluyen texto y no dependen únicamente del color.
- La interfaz visible, ayudas, errores y propuesta se presentan en español.

Se verifican 320, 768, 1024 y 1440 px.

## 8. Seguridad y auditoría visible

- React oculta acciones no autorizadas y FastAPI vuelve a comprobar cada permiso.
- Una credencial guardada sólo se presenta como configurada o pendiente.
- La pantalla informa qué metadatos serán enviados al proveedor.
- La trazabilidad muestra fecha, fuente, instantánea, proveedor/modelo, resultado del validador y decisión humana.
- Nunca muestra clave, contraseña, cadena de conexión, prompt interno ni razonamiento privado del modelo.

## 9. Criterios de aceptación

- [ ] El administrador configura y prueba SQL Server desde la web.
- [ ] El analista BI completa el asistente sin seleccionar manualmente tablas, escribir SQL ni interpretar JSON como interfaz principal.
- [ ] Los metadatos técnicos en inglés se presentan como conceptos comprensibles en español.
- [ ] Cada concepto conserva un origen técnico consultable y validado.
- [ ] Una referencia inventada no aparece como válida ni puede aprobarse.
- [ ] La propuesta separa claramente IA, validación de la aplicación y decisión humana.
- [ ] Aprobar o rechazar queda auditado y no ejecuta todavía ETL.
- [ ] El explorador permite verificar tablas, columnas y relaciones sin editarlas.
- [ ] Los nombres largos de tablas y esquemas permanecen legibles dentro de su tarjeta en los anchos definidos, sin solapar métricas ni detalle.
- [ ] Los estados de error explican cómo continuar y no exponen datos sensibles.
- [ ] El recorrido funciona con teclado y en los cuatro anchos definidos.

## 10. Pruebas y evidencia

- Componentes: formularios, pasos, concepto/origen, propuesta, estados y confirmaciones.
- Integración: conexión > instantánea > necesidad > interpretación > propuesta > validación > decisión.
- Seguridad: permisos, ocultamiento de secretos y errores sanitizados.
- Responsive y accesibilidad: teclado, foco y capturas en los cuatro anchos.
- Evidencia académica: secuencia completa narrada desde la necesidad del usuario hasta la propuesta aprobada.

## 11. Fuera de Sprint 3

- Chat conversacional general.
- Edición manual del alcance técnico.
- Grafo interactivo de las 71 tablas.
- Editor visual con drag and drop de tablas, relaciones o pasos ETL.
- Dashboard y resultados calculados.
- ETL, datamart físico y pronóstico.

## 12. Resultado de implementación

Pendiente. Al cerrar se incorporarán capturas, pruebas, SHA, desviaciones y estado final.
