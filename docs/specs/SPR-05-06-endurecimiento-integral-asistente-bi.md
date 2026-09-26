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
- Sólo se reintentan fallos transitorios. Credenciales, parámetros inválidos y
  respuestas estructuradas no reparables requieren acción explícita.
- Un fallo del LLM no convierte una necesidad viable en una necesidad inviable.

### HBI-002 — Formulación y viabilidad de la necesidad

- La necesidad admite hasta 2000 caracteres, muestra contador y puede ser
  reformulada por la IA únicamente como borrador sujeto a aprobación.
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
- Las medidas derivadas conservan fórmula, moneda, denominador y conciliación.

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
- Una diferencia de reproducción entre versiones se informa como advertencia de
  compatibilidad, no como error estructural genérico ni como retiro automático de
  una aprobación válida.
- La pantalla del datamart siempre conserva visibles los expedientes ETL ya
  preparados o ejecutados, incluso cuando ninguna propuesta esté habilitada para
  una materialización nueva.
- Abrir un expediente histórico es una operación de consulta: no habilita repetir
  el ETL ni modificar el contrato que lo originó.

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
| HBI-009 | `make verify` completo y diff sin secretos | registro de cierre | pendiente |
| HBI-010 | Las propuestas v3 válidas siguen disponibles bajo motor v4 y los expedientes no desaparecen si el catálogo queda bloqueado | pruebas de evidencia, catálogo y flujo frontend | en implementación |

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
