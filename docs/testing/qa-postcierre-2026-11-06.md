# QA del 6 de noviembre de 2026: rutas exactas, cargas y analítica

**Estado:** código y escenarios operativos verificados. Los nuevos casos de reglas 5 son AdventureWorks 129/21 y WideWorldImporters 131/22. La revisión de los tres PDF técnicos se registra al concluir su compilación. No se declara fusión de PR, despliegue o aprobación académica.

**Evidencia resumida:** [registro verificable del corte](evidencia-postcierre-2026-11-06.json), con versiones, cifras y SHA-256 de los registros de origen. Los originales de las campañas, capturas nuevas y QA de exportes se conservan con la entrega documental consolidada.

## 1. Problemas encontrados y corrección

La auditoría para renovar los manuales detectó fallos del programa, sin atribuirlos exclusivamente a un proveedor:

| Incidente | Observación y decisión |
|---|---|
| Propuesta 125 | La expansión reemplazó territorio comercial por provincia mediante puntaje léxico, tomó atributos temporales por posición y permitió un promedio de líneas malrotulado por pedido. La revisión humana detuvo el intento antes de aprobar; no se le atribuye otro ETL. La pantalla del corte aún indicaba cero errores: no se presenta esa detección como un bloqueo automático ya existente. |
| Corte intermedio de reglas 4 | Preservó fuentes y fecha revisada, añadió evidencia del servidor y corrigió coherencia de promedios. Pasó 475 backend/48 frontend y produjo AW 126/20. Es un antecedente real, no una prueba de las reglas 5 posteriores. |
| WWI 127/128 | Conservar la tabla no bastaba: FK de comprador/facturación y entrega/postal podían llegar a la misma entidad. La evidencia persistida y la búsqueda del materializador podían escoger roles diferentes. Se mantuvieron sin aprobación, sin atribuirles otra materialización. |
| Regla vigente 5 | Conserva aristas exactas y roles respaldados; materializador y procedencia usan el mismo comprobador. No elige por orden del catálogo ni longitud del camino. Los contratos 1–4 permanecen congelados. |
| Copiloto temporal | Una respuesta rechazó el pronóstico pero añadió un año ajeno al contexto. Se incorporó reloj ISO UTC separado del histórico y la fecha ETL, y se precisaron las instrucciones. La prosa continúa supervisada. |
| Presentación | Se corrigieron título genérico para ambas vistas, preparación de un esquema propio por expediente y alias monetarios comunes. No cambian contratos ni cifras por esos ajustes de texto. |

No se implementó un límite automático de cantidad de KPI. La cantidad permanece variable y la selección sigue supervisada. Un promedio por documento requiere un denominador de documentos distintos; AVG de líneas no acredita ese resultado.

## 2. Contrato y límites de las rutas

- Los contratos nuevos identifican `sales-bi-v8` y `compilation_rules_version=5`.
- `source_resolution.path` conserva las aristas ordenadas con tablas y columnas de ambos extremos. Se comprueban FK dirigidas hacia PK completas, continuidad, clave de negocio y prefijos compatibles.
- El descubrimiento enumera rutas simples seguras hasta 32 rutas y 4096 estados. Al exceder el límite se bloquea; no se presenta la primera como única ni se prioriza la más corta como prueba de significado.
- La evidencia primaria y de otras dimensiones revisadas delimita el rol. La trazabilidad de pedido no autoriza por sí sola cambiar comprador, factura o entrega. Una elección humana incompatible requiere editar y reevaluar la necesidad.
- La interfaz no preselecciona una relación ambigua y bloquea el guardado hasta una elección. No se incorporaron alias separados por rol para eludir conflictos de prefijos hacia una tabla.
- `persisted_relationship_paths` es compartido por el materializador y la procedencia analítica. Si la evidencia es inválida, no se comunica una ruta alternativa descubierta por BFS como si fuera la ejecutada.
- Las medidas externas reutilizan una ruta custodiada o requieren una única ruta dirigida segura compatible. No reabren una búsqueda libre por orden de metadatos.
- La unicidad actual se prueba con PK capturadas. Restricciones UNIQUE alternativas no exportadas, identidades dimensionales compuestas no admitidas y motores futuros son límites explícitos.

