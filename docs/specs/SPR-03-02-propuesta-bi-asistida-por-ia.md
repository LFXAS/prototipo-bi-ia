# SPR-03-02: propuesta BI asistida por IA y supervisada

> **Evolución vigente (Sprint 6).** Donde este documento dice “fuente activa”, el
> contrato actual usa la fuente seleccionada y validada mediante `connection_id`. El
> catálogo funcional es independiente por conexión y la cobertura técnica se recalcula
> desde su instantánea; véase
> [SPR-06-01](SPR-06-01-contexto-multifuente-sqlserver.md).

- Estado: **implementado y verificado localmente; pendiente de validación del usuario**.
- Pertenece a: [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md).
- Fecha de creación: 2026-09-14.
- Rama prevista de implementación: `feature/sprint-03-metadata-copilot`.
- PR de implementación: pendiente.

## 1. Problema y objetivo

Una instantánea técnica no determina por sí sola qué tabla representa el proceso de ventas, cuál debe ser la granularidad del hecho, qué dimensiones son pertinentes ni qué KPIs son calculables. Tampoco es razonable exigir que un gerente seleccione tablas o que un programador prepare SQL para cada análisis. El proyecto necesita demostrar asistencia de IA para transformar una necesidad comercial en una propuesta BI, sin delegarle la ejecución ni aceptar referencias inventadas.

El objetivo es integrar la configuración LLM activa del Sprint 2 para convertir una solicitud de negocio guiada y un alcance técnico preparado por la aplicación en una propuesta BI estructurada, validarla con reglas determinísticas y someter su significado a una decisión humana explícita. La propuesta aprobada será una entrada versionada del Sprint 4, no una ejecución.

## 2. Alcance y exclusiones

### Incluido

- Captura guiada en español del objetivo, preguntas de negocio y periodicidad. Las dimensiones no se solicitan en este paso: el LLM debe proponerlas a partir de la necesidad y de los metadatos verificados.
- Sugerencias de necesidades desde la instantánea, reformulación de un objetivo y revisión previa IA/reglas, con referencias comprobadas, límites visibles, consentimiento por destino LLM y adopción humana explícita.
- Descubrimiento semántico dinámico por bloques para interpretar tablas, columnas y relaciones técnicas según la solicitud de ventas.
- Confirmación de conceptos y alcance en lenguaje de negocio, sin requerir identificadores técnicos.
- Inclusión automática de tablas y columnas relacionadas por claves declaradas; el usuario sólo las consulta como trazabilidad.
- Mapa semántico versionado generado para cada instantánea: concepto, nombre y explicación en español, referencias técnicas y confianza declarada.
- Paquete compacto de metadatos con hash, versión y presupuesto de tamaño.
- Adaptadores para usar la única configuración LLM activa y previamente probada.
- Plantilla de instrucciones versionada y salida JSON contractual.
- Validación sintáctica, referencial, semántica mínima y de operaciones permitidas.
- Persistencia de propuesta, resultados de validación, proveedor/modelo y decisión humana.
- Conservación de cada intento; las propuestas y decisiones no se sobrescriben.
- Selección de cualquier versión persistida para volver a examinarla y decidirla sin consumir nuevamente el proveedor.
- Catálogo de dominios y capacidades calculado en backend desde la instantánea vigente; las preguntas y periodicidades no se codifican en React y las dimensiones pertenecen al resultado de la IA.
- Catálogo analítico administrable por dominio: permite CRUD de preguntas de negocio y varias periodicidades soportadas, con permisos separados de los parámetros generales. No almacena objetivos ni dimensiones.
- Personalización supervisada de decisiones de negocio ya verificadas, creando una versión derivada y auditada sin SQL libre.
- Filtro por estado y dominio, con paginación del historial y estado inicial **Lista para revisar**.

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

1. El analista BI abre **Asistente de datamart**, consulta los dominios disponibles y selecciona **Datamart de ventas**. El catálogo se deriva de la instantánea y de perfiles versionados; sólo se habilitan capacidades con evidencia técnica.
2. La pantalla obtiene del backend preguntas orientadoras y periodicidades compatibles. El analista escribe el objetivo específico en español o solicita sugerencias desde la fuente; React no mantiene un modelo dimensional fijo de AdventureWorks. Antes del envío confirma proveedor/modelo y datos estructurales permitidos. La sugerencia no sustituye su texto hasta que decide usarla.
   Antes de generar conceptos se revisa el texto definitivo con IA y reglas determinísticas; la evaluación y sus huellas se persisten para el mismo actor, instantánea, preguntas y período. Las limitaciones se confirman o se modifica la necesidad; la comprobación no aprueba automáticamente el futuro contrato BI.
