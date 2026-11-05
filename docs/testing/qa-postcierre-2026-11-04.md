# QA posterior al cierre del Sprint 6 - 4–5 de noviembre de 2026

**Naturaleza:** revisión correctiva del incremento existente, iniciada el 4 y cerrada
documentalmente el 5 de noviembre, hora de Guayaquil. El nombre de este archivo
conserva la fecha de inicio. No es un sprint nuevo ni una validación universal de
proveedores, fuentes o lenguaje natural.

**Corte de código anterior al ajuste adicional de presentación:** `bf50172`,
`make verify` V4 terminó con código 0: 454 pruebas backend,
un aviso Starlette/AnyIO sin fallo, 46 pruebas frontend, Ruff/formato en 91 archivos,
Mypy en 57 archivos, controles de ramas, Compose, workflow, lint, construcción y
documentación aprobados. Se revisó
`/tmp/bi-make-verify-final-v4-20261105.log`; los registros de ejecución no se
incorporan a Git. El ajuste posterior de unidades y disposición de conciliación
se registra al final de este documento con su propia verificación.

**Cierre adicional de código:** `8f1c7d1`, posterior a `bf50172`, aprobó `make verify`
V6 con salida 0: 454 pruebas backend y 48 frontend, más los controles de rama,
Compose, workflow, calidad, construcción y los doce documentos LaTeX. Registro:
`/tmp/bi-make-verify-final-v6-20261105.log`. V5 había completado esas pruebas y
compilaciones, pero su sesión retornó 143: se conserva como intento interrumpido,
no como cierre aprobado. La regeneración final de los tres documentos actualizados
y su inspección visual se distinguen de esta verificación de código.

## Problemas reproducidos y contrato de la corrección

| ID | Problema observado | Comportamiento corregido |
|---|---|---|
| QA-ROOT-01 | Trazabilidad entre línea y pedido clasificada como `invoice_event` aunque se pedían pedidos. | `transactions`/`identifier` conserva claves; factura exige intención positiva original y PK completa de hecho cabecera o FK completa a su cabecera. Un ACK no habilita una contradicción técnica. |
| QA-ROOT-02 | Importe dividido entre un ID numérico. | PK/FK/identificadores no son operandos monetarios; el promedio documental exige razón de agregados válidos. |
| QA-ROOT-03 | Conteo de líneas convertido en pedidos conservando etiqueta de líneas. | No cambiar población silenciosamente: reglas 2 excluyen el conteo de líneas que el contrato transaccional actual no representa. |
| QA-ROOT-04 | Ranking interpretado como preferencias o entrega histórica. | Delimitar cifra, filtros y denominador; no inferir demanda, eficacia, mercado, causalidad o historia no demostrados. |
| QA-ROOT-05 | Serie siempre mensual y herencia sin normalizar códigos. | Resolver KPI o herencia entre vocabularios cerrados y agrupar día/semana ISO/mes/trimestre/año con etiquetas y subtítulo correctos. |
| QA-ROOT-06 | Moneda por unidad/pedido tratada como conteo, con pérdida de decimales. | Unidad contractual decide precisión; importes, razones y cantidades fraccionarias conservan dos decimales y sólo conteos explícitos usan cero. |
| QA-ROOT-07 | Correo editable ignorado por API, roles enviados en edición protegida y errores de catálogos convertidos en vacíos guardables. | Correo de sólo lectura, omitir roles al editar cuenta protegida y bloquear ante carga/error hasta recarga válida. |
| QA-ROOT-08 | Respuesta tardía del padre interfería con la hija guardada. | Adoptar ID/estados de hija e ignorar recuperaciones/evidencias tardías, sin mutar el origen. |
| QA-ROOT-09 | Sugerencias libres pedían margen ausente. | Hasta tres preguntas desde métricas agrupables y ejes materializados; intención usa el mismo catálogo. |
| QA-ROOT-10 | Cautela negada sobre utilidad añadía margen y ACK falso. | Escáner acotado de peticiones positivas y exclusiones coordinadas ES/EN; no ocultar una petición positiva real de otra pregunta. |
| QA-ROOT-11 | Personalización mostraba referencia cruda en vez del contrato compilado y exclusiones seleccionadas. | Enlazar por nombre/código, mostrar origen/rol/agregación/receta efectivos, exclusiones desmarcadas y razón con dependencias; no enviar salidas sin decisión editable. |
| QA-ROOT-12 | Reporte sin fuente/base/zona y posibilidad de convertir texto en fórmula o vínculo XLSX. | Imprimir fuente/base y fecha ISO con offset recibido o zona no informada; cadenas literales sin fórmulas ni vínculos automáticos. |
| QA-ROOT-13 | Chat 19 atribuyó vigencia territorial a fecha del hecho sin prueba histórica. | Procedencia estructurada y cautela íntegramente de plataforma; ventana ETL no demuestra vigencia al hecho, entrega real, lectura exacta o última modificación del origen. Primer hallazgo visible también en modo ejecutivo. |
| QA-ROOT-14 | Nombre de configuración LLM perdido al elegir preset en la verificación integral. | Inicialización por identidad de registro, actualizaciones funcionales/valores capturados y limpieza sólo tras éxito; nombre conservado en preset y envío. |
| QA-ROOT-15 | En la UI actual del expediente 18, la etiqueta del promedio se superponía al valor y una razón seguía mostrando moneda de origen aunque USD estaba verificado. | Columnas contraíbles con salto de línea y apilado a 760 px; formatter basado en unidad completa y divisa comprobada, conservando denominador y precisión. La verificación adicional se registra por separado del V4. |

