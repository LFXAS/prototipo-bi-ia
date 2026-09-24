# Plan acumulativo de validación del prototipo

## Propósito

Este plan convierte el objetivo específico de validación en evidencia visible y repetible dentro de la plataforma. La validación se incorpora en el sprint donde existe el artefacto que puede comprobarse; no se aplaza toda la evaluación hasta el final ni se declara como aprobada una capacidad todavía no construida.

La persona usuaria principal de esta evidencia es el analista BI. La pantalla **IA > Asistente de datamart > Validación estructural de la propuesta - Sprint 3** reúne los controles que ya pueden ejecutarse sobre la versión seleccionada. A partir de Sprint 4, un apartado acumulativo **Validación del datamart** ampliará el expediente con la conciliación cuantitativa entre AdventureWorks OLTP y el datamart materializado.

## Matriz incremental

| Criterio | Evidencia | Momento | Estado actual |
|---|---|---|---|
| Exactitud estructural | La huella de la instantánea coincide con sus metadatos persistidos; tablas, columnas, PK y FK proceden del catálogo SQL Server. | Sprint 3 | Implementado y visible. |
| Exactitud referencial | Todas las tablas y columnas usadas por la propuesta existen en la instantánea; las referencias inventadas se descartan. | Sprint 3 | Implementado y visible. |
| Controles de calidad del contrato | Granularidad, hecho, dimensiones, medidas, uniones, KPI y operaciones ETL cumplen reglas determinísticas. | Sprint 3 | Implementado y visible. |
| Reproducibilidad de la propuesta aprobada | Las decisiones IA persistidas se reejecutan con el motor determinístico y deben producir la misma huella de propuesta. No se exige que una nueva llamada al LLM repita literalmente su respuesta. | Sprint 3 | Implementado y visible. |
| Utilidad inicial | Decisión y comentario del analista BI sobre claridad, coherencia y pertinencia de la propuesta. | Sprint 3 | Revisión supervisada disponible; rúbrica formal pendiente. |
| Conciliación OLTP–datamart | Consultas de referencia comparan filas, pedidos distintos, unidades e importes totales y mensuales entre la fuente y el datamart. | Sprint 4 | Implementado y visible en el expediente ETL. |
| Exactitud de KPI calculados | Los KPI variables sugeridos por IA usan recetas declarativas conocidas y contrastan su resultado OLTP--datamart con período y filtros equivalentes. La demostración final evidencia al menos cinco. | Sprint 4 | Implementado: seis KPI en la ejecución 6. |
| Contraste secundario | Resultados equivalentes se contrastan posteriormente con AdventureWorksDW cuando exista correspondencia semántica documentada. | Sprint posterior a ETL | Pendiente. |
| Utilidad formal | Juicio de expertos mediante instrumento y escala definidos, sin sustituir la validación técnica. | Evaluación final | Pendiente. |
| Pronóstico | MAPE y RMSE sobre un conjunto temporal separado de prueba. | Sprint de analítica predictiva | Pendiente. |

## Evidencia implementada en Sprint 3

Al seleccionar una propuesta y ejecutar **Verificar evidencia**, FastAPI realiza nuevamente, sin invocar al LLM:

1. la comprobación SHA-256 de la instantánea;
2. la validación de referencias y reglas del contrato;
3. la comparación entre la validación recalculada y la almacenada;
4. la reconstrucción de la propuesta a partir de `ai_decisions`, alcance y mapa semántico;
5. la comparación entre la huella persistida y la huella reconstruida.

El resultado muestra cada control como **Cumple** o **Revisar**, conserva sólo hashes y métricas seguras y registra el evento `copilot.proposal.verify`. Los nombres visibles son: **Integridad de los metadatos**, **Referencias técnicas comprobadas**, **Consistencia del contrato BI** y **Reproducción determinística del contrato**. La pantalla enumera por separado las validaciones futuras para que el analista conozca el alcance real de la evidencia.

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

Los seis KPI quedaron asociados a recetas versionadas. Los importes se enriquecieron posteriormente con la moneda base USD comprobada mediante `Sales.CurrencyRate.FromCurrencyCode`, sin repetir el ETL. La interpretación española publicó únicamente las etiquetas territoriales revisadas, conservó los valores originales y registró responsable, comentario y fecha. Una selección idéntica ya ejecutada abre el expediente existente en lugar de materializar nuevamente.

## Regla de interpretación

Una propuesta puede ser técnicamente válida y aun requerir ajustes de negocio. Del mismo modo, una aprobación humana no demuestra por sí sola exactitud cuantitativa. El prototipo sólo declarará el objetivo completamente validado cuando reúna evidencia técnica, reproducibilidad, conciliación de cifras, evaluación de utilidad y métricas predictivas en los incrementos correspondientes.
