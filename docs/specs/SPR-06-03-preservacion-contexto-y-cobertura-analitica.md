# SPR-06-03 — Conservación del contexto y cobertura analítica utilizable

- Fecha: 25 de noviembre de 2026, America/Guayaquil.
- Tipo: corrección del incremento multifuente y de la generación supervisada; no incorpora un dominio nuevo.
- Estado: implementación y regresiones focales verificadas. El acta de QA registra por separado la comprobación integral final y los ensayos reales.
- Contratos: instrucciones nuevas `sales-bi-v9`; reglas nuevas de compilación 6; metadatos y recetas ETL conservan sus contratos.

## Problemas comprobados

1. Un borrador recuperado conservaba preguntas que ya no pertenecían al catálogo visible de su fuente. El servidor bloqueaba la solicitud antes de invocar IA, pero el usuario no podía corregir fácilmente esas opciones invisibles.
2. Las etapas posteriores a la revisión de viabilidad reducían nuevamente las columnas por puntuación y posición. Una referencia ya comprobada podía desaparecer del contexto entregado al modelo. El esquema de respuesta tampoco ofrecía todas las claves existentes aptas para un conteo distinto.
3. Una propuesta podía contener una medida solicitada y declarar su requisito cubierto sin ofrecer un KPI seleccionable que la expusiera en Analítica. La propuesta 133 conservó una medida de unidades, pero el proveedor sólo entregó indicadores de importe, facturas distintas y promedio por factura. La pantalla analítica se construye desde recetas de KPI, por lo que aquella medida no bastaba para analizar unidades.

El registro 132 prueba las pérdidas de contexto y se conserva con su validación fallida. El registro 133 acredita la conservación estructural corregida y permitió identificar la tercera incidencia. No se reescriben estos registros para convertirlos en resultados posteriores.

## Requisitos de la corrección

| Identificador | Regla comprobable |
|---|---|
| Contexto-1 | Conservar las tablas y columnas exactas verificadas para requisitos directos o derivables durante descubrimiento, alcance y preparación de la propuesta. |
| Contexto-2 | El límite de contexto adicional no podrá eliminar evidencia necesaria. Las columnas de relleno se reducen antes que las referencias revisadas. No se inventan columnas ausentes. |
| Contexto-3 | Ofrecer las claves existentes en el catálogo de columnas para conteos; su condición de clave no permite sumarlas ni emplearlas como una magnitud. El rol comercial sigue sujeto al validador. |
| Cobertura-1 | Diferenciar una medida física de un indicador seleccionable. Un resultado agregado solicitado exige una receta de KPI que permita consultarlo. |
| Cobertura-2 | Completar una agregación sólo cuando existe un requisito viable que solicita ese resultado, una única medida compatible y una receta segura e inequívoca. |
| Cobertura-3 | No crear un KPI por cada operando intermedio. La cantidad utilizada para calcular un costo no solicita por sí sola otro indicador de unidades. |
| Cobertura-4 | Conservar un KPI equivalente entregado por el proveedor aunque tenga otro nombre o código. No imponer una lista fija de indicadores ni duplicar la misma receta. |
| Cobertura-5 | Identificar toda adición como decisión de la plataforma originada en un requisito validado. Conservar las decisiones originales del proveedor y explicar la adición en diagnósticos y ajustes automáticos. |
| Revisión-1 | Cuando el analista retire un KPI que ya se le ofreció, respetar esa decisión. La cobertura debe advertir la ausencia y bloquear una aprobación incompatible con la necesidad; no reponerlo silenciosamente. |
| Revisión-2 | No interpretar como exclusión un KPI que el registro de origen todavía no ofrecía. Una versión hija de reglas 6 puede completar por primera vez una omisión de su padre histórico. |
| Selección-1 | Si la selección ETL omite un KPI necesario para los resultados solicitados, indicar una selección parcial y conservar sus motivos. |
| Selección-2 | Vincular los resultados derivados solicitados con recetas verificadas y sus dependencias. Un promedio documental exige importe agregado y conteo distinto del documento; el nombre o código elegido por el proveedor no prueba esa receta. |
| Compatibilidad-1 | Reproducir las reglas persistidas de los contratos 1–5 sin completar KPI nuevos ni cambiar huellas o aprobaciones. |
| Compatibilidad-2 | Permitir consultar los expedientes anteriores y sus datos publicados. Una carga nueva exige una propuesta aprobada con las reglas actuales. |

