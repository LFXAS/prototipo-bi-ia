# Plan acumulativo de validación del prototipo

## Propósito

Este plan convierte el objetivo específico de validación en evidencia visible y repetible dentro de la plataforma. La validación se incorpora en el sprint donde existe el artefacto que puede comprobarse; no se aplaza toda la evaluación hasta el final ni se declara como aprobada una capacidad todavía no construida.

La persona usuaria principal de la evidencia técnica es el analista BI. La pantalla **Diseño y transformación BI > Asistente de datamart > Validación estructural de la propuesta** reúne los controles de la versión seleccionada. Sprint 4 añadió conciliación cuantitativa, Sprint 5 incorporó calidad semántica, analítica y reportería, y Sprint 6 añadió aislamiento multifuente y contraste estructural con WideWorldImporters. La ampliación del 3 de octubre incorpora una revisión previa IA/reglas de la necesidad, distinta de la validación del contrato y de los datos materializados.

## Matriz incremental

| Criterio | Evidencia | Momento | Estado actual |
|---|---|---|---|
| Exactitud estructural | La huella de la instantánea coincide con sus metadatos persistidos; tablas, columnas, PK y FK proceden del catálogo SQL Server. | Sprint 3 | Implementado y visible. |
| Exactitud referencial | Todas las tablas y columnas usadas por la propuesta existen en la instantánea; las referencias inventadas se descartan. | Sprint 3 | Implementado y visible. |
| Necesidad con respaldo estructural | Texto propio, reformulado o sugerido desde los metadatos; evidencia, tipos, roles y rutas FK comprobados, límites y evaluación persistida del mismo actor/entrada. | Endurecimiento Sprint 3 | Aceptación funcional supervisada de la puerta previa en ambas fuentes: límites aceptados y generación habilitada, sin crear propuestas ni ETL. No garantiza toda reformulación ni interpretación. |
| Consentimiento y continuidad de revisión | El destino LLM coincide con la autorización; cambios de fuente/texto/preguntas/período invalidan la evaluación y se descartan respuestas tardías. | Endurecimiento Sprints 3 y 6 | Implementado y cubierto por regresión; no se hereda consentimiento desde el borrador. |
| Controles de calidad del contrato | Granularidad, hecho, dimensiones, medidas, uniones, KPI y operaciones ETL cumplen reglas determinísticas. | Sprint 3 | Implementado y visible. |
| Reproducibilidad de la propuesta aprobada | Las decisiones IA persistidas se reejecutan con el motor determinístico y deben producir la misma huella de propuesta. No se exige que una nueva llamada al LLM repita literalmente su respuesta. | Sprint 3 | Implementado y visible. |
| Utilidad inicial | Decisión y comentario del analista BI sobre claridad, coherencia y pertinencia de la propuesta. | Sprint 3 | Revisión supervisada disponible; rúbrica formal pendiente. |
| Conciliación OLTP–datamart | Consultas de referencia comparan filas, pedidos distintos, unidades e importes totales y mensuales entre la fuente y el datamart. | Sprint 4 | Implementado y visible en el expediente ETL. |
| Exactitud de KPI calculados | Los KPI variables sugeridos por IA usan recetas declarativas conocidas y contrastan su resultado OLTP--datamart con período y filtros equivalentes. La demostración final evidencia al menos cinco. | Sprint 4--5 | Implementado: nueve indicadores distintos en la ejecución 9. |
| Calidad descriptiva de entidades | La población se conserva y la etiqueta visible se obtiene por relaciones verificadas, con cobertura y muestra controlada. | Sprint 5 | Implementado: 19820 clientes con nombre y tipo, sin etiquetas vacías. |
| Analítica y reportería | Panel, hallazgos, chat, PDF y Excel se reconstruyen desde la ejecución conciliada y respetan vista y filtros. | Sprint 5 | Implementado y revisado visualmente. |
| Interacción visual segura | Puntos, barras y leyendas permiten explorar valores exactos; sólo una categoría presente en el catálogo autorizado puede convertirse en filtro global. | Sprint 5 | Implementado con teclado, puntero y pruebas automatizadas. |
| Aislamiento multifuente | Conexión, instantánea, catálogo, propuesta, ejecución y tablero conservan la misma procedencia y rechazan cruces. | Sprint 6 | Implementado con AdventureWorks y WideWorldImporters habilitadas simultáneamente. |
| Portabilidad estructural | El mismo motor descubre hecho, dimensiones y medidas sin bifurcar por nombre de base; omisiones o invenciones del LLM se corrigen o bloquean. | Sprint 6 | Propuesta 96 aprobada y ejecución 13 conciliada con 231412 filas. |
| Proveedores LLM intercambiables | Gemini, Groq, Anthropic, Qwen y Ollama conservan un contrato JSON validado; secretos y particularidades de protocolo no llegan al dominio BI. | Sprint 2--5 | Implementado; Anthropic usa Messages API, URL restringida y credencial cifrada. |
| Neutralidad de recetas y versiones | Los nombres del proveedor compilan a identificadores canónicos, los KPI equivalentes se consolidan y cada ejecución nueva conserva sus tablas sin sustituir otra. | Sprint 4--5 | Implementado en código y regresión; materialización física dual pendiente de evidencia integrada. |
| Contraste secundario | Resultados equivalentes se contrastan posteriormente con AdventureWorksDW cuando exista correspondencia semántica documentada. | Sprint posterior a ETL | Pendiente. |
| Utilidad formal | Juicio de expertos mediante instrumento y escala definidos, sin sustituir la validación técnica. | Evaluación final | Pendiente. |
| Decisión de alcance predictivo | Se documenta que pronóstico, MAPE y RMSE no pertenecen al problema de investigación vigente. | Sprint 5 | Retirado del alcance por decisión del tutor. |