No se introduce SQL libre, ejecución autónoma, API pública nueva ni migración de
tablas. Se conservan consentimiento, permisos, aprobación y evidencia histórica.

## Versiones y fronteras

- **`need-review-6`:** revisión vigente para generaciones nuevas. Conserva los controles
  de ranking y exclusiones de v4/v5 y precisa tildes, negación y anclas documentales;
  el escáner determinístico reconoce menciones positivas,
  exclusiones y cautelas coordinadas, incluidas preguntas, derivaciones y facturas.
  «Sin asumir moneda, utilidad ni composición fiscal» no solicita margen. Una
  pregunta positiva conserva su requisito y una contradicción debe resolverse.
  No se afirma comprensión exhaustiva del lenguaje natural.
- **Trazabilidad:** capacidad existente `transactions`, `kind=identifier`, con
  `identity_references` verificadas. No se añadió capacidad al catálogo.
  `invoice_event` exige petición positiva en objetivo y preguntas originales,
  respetando exclusiones, y prueba de PK completa declarada/referencias exactas del propio hecho cabecera o FK completa hacia cabecera de factura.
  Una contradicción persistente tras una reparación devuelve 422 sin revisión
  continuable sólo por ACK.
- **Ranking:** `kind=ranking` usa capacidades existentes de producto/cliente/territorio
  y `analytical_operations`, separado de columnas. Primero comprueba requisitos de
  origen y después enlaza cada par medida/dimensión y rutas, aunque el JSON los
  presente en otro orden. `analytical_operation` se conserva en propuesta/cobertura
  y exige ambos componentes. No incorpora percentiles, predicción ni puntuación libre.
- **`sales-bi-v7` / `compilation_rules_version=3`:** nuevos contratos excluyen
  aritmética con IDs, construyen promedio documental con razón de agregados y no
  sustituyen líneas por pedidos. Documentos sin marcador reproducen reglas 1 y los marcados 2 conservan reglas 2.
  No se añade retrospectivamente el marcador ni se reescriben huellas/aprobaciones.
- **Aprobación nueva:** un borrador con prompt/reglas anteriores recibe 409 y debe
  regenerarse o personalizarse para crear hija actual con `source_proposal_id`.
  La idempotencia de un aprobado legado devuelve su contrato sin actualizarlo.
- **Editor:** el contrato efectivo determina referencias y selección inicial, no
  las posiciones o fuentes crudas de `ai_decisions`. Razones conservan dos entradas;
  retirar denominador retira su KPI. Salidas añadidas sin decisión editable son consulta.