3. Las dimensiones, el hecho, las medidas, la granularidad, los KPIs y el plan ETL son decisiones propuestas por el LLM desde los metadatos. La aplicación valida referencias y coherencia; el analista puede personalizar la propuesta sin escribir SQL.
4. FastAPI valida la solicitud y divide la instantánea en bloques que conservan nombres, tipos, PK y FK.
5. El LLM identifica en cada bloque posibles conceptos de ventas y los explica en español.
6. FastAPI elimina cualquier referencia inexistente y une únicamente candidatos conectados por relaciones declaradas.
7. Si el resultado es ambiguo o vacío, la pantalla pide al usuario precisar su necesidad; no exige seleccionar tablas.
8. La pantalla presenta concepto, explicación y origen técnico plegable para que la persona confirme el significado.
9. FastAPI recupera la configuración LLM activa, forma el paquete final y solicita decisiones dimensionales compactas en JSON.
10. La aplicación expande esas decisiones con PK, FK, atributos, reglas y operaciones determinísticas; después comprueba contrato, referencias, relaciones, granularidad, medidas y KPIs.
11. Una propuesta con errores queda bloqueada; una propuesta válida queda lista para revisión.
12. El analista puede abrir **Personalizar propuesta** y ajustar resumen, granularidad, dimensiones, medidas, agregaciones y KPIs entre las opciones ya verificadas. El backend rechaza objetos nuevos, elimina dependencias incoherentes, vuelve a validar y crea una versión enlazada a la original.
13. Cada medida y KPI declara una función semántica tipada (`sales_amount`, `quantity`, `customer_count` o `transaction_count`). El backend comprueba columna, agregación, operación y compatibilidad KPI--medida; el nombre visible nunca basta para aceptar una fórmula.
14. Las observaciones libres del proveedor se conservan sólo como trazabilidad. Los ajustes automáticos se muestran como información y únicamente los problemas confirmados por reglas determinísticas cuentan como advertencias o errores.
15. El historial consulta al servidor por dominio y estado, muestra por defecto versiones listas para revisar y pagina el resultado. Cada fila permite abrir el artefacto persistido sin volver a ejecutar el LLM.
16. Una persona autorizada selecciona la versión que considera adecuada y la aprueba o rechaza con comentario. La decisión queda auditada y el registro no se sobrescribe.

Si la primera propuesta no satisface la necesidad, el analista no queda obligado a aceptarla. Puede volver al objetivo, ajustar preguntas y dimensiones, descartar conceptos semánticos no pertinentes y generar una nueva versión con IA; o puede personalizar las decisiones verificadas sin consumir nuevamente el proveedor. La versión anterior se conserva. No se admiten SQL, columnas libres ni relaciones manuales: todo ajuste vuelve a pasar por el validador determinístico.

No existe una lista codificada de tablas AdventureWorks que se presente como interpretación de IA. La misma secuencia debe operar sobre otra base relacional de ventas cuando se implemente su conector: cambian los metadatos y el mapa producido, no el contrato de la experiencia. Desde Sprint 6 la validación funcional incluye AdventureWorks y WideWorldImporters con el mismo adaptador SQL Server; esto no acredita otros motores ni cualquier esquema desconocido.

La implementación registra `connector_code` y `domain_code`. El contrato de metadatos es neutral al motor y el backend despacha la lectura mediante un registro de adaptadores; SQL Server es el único adaptador habilitado. Las preguntas de negocio son configurables, mientras que las reglas semánticas, destinos admitidos y validadores pertenecen a un perfil de dominio. `ventas` es el único perfil habilitado y validado. Un motor o dominio futuro debe incorporar y probar su adaptador o perfil antes de aparecer como opción disponible.

### 3.3 Estados

| Estado | Significado | Transiciones permitidas |
|---|---|---|
| `generating` | Solicitud en curso. | `validation_failed`, `ready_for_review`, `provider_failed`. |
| `provider_failed` | Proveedor inaccesible, tiempo agotado o respuesta no utilizable. | Nueva propuesta. |
| `validation_failed` | Contrato o reglas incumplidos. | Nueva propuesta. |
| `ready_for_review` | Sin errores determinísticos; puede contener advertencias. | `approved`, `rejected`, nueva propuesta. |
| `approved` | Decisión humana favorable; sigue sujeta a revalidación antes del ETL. | `invalidated` únicamente mediante una decisión explícita y auditada. |
| `rejected` | Decisión humana negativa con comentario. | Ninguna; un nuevo intento crea otro registro. |
| `invalidated` | Aprobación retirada manualmente o por incumplir reglas bloqueantes vigentes. | Restauración auditada cuando sólo exista compatibilidad histórica, versión corregida o `discarded`. |
| `discarded` | Retirada de las listas operativas sin eliminar auditoría ni linaje. | Terminal. |

Cada intento aceptado por el backend conserva su estado aunque se cierre el navegador. Una cola distribuida queda fuera del prototipo.

## 4. Datos y contratos

### 4.1 Persistencia propuesta

Tabla `app.bi_proposals`:

| Campo | Regla |
|---|---|
| `id` | Identificador interno. |
| `source_proposal_id` | Enlace opcional a la versión desde la que se generó o personalizó el registro. |
| `metadata_snapshot_id` | FK a la instantánea inmutable. |
| `business_goal` | Objetivo de negocio normalizado, de longitud limitada y sin instrucciones técnicas ejecutables. |
| `business_questions` | Lista controlada de preguntas o intereses comerciales. |
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

