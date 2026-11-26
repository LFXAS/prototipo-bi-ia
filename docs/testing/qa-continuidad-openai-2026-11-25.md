# Auditoría correctiva: continuidad, propuestas BI y OpenAI

Fecha local: 25 de noviembre de 2026 (America/Guayaquil).
Estado: auditoría operativa completada; resultados observados y límites diferenciados.
Corte: entorno local SQL Server, dos fuentes de demostración y adaptadores indicados.

## Alcance y condiciones

Se revisa el sistema local existente, sin reinicializar volúmenes ni reemplazar
catálogos, aprobaciones o datamarts. Se atienden los cinco puntos del PDF del tutor
y se integra OpenAI como sexto adaptador. La prueba de cada proveedor se distingue
de sus regresiones simuladas. Las fuentes de demostración son públicas; la clave
de OpenAI fue ingresada por el usuario en la interfaz, sin exposición en este informe.

## Navegación y sesión

Los retornos desde los pasos 2, 3, 4 y 5 de la preparación de Inicio se verificaron
en navegador: LLM, Conexiones, Explorador y Asistente mostraron Atrás y regresaron
al mismo paso. Recargar Configuración LLM conservó el módulo y su origen. La
expiración se observó sin otra solicitud y, después de autenticar, el asistente
recuperó el módulo, la fuente, la propuesta 132 y el paso 3. Esa recuperación no
convirtió la propuesta fallida en una aprobable.

Durante la revisión el usuario sustituyó el máximo inicial del PDF por una
duración mayor y parametrizable. La versión final utiliza el parámetro web de
duración, inicial 60 minutos y rango 15–240. Sus pruebas incluyen valores, límites,
respaldo y login con 120 minutos. Los JWT ya emitidos conservan su expiración previa;
no se presenta como un plazo renovable de inactividad.

## Diagnóstico y corrección de la selección de preguntas

La captura de WideWorldImporters incluida en el PDF muestra un borrador recuperado con tres identificadores de preguntas personalizadas que no forman parte del catálogo visible. El formulario sólo dibuja las preguntas vigentes, pero antes de esta corrección conservaba los identificadores antiguos dentro de la selección enviada. El servidor rechazaba esa solicitud antes de llamar al proveedor de IA. Este resultado no demuestra un fallo de Claude ni una corrupción de los metadatos.

La corrección conserva el objetivo escrito y exige revisar la selección frente al catálogo de la fuente actual. Las preguntas retiradas o deshabilitadas no pueden heredarse silenciosamente de otro catálogo. La validación del servidor se comparte ahora entre sugerencias, redacción, comprobación previa y generación de propuestas; rechaza una solicitud obsoleta sin consumir una llamada al proveedor ni guardar una propuesta. El mensaje explica la cantidad de preguntas retiradas o sus etiquetas cuando todavía existen, y dirige al paso Necesidad. La recuperación de la interfaz debe informar los cambios, invalidar una viabilidad anterior y respetar la consulta inmutable de versiones históricas.

No se han restablecido los catálogos. En esta instalación los dos catálogos conservan seis preguntas cada uno: cuatro estándar y dos personalizadas. Los identificadores de la captura no existen en estos catálogos locales; por ello no se atribuye a esta instalación la eliminación de aquellas preguntas ni se inventa un historial de acciones de otro equipo.

| Caso | Acción o condición | Resultado esperado y obtenido |
|---|---|---|
| Selección personalizada vigente | Validar una pregunta personalizada habilitada en su propia fuente, con metadatos en español o inglés | Se acepta sin cambiar el objetivo ni la selección. |
| Catálogo de otra fuente | Enviar ese mismo identificador a un catálogo que no lo contiene | Se rechaza; no se copia la personalización entre fuentes. |
| Pregunta deshabilitada o sin respaldo | Validar una selección cuya pregunta no está disponible | Se rechaza y se muestra su etiqueta comprensible. |
| Periodicidad retirada | Enviar una periodicidad deshabilitada o no implementada | Se rechaza con orientación para revisar el paso Necesidad. |
| Borrador de la captura | Enviar las tres preguntas ausentes a sugerencia, redacción, viabilidad y generación | Las cuatro operaciones se detienen antes de invocar IA o persistir resultados. |
| Sugerencia inicial | Pedir ideas sin preguntas seleccionadas y con un período válido | El guardado de selección permite esa operación; no obliga a inventar una selección inicial. |

