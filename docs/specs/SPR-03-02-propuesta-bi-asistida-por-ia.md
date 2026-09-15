# SPR-03-02: propuesta BI asistida por IA y supervisada

- Estado: **borrador para revisión y aprobación**.
- Pertenece a: [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md).
- Fecha de creación: 2026-09-14.
- Rama prevista de implementación: `feature/sprint-03-metadata-copilot`.
- PR de implementación: pendiente.

## 1. Problema y objetivo

Una instantánea técnica no determina por sí sola qué tabla representa el proceso de ventas, cuál debe ser la granularidad del hecho, qué dimensiones son pertinentes ni qué KPIs son calculables. Tampoco es razonable exigir que un gerente seleccione tablas o que un programador prepare SQL para cada análisis. El proyecto necesita demostrar asistencia de IA para transformar una necesidad comercial en una propuesta BI, sin delegarle la ejecución ni aceptar referencias inventadas.

El objetivo es integrar la configuración LLM activa del Sprint 2 para convertir una solicitud de negocio guiada y un alcance técnico preparado por la aplicación en una propuesta BI estructurada, validarla con reglas determinísticas y someter su significado a una decisión humana explícita. La propuesta aprobada será una entrada versionada del Sprint 4, no una ejecución.

## 2. Alcance y exclusiones

### Incluido

- Captura guiada en español del objetivo, preguntas de negocio, periodo y dimensiones de interés.
- Descubrimiento semántico dinámico por bloques para interpretar tablas, columnas y relaciones técnicas según la solicitud de ventas.
- Confirmación de conceptos y alcance en lenguaje de negocio, sin requerir identificadores técnicos.
- Modo avanzado opcional para que un analista BI ajuste el alcance; nunca es obligatorio para el gerente.
- Inclusión automática y visible de tablas/columnas requeridas por claves declaradas.
- Mapa semántico versionado generado para cada instantánea: concepto, nombre y explicación en español, referencias técnicas y confianza declarada.
- Paquete compacto de metadatos con hash, versión y presupuesto de tamaño.
- Adaptadores para usar la única configuración LLM activa y previamente probada.
- Plantilla de instrucciones versionada y salida JSON contractual.
- Validación sintáctica, referencial, semántica mínima y de operaciones permitidas.
- Persistencia de propuesta, resultados de validación, proveedor/modelo y decisión humana.
- Versionado por regeneración; las propuestas y revisiones no se sobrescriben.

### Excluido

- Chat libre, preguntas generales, historial conversacional abierto o agentes autónomos.
- Envío de filas, valores, usuarios, auditoría, secretos o datos personales al proveedor.
- SQL, código Python, scripts ETL o expresiones ejecutables generadas por el LLM.
- Creación de tablas, transformación, carga, KPI calculado, dashboard o pronóstico.
- Aprobación automática por puntaje del modelo.
- Comparación automática de proveedores o selección del “mejor” LLM.
- Selección manual obligatoria de tablas o escritura de SQL por parte del usuario de negocio.
- Intervención de un programador para preparar consultas por cada solicitud.

## 3. Actores, flujo y estados

### 3.1 Prerrequisitos

- Sesión válida y permisos correspondientes.
- Instantánea de metadatos vigente.
- Solicitud de negocio válida y una conexión activa con instantánea capaz de producir un alcance técnico no vacío.
- Una sola configuración LLM activa, cuya última prueba sea exitosa.

Si falta un prerrequisito, la interfaz explica el paso necesario y no envía una solicitud al proveedor.

### 3.2 Flujo principal

