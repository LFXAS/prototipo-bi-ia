# SPR-05-02: reportería fiel en PDF y Excel

- Estado: **implementada y verificada**
- Dependencia: `SPR-05-01`
- Usuarios: roles con acceso al dashboard y permiso de exportación

## 1. Problema y objetivo

Una captura o un volcado de tablas no constituye un reporte profesional. PDF y Excel deben representar la misma selección autorizada que el usuario observa, conservar contexto y ser utilizables fuera de la aplicación sin confundir datos filtrados con totales generales.

## 2. Alcance

- PDF ejecutivo listo para lectura e impresión;
- libro Excel con resumen, datos de cada visual visible y hoja de trazabilidad para la vista analítica;
- aplicación de modo, indicador y filtros vigentes;
- fecha, moneda, período, propuesta, ejecución y estado de conciliación;
- nombres de archivo inequívocos y descarga generada por servidor;
- registro de auditoría por formato y selección.

No se exportan credenciales, filas del OLTP, SQL, datos ocultos por la vista, fórmulas ejecutables ni componentes que el rol no puede consultar.

## 3. Reglas de fidelidad

1. La exportación vuelve a construir el conjunto autorizado en servidor; no confía en datos enviados por el navegador.
2. La vista ejecutiva excluye controles y hojas reservadas al analista.
3. Excel usa valores numéricos reales y formatos de número, no cifras convertidas en texto.
4. PDF repite encabezados, reserva espacio después de cada salto, evita cortes ilegibles y numera páginas.
5. Ambos formatos indican explícitamente los filtros activos y el expediente de origen.
6. Si la ejecución dejó de ser válida entre consulta y exportación, la operación falla de forma segura.
7. Un KPI porcentual ya calculado en escala 0--100 conserva esa escala en Excel; el formato añade el signo sin volver a multiplicar el valor. Las participaciones de gráficos, calculadas como fracción, sí usan formato porcentual convencional.

### 3.1. Precisión de unidades posterior al cierre

La revisión del 4–5 de noviembre corrige la pérdida de decimales cuando una unidad
compuesta, como moneda por unidad o moneda por pedido, se confundía con un conteo.
El formato utiliza la unidad del contrato, sin deducirla del nombre o la descripción
del KPI. Importes, razones y cantidades fraccionarias conservan dos decimales por
defecto; la etiqueta genérica unidades no acredita que la cantidad sea entera.
Los conteos explícitos de pedidos, clientes, filas o facturas, incluidos sus
equivalentes admitidos en inglés, se presentan sin decimales. El resumen Excel
recibe exclusivamente `metric.unit` para esta decisión.

La corrección afecta las exportaciones nuevas; los PDF y libros históricos se
conservan como evidencia de su corte y no se reescriben. Las 52 pruebas focalizadas
de `backend/tests/test_analytics_export.py`, Ruff, formato y Mypy del bloque están
aprobados. La suite integrada y la inspección de exportaciones nuevas se registran
por separado en [QA posterior al cierre](../testing/qa-postcierre-2026-11-04.md).

Ambos reportes imprimen `source_name`, `database_name` y actualización en formato
ISO con el offset recibido. Si la fecha no incluye zona, se indica que no está
informada; no se inventa una conversión local. XLSX conserva cadenas como texto
literal y deshabilita su conversión automática en fórmulas o hipervínculos.

La primera exportación 18, sin el contexto nuevo, se conserva revisada con esa
limitación. La exportación 19 inicial se contrastó en cinco páginas y cuatro hojas:
22 controles conformes, números/razón/totales, fuente/base/offset y sin fórmulas de
celda ni hipervínculos automáticos. Cada descarga posterior de contexto requiere
su propio hash y revisión; no se le transfiere la QA del original anterior.

La descarga intermedia 19-contexto conservaba el aviso completo pero lo recortaba
visualmente en una fila de 34 pt. La altura se calcula ahora según texto, palabras,
saltos, identificadores, fuente y ancho real/fusionado, también para fuente/base/fecha.
Los finales 18 y 19 mostraron aviso íntegro en 57 pt: diez páginas PDF y ambos XLSX
revisados con ArtifactTool, cifras/razones/sumas/Top 8/contexto conformes y SHA propios.
No se afirma una inspección Calc final que no se completó por memoria; la prueba
sintética previa pertenece a otro artefacto. Los originales intermedios se conservan.

### 3.2. Correspondencia con la presentación web posterior

La revisión adicional de la interfaz del 5 de noviembre aplica también la unidad
completa a la lectura web: ISO monetario y denominador conservan dos decimales,
cantidades fraccionarias mantienen su precisión y sólo un conteo explícito del
conjunto cerrado usa formato entero. La divisa verificada sustituye el prefijo
genérico monetario sin borrar «por transacción» u otro denominador contractual.
La presentación de conciliación admite saltos de línea y apila sus columnas en
pantallas estrechas; véase [SPR-04-02](SPR-04-02-kpis-controlados-y-calculables.md).

El ajuste de frontend `8f1c7d1`, verificado por V6 (454 backend/48 frontend), es
posterior al corte `bf50172`; no constituye una regeneración de
los PDF/XLSX anteriores. Sus capturas originales y sus hashes conservan el aspecto
observado en su fecha. La revisión visual de una pantalla nueva sobre 18/19 se
identifica por separado y no se transfiere retroactivamente a esas evidencias.

## 4. Contrato

- `GET /api/v1/analytics/reports/pdf`
- `GET /api/v1/analytics/reports/xlsx`
- Parámetros: `view`, `metric`, `year`, `territory`.
- Respuesta: archivo adjunto con tipo MIME y nombre controlados.

## 5. Seguridad y auditoría

Requiere conjuntamente `analytics.dashboard.read` y `reports.analytics.export`. Se registra usuario, formato, vista, filtros, propuesta y ejecución. Las hojas no contienen macros, vínculos externos ni fórmulas procedentes de IA.

## 6. Criterios de aceptación

- [x] PDF y Excel muestran los mismos filtros, KPIs y visuales habilitados en la pantalla.
- [x] La vista ejecutiva y la analítica producen contenidos acordes con sus responsabilidades.
- [x] Los números de Excel conservan tipo y formato; las hojas de datos permiten comprobación.
- [x] El PDF es legible en A4 horizontal y no corta títulos, gráficos ni tablas.
- [x] Una persona sin permiso no puede invocar los endpoints.
- [x] Cada descarga queda auditada.
- [x] Las pruebas inspeccionan estructura, contenido, permisos y errores controlados; PDF y todas las hojas del libro se renderizaron para control visual.

## 7. Evidencia

Se verificó primero el reporte analítico real de la ejecución 7. El PDF contiene seis páginas A4 horizontales con resumen, tendencia, rankings y calidad sin cortes. Excel contiene las hojas Resumen, Evolución en el tiempo, Productos líderes, Distribución territorial, Clientes principales y Trazabilidad; sus gráficos y tablas fueron renderizados hoja por hoja, con valores numéricos, moneda USD, pedidos enteros y nombres descriptivos de clientes.

La regresión final se repitió con la ejecución 12, conciliada con 121.317 filas de origen y destino, propuesta 91 y moneda USD. El PDF ejecutivo produjo cinco páginas A4 horizontales y se inspeccionó página por página; el espaciado posterior a cada salto evita que el encabezado de una sección quede recortado por el margen superior. El Excel analítico produjo seis hojas y cuatro gráficos, con áreas de impresión válidas y sin fórmulas ni errores. El KPI Margen bruto \% conserva el valor 8,53 y se presenta como 8,5\%, no como 853,2\%.
