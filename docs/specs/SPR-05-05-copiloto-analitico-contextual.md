# SPR-05-05: copiloto analítico contextual y guía de preguntas

- Estado: **implementada y verificada**
- Dependencia: `SPR-05-01`
- Usuarios: dirección, gerencias, usuarios finales autorizados y analista BI

## 1. Problema y objetivo

Un tablero puede mostrar cifras correctas y aun así dejar al usuario sin saber qué preguntar, qué evidencia respalda una lectura o qué conclusión no está permitida. El copiloto analítico ayuda a comprender la selección visible y puede solicitar agregaciones adicionales sobre el datamart publicado, sin convertir al LLM en fuente de cifras ni permitirle escribir o ejecutar SQL.

## 2. Alcance

- conversación contextual separada de los hallazgos determinísticos;
- guía de preguntas adaptada a la vista ejecutiva o analítica;
- ejemplos agrupados por comprender, decidir e interpretar con cautela, o por comparar, investigar y validar;
- historial breve dentro de la sesión de pantalla;
- respuesta, evidencias citadas, advertencia y preguntas de seguimiento;
- reinicio de conversación al cambiar vista, indicador o filtros;
- proveedor y modelo visibles para trazabilidad.
- interpretación controlada de indicador, dimensión, filtro, orden y Top N;
- consulta de agregados adicionales aunque el filtro no esté activo en el tablero;
- denominador y procedencia técnica visibles para toda participación porcentual.

No conserva una memoria personal permanente, no accede a filas del OLTP, no recibe credenciales, no acepta SQL generado por IA, no ejecuta acciones y no formula pronósticos.

## 3. Contrato seguro

`POST /api/v1/analytics/copilot` recibe pregunta, historial acotado, vista, ejecución, indicador y filtros. El servidor vuelve a construir el dashboard conciliado y realiza dos pasos separados:

1. la IA traduce la pregunta a un contrato JSON cerrado con indicador, dimensión, Top N, orden, año y territorio; cada valor está restringido a catálogos suministrados por la aplicación;
2. la aplicación valida el contrato y ejecuta una agregación parametrizada construida exclusivamente por código propio sobre la ejecución conciliada. La IA recibe después el resultado agregado para explicarlo.

No se acepta texto SQL en ninguna parte del contrato. Los identificadores provienen de la propuesta aprobada, las columnas materializadas y las recetas KPI verificadas. El filtro `__dashboard__` conserva la selección visible y `__all__` solicita el universo completo; un territorio explícito sólo puede seleccionarse si existe en el catálogo de la ejecución.

La salida utiliza un esquema JSON estricto con:

- `answer`;
- `evidence`;
- `suggested_questions`;
- `caveat`;
- `provider_kind` y `model_id` añadidos por el servidor.
- `interpreted_query`, cuando fue necesaria una agregación adicional, con alcance, resultados, denominador y procedencia.

La instrucción prohíbe inventar cifras, causas, relaciones, acciones o pronósticos. Una comparación temporal entre extremos visibles no se presenta como causalidad ni como tendencia probada; se advierte que los períodos extremos pueden tener cobertura parcial.

### 3.1. Precisión de interpretación posterior al cierre

En la revisión del 4–5 de noviembre se precisan las instrucciones de explicación sin
añadir campos de API ni consultas libres. Un ranking con sumas correctas no demuestra
preferencias de consumidores, demanda, eficacia de una campaña, penetración o cuota
de mercado. Se puede describir qué producto acumuló más importe dentro del alcance
consultado y presentar una acción como hipótesis a investigar, sin afirmar esa causa.

Una provincia derivada de la ciudad de entrega de la ficha actual del cliente es una
clasificación de esa ficha. No acredita el lugar real de cada entrega ni la ubicación
histórica de la venta. La respuesta debe cubrir las cautelas pedidas y distinguirlas
de la cifra, período y denominador comprobados; acertar el Top N no cubre toda una
pregunta compuesta.