1. El gerente comercial o analista elige una plantilla como **Analizar ventas** y expresa qué necesita conocer mediante campos y opciones en español.
2. FastAPI valida longitud, formato y catálogo de la solicitud; el texto se trata como dato de negocio, no como una instrucción del sistema.
3. FastAPI divide determinísticamente la instantánea en bloques que conservan nombres, tipos, PK, FK y componentes relacionados, dentro del presupuesto del proveedor.
4. El LLM procesa cada bloque con la tarea `discover_sales_semantics`: identifica candidatos vinculados con la solicitud y propone conceptos y explicaciones en español.
5. FastAPI valida cada tabla, columna y relación contra la instantánea. Descarta referencias inventadas, registra el resultado de cada bloque y combina sólo candidatos válidos.
6. Cuando existen candidatos válidos, FastAPI prepara un mapa semántico y un alcance compacto. Si existen ambigüedades, la interfaz solicita una aclaración de negocio antes de continuar.
7. La aplicación muestra conceptos, relaciones y advertencias en español. El detalle de tablas queda plegado como información avanzada.
8. La persona confirma el alcance de negocio. Un analista con permiso puede abrir el modo avanzado y ajustar tablas sin introducir nombres libres.
9. FastAPI crea el paquete final y calcula `input_hash`.
10. FastAPI recupera la configuración LLM activa y su secreto cifrado mediante el almacén definido en SPR-03-04.
11. El adaptador solicita una propuesta dimensional con tiempo máximo y límites de salida.
12. La respuesta se analiza contra el esquema JSON. Si no cumple, queda `validation_failed`.
13. Los validadores comparan cada referencia con la instantánea y producen errores, advertencias e información.
14. Sin errores, la propuesta queda `ready_for_review`.
15. El revisor evalúa granularidad, dimensiones, KPIs, traducciones, supuestos y utilidad para el negocio; puede aprobar, rechazar con motivo o solicitar otra versión. No revisa SQL porque el Sprint 3 no lo genera.
16. Al aprobar una sustitución, la persona confirma expresamente el reemplazo y la propuesta aprobada anterior del mismo análisis pasa a `superseded` dentro de la misma transacción.

No existe una lista codificada de tablas AdventureWorks que se presente como interpretación de IA. La misma secuencia debe operar sobre otra base relacional de ventas cuando se implemente su conector: cambian los metadatos y el mapa producido, no el contrato de la experiencia. AdventureWorks sigue siendo la única fuente exigida para las pruebas funcionales de esta investigación.

### 3.3 Estados

| Estado | Significado | Transiciones permitidas |
|---|---|---|
| `generating` | Solicitud en curso. | `validation_failed`, `ready_for_review`, `provider_failed`. |
| `provider_failed` | Proveedor inaccesible, tiempo agotado o respuesta no utilizable. | Nueva propuesta. |
| `validation_failed` | Contrato o reglas incumplidos. | Nueva propuesta. |
| `ready_for_review` | Sin errores determinísticos; puede contener advertencias. | `approved`, `rejected`, nueva propuesta. |
| `approved` | Decisión humana favorable e inmutable. | `superseded`. |
| `rejected` | Decisión humana negativa con comentario. | Nueva propuesta. |
| `superseded` | Sustituida de forma explícita por otra aprobación. | Ninguna. |

Cerrar el navegador no cancela la trazabilidad del intento ya aceptado por el backend. La recuperación de trabajos asíncronos se limitará a un tiempo de solicitud razonable; una cola distribuida queda fuera del prototipo.

## 4. Datos y contratos

### 4.1 Persistencia propuesta

Tabla `app.bi_proposals`:

| Campo | Regla |
|---|---|
| `id` | Identificador interno. |
| `metadata_snapshot_id` | FK a la instantánea inmutable. |
| `parent_proposal_id` | FK opcional a la versión que motivó la regeneración. |
| `business_goal` | Objetivo de negocio normalizado, de longitud limitada y sin instrucciones técnicas ejecutables. |
| `business_questions` | Lista controlada de preguntas o intereses comerciales. |
| `scope_mode` | `guided` por defecto o `advanced` cuando un analista autorizado ajustó la selección. |
| `scope_document` | Conceptos solicitados, objetos técnicos derivados, dependencias y versión del proceso de descubrimiento. |
| `semantic_map_document` | Equivalencias dinámicas entre conceptos españoles y el origen técnico, explicaciones, confianza, referencias y validación. |
| `status` | Catálogo cerrado de estados. |
| `input_hash` | Huella del paquete enviado, sin secreto. |
| `prompt_version` | Versión de instrucciones del sistema. |
| `contract_version` | Versión del JSON esperado. |
| `provider_kind`, `model_id` | Evidencia técnica no secreta usada al generar. |
| `proposal_document` | JSONB estructurado aceptado; vacío si el proveedor no produjo un documento válido. |
| `validation_document` | JSONB con códigos, nivel, ruta y mensaje de cada hallazgo. |
| `review_comment` | Motivo o comentario humano; obligatorio al rechazar o solicitar nueva versión. |
| `created_by_user_id`, `reviewed_by_user_id` | Referencias con `SET NULL` y etiqueta histórica segura. |
| `created_at`, `reviewed_at` | Fechas UTC del servidor. |

