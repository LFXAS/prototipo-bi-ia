# SPR-05-06: endurecimiento integral del asistente BI autosuficiente y supervisable

- Estado: **en implementación controlada**
- Tipo: corrección transversal con alcance funcional en los Sprints 3, 4 y 5
- Usuarios: analista BI, administrador de plataforma y usuario final autorizado
- Rama de implementación: `feature/bi-assistant-hardening`
- Punto de recuperación: `checkpoint-bi-pre-codex-2026-09-25`

## 1. Problema y objetivo

El asistente debe resolver automáticamente toda decisión que pueda demostrar con
metadatos, relaciones declaradas y reglas determinísticas. La IA interpreta,
propone y explica; no inventa objetos ni sustituye las comprobaciones. Sólo se
solicita una decisión humana cuando exista una ambigüedad real o una definición de
negocio que no pueda deducirse. En ese caso, la plataforma presenta alternativas
ejecutables, evidencia, riesgo y consecuencia sin obligar al analista a usar SQL ni
una herramienta externa.

Esta especificación convierte ese principio en contratos comprobables y evita que
un requisito desaparezca silenciosamente entre necesidad, propuesta, ETL y
analítica.

## 2. Requisitos normativos

### HBI-001 — Compatibilidad y diagnóstico del proveedor LLM

- La plataforma traduce los niveles de razonamiento a las capacidades reales del
  proveedor y modelo sin afectar proveedores existentes.
- Cada fallo conserva categoría sanitizada, código HTTP e identificador de
  solicitud cuando el proveedor lo entrega.
- Groq puede expresar un límite temporal de tokens con HTTP 413 y código
  `rate_limit_exceeded`; ese caso se clasifica y reintenta como límite temporal,
  sin confundirlo con un contrato demasiado grande.
- El contexto enviado para proponer el modelo usa una proyección compacta: conserva
  objetivo, preguntas, requisitos, referencias, columnas y relaciones necesarias,
  pero excluye explicaciones y evidencias duplicadas que el motor ya validó.
- Sólo se reintentan fallos transitorios. Credenciales, parámetros inválidos y
  respuestas estructuradas no reparables requieren acción explícita.
- Un fallo del LLM no convierte una necesidad viable en una necesidad inviable.

### HBI-002 — Formulación y viabilidad de la necesidad

- La necesidad admite hasta 2000 caracteres, muestra contador y puede ser
  reformulada por la IA únicamente como borrador sujeto a aprobación.
- El área de redacción presenta al menos doce líneas visibles, conserva el texto
  completo y permite ampliarse verticalmente sin superponer el contador ni la
  ayuda contextual.
- Antes de generar conceptos se clasifica cada requisito como **directo**,
  **derivable**, **ambiguo** o **no disponible** usando la instantánea vigente.
- Toda limitación debe aceptarse individualmente. Cambiar necesidad, preguntas,
  periodicidad o metadatos invalida la comprobación previa.

### HBI-003 — Cobertura de extremo a extremo

- Cada requisito de la necesidad se vincula con concepto, dimensión, medida, KPI o
  decisión pendiente.
- Una salida debe indicar `covered`, `human_decision`, `accepted_limitation` o
  `not_covered`; no existen omisiones implícitas.
- Un requisito viable marcado `not_covered` bloquea la aprobación.

### HBI-004 — Fuentes, fórmulas y granularidad

- Toda medida directa muestra `esquema.tabla.columna`, agregación y tipo funcional.
- Todo cálculo muestra fórmula legible y componentes físicos comprobados.
- Transacciones equivale a conteo distinto del identificador de pedido, nunca de la
  línea de detalle.
- La tabla de hechos conserva una fila por identificador de detalle aprobado y la
  validación detecta cualquier multiplicación de filas.

### HBI-005 — Corrección controlada de relaciones

- El analista elige únicamente tablas, columnas y relaciones existentes en la
  instantánea.
- La plataforma comprueba compatibilidad de tipos, PK/FK, unicidad del destino,
  cardinalidad, nulabilidad, ruta y riesgo de duplicación.
- Una ruta insegura se muestra con la razón y queda inhabilitada.
- Una corrección genera una nueva versión y vuelve a ejecutar todas las reglas; no
  modifica propuestas ni ejecuciones históricas.
- El flujo normal no requiere SQL libre.

