# SPR-04-02: KPIs propuestos por IA, calculables y trazables

- Estado: **contrato, medidas y seis KPI implementados y conciliados en la ejecución 6**.
- Dependencias: `SPR-04-01`, una propuesta de ventas aprobada y un contrato ETL compatible.
- Propósito: convertir los KPIs propuestos dinámicamente por el copiloto en cálculos reproducibles, sin fórmulas libres ni resultados atribuidos al LLM.

## 1. Decisión de alcance

Los KPI no se predefinen como una lista fija. Para cada necesidad, el LLM interpreta el objetivo comercial, las preguntas elegidas, la periodicidad y los metadatos comprobados. A partir de ello propone una cantidad variable de KPI en español. Puede proponer menos o más de cinco indicadores cuando la necesidad lo justifique.

El sistema establece un límite técnico de doce KPI y seis medidas por propuesta para conservar un contrato manejable y una interfaz legible. Este límite no define cuáles indicadores aparecerán ni obliga a una cantidad determinada. Si una necesidad necesita mayor detalle, el analista puede delimitar otro análisis o solicitar una nueva propuesta.

El anteproyecto exige evidenciar cinco KPI en la demostración final. Para el caso de ventas seleccionado se aprobarán y validarán al menos cinco sugerencias que la IA haya generado. No significa que cada propuesta contenga cinco, que se repitan siempre los mismos indicadores ni que el frontend los imponga.

## 2. Profundización semántica del copiloto

Antes de proponer, FastAPI forma un alcance semántico desde metadatos estructurales: tablas, columnas, tipo de dato, PK, FK, relación, grano posible y clasificación de columnas candidatas a importe, cantidad, pedido, cliente, fecha o segmento. No envía filas, valores, secretos ni código SQL al proveedor.

La IA usa ese alcance para relacionar la necesidad con medidas, claves y dimensiones. Cada sugerencia debe declarar nombre, explicación, tipo de fórmula, dependencias, dimensiones, periodicidad, unidad y función semántica. Por ejemplo:

```json
{
  "code": "ventas_por_pedido",
  "name_es": "Venta promedio por pedido",
  "description_es": "Importe de ventas dividido para pedidos distintos del período.",
  "formula_kind": "ratio",
  "inputs": ["importe_venta", "pedido_distinto"],
  "dimensions": ["dim_fecha", "dim_territorio"],
  "periodicity": "month",
  "unit": "moneda_por_pedido",
  "semantic_roles": ["sales_amount", "transaction_count"]
}
```

El analista BI revisa relevancia, período, dimensiones y advertencias. Puede retirar sugerencias, reasignarlas únicamente a medidas compatibles o volver a solicitar una propuesta más precisa. No crea tablas, no escribe SQL y no escribe fórmulas libres.

## 3. Capacidades de KPI que la IA puede sugerir

La siguiente matriz representa capacidades iniciales, no un catálogo obligatorio. El LLM las puede sugerir sólo cuando la fuente y la propuesta contienen los requisitos correspondientes.

| Tipo de sugerencia | Cálculo controlado | Requisitos que valida FastAPI |
|---|---|---|
| Ventas netas | Suma del importe de líneas de venta. | Medida monetaria validada. |
| Unidades vendidas | Suma de cantidades vendidas. | Medida de cantidad validada. |
| Número de pedidos | Conteo distinto de pedidos. | Identificador de pedido preservado al grano. |
| Clientes con compras | Conteo distinto de clientes en el período. | Clave de cliente verificable y relación aprobada. |
| Venta promedio por pedido | Ventas netas dividido para número de pedidos. | Numerador y denominador con mismo período y filtros. |
| Unidades promedio por pedido | Unidades vendidas dividido para número de pedidos. | Numerador y denominador con mismo período y filtros. |
| Ventas por producto, cliente o territorio | Ventas netas agrupadas por la dimensión elegida. | Dimensión, relación y medida monetaria verificadas. |
| Participación de ventas | Ventas del segmento dividido para ventas totales por cien. | Segmento y total con misma medida, filtros y ventana temporal. |

La IA puede proponer otros indicadores si encajan en una receta soportada. Si alguien solicita clientes nuevos, margen, utilidad, estados de pedido u otro cálculo que no pueda sustentarse con metadatos y recetas implementadas, el sistema debe indicar el requisito faltante en lugar de inventarlo.

## 4. Recetas controladas y extensibilidad

Cada KPI propuesto debe corresponder a una receta declarativa, versionada y probada por el perfil de dominio. El LLM selecciona referencias existentes, pero no inventa recetas.

| Receta inicial | Qué permite | Reglas bloqueantes |
|---|---|---|
| `aggregate` | Suma, conteo, conteo distinto, promedio, mínimo o máximo de una medida válida. | Columna, tipo, agregación y grano compatibles. |
| `ratio` | Divide una medida o KPI base por otra medida o KPI base equivalente. | Numerador y denominador comparten alcance; si el denominador es cero, el resultado es nulo y se registra la condición. |
| `share` | Participación de un segmento respecto al total del mismo período. | Segmento y total comparten medida, filtros y ventana de tiempo. |

Una receta futura requiere especificación, pruebas, plantilla de referencia y control de conciliación. No se aceptan SQL, texto de fórmula, nombres de columnas libres ni cálculos anidados enviados por el LLM, navegador o administración.