## Evidencia implementada en Sprint 3

Al seleccionar una propuesta y ejecutar **Verificar evidencia**, FastAPI realiza nuevamente, sin invocar al LLM:

1. la comprobación SHA-256 de la instantánea;
2. la validación de referencias y reglas del contrato;
3. la comparación entre la validación recalculada y la almacenada;
4. la reconstrucción de la propuesta a partir de `ai_decisions`, alcance y mapa semántico;
5. la comparación entre la huella persistida y la huella reconstruida.

El resultado muestra cada control como **Cumple** o **Revisar**, conserva sólo hashes y métricas seguras y registra el evento `copilot.proposal.verify`. Los nombres visibles son: **Integridad de los metadatos**, **Referencias técnicas comprobadas**, **Consistencia del contrato BI** y **Reproducción determinística del contrato**. La pantalla no presenta el antiguo acordeón de validaciones futuras: la conciliación cuantitativa se consulta en el expediente ETL. Verificar no cambia estados ni retira aprobaciones; diferencias de reproducción por evolución del motor no se interpretan por sí solas como corrupción.

## Validación previa de necesidades

La asesoría combina interpretación probabilística con comprobaciones determinísticas.
No se acepta como evidencia suficiente que el proveedor declare una necesidad viable.
La prueba debe distinguir cuatro momentos: sugerencia o reformulación, adopción del
texto, revisión del texto definitivo y generación del contrato. Una sugerencia no
aprueba propuestas ni modifica el catálogo analítico.

| Escenario | Resultado exigido | Evidencia que conservar |
|---|---|---|
| Solicitar ideas sin objetivo inicial | Hasta dos necesidades explicadas y sujetas a adopción humana; no sobrescritura automática. | Fuente, instantánea, proveedor/modelo, captura y referencias. |
| Reformular un objetivo | Mantener la intención y mostrar límites; no introducir una fuente inexistente como resuelta. | Texto original/sugerido y decisión de uso. |
| Revisar una necesidad definitiva | Requisitos directos, derivables, ambiguos o no disponibles, validados contra tipos y FK dirigidas. | Huellas de entrada/evaluación, referencias y registro persistido. |
| Datos o relaciones sin respaldo | No aceptar importe textual, costo desconectado, FK inversa con multiplicación ni pedidos como facturación. | Regresiones con metadatos controlados y resultado del validador. |
| Tipo compatible, significado contradictorio | No usar un precio de venta como costo ni una fecha como operando numérico; los nombres desconocidos quedan ambiguos. | Caso real `UnitPrice`, regresiones ES/EN y feedback controlado. |
| Alcance no demostrable | Explicar la limitación; presencia de esquema no prueba datos, costo histórico, predicción ni rentabilidad económica completa. | Advertencias y decisión humana, sin atribuir garantía de exhaustividad a la IA. |
| Cambiar contexto/destino | Invalidar evaluación y consentimiento cuando corresponda; descartar respuesta tardía. | Pruebas UI y bloqueo antes de llamada al proveedor. |
| Pasar a la propuesta | Usar la revisión guardada del mismo actor y entrada; verificar cobertura con medidas/KPI reales. | Requisito, capacidad controlada y resultado del contrato. |
| Cambiar la versión de reglas | Conservar revisiones históricas, pero impedir que una huella anterior a `need-review-2` autorice otra generación. | Prueba del hash versionado y reevaluación; propuestas/ETL históricos sin mutación. |

Los casos QA-NEED de
[`testing/auditoria-operativa-2026-10-03.md`](testing/auditoria-operativa-2026-10-03.md)
documentan método, incidencias, capturas y resultados. El contraste determinístico con
instantáneas reales no se confunde con una respuesta real de Claude. Del mismo modo,
un ensayo real de la revisión de necesidades no se contabiliza como otro ciclo ETL ni
como prueba de todos los proveedores, idiomas o motores. La autorización de envío
corresponde al destino configurado y excluye filas y credenciales.

