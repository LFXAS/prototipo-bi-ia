# Auditoría operativa BI + IA: 3 de octubre de 2026

**Código:** QA-E2E-20261003

**Alcance:** AdventureWorks2022 y WideWorldImporters, dominio ventas, SQL Server

**Rama:** `fix/qa-operational-20261003`

**Resultado global:** ambos orígenes completaron un ciclo nuevo hasta tablero y copiloto: AW #98/#14 y WWI #114/#15. Permanecen límites de rol autenticado y generalización a otros motores.
**Entorno:** aplicación local en Docker Compose; sin filas ni credenciales remitidas a la IA. Los metadatos estructurales y la necesidad sí se remiten al proveedor activo al generar.

## Roles de evaluación y criterio de aceptación

| Perspectiva | Criterio observable |
|---|---|
| QA | Navegación sin excepción, fuentes aisladas, errores recuperables, contrato y reconciliación verificables, regresión automatizada. |
| Analista BI | Granularidad, medidas, denominadores, rutas de cliente/territorio y alcance comercial comprobables; no aprobar sustituciones semánticas. |
| Gerencia comercial | Un pedido no equivale automáticamente a una venta facturada; se distinguen promedio por línea y promedio por documento; se muestran límites antes de decidir. |

Se crearon los roles **Analista BI** y **Gerente comercial** sin asignar usuarios. El segundo, creado después de la autorización explícita del usuario, recibió exclusivamente `analytics.dashboard.read`, `parameters.connections.read` y `analytics.reports.export` (descarga de informes, sin modificar datos). No se amplió acceso a ninguna cuenta. La aprobación de propuestas y la ejecución de ETL se efectuaron con la sesión administrativa de prueba que ya tenía permisos, registrando decisión humana en la aplicación. Esto prueba el flujo administrativo, pero no demuestra todavía un recorrido completo de usuario autenticado bajo cada nuevo rol.

## Método y datos de control

Se recorrieron las pantallas reales: Inicio, Explorador de esquema, Catálogo analítico, Asistente, validación, Datamart, Analítica y copiloto. Además se contrastaron agregados con consultas SQL de sólo lectura en los orígenes y se ejecutaron pruebas automáticas. La instantánea AdventureWorks #2 contiene 6 esquemas, 71 tablas, 482 columnas y 90 relaciones; WideWorldImporters #3 contiene 4 esquemas, 48 tablas, 546 columnas y 98 relaciones. El catálogo de AdventureWorks conserva las dos preguntas adicionales del analista y no las traslada al catálogo de WWI.

Necesidad común inicial: comparar mensualmente unidades y ventas por producto, cliente y territorio, identificar contribuciones y **promedio por transacción**, conservar trazabilidad documental y mostrar costos/márgenes sólo con columnas verificadas. Para WWI se refinó a **ventas efectivamente facturadas, no pedidos solamente registrados**, con fecha e identificador de factura.

## Matriz reproducible de escenarios