### HBI-006 — Costos, rentabilidad y descuento monetario

- `CostoTotal`, `MargenBruto`, `Margen%`, `VentaPorUnidad` y `CostoPorUnidad` sólo se
  publican cuando sus componentes físicos están verificados.
- `DescuentoMonetario` se calcula por línea como precio unitario por tasa de
  descuento por cantidad; una tasa no se suma como si fuera moneda.
- Si la IA entrega una receta incompleta pero las tres fuentes son inequívocas,
  el motor la corrige antes de validar y registra el ajuste automático. Para el
  costo unitario se prioriza la fuente de la dimensión de producto conectada al
  hecho; coincidencias homónimas en otras tablas no deben impedir una resolución
  demostrable ni autorizar una elección arbitraria.
- Las medidas derivadas conservan fórmula, moneda, denominador y conciliación.
- La revisión previa al ETL representa cada receta fielmente: una diferencia se
  explica como minuendo menos sustraendo y no como razón. Si una etiqueta promete
  ventas netas pero la receta demostrada sólo calcula precio por cantidad, el
  compilador la presenta como venta bruta y registra el ajuste semántico.
- El enriquecimiento determinístico no agrega un KPI si ya existe otro agregado
  sobre la misma medida y función semántica, aunque sus códigos visibles sean
  distintos. La deduplicación ocurre antes de preparar el ETL.

### HBI-007 — Copiloto analítico seguro y no limitado al lienzo

- Una pregunta se interpreta como dimensión, métrica, filtros, orden y Top N sobre
  un catálogo permitido.
- El motor puede resolver, por ejemplo, “cinco productos más vendidos en Europa”
  aunque Europa no esté seleccionado en el tablero.
- El servidor ejecuta agregaciones parametrizadas; la IA no escribe ni ejecuta SQL
  libre y no recibe credenciales ni filas sensibles.
- La respuesta declara filtros, universo, denominador de porcentajes, ejecución y
  procedencia.

### HBI-008 — Recuperación de sesión y accesibilidad

- El texto del usuario mantiene contraste AA en todos los estados.
- Un vencimiento de sesión conserva localmente el borrador, paso, selección y
  versión; tras autenticarse se restaura sin repetir una mutación incierta.
- Los mensajes distinguen sesión vencida, red, proveedor, validación y permisos e
  indican una acción concreta.
- Una excepción inesperada de renderizado no puede dejar la aplicación en blanco:
  el marco principal muestra una recuperación legible, conserva el expediente en
  el servidor y permite recargar la interfaz sin repetir el ETL.
- Al abrir un expediente desde el historial, la vista regresa al inicio del
  comprobante para evitar que una posición de desplazamiento antigua simule una
  pantalla vacía.
- Un expediente ya validado debe poder reconstruirse aunque combine indicadores
  monetarios, porcentajes y razones por unidad con una interpretación española
  previamente publicada. La vista debe mostrar el comprobante, la conciliación y
  la decisión semántica sin volver a ejecutar el ETL.

### HBI-009 — Regresión automatizada y trazabilidad

- Cada requisito anterior posee al menos una prueba automatizada positiva y una
  negativa donde aplique.
- Cada commit temático pasa formato, lint, tipos, pruebas del módulo y compilación
  de la interfaz; antes del PR se ejecuta la verificación integral.
- No se versionan secretos, credenciales, `.env` ni reportes locales.

### HBI-010 — Compatibilidad del catálogo y acceso a expedientes

- Todo cambio que altere la expansión determinística del contrato incrementa la
  versión del motor; una propuesta creada por una versión anterior conserva su
  aprobación si la instantánea, las referencias y la validación vigente siguen
  siendo seguras.
- La reproducción de una propuesta vigente repite la cadena determinística
  completa —expansión, enriquecimiento financiero, evaluación de necesidad y
  cobertura—, no sólo el primer paso de expansión.
- Una diferencia de reproducción entre versiones se informa como advertencia de
  compatibilidad, no como error estructural genérico ni como retiro automático de
  una aprobación válida.
- La pantalla del datamart siempre conserva visibles los expedientes ETL ya
  preparados o ejecutados, incluso cuando ninguna propuesta esté habilitada para
  una materialización nueva.
- Abrir un expediente histórico es una operación de consulta: no habilita repetir
  el ETL ni modificar el contrato que lo originó.