- **Copiloto:** proveedor devuelve `answer`/`evidence`; la API mantiene
  `suggested_questions` y `caveat`, construidos en plataforma. La procedencia deriva
  de contrato/instantánea, fuentes, columnas, claves y la misma ruta FK del materializador.
  Nombres derivados conservan linaje/operación sin transmitir sus valores. `same_source`
  distingue origen directo sin FK. Las fechas ETL son una ventana, no un instante de
  lectura ni la fecha de última modificación del origen.
- **Períodos:** KPI `daily/weekly/monthly/quarterly/yearly`; catálogo/propuesta
  `day/week/month/quarter/year`. `inherit` normaliza ambos. El lector usa un
  argumento interno permitido de `date_trunc`, sin SQL libre ni otro ETL.

## Evidencia anterior y compatibilidad

Los identificadores pertenecen a la instalación de ensayo y cada artefacto conserva
sus reglas. No se presentan los recorridos previos como pruebas retrospectivas de revisión 6/reglas 3.

- **WWI 115:** bloqueo correcto de producto líder basado en máximo de una línea.
  No se aprobó. La continuación 116 y la hija 117 produjeron ejecución 16: cinco tablas,
  228.265 filas por lado, diferencia cero, 8.950.628 unidades, 70.510 facturas e importe
  de origen 198.043.439,45. No se acreditó moneda única.
- **AW 118:** intento detallado bloqueado por falsa factura. Se conserva ese incidente;
  no se presenta la clasificación equivocada como control semántico correcto.
- **AW básico 119/120 -> 17:** ejercicio distinto de dos KPI, fecha/producto/territorio
  y sin cliente; 22 operaciones, cuatro tablas, 121.317 filas por lado, diferencia cero,
  109.846.381,40 USD y 274.914 unidades. No sustituye el objetivo detallado.
- **Compatibilidad 91/98/117/120:** contraste de sólo lectura antes/después conservó
  documento, validación, replay y `approval_safe` idénticos, cero errores y avisos
  5/3/6/9 respectivamente. No se actualizaron filas.
- **Clientes WWI 16:** 663 claves/etiquetas coinciden con `CustomerName` del origen tras
  la limpieza existente, sin ausentes ni diferencias. Una diferencia literal era
  espacio externo. No se cambió por nombres imaginados ni se unió a `People`.
  El aspecto de un nombre no acredita categoría jurídica. La etiqueta técnica
  `invoice_line_fact` observada en `dim_cliente` queda como revisión futura separada;
  no demuestra corrupción de esos valores ni se arregló alterando el contrato aprobado.

## Repeticiones operativas con objetivos intactos

### AdventureWorks: 532 caracteres, v4/v7, 122/18

El mismo objetivo detallado produjo 121 y la hija 122 aprobada con cuatro KPI, tres
medidas, cuatro dimensiones y claves de detalle/pedido: cero errores, nueve avisos,
seis referencias y huella `28ac4d6997d8` igual a reconstrucción. Cobertura descriptiva:
504 productos, 19.820 clientes y 10 territorios al 100 %. Este ensayo fue revisión 4/reglas 2, anterior
a las precisiones de exclusiones v5 y bordes v6/reglas 3; no se reescribe su evaluación.

La ejecución 18 completó 26 operaciones y cinco tablas; 121.317 filas por lado,
diferencia cero, importe 109.846.381,399888 USD, 274.914 unidades, 31.465 pedidos y razón
3.491,065672966407. Se publicaron tres equivalencias de grupos y se excluyeron seis
códigos conservando originales. El panel mensual mostró 38 períodos. En 2013/Northwest:
6.015.174,735836 USD, 17.452 unidades, 2.053 pedidos y razón 2.929,943855740867.

El Top 3 observado fue 392.175,27 / 338.770,42 / 334.598,66, 17,71 % conjunto sobre
el denominador territorial anterior al Top 3, con cautelas causales correctas.
La sugerencia inicial de margen ausente motivó la restricción de catálogo; la repetición final AW (121) mostró el mismo Top 3/denominador, sin preferencias ni causalidad y tres sugerencias válidas. Los finales de contexto 18 se comprobaron por archivo propio.