Se conserva el caso que motivó el ajuste y se repite la misma pregunta con conversación
limpia. Las pruebas automatizadas del prompt no sustituyen esa observación real ni
prueban todas las futuras respuestas. Véase
[QA posterior al cierre](../testing/qa-postcierre-2026-11-04.md).

### 3.2. Preguntas sugeridas desde el catálogo de la ejecución

La respuesta API conserva `suggested_questions: list[str]`, pero las preguntas ya
no proceden de texto libre del proveedor. El esquema interno del LLM solicita sólo
`answer` y `evidence`; el servidor construye hasta tres sugerencias desde
`available_metrics`, usando recetas agrupables y dimensiones presentes en los
visuales materializados y admitidas por el agregador. Prioriza la métrica
seleccionada. Si no hay un eje apto, ofrece el valor o la evolución visibles.

La interpretación de intención enumera esas mismas dimensiones disponibles. Una
etiqueta que contenga costo, margen u otra palabra no habilita una receta ausente;
las etiquetas arbitrarias siguen siendo presentación, no permisos de cálculo.
No cambian los campos de API, filtros, alcance, permisos ni SQL permitido. El cierre
de copiloto y servicio analítico aprobó 53 pruebas focalizadas, Ruff, formato y Mypy,
incluidas las regresiones de sugerencias y procedencia. Son parte del cierre integral
454 backend/46 frontend, no conteos adicionales.

### 3.3. Procedencia temporal y cautela de plataforma

`caveat` conserva su tipo público de texto, pero se construye íntegramente en el
servidor. No se acepta, concatena ni trunca una cautela libre del proveedor. El
contexto registra alcance y procedencia estructurada desde contrato, instantánea,
fuentes, columnas, claves y la misma ruta FK que utiliza el materializador; distingue
origen directo mediante `same_source`. Los nombres derivados conservan operación y
linaje sin transmitir sus valores.

Las fechas reales de la ejecución definen una ventana ETL, no el instante exacto de
lectura ni la última actualización de una fila fuente. La ficha extraída no demuestra
vigencia a fecha del hecho ni entrega verificada. Los flags internos conservan ese
significado; el texto público lo explica sin exigir el acrónimo técnico SCD2. La
advertencia ocupa el primer hallazgo y queda dentro de los cuatro visibles en modo
ejecutivo. Incluye los límites de causalidad, preferencias y demanda.

La primera respuesta de WWI 19 acertó cifras pero afirmó historia no acreditada. La
misma pregunta con conversación limpia, tras el refuerzo, mostró Top 3 y porcentajes
correctos sobre 1.215.705,55 y explicó ficha durante ETL, historia y entrega no probadas.
La evidencia 117–119 fue inspeccionada visualmente por la revisión principal. Ello no
acredita todos los proveedores o todas las futuras respuestas.

### 3.4. Reloj de consulta y cobertura histórica

La revisión operativa del 6 de noviembre observó una respuesta que rechazaba el
pronóstico, pero añadía un año ajeno al contexto pertinente. El contexto de intención
y de explicación incorpora ahora `calendar_reference`: fecha ISO actual del servidor,
`timezone=UTC` y significado `request_clock_not_dataset_coverage`. El reloj de la
consulta se distingue del año filtrado, de la cobertura histórica y de la ventana ETL.

Las instrucciones prohíben introducir fechas, años, períodos o categorías ajenos a la
pregunta y a la evidencia. Si una consulta relativa, como «próximo año», pide un
pronóstico no disponible, la explicación utiliza «el período solicitado» sin inventar
un año de ejemplo. Conocer la fecha actual no añade años al catálogo ni acredita datos
futuros o un modelo predictivo.

La regresión `test_dashboard_explanation_keeps_calendar_and_data_coverage_separate`
contrasta un reloj de 2026 con datos disponibles de 2014. Ambos pasos reciben la misma
referencia, conservan el catálogo histórico y no ejecutan una agregación adicional
para un resumen del dashboard. Las 26 pruebas focales del copiloto aprobaron junto
con Ruff y Mypy. Son parte del corte intermedio, no se suman a sus 475 pruebas
backend. El corte intermedio `make verify` del 6 de noviembre, anterior al ajuste de rutas de reglas 5, concluyó con salida 0, 475 backend
y 48 frontend; la etapa frontend se reutilizó de caché del mismo árbol de fuentes.