### HBI-011 — Neutralidad semántica, cobertura ejecutable y versiones analíticas

- Las etiquetas propuestas por el LLM se desacoplan de los identificadores
  canónicos usados por ETL, analítica, reportes y copiloto.
- Una razón, diferencia o participación resuelve dependencias por identificadores
  compilados, no por coincidencia literal del texto del proveedor.
- La selección ETL registra cobertura ejecutable posterior a la selección. Si el
  analista retira salidas solicitadas, la ejecución queda identificada como parcial
  y nunca se recomienda como equivalente completo.
- La materialización conserva los datos por ejecución en un esquema versionado; no
  destruye una versión conciliada al publicar otra.
- Analítica enumera sólo ejecuciones conciliadas con tablas comprobables, permite
  elegir la activa y propaga `execution_id` a dashboard, chat y reportes.
- Los KPI no calculables se presentan como incidencia, no como resultado correcto.
- El motor analítico resuelve primero todas las medidas físicas requeridas y después
  las dependencias derivadas hasta un punto fijo. No depende del orden de salida del
  LLM ni exige que cada operando tenga un KPI agregado redundante.

### HBI-013 — Consulta histórica legible y continuidad del asistente

- Abrir una propuesta aprobada conserva exactamente su necesidad, preguntas y
  periodicidad; la vista de sólo lectura nunca reemplaza esos datos por valores del
  borrador vigente ni por valores predeterminados.
- El modo consulta ofrece una acción visible **Crear nueva propuesta**. La acción
  inicia un borrador limpio en el mismo dominio, conserva la versión histórica y no
  exige cerrar la sesión ni cambiar de usuario.
- En Personalización, cada medida y KPI separa visualmente el nombre de negocio del
  identificador técnico. Ningún texto se forma por concatenación sin separadores.
- Cada medida muestra su tabla/columna de origen y su regla ejecutable. Los conteos
  distintos identifican explícitamente la clave contada, por ejemplo
  `COUNT(DISTINCT SalesOrderID)`; los cálculos muestran la expresión por fila y su
  agregación.
- Selectores, botones y etiquetas admiten salto de línea y conservan el texto
  completo en resoluciones de escritorio y móviles.

### HBI-014 — Derivación automática y recuperación neutral del contrato LLM

- La viabilidad se calcula con la instantánea y reglas determinísticas, antes de
  invocar al proveedor. Claude, Groq, Gemini, Qwen u Ollama reciben el mismo
  significado de negocio; ninguno decide si una fuente existe.
- **Directo** significa que la salida se obtiene de una referencia física ya
  comprobada. **Derivable automáticamente** significa que la plataforma dispone de
  una ruta de relaciones declaradas o de una fórmula tipada y no requiere que el
  analista escriba SQL, seleccione tablas ni complete el cálculo a mano.
- Al generar, la evaluación completa acompaña a la propuesta. El motor aplica las
  derivaciones determinísticas inequívocas y construye la matriz
  necesidad--salida. Si un requisito directo o derivable no termina materializado,
  la propuesta queda bloqueada y no puede aprobarse como válida.
- Sólo los estados ambiguo o no disponible requieren una decisión humana. La
  interfaz explica antes de invocar a la IA qué resolverá automáticamente, qué se
  volverá a comprobar y qué ocurriría si una derivación falla.
- El contrato JSON se valida localmente para todos los proveedores. Un adaptador
  puede cambiar exclusivamente el mecanismo de transporte: si Groq agota los
  reintentos de esquema estricto por una generación no determinística, realiza un
  único intento degradado a objeto JSON con el mismo esquema en la instrucción. La
  respuesta sólo continúa si supera el mismo validador local; en otro caso se
  descarta sin crear una propuesta utilizable.
- Antes de repetir una generación, el validador común puede proyectar de forma
  determinística la respuesta sobre el esquema: elimina únicamente propiedades
  no admitidas y limita textos o listas al máximo declarado. Nunca crea campos
  faltantes, convierte tipos, completa referencias ni corrige fórmulas. Si la proyección sigue
  siendo inválida, se permite un solo reintento del mismo proveedor, modelo,
  necesidad, metadatos y presupuesto con el error estructural como guía. La nueva
  respuesta vuelve a pasar por el contrato completo.