La **primera exportación 18** se verificó: cinco páginas y cuatro hojas, suma temporal
6.015.174,7358359999 frente a 6.015.174,735836, diferencia 10^-10 dentro de tolerancia,
unidades/pedidos/razón correctos y sin recortes. No imprimía fuente/base/zona. Sus
originales y hashes se preservan como corte anterior al contexto añadido después.

### WideWorldImporters: 693 caracteres, v5/v7, 124/19

La repetición v5 conservó 693 caracteres, cuatro preguntas y Mensual: 16 directos,
siete automáticos y siete límites legítimos, sin falso margen/ACK (106). La propuesta
123 se personalizó como 124 con cuatro KPI, siete referencias, cero errores, siete
avisos y huella `b5872c3bbd6d` reproducida igual. La hija quedó seleccionada
automáticamente; el editor mostró conteo efectivo de `InvoiceID`, no la referencia
cruda `ExtendedPrice`.

La ejecución 19 completó 26 operaciones y cinco tablas, 228.265 filas por lado y
diferencia cero; importe de origen 198.043.439,45, 8.950.628 unidades, 70.510 facturas
y razón mostrada 2.808,73. Fecha consolidó 1.069 valores desde 70.510 entradas con
69.441 duplicados controlados; Producto 227, Cliente 663 y Territorio 53 al 100 %
descriptivo. No requirió mapeos adicionales y quedó Validada. Comprobar divisa no
repitió ETL y conservó moneda de origen porque no demostró moneda única.

En 2015/California se comprobaron 1.215.705,55 de origen, 57.142 unidades, 481 facturas
y razón 2.527,454365904366. La primera respuesta 19 acertó cifras/sugerencias pero
atribuyó ubicación a fecha de transacción sin prueba histórica. Se conserva como
incidente. La captura 116 sólo muestra pregunta y comienzo: no se atribuye a la
imagen una frase que queda fuera del encuadre.

Después del refuerzo, se repitió la misma pregunta con conversación limpia:
54.648 / 50.715 / 45.860,85; 4,50 / 4,17 / 3,77 % sobre 1.215.705,55. La respuesta
distingue ficha extraída durante ETL, historia no demostrada y entrega no probada.
La cautela de plataforma y tres sugerencias sólo del catálogo se observaron correctas.
117 muestra el primer aviso en vista ejecutiva, 118 la respuesta completa y 119 la
cautela, sugerencias y ejecución. Un clic real en la sugerencia de unidades por cliente devolvió cinco clientes y denominador 57.142 (120). La revisión visual de esos originales la realizó
la agente principal; no acredita todos los proveedores o futuras preguntas.

La **exportación 19 inicial** se revisó con 22 controles conformes, cinco páginas PDF
y cuatro hojas XLSX, sin editar originales. Fuente `WideWorldImporters local`,
base `WideWorldImporters`, 19/124, filtros, moneda de origen y fecha
`2026-11-05 04:56+00:00` están impresos. Importes, unidades, documentos, razón y
sumas concilian. Las hojas no contienen fórmulas de celda ni hipervínculos automáticos.
Los porcentajes de productos usan suma de las ocho categorías mostradas
(307.083,35), no el total territorial; el reporte aclara «total mostrado».
SHA-256 PDF `3b39c79e3ef63c052ea1fe6ec777e182e6ac651f71b2f32e320f39f5eed876bf`;
XLSX `85470fb9866a3e686660e327b1700fd40b96395544bfd51291edc0bd3714baab`.
La descarga intermedia 19-contexto conservó texto pero recortó el aviso en 34 pt. Los finales 18/19 se revisaron por separado: diez páginas PDF y cuatro hojas por XLSX, fuente/base/offset, cifras y aviso completo con altura de 57 pt. Se conservan hashes propios y los originales anteriores. Calc final no se completó por memoria; ArtifactTool sí, sin adjudicar la prueba sintética a esos archivos.

La captura 110 muestra sólo la parte superior de evidencia. La nueva 124 muestra ambas huellas b5872c3bbd6d coincidentes; no se atribuye ese contenido al recorte anterior.
Las capturas no sustituyen datos de expediente o una comprobación ausente.

## Matriz temporal real de sólo lectura