No se persisten claves, encabezados HTTP, cadena de conexión, razonamiento interno del modelo ni una conversación completa. Se conserva la propuesta estructurada necesaria para reproducibilidad académica.

### 4.2 Contrato de descubrimiento semántico

Cada bloque usa un contrato reducido con la tarea `discover_sales_semantics`, la solicitud normalizada y metadatos técnicos. Su salida contiene únicamente candidatos:

```json
{
  "contract_version": 1,
  "candidates": [
    {
      "business_concept": "venta",
      "business_name_es": "Detalle de venta",
      "description_es": "Registro que representa un artículo incluido en una operación de venta.",
      "technical_refs": ["Sales.SalesOrderDetail"],
      "confidence": "high",
      "reason": "Contiene cantidades, precio y relación con el pedido."
    }
  ],
  "ambiguities": []
}
```

FastAPI no acepta un candidato hasta comprobar que todas sus referencias pertenecen al bloque y a la instantánea. La traducción es dinámica y puede variar por fuente, pero los identificadores originales nunca se sustituyen ni se inventan.

### 4.3 Contrato de entrada para la propuesta dimensional

```json
{
  "request_version": 1,
  "language": "es",
  "task": "propose_sales_dimensional_model",
  "source": {"connection_id": 1, "connector": "sqlserver", "snapshot_hash": "..."},
  "business_request": {
    "goal": "Analizar las ventas mensuales por producto, cliente y territorio.",
    "questions": ["¿Cuánto se vendió por mes?", "¿Qué productos venden más?"],
    "requested_dimensions": ["fecha", "producto", "cliente", "territorio"]
  },
  "scope": {
    "origin": "semantic-discovery:v1",
    "mode": "guided",
    "tables": [
      {
        "schema": "Sales",
        "name": "SalesOrderDetail",
        "columns": [],
        "foreign_keys": []
      }
    ]
  },
  "constraints": {
    "no_sql": true,
    "human_approval_required": true,
    "allowed_etl_operations": ["extract", "join", "filter", "derive", "aggregate", "load"],
    "technical_names_must_exist": true
  }
}
```

El paquete incluye únicamente la solicitud de negocio normalizada, los objetos derivados y las dependencias confirmadas. El texto del usuario queda claramente delimitado como dato y no puede modificar las instrucciones del sistema. Si excede el presupuesto del proveedor, FastAPI no lo trunca silenciosamente: solicita reducir el alcance o aplica una compactación determinística que conserva nombres, tipos, PK y FK e informa el cambio.

### 4.4 Contrato de salida del LLM