Las nueve regresiones nuevas están en `backend/tests/test_catalog_selection.py`. La ejecución focal de ese archivo junto con `test_need_advisor.py` y `test_proposal_approval.py` completó 110 pruebas sin fallos. También pasaron Ruff y MyPy del módulo modificado. Este corte focal no sustituye la verificación integral final del repositorio.

## Contraste de fuentes y datos ya publicados

Se realizó una auditoría en lectura, con transacción PostgreSQL de sólo lectura y sin ejecutar un nuevo ETL, invocar un LLM, alterar catálogos o cambiar aprobaciones. Se consultaron los catálogos físicos de SQL Server por el mismo adaptador de introspección que utiliza la aplicación. La evidencia está en `evidence/20261125/auditoria-lectura-fuentes-y-publicados.json`.

| Comprobación | AdventureWorks | WideWorldImporters |
|---|---|---|
| Instantánea y estructura física | Coincidencia exacta del hash de la instantánea 2 | Coincidencia exacta del hash de la instantánea 3 |
| Esquemas, tablas, columnas y relaciones | 6; 71; 482; 90 | 4; 48; 546; 98 |
| Propuesta publicada revisada | 129, aprobada | 131, aprobada |
| Verificación estructural y reproducción | Cuatro controles satisfactorios | Cuatro controles satisfactorios |
| Datos publicados revisados | Ejecución 21; esquema `mart_ventas_e21` | Ejecución 22; esquema `mart_ventas_e22` |
| Filas origen y destino; diferencia | 121 317 y 121 317; diferencia cero | 228 265 y 228 265; diferencia cero |
| Importe total | 109 846 381,399888 USD | 198 043 439,45 en moneda de origen |
| Unidades; documentos distintos | 274 914; 31 465 pedidos | 8 950 628; 70 510 facturas |
| Filtro de contraste | 2013 y Northwest | 2015 y California |
| Importe filtrado | 6 015 174,735836 USD | 3 191 769,11 en moneda de origen |
| Unidades y documentos filtrados | 17 452; 2 053 pedidos | 142 247; 1 179 facturas |
| Estado y contrato después de consultar | Permanecieron sin cambios | Permanecieron sin cambios |

Los resultados corresponden a dos expedientes existentes, no a dos ETL ejecutados de nuevo. Los identificadores son propios de esta instalación. La moneda de WideWorldImporters permanece sin una atribución ISO no demostrada. La coherencia de estos casos no garantiza que cualquier petición, proveedor o base sin adaptador pueda ejecutarse.

## Límite observado en una revisión nueva con Claude

La prueba nueva de WideWorldImporters realizada desde la interfaz durante esta auditoría fue detenida en la revisión previa porque el proveedor presentó una fecha junto con un importe como operandos de una medida derivada, incluso después de una reparación acotada. Los tipos numéricos son un requisito obligatorio; una agrupación temporal debe separar la medida y su fecha. Las instrucciones y el mensaje de reparación ya indican esta regla de forma explícita. No se ha relajado el validador, cambiado el objetivo solicitado ni considerado válida la respuesta por cambiar de proveedor. La corrección del borrador obsoleto y este fallo posterior de cumplimiento del contrato son incidencias distintas. Deben registrarse por separado, junto con el resultado real de las pruebas que continúen con OpenAI u otro proveedor.

## OpenAI: integración y primeras pruebas reales

El usuario registró la clave desde el panel protegido. Para los ensayos completos se creó y activó la
configuración OpenAI BI — GPT-6.2 Sol, modelo `gpt-6.2-sol`, esfuerzo medio. La
prueba real de conexión y esquema terminó correctamente. La revisión previa nueva
de WideWorldImporters también terminó, manteniendo límites explícitos sobre moneda,
composición del importe y ubicación actual del cliente.

El primer contrato de generación, propuesta 132, fue bloqueado con 18 errores y
7 advertencias. Su salida parcial no fue aprobada ni materializada. La auditoría
detectó dos recortes internos de contexto: una compactación eliminaba columnas
comprobadas y el payload volvía a limitar cada tabla a ocho columnas; además, el
catálogo de columnas para medidas excluía InvoiceID aunque se necesitaba para un
conteo distinto. La corrección conserva referencias revisadas y permite seleccionar
claves existentes, sin permitir sumarlas como importes. El arreglo de contexto mantuvo primero la compilación 5. El cierre posterior
usa el prompt `sales-bi-v9` y la compilación 6, sin reescribir contratos históricos. La propuesta 132 se conserva como evidencia del fallo previo.