22 consultas: dos con configuración mensual persistida sin alterarla, diez con
códigos KPI y diez con `inherit` y códigos de catálogo. Escenarios alternativos usan
copias en memoria bajo transacción de sólo lectura. No son 22 propuestas ni 22 ETL.

| Datamart | Días | Semanas ISO | Meses | Trimestres | Años |
|---|---:|---:|---:|---:|---:|
| WWI 16 | 1.069 | 179 | 41 | 14 | 4 |
| AW 17 | 1.124 | 162 | 38 | 13 | 4 |

Los 22 casos cumplen: sumas temporales frente a KPI con diferencia cero salvo residuo
AW trimestral de aproximadamente 1,49 × 10^-8, menor que tolerancia 10^-6. Se verificaron
etiquetas/subtítulos sin reescribir nombres históricos ni contratos mensuales.
El original sanitizado `qa/matriz_temporal_solo_lectura.json` se custodia con el manual.

## Regresión final y límites de verificación

| Alcance | Evidencia | Resultado |
|---|---|---|
| Integral V4 | `make verify`; registro del 5 de noviembre | Código 0; backend 454/454, frontend 46/46; un aviso sin fallo; Compose, rama, workflow, lint/build/docs aprobados. |
| Integral V6, ajuste UI adicional | `make verify`; mismo árbol publicado como `8f1c7d1` | Salida 0; backend 454/454, frontend 48/48; controles de rama, Compose, workflow, calidad, construcción y doce documentos aprobados. V5 se conserva interrumpido con 143. |
| Calidad global | Ruff/formato/Mypy | 91 archivos con formato correcto; 57 archivos Mypy sin incidencias. `git diff --check` limpio. |
| Necesidad | `test_need_advisor.py` + `test_copilot_needs.py` | 156 focales de necesidad/advisor; intención, FK, ranking y negaciones acotadas. |
| Compilación/aprobación | `test_copilot_service.py` + `test_proposal_approval.py` | 110 focales combinadas; IDs, razón, población, cobertura, hija actual y aprobado legado idempotente. |
| Analítica/copiloto | `test_analytics_service.py` + `test_analytics_copilot.py` | 53 focales definitivas, incluidas procedencia/advertencia y catálogos; 22 consultas temporales reales separadas. |
| Exportación | `test_analytics_export.py` | 52 focales; precisión, contexto, zona y texto literal. Cada archivo recibe QA propia. |
| Frontend | Suite Vitest, imagen fresca y runtime | 46/46; correo, protegidos, catálogos, hija, editor efectivo y preset; ESLint/TypeScript/Vite aprobados. |
| Consulta UI | Operación autorizada de la agente principal | AW 122/18 y WWI 124/19 conciliados; mismo chat 19 repetido con contexto correcto. No es prueba de sesiones de todos los roles. |

Los conteos focalizados son subconjuntos de la suite: no se suman al 454.
La primera verificación integral aprobó 407 backend de su corte y falló 43/44 frontend
por el nombre perdido al seleccionar preset. Se corrigió la causa y se comprobó
nombre, envío y limpieza sólo tras éxito, sin aumentar timeouts ni llamar a un LLM.
407 no se adjudica al corte V4; los cierres V2 (408/44) y V3 (411/44) fueron anteriores; V4 cerró 454/46 antes del ajuste adicional de presentación.

La consulta administrativa 105 mostró correo de sólo lectura y rol protegido
deshabilitado sin guardar modificaciones. El cambio AW 18 -> WWI 16 restableció
filtros a Todos, moneda de origen y conversación limpia. Los errores de catálogos
bloquean guardado hasta reintento válido; permanece el tope de 100 elementos en esos
selectores. No se crearon cuentas ni se cambiaron credenciales para estas comprobaciones.


## Bordes finales y compatibilidad de evidencia

Need-review-6 normaliza tildes/puntuación y exclusiones del ranking y conserva
«no excluir/do not exclude» como intención positiva. invoice_event admite el propio
hecho cabecera con PK completa declarada/referencias exactas o FK completa existente;
ni nombre ni PK parcial bastan. Reglas 3 restringe Number/Numero como identificador
nominal a semántica documental/entidad y respeta PK/FK; NumberOfUnits/NumeroDeUnidades
sin claves queda disponible como cantidad SUM. Las 266 focales de los cuatro módulos
son 156 de necesidad y 110 de compilación/aprobación, incluidas en las 454 globales.