```json
{
  "contract_version": 1,
  "domain": "ventas",
  "summary": "Modelo dimensional propuesto para analizar ventas.",
  "business_explanation": "Cada registro representará una línea vendida y podrá analizarse por fecha, producto, cliente y territorio.",
  "semantic_mapping": [
    {
      "business_name_es": "Detalle de venta",
      "technical_refs": ["Sales.SalesOrderDetail"]
    }
  ],
  "grain": {
    "description": "Una fila por línea de pedido de venta.",
    "source_tables": ["Sales.SalesOrderDetail"]
  },
  "fact": {
    "name": "fact_ventas",
    "source_tables": ["Sales.SalesOrderHeader", "Sales.SalesOrderDetail"],
    "business_keys": ["SalesOrderID", "SalesOrderDetailID"],
    "measures": [
      {"name": "importe_venta", "source_columns": ["LineTotal"], "aggregation": "sum"}
    ]
  },
  "dimensions": [
    {
      "name": "dim_producto",
      "source_tables": ["Production.Product"],
      "business_key": "ProductID",
      "attributes": ["Name", "ProductNumber"]
    }
  ],
  "joins": [],
  "kpis": [
    {
      "code": "ventas_totales",
      "name": "Ventas totales",
      "formula": {"operation": "sum", "measure": "importe_venta"},
      "unit": "currency"
    }
  ],
  "etl_plan": [
    {
      "order": 1,
      "operation": "extract",
      "inputs": ["Sales.SalesOrderHeader", "Sales.SalesOrderDetail"],
      "output": "stg_ventas",
      "description": "Extraer los campos aprobados para la carga completa."
    }
  ],
  "quality_rules": [],
  "assumptions": [],
  "warnings": []
}
```

Los nombres de destino permitidos en el alcance académico son `fact_ventas`, `dim_fecha`, `dim_producto`, `dim_cliente` y `dim_territorio`. Una propuesta puede justificar que una dimensión no aplica, pero no puede inventar otros módulos o ampliar el dominio.

### 4.5 Límite con la generación y ejecución de SQL

El LLM no produce SQL ejecutable. El equipo de desarrollo implementará una sola vez, dentro del Sprint 4, un constructor determinístico que traduzca el documento aprobado a operaciones tipadas y consultas parametrizadas. Ese módulo deberá:

- generar extracción de sólo lectura sobre AdventureWorks con `bi_reader`;
- materializar y cargar únicamente el esquema `mart` de PostgreSQL con una cuenta técnica de permisos mínimos;
- usar tablas, columnas, relaciones y operaciones incluidas en el contrato aprobado;
- presentar vista previa y validaciones antes de ejecutar;
- ejecutar desde FastAPI con transacciones, límites y auditoría;
- impedir que gerente, analista, navegador o LLM introduzcan SQL libre.

Por tanto, un programador construye el motor como parte del producto, pero no participa en la operación normal ni redacta consultas por cada usuario.

## 5. Validaciones determinísticas

### Errores que impiden revisión/aprobación

- Contrato JSON inválido, campos requeridos ausentes o versión desconocida.
- Tabla, columna, PK o FK inexistente en la instantánea referenciada.
- Tabla usada fuera del alcance confirmado.
- Objeto candidato que no existe en la instantánea, no pertenece al bloque procesado o no está conectado mediante relaciones declaradas.
- Traducción o concepto sin referencia técnica verificable.
- Solicitud de negocio que intenta introducir instrucciones del sistema, código o identificadores técnicos libres fuera del modo avanzado.
- Medida basada en un tipo no numérico sin transformación declarativa permitida.
- Agregación fuera del catálogo `sum`, `count`, `count_distinct`, `average`, `min` o `max`.
- KPI que referencia una medida inexistente o usa fórmula libre.
- Unión que no corresponde a una FK declarada o no identifica ambos extremos.
- Granularidad vacía o incompatible con la clave del hecho propuesta.
- Operación ETL fuera del catálogo permitido, SQL, código ejecutable o instrucción de escritura a la fuente.
- Más de un hecho o destino fuera del datamart de ventas aprobado.

### Advertencias que requieren atención humana

- Relación muchos a muchos, clave compuesta o columna nullable usada como clave de negocio.
- Medida potencialmente derivada, conversión monetaria o zona horaria no resuelta.
- Dimensión prevista por el alcance académico que el modelo omite con justificación.
- Supuesto no respaldado por metadatos.

El validador devuelve códigos estables y mensajes en español. El revisor debe confirmar que leyó las advertencias antes de aprobar.

## 6. API prevista