| Caso | Pasos y criterio esperado | Resultado obtenido | Estado |
|---|---|---|---|
| QA-01 | Cambiar AW/WWI en Inicio y Explorador; revisar versión y entidades. | Fuentes y conteos distintos; se corrigió un instante en que la respuesta de Roles se trataba como instantánea al navegar. Test de regresión agregado. | Aprobado tras corrección |
| QA-02 | Inspeccionar catálogo por conexión. | AW: 6 preguntas, incluidas 2 personalizadas; WWI: 4. Una pregunta personalizada seleccionable sin evidencia ya no se etiqueta como verificable. | Aprobado |
| QA-03 | Generar necesidad mensual AW y revisar medidas. | Versión #97 proponía `AVG(LineTotal)` como promedio por transacción. No se aprobó. Regla universal corrige a `SUM(importe) / COUNT(DISTINCT documento)` o etiqueta honestamente promedio por línea. | Aprobado tras corrección |
| QA-04 | Verificar y aprobar versión AW corregida. | Versión #98; 0 errores, 3 advertencias de candidatos excluidos, 6 referencias válidas, reproducción determinística coincidente. Aprobación registrada. | Aprobado |
| QA-05 | Materializar AW, conciliar origen/destino y publicar etiquetas. | Ejecución #14: 121.317/121.317 filas, diferencia 0, 5 tablas; 9 KPI calculados. Se excluyó la «traducción» inútil de códigos de país y se publicaron Europe/Europa, North America/América del Norte, Pacific/Pacífico. | Aprobado |
| QA-06 | Comparar ventas y promedio por pedido AW con SQL de sólo lectura. | Origen: 121.317 líneas, 31.465 pedidos, 109.846.381,4250 de importe; cociente 3.491,065673. Tablero: 109,8 M y 3.491,07. | Aprobado |
| QA-07 | Cambiar año 2014, inspeccionar gráficos, consultar Top 5 en Southwest y cambiar a WWI. | Filtro: 20,1 M, 11.761 pedidos, promedio 1.705,46; copiloto consultó Top 5 con denominador territorial 24.184.609,60 y alcance explícito. Al cambiar a WWI aparecen ejecución #13, productos/territorios y período de WWI, no AW. | Aprobado; revisar redondeo narrativo de centavos |
| QA-08 | Generar propuesta WWI con necesidad ambigua «documento comercial». | Versión #99 eligió `Sales.OrderLines`, no facturas. Se conservó para auditoría y **no** se aprobó. | Hallazgo de negocio |
| QA-09 | Pedir ventas facturadas y comprobar si orden ≠ factura. | #100 mantuvo `OrderLines` pese al objetivo. El validador exige línea, identificador y fecha de factura; la selección de metadatos prioriza el evento de factura sin fijar nombres de tablas de una base particular. #114 usa `Sales.InvoiceLines` y `Sales.Invoices.InvoiceDate`. | Aprobado tras corrección |
| QA-10 | Reintentar necesidad facturada con Claude y Groq. | Groq alcanzó cuota temporal; Claude inicialmente devolvió contratos inválidos. El adaptador de Claude pasó a salida JSON estructurada nativa, con un reintento acotado si se agota la salida. La validación local sigue siendo obligatoria. Claude generó #113; #114 es su revisión supervisada. Gemini produjo HTTP 400 en el intento autorizado; Ollama no hizo falta. | Aprobado con Claude; Groq/Gemini no superaron este caso |
| QA-11 | Comparar eventos y montos WWI con SQL de sólo lectura. | `OrderLines`: 231.412 filas, 73.595 pedidos y 177.634.276,40; `InvoiceLines`: 228.265 filas, 70.510 facturas y 198.043.439,45 de `ExtendedPrice`. Este último incluye 172.261.341,20 de precio×cantidad y 25.782.098,25 de impuesto. No son intercambiables ni debe llamarse «venta neta» al total con impuesto. | Aprobado |
| QA-12 | Crear rol Gerente comercial sin asignarlo. | El primer intento fue detenido por autorización insuficiente; tras permiso específico del usuario, se creó con tres permisos de consulta/descarga y ningún usuario asignado. Falta una prueba autenticada con cuenta gerencial. | Creación aprobada; uso autenticado pendiente |
| QA-13 | Preguntar al copiloto de WWI por limitaciones y por el evento comercial real. | La primera respuesta omitió pedido frente a factura. Se corrigió el contexto y se añadió una salvedad determinística; la nueva respuesta declara que son pedidos registrados, no facturas emitidas. Se añadió instrucción para no confundir el filtro actual con una imposibilidad de comparar períodos. | Aprobado tras corrección; respuesta abierta debe seguir bajo revisión humana |
| QA-14 | Revisar una propuesta de Claude para facturas sin aceptar afirmaciones técnicas falsas. | #111 decía que `ExtendedPrice` no existía; la instantánea demuestra lo contrario y la regla nueva la bloquea. #112 omitía venta total pese a la cobertura declarada; la cobertura se recalcula del contrato real. #113 propuso máximo de línea como producto líder y AVG de línea como promedio por cliente. Ambos KPI se excluyeron en la personalización #114; la regla bilingüe ahora bloquea esas fórmulas si reaparecen. | Aprobado tras corrección |
| QA-15 | Aprobar #114, preparar y ejecutar ETL de facturas. | #114 aprobada con decisión registrada. Ejecución #15: 228.265/228.265 líneas, diferencia 0, cinco tablas, seis KPI conciliados. Total 198.043.439,45, 70.510 facturas, promedio 2.808,73 por factura. No se asignó divisa porque no consta una moneda única comprobada. | Aprobado |
| QA-16 | Filtrar 2015, consultar al copiloto y alternar #15/#13/AW #14. | En #15, 2015 muestra 62.090.220,81, 22.250 facturas y promedio 2.790,57. Claude citó las mismas cifras, explicó SUM/COUNT DISTINCT y distinguió facturas de pedidos y de cobros. #13 conserva 177,6 M y encabezado de pedidos; AW #14 conserva USD 109,8 M y 31.465 pedidos. No se observaron cruces al alternar. | Aprobado |