- La recuperación es acotada y auditable. No cambia la necesidad, no reduce el
  alcance, no inventa referencias y no alterna de proveedor automáticamente.
- Si el proveedor propone una dimensión de partes/personas incompatible con el rol
  solicitado, el alcance no confía en el nombre elegido por el modelo. La plataforma
  puntúa rutas reales desde el hecho mediante claves foráneas, columnas de enlace,
  atributos descriptivos y roles excluyentes (por ejemplo empleado, vendedor o
  proveedor). La tabla puede llamarse cliente, persona, entidad, organización o de
  cualquier otra forma; sólo se acepta la ruta que conserva el significado y permite
  resolver una etiqueta descriptiva verificable.

## 3. Experiencia guiada para el analista

1. **Describir**: redacta o aprueba una necesidad reformulada.
2. **Comprobar viabilidad**: revisa qué existe, qué se deriva y qué requiere una
   definición humana.
3. **Revisar contrato**: ve cobertura, fuentes, fórmulas y grano antes de aprobar.
4. **Resolver ambigüedades**: elige entre opciones reales; la plataforma explica y
   bloquea las inseguras.
5. **Versionar y revalidar**: toda corrección crea una versión nueva con resultado
   de las reglas.
6. **Materializar y conciliar**: se ejecutan sólo recetas aprobadas y reproducibles.
7. **Consultar**: el usuario pregunta en lenguaje natural; el sistema responde con
   agregados permitidos y evidencia.

Los detalles técnicos se presentan de forma progresiva. El estado principal debe
responder: qué encontró el sistema, qué resolvió automáticamente, qué requiere una
decisión y cuál es el efecto de cada alternativa.

## 4. Seguridad y límites

- Sólo lectura sobre el origen durante análisis y diagnóstico.
- Catálogos cerrados y parámetros tipados para revisiones y consultas.
- No se envían filas, credenciales ni secretos al proveedor LLM.
- No se acepta una referencia que no pertenezca a la instantánea vigente.
- Las mutaciones requieren permisos, comentario, usuario y auditoría.
- Las muestras autorizadas se limitan, enmascaran cuando corresponda y no se
  incluyen en trazas del proveedor.

## 5. Criterios de aceptación y evidencia

| ID | Criterio observable | Evidencia automatizada mínima | Estado |
|---|---|---|---|
| HBI-001 | Groq low/medium/high produce payload compatible o error accionable con request-id | `test_parameters_providers.py` | implementado |
| HBI-002 | Reformulación requiere aprobación y la viabilidad se invalida al cambiar la entrada | pruebas de `needs` y flujo frontend | implementado |
| HBI-003 | Costos solicitados y omitidos bloquean la propuesta | cobertura en `test_copilot_service.py` | en implementación |
| HBI-004 | Medidas muestran fuentes/fórmulas y se rechaza conteo por detalle | validación de contrato y UI | en implementación |
| HBI-005 | Sólo una FK compatible, única y sin duplicación puede crear una versión | catálogo/revisión backend y UI | en implementación |
| HBI-006 | Costos, margen y descuento concilian contra fuentes verificadas | pruebas ETL y analítica | implementado |
| HBI-007 | Top 5 de Europa se resuelve sin filtro visual ni SQL libre | `test_analytics_copilot.py` y `test_analytics_service.py` | implementado |
| HBI-008 | Una sesión vencida restaura el paso y borrador con contraste accesible | `App.test.tsx` (sesión y borrador) y comprobación WCAG | implementado |
| HBI-009 | `make verify` completo y diff sin secretos | registro de cierre | validado |
| HBI-010 | Las propuestas v3 válidas siguen disponibles bajo motor v4 y los expedientes no desaparecen si el catálogo queda bloqueado | pruebas de evidencia, catálogo y flujo frontend | en implementación |
| HBI-011 | Anthropic y Groq compilan dependencias equivalentes; dos ejecuciones se conservan y el dashboard no presenta falsos positivos | pruebas ETL, analítica y `AnalyticsPage.test.tsx` | implementado; validación física dual pendiente |
| HBI-012 | Los KPI derivados de una ejecución conciliada se recalculan con filtros aunque una medida base no tenga tarjeta agregada propia | `test_analytics_service.py` y validación de la ejecución 11 | implementado |
| HBI-013 | Una versión mensual abre como mensual, permite iniciar otra propuesta y muestra identificadores, etiquetas, fuentes y fórmulas sin concatenación ni recortes | `App.test.tsx` y compilación frontend | implementado |
| HBI-014 | Directos y derivables explican su tratamiento; un derivable omitido bloquea; Groq puede recuperar una salida válida sin alterar el contrato | `App.test.tsx`, `test_parameters_providers.py` y validación de propuesta | implementado |

