# SPR-05-01: dashboard ejecutivo y espacio analítico explicable

- Estado: **implementada y verificada**
- Dependencias: ejecución ETL conciliada y `SPR-05-03`
- Usuarios: CEO, gerencias y analista BI

## 1. Problema y objetivo

Los resultados del datamart deben poder comprenderse y utilizarse sin consultar tablas técnicas. La plataforma ofrecerá una vista ejecutiva predeterminada y una vista analítica avanzada sobre la misma fuente conciliada, sin inventar conclusiones ni mezclar responsabilidades.

## 2. Alcance

- KPIs dinámicos calculados por el Sprint 4, sin fijar una cantidad exacta.
- filtros por indicador, año y dimensiones disponibles;
- evolución temporal, rankings de producto, territorio y cliente, sólo si la dimensión supera calidad semántica;
- hallazgos determinísticos con cifra, comparación y advertencia de no causalidad;
- vista ejecutiva resumida y vista de analista con tablas accesibles, calidad y trazabilidad;
- estados de carga, vacío, error, falta de permiso y datamart no disponible;
- diseño responsive desde 320 px y presentación profesional en pantallas amplias.
- interacción por ratón y teclado con puntos, barras y categorías para consultar
  valor exacto, participación y contexto sin abandonar el dashboard;
- aplicación directa de una categoría territorial como filtro global cuando la
  categoría existe en el catálogo autorizado de la ejecución.

Quedan fuera el pronóstico de ventas, alertas autónomas, edición libre del dashboard, creación manual de fórmulas y ejecución de consultas SQL.

## 3. Reglas funcionales

1. La API consulta únicamente una ejecución exitosa y conciliada.
2. Los filtros se aplican en servidor y cada respuesta identifica propuesta, ejecución, moneda y período.
3. Una dimensión sin etiqueta descriptiva válida no se publica como ranking ejecutivo; se presenta al analista como incidencia de calidad.
4. Los hallazgos indican la evidencia que los sustenta y no atribuyen causalidad.
5. El modo ejecutivo oculta detalle operativo innecesario; el modo analista no altera los datos, sólo amplía la evidencia.
6. La moneda se expresa mediante código ISO demostrado por la fuente; no se infiere por ubicación o símbolo.
7. Los cocientes `CostoTotal / UnidadesVendidas` y `Ventas / UnidadesVendidas`
   se presentan como **Costo promedio por unidad vendida** y **Venta promedio por
   unidad vendida**. La tarjeta y su ayuda muestran el denominador y evitan que el
   usuario los confunda con el costo o precio de una unidad específica.
8. Las tarjetas separan cifra y unidad, usan abreviación legible sólo cuando el
   valor completo no cabe y conservan el valor exacto como ayuda accesible.
9. Seleccionar un punto, barra o leyenda abre un detalle contextual dentro de la
   misma tarjeta. El detalle se puede cerrar, no cambia filtros por sorpresa y
   anuncia valor, participación y acción disponible.
10. Una categoría territorial ofrece **Filtrar tablero** sólo si su clave coincide
    con una opción real devuelta por el backend. Al aplicarla se actualizan KPIs,
    gráficos, hallazgos y contexto mediante la API existente.
11. El usuario puede elegir entre ejecuciones conciliadas cuyos datos físicos se
    conserven. La interfaz muestra ejecución, propuesta, fecha, proveedor, cobertura
    y estado analítico; no confunde la ejecución más reciente con la versión activa
    o más completa.
12. Una nueva materialización se guarda en un espacio versionado por ejecución y no
    elimina las tablas de ejecuciones anteriores. Los expedientes previos que sólo
    conserven metadatos se identifican como históricos no disponibles y no se
    ofrecen como si todavía pudieran consultarse.
13. Una tarjeta `not_calculable` muestra **No calculable**, la causa disponible y
    una acción de revisión. No usa confirmación verde ni afirma que fue calculada.

## 4. API e interfaz

- `GET /api/v1/analytics/dashboard`
- Parámetros: `metric`, `year`, `territory` y futuras dimensiones verificadas.
- Menú: **Analítica de ventas**.
- Componentes: contexto, filtros, tarjetas KPI, tendencia, rankings, hallazgos, calidad y trazabilidad.

La pantalla conserva una acción primaria clara, orden de foco lógico, encabezados jerárquicos, texto alternativo/tablas de respaldo para gráficos y mensajes que no dependen sólo del color. En móvil los paneles se apilan sin desplazamiento horizontal.

## 5. Seguridad

Requiere `analytics.dashboard.read`. La consulta de datos agregados no otorga acceso a configuración, ETL ni muestras de origen. Un usuario sin autorización recibe `403` y la opción de menú no se presenta.

## 6. Criterios de aceptación

- [x] La vista ejecutiva abre por defecto y permite comprender situación, variación y contribuciones principales.
- [x] La vista analítica muestra calidad, tablas de datos y trazabilidad adicional.
- [x] Los filtros cambian conjuntamente KPIs, gráficos y hallazgos.
- [x] Los rankings de entidades usan una etiqueta descriptiva validada, no una clave técnica silenciosa.
- [x] Cada hallazgo conserva cálculo y evidencia reproducible; la comparación de extremos advierte cobertura parcial y no causalidad.
- [x] Los estados de carga, vacío, error y falta de autorización son comprensibles.
- [x] La interfaz funciona con teclado y adapta su composición a móvil, tableta y escritorio.
- [x] Las pruebas cubren agregación, filtros, permisos, ausencia de ejecución y calidad semántica insuficiente.
- [x] Los KPI por unidad se identifican como promedios, muestran moneda comprobada
      y no desbordan sus tarjetas.
- [x] La pregunta escrita por el usuario conserva contraste AA sobre el globo azul.
- [x] Los puntos, barras y leyendas son controles enfocables con nombre accesible
      y presentan un detalle contextual verificable.
- [x] Una categoría territorial puede convertirse explícitamente en filtro global
      sin aceptar valores ajenos al catálogo autorizado.
- [x] El selector de datamart cambia de ejecución sin repetir el ETL y conserva la
      selección en filtros, chat y exportaciones.
- [ ] Dos ejecuciones nuevas pueden consultarse de forma independiente después de
      materializar la segunda.
- [x] Los expedientes sin tablas físicas no aparecen como datamarts consultables.
- [x] Si sólo existe un datamart con filas físicas, se identifica en modo lectura,
      no se presenta un selector vacío y se enlaza la consulta de expedientes
      conservados; el selector aparece desde dos alternativas reales.
- [x] El detalle interactivo adapta nombre, valor y participación al ancho de cada
      visualización sin desbordar ni superponerse con tarjetas contiguas.

## 7. Evidencia

La ejecución conciliada 7, derivada de la propuesta 54, publica 121317 líneas sin diferencia. El panel presenta nombres descriptivos de clientes, código de moneda USD comprobado, siete indicadores disponibles, cuatro visualizaciones en modo analista y evidencia asociada a cada hallazgo. La validación se completa con pruebas backend, pruebas de componentes, compilación de producción y revisión visual de ambos modos.