Las consultas de control fueron agregados de `Sales.SalesOrderDetail`, `Sales.OrderLines` y `Sales.InvoiceLines`; no se extrajeron ni documentaron filas individuales ni secretos.

## Hallazgos y decisiones de BI

1. **Denominador de promedio:** `AVG(importe de línea)` responde «promedio por línea», no «promedio por transacción». La versión #98 materializó un cociente entre ventas totales y documentos distintos. La conciliación directa coincide al centavo mostrado.
2. **Evento comercial WWI:** el datamart histórico #13 usa pedidos. Aunque los 231.412 registros están conciliados, el número 177,6 M no debe presentarse como facturación emitida. La cabecera analítica y la salvedad obligatoria del copiloto ahora lo advierten; el nuevo validador bloquea propuestas de facturación construidas sólo sobre pedidos.
3. **Costo en WWI:** `LastCostPrice` es un último costo registrado, no prueba de costo histórico al momento de cada factura. La versión #100, que lo usó, no fue aprobada. La evaluación gerencial debe considerar ese margen como estimación, o excluirlo hasta disponer de costo histórico verificable.
4. **Proveedores:** un fallo de JSON o límite de cuota no autoriza usar salida incompleta ni modificar el origen. Claude se recuperó mediante su contrato de salida estructurada, sin relajar la validación común. Groq devolvió 429 y Gemini HTTP 400; no se tomó ninguna salida inválida. Ollama quedó como alternativa no utilizada en este recorrido. La preferencia de proveedor no sustituye la comprobación determinística.
5. **Roles:** ambos roles existen sin usuarios asignados. La existencia de un rol no demuestra segregación de funciones sin una prueba autenticada de cada perfil; ese caso sigue abierto.
6. **Lectura gerencial:** WWI #15 refleja facturación emitida, no cobro; `ExtendedPrice` incluye impuesto. #13 refleja pedidos registrados y no debe compararse como si fuera la misma métrica. La selección de expediente en el panel permite consultar ambos de forma separada, cada uno con linaje.

## Evidencia visual

Las capturas fueron tomadas en la aplicación durante la ejecución, sin recrear interfaces. Los números son identificadores observados, no datos de ejemplo. Véanse en `evidencias/qa-20261003/` las capturas de explorador WWI, catálogo AW, validación #98, conciliación #14, tablero y copiloto AW, tablero WWI #13 con advertencia de pedidos, fallo Claude y límite Groq. Se añadieron `31_wwi_facturas_etl15.png` (conciliación de #15) y `32_wwi_facturas_copiloto2015.png` (respuesta contextual de Claude).

## Pruebas automatizadas y estado de cierre

Los tests focalizados del backend para viabilidad, proveedor, propuesta, ETL y analítica, y los del frontend para navegación y tablero, pasaron tras las correcciones. La verificación integral `make verify` incluyó 176 pruebas backend, controles estáticos, frontend y compilación documental. La revisión visual del PDF se registra al finalizar esta auditoría. La ejecución histórica #13 permanece disponible, claramente identificada como pedidos.

