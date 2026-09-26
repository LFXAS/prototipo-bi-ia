# SPR-03-02: propuesta BI asistida por IA y supervisada

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
2. La pantalla obtiene del backend preguntas orientadoras y periodicidades compatibles. El analista escribe el objetivo específico en español; React no mantiene un modelo dimensional fijo de AdventureWorks.
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
15. Una persona autorizada selecciona la versión que considera adecuada y la aprueba o rechaza con comentario. La decisión queda auditada y el registro no se sobrescribe.

Si la primera propuesta no satisface la necesidad, el analista no queda obligado a aceptarla. Puede volver al objetivo, ajustar preguntas y dimensiones, descartar conceptos semánticos no pertinentes y generar una nueva versión con IA; o puede personalizar las decisiones verificadas sin consumir nuevamente el proveedor. La versión anterior se conserva. No se admiten SQL, columnas libres ni relaciones manuales: todo ajuste vuelve a pasar por el validador determinístico.

No existe una lista codificada de tablas AdventureWorks que se presente como interpretación de IA. La misma secuencia debe operar sobre otra base relacional de ventas cuando se implemente su conector: cambian los metadatos y el mapa producido, no el contrato de la experiencia. AdventureWorks sigue siendo la única fuente exigida para las pruebas funcionales de esta investigación.

La implementación registra `connector_code` y `domain_code`. El contrato de metadatos es neutral al motor y el backend despacha la lectura mediante un registro de adaptadores; SQL Server es el único adaptador habilitado. Las preguntas de negocio son configurables, mientras que las reglas semánticas, destinos admitidos y validadores pertenecen a un perfil de dominio. `ventas` es el único perfil habilitado y validado. Un motor o dominio futuro debe incorporar y probar su adaptador o perfil antes de aparecer como opción disponible.

### 3.3 Estados

| Estado | Significado | Transiciones permitidas |
|---|---|---|
| `generating` | Solicitud en curso. | `validation_failed`, `ready_for_review`, `provider_failed`. |
| `provider_failed` | Proveedor inaccesible, tiempo agotado o respuesta no utilizable. | Nueva propuesta. |
| `validation_failed` | Contrato o reglas incumplidos. | Nueva propuesta. |
| `ready_for_review` | Sin errores determinísticos; puede contener advertencias. | `approved`, `rejected`, nueva propuesta. |
| `approved` | Decisión humana favorable; sigue sujeta a revalidación antes del ETL. | `invalidated`. |
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

La solicitud de creación admite `metadata_snapshot_id`, `business_goal` de 20 a 500 caracteres, uno o más códigos de preguntas aprobadas y una periodicidad inicial `month`. El texto libre complementa el objetivo, pero no amplía el dominio ni habilita operaciones. Una petición de inventario, compras, finanzas u otro dominio se rechaza antes de consumir el proveedor con una explicación de alcance. Los conceptos o dimensiones no se vinculan a tablas predefinidas: se descubren desde los metadatos.

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

Estados obligatorios: prerrequisito faltante, generando, proveedor inaccesible, validación fallida, listo para revisar, aprobado y rechazado.

Debajo del recorrido se presenta **Versiones generadas** con paginación y filtro de estado. El filtro inicial es **Lista para revisar** para priorizar trabajo pendiente; el analista puede cambiar a aprobadas, rechazadas, con problemas o todas. Cada fila identifica el proveedor y modelo usados, señala si deriva de otra versión y permite **Abrir resultado**. La versión elegida repone su necesidad, conceptos, propuesta, validación y decisión en las mismas vistas del asistente. Esta consulta no llama nuevamente al LLM y permite preparar previamente una evidencia local lenta —por ejemplo Qwen en CPU— y compararla con una ejecución cloud rápida durante la sustentación. La aplicación no elige automáticamente al “mejor” proveedor: la selección y aprobación pertenecen al analista BI.

La versión seleccionada presenta además **Validación estructural de la propuesta - Sprint 3**. La acción **Verificar evidencia** recalcula la integridad de metadatos, las referencias, el contrato y la validación, y reconstruye la propuesta desde las decisiones IA guardadas. La huella reconstruida debe coincidir con la persistida. Esta reejecución no llama al LLM: la reproducibilidad exigida corresponde al artefacto aprobado y al motor determinístico, no a obtener dos textos idénticos de un modelo probabilístico.

Una versión aprobada cambia a **Aprobación retirada** sólo cuando la verificación detecta un error bloqueante vigente. Una diferencia de huella causada exclusivamente por una versión anterior del motor se muestra como compatibilidad histórica y no invalida por sí sola el contrato. Si una aprobación fue retirada por ese falso positivo, una persona revisora puede restaurarla con justificación y confirmación de advertencias. El analista también puede retirarla indicando el motivo. Los intentos no aprobados pueden marcarse **Descartados**; no aparecen en el trabajo ordinario, pero sus registros, vínculos y eventos permanecen para auditoría. La eliminación física no se utiliza para ocultar decisiones históricas.

En este sprint la exactitud visible es estructural y contractual. La pantalla declara como pendientes la conciliación de cantidades e importes entre OLTP y datamart, el juicio formal de expertos y MAPE/RMSE. Sprint 4 ampliará el mismo expediente con consultas de referencia cuantitativas; no se presentará la validación estructural como si ya demostrara igualdad de cifras.

