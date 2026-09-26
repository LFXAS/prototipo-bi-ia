# SPR-03-05: interfaz y experiencia profesional del asistente BI

- Estado: **implementado y verificado localmente; pendiente de validación del usuario**.
- Pertenece a: [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md).
- Complementa: [SPR-03-03-explorador-esquema-y-trazabilidad.md](SPR-03-03-explorador-esquema-y-trazabilidad.md).
- Fecha de creación: 2026-09-18.
- Alcance: definición UI/UX implementada para la validación local del Sprint 3.

## 1. Objetivo de experiencia

El Sprint 3 debe presentar el primer recorrido funcional orientado al negocio. La interfaz debe permitir que una persona comprenda qué fuente está utilizando, exprese una necesidad de ventas, revise la interpretación realizada con IA y tome una decisión supervisada sin seleccionar tablas, escribir SQL ni interpretar JSON.

La experiencia se considera profesional cuando:

1. muestra con claridad dónde está la persona, qué necesita hacer y cuál es el siguiente paso;
2. distingue visualmente configuración, contenido propuesto por IA, comprobaciones automáticas y decisión humana;
3. informa el estado real del proceso sin porcentajes ficticios ni esperas silenciosas;
4. mantiene trazabilidad técnica accesible mediante divulgación progresiva, sin convertirla en el punto de partida del analista;
5. es consistente, accesible y utilizable desde 320 hasta 1440 px;
6. no presenta módulos futuros, acciones sin funcionamiento ni datos demostrativos como resultados reales.

## 2. Perfiles y recorridos

| Perfil | Recorrido principal | Información avanzada |
|---|---|---|
| Administrador | Configurar y probar la conexión SQL Server, activar la fuente, actualizar metadatos y configurar el LLM. | Diagnóstico seguro de conexión, fechas, instantánea y permisos de sólo lectura. |
| Analista BI o responsable de datos | Usuario principal del asistente: registrar la necesidad comercial, revisar conceptos, resolver ambigüedades, evaluar propuesta, supuestos y advertencias, y decidir. | Explorador de esquema, referencias técnicas, validaciones y versiones, sin escribir SQL. |
| Gerente o solicitante de negocio | Aportar objetivo, preguntas y criterios de utilidad; revisar opcionalmente el resumen de negocio y consumir resultados en sprints posteriores. | No valida relaciones, granularidad, plan ETL ni detalles técnicos. |

La interfaz adapta acciones a permisos, pero conserva los mismos nombres, estados y estructura. Ocultar una acción en React no reemplaza la autorización de FastAPI.

## 3. Arquitectura de información

### 3.1 Navegación autorizada del Sprint 3

| Grupo | Opción | Propósito |
|---|---|---|
| Acceso directo | Inicio | Estado general, prerrequisitos y accesos permitidos. |
| Parámetros generales | Conexiones de datos | Registrar, probar, activar y actualizar metadatos de SQL Server. |
| Parámetros generales | Configuración LLM | Registrar o reemplazar credencial, configurar modelo y probar proveedor. |
| Parámetros generales | Parámetros | Administrar los cuatro parámetros numéricos aprobados y el catálogo estructurado de necesidades analíticas. |
| Datos | Explorador de esquema | Consultar la instantánea técnica de sólo lectura. |
| IA | Asistente de datamart | Seleccionar un dominio habilitado, crear la solicitud, revisar conceptos, personalizar la propuesta y decidir. |

No se mostrarán ETL, Datamart, Dashboard, Reportes, Alertas, Predicciones ni chat analítico hasta que exista una capacidad funcional aprobada.

### 3.2 Cascarón común

La aplicación conserva el cascarón del Sprint 2 y lo amplía sin duplicarlo:

- **Encabezado:** control para mostrar u ocultar navegación, marca, nombre de la vista, fuente activa y estado, cuenta y cierre de sesión.
- **Navegación lateral:** grupos plegables autorizados, opción activa y comportamiento responsive ya aprobado.
- **Área principal:** ruta, título, explicación breve, acción principal y contenido de la vista.
- **Avisos globales:** sesión, acceso denegado o dependencia general; los errores de formulario permanecen junto a su contexto.