**Conclusión:** las dos fuentes SQL Server completaron metadatos → catálogo → propuesta supervisada → aprobación → ETL → conciliación → tablero → copiloto. El caso WWI obligó a diferenciar pedido, factura e impuesto, y a corregir salida y semántica de Claude sin codificar una propuesta exclusiva para ese modelo. La evidencia sustenta estos dos escenarios observados, no una garantía universal para bases, modelos, idiomas o dominios no ensayados. Los roles nuevos aún carecen de prueba de autorización con usuarios asignados.

## Adenda QA-NEED: factibilidad y sugerencias previas

Esta adenda es posterior a los ciclos ETL anteriores. No los presenta como pruebas
de las nuevas rutas. La auditoría encontró que el botón de redacción enviaba sólo
objetivo, preguntas, periodicidad y hash, sin estructura; también encontró falsos
positivos de viabilidad por columnas desconectadas o de tipos inadecuados.

| ID | Preparación y acción | Criterio y resultado observado | Evidencia |
|---|---|---|---|
| NEED-01 | Fixture con venta y costo en tablas sin FK; pedir margen. | No clasificar el costo ni el margen como respaldados. Cumple. | `test_copilot_needs.py` |
| NEED-02 | Importes/cantidades/fechas con tipos textuales o desconocidos. | Tipos incompatibles se excluyen; tipos desconocidos quedan por decidir. Cumple. | `test_copilot_needs.py`, `test_need_advisor.py` |
| NEED-03 | Invertir FK o incompletar una FK compuesta. | No acreditar rutas con fan-out o sin todos los componentes. Cumple. | Ambas suites backend anteriores |
| NEED-04 | Pedidos y tabla de facturas desconectada; solicitar facturación. | No aceptar un identificador aislado como prueba de ventas facturadas. Cumple. | `test_copilot_needs.py` |
| NEED-05 | Metadatos sintéticos en español e inglés; cambiar orden de tablas. | Referencias genéricas y resultados estables, sin nombres de bases codificados. Cumple. | Ambas suites backend anteriores |
| NEED-06 | Proveedor simulado inventa una columna y añade requisito climático/predictivo no disponible. | Evidencia inventada descartada; sugerencia no adoptable; límite visible en evaluación. Cumple. No prueba exhaustividad de todo LLM real. | `test_need_advisor.py` |
| NEED-07 | Introducir contraseña y muestras de filas en fixture; preparar contexto. | Sólo salen nombres, tipos, claves y relaciones. Cumple. | `test_need_advisor.py` |
| NEED-08 | Ausencia de consentimiento o cambio de destino activo. | Cero llamadas al proveedor simulado. Cumple. | `test_need_advisor.py`, `App.test.tsx` |
| NEED-09 | Sugerir con objetivo vacío; escoger texto; recibir respuesta tardía tras cambio de fuente. | No sustituir texto sin elección; invalidar contexto y respuesta obsoleta. Cumple. | `App.test.tsx` |
| NEED-10 | Cambiar fuente, objetivo, preguntas o período de evaluación. | Huella de entrada diferente; no reutilizar evaluación anterior. Cumple. | `test_need_advisor.py` |
| NEED-11 | Abrir el asistente local WWI, paso Necesidad. | Botón nuevo, destino Claude y consentimiento sin marcar; acciones de envío bloqueadas. Observado. | Comprobación visual local, sin llamada externa |
| NEED-12 | Probar sugerencias, redacción y viabilidad nuevas con Claude y ambas fuentes reales. | Autorizado posteriormente por el usuario; resultados desglosados en la ampliación de prueba real siguiente. | Capturas y auditoría local |
| NEED-13 | Combinar evaluación IA/reglas, enriquecer cálculos y validar propuesta; después retirar el margen. | Cobertura correcta con el resultado derivado; bloqueo si sólo quedan operandos. Cumple. | `test_copilot_service.py` |
| NEED-14 | IA cambia el objetivo al analizar o se cambia proveedor antes de generar. | La evaluación ajena se rechaza y la generación exige el destino autorizado. Cumple. | `test_need_advisor.py`, `App.test.tsx` |

