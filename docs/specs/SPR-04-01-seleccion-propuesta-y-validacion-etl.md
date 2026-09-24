# SPR-04-01: selección de propuesta aprobada y expediente de validación ETL

- Estado: **implementación y conciliación de referencia completadas con la ejecución 6**.
- Dependencias: Sprint 3 aceptado, propuesta BI aprobada e instantánea vigente.
- Propósito: fijar la lógica de entrada del ETL y de conciliación antes de programar Sprint 4.

## 1. Decisión funcional

El Sprint 4 no utilizará silenciosamente cualquier propuesta aprobada. La pantalla de materialización listará las versiones que cumplan simultáneamente:

1. estado `approved`;
2. dominio compatible con el constructor ETL habilitado;
3. instantánea y fuente disponibles;
4. contrato soportado por la versión del ejecutor;
5. ausencia de una invalidación administrativa posterior.
6. revalidación semántica vigente de función, columna, agregación y compatibilidad KPI--medida.
7. para cada KPI, una receta de cálculo admitida por `SPR-04-02`; una etiqueta de negocio no es suficiente para habilitar una ejecución.

La versión aprobada más reciente y compatible aparecerá **preseleccionada**, pero el analista BI deberá confirmar explícitamente **Usar como base del ETL**. Esta regla agiliza el caso normal sin ocultar la decisión humana.

La elegibilidad no confía únicamente en el estado histórico. Antes de listarla y nuevamente antes de crear una ejecución, FastAPI recalcula la validación contra la instantánea y las reglas vigentes. Si falla, retira su aprobación, registra el evento y exige una versión corregida; nunca materializa un contrato inconsistente.

## 2. Comparación de propuestas aprobadas

Antes de confirmar, el analista podrá comparar dos versiones aprobadas por:

- proveedor y modelo que originaron la propuesta;
- versión de origen y persona que la personalizó;
- granularidad;
- hecho, dimensiones, medidas, agregaciones y KPIs;
- advertencias y comentario de aprobación;
- instantánea, fecha y huellas del contrato.

La aplicación no declarará qué LLM es mejor ni fusionará propuestas automáticamente. El analista elige el contrato que representa la necesidad y la selección queda auditada.

## 3. Inmutabilidad y trazabilidad

Cada ejecución ETL conservará el `proposal_id` confirmado, la instantánea, la versión del constructor, los parámetros y las huellas de entrada. Cambiar de propuesta o seleccionar un conjunto distinto de KPI crea un nuevo contrato y, por tanto, puede originar un nuevo intento. Una propuesta aprobada tampoco se edita; cualquier ajuste vuelve al flujo de versión derivada y aprobación del Sprint 3.

Una ejecución idéntica no se interpreta como actualización de datos. Si ya existe un expediente preparado, en curso, conciliado o validado con la misma huella de propuesta y el mismo conjunto de KPI, la interfaz abre ese expediente y la API rechaza un segundo intento con una respuesta accionable. La comprobación se repite dentro de una transacción con bloqueo de la propuesta para cubrir solicitudes simultáneas. Sólo un intento fallido puede reintentarse mediante la acción controlada correspondiente. Una futura actualización periódica de datos deberá tener una operación explícita de refresco y una nueva identidad de ejecución; nunca reutilizará silenciosamente el botón de carga inicial.

## 4. Expediente acumulativo de validación

La plataforma mantendrá un apartado **Validación del datamart** vinculado a la ejecución:

| Etapa | Evidencia |
|---|---|
| Sprint 3 | Integridad de metadatos, referencias, contrato y reproducción determinística del artefacto aprobado. |
| Sprint 4 | Conteo al grano, pedidos distintos, unidades e importes totales y mensuales entre AdventureWorks OLTP y el datamart. |
| Sprint 4 | Definiciones y conciliación de los KPI variables sugeridos por IA para la necesidad aprobada. La demostración final evidencia al menos cinco. |
| Incremento posterior | Contraste secundario con AdventureWorksDW cuando exista correspondencia semántica documentada. |
| Evaluación final | Rúbrica de juicio de expertos sobre claridad, coherencia y utilidad. |
| Pronóstico | MAPE y RMSE sobre un conjunto temporal de prueba separado. |

Cada control mostrará fuente, resultado esperado, resultado obtenido, diferencia absoluta y relativa, tolerancia, fecha y estado. No se marcará como cumplida una validación que todavía no disponga del artefacto necesario.

## 5. Criterios de aceptación

- [x] La lista contiene sólo propuestas aprobadas y compatibles; las bloqueadas conservan causas accionables.
- [x] La más reciente aparece preseleccionada, pero no puede ejecutarse sin confirmación del analista.
- [x] Se pueden comparar al menos dos propuestas aprobadas sin llamar nuevamente al LLM.
- [x] Cada ejecución conserva de forma inmutable la versión seleccionada.
- [x] La vista previa muestra las operaciones determinísticas que se materializarán y no acepta SQL libre.
- [x] La carga completa es transaccional, auditable y reemplaza el destino sólo después de terminar correctamente.
- [x] La conciliación OLTP-datamart evidencia filas, pedidos, unidades e importes con tolerancias documentadas.
- [x] Cada KPI calculado usa una receta declarativa conocida, conserva su versión y el resultado del control.
- [x] Un fallo conserva la evidencia y permite reintento seguro sin alterar la fuente; la interpretación puede reintentarse sin repetir el ETL.
- [x] Un contrato ya preparado o ejecutado no puede materializarse de nuevo por error: la interfaz abre el expediente existente y la API bloquea también las solicitudes duplicadas o simultáneas.

## 6. Exclusiones de esta especificación

- Selección automática del proveedor LLM “ganador”.
- Ejecución de SQL producido libremente por un LLM o por el navegador.
- Mezcla automática de dos contratos aprobados.
- Declarar equivalencia con AdventureWorksDW sin documentar diferencias de granularidad y reglas.
- Implementar inventario u otro datamart antes de disponer de perfil, constructor y validadores propios.