| Método y ruta | Permiso | Resultado |
|---|---|---|
| `POST /api/v1/copilot/proposals` | `copilot.proposals.generate` | Crea un intento desde una solicitud de negocio; FastAPI deriva el alcance técnico. |
| `GET /api/v1/copilot/proposals` | `copilot.proposals.read` | Lista paginada por estado, fecha y snapshot. |
| `GET /api/v1/copilot/proposals/{id}` | `copilot.proposals.read` | Propuesta, validaciones, procedencia y revisión. |
| `POST /api/v1/copilot/proposals/{id}/approve` | `copilot.proposals.review` | Aprueba sólo `ready_for_review`, con confirmación de advertencias. |
| `POST /api/v1/copilot/proposals/{id}/reject` | `copilot.proposals.review` | Rechaza con comentario obligatorio. |
| `POST /api/v1/copilot/proposals/{id}/regenerate` | `copilot.proposals.generate` | Genera otra versión con observación humana y referencia al padre. |

La solicitud de creación admite `metadata_snapshot_id`, `business_goal` de 20 a 500 caracteres, uno o más códigos de preguntas aprobadas y una periodicidad inicial `month`. El texto libre complementa el objetivo, pero no amplía el dominio ni habilita operaciones. Una petición de inventario, compras, finanzas u otro dominio se rechaza antes de consumir el proveedor con una explicación de alcance. Los conceptos o dimensiones no se vinculan a tablas predefinidas: se descubren desde los metadatos. `scope_mode=advanced` y las referencias de tabla sólo se aceptan con `metadata.read`; cada referencia debe proceder de la instantánea seleccionada.

Las operaciones de revisión son idempotentes por estado: repetir una aprobación no duplica eventos; intentar cambiar una decisión final devuelve 409.

## 7. Interfaz y experiencia

La ruta visible **IA > Asistente de análisis** usa un flujo guiado:

1. Objetivo y preguntas de negocio.
2. Conceptos y alcance sugerido.
3. Generación.
4. Validación automática.
5. Revisión de negocio.

El recorrido principal usa las etiquetas españolas generadas para la fuente activa y explica qué podrá obtenerse. Cada concepto muestra su explicación y un acceso **Ver origen técnico**. La propuesta se presenta por secciones: significado de la venta, granularidad, dimensiones, medidas, KPIs, plan ETL, reglas de calidad, supuestos y advertencias. Los nombres de tablas, relaciones y el JSON permanecen en **Detalles técnicos**, que puede consultar el analista, pero no son obligatorios para el gerente.

Estados obligatorios: prerrequisito faltante, listo para generar, generando, proveedor agotado/inaccesible, respuesta inválida, errores de validación, listo para revisar, aprobado, rechazado y sustituido.

En móvil, cada sección es un acordeón y las acciones de decisión permanecen visibles sin cubrir contenido. En escritorio amplio, el resumen puede convivir con un panel de explicación, pero no habrá chat abierto en Sprint 3. El foco, mensajes y confirmaciones cumplen SPR-02-04.

## 8. Seguridad y auditoría

- `copilot.proposals.read`, `generate` y `review` separan consulta, consumo de proveedor y decisión.
- FastAPI obtiene la única configuración LLM activa, verifica una prueba exitosa y recupera su secreto cifrado; React no lee credenciales.
- La URL se valida según el catálogo del proveedor del Sprint 2; no se aceptan destinos arbitrarios ni redirecciones.
- El paquete se construye en backend. El cliente no puede inyectar metadatos ni instrucciones del sistema.
- La solicitud de negocio se delimita, normaliza y limita; nunca se concatena con instrucciones privilegiadas ni se interpreta como SQL.
- Se limita tamaño, duración, reintentos y respuesta. No se reintenta automáticamente una operación que pueda duplicar consumo sin idempotencia.
- Eventos: `copilot.proposal.generate`, `provider_failed`, `validation_failed`, `ready_for_review`, `approve`, `reject`, `regenerate` y `supersede`.
- La auditoría contiene ids, hashes, estado, proveedor/modelo y códigos de validación; nunca clave, prompt completo, cabeceras ni razonamiento del modelo.

## 9. Criterios de aceptación verificables