En móvil, cada sección es un acordeón y las acciones de decisión permanecen visibles sin cubrir contenido. En escritorio amplio, el resumen puede convivir con un panel de explicación, pero no habrá chat abierto en Sprint 3. El foco, mensajes y confirmaciones cumplen SPR-02-04.

## 8. Seguridad y auditoría

- `copilot.proposals.read`, `generate` y `review` separan consulta, consumo de proveedor y decisión.
- FastAPI obtiene la única configuración LLM activa, verifica una prueba exitosa y recupera su secreto cifrado; React no lee credenciales.
- La URL se valida según el catálogo del proveedor del Sprint 2; no se aceptan destinos arbitrarios ni redirecciones.
- El paquete se construye en backend. El cliente no puede inyectar metadatos ni instrucciones del sistema.
- La solicitud de negocio se delimita, normaliza y limita; nunca se concatena con instrucciones privilegiadas ni se interpreta como SQL.
- Se limita tamaño, duración, reintentos y respuesta. No se reintenta automáticamente una operación que pueda duplicar consumo sin idempotencia.
- Eventos: `copilot.proposal.generate`, `provider_failed`, `validation_failed`, `ready_for_review`, `approve` y `reject`.
- La auditoría contiene ids, hashes, estado, proveedor/modelo y códigos de validación; nunca clave, prompt completo, cabeceras ni razonamiento del modelo.

## 9. Criterios de aceptación verificables

- [ ] Sólo se puede generar con instantánea válida, solicitud de negocio confirmada, alcance derivado, permiso y configuración LLM activa/probada.
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
- [ ] La verificación distingue un error actual de una diferencia histórica entre versiones del motor y permite restaurar una aprobación retirada por compatibilidad sin borrar evidencia.
- [ ] Un perfil autorizado puede crear, editar, habilitar y retirar preguntas por dominio, así como administrar varias periodicidades soportadas, sin convertir esas guías en tablas o dimensiones predefinidas.
- [ ] Rechazar requiere comentario y un nuevo intento crea otro registro sin sobrescribir el anterior.
- [ ] El historial permite abrir cualquier resultado persistido, distingue proveedor/modelo y no vuelve a invocar el LLM al seleccionarlo.
- [ ] La plataforma reejecuta la propuesta seleccionada sin invocar al LLM y muestra integridad, referencias, calidad, coherencia y coincidencia de huellas.
- [ ] La interfaz distingue la evidencia disponible de las conciliaciones OLTP–datamart, juicio de expertos y métricas predictivas todavía pendientes.
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

## 11. Riesgos, dependencias y decisiones

- `qwen2.5:3b` prioriza agilidad, pero puede producir propuestas menos completas: el contrato y el validador deben funcionar igual con cualquier proveedor aprobado.
- El perfil local debe reservar 4096 tokens de contexto y presupuestos de salida suficientes para la interpretación semántica y la propuesta compacta. Una respuesta que alcance el límite sin cerrar el JSON se registra como fallo del proveedor y nunca se acepta parcialmente.
- El contexto local es limitado: FastAPI procesa bloques con presupuesto estable y conserva trazabilidad; esto puede requerir varias llamadas y debe mostrar progreso y consumo.
- Una salida válida sintácticamente puede ser inadecuada para negocio: por eso la aprobación humana no se reemplaza por validación automática.
- El gerente aporta la necesidad y los criterios de utilidad; el analista BI revisa la propuesta. Los validadores cubren la integridad estructural y el explorador de sólo lectura permite comprobar el origen sin escribir SQL.
- La interpretación dinámica puede asignar etiquetas imprecisas aunque las referencias existan: por eso cada concepto muestra confianza, explicación y origen, y requiere aprobación humana.
- Depende de SPR-03-01, SPR-03-04 y ADR 0003.

## 12. Resultado de implementación

Implementada localmente y pendiente de aceptación de las autoras antes del PR. Con `qwen2.5:3b` en Ollama se comprobó sobre la instantánea real de AdventureWorks la interpretación de cuatro conceptos, la generación de decisiones compactas y la expansión determinística. La prueba correctiva produjo la versión 31 en estado `ready_for_review`, con cero errores y cero advertencias: `LineTotal` y `OrderQty` como medidas y cuatro dimensiones con referencias verificadas. Los cuatro controles de evidencia resultaron satisfactorios. La revisión vigente retiró del paso 1 toda selección de dimensiones; los nuevos intentos dependen de la propuesta del LLM y de la validación posterior.

La primera configuración `gemini-2.5-flash` fue rechazada por el catálogo vigente del proyecto. Sin cambiar código ni archivos del entorno, se parametrizó `gemini-3.6-flash` con razonamiento mínimo y se repitió la prueba. Gemini produjo una propuesta real `ready_for_review`, válida y persistida, con cinco conceptos semánticos, cuatro dimensiones y dos KPI. Las versiones de Ollama y Gemini pueden abrirse desde **Versiones generadas** sin consumir nuevamente al proveedor, para que el analista compare, seleccione y decida cuál revisar. La evidencia definitiva de SHA, aceptación y CI se incorporará al cerrar el PR.

La verificación visible se ejecutó sobre las propuestas reales de Ollama y Gemini. En ambas coincidieron integridad de la instantánea, referencias, validación recalculada y huella de reejecución. El resultado no se interpreta como conciliación cuantitativa: las comparaciones OLTP--datamart permanecen correctamente señaladas como pendientes de Sprint 4.