Se aplicó la migración aditiva `20261003_19`, que conserva revisiones previas sin
sobrescribir propuestas o ejecuciones. Las suites focalizadas de necesidades y
servicio aprobaron 83 casos; el asesor nuevo aprobó 11; frontend aprobó 33, incluyendo
consentimiento, selección humana y respuestas tardías. La verificación integral se
completó sin errores (`make verify`, salida 0). La captura
`evidencias/qa-20261003/33_necesidad_metadatos_consentimiento.png` documenta el paso
Necesidad sin texto y sin autorización marcada, no una respuesta real de Claude.

En el corte previo al ensayo autorizado, la regresión acumulada alcanzó 201 casos backend y 33 frontend; los
controles de formato, tipos y compilación se ejecutan en Docker. El aviso de
deprecación de Starlette/AnyIO no constituye un fallo de prueba.

La comprobación determinística de las instantáneas reales confirmó cinco requisitos
directos en AW y cinco directos más dos derivables en WWI, sin pendientes para los
objetivos de control. Se corrigió la prioridad de una fecha comercial exacta con FK
frente a `ModifiedDate`: AW eligió `Sales.SalesOrderHeader.OrderDate` y WWI
`Sales.Invoices.InvoiceDate`. La periodicidad seleccionada obliga a comprobar una
fecha incluso cuando el texto no menciona tiempo. Esto no es un ensayo del nuevo LLM.

Juicio BI: «derivable» significa que existe una ruta/fórmula candidata, no que la IA
haya probado importes, historia o calidad de filas. La guía debe mostrar qué se usará,
qué falta y qué decisión corresponde al analista. Las sugerencias no aprueban un ETL.

## Ampliación QA-NEED real con Claude

Después de la autorización explícita, se probaron las rutas nuevas mediante la
interfaz local con `anthropic-cloud` y `claude-haiku-4-5-20251001`. Se enviaron sólo
necesidades de prueba y la estructura permitida de las instantáneas; no filas,
credenciales ni documentos aprobados. Estas pruebas son adicionales a los ciclos
AW #98/#14 y WWI #114/#15, y no se presentan como una repetición de esos ETL.

### Incidentes iniciales y criterio de corrección

1. Al sugerir desde WWI sin objetivo inicial, ambas opciones quedaron no utilizables.
   El servidor detectó rutas que no preservaban la granularidad, una capacidad sin
   validador y una referencia temporal incompatible. No se adoptó ninguna opción.
2. Una limitación redactada por Claude afirmó que `ExtendedPrice` excluía impuestos.
   Esa afirmación no se podía probar con los nombres y tipos enviados y contradice
   la conciliación previa de esta instalación. Se reforzó la prohibición general
   de inferir impuestos, moneda o costo histórico a partir de nombres de columnas.
   El texto del modelo sigue siendo una interpretación sometida a revisión, no
   evidencia financiera certificada.
3. La reformulación de un objetivo simple de facturación se bloqueó por rutas.
   Un control local del mismo esquema, con el hecho en `Sales.InvoiceLines`, pasó
   cinco requisitos directos (importe, unidades, fecha, producto y cliente). La
   captura de FK era correcta; no se modificaron los metadatos para aceptar al LLM.
4. La revisión de viabilidad rechazó una respuesta que alteraba el texto original.
   No se guardó una evaluación para otro alcance. La recuperación conserva ese
   control y limita la corrección automática a un reintento con feedback concreto,
   el mismo destino consentido y los mismos validadores.

El criterio de aceptación no es que todo texto resulte viable: es que cada
requisito tenga respaldo o una limitación explícita, que no se borren objetivos
no factibles, y que ninguna sugerencia apruebe o ejecute por sí sola un datamart.

### Contradicción semántica adicional detectada

La revisión AdventureWorks #2 del asesor clasificó «Costo unitario» como directo
usando `UnitPrice`, aunque su propia explicación reconocía que era precio de venta.
Se rechazó esa interpretación en QA; no se generó ni aprobó un contrato a partir de
ella. La validación de existencia y tipo numérico no era suficiente. Se añadió
contraste de roles conocidos en español e inglés para precio frente a costo, tasa
frente a importe de descuento e identificadores frente a medidas monetarias.
Los nombres que no permiten confirmar un rol quedan pendientes de interpretación.
La versión de revisión se incrementa para que una evaluación persistida anterior
no pueda reutilizarse como si hubiera superado los nuevos controles.

