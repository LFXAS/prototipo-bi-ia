# SPR-03-02: propuesta BI asistida por IA y supervisada

- Estado: **borrador para revisión y aprobación**.
- Pertenece a: [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md).
- Fecha de creación: 2026-09-14.
- Rama prevista de implementación: `feature/sprint-03-metadata-copilot`.
- PR de implementación: pendiente.

## 1. Problema y objetivo

Una instantánea técnica no determina por sí sola qué tabla representa el proceso de ventas, cuál debe ser la granularidad del hecho, qué dimensiones son pertinentes ni qué KPIs son calculables. El proyecto necesita demostrar la asistencia de IA sin delegarle la ejecución ni aceptar referencias inventadas.

El objetivo es integrar la configuración LLM activa del Sprint 2 para convertir un alcance de metadatos aprobado en una propuesta BI estructurada, validarla con reglas determinísticas y someterla a una decisión humana explícita. La propuesta aprobada será una entrada versionada del Sprint 4, no una ejecución.

## 2. Alcance y exclusiones

### Incluido

- Selección humana de un conjunto de tablas desde una instantánea de AdventureWorks.
- Inclusión automática y visible de tablas/columnas requeridas por claves declaradas.
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

## 3. Actores, flujo y estados

### 3.1 Prerrequisitos

- Sesión válida y permisos correspondientes.
- Instantánea de metadatos vigente.
- Alcance con al menos una tabla y relaciones suficientes para justificar ventas.
- Una sola configuración LLM activa, cuya última prueba sea exitosa.

Si falta un prerrequisito, la interfaz explica el paso necesario y no envía una solicitud al proveedor.

### 3.2 Flujo principal

1. El analista abre una instantánea y selecciona tablas candidatas.
2. La aplicación muestra las relaciones y añade dependencias técnicas necesarias; la persona confirma el alcance final.
3. FastAPI crea un paquete canónico y calcula `input_hash`.
4. FastAPI recupera la configuración activa y su credencial por referencia desde el entorno.
5. El adaptador solicita una única propuesta con tiempo máximo y límites de salida.
6. La respuesta se analiza contra el esquema JSON. Si no cumple, queda `validation_failed`.
7. Los validadores comparan cada referencia con la instantánea y producen errores, advertencias e información.
8. Sin errores, la propuesta queda `ready_for_review`.
9. El revisor puede aprobar, rechazar con motivo o solicitar otra versión con observaciones.
10. Al aprobar, cualquier propuesta aprobada anterior del mismo análisis pasa a `superseded` dentro de la misma transacción.

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

### 4.2 Contrato de entrada al LLM

```json
{
  "request_version": 1,
  "language": "es",
  "task": "propose_sales_dimensional_model",
  "source": {"code": "adventureworks", "snapshot_hash": "..."},
  "scope": {
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
    "allowed_etl_operations": ["extract", "join", "filter", "derive", "aggregate", "load"]
  }
}
```

El paquete incluye únicamente objetos seleccionados y dependencias confirmadas. Si excede el presupuesto del proveedor, FastAPI no lo trunca silenciosamente: solicita reducir el alcance o aplica una compactación determinística que conserva nombres, tipos, PK y FK e informa el cambio.

### 4.3 Contrato de salida del LLM