La auditoría final SELECT-only de seis aprobadas con reglas almacenadas conserva
documentos y validaciones sin mutación y approval_safe true para todas. 122/124
siguen reglas 2 con replay exacto. Cinco hashes coinciden y 91 mantiene su diferencia
preexistente; proposal.replay.passed refleja ese resultado real y la advertencia de
versiones permanece separada. Los detalles informan prompt/reglas guardados y actuales;
sin decisiones se informa ausencia explícita. El gate de aprobación nueva sigue
exigiendo reglas 3. No existe un campo histórico need-review en esos documentos:
v4/v5 de los ensayos se describe por el corte observado, no como una columna inventada.

La acción explícita de preparar hija desde aprobada/invalidada habilita sólo su
borrador en paso 4. Cancelar restablece consulta y valores originales. Guardar crea
y selecciona hija, sin aprobarla ni alterar padre. La prueba UI de 124 aprobada
habilitó Justificación/Guardar y canceló sin crear otra hija (125).
Nombre/presets LLM se consultaron sin guardar/activar; Claude continuó activo (122),
y correo protegido sólo lectura se confirmó en 123.

Los informes externos comparativo_exportaciones18_19_final.json y
verificacion_exportacion18_final.json / verificacion_exportacion19_final.json
identifican los cuatro archivos finales, sus SHA y métodos. El reporte intermedio
19-contexto recortado permanece como incidencia; no se sobrescribió. La advertencia
final está completa en ambos formatos. No se suman importes entre USD y moneda de
origen ni se afirma revisión Calc de los finales.

## Guion de formación

1. Conservar objetivo, preguntas, período y corte. Un ejercicio más sencillo no sustituye
   la repetición de la necesidad que falló.
2. Explicar dato, significado y validación; revisar grano, claves, agregación y población.
3. Usar plan A de consulta de propuestas/expedientes/reportes comprobados sin LLM ni
   otra carga. Plan B genera sólo con disponibilidad, permiso y consentimiento.
4. Revisar contrato efectivo, exclusiones, fórmula/denominador y evidencia antes de aprobar.
5. Separar cifras, cobertura descriptiva, procedencia temporal y prudencia de lenguaje.
   La generación LLM no es 100 % determinista ni el replay equivale a otra generación.
6. Identificar cada exportación por procedencia/hash y distinguir datos leídos de texto
   efectivamente visible en cada captura.

Los originales de capturas y exportaciones, los informes sanitizados
`verificacion_exportacion18.json`, `verificacion_exportacion19.json` y diagnóstico
de clientes se custodian con la entrega externa del manual. No se incorporan secretos,
volúmenes, bases, registros de compilación ni filas completas de clientes a Git.

## Documentos relacionados

- [SPR-02-01](../specs/SPR-02-01-seguridad-rbac.md): formularios de seguridad.
- [SPR-03-02](../specs/SPR-03-02-propuesta-bi-asistida-por-ia.md): intención y revisión previa.
- [SPR-04-02](../specs/SPR-04-02-kpis-controlados-y-calculables.md): recetas y población.
- [SPR-05-01](../specs/SPR-05-01-dashboard-ejecutivo-explicable.md): periodicidad y procedencia.
- [SPR-05-02](../specs/SPR-05-02-reporteria-fiel-pdf-excel.md): contexto y precisión.
- [SPR-05-05](../specs/SPR-05-05-copiloto-analitico-contextual.md): respuesta, sugerencias y cautela.
- [SPR-06-01](../specs/SPR-06-01-contexto-multifuente-sqlserver.md): contexto multifuente.
- [Manual técnico](../manual-tecnico/manual-tecnico.pdf) e
  [informe Sprint 6](../sprints/sprint-06-multifuente-universal.pdf): adenda de cierre sin otro sprint.

## Integración del corte