La fuente activa se muestra como contexto, no como selector multifuente: nombre visible, estado textual e indicador semántico. Al activarse una conexión distinta, la aplicación actualiza el contexto después de confirmar la operación.

## 4. Lenguaje visual

Se reutilizan los tokens definidos en [SPR-02-04](SPR-02-04-identidad-visual-y-shell-bi.md). No se crea una segunda identidad visual.

### 4.1 Jerarquía

- Un solo `h1` por vista, entre 32 y 40 px en escritorio y entre 28 y 32 px en móvil.
- Texto base mínimo de 16 px; ayudas y metadatos nunca menores de 14 px.
- Ancho de lectura del asistente entre 720 y 1120 px; las vistas técnicas pueden usar hasta 1440 px.
- Separación basada en una escala de 4, 8, 12, 16, 24, 32 y 48 px.
- Tarjetas con borde visible, radio moderado y sombra sutil; no se apilan sombras fuertes.
- La acción primaria es única por contexto. Acciones secundarias y destructivas no compiten visualmente con ella.

### 4.2 Significado de estados

| Tipo | Color semántico | Icono y texto obligatorio | Ejemplos |
|---|---|---|---|
| Éxito | `--color-success` | Sí | Conexión probada, instantánea vigente, propuesta aprobada. |
| Información | `--color-info` | Sí | Interpretando metadatos, validación automática. |
| Advertencia | `--color-warning` | Sí | Supuesto por revisar, instantánea desactualizada. |
| Error | `--color-danger` | Sí | Proveedor inaccesible, referencia inválida, acción bloqueada. |
| Neutral | texto y borde | Sí | Sin registros, pendiente, no requiere credencial. |

Ningún significado depende únicamente del color. Las insignias emplean nombres comprensibles en español y no exponen valores internos como `ready_for_review`.

### 4.3 Diferenciación de responsabilidades

La propuesta utiliza tres patrones consistentes:

- **Propuesto por IA:** distintivo informativo con icono de destello y texto explícito.
- **Comprobado por la aplicación:** distintivo de verificación y resumen de reglas superadas o bloqueos encontrados.
- **Decidido por una persona:** nombre o etiqueta histórica del revisor, fecha, decisión y comentario.

Estos distintivos no sugieren que la IA tenga autoridad para aprobar o ejecutar.

## 5. Componentes reutilizables obligatorios

| Componente | Uso y regla |
|---|---|
| `PageHeader` | Ruta, título, explicación, contexto y una acción principal. |
| `StatusBadge` | Estado con texto, icono y color semántico. |
| `InlineAlert` | Resultado persistente relacionado con la pantalla; nunca se reemplaza por un `alert()` del navegador. |
| `Toast` | Confirmación breve de una operación ya visible; no contiene errores que requieren decisión. |
| `Stepper` | Cinco pasos del asistente, con estado actual y completado; no permite saltar prerrequisitos. |
| `SetupWizard` | Preparación inicial del administrador; reutiliza los formularios reales y puede retomarse sin crear una segunda configuración paralela. |
| `SectionCard` | Agrupa información con título y descripción; evita tarjetas anidadas sin necesidad. |
| `Disclosure` | Muestra detalles técnicos opcionales con estado expandido accesible. |
| `DataTable` | Encabezados, paginación, estado vacío y desplazamiento contenido. En móvil se transforma en filas apiladas cuando resulte más legible. |
| `EmptyState` | Explica por qué no existen datos y ofrece la siguiente acción autorizada. |
| `Skeleton` | Reserva el espacio de contenido durante lecturas; las operaciones externas usan además mensaje de progreso. |
| `ConfirmDialog` | Activar, eliminar, aprobar y rechazar; describe el efecto antes de confirmar y devuelve el foco al origen. |
| `FieldMessage` | Error o ayuda enlazada al campo mediante atributos accesibles. |

Los componentes deben extender los patrones existentes del frontend; no se incorporará una biblioteca visual completa salvo decisión arquitectónica separada.

## 6. Asistente de preparación inicial