La revisión previa se conserva separadamente en `app.business_need_reviews`, creada
por la migración aditiva `20261003_19`: instantánea, actor, huella de entrada,
huella y documento de evaluación, proveedor/modelo e instante. Es evidencia no
ejecutable; no reemplaza `bi_proposals` ni altera versiones históricas. La generación
exige encontrar una evaluación coincidente, no aceptar una huella calculada sólo en
el navegador o por la comprobación heurística anterior.
La huella incorpora la versión de reglas `need-review-2`: las evaluaciones anteriores
se conservan para auditoría, pero no autorizan una generación nueva hasta repetir la
revisión con las reglas vigentes. Esta invalidación de revisión no retira aprobaciones
ni altera contratos o materializaciones existentes.

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
    "periodicity": "month"
  },
  "scope": {
    "origin": "semantic-discovery:v1",
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

### 4.4 Decisiones compactas del LLM

```json
{
  "contract_version": 1,
  "domain": "ventas",
  "summary": "Ventas por producto, cliente y territorio.",
  "grain_description": "Una fila por línea vendida.",
  "fact_source": "Sales.SalesOrderDetail",
  "measures": [
    {"name": "importe_venta", "source_column": "LineTotal", "aggregation": "sum"}
  ],
  "dimensions": [
    {"name": "dim_producto", "source_table": "Production.Product"}
  ],
  "kpis": [
    {"code": "ventas_totales", "name": "Ventas totales", "measure_index": 0, "operation": "sum", "unit": "moneda"}
  ],
  "assumptions": [],
  "warnings": []
}
```

La salida se restringe mediante un esquema JSON dinámico construido desde la instantánea: la tabla de hechos procede de los conceptos de venta detectados; las medidas sólo pueden usar columnas cuantitativas del candidato; las dimensiones sólo pueden seleccionar tablas del alcance; y cada KPI referencia por índice una medida elegida. Esta salida breve permite que un modelo local pequeño tome las decisiones analíticas sin obligarlo a repetir claves, atributos, relaciones y pasos mecánicos.

El contrato compacto exige además `semantic_role` en medidas y KPIs. Los identificadores verificados pueden proponerse únicamente para conteos tipados; un importe no puede representar clientes y un identificador no puede sumarse. Si el LLM asocia un KPI con una medida incompatible, el backend excluye esa decisión, explica la causa y enumera medidas compatibles. Si no queda ningún KPI válido, la propuesta falla y no puede aprobarse.

### 4.5 Expansión determinística del contrato

FastAPI amplía las decisiones del LLM con datos comprobables de la instantánea: claves de negocio, atributos descriptivos, uniones FK, reglas de calidad y plan ETL tipado. El documento final conserva `ai_decisions` para distinguir lo propuesto por la IA de lo completado por la aplicación. Después se ejecuta el mismo validador determinístico sobre el contrato expandido.

Los nombres de destino permitidos en el alcance académico son `fact_ventas`, `dim_fecha`, `dim_producto`, `dim_cliente` y `dim_territorio`. Una propuesta puede justificar que una dimensión no aplica, pero no puede inventar otros módulos o ampliar el dominio.

### 4.6 Límite con la generación y ejecución de SQL

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
- Objeto candidato que no existe en la instantánea o no está conectado mediante relaciones declaradas.
- Traducción o concepto sin referencia técnica verificable.
- Solicitud de negocio que intenta introducir instrucciones del sistema, código o identificadores técnicos libres.
- Medida basada en un tipo no numérico sin transformación declarativa permitida.
- Contradicción semántica conocida entre capacidad y referencia: un precio de venta
  no acredita costo unitario, un identificador no acredita importe, ni una tasa
  acredita un descuento monetario. El control utiliza roles y alias generales en
  español e inglés; no bifurca por nombre de base. Un nombre no reconocido exige
  revisión y no se acepta automáticamente por tener tipo numérico.
- Fecha, texto o clave dimensional usados como operandos de una medida aritmética:
  sumar ventas por mes requiere importe numérico y fecha separados, no una medida
  derivada que trate la fecha como número.
- Agregación fuera del catálogo `sum`, `count`, `count_distinct`, `average`, `min` o `max`.
- KPI que referencia una medida inexistente o usa fórmula libre.
- Unión que no corresponde a una FK declarada o no identifica ambos extremos.
- Granularidad vacía o incompatible con la clave del hecho propuesta.
- Operación ETL fuera del catálogo permitido, SQL, código ejecutable o instrucción de escritura a la fuente.
- Más de un hecho o destino fuera del datamart de ventas aprobado.
- Si la necesidad exige ventas facturadas o facturas emitidas, el hecho y el
  identificador y la fecha de transacción deben provenir del evento de factura
  verificado;
  líneas de pedido no pueden sustituirlo aunque el LLM use el término «venta».
- Un promedio por transacción debe dividir el importe agregado entre documentos
  distintos. `AVG(importe de línea)` sólo puede llamarse promedio por línea.
- Un ranking de producto, cliente o territorio no puede calcularse con el
  máximo de una línea: primero requiere agregar por entidad. De igual manera,
  `AVG(importe de línea)` no equivale a promedio por cliente o territorio.
  Estas reglas se aplican a denominaciones equivalentes en español e inglés.
- La cobertura declarada por la IA se recalcula desde las medidas y KPI realmente
  incluidos; no basta con que el texto diga que una necesidad está cubierta.
- Una afirmación del proveedor que contradiga una columna presente en la
  instantánea se rechaza antes de la aprobación.

### Advertencias que requieren atención humana

- Relación muchos a muchos, clave compuesta o columna nullable usada como clave de negocio.
- Medida potencialmente derivada, conversión monetaria o zona horaria no resuelta.
- Dimensión prevista por el alcance académico que el modelo omite con justificación.
- Supuesto no respaldado por metadatos.

La auditoría QA-E2E-20261003 mostró estos riesgos con propuestas reales de
AdventureWorks y WideWorldImporters. La integración puede adaptar la solicitud
de salida estructurada a las capacidades de cada proveedor (en Claude,
`output_config.format` y un reintento acotado ante salida truncada), pero todos
los resultados pasan por el mismo contrato y validador local. Los errores del
contrato JSON y los límites de cuota se registran como fallos del proveedor,
conservando la necesidad y sin aprobar automáticamente ninguna versión. Véase
`docs/testing/auditoria-operativa-2026-10-03.md`.

El validador devuelve códigos estables y mensajes en español. El revisor debe confirmar que leyó las advertencias antes de aprobar.

## 6. API prevista

| Método y ruta | Permiso | Resultado |
|---|---|---|
| `POST /api/v1/copilot/needs/suggest` | `copilot.proposals.generate` | Sugiere hasta dos necesidades con evidencia y límites desde la instantánea vigente; no exige objetivo inicial ni preguntas seleccionadas. |
| `POST /api/v1/copilot/needs/formulate` | `copilot.proposals.generate` | Mejora un objetivo existente bajo los límites reales de la estructura y conserva el texto original. |
| `POST /api/v1/copilot/needs/viability` | `copilot.proposals.generate` | Revisa el objetivo sin sustituirlo, combina IA y reglas, persiste la evaluación y devuelve su huella. |
| `POST /api/v1/copilot/proposals` | `copilot.proposals.generate` | Crea un intento desde una solicitud de negocio; FastAPI deriva el alcance técnico. |
| `GET /api/v1/copilot/catalog` | `copilot.proposals.read` | Devuelve dominios, preguntas orientadoras y periodicidades disponibles para la instantánea vigente; no predefine dimensiones. |
| `GET /api/v1/analysis-catalog/domains` | `copilot.catalog.read` | Lista dominios con catálogo analítico implementado. |
| `GET /api/v1/analysis-catalog/domains/{code}` | `copilot.catalog.read` | Consulta preguntas y periodicidades del dominio. |
| `PUT /api/v1/analysis-catalog/domains/{code}` | `copilot.catalog.write` | Guarda el catálogo validado con trazabilidad. |
| `POST /api/v1/analysis-catalog/domains/{code}/reset` | `copilot.catalog.write` | Restaura el catálogo validado del dominio. |
| `GET /api/v1/copilot/proposals` | `copilot.proposals.read` | Lista paginada y filtrable por uno o varios estados y por dominio. |
| `GET /api/v1/copilot/proposals/{id}` | `copilot.proposals.read` | Propuesta, validaciones, procedencia y revisión. |
| `POST /api/v1/copilot/proposals/{id}/revisions` | `copilot.proposals.generate` | Crea una versión derivada con ajustes supervisados y vuelve a validarla sin llamar al LLM. |
| `POST /api/v1/copilot/proposals/{id}/verify` | `copilot.proposals.read` | Recalcula la evidencia estructural y la reproducción determinística del contrato. |
| `POST /api/v1/copilot/proposals/{id}/approve` | `copilot.proposals.review` | Aprueba sólo `ready_for_review`, con confirmación de advertencias. |
| `POST /api/v1/copilot/proposals/{id}/reject` | `copilot.proposals.review` | Rechaza con comentario obligatorio. |
| `POST /api/v1/copilot/proposals/{id}/invalidate` | `copilot.proposals.review` | Retira una aprobación con motivo obligatorio y conserva auditoría. |
| `POST /api/v1/copilot/proposals/{id}/restore-approval` | `copilot.proposals.review` | Restaura de forma auditada una aprobación retirada cuando no existen errores bloqueantes vigentes. |
| `POST /api/v1/copilot/proposals/{id}/discard` | `copilot.proposals.generate` | Descarta una versión no aprobada sin borrarla físicamente. |

La solicitud de creación admite `metadata_snapshot_id`, `business_goal` de 20 a 2000 caracteres, uno o más códigos de preguntas habilitadas y una periodicidad inicial `month`. Exige además `viability_hash` de una revisión persistida coincidente y `metadata_consent_target` del destino LLM vigente. El texto libre complementa el objetivo, pero no amplía el dominio ni habilita operaciones. Las peticiones claramente ajenas al dominio se rechazan mediante las reglas de entrada; el análisis IA también puede declarar partes sin respaldo, pero no se presenta como detección exhaustiva de toda intención en lenguaje natural. Los conceptos o dimensiones no se vinculan a tablas predefinidas: se descubren desde los metadatos.

Las tres operaciones de necesidad usan `metadata_consent_target`; el servidor lo
comprueba antes de recuperar la credencial o llamar al proveedor. Las preguntas y
periodicidad deben pertenecer al catálogo habilitado de la conexión de la instantánea.
Sugerir no crea ni aprueba una propuesta y no guarda una nueva pregunta del catálogo.

Las operaciones de revisión son idempotentes por estado: repetir una aprobación no duplica eventos; intentar cambiar una decisión final devuelve 409.

## 7. Interfaz y experiencia

La ruta visible **IA > Asistente de datamart** empieza por un catálogo de dominios y usa un flujo guiado:

1. Necesidad de negocio.
2. Conceptos encontrados y su origen.
3. Propuesta y validación automática.
4. Personalización supervisada opcional.
5. Revisión humana.

El campo **Objetivo del análisis** admite hasta 2000 caracteres, muestra al menos
doce líneas visibles y puede ampliarse verticalmente. El contador y la ayuda se
mantienen fuera del área editable para que una necesidad completa pueda revisarse
sin texto oculto ni superposiciones.

El recorrido principal usa las etiquetas españolas generadas para la fuente activa y explica qué podrá obtenerse. Cada concepto muestra su explicación y un acceso **Ver origen técnico**. La propuesta se presenta por secciones: significado de la venta, granularidad, dimensiones, medidas, KPIs, plan ETL, reglas de calidad, supuestos y advertencias. Los nombres de tablas, relaciones y el JSON permanecen en **Detalles técnicos**, que el analista consulta sólo cuando necesita verificar la trazabilidad.

En la revisión de la necesidad, la interfaz distingue **Referencia estructural
comprobada** y **Derivación candidata**. Para los requisitos de origen IA (`ai:*`),
la explicación o fórmula se presenta como **Interpretación propuesta por IA
(no ejecutable)**, no como receta aprobada. Una reformulación no utilizable permite
**Mantener mi redacción** y revisar el objetivo original; no obliga a aceptar el texto
del proveedor ni garantiza que toda reformulación pueda adoptarse.

Estados obligatorios: prerrequisito faltante, generando, proveedor inaccesible, validación fallida, listo para revisar, aprobado y rechazado.

Debajo del recorrido se presenta **Versiones generadas** con paginación y filtro de estado. El filtro inicial es **Lista para revisar** para priorizar trabajo pendiente; el analista puede cambiar a aprobadas, rechazadas, con problemas o todas. Cada fila identifica el proveedor y modelo usados, señala si deriva de otra versión y permite **Abrir resultado**. La versión elegida repone su necesidad, conceptos, propuesta, validación y decisión en las mismas vistas del asistente. Esta consulta no llama nuevamente al LLM y permite preparar previamente una evidencia local lenta —por ejemplo Qwen en CPU— y compararla con una ejecución cloud rápida durante la sustentación. La aplicación no elige automáticamente al “mejor” proveedor: la selección y aprobación pertenecen al analista BI.

La versión seleccionada presenta además **Validación estructural de la propuesta - Sprint 3**. La acción **Verificar evidencia** recalcula la integridad de metadatos, las referencias, el contrato y la validación, y reconstruye la propuesta desde las decisiones IA guardadas. Esta acción es estrictamente de sólo lectura: no llama al LLM, no modifica el estado de la propuesta y no altera decisiones humanas ni expedientes ETL. La huella reconstruida se conserva como evidencia diagnóstica; una diferencia puede revelar evolución del normalizador determinístico incluso cuando el identificador funcional del contrato no haya cambiado.

Una diferencia entre la huella persistida y la reconstruida se muestra como advertencia de compatibilidad y no invalida por sí sola el contrato. Sólo la integridad de la instantánea, las referencias reales y los errores vigentes de validación estructural determinan si el contrato es seguro para una nueva ejecución. Una versión aprobada cambia a **Aprobación retirada** únicamente cuando una persona autorizada ejecuta esa decisión con su motivo; la comprobación previa al ETL puede bloquear una ejecución nueva, pero tampoco cambia el estado histórico. Si una aprobación fue retirada por un falso positivo anterior, una migración auditable puede restaurarla cuando existe un ETL conciliado con la misma propuesta e instantánea. Los intentos no aprobados pueden marcarse **Descartados**; no aparecen en el trabajo ordinario, pero sus registros, vínculos y eventos permanecen para auditoría. La eliminación física no se utiliza para ocultar decisiones históricas.

En el cierre histórico de este sprint la exactitud visible era estructural y contractual. Desde Sprint 4, la conciliación de cantidades e importes se consulta en el expediente ETL correspondiente. El asistente no presenta un acordeón de “validaciones futuras”: muestra únicamente sus cuatro comprobaciones estructurales y remite la evidencia cuantitativa al expediente materializado. El juicio formal de expertos se documenta como método de evaluación de la tesis, no como una acción pendiente del asistente, y las métricas predictivas permanecen fuera del alcance.

En móvil, cada sección es un acordeón y las acciones de decisión permanecen visibles sin cubrir contenido. En escritorio amplio, el resumen puede convivir con un panel de explicación, pero no habrá chat abierto en Sprint 3. El foco, mensajes y confirmaciones cumplen SPR-02-04.

## 8. Seguridad y auditoría

- `copilot.proposals.read`, `generate` y `review` separan consulta, consumo de proveedor y decisión.
- FastAPI obtiene la única configuración LLM activa, verifica una prueba exitosa y recupera su secreto cifrado; React no lee credenciales.
- La URL se valida según el catálogo del proveedor del Sprint 2; no se aceptan destinos arbitrarios ni redirecciones.
- El paquete se construye en backend. El cliente no puede inyectar metadatos ni instrucciones del sistema.
- La solicitud de negocio se delimita, normaliza y limita; nunca se concatena con instrucciones privilegiadas ni se interpreta como SQL.
- Se limita tamaño, duración, reintentos y respuesta. La asesoría puede solicitar una
  única corrección al mismo proveedor cuando la salida no conserva el objetivo o la
  comprobación local detecta referencias, tipos o rutas sin respaldo. El feedback es
  estructurado y no amplía el contexto autorizado. No cambia de proveedor en silencio,
  no repite indefinidamente ni crea propuestas o ETL durante ese reintento; si no se
  resuelve, conserva el fallo y comunica la limitación. Las operaciones de escritura o
  ejecución no se reintentan automáticamente de modo que dupliquen sus efectos.
- Eventos: `copilot.proposal.generate`, `provider_failed`, `validation_failed`, `ready_for_review`, `approve` y `reject`.
- La auditoría contiene ids, hashes, estado, proveedor/modelo y códigos de validación; nunca clave, prompt completo, cabeceras ni razonamiento del modelo.

## 9. Criterios de aceptación verificables

- [ ] Sólo se puede generar con instantánea válida, solicitud de negocio confirmada, alcance derivado, permiso y configuración LLM activa/probada.
- [ ] Sugerir, reformular y analizar reciben estructura real permitida y consentimiento vinculado a configuración, proveedor, destino y modelo; sin consentimiento coincidente no hay envío.
- [ ] Las sugerencias muestran evidencia y límites; su adopción es explícita y no sobrescribe el objetivo automáticamente. Una sugerencia sin respaldo no puede adoptarse como viable.
- [ ] La revisión previa comprueba tipos, referencias y rutas FK dirigidas; no confunde importes textuales, costos desconectados, fecha de modificación ni pedidos con evidencia suficiente de facturación.
- [ ] Cambiar fuente, instantánea, objetivo, preguntas o periodicidad invalida la revisión; una respuesta tardía de otro contexto no la reemplaza. Recuperar un borrador no recupera consentimiento.
- [ ] Crear una propuesta exige la revisión persistida del mismo actor y entrada; los requisitos de margen o razón requieren resultados derivados reales, no sólo operandos disponibles.
- [ ] La revisión distingue respaldo estructural de calidad de filas, historia de costos, conciliación y utilidad comercial, que conservan sus controles posteriores.
- [ ] El feedback correctivo permite como máximo un reintento con el mismo proveedor,
  sin relajar el contrato ni introducir otra fuente. Si analizar modifica el objetivo
  original y no lo conserva tras ese intento, se rechaza en lugar de guardar una
  evaluación de otra necesidad.
- [ ] Etiquetas como neto, bruto, impuesto incluido o costo histórico no se acreditan
  sólo porque un nombre de columna parezca compatible; la necesidad y su explicación
  exponen el límite semántico cuando los metadatos no lo demuestran.
- [ ] La compatibilidad de tipo no se presenta como equivalencia semántica: los roles
  conocidos de precio, costo, tasa, cantidad e importe deben corresponder al cálculo.
  Las evaluaciones de una versión anterior no habilitan generación con reglas nuevas.
- [ ] Un analista BI puede completar el recorrido guiado sin seleccionar manualmente tablas, escribir identificadores ni programar SQL.
- [ ] El descubrimiento por bloques deriva un alcance reproducible usando únicamente objetos y PK/FK existentes.
- [ ] El proveedor recibe exclusivamente el paquete de metadatos permitido y nunca filas, secretos o usuarios.
- [ ] La respuesta se acepta únicamente si cumple el contrato JSON versionado.
- [ ] Una referencia inventada produce error determinístico y bloquea aprobación.
- [ ] Una propuesta válida presenta hecho, granularidad, dimensiones, medidas, al menos un KPI y plan ETL declarativo.
- [ ] Las dimensiones son propuestas por el LLM desde los metadatos; ninguna dimensión predefinida se envía desde el paso de necesidad y ninguna referencia sin fuente verificable puede aprobarse.
- [ ] Ninguna propuesta contiene SQL o código ejecutable utilizable por el sistema.
- [ ] Sólo `ready_for_review` puede aprobarse y las advertencias requieren confirmación.
- [ ] La aprobación vuelve a ejecutar las reglas vigentes y bloquea inconsistencias semánticas antiguas.
- [ ] El analista puede excluir o reasignar un KPI a una medida compatible, retirar aprobaciones y descartar versiones con motivo trazable.
- [ ] Verificar evidencia es una operación de sólo lectura: distingue errores actuales de diferencias de reproducción, no cambia estados y permite restaurar de forma auditada una aprobación retirada por un falso positivo anterior.
- [ ] Un perfil autorizado puede crear, editar, habilitar y retirar preguntas por dominio, así como administrar varias periodicidades soportadas, sin convertir esas guías en tablas o dimensiones predefinidas.
- [ ] Rechazar requiere comentario y un nuevo intento crea otro registro sin sobrescribir el anterior.
- [ ] El historial permite abrir cualquier resultado persistido, distingue proveedor/modelo y no vuelve a invocar el LLM al seleccionarlo.
- [ ] La plataforma reconstruye la propuesta seleccionada sin invocar al LLM y muestra integridad, referencias, calidad, coherencia y comparación de huellas sin tratar la evolución del motor como corrupción demostrada.
- [ ] La interfaz muestra sólo la evidencia estructural disponible; la conciliación OLTP–datamart se consulta en el expediente ETL y no existe un bloque ambiguo de “validaciones que se habilitarán posteriormente”.
- [ ] La interfaz diferencia claramente contenido propuesto por IA, resultado del validador y decisión humana.
- [ ] El LLM interpreta nombres técnicos en inglés y genera conceptos comprensibles en español para la fuente activa.
- [ ] La explicación relaciona cada concepto con identificadores técnicos consultables y cualquier tabla o columna inventada queda descartada y auditada.
- [ ] No existe una tabla de traducciones codificada sólo para AdventureWorks como sustituto de la interpretación dinámica.
- [ ] La documentación declara que el futuro SQL será generado por el motor determinístico del Sprint 4 y no por el LLM ni por un programador durante cada análisis.
- [ ] Errores, cuotas y tiempos agotados no exponen secretos ni dejan estados engañosos.
- [ ] Todo el flujo se prueba con proveedor simulado en CI y al menos una prueba manual real documentada.

## 10. Plan de pruebas y evidencia

- Unitarias: solicitud de negocio, partición estable, descubrimiento semántico, combinación de candidatos, esquema JSON, referencias inventadas, joins, tipos numéricos, granularidad, fórmulas KPI y operaciones ETL.
- Integración: estados, inmutabilidad, aprobación, rechazo, verificación de evidencia y auditoría.
- Adaptadores: Gemini, Qwen Cloud y Ollama mediante respuestas simuladas; Gemini y Ollama mediante pruebas reales controladas.
- Seguridad: 401/403, inyección de metadatos, URL no permitida, tamaño excesivo y sanitización de errores.
- Frontend: recorrido no técnico, prerrequisitos, secciones, advertencias, selección de versiones persistidas, validación visible, confirmaciones, estados y responsive.
- Evidencia académica: hash de entrada, versión de prompt/contrato, proveedor/modelo, propuesta validada y decisión humana.
- Revisión previa: respuestas simuladas con columnas inexistentes, tipos incompatibles,
  tablas desconectadas, FK inversa, necesidad fuera de alcance, cambio de destino sin
  consentimiento y respuesta tardía; contraste local con ambas instantáneas y ensayo
  real autorizado documentado por separado. La aprobación de pruebas simuladas no
  sustituye el ensayo real ni acredita cualquier combinación de proveedor y fuente.

## 11. Riesgos, dependencias y decisiones

- `qwen2.5:3b` prioriza agilidad, pero puede producir propuestas menos completas: el contrato y el validador deben funcionar igual con cualquier proveedor aprobado.
- El perfil local debe reservar 4096 tokens de contexto y presupuestos de salida suficientes para la interpretación semántica y la propuesta compacta. Una respuesta que alcance el límite sin cerrar el JSON se registra como fallo del proveedor y nunca se acepta parcialmente.
- El contexto local es limitado: FastAPI procesa bloques con presupuesto estable y conserva trazabilidad; esto puede requerir varias llamadas y debe mostrar progreso y consumo.
- Una salida válida sintácticamente puede ser inadecuada para negocio: por eso la aprobación humana no se reemplaza por validación automática.
- El gerente aporta la necesidad y los criterios de utilidad; el analista BI revisa la propuesta. Los validadores cubren la integridad estructural y el explorador de sólo lectura permite comprobar el origen sin escribir SQL.
- La interpretación dinámica puede asignar etiquetas imprecisas aunque las referencias existan: por eso cada concepto muestra confianza, explicación y origen, y requiere aprobación humana.
- Depende de SPR-03-01, SPR-03-04 y ADR 0003.

## 12. Resultado de implementación

### Ampliación: necesidades fundamentadas, 3 de octubre de 2026

El paso Necesidad ofrece tres operaciones separadas: proponer necesidades desde una
instantánea, mejorar un objetivo escrito y analizar su viabilidad. Las tres usan el
adaptador LLM común, sin personalizaciones por base de datos. Antes de cada revisión,
la interfaz informa proveedor/modelo y exige consentimiento para transmitir únicamente
objetivo y metadatos estructurales. Una huella vincula la autorización a configuración,
proveedor, destino y modelo; un cambio de destino invalida esa autorización.

La IA recibe una lista permitida de tablas, columnas, tipos, claves y relaciones, no
sólo un hash. Propone una descomposición de la intención en requisitos y declara límites semánticos.
El servidor comprueba existencia, tipos de operandos, identificadores y rutas FK
dirigidas. Una relación inversa no acredita por sí sola que se preserve la granularidad.
Una columna de texto no acredita un importe; una tabla de compras o pedidos no prueba
facturación. Los alias generales españoles e ingleses ayudan al descubrimiento, pero
no sustituyen la interpretación supervisada ni demuestran equivalencia de negocio.

Las sugerencias muestran evidencia y límites, nunca sustituyen automáticamente el texto
del analista y no pueden adoptarse cuando sus requisitos declarados carecen de respaldo.
Después de elegir una, se exige validar su texto definitivo. Las respuestas tardías se
descartan si cambian fuente, instantánea, texto, preguntas, período o consentimiento.

La revisión conjunta IA/reglas se guarda en `app.business_need_reviews` (migración
`20261003_19`), vinculada al actor, texto, preguntas, período e instantánea. Crear una
propuesta exige una revisión persistida coincidente; no basta presentar una huella de
la comprobación heurística anterior. Los límites requieren confirmación explícita y
se trasladan a la propuesta. Las propuestas y ejecuciones históricas no se modifican.

El ensayo real detectó que Claude podía presentar `UnitPrice` como costo unitario:
el tipo numérico y la relación eran correctos, pero el significado no. Se añadió
validación de roles semánticos y operandos en español/inglés; una contradicción
conocida queda no disponible y un nombre desconocido permanece ambiguo. La versión
`need-review-2` obliga a revalidar evaluaciones previas sin borrarlas. También se
separó en las instrucciones y el feedback la agrupación temporal de la derivación
aritmética: una fecha no puede ser operando numérico de una «evolución de ventas».

**Límite:** este análisis acredita respaldo estructural condicionado, no cobertura
exhaustiva demostrada del lenguaje natural, existencia de filas, corrección de valores,
historia de costos ni conciliación. Se conservan los controles posteriores y aprobación.
Las nuevas rutas están verificadas con proveedores simulados; su ensayo real con Claude
fue autorizado y se documenta en la auditoría del 3 de octubre. Los intentos iniciales
de WideWorldImporters no se califican como éxito: las sugerencias y la reformulación
quedaron bloqueadas por evidencia relacional insuficiente, y el análisis que modificó
el objetivo fue rechazado. Se añadió feedback acotado para corregir con el mismo
proveedor sin debilitar las reglas. Una repetición produjo dos opciones estructuralmente
usables en AdventureWorks, aunque sus explicaciones contenían afirmaciones incorrectas
sobre estados de pedidos. WideWorldImporters produjo una opción usable y otra bloqueada;
su análisis añadió una medida derivada temporal duplicada con una fecha como operando,
que fue rechazada por las reglas. Estas incidencias se conservan incluso después del
cierre funcional supervisado: demuestran utilidad y bloqueo seguro, pero no corrección
semántica exhaustiva del texto del proveedor. La clausura del ensayo y sus resultados se conservan en la auditoría,
separados de esas incidencias y de los ciclos ETL anteriores; no se atribuye un nuevo ETL
a estas pruebas de necesidades.

En la repetición correctiva de WideWorldImporters, una necesidad mensual de importe
registrado en líneas de factura y trazabilidad obtuvo seis requisitos directos, dos
derivables, cuatro límites de interpretación y ninguno
no disponible. Los límites distinguieron composición del importe, fecha de factura
frente a cobro, ausencia de filtrado implícito de notas de crédito y facturas frente
a pedidos. Después de aceptarlos explícitamente se habilitó generar; no se creó una
propuesta ni se ejecutó ETL. La prueba negativa de clima identificó la ausencia de
datos climáticos externos y no confundió sensores frigoríficos o de vehículos con
esa fuente: sin aceptar un alcance parcial, la generación permaneció deshabilitada.

En AdventureWorks la reformulación final introdujo atributos de producto con capacidad
`other`, sin validador implementado; permaneció no utilizable después de dos intentos.
Se conservó el objetivo original: «Comparar por mes el importe registrado y la cantidad
de unidades de las líneas de venta por producto, conservando su identificador de pedido».
Con la pregunta de desempeño por producto y características y periodicidad mensual, la
revisión obtuvo once directos, uno derivable, cinco ambiguos o advertencias y cero no
disponibles. Tras aceptar explícitamente los cinco límites se habilitó generar, sin
crear propuesta. El cierre es **aceptación funcional supervisada de la puerta previa**
en ambos escenarios, no aceptación de toda reformulación ni validación universal del
lenguaje natural. No se generaron propuestas ni se repitieron ETL en este ensayo.

### Evidencia histórica anterior a esta ampliación

Implementada localmente y pendiente de aceptación de las autoras antes del PR. Con `qwen2.5:3b` en Ollama se comprobó sobre la instantánea real de AdventureWorks la interpretación de cuatro conceptos, la generación de decisiones compactas y la expansión determinística. La prueba correctiva produjo la versión 31 en estado `ready_for_review`, con cero errores y cero advertencias: `LineTotal` y `OrderQty` como medidas y cuatro dimensiones con referencias verificadas. Los cuatro controles de evidencia resultaron satisfactorios. La revisión vigente retiró del paso 1 toda selección de dimensiones; los nuevos intentos dependen de la propuesta del LLM y de la validación posterior.

La primera configuración `gemini-2.5-flash` fue rechazada por el catálogo vigente del proyecto. Sin cambiar código ni archivos del entorno, se parametrizó `gemini-3.6-flash` con razonamiento mínimo y se repitió la prueba. Gemini produjo una propuesta real `ready_for_review`, válida y persistida, con cinco conceptos semánticos, cuatro dimensiones y dos KPI. Las versiones de Ollama y Gemini pueden abrirse desde **Versiones generadas** sin consumir nuevamente al proveedor, para que el analista compare, seleccione y decida cuál revisar. La evidencia definitiva de SHA, aceptación y CI se incorporará al cerrar el PR.

La verificación visible se ejecutó sobre las propuestas reales de Ollama y Gemini. En ambas coincidieron integridad de la instantánea, referencias, validación recalculada y huella de reejecución. El resultado no se interpreta como conciliación cuantitativa: las comparaciones OLTP--datamart permanecen correctamente señaladas como pendientes de Sprint 4.