- [ ] Sólo se puede generar con instantánea válida, solicitud de negocio confirmada, alcance derivado, permiso y configuración LLM activa/probada.
- [ ] Un gerente puede completar el recorrido guiado sin seleccionar tablas, escribir identificadores ni conocer SQL.
- [ ] El descubrimiento por bloques deriva un alcance reproducible usando únicamente objetos y PK/FK existentes.
- [ ] El modo avanzado está claramente separado y no acepta identificadores técnicos escritos libremente.
- [ ] El proveedor recibe exclusivamente el paquete de metadatos permitido y nunca filas, secretos o usuarios.
- [ ] La respuesta se acepta únicamente si cumple el contrato JSON versionado.
- [ ] Una referencia inventada produce error determinístico y bloquea aprobación.
- [ ] Una propuesta válida presenta hecho, granularidad, dimensiones, medidas, al menos un KPI y plan ETL declarativo.
- [ ] Ninguna propuesta contiene SQL o código ejecutable utilizable por el sistema.
- [ ] Sólo `ready_for_review` puede aprobarse y las advertencias requieren confirmación.
- [ ] Rechazar requiere comentario; regenerar crea otra versión y no sobrescribe la anterior.
- [ ] Una sola propuesta queda aprobada por análisis y la sustitución es explícita y transaccional.
- [ ] La interfaz diferencia claramente contenido propuesto por IA, resultado del validador y decisión humana.
- [ ] El LLM interpreta nombres técnicos en inglés y genera conceptos comprensibles en español para la fuente activa.
- [ ] La explicación relaciona cada concepto con identificadores técnicos consultables y cualquier tabla o columna inventada queda descartada y auditada.
- [ ] No existe una tabla de traducciones codificada sólo para AdventureWorks como sustituto de la interpretación dinámica.
- [ ] La documentación declara que el futuro SQL será generado por el motor determinístico del Sprint 4 y no por el LLM ni por un programador durante cada análisis.
- [ ] Errores, cuotas y tiempos agotados no exponen secretos ni dejan estados engañosos.
- [ ] Todo el flujo se prueba con proveedor simulado en CI y al menos una prueba manual real documentada.

## 10. Plan de pruebas y evidencia

- Unitarias: solicitud de negocio, partición estable, descubrimiento semántico, combinación de candidatos, esquema JSON, referencias inventadas, joins, tipos numéricos, granularidad, fórmulas KPI y operaciones ETL.
- Integración: estados, inmutabilidad, versiones, aprobación única, transacciones y auditoría.
- Adaptadores: Gemini, Qwen Cloud y Ollama mediante respuestas simuladas; Ollama real como alternativa local.
- Seguridad: 401/403, inyección de metadatos, URL no permitida, tamaño excesivo y sanitización de errores.
- Frontend: recorrido no técnico, modo avanzado, prerrequisitos, secciones, advertencias, confirmaciones, estados y responsive.
- Evidencia académica: hash de entrada, versión de prompt/contrato, proveedor/modelo, propuesta validada y decisión humana.

## 11. Riesgos, dependencias y decisiones

- `qwen2.5:3b` prioriza agilidad, pero puede producir propuestas menos completas: el contrato y el validador deben funcionar igual con cualquier proveedor aprobado.
- El contexto local es limitado: FastAPI procesa bloques con presupuesto estable y conserva trazabilidad; esto puede requerir varias llamadas y debe mostrar progreso y consumo.
- Una salida válida sintácticamente puede ser inadecuada para negocio: por eso la aprobación humana no se reemplaza por validación automática.
- Un gerente puede validar utilidad y significado, pero no necesariamente relaciones técnicas: los validadores cubren integridad estructural y el modo avanzado queda para un analista BI.
- La interpretación dinámica puede asignar etiquetas imprecisas aunque las referencias existan: por eso cada concepto muestra confianza, explicación y origen, y requiere aprobación humana.
- Depende de SPR-03-01, SPR-03-04 y ADR 0003.

## 12. Resultado de implementación

Pendiente. Al cerrar el PR se documentarán proveedor real probado, SHA, casos ejecutados, resultado, desviaciones y estado final.