Se incorpora un **wizard de configuración inicial** para evitar que una instalación nueva obligue al administrador a descubrir por su cuenta el orden de las pantallas. No reemplaza los módulos de Conexiones, Configuración LLM o Parámetros: los orquesta y reutiliza sus mismos formularios y API.

### 6.1 Activación

- Se ofrece desde Inicio cuando falta uno o más prerrequisitos del Asistente de datamart.
- Sólo lo puede ejecutar un perfil con los permisos administrativos necesarios.
- Después de completar la preparación, no se abre automáticamente en cada sesión; Inicio conserva una acción **Revisar configuración**.
- El avance se deriva del estado real persistido. No se almacena una copia de credenciales o formularios en el navegador.

### 6.2 Pasos

1. **Bienvenida y comprobación:** explica el alcance, verifica permisos y muestra qué se configurará.
2. **Proveedor de IA:** seleccionar proveedor/modelo, registrar la credencial cuando aplique y probar la conexión.
3. **Fuente de ventas:** ingresar SQL Server, base y credencial, probar conexión y confirmar sólo lectura.
4. **Activación y metadatos:** activar la fuente, crear o reutilizar la instantánea y mostrar cantidades de tablas, columnas y relaciones.
5. **Resumen:** comprobar todos los prerrequisitos y ofrecer **Abrir Asistente de datamart**.

Cada paso permite volver sin borrar una configuración ya guardada. **Salir y continuar después** conserva exclusivamente lo confirmado en backend. Un paso incompleto no se marca como terminado.

### 6.3 Reglas de experiencia

- El wizard muestra **Paso N de 5**, título, explicación, contenido y acciones **Atrás** y **Continuar**.
- **Continuar** permanece deshabilitado únicamente cuando la causa se explica junto al control.
- Probar proveedor o fuente es obligatorio antes de avanzar a su activación.
- Los errores permanecen en el paso donde ocurrieron y no eliminan valores no sensibles.
- En móvil el stepper muestra el paso actual y un resumen textual; no intenta presentar cinco etiquetas en una fila.
- Cerrar el wizard devuelve el foco al control que lo abrió.

### 6.4 Lo que el wizard no hace

- no instala Docker, SQL Server u Ollama;
- no modifica puertos, redes, volúmenes ni credenciales internas de infraestructura;
- no descarga modelos locales;
- no crea usuarios o roles;
- no reemplaza las validaciones de FastAPI.

## 7. Pantalla Inicio

Inicio deja de ser una portada vacía y actúa como orientación, sin convertirse todavía en dashboard analítico.

### 7.1 Contenido

1. saludo y rol visible;
2. tarjeta **Fuente de datos** con nombre, estado, última prueba e instantánea vigente;
3. tarjeta **Asistente de IA** con proveedor/modelo, estado de prueba y acceso autorizado;
4. tarjeta **Preparación del análisis** con los prerrequisitos en orden;
5. acceso principal **Crear propuesta de datamart** cuando todo esté disponible;
6. acción **Completar configuración inicial** cuando falten prerrequisitos;
7. explicación honesta de que Sprint 3 prepara una propuesta y todavía no ejecuta el ETL.

Las tarjetas muestran únicamente datos reales. Si falta un prerrequisito, indican quién puede resolverlo y enlazan a la pantalla correspondiente sólo cuando existe permiso.

## 8. Pantalla Conexiones de datos

### 8.1 Estructura de escritorio

1. `PageHeader` con **Nueva conexión**.
2. Resumen de la fuente activa con estado, última prueba, última instantánea y acción **Actualizar metadatos**.
3. Lista de conexiones con nombre, servidor/base ocultando información sensible innecesaria, estado, última prueba y menú de acciones.
4. Formulario de creación o edición en panel de la misma vista; no desplaza la navegación ni mezcla datos con otras pantallas.

En móvil, el resumen aparece primero, la lista se representa como tarjetas y el formulario ocupa una vista apilada. No se fuerza una tabla horizontal para seis o más columnas.

### 8.2 Formulario