El commit de código `bf50172` se publicó en la rama correctiva. El [PR 57](https://github.com/LFXAS/prototipo-bi-ia/pull/57) hacia `develop` se abrió como borrador; este registro no afirma fusión ni promoción a `main`.
El ajuste de presentación posterior corresponde a `8f1c7d1` y al cierre V6; no abre
otro sprint ni modifica las versiones históricas de motor.

## Ajuste adicional de presentación sobre expedientes conservados

La inspección de la UI actual del expediente 18 reprodujo una columna de etiqueta
de unos 50 px frente a un texto de unos 73 px, con superposición sobre el resultado.
Además, la unidad de una razón conservaba «moneda de origen por transacción» pese
a la divisa USD ya verificada. Son defectos de presentación de los datos conservados;
no se repiten comprobación monetaria, materialización, LLM ni consultas comerciales
para corregirlos.

`styles.css` permite contraer ambas columnas de conciliación, envolver etiquetas y
valores y apilarlos hasta 760 px. `App.tsx` resuelve la unidad completa para cualquier
código KPI: sustituye el prefijo `moneda`, `moneda de origen` o `currency` por la
divisa verificada, conservando `por…`, `per…` o `/…`. ISO3 monetario, razones,
cantidades fraccionarias y unidades desconocidas conservan dos decimales; sólo una
unidad completa del conjunto cerrado de conteos usa enteros, con prioridad sobre
el patrón ISO3 (`ROW` sigue siendo conteo). No se infieren esos
alias por nombre/código del KPI. Permanece la compatibilidad de dos códigos del
catálogo cuando un expediente anterior omitió el denominador «por unidad».

Archivos de implementación: `frontend/src/App.tsx`, `frontend/src/App.test.tsx` y
`frontend/src/styles.css`. No cambian backend, API, fórmula, valores, aprobaciones,
metadatos, tablas ni contrato persistido. Las capturas y exportaciones anteriores
permanecen intactas; la inspección nueva de 18/19 tiene su propio corte y no demuestra
una carga nueva ni corrige retrospectivamente el aspecto de los originales.

**Resultado adicional:** V6 terminó con salida 0, 454 backend y 48 frontend. Las
dos regresiones UI parametrizadas cubren divisa verificada y no resuelta, unidades
compuestas, cantidades fraccionarias, conteos y compatibilidad anterior; lint/build
también aprobaron. La consulta real de 18/19 a 574 y 1366 px no mostró solapes:
AW mostró `USD 3.491,07 por transacción`; WWI conservó
`2.808,73 moneda de origen por transacción`. Se preservaron las capturas nuevas
126/127 y `qa/verificacion_unidades_disposicion_etl_20261105.json` en la entrega
externa del manual. No hubo nuevo ETL, LLM ni cambios de datos. Los PDF anteriores
no reciben este resultado; la compilación y revisión documental final se registran
por separado y sin solapar la suite de código.


## Entrega del manual de usuario y formación

La edición final de `docs/manual-usuario/Manual_de_usuario_Plataforma_BI.docx` y su
PDF reúne 464 páginas, 18 capítulos, 76 procedimientos, 140 capturas originales
incluidas y 52 casos documentados con estados y límites propios. Incluye conceptos
de BI, configuración por fuente, catálogo, necesidad, aprobación, ETL, semántica,
panel, copiloto, exportaciones, incidencias y preparación de la sustentación.

Se inspeccionaron individualmente las 464 páginas renderizadas de V2. Tras corregir
espaciados y seis pies históricos se generó V3: 457 PNG resultaron idénticos por
SHA-256 a los ya revisados y las siete páginas distintas se inspeccionaron de nuevo
a tamaño nativo. No se alteraron los originales de la aplicación. Los 880 enlaces
internos tienen destino; no hay páginas vacías ni bloqueantes de composición.
El comprobante de entrega está en
`docs/manual-usuario/qa/verificacion_entrega_manual_20261105.json`.

Las exportaciones finales y las variantes históricas conservan su identidad y
sus comprobaciones. Los recorridos reales se efectuaron con cuenta administrativa:
la matriz de permisos no acredita sesiones autenticadas de todos los roles. El
plan de sustentación distingue consulta conservada de generación nueva con un
proveedor disponible y revisión humana. No se acredita un benchmark concluyente
de proveedores ni funcionamiento garantizado de todo escenario futuro.