## 6. Matriz de trazabilidad técnica

| Requisito | Contrato/módulo principal | Superficie de usuario |
|---|---|---|
| HBI-001 | `parameters/providers.py` | Configuración LLM |
| HBI-002 | `copilot/needs.py`, `copilot/router.py` | Paso Necesidad |
| HBI-003/HBI-004 | `copilot/service.py` | Paso Propuesta |
| HBI-005 | catálogo y revisión de relaciones | Personalización |
| HBI-006 | compilador/materializador/analítica | Propuesta, ETL y dashboard |
| HBI-007 | motor analítico permitido | Copiloto analítico |
| HBI-008 | cliente de sesión y persistencia de wizard | Asistente completo |
| HBI-009 | suites backend, frontend y E2E | Evidencia de entrega |
| HBI-010 | versionado de contrato, catálogo ETL e historial | Datamart de ventas |
| HBI-011 | compilador KPI, materializador versionado y catálogo analítico | Preparación ETL y Analítica de ventas |
| HBI-013 | estado del asistente, historial y tarjetas de personalización | Asistente de datamart |
| HBI-014 | evaluación de necesidad, adaptadores LLM y validador local del contrato | Necesidad, Propuesta y recuperación del proveedor |

## 7. Fuera de alcance

- predicción o pronóstico de ventas;
- consola SQL libre como mecanismo ordinario;
- edición directa de datos de origen;
- aprobación automática de una definición puramente comercial;
- inferir relaciones no presentes ni demostrables en los metadatos.

## 8. Control de cambios

- 25/09/2026: especificación formal creada antes de continuar las fases 3 a 6. Se
  incorporan los resultados ya verificados de Groq y viabilidad como requisitos
  implementados, sin declarar completas las fases aún no probadas.
- 25/09/2026: HBI-006 implementado. Las recetas financieras usan referencias
  físicas y rutas FK verificadas; el materializador compila fuentes relacionadas,
  calcula costos, margen y descuento monetario, concilia medidas y publica
  diferencias y ratios con denominador explícito.
- 25/09/2026: HBI-007 implementado. La IA traduce preguntas a un contrato
  cerrado; la aplicación ejecuta agregaciones parametrizadas, calcula el
  denominador antes del Top N y expone procedencia auditable.
- 25/09/2026: HBI-008 implementado. Una respuesta 401 activa recuperación
  global, conserva sólo el borrador no secreto y el identificador de versión,
  restaura el módulo mediante lectura autorizada y distingue 401, 403 y 503.
  Los textos del usuario alcanzan relaciones de contraste 5,08:1 y 5,42:1.
- 25/09/2026: HBI-010 especificado después de reproducir que propuestas v3
  estructuralmente válidas quedaban bloqueadas al aplicarles reglas de expansión
  posteriores sin incrementar la versión del motor. Se exige compatibilidad
  explícita y acceso permanente a los expedientes históricos.
- 25/09/2026: se amplía HBI-001 con evidencia real de Groq: HTTP 413,
  `rate_limit_exceeded`, presupuesto restante y `retry-after`. La política debe
  decidir por el código semántico del proveedor y no únicamente por el estado
  HTTP.
- 25/09/2026: el motor `sales-bi-v5` completa de forma determinística una receta
  de descuento incompleta cuando precio, tasa y cantidad son inequívocos, y
  prioriza el costo unitario perteneciente a la dimensión semántica de producto.
  También se amplía el área de necesidad a doce líneas visibles.
- 25/09/2026: el motor `sales-bi-v6` evita publicar dos KPIs agregados con la
  misma medida y función semántica. Si la IA ya propuso el descuento monetario,
  el enriquecimiento determinístico conserva ese KPI y no crea un duplicado;
  esto mantiene el catálogo dentro del máximo ejecutable de doce indicadores.