Las primeras sugerencias de AW fueron estructuralmente utilizables, pero su texto
incluyó afirmaciones de estado de pedidos no verificadas. Por ello la interfaz
señala «Necesidades propuestas para revisar» y «Referencias existentes en la
instantánea». Los nombres y las FK son verificables; el significado de los estados
y la composición de los importes siguen requiriendo evidencia del negocio.

### Repetición final, resultados y criterio de aceptación

La repetición mantuvo las instantáneas #2 (AW) y #3 (WWI), el mismo proveedor y el
contrato común. No se añadieron reglas por nombre de base, no se alteró el catálogo
y no se aprobaron propuestas ni se ejecutaron cargas durante esta ampliación.
Los números de revisión siguientes pertenecen a `business_need_reviews`, **no**
a versiones de propuesta o expedientes ETL.
Los conteos combinan requisitos de las reglas y de la revisión IA; no equivalen
al número de KPI únicos ni a observaciones estadísticas independientes.

| Caso | Preparación y pasos reproducibles | Resultado obtenido | Juicio QA |
|---|---|---|---|
| NEED-15 | Simular precio como costo, tasa como importe e identificador como dinero; repetir con roles válidos ES/EN y nombres desconocidos. | Contradicciones rechazadas; roles desconocidos quedan ambiguos. `need-review-2` obliga a reevaluar las revisiones anteriores, sin borrarlas. | Regresión automatizada aprobada; no prueba comprensión de todos los nombres posibles. |
| NEED-16 | WWI, mensual, sin objetivo inicial: autorizar y solicitar sugerencias. | En la repetición apareció una opción utilizable y otra bloqueada. Elegir una opción no aprueba ni genera nada y obliga a revisar de nuevo su alcance. | Adopción supervisada observada; no se exige aceptar toda salida del modelo. |
| NEED-17 | AW, objetivo de importe/unidades por producto, pregunta de producto y características: pedir reformulación. | Tras dos respuestas, una capacidad sin validador mantuvo «Usar esta redacción» deshabilitado. Se usó «Mantener mi redacción» y el texto original quedó conservado. | Límite funcional vigente de la reformulación; rechazo seguro, no reformulación exitosa. |
| NEED-18 | WWI, pregunta evolución temporal, mensual: escribir el objetivo de control indicado debajo, consentir y validar. | Revisión #5: 6 directos, 2 derivables, 4 advertencias y 0 no disponibles; una respuesta del asesor. Antes de aceptar los cuatro límites, generar estaba deshabilitado; después se habilitó. No se pulsó generar. | Caso positivo aprobado hasta la revisión previa; no constituye un nuevo ETL. |
| NEED-19 | AW, pregunta producto/características, mensual: conservar el objetivo de control, consentir y validar. | Revisión #6: 11 directos, 1 derivable, 5 advertencias y 0 no disponibles; una respuesta. Aceptar los cinco límites habilitó generar sin ejecutarlo. | Caso positivo aprobado hasta la revisión previa. |
| NEED-20 | WWI: solicitar ventas mensuales y explicar influencia de temperaturas externas por ciudad. | Revisión #4 identificó clima no disponible y distinguió sensores frigoríficos/vehiculares de meteorología. La generación permaneció deshabilitada; no se aceptó alcance parcial. Este ensayo aún detectó agrupación temporal mal tipada, corregida antes del caso NEED-18. | Negativo climático aprobado; se conserva el incidente adicional, sin ocultarlo. |
| NEED-21 | Modificar el texto y cambiar de WWI a AW; retomar tras expiración normal de sesión. | El consentimiento se desmarcó al cambiar el texto; AW no reutilizó la revisión WWI. La sesión exigió autenticación y el nuevo caso siguió con su instantánea y catálogo propios. | Aislamiento y recuperación observados. |

