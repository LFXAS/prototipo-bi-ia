# SPR-04-04: limpieza, transformaciones y columnas calculadas controladas

- Estado: **carga, limpieza, derivaciones aritméticas, control de calidad e interpretación supervisada implementados**.
- Dependencias: `SPR-04-01`, propuesta de ventas aprobada e instantánea vigente.
- Propósito: convertir datos operacionales en un datamart analíticamente utilizable mediante reglas reproducibles, sin SQL ni fórmulas libres producidas por la IA.

## 1. Decisión funcional

Materializar no significa copiar tablas. Antes de cargar el esquema `mart`, FastAPI perfila las columnas incluidas, compila un plan de limpieza y transformación desde el contrato aprobado y muestra al analista qué regla se aplicará y por qué. La IA puede sugerir la necesidad analítica y la intención de una derivación; el ejecutor sólo acepta operaciones tipadas, versionadas y probadas por el perfil de ventas.

La primera versión implementará carga completa desde destino vacío o reemplazable de forma transaccional. Las cargas incrementales, CDC y dimensiones lentamente cambiantes complejas permanecen fuera del alcance.

## 2. Catálogo inicial de transformaciones

| Operación tipada | Aplicación | Control bloqueante |
|---|---|---|
| `cast` | Convierte fechas, enteros, decimales y texto a tipos canónicos del datamart. | La conversión debe ser compatible con el tipo introspectado; los fallos se cuentan y bloquean según tolerancia. |
| `trim` | Elimina espacios laterales de atributos descriptivos. | No cambia claves ni valores nulos. |
| `null_policy` | Rechaza claves obligatorias nulas y permite valores descriptivos desconocidos documentados. | Nunca reemplaza importes, cantidades o claves con cero de forma silenciosa. |
| `deduplicate` | Conserva una fila por clave de dimensión o por grano del hecho. | La clave y el criterio de selección deben estar declarados; no se deduplica por una heurística del LLM. |
| `date_parts` | Deriva fecha, año, trimestre, mes y día desde una fecha de venta validada. | Requiere columna temporal verificable. |
| `arithmetic` | Calcula una medida mediante una receta conocida, por ejemplo cantidad por precio por uno menos descuento. | Sólo referencias numéricas existentes y operadores permitidos; división por cero produce nulo y evidencia. |
| `surrogate_key` | Genera claves internas del datamart y conserva la clave de negocio de origen. | La relación con la clave natural debe quedar trazable. |
| `normalize_sign` | Conserva o normaliza el signo cuando la regla de negocio lo declara. | No convierte ventas negativas o devoluciones sin una regla del dominio. |
| `localize_label` | Crea una etiqueta española para valores categóricos no sensibles cuando el idioma de origen no sea español. | Conserva el valor original, exige mapeo revisado y no procesa identificadores, PII, texto libre ni columnas de alta cardinalidad. |

## 3. Columnas calculadas

Las columnas calculadas no se escriben como expresiones libres. El constructor recibe una receta declarativa con código, entradas, tipo de salida y versión. Para ventas podrá producir, cuando la fuente lo sustente:

- `fecha_key`, `anio`, `trimestre`, `mes` y `dia` desde la fecha transaccional;
- `importe_linea` desde una columna monetaria validada o desde `cantidad * precio_unitario * (1 - descuento)`;
- `cantidad_vendida` mediante conversión numérica controlada;
- claves de negocio de pedido, producto, cliente y territorio preservadas para conciliación;
- claves sustitutas de dimensiones generadas por PostgreSQL;
- indicadores auxiliares documentados para calidad, nunca presentados como KPI de negocio.

Cada derivación conserva receta, columnas fuente, tipo, versión y resultado del control. La misma lógica se usa para la consulta de referencia OLTP y para la comprobación del datamart.

La resolución sigue una política de automatización segura. La IA puede proponer `direct`,
`multiply`, `add`, `subtract` o `divide`; no entrega una expresión ejecutable. El validador intenta
resolver automáticamente los casos inequívocos a partir de nombres, tipos y función semántica. La
división protege el denominador cero y todas las operaciones aceptan únicamente de dos a cuatro
columnas numéricas verificadas. Una ambigüedad se presenta como diagnóstico, candidatos y acción
guiada, nunca como un pedido para que el analista adivine una columna o escriba SQL.

La propuesta 48 evidenció el control: `UnitPriceDiscount` conciliaba técnicamente, pero representa
una tasa. La propuesta 49 se derivó sin modificar la 48 ni la ejecución 5 y declaró la medida
`Descuento total` como `UnitPrice * UnitPriceDiscount * OrderQty`. La versión corregida superó
integridad de metadatos, referencias, consistencia del contrato y reproducción determinística con
cero errores y cero advertencias. La versión 48 permanece auditable, pero queda bloqueada para
nuevas ejecuciones.