- 26/09/2026: HBI-011 se especifica después de reproducir con Anthropic la
  propuesta 77. Se observaron siete advertencias contradictorias con cobertura
  declarada, dos promedios de línea rotulados como valores por unidad, una razón
  calculada por ETL pero perdida en el dashboard por normalización desigual y la
  sustitución física de la ejecución 9 al materializar la 10.
- 26/09/2026: HBI-011 se implementa mediante identificadores canónicos, cierre de
  dependencias, consolidación de recetas equivalentes, cobertura posterior a la
  selección, esquemas por ejecución, catálogo de versiones físicamente disponibles
  y estados honestos para KPI no calculables. La ejecución 10 recuperó USD 401,49
  por unidad sin repetir el ETL; queda pendiente materializar dos ejecuciones nuevas
  para registrar evidencia física dual de integración.
- 27/09/2026: HBI-009 se valida con `make verify`: 133 pruebas Pytest, 21 pruebas
  Vitest, Ruff, formato, Mypy, ESLint, compilación Vite, contratos Compose, flujo de
  ramas y documentación LaTeX finalizaron correctamente. El control final del diff
  no detectó credenciales ni archivos `.env` incorporados.
- 27/09/2026: HBI-012 se especifica al comprobar que la ejecución 11 guardó margen
  bruto, margen porcentual y venta por unidad conciliados, pero el dashboard no los
  recalculó porque `importe_bruto` no tenía un KPI agregado redundante. La solución
  debe ser canónica, independiente del proveedor y reutilizable con filtros.
- 27/09/2026: HBI-012 se implementa resolviendo primero agregados declarados y
  medidas físicas aprobadas, y después diferencias, razones y participaciones hasta
  un punto fijo. La ejecución 11 recuperó margen bruto USD 9899411,54, margen 8,97 %,
  costo promedio USD 365,48 y venta promedio USD 401,49 por unidad; el filtro 2013 +
  Europa recalculó también los cuatro valores sin repetir el ETL.
- 29/09/2026: HBI-013 se especifica al reproducir cuatro fallos de consulta: una
  versión mensual se mostraba como diaria, el modo histórico no tenía salida hacia
  un borrador nuevo, los identificadores se unían a las etiquetas de negocio y el
  origen de `numero_transacciones` no era visible. La corrección debe preservar el
  historial, ser independiente del proveedor LLM y exponer la fórmula realmente
  ejecutable.
- 29/09/2026: HBI-013 se implementa restaurando el estado persistido completo de
  cada versión, incorporando una salida explícita y no destructiva del modo consulta
  y presentando las medidas con etiqueta, identificador, origen y regla ejecutable.
  Vitest cubre la periodicidad mensual, el nuevo borrador y
  `COUNT(DISTINCT SalesOrderID)`; ESLint, TypeScript y Vite completan sin errores.
- 29/09/2026: HBI-014 se especifica e implementa después de observar con Claude que
  la palabra «derivable» no explicaba la acción esperada y de comprobar que la
  evidencia mezclaba columnas homónimas de compras y ventas. La viabilidad ahora
  selecciona un subgrafo coherente, explica la resolución automática y bloquea toda
  omisión. El contrato local común permite una recuperación JSON acotada de Groq sin
  cambiar reglas, alcance ni proveedor.
- 29/09/2026: la propuesta 87 de Claude confirmó un segundo caso: JSON sintácticamente
  válido que no satisfacía el esquema canónico. HBI-014 incorpora proyección segura y
  un único reintento común a todos los proveedores; si aún falta información
  obligatoria, el resultado se descarta como antes.
- 29/09/2026: la propuesta 89 superó la recuperación JSON, pero propuso una entidad de
  vendedores como dimensión cliente. La resolución del alcance se amplía para escoger
  de forma determinística la ruta de parte compradora y sus entidades descriptivas,
  sin depender del proveedor, del nombre físico de la tabla ni de AdventureWorks.
- 29/09/2026: la propuesta 90 resolvió correctamente la identidad del cliente, pero
  atribuyó una clave de una tabla relacionada a la tabla de hechos. HBI-014 exige que
  toda medida directa use una columna física comprobada de su hecho; una medida
  opcional inválida se excluye con diagnóstico y sus KPI dependientes no se publican.
  Si la medida cubre un requisito obligatorio, la cobertura posterior debe bloquear
  la propuesta en vez de inventar procedencia.