```json
{
  "contract_version": 1,
  "domain": "ventas",
  "summary": "Modelo dimensional propuesto para analizar ventas.",
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

## 5. Validaciones determinísticas

### Errores que impiden revisión/aprobación

- Contrato JSON inválido, campos requeridos ausentes o versión desconocida.
- Tabla, columna, PK o FK inexistente en la instantánea referenciada.
- Tabla usada fuera del alcance confirmado.
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
| `POST /api/v1/copilot/proposals` | `copilot.proposals.generate` | Crea un intento a partir de instantánea y tablas seleccionadas. |
| `GET /api/v1/copilot/proposals` | `copilot.proposals.read` | Lista paginada por estado, fecha y snapshot. |
| `GET /api/v1/copilot/proposals/{id}` | `copilot.proposals.read` | Propuesta, validaciones, procedencia y revisión. |
| `POST /api/v1/copilot/proposals/{id}/approve` | `copilot.proposals.review` | Aprueba sólo `ready_for_review`, con confirmación de advertencias. |
| `POST /api/v1/copilot/proposals/{id}/reject` | `copilot.proposals.review` | Rechaza con comentario obligatorio. |
| `POST /api/v1/copilot/proposals/{id}/regenerate` | `copilot.proposals.generate` | Genera otra versión con observación humana y referencia al padre. |

Las operaciones de revisión son idempotentes por estado: repetir una aprobación no duplica eventos; intentar cambiar una decisión final devuelve 409.

## 7. Interfaz y experiencia

La ruta **IA > Propuesta BI** usa un flujo guiado:

1. Fuente e instantánea.
2. Alcance de tablas.
3. Generación.
4. Validación.
5. Revisión humana.

La propuesta se presenta por secciones: granularidad, hecho, dimensiones, relaciones, medidas, KPIs, plan ETL, reglas de calidad, supuestos y advertencias. Nunca se muestra como un bloque JSON obligatorio para la persona; el JSON puede descargarse como evidencia técnica autorizada.

Estados obligatorios: prerrequisito faltante, listo para generar, generando, proveedor agotado/inaccesible, respuesta inválida, errores de validación, listo para revisar, aprobado, rechazado y sustituido.

En móvil, cada sección es un acordeón y las acciones de decisión permanecen visibles sin cubrir contenido. En escritorio amplio, el resumen puede convivir con un panel de explicación, pero no habrá chat abierto en Sprint 3. El foco, mensajes y confirmaciones cumplen SPR-02-04.

## 8. Seguridad y auditoría

- `copilot.proposals.read`, `generate` y `review` separan consulta, consumo de proveedor y decisión.
- FastAPI obtiene la única configuración LLM activa y verifica una prueba exitosa; React no elige credenciales.
- La URL se valida según el catálogo del proveedor del Sprint 2; no se aceptan destinos arbitrarios ni redirecciones.
- El paquete se construye en backend. El cliente no puede inyectar metadatos ni instrucciones del sistema.
- Se limita tamaño, duración, reintentos y respuesta. No se reintenta automáticamente una operación que pueda duplicar consumo sin idempotencia.
- Eventos: `copilot.proposal.generate`, `provider_failed`, `validation_failed`, `ready_for_review`, `approve`, `reject`, `regenerate` y `supersede`.
- La auditoría contiene ids, hashes, estado, proveedor/modelo y códigos de validación; nunca clave, prompt completo, cabeceras ni razonamiento del modelo.

## 9. Criterios de aceptación verificables

- [ ] Sólo se puede generar con instantánea válida, alcance confirmado, permiso y configuración LLM activa/probada.
- [ ] El proveedor recibe exclusivamente el paquete de metadatos permitido y nunca filas, secretos o usuarios.
- [ ] La respuesta se acepta únicamente si cumple el contrato JSON versionado.
- [ ] Una referencia inventada produce error determinístico y bloquea aprobación.
- [ ] Una propuesta válida presenta hecho, granularidad, dimensiones, medidas, al menos un KPI y plan ETL declarativo.
- [ ] Ninguna propuesta contiene SQL o código ejecutable utilizable por el sistema.
- [ ] Sólo `ready_for_review` puede aprobarse y las advertencias requieren confirmación.
- [ ] Rechazar requiere comentario; regenerar crea otra versión y no sobrescribe la anterior.
- [ ] Una sola propuesta queda aprobada por análisis y la sustitución es explícita y transaccional.
- [ ] La interfaz diferencia claramente contenido propuesto por IA, resultado del validador y decisión humana.
- [ ] Errores, cuotas y tiempos agotados no exponen secretos ni dejan estados engañosos.
- [ ] Todo el flujo se prueba con proveedor simulado en CI y al menos una prueba manual real documentada.

## 10. Plan de pruebas y evidencia

- Unitarias: esquema JSON, tablas/columnas inventadas, joins, tipos numéricos, granularidad, fórmulas KPI y operaciones ETL.
- Integración: estados, inmutabilidad, versiones, aprobación única, transacciones y auditoría.
- Adaptadores: Gemini, Qwen Cloud y Ollama mediante respuestas simuladas; Ollama real como alternativa local.
- Seguridad: 401/403, inyección de metadatos, URL no permitida, tamaño excesivo y sanitización de errores.
- Frontend: prerrequisitos, secciones, advertencias, confirmaciones, estados y responsive.
- Evidencia académica: hash de entrada, versión de prompt/contrato, proveedor/modelo, propuesta validada y decisión humana.

## 11. Riesgos, dependencias y decisiones

- `qwen2.5:3b` prioriza agilidad, pero puede producir propuestas menos completas: el contrato y el validador deben funcionar igual con cualquier proveedor aprobado.
- El contexto local es limitado: el alcance de tablas es obligatorio y visible.
- Una salida válida sintácticamente puede ser inadecuada para negocio: por eso la aprobación humana no se reemplaza por validación automática.
- Depende de SPR-03-01, configuración LLM de Sprint 2 y ADR 0003.

## 12. Resultado de implementación

Pendiente. Al cerrar el PR se documentarán proveedor real probado, SHA, casos ejecutados, resultado, desviaciones y estado final.