## 4. Interpretación dinámica al español

La interpretación de esquemas, tablas y columnas continúa en el flujo semántico del Sprint 3: el LLM explica en español nombres técnicos de cualquier idioma y FastAPI conserva la referencia original. Sprint 4 amplía la experiencia a valores categóricos aptos para visualización, sin alterar la verdad operacional.

La inspección de metadatos debe resolver los tipos alias de SQL Server mediante su tipo base. AdventureWorks utiliza alias como `dbo.Name`; si la cuenta de sólo lectura no puede describir el alias, la introspección no debe perder la columna `Name`. Una instantánea incompleta invalida la calidad semántica y debe volver a capturarse después de corregir el conector.

El perfilador selecciona únicamente columnas descriptivas de baja cardinalidad, calcula valores distintos y aplica estas reglas:

1. si la etiqueta ya está en español, conserva el mismo texto;
2. la detección se realiza por elemento, porque una base puede mezclar nombres españoles e ingleses;
3. si requiere localización, propone un mapeo `valor_origen -> etiqueta_es` y conserva ambos;
4. el analista revisa, corrige entre opciones admitidas o excluye el mapeo antes de ejecutar;
5. la ejecución registra proveedor, versión, fecha, columna, valores cubiertos y valores sin traducción;
6. las nuevas etiquetas no participan como claves ni modifican conciliaciones numéricas.

No se envían filas completas al LLM. Tampoco se traducen identificadores, códigos, correos, nombres de personas, direcciones, comentarios, descripciones libres ni otra información sensible. Cuando una columna no pueda clasificarse con seguridad, se muestra con su valor original y una explicación accionable.

## 5. Perfilado y calidad visibles

Antes de confirmar, la interfaz resume por columna relevante: tipo de origen y destino, nulabilidad, función semántica, regla aplicada y acción ante rechazo. Después de cargar muestra filas leídas, aceptadas, rechazadas y deduplicadas, además de nulos, conversiones fallidas y diferencias de conciliación.

Una fila rechazada no desaparece sin explicación. La ejecución conserva un conteo y una muestra técnica limitada sin secretos; la pantalla ofrece la causa y la acción sugerida. Una regla bloqueante revierte la transacción de materialización.

## 6. Supervisión del analista

El analista puede:

- retirar una columna calculada opcional;
- escoger entre recetas compatibles ya validadas;
- definir una tolerancia permitida por el perfil;
- confirmar el tratamiento de valores desconocidos;
- aprobar o excluir etiquetas españolas propuestas para categorías no sensibles;
- volver al asistente para generar o personalizar otra propuesta.

No puede introducir SQL, código, nombres libres de columnas, funciones no registradas ni relaciones inexistentes.

## 7. Criterios de aceptación

- [x] La vista previa distingue extracción, limpieza, transformación, carga y conciliación.
- [x] Las medidas calculadas muestran entradas, operación, justificación y regla controlada antes de la aprobación.
- [x] Las claves obligatorias nulas, conversiones incompatibles y duplicados al grano tienen tratamiento explícito.
- [x] Las fechas y medidas calculadas usan recetas determinísticas conocidas.
- [x] La carga completa es transaccional y un fallo bloqueante no deja un datamart parcialmente actualizado.
- [x] La ejecución conserva conteos de filas leídas, aceptadas, rechazadas y deduplicadas.
- [x] El analista revisa, corrige o excluye etiquetas propuestas sin escribir SQL; su decisión queda auditada.
- [x] Las transformaciones se compilan desde referencias verificadas, claves foráneas declaradas y funciones semánticas del perfil.
- [x] Esquemas, tablas, columnas y categorías aptas se explican en español conservando siempre la referencia o valor original.
- [x] Un dato que ya está en español no se vuelve a traducir y una columna sensible o de alta cardinalidad no se envía al LLM.
- [x] Una caída o saturación del proveedor no invalida la carga conciliada: el analista puede activar otro proveedor y reintentar sólo la interpretación española.

## 8. Exclusiones

- SQL o Python generado y ejecutado por el LLM.
- Editor libre de fórmulas o transformaciones.
- Imputación estadística no especificada, enriquecimiento externo o corrección manual de filas.
- CDC, carga incremental y SCD tipo 2.
- Ocultar rechazos, conversiones fallidas o diferencias para presentar una ejecución como exitosa.