- Secciones: identificación, servidor, credencial y seguridad de transporte.
- Etiquetas siempre visibles; los placeholders sólo muestran ejemplos.
- Puerto usa control numérico con límites; contraseña permite mostrar u ocultar durante el ingreso.
- En edición, contraseña vacía significa **Conservar credencial actual** y se explica junto al campo.
- La aplicación no completa ni vuelve a mostrar la contraseña guardada.
- El botón primario cambia entre **Crear conexión** y **Guardar cambios**; **Cancelar** restaura la vista sin conservar errores.

### 8.3 Acciones y estados

- **Probar conexión** muestra las etapas reales conocidas: conectando, verificando base y comprobando sólo lectura. No usa porcentajes inventados.
- **Activar** exige prueba exitosa y un diálogo que informa que sustituirá la fuente activa.
- **Actualizar metadatos** aclara que lee estructura, no filas, y conserva la última instantánea válida si falla.
- **Eliminar** es destructiva, se muestra únicamente cuando corresponde y explica las dependencias que impiden la acción.
- Los resultados exitosos permanecen como confirmación verde accesible; los fallos usan mensaje seguro con acción de recuperación.

## 9. Pantalla Configuración LLM

La corrección del Sprint 2 adopta el mismo patrón visual de Conexiones:

- proveedor y modelo con ayuda contextual;
- URL sólo cuando el proveedor la requiera;
- estado de credencial: **Configurada**, **Pendiente** o **No requerida**;
- acción **Registrar credencial** o **Reemplazar credencial**, nunca **Ver clave**;
- acción **Probar conexión** y fecha del último resultado;
- una sola configuración activa y explicación de su impacto en el asistente.

La interfaz no atribuye un fallo de cuota, credencial, red o modelo a una misma causa genérica cuando el backend pueda distinguirlas de forma segura.

## 10. Pantalla Asistente de datamart

Es la experiencia central del Sprint 3. No abre directamente un formulario de ventas: primero presenta un catálogo de tipos de datamart calculado por el backend. **Datamart de ventas** es el único perfil funcional de la prueba de concepto; otros dominios aparecen deshabilitados o se incorporan después con su propio perfil, reglas y pruebas, sin crear otra pantalla.

Después de seleccionar un dominio, el asistente usa un flujo de cinco pasos. En escritorio, el stepper se muestra horizontal; en móvil se presenta compacto y anuncia **Paso N de 5**.

### 10.1 Prerrequisitos

Antes del paso 1 se presenta una comprobación breve:

- fuente activa y probada;
- instantánea disponible;
- configuración LLM activa y probada;
- permisos del actor.

Si falta algo, no se presenta un formulario que después fallará. Se muestra el bloqueo, la acción siguiente y el responsable capaz de resolverlo.

### 10.2 Paso 1: necesidad de negocio

Campos visibles:

- objetivo de análisis, con ejemplo en lenguaje comercial;
- preguntas de negocio mediante opciones comprensibles y selección múltiple;
- una periodicidad elegida entre las estrategias habilitadas para el dominio;
- una explicación visible de que las dimensiones serán propuestas por la IA desde los metadatos y revisadas en los pasos posteriores;
- texto complementario limitado, sin aceptar SQL ni identificadores técnicos.

Las preguntas orientadoras y periodicidades se reciben desde `GET /copilot/catalog` para la instantánea vigente. El objetivo se escribe en cada análisis y el paso 1 no solicita dimensiones. La IA debe inferirlas desde los metadatos; recién después se muestran con su evidencia para revisión y personalización humana. React no contiene un modelo dimensional fijo de AdventureWorks.

La pantalla explica qué se enviará: solicitud normalizada y metadatos estructurales; nunca credenciales ni filas de ventas. **Analizar metadatos** es la acción primaria.

### 10.3 Paso 2: conceptos encontrados

Los conceptos se presentan como una lista de tarjetas, no como una tabla técnica. Cada tarjeta contiene:

- nombre comprensible en español;
- explicación breve;
- confianza cualitativa;
- estado de comprobación de referencias;
- control **Ver origen técnico** plegado.

El origen técnico muestra esquema, tabla, columnas principales y relación utilizada. Si existen ambigüedades, la interfaz formula una pregunta concreta en español. No pide al analista escoger entre identificadores sin explicación ni escribir una consulta.

La acción primaria es **Generar propuesta BI**. La secundaria **Modificar necesidad** vuelve al paso 1 sin mezclar resultados de otro intento.

