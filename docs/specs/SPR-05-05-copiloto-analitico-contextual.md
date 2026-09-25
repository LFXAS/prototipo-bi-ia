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

La instrucción prohíbe inventar cifras, causas, relaciones, acciones o pronósticos. Una comparación temporal entre extremos visibles no se presenta como causalidad ni como tendencia probada; se advierte que los meses extremos pueden tener cobertura parcial.

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