**Objetivo WWI final:** «Analizar mensualmente el importe registrado de las líneas
de factura, conservando la trazabilidad con su factura y sin inferir cobros ni
composición de impuestos.»

**Objetivo AW final:** «Comparar por mes el importe registrado y la cantidad de
unidades de las líneas de venta por producto, conservando su identificador de pedido.»

**Objetivo negativo:** «Analizar las ventas mensuales registradas y explicar cuánto
influyó el clima de cada ciudad usando temperaturas externas que no están en esta
base de datos.»

Las advertencias finales tratan composición del importe, fecha comercial frente a
cobro, estados/población no filtrados implícitamente y cobertura de atributos. No
se aceptó que un precio fuese costo ni que una fecha fuese operando monetario. La
agrupación por período se separó de las derivaciones aritméticas en las instrucciones
y en el feedback del reintento, manteniendo el rechazo de tipos incompatibles.

La interfaz distingue para `ai:*` «Referencia estructural comprobada», «Derivación
candidata» e «Interpretación propuesta por IA (no ejecutable)». No presenta el texto
libre del modelo como una fórmula ejecutable certificada. La generación posterior
sigue obligada a construir y validar su propio contrato controlado.

### Capturas añadidas

| Archivo | Evidencia y alcance |
|---|---|
| `34_necesidad_objetivo_rechazado.png` | Rechazo inicial de una respuesta que cambió el objetivo. |
| `35_necesidad_clima_no_disponible.png` | Clima ausente y agrupación temporal rechazada; captura del incidente antes del ajuste final de etiquetas. |
| `36_necesidad_wwi_revision.png` | Revisión final WWI: 6 directos, 2 derivables y 4 advertencias. |
| `37_necesidad_wwi_continuacion.png` | Límites WWI aceptados y continuación habilitada, no ejecutada. |
| `38_necesidad_aw_interpretacion.png` | Etiquetas nuevas: evidencia estructural separada de interpretación no ejecutable. |
| `39_necesidad_aw_revision.png` | Revisión final AW: 11 directos, 1 derivable y 5 advertencias. |
| `40_necesidad_aw_continuacion.png` | Decisión explícita del analista y continuación AW habilitada. |

Todas están en `evidencias/qa-20261003/` y provienen del navegador real. Los registros
persistidos y eventos de auditoría se consultaron en modo de sólo lectura para
corroborar conteos e intentos. No se calculó una tasa de éxito: hubo cambios entre
repeticiones y la muestra no representa un experimento estadístico controlado.

**Cierre de la ampliación:** los dos objetivos finales superaron la revisión
estructural supervisada. La prueba negativa detectó información ausente. La
reformulación automática no logró una opción utilizable en la última repetición
AW y permanece documentada como límite, con alternativa de mantener el texto del
analista. No se garantiza que toda respuesta de un LLM sea correcta o utilizable,
ni se extrapola esta evidencia a otros modelos, motores o idiomas no ensayados.

La regresión final `make test` terminó con salida 0: **231 pruebas backend y 34
frontend**, Ruff, formato, Mypy, ESLint y compilación TypeScript/Vite. El primer
intento se detuvo por formato de `copilot/service.py`; se aplicó el formato y se
repitió el bloque completo con éxito. Permanece un aviso de deprecación
Starlette/AnyIO sin fallo de prueba. Los conteos anteriores son cortes históricos,
no el resultado final de esta ampliación.

La verificación integral posterior `make verify` también finalizó con salida 0:
configuración de entornos, política de ramas, regresión y compilación de los 11
PDF del proyecto. Ocho PDF contienen actualizaciones en esta intervención.

La revisión visual final cubrió el panorama de los ocho PDF actualizados y las
páginas modificadas a resolución legible: auditoría (15 páginas), bitácora (57),
manual (52), tesis (22) y cuatro sprints (40 en conjunto). Se corrigió una línea
viuda en Sprint 3 y dos comandos sin espacios en el control documental de tesis;
ambos se recompilaron y reinspeccionaron. No se observaron cortes ni superposiciones
en las páginas revisadas. Los avisos tipográficos menores de identificadores
largos no impidieron la compilación ni recortaron contenido visible.