Al abrir una versión aprobada desde el historial, las cinco etapas funcionan como
pestañas de consulta. Necesidad, conceptos, propuesta, personalización y revisión
se reconstruyen desde el artefacto persistido; sus campos y decisiones quedan
inhabilitados para evitar que la demostración o auditoría altere lo aprobado.

### 10.4 Paso 3: propuesta validada

La primera sección responde en lenguaje de negocio:

- qué representa una venta;
- cuál es la granularidad;
- qué preguntas podrá responder el futuro datamart;
- principales supuestos y limitaciones.

Después se muestran secciones separadas para dimensiones, medidas, KPIs, plan ETL declarativo, calidad y advertencias. Cada sección indica **Propuesto por IA** y su resultado de **Comprobación automática**.

El plan ETL incluye una **vista previa visual no editable** de izquierda a derecha —Fuente, Extracción, Uniones validadas, Modelo dimensional, KPIs propuestos y Destino—. Cada nodo permite consultar su explicación, pero no puede moverse, conectarse ni borrarse. Esta vista ayuda al analista a comprender y supervisar la propuesta sin obligarlo a diseñar manualmente el proceso.

Los detalles técnicos —identificadores, joins, documento contractual y códigos del validador— están plegados y dirigidos al analista BI. El JSON crudo no es la presentación principal y, si se ofrece para evidencia, usa una vista de sólo lectura con copia controlada.

Si existen errores, la propuesta muestra **No puede aprobarse**, agrupa los problemas por sección y ofrece **Crear una nueva versión**. Las advertencias permiten continuar sólo después de su lectura y confirmación.

### 10.5 Paso 4: personalización supervisada

Si la propuesta técnicamente válida no representa por completo la necesidad, el analista puede ajustar, sin SQL:

- resumen y descripción de granularidad;
- dimensiones entre las ya verificadas;
- medidas entre las ya verificadas y su agregación permitida;
- KPIs compatibles con las medidas seleccionadas;
- justificación obligatoria del cambio.

La interfaz elimina un KPI dependiente cuando se retira su medida y no permite inventar tablas, columnas, relaciones ni fórmulas. **Guardar como nueva versión** envía el ajuste al backend, vuelve a ejecutar las reglas determinísticas y conserva el vínculo con la versión de origen. La propuesta original nunca se sobrescribe.

Cada KPI muestra su función semántica y un selector con únicamente las medidas compatibles ya verificadas. Cuando no existe una medida compatible, el control queda deshabilitado y explica dos acciones concretas: excluir el KPI o generar una nueva versión que solicite la medida faltante. La pantalla separa **Ajustes automáticos aplicados**, **Advertencias pendientes**, **Decisiones excluidas** y **Observaciones originales del proveedor**; estas últimas son trazabilidad, no evidencia validada.

### 10.6 Paso 5: revisión humana

La vista resume:

- necesidad original;
- fuente e instantánea;
- versión de propuesta;
- validación automática;
- supuestos y advertencias pendientes;
- efecto de la decisión.

**Aprobar propuesta** exige confirmación y aclara que no ejecutará ETL todavía. **Rechazar propuesta** exige comentario. Una decisión final reemplaza los controles por un comprobante con estado, persona, fecha y comentario; el registro queda inmutable.

### 10.7 Versiones generadas

El asistente conserva una tabla paginada de resultados persistidos con versión, origen, necesidad, proveedor/modelo, estado y fecha. El filtro inicial **Lista para revisar** concentra el trabajo pendiente; se puede cambiar a aprobadas, rechazadas, con problemas o todas. El filtrado y la paginación se ejecutan en servidor.

Una propuesta aprobada dispone de **Retirar aprobación** con motivo obligatorio. Una versión no aprobada dispone de **Descartar versión**. Ambas acciones conservan historial y auditoría; el filtro **Retiradas o descartadas** permite recuperarlas como evidencia sin mezclarlas con el trabajo vigente.

**Abrir resultado** selecciona una fila y repone su contenido validado sin volver a ejecutar el proveedor. La fila abierta se diferencia visualmente y la selección anuncia el proveedor y modelo mediante una región de estado.