Los primeros intentos reales de Claude mostraron un límite concreto: dos opciones
de AdventureWorks pasaron la comprobación estructural, aunque contenían afirmaciones
incorrectas sobre estados de pedidos. WideWorldImporters produjo en una repetición
una opción usable y otra bloqueada, y un requisito temporal aritmético inválido fue
rechazado al analizar. La confusión de `UnitPrice` con costo evidenció que validar
únicamente tipos no era suficiente; se añadió el control de roles y se versionó la
revisión. Estos resultados no se cuentan como aceptación semántica completa; la
repetición final y la prueba negativa se incorporan a la auditoría con su estado real.

La repetición correctiva en WWI obtuvo seis directos, dos derivables, cuatro límites
de interpretación y ninguno no disponible para una necesidad mensual de líneas de
factura. Confirmar los límites habilitó generar, pero la prueba terminó antes de crear
otra propuesta. La prueba negativa sobre clima externo identificó su ausencia y
distinguió esos datos de sensores internos; sin aceptar alcance parcial no permitió
generar. Se registra como resultado de la puerta previa, no como una nueva aprobación
de contrato ni una carga conciliada.

En AdventureWorks la reformulación no resultó utilizable tras dos intentos porque
incluía una capacidad sin validador. La alternativa de conservar el objetivo original
permitió revisarlo: once directos, uno derivable, cinco ambiguos o advertencias y cero
no disponibles. Sólo después de aceptar los cinco límites se habilitó generar; no se
creó otra propuesta. Esta recuperación y los bloqueos forman parte de la aceptación
funcional supervisada, sin prometer éxito de cada respuesta del LLM. La UI distingue
referencia estructural, derivación candidata e interpretación IA no ejecutable.

La regresión posterior a estas correcciones completó `make test` con **231 pruebas
backend y 34 frontend** aprobadas. También finalizaron correctamente Ruff, formato,
Mypy, ESLint y la compilación estricta TypeScript/Vite. Estos resultados corresponden
al cierre de código del ensayo; no sustituyen las evidencias reales anteriores ni
se presentan como resultado de una nueva ejecución ETL. La verificación integral y
documental se registra separadamente en la bitácora de entrega.

## Conciliación cuantitativa exigida para Sprint 4

La materialización no se considerará correcta sólo porque termine sin error. La plataforma deberá ejecutar consultas de referencia determinísticas sobre AdventureWorks OLTP y consultas equivalentes sobre el datamart para presentar, como mínimo:

| Métrica de control | Fuente OLTP | Datamart | Tolerancia prevista |
|---|---|---|---|
| Filas al grano aprobado | Conteo de líneas de venta incluidas | Conteo de `fact_ventas` | Diferencia 0 |
| Pedidos distintos | Identificadores de pedido distintos | Pedidos distintos en el hecho | Diferencia 0 |
| Unidades vendidas | Suma de cantidad aprobada | Suma de unidades | Diferencia 0 |
| Importe de ventas | Suma del importe aprobado | Suma de importe en el hecho | 0 o tolerancia decimal documentada |
| Ventas por mes | Agregación por fecha de venta | Agregación por `dim_fecha` | Mismos períodos e importes |

Cada ejecución conservará consulta de referencia versionada, parámetros, instante, resultados, diferencias absoluta y relativa y estado. AdventureWorksDW será un contraste secundario; no reemplazará la fuente OLTP como verdad de la carga porque su diseño y reglas pueden diferir.

Además de los controles de carga, Sprint 4 calculará los KPI variables que el LLM haya sugerido desde la necesidad y los metadatos comprobados. FastAPI sólo ejecutará recetas declarativas como agregación, razón o participación y rechazará fórmulas libres. La demostración final seleccionará al menos cinco KPI sugeridos por IA y conciliados. El contrato y las exclusiones se detallan en `docs/specs/SPR-04-02-kpis-controlados-y-calculables.md`.

La versión aprobada más reciente y compatible será la sugerencia inicial para el ETL, pero el analista deberá confirmarla. También podrá comparar propuestas aprobadas de distintos modelos o revisiones; cada ejecución conservará el `proposal_id` elegido. Esta regla se desarrolla en `docs/specs/SPR-04-01-seleccion-propuesta-y-validacion-etl.md`.

## Evidencia implementada en Sprint 4

La propuesta 52 generó la ejecución 6 como expediente de referencia. La plataforma conservó las huellas de propuesta e instantánea, compiló 27 operaciones y cargó 121317 líneas tanto en origen como en destino, con diferencia cero. Las dimensiones registraron 1124 fechas, 504 productos, 19820 clientes y 10 territorios; se conciliaron 274914 unidades y 31465 pedidos distintos.