## Resolución prevista e implementada

### Selecciones del catálogo

La recuperación del borrador se contrasta con el catálogo vigente de su fuente. Se preservan el objetivo y las opciones válidas, se informa la retirada de las opciones obsoletas y se invalida una revisión previa de otro estado. La consulta de una versión histórica conserva sus selecciones originales. La API utiliza una guardia común en sugerencia, redacción, revisión de viabilidad y generación. No elimina preguntas de una solicitud recibida para forzar que pase: la rechaza antes del proveedor y de la persistencia.

### Contexto de generación

Las referencias comprobadas se extraen de los requisitos directos y derivables. La compactación prioriza esas columnas y tablas, y el paquete de propuesta incorpora sus referencias exactas. Los nombres técnicos se conservan; los mismos procedimientos operan con metadatos en español e inglés. Las limitaciones aceptadas se mantienen vinculadas a sus requisitos: una divisa no identificada no autoriza omitir un importe registrado que sí tiene respaldo.

El catálogo de respuesta admite claves existentes para agregaciones de conteo. Esto no sustituye la comprobación de tipos, roles, granularidad ni relaciones. Un identificador cuyo rol documental no esté acreditado no se vuelve una factura sólo por su nombre.

### Indicadores agregados solicitados

Las reglas 6 distinguen las solicitudes explícitas de importe, unidades y documentos de los operandos de fórmulas mayores. Una agrupación o ranking comprobado también puede requerir que su magnitud esté disponible como indicador. Se consideran las agregaciones seguras del catálogo: suma de importes o unidades y conteo distinto de documentos cuando corresponda.

El completado se realiza antes de la revisión humana. Sólo utiliza medidas ya compiladas, sus tipos, sus referencias y su rol comprobado. Si hay varias recetas de la misma función, referencias inexistentes, operandos identificadores para una suma o se alcanzó el límite del contrato, la aplicación no elige arbitrariamente. La cobertura permanece incompleta para su revisión.

El indicador añadido queda disponible en Personalización. Su origen se registra como `validated_requirement`, mientras `provider_kpis` conserva los KPI originales y `platform_kpi_additions` registra requisito, medida, operación y referencias. La exclusión de un indicador previamente ofrecido se registra en el borrador hijo y evita su reposición automática. Si con esa exclusión se incumple una solicitud vigente, la versión hija no se considera aprobable.

La selección ETL comprueba además las recetas derivadas materializadas. Un importe promedio por documento se vincula con una razón cuyo numerador es una suma de importe y cuyo denominador cuenta documentos distintos. Los costos o descuentos agregados, la venta o costo por unidad y el margen se vinculan con sus operaciones y roles de entrada correspondientes. Las etiquetas y códigos del modelo pueden variar: se sigue la receta, no una coincidencia literal de su nombre. Si se omite uno de esos resultados solicitados, la selección queda parcial; esa comprobación no modifica la propuesta ni añade indicadores después de la decisión del usuario.

### Compatibilidad

La nueva conducta queda acotada a `compilation_rules_version=6`. Las versiones 1–5 se reconstruyen con las mismas reglas anteriores y sin completar indicadores adicionales. La revisión histórica puede informar una diferencia de instrucciones o motor; esa advertencia no retira aprobaciones ni cambia datos. Los expedientes publicados se consultan sin generar ni cargar de nuevo. Para otra carga se requiere una versión derivada actual, revisada y aprobada.

## Pruebas y evidencias