Este mecanismo permite revisar propuestas producidas en momentos distintos, escoger cuál someter a aprobación y reutilizar durante una demostración un resultado local cuya generación haya requerido varios minutos. La comparación es humana: la interfaz no puntúa ni declara automáticamente un modelo superior.

### 10.8 Validación estructural visible

La sección **Validación estructural de la propuesta - Sprint 3** muestra únicamente evidencia que puede comprobarse antes de materializar el datamart: integridad de metadatos, referencias técnicas, consistencia del contrato y reproducción determinística del artefacto guardado. Un aviso explícito aclara que todavía no existe conciliación de filas, unidades o importes.

El mismo expediente crecerá en Sprint 4 con la conciliación OLTP-datamart y, en incrementos posteriores, con contraste AdventureWorksDW, juicio de expertos, MAPE y RMSE. No se mezclan controles pendientes con tarjetas de cumplimiento.

### 10.9 Generación y espera

Durante operaciones LLM:

- se bloquea el envío duplicado;
- se conserva el cascarón y el contexto;
- se muestran etapas reales: preparando metadatos, interpretando conceptos, validando referencias y preparando propuesta;
- no se muestra razonamiento interno del modelo;
- no se afirma que una etapa terminó si el backend no lo confirma;
- si la operación falla, se conserva la necesidad ingresada y se ofrece reintento seguro o cambio de configuración por un administrador.

## 11. Pantalla Explorador de esquema

Es una herramienta avanzada de consulta, no la puerta de entrada al asistente.

### 11.1 Escritorio

- barra de búsqueda y filtros por esquema;
- lista maestra paginada de tablas a la izquierda;
- detalle a la derecha con resumen, columnas, PK, FK y relaciones;
- etiquetas de negocio propuestas, diferenciadas de los nombres técnicos originales;
- cabecera con fuente, hash abreviado y fecha de instantánea.

### 11.2 Móvil y tableta

La lista y el detalle se muestran como vistas consecutivas con acción **Volver a tablas**. No se comprimen en dos columnas estrechas. Las columnas se representan como filas apiladas cuando una tabla no resulte legible.

No existe edición de metadatos, selección manual de tablas en el recorrido principal ni grafo de 71 tablas en Sprint 3.

## 12. Decisión sobre drag and drop

No se implementará drag and drop funcional en el Sprint 3.

Las herramientas profesionales lo utilizan principalmente cuando el usuario diseña manualmente un flujo de preparación o ETL. Ese patrón exigiría incorporar semántica de nodos, conexiones válidas, eliminación, deshacer/rehacer, persistencia parcial, validaciones de grafos, alternativa completa de teclado y un modelo de permisos adicional. También trasladaría al usuario una decisión técnica que en este proyecto debe proponer la IA y comprobar la aplicación.

En su lugar se utilizarán:

- wizard para preparar la plataforma;
- stepper para construir y revisar el análisis;
- tarjetas seleccionables para conceptos de negocio;
- vista visual de sólo lectura para explicar el plan ETL;
- acordeones para revelar trazabilidad técnica.

Un editor visual podrá evaluarse en Sprint 4 únicamente como vista avanzada del analista BI y mediante una especificación separada. No formará parte de los criterios de aceptación del anteproyecto ni sustituirá la propuesta asistida por IA.

## 13. Contenido y microcopy

1. Toda la interfaz visible se redacta en español claro y consistente.
2. Las acciones usan verbo y objeto: **Probar conexión**, **Actualizar metadatos**, **Generar propuesta BI**, **Aprobar propuesta**.
3. Se evita la jerga cuando no aporta una decisión. `snapshot` se presenta como **instantánea de metadatos** y `read-only` como **sólo lectura**.
4. Los mensajes indican qué ocurrió, por qué afecta al usuario y qué puede hacer después.
5. No se usan mensajes genéricos como **Ocurrió un error**, códigos HTTP, `undefined`, objetos serializados ni contenido del proveedor sin procesar.
6. La interfaz diferencia **propuesta**, **validación** y **ejecución futura** para no sugerir que el datamart ya fue construido.

Ejemplos aprobados:

- **La conexión funciona y la cuenta tiene acceso de sólo lectura.**
- **No se pudo probar la conexión. Revise el servidor, la base y la credencial. La contraseña guardada no fue modificada.**
- **La propuesta contiene dos referencias que no existen en la instantánea y no puede aprobarse.**
- **Propuesta aprobada. Quedó disponible como entrada para la construcción controlada del datamart en el siguiente sprint.**

## 14. Responsive

| Ancho | Comportamiento obligatorio |
|---|---|
| 320–767 px | Una columna; navegación superpuesta; stepper compacto; formularios y acciones a ancho disponible; detalle técnico plegado; diálogos utilizables sin desbordamiento. |
| 768–1023 px | Contenido principal prioritario; navegación temporal; listas y detalles alternables; formularios hasta dos columnas sólo cuando cada campo conserve legibilidad. |
| 1024–1439 px | Sidebar contraíble; formularios de dos columnas; stepper horizontal; explorador maestro-detalle. |
| Desde 1440 px | Ancho máximo de contenido; no se estiran párrafos ni formularios hasta ocupar toda la pantalla; panel de resumen opcional. |

Se prohíbe reducir la escala global, usar zoom CSS para hacer caber contenido o provocar desplazamiento horizontal de toda la aplicación.

## 15. Accesibilidad

El objetivo mínimo es WCAG 2.1 AA en los recorridos implementados:

- orden de encabezados y regiones semánticas;
- navegación completa por teclado;
- foco visible y restaurado después de diálogos, acordeones y operaciones;
- etiqueta programática para cada campo;
- asociación de errores, ayudas y descripciones con el control correspondiente;
- contraste mínimo de 4.5:1 para texto normal y 3:1 para texto grande o componentes;
- objetivos táctiles de al menos 44 por 44 px cuando sea viable;
- anuncios accesibles para carga, éxito y error mediante regiones vivas sin repetir mensajes;
- respeto de `prefers-reduced-motion`; las transiciones no son necesarias para comprender el flujo.

## 16. Seguridad y privacidad visibles

- Las credenciales nunca vuelven al navegador después de guardarse.
- No se almacenan credenciales, documentos completos de propuesta ni respuestas del LLM en `localStorage` o `sessionStorage`. Para recuperación ante vencimiento se permite únicamente el borrador escrito por el usuario, códigos de selección, paso actual e identificador opaco de una versión ya persistida; el expediente se vuelve a leer desde la API autorizada.
- Los detalles técnicos no incluyen cadena de conexión, prompt interno ni razonamiento privado.
- Antes de llamar al LLM se informa que se enviarán metadatos y la necesidad normalizada, no filas de negocio.
- Cerrar sesión limpia el estado sensible en memoria.
- Los mensajes de acceso denegado no invitan a reintentar una acción que el perfil no puede realizar.

## 17. Criterios de aceptación UI/UX