Las medidas que alimentan a esos KPI también pueden usar una receta aritmética por fila. La IA
declara una operación del catálogo y columnas presentes en la tabla de hechos; FastAPI vuelve a
comprobar tipos, existencia, cantidad de operandos y función semántica. Si detecta una tasa de
descuento usada como importe y encuentra de forma inequívoca precio, tasa y cantidad, la corrige
automáticamente como `precio * tasa * cantidad`. Si falta una entrada o hay varias candidatas,
bloquea la propuesta y muestra al analista las referencias reales y la acción necesaria.

La misma regla se aplica cuando el proveedor ya envía una fórmula parcial. Una multiplicación de
tasa por cantidad no se considera un importe: el backend sustituye esa receta por precio, tasa y
cantidad si las tres referencias son inequívocas. Cuando no puede demostrar una base monetaria,
la validación de la propuesta y la puerta previa del ETL la bloquean, aunque el LLM la haya marcado
como válida.

## 5. Contrato ejecutable

El contrato persistido conserva la sugerencia de IA y, al preparar el ETL, FastAPI agrega la receta exacta que ejecutará:

```json
{
  "code": "ventas_por_pedido",
  "name_es": "Venta promedio por pedido",
  "formula_kind": "ratio",
  "inputs": ["importe_venta", "pedido_distinto"],
  "periodicity": "month",
  "filters": [],
  "definition_version": "sales-kpi-v1",
  "recipe": {
    "template": "ratio",
    "numerator": "importe_venta",
    "denominator": "pedido_distinto",
    "zero_denominator": "null"
  }
}
```

Cada definición queda ligada a la propuesta, instantánea, ejecución, período y filtros. Cambiar de propuesta, reglas o selección crea una ejecución nueva y no altera resultados anteriores.

## 6. Validación y evidencia

Después de materializar el datamart, **Validación del datamart** muestra por cada KPI seleccionado:

- nombre y explicación sugeridos por IA;
- receta y versión aplicada por FastAPI;
- período, filtros y dimensiones usados;
- valor de referencia desde AdventureWorks OLTP;
- valor obtenido desde `mart`;
- diferencia absoluta, diferencia relativa, tolerancia, estado y acción sugerida;
- propuesta, instantánea y ejecución de origen.

Cada KPI base o derivado se compara mediante la misma receta en ambas fuentes. Una diferencia bloqueante impide presentarlo como resultado validado. AdventureWorksDW permanece como contraste secundario posterior y no sustituye la fuente OLTP de referencia.

### 6.1. Divisa monetaria comprobada

Una etiqueta como `moneda`, `importe` o `currency` no autoriza a mostrar un símbolo. El ejecutor busca en el alcance relacional de la tabla de hechos una columna verificable de moneda de origen o base, consulta únicamente sus códigos distintos mediante la conexión de sólo lectura y acepta el resultado sólo cuando obtiene un único código ISO de tres letras. La evidencia conserva el código, la tabla, la columna y el mensaje usado para resolver la unidad.

Los KPI monetarios se presentan con ese código ISO —por ejemplo, `USD 109.846.381,40`— y las unidades no monetarias permanecen sin cambios. Si la fuente contiene monedas mezcladas, varios candidatos contradictorios o ninguna evidencia suficiente, el sistema mantiene `moneda de origen`, no inventa un símbolo y explica qué dato falta. Un expediente anterior puede ejecutar esta comprobación y enriquecer sus unidades sin repetir extracción, transformación, carga ni conciliación.

## 7. Criterios de aceptación

- [x] La IA propone una cantidad variable de KPI a partir de necesidad, preguntas, periodicidad y metadatos verificables.
- [x] La interfaz no fuerza una lista ni cantidad fija de KPI; admite hasta doce sugerencias y seis medidas por propuesta.
- [x] Cada KPI muestra explicación, dependencias, período y receta antes de materializarlo.
- [ ] El analista puede retirar una sugerencia o reasignarla sólo a una medida compatible comprobada.
- [x] Un KPI sin columna, relación, tipo, receta o denominador válido queda bloqueado con una explicación accionable.
- [x] Cada KPI calculado usa una plantilla conocida, sin SQL ni fórmulas libres generadas por IA.
- [x] La ejecución 5 reunió cinco KPI sugeridos por IA; la ejecución 6 materializó los seis KPI de la propuesta 52, excluyó preventivamente un concepto débil y aplicó el descuento monetario autocorregido.
- [x] Una unidad monetaria se reemplaza por un código ISO sólo después de comprobar una moneda única y trazable en la fuente; la ambigüedad conserva una etiqueta genérica y una acción guiada.
- [x] Cada resultado conserva trazabilidad de propuesta, ejecución, período y regla aplicada.

## 8. Exclusiones

- Catálogo fijo de KPI impuesto por el frontend o AdventureWorks.
- Repetir siempre los mismos indicadores sin analizar la necesidad.
- Crear SQL, fórmulas arbitrarias, columnas o relaciones inexistentes.
- Declarar calculado un KPI antes de ejecutar el ETL y conciliarlo.
- Usar AdventureWorksDW como fuente primaria de carga o como equivalencia automática del datamart generado.