## Evidencia implementada en Sprints 5 y 6

La propuesta 54 y la ejecución 7 corrigen la identidad del cliente sin modificar la población comercial ni el grano. La dimensión contiene 19119 personas y 701 organizaciones, todas con `nombre_cliente` y `tipo_cliente`. La conciliación conserva 121317 líneas, 274914 unidades y 31465 pedidos distintos.

La propuesta 73 reprocesó el flujo completo con Groq y `sales-bi-v6`. La ejecución 9 confirmó diferencia cero para cantidad, ventas brutas, descuento monetario, pedidos y costo; publicó nueve KPI sin duplicados y mantuvo 19820 nombres de cliente no vacíos. La revisión humana aprobó únicamente las etiquetas territoriales de agrupación, por lo que la ejecución quedó disponible para analítica sin una segunda carga.

El dashboard sólo abre ejecuciones exitosas y conciliadas. PDF y Excel vuelven a construir la misma selección en servidor; el control visual confirmó seis páginas A4 horizontales sin cortes y seis hojas de cálculo completas. El copiloto contextual recibe exclusivamente indicadores y agregados autorizados. Para preguntas fuera del lienzo, Groq `openai/gpt-oss-120b` selecciona valores de un contrato cerrado y FastAPI ejecuta la agregación parametrizada; la prueba Top 5 de productos en Europa verifica filtro no visible, denominador completo y procedencia sin SQL libre. La recuperación de sesión conserva el borrador y vuelve a leer la versión autorizada sin repetir mutaciones.

Los nueve KPI de la ejecución final quedaron asociados a recetas versionadas. Los importes usan la moneda base USD comprobada mediante `Sales.CurrencyRate.FromCurrencyCode`. `CostoTotal / UnidadesVendidas` y `VentasBrutas / UnidadesVendidas` se muestran como **Costo promedio por unidad vendida** y **Venta promedio por unidad vendida**, respectivamente; la denominación, el código ISO y el valor exacto permanecen trazables. La interpretación española publicó únicamente las etiquetas territoriales revisadas, conservó los valores originales y registró responsable, comentario y fecha.

Una selección idéntica ya ejecutada abre el expediente existente en lugar de materializar nuevamente. Tanto la propuesta aprobada como la ejecución completada permiten recorrer sus cinco etapas en modo de sólo lectura. Las pruebas de interfaz comprueban que los campos permanecen deshabilitados, la materialización no vuelve a ofrecerse y el paso final conserva la conciliación publicada.

Sprint 6 agrega una segunda línea de evidencia real. AdventureWorks2022 conserva sus
ejecuciones históricas y WideWorldImporters produce la ejecución 13 en un destino físico
independiente: 231412 filas de origen y destino, diferencia cero, 73595 pedidos y
9310904 unidades. La calidad descriptiva confirma 227 productos, 663 clientes y 53
territorios. Moneda y descuento no demostrables permanecen explícitamente sin resolver.

La repetición con Anthropic conservó la propuesta 77 como evidencia sin aprobarla ni ejecutar el ETL. El endurecimiento posterior comprobó que nombres con espacios o idiomas distintos producen las mismas dependencias técnicas, que `AVG(LineTotal)` se rotula como importe promedio por línea y que la razón `SUM(ventas) / SUM(unidades)` permanece calculable en la ejecución histórica 10. El catálogo analítico omite la ejecución 9 porque el materializador legado ya había sustituido sus filas físicas; los nuevos esquemas `mart_ventas_e{id}` evitan esa pérdida en cargas futuras.

El 27 de septiembre se repitió la necesidad completa con Groq y Claude en niveles medio
y alto. Las cuatro pruebas superaron la conexión mínima, pero ninguna quedó aprobable:
Groq produjo dos fallos controlados de proveedor y Claude generó dos contratos que fueron
bloqueados por referencias y procedencia inválidas. Las propuestas 78--81 quedaron como
evidencia sin aprobación ni ETL. Frente a la propuesta Groq 73 (0 errores, 0 advertencias)
y la propuesta Claude 77 (0 errores, 7 advertencias), se recomienda Groq bajo como
principal y Claude bajo/mínimo como contingencia. La metodología y sus límites están en
`docs/experiments/2026-09-27-groq-vs-claude.md`.

## Regla de interpretación

Una propuesta puede ser técnicamente válida y aun requerir ajustes de negocio. Del mismo modo, una aprobación humana no demuestra por sí sola exactitud cuantitativa. El prototipo sólo declarará el objetivo completamente validado cuando reúna evidencia técnica, reproducibilidad, conciliación de cifras y evaluación formal de utilidad por usuarios y expertos.