## 3. Historial y puerta de nueva carga

La puerta ETL `_candidate` exige reglas 5 para preparar o ejecutar otra carga, incluido un expediente que permanecía preparado con reglas anteriores. Bloquea antes de insertar o pasar a running y pide una versión derivada actual aprobada.

GET de historial, panel y exportes conservan acceso de lectura; no se retiran aprobaciones ni se cambian estados, datos o huellas por consultar. La expansión y ejecución histórica 1–4 quedan congeladas. AW 126/20 conserva reglas 4 y no se renombra como ensayo de reglas 5.

La comparación independiente de reglas 3 contra el servicio real de `origin/develop` conservó objetos y hashes ES/EN; no compara únicamente dos llamadas a la función nueva. Las lecturas de la campaña conservaron propuestas, métricas y esquemas anteriores sin mutación. La auditoría de lectura no volvió a invocar IA ni ejecutar otro ETL.

## 4. Verificación automatizada definitiva

| Control | Resultado del árbol final |
|---|---|
| Comando | `make verify`, salida 0. |
| Backend | 530 pruebas aprobadas; un aviso sin fallo. |
| Frontend | 50 pruebas aprobadas en 3 archivos, lint y construcción. |
| Calidad backend | Ruff aprobado; 93 archivos con formato; Mypy sin incidencias en 57 fuentes. |
| Rama, Compose y workflow | Controles aprobados por la misma verificación. |
| Registro final | `/tmp/bi-verify-entrega-final-20261106.log`, corte 03:24:58 -05:00 del 6 de noviembre. |
| Reutilización | Capas idénticas del árbol final; no se atribuye una ejecución nueva sin caché a cada capa. |

El corte incluye las rutas de reglas 5, puerta histórica, título genérico y alias importe/valor con denominadores. La ampliación de 48 a 50 frontend corresponde a dos casos adicionales de alias. Las 67 focales de ejecución/procedencia, 27 de la puerta ETL, 44 de App y 26 del reloj del copiloto son subconjuntos: no se suman al total global.

Los cortes 475/48 y 530/48 se conservan como antecedentes anteriores a todos los ajustes de presentación. No se reutilizan como el resultado definitivo 530/50.

## 5. AdventureWorks: propuesta 129, ejecución 21

| Control | Resultado |
|---|---|
| Contrato | Reglas 5, aprobado; cero errores y nueve avisos aceptados. |
| Materialización | Cinco tablas; 121317 filas en origen y destino; diferencia cero. |
| Rutas | Cuatro dimensiones con correspondencia entre contrato, plan y procedencia; territorio comercial desde Sales.SalesTerritory. |
| Global | 109846381.399888 USD; 274914 unidades; 31465 pedidos; promedio 3491.065672966407 por pedido. |
| Filtro 2013/Northwest | 6015174.735836 USD; 17452 unidades; 2053 pedidos; promedio 2929.943855740867. |
| Historial | Datos, aprobaciones y huellas 18/20/21 conservados; esquemas físicos separados. |
| Exportes 21 | PDF 6 páginas legibles; XLS 6 hojas con Resumen, 4 visuales y Trazabilidad. El indicador exportado fue unidades. |

Los meses y la distribución territorial suman 17452 unidades. Los Top 8 de productos/clientes son subconjuntos, con participaciones sobre el total mostrado. Los cuatro KPI exactos de Resumen coinciden con el control. El título ahora es Análisis de ventas y la descripción aparece completa.

Permanece una observación de presentación: la razón monetaria del PDF 21 conserva «moneda de origen por transacción» aunque USD esté comprobado. El valor y denominador son correctos. No se retocó ese archivo para atribuirle una corrección posterior ni se lo presenta como perfección semántica universal.