No se modifican SQL, filtros, filas, proveedor ni cuotas y no se reescriben números de
la respuesta mediante expresiones regulares. Es una reducción de un riesgo narrativo
observado. La prosa de IA sigue bajo supervisión: una estructura JSON válida y una
instrucción más precisa no constituyen un validador universal de veracidad ni garantizan
que todas las respuestas futuras sean correctas. Las reglas 5 verifican además que la procedencia descrita utiliza la misma ruta FK persistida que el materializador; ante evidencia inválida no se reconstruye otra ruta por búsqueda. El integral de esa corrección y la repetición operativa posterior se
registran por separado en [QA del 6 de noviembre](../testing/qa-postcierre-2026-11-06.md).

La explicación utiliza nombres de negocio y su significado, evitando mostrar claves JSON, estados internos o códigos KPI como si fueran lenguaje para la persona usuaria. Esta precisión de instrucciones no sustituye la revisión humana de la respuesta.

El caso nuevo WWI 131/22 respondió sobre 2015/California con 3.191.769,11 de importe, 142.247 unidades y 1.179 facturas, y distinguió ubicación histórica, entrega no comprobada y moneda no identificada. La concordancia de cifras y cautelas no equivale a precisión perfecta de toda la redacción: se conservan sus límites narrativos y la supervisión humana.

## 4. Experiencia de usuario

El copiloto se presenta como un espacio ancho y separado del panel de hallazgos. A la izquierda se encuentra la guía de preguntas; a la derecha, el estado vacío, la conversación y el campo de entrada. Esto evita comprimir el texto en una barra lateral y permite leer respuestas, evidencia y límites en orden.

Las preguntas sugeridas son botones, pero el usuario puede redactar otra. El formulario explica que una buena pregunta menciona el indicador, la comparación esperada y la decisión que desea apoyar. La respuesta presenta una tarjeta «Consulta interpretada» para que una persona no técnica pueda comprobar qué entendió el sistema antes de usar la explicación.

## 5. Seguridad y auditoría

Requiere `analytics.dashboard.read`. Cada consulta registra usuario, ejecución, vista, indicador, filtros, proveedor, modelo, número de turnos y una huella de la pregunta; no persiste el texto de la pregunta ni la respuesta completa en auditoría.

## 6. Criterios de aceptación

- [x] El usuario final dispone de ejemplos comprensibles para formular preguntas.
- [x] El analista recibe preguntas orientadas a comparación, investigación y validación.
- [x] La IA usa sólo agregados de una ejecución conciliada y un catálogo cerrado de filtros reales.
- [x] «¿Cuáles son los 5 productos más vendidos en Europa?» se interpreta como unidades, producto, Top 5 y filtro Europa aunque el filtro visual no esté activo.
- [x] El motor calcula la participación contra el total filtrado antes del Top N y explicita ese denominador.
- [x] La respuesta muestra medida, operación y columnas materializadas de procedencia sin exponer SQL.
- [x] La respuesta contiene evidencia, advertencia y seguimientos accionables.
- [x] Cambiar filtros o vista elimina el contexto anterior para evitar mezclar selecciones.
- [x] La interfaz identifica proveedor y modelo y presenta estados de carga y error.
- [x] El servicio rechaza configuraciones no activas o no probadas y errores del proveedor de forma segura.
- [x] La consulta real con Groq `openai/gpt-oss-120b` respondió en español y citó evidencia del expediente 7.

## 7. Evidencia

Pruebas automatizadas del esquema cerrado de interpretación y del motor de agregaciones con filtro Europa no visible, Top 5 y denominador completo. Se conserva también la prueba funcional desde la vista ejecutiva con Groq, la auditoría sin texto en claro, la compilación frontend y la revisión visual de la conversación.