| Prueba | Evidencia y resultado del corte focal |
|---|---|
| Borrador con las tres preguntas ausentes de la captura | Nueve regresiones de catálogo; las cuatro operaciones se detienen antes de llamar al LLM o guardar una propuesta. |
| Columnas al final y contexto amplio | Casos con nombres españoles e ingleses y más de doce tablas requeridas; las referencias sobreviven a las tres etapas. |
| Claves documentales | El esquema ofrece claves presentes; SUM sobre un identificador se mantiene inválido en reglas 5 y 6. |
| KPI omitido, equivalente o ambiguo | Se completa sólo la receta única solicitada; se preserva un KPI equivalente y no se elige entre dos medidas incompatibles. |
| Operando intermedio e identificador | No se añade un KPI de unidades por un mero operando de costo ni se suma una clave. |
| Personalización | Retirar el KPI ofrecido conserva la ausencia y produce cobertura incompleta; la primera hija de un padre que no lo ofrecía puede completarlo. |
| Selección ETL | La omisión del KPI solicitado deja la selección parcial. |
| Promedio documental y derivados | Con cuatro KPI del caso real se conserva el resultado completo; sin el promedio por factura la selección queda parcial. Regresiones con códigos y etiquetas arbitrarias comprueban los bindings por receta de promedio, costo, descuento, resultados por unidad y margen. |
| Reproducción 1–5 | Huellas de una misma entrada cotejadas con el compilador del commit anterior, para cada versión persistida. |
| Casos históricos reales | Propuestas 129 y 131 continúan aprobadas, con huellas intactas y cuatro controles estructurales satisfactorios. |
| Nueva versión 6 | La recompilación pura del caso 133 incorpora el indicador de unidades y reproduce exactamente el nuevo contrato; no se presenta como una hija persistida ni como otro ETL. |

Archivos de pruebas: `test_catalog_selection.py`, `test_proposal_context.py`, `test_requested_aggregate_kpis.py` y regresiones de aprobación, selección y rutas ETL. El corte focal integrado final de este incremento completó 226 pruebas junto con Ruff y MyPy. Ese corte no sustituye `make verify` final.

Evidencias seguras:

- `docs/testing/evidence/20261125/auditoria-lectura-fuentes-y-publicados.json`.
- `docs/testing/evidence/20261125/contexto-propuesta-132-diagnostico.json`.
- `docs/testing/evidence/20261125/cobertura-operativa-reglas6.json`.
- `docs/testing/evidence/20261125/seleccion-kpi-promedio-reglas6.json`.

El resultado de la versión hija creada desde la interfaz, la aprobación humana, la eventual ejecución ETL y la prueba analítica deben registrarse en el acta de QA con sus identificadores reales. No se infieren de las pruebas unitarias ni de una reconstrucción sin persistencia.

### Aceptación real registrada después del corte focal

La interfaz produjo y aprobó la propuesta 135 de WideWorldImporters con las reglas 6. La ejecución 23 terminó satisfactoriamente con 228 265 filas de origen y destino, diferencia cero, cinco tablas y cuatro KPI. La auditoría de lectura posterior confirmó los cuatro controles estructurales y el contraste independiente del total y del filtro 2015/California. El copiloto conservó las cifras, el denominador por factura y los límites de moneda y ubicación. Esa aceptación consta en `aceptacion-wwi-propuesta135-ejecucion23.json` y en el texto y auditoría del copiloto, dentro del mismo directorio de evidencias. Las propuestas 129 y 131 permanecieron aprobadas e inmutables durante la comprobación. El acta de QA diferencia esta aceptación observada de los registros intermedios 132–134.

## Límites

Esta corrección no habilita motores nuevos, SQL libre, fórmulas arbitrarias, monedas no demostradas, relaciones inventadas ni ejecución autónoma. Las pruebas de dos fuentes y dos idiomas acreditan los casos observados; no garantizan cualquier solicitud o proveedor. Las medidas ambiguas siguen requiriendo una decisión del analista o un ajuste de la necesidad.