La propuesta 132 permanece fallida e intacta. La capacidad de JSON estricto no
prueba por sí sola la calidad semántica ni un mejor desempeño general del modelo.

## Contexto del chat y recuperación analítica

Se reprodujeron y corrigieron dos carreras: una respuesta de chat pendiente podía
aparecer tras cambiar filtros o ejecución, y una selección pendiente o rechazada
podía guardarse como si estuviera confirmada. Las regresiones fallaron antes y
aprobaron después. Ahora se invalidan respuestas, errores y finalizaciones tardías;
chat y exportaciones esperan que el panel confirme la selección. La recuperación
guarda sólo conexión, ejecución, indicador, año, territorio y vista, nunca datos
ni conversación. Si falta el destino guardado, exige una selección explícita.

## Cobertura operativa y conservación de las decisiones

La propuesta 133 pasó la validación estructural, pero sólo ofrecía tres KPI y no
permitía seleccionar las unidades solicitadas. Una medida física no equivale a
un indicador disponible en el panel. Las reglas de compilación 6 completan una
agregación base únicamente si el requisito viable la pide, existe una medida
compatible única y la receta está comprobada. La interfaz muestra que la adición
proviene de la plataforma y explica su motivo. La revisión humana sigue siendo
obligatoria. Una exclusión explícita no se repone: la cobertura señala lo faltante.

Los indicadores derivados se vinculan a sus entradas y operaciones, sin depender
del nombre dado por el modelo. Se comprobó que retirar sólo el promedio documental
de una selección completa produce cobertura parcial y no modifica el contrato.
La propuesta intermedia 134 tampoco se presenta como un éxito final. Las reglas
1–5 conservan su reproducción; 129 y 131 permanecen aprobadas e inmutables. Su
consulta está permitida. Para una carga nueva se exige una versión actual aprobada.

## Dos casos nuevos completados desde la interfaz

Las propuestas finales se revisaron y aprobaron bajo la autorización del usuario.
Cada ETL creó su propio esquema de destino; no se reemplazó el de una ejecución
anterior. Los cuatro indicadores elegidos se conciliaron contra su fuente.

| Comprobación observada | AdventureWorks | WideWorldImporters |
|---|---|---|
| Modelo durante el ensayo completo | GPT-6.2 Sol, razonamiento medio | GPT-6.2 Sol, razonamiento medio |
| Propuesta aprobada; ejecución nueva | 136; 24 | 135; 23 |
| Contrato; verificaciones | Reglas 6; cuatro satisfactorias | Reglas 6; cuatro satisfactorias |
| Grano | Una línea de pedido | Una línea de factura |
| Destino independiente | `mart_ventas_e24` | `mart_ventas_e23` |
| Filas origen y destino | 121 317 y 121 317 | 228 265 y 228 265 |
| Diferencia de filas | Cero | Cero |
| Indicadores conciliados | Cuatro de cuatro | Cuatro de cuatro |
| Importe registrado total | 109 846 381,399888 USD | 198 043 439,45 en moneda de origen |
| Unidades totales | 274 914 | 8 950 628 |
| Documentos distintos | 31 465 pedidos | 70 510 facturas |
| Promedio por documento | 3 491,0656729664 USD | 2 808,7283995178 en moneda de origen |
| Filtro aplicado | 2013; Northwest | 2015; California |
| Importe filtrado | 6 015 174,735836 USD | 3 191 769,11 en moneda de origen |
| Unidades filtradas | 17 452 | 142 247 |
| Documentos filtrados | 2 053 pedidos | 1 179 facturas |
| Promedio filtrado | 2 929,9438557409 USD por pedido | 2 707,1832994063 por factura |
| Revisión semántica | Nueve etiquetas territoriales revisadas y publicadas; originales conservados | Sin etiquetas pendientes de aprobación |

El oráculo de contraste ejecutó cuatro consultas independientes de sólo lectura
en SQL Server: total y filtro de cada fuente. Se verificaron cantidades e importes,
además de los controles de conciliación del producto. La comparación admite sólo
el efecto de serialización decimal documentado; no se modificaron cifras para
hacerlas coincidir.

El territorio de AdventureWorks es el comercial del pedido. El de
WideWorldImporters procede de la provincia de la ciudad de entrega que consta en
la ficha del cliente al cargar los datos. Ninguno acredita por sí mismo una entrega
física o una ubicación histórica. No se atribuyen costos, margen o impuestos a las
medidas elegidas. Los nombres concretos de tablas en la evidencia son datos de los
casos de prueba; las correcciones del producto no seleccionan esas bases por nombre.