## 6. WideWorldImporters: propuesta 131, ejecución 22

| Control | Resultado |
|---|---|
| Contrato | Reglas 5, aprobado; cero errores y siete avisos aceptados. |
| Materialización | Cinco tablas; 228265 filas en origen y destino; diferencia cero. |
| Global | Importe 198043439.45 de moneda de origen; 8950628 unidades; 70510 facturas; promedio 2808.7283995177986. |
| Ruta de cliente/territorio | InvoiceLines→Invoices.CustomerID→Customers.DeliveryCityID→Cities.StateProvinceID→StateProvinces; misma evidencia en contrato, plan y procedencia. |
| Oráculo OLTP 2015/California | 3771 líneas; 3191769.11 de importe; 142247 unidades; 1179 facturas; promedio 2707.1832994062765. |
| Exportes 22 | PDF 6 páginas legibles; XLS 6 hojas/4 gráficos, con indicador de importe; 4 KPI exactos de Resumen y sumas mensual/territorial acordes. |

El oráculo es una consulta independiente sólo SELECT sobre InvoiceDate de 2015 y California, con el rol comprador y la ciudad registrada de entrega. El conteo físico filtrado del datamart también fue 3771. La conciliación global 228265 no se confunde con ese conteo del filtro.

La ejecución 19 utilizaba otro rol legado de facturación. Sus cuatro totales globales se conservaron y pudieron contrastarse sin mutación, pero sus cifras territoriales no son oráculo para el nuevo rol. La diferencia de clasificación no demuestra mezcla entre bases.

La comprobación de divisa del expediente 22 fue reintentada sin otro ETL: siguió no resuelta y mantuvo cifras y huella. La interfaz admite alias monetarios comunes importe/valor y denominadores, sin inventar USD y preservando unidades personalizadas anteriores. El exporte conserva Importe como etiqueta genérica y moneda de origen en cabecera, sin un ISO no demostrado.

## 7. Copiloto, lectura comercial y límites

El reloj ISO UTC del servidor no amplía años disponibles ni acredita un pronóstico. Las instrucciones prohíben añadir fechas/categorías ajenas y piden «el período solicitado» al rechazar pronóstico relativo. También piden lenguaje de negocio, evitando claves JSON, estados internos y códigos KPI en la prosa.

La respuesta operativa de WWI 22 acertó 3191769.11/142247/1179 y explicó límites de ubicación histórica, entrega no demostrada y moneda sin identificar. No se declara perfecta su redacción: la IA conserva texto libre supervisado y carece de un validador universal de veracidad.

Los atributos reflejan el estado leído duranteETL. Ni la fecha del hecho ni la provincia registrada prueban vigencia histórica o una entrega real. Un ranking no demuestra preferencias, demanda, causalidad, cuota de mercado o eficacia comercial. El sistema no añade pronóstico, otros motores ni hechos fiscales no demostrados.

Las variantes ES/EN de pruebas y dos fuentes SQL Server no acreditan todos los idiomas, proveedores o esquemas. Los controles de permisos no equivalen a sesiones manuales completas con todos los roles. Los casos documentados son reproducibles dentro de sus requisitos, configuración y límites; no una garantía de infalibilidad del LLM.

## 8. Documentación y revisión visual

Fuentes actualizadas: SPR-03-02, SPR-04-01, SPR-04-02, SPR-05-05 y SPR-05-06; manual técnico 5.2.2, bitácora 0.6.9, informe Sprint 6 v1.2.2, arquitectura, guía de réplica y título académico de scope. No se cambian objetivos o motores por el título.

Los tres PDF técnicos se recompilan con Docker desde esas fuentes. La revisión final de todas sus páginas, huellas de PDF/TEX y advertencias de compilación se registra en el actaQA visual del consolidado. Estado al cerrar este texto: compilación y revisión final en proceso; las cifras y el código ya están verificados.
