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