## Interpretación de IA, unidades y aislamiento

Se conversó realmente con el copiloto sobre ambos filtros. Las respuestas
coincidieron con las cifras del panel y explicaron que el promedio es importe
total dividido para documentos distintos, no un promedio de importes de líneas.
La auditoría de WideWorldImporters cumplió nueve criterios; la de AdventureWorks,
diez. Incluyen cifras, denominador, moneda y alcance del territorio. Son resultados
de dos consultas observadas, no una medición general de exactitud de los LLM.

Se corrigió una inconsistencia de presentación: un promedio monetario genérico
podía conservar una unidad sin divisa pese a existir USD verificado en la fuente.
La divisa acreditada es ahora la autoridad de presentación y se conserva el
denominador por documento o unidad. Las unidades físicas no se convierten en
divisas. WideWorldImporters continúa en moneda de origen. La comprobación posterior
mostró que contratos, planes y métricas numéricas no cambiaron por este arreglo.

La recuperación analítica se guarda por conexión en la sesión del navegador.
Se eligieron 2015/California en 23 y 2013/Northwest en 24; al alternar dos veces,
cada fuente recuperó sus propios filtros y su ejecución. No reapareció una
conversación de la otra fuente. La regresión cubre también respuestas de chat
pendientes, selecciones rechazadas y desmontaje del componente. Los datos y los
mensajes del chat no se guardan en ese mecanismo de recuperación.

Se descargaron los PDF y Excel de los dos filtros desde los botones del producto.
Su auditoría y sus copias están en `evidence/20261125/exports/`; no son informes
reconstruidos manualmente para sustituir una exportación de la aplicación.

## Cambio económico solicitado al finalizar

El usuario informó una reducción importante de su saldo de API. Se suspendieron
las nuevas pruebas extensas de IA. La configuración activa se cambió a
**OpenAI BI — Luna económico**, modelo `gpt-6-luna`, razonamiento bajo, conservando
la credencial cifrada existente. Una única prueba breve de conexión y salida
estructurada resultó satisfactoria. No se volvió a generar un datamart con Luna.
Los casos completos 135/23 y 136/24 siguen atribuidos a Sol medio.

Según las fichas oficiales consultadas el 25 de noviembre, Luna cuesta USD 0,10 de
entrada y USD 0,50 de salida por millón de tokens estándar, frente a USD 2 y USD 10
de Sol. Eso supone tarifas 95 % menores para igual volumen, no una garantía de
ahorro idéntico por tarea ni de igual calidad. Sin el detalle de facturación no se asigna toda la variación de saldo a una
llamada o modelo. Los importes personales de la cuenta no se publican en el repositorio. La tabla de modelos, ejemplos aritméticos y pautas para la
sustentación están en la adenda de operación y en su tabla editable.

No hay escalamiento automático a un modelo más caro. Abrir una propuesta aprobada,
consultar un expediente, filtrar datos publicados y exportarlos no vuelve a llamar
al LLM. Solicitar una propuesta, sugerencia, interpretación o respuesta del
copiloto sí puede consumir crédito. Un fallo de cuota no se reintenta a ciegas.

## Verificación integrada y entrega

El cierre final de `make verify` terminó con salida **0**: política de ramas,
configuración Compose, Ruff, formato, MyPy, **656 pruebas de backend**, **80 de
frontend**, build de Vite y compilación de **13 PDF**. La capa backend, sin cambios
respecto del ensayo inmediatamente anterior de 656 pruebas, se reutilizó desde la
caché Docker. Frontend se reconstruyó con el preset económico y su regresión nueva.
Los subconjuntos focales anteriores no se suman a esos totales. El comprobante
`evidence/20261125/verificacion-final.json` distingue estos cortes.

Sólo se observó una advertencia de deprecación externa de Starlette/AnyIO; no fue
un fallo del producto. Los contratos inválidos permanecen bloqueados y no se
presentan como éxitos. Los dos catálogos, datos históricos, volúmenes y secretos
anteriores se conservaron. No se reconstruyó el BI Portable en esta intervención.

La entrega incorpora esta auditoría, especificaciones, manual técnico, bitácora,
incremento correctivo del Sprint 6 y adenda para el manual de aprendizaje. La tesis
Word y los manuales académicos anteriores conservan su corte documental. Esta
prueba acredita los escenarios descritos sobre dos bases SQL Server; no demuestra
compatibilidad operativa con un motor que aún no tenga adaptador ni garantiza la
respuesta correcta de cualquier modelo ante cualquier necesidad.