- [ ] El analista BI completa el asistente sin seleccionar manualmente tablas, escribir SQL ni usar JSON como interfaz principal.
- [ ] El administrador configura y prueba la fuente y el LLM desde pantallas consistentes, sin editar archivos.
- [ ] Una instalación incompleta ofrece el wizard de cinco pasos y una configuración completada no vuelve a imponerlo.
- [ ] El wizard reutiliza los datos reales de los módulos, puede retomarse y nunca conserva secretos en el navegador.
- [ ] Inicio comunica los prerrequisitos reales y ofrece el siguiente paso autorizado.
- [ ] La entrada genérica muestra el catálogo de dominios y habilita únicamente perfiles respaldados por metadatos y validadores.
- [ ] Las preguntas y periodicidades se obtienen del backend; el objetivo se escribe por análisis y el paso 1 no predefine dimensiones.
- [ ] El flujo de cinco pasos conserva contexto y no permite saltar dependencias.
- [ ] El analista puede personalizar decisiones verificadas, crear una versión derivada y justificarla sin escribir SQL.
- [ ] Versiones generadas filtra por defecto **Lista para revisar**, permite cambiar de estado y pagina en servidor.
- [ ] La validación del Sprint 3 distingue controles estructurales cumplidos de conciliaciones futuras.
- [ ] IA, validador y decisión humana se distinguen mediante texto, icono y estilo consistente.
- [ ] Cargas externas muestran progreso comprensible sin porcentajes ficticios y bloquean duplicados.
- [ ] Éxito, error, vacío, acceso denegado, sesión vencida y dependencia pendiente tienen una presentación definida.
- [ ] Los errores quedan junto a su contexto y siempre ofrecen una acción posible cuando existe.
- [ ] Aprobar y rechazar explican su efecto; rechazar requiere comentario y ninguna decisión ejecuta ETL.
- [ ] Versiones generadas permite abrir y decidir un resultado persistido sin volver a consumir el proveedor; proveedor y modelo permanecen visibles.
- [ ] Las tablas y detalles técnicos no producen desplazamiento horizontal de toda la aplicación.
- [ ] Los recorridos son utilizables en 320, 768, 1024 y 1440 px.
- [ ] Los recorridos principales funcionan con teclado, foco visible, etiquetas y contraste AA.
- [ ] No aparecen módulos futuros, controles sin función, datos falsos ni secretos.
- [ ] El plan ETL se explica mediante una vista visual no editable; no existe drag and drop funcional en Sprint 3.
- [ ] El idioma visible es español y no se muestran estados internos, trazas o respuestas crudas.

## 18. Pruebas y evidencia

### 18.1 Automatizadas

- pruebas de componentes para campos, errores, estados, acordeones, stepper, diálogos y acciones por permiso;
- pruebas del wizard: primera entrada, reanudación, paso bloqueado, finalización y reapertura voluntaria;
- pruebas de integración del recorrido con API simulada desde prerrequisitos hasta decisión;
- comprobación de navegación por teclado y reglas automatizables de accesibilidad;
- vistas en 320, 768, 1024 y 1440 px sin desbordamiento global;
- comprobación de que errores estructurados nunca se convierten en texto no legible.

### 18.2 Manuales

- recorrido de administrador para fuente y LLM;
- recorrido principal del analista BI sin programación;
- revisión opcional del resumen de negocio con un representante comercial;
- sesión vencida, acceso denegado, proveedor caído, fuente inaccesible y validación fallida;
- lector de pantalla en formularios, stepper, alertas y decisión;
- ampliación al 200 % sin pérdida de información ni acciones.

### 18.3 Evidencia académica

- capturas de cada paso y de los tres tipos de responsabilidad;
- registro de una prueba de usabilidad con tareas, resultado, tiempo, errores y observaciones;
- rúbrica posterior de expertos sobre utilidad, claridad, trazabilidad, supervisión y pertinencia;
- evidencia de contraste y responsive sin incluir credenciales o datos sensibles.

## 19. Decisiones para mantener viabilidad

- No se implementa chat abierto en Sprint 3.
- No se incorpora un framework visual nuevo si los componentes actuales pueden extenderse.
- No se crea un diseñador gráfico del modelo dimensional; se usa una presentación por secciones.
- No se implementa arrastrar y soltar funcional, personalización de temas ni preferencias por usuario.
- No se muestra un grafo completo del esquema.
- No se hacen pruebas de usabilidad con una muestra estadística; se documentan tareas controladas y el juicio de expertos se realiza en la validación académica final.

## 20. Condición de aprobación de esta especificación

Antes de escribir código deben aprobarse:

1. los tres perfiles y sus responsabilidades;
2. la navegación mínima;
3. el wizard inicial de cinco pasos, el catálogo de dominios y el flujo analítico de cinco pasos;
4. la separación visible entre IA, validador y persona;
5. la vista visual no editable del plan ETL;
6. la ausencia de chat, drag and drop funcional, diseñador gráfico y módulos futuros;
7. los criterios responsive y de accesibilidad.

## 21. Resultado de implementación

Implementado localmente y pendiente de la prueba de aceptación usuaria. La aplicación incorpora catálogo de dominios, opciones dinámicas según la instantánea, recorrido de cinco pasos, personalización supervisada, filtro y paginación de versiones, y delimitación visible de la evidencia de Sprint 3. La evidencia definitiva de capturas, SHA y CI se completará antes del PR de cierre.
