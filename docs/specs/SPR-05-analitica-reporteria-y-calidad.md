# SPR-05: analítica explicable, reportería fiel y calidad semántica

- Estado: **implementado y verificado localmente**
- Sprint: SPR-05
- Responsable de especificación: equipo del proyecto
- Rama: `feature/sprint-05-analitica-visual`
- Fecha de creación: 2026-09-24
- PR de implementación: pendiente

## 1. Objetivo del incremento

Convertir el datamart conciliado del Sprint 4 en una experiencia analítica profesional para gerencia comercial, gerencia general, dirección ejecutiva y analistas BI. El incremento debe presentar indicadores y visualizaciones reproducibles, hallazgos explicables, exportaciones fieles a la vista y herramientas internas para comprobar la calidad semántica sin depender de DBeaver, SQL libre ni conocimiento previo de la base operacional.

El Sprint 5 no incluye pronóstico de ventas. El tutor determinó que un modelo de *forecasting* no aporta al problema central de construcción semiautomatizada de un datamart y desviaría la validación hacia un objetivo predictivo distinto. La modificación debe reflejarse en alcance, requisitos, arquitectura, tesis, manual e informe de sprint, conservando trazabilidad de la decisión.

## 2. Especificaciones que componen el sprint

| Código | Capacidad | Resultado verificable |
|---|---|---|
| [`SPR-05-01`](SPR-05-01-dashboard-ejecutivo-explicable.md) | Dashboard ejecutivo y espacio analítico | KPIs, gráficos, filtros, vistas por rol y hallazgos explicables calculados desde un datamart conciliado. |
| [`SPR-05-02`](SPR-05-02-reporteria-fiel-pdf-excel.md) | Exportación PDF y Excel | El archivo refleja filtros, indicadores, vista y trazabilidad que el usuario puede observar. |
| [`SPR-05-03`](SPR-05-03-calidad-semantica-y-resolucion-de-entidades.md) | Identidad descriptiva y resolución visual | La plataforma detecta dimensiones sin etiquetas válidas, recorre relaciones comprobadas y permite resolver excepciones sin herramientas externas. |
| [`SPR-05-04`](SPR-05-04-capacidades-y-compatibilidad-llm.md) | Compatibilidad de proveedores LLM | Cada proveedor/modelo expone sólo opciones admitidas y traduce errores de capacidad a una acción concreta. |
| [`SPR-05-05`](SPR-05-05-copiloto-analitico-contextual.md) | Copiloto analítico contextual | Usuarios finales y analistas conversan sobre la selección visible mediante preguntas guiadas, evidencia y límites explícitos. |

## 3. Actores y separación de responsabilidades

| Actor | Responsabilidad |
|---|---|
| CEO, gerente general o gerente comercial | Consulta la vista ejecutiva, filtra, interpreta hallazgos y exporta un resumen autorizado. No diseña el ETL. |
| Analista BI | Usa la vista detallada, inspecciona datos agregados, calidad, linaje y excepciones semánticas; confirma una corrección guiada cuando la automatización no alcanza certeza suficiente. |
| Administrador de plataforma | Asigna permisos, registra fuentes y configura proveedores LLM. No aprueba decisiones de negocio por defecto. |
| IA | Sugiere conceptos, atributos, KPIs y explicaciones; no ejecuta SQL libre ni sustituye validaciones estructurales o cuantitativas. |
| Motor determinístico | Valida referencias, relaciones, recetas, cobertura, unicidad, conciliación y compatibilidad del proveedor antes de ejecutar o publicar. |

## 4. Reglas transversales

1. Ninguna cifra o etiqueta visible procede directamente de texto generado por la IA; debe calcularse o resolverse desde referencias verificadas.
2. Los nombres de tablas no bastan para identificar una entidad. Se consideran claves, relaciones, tipos, cardinalidad, nulabilidad, cobertura y atributos descriptivos de las tablas relacionadas.
3. La población de una dimensión responde al evento de negocio. Una dimensión de clientes parte de quienes compran, aunque el nombre descriptivo resida en otra entidad; no se sustituye por todas las personas de la organización.
4. Una dimensión presentada a usuarios debe disponer de una etiqueta descriptiva controlada. Un identificador o número de cuenta sólo puede ser respaldo explícito, nunca una etiqueta silenciosa.
5. La automatización aplica correcciones inequívocas. Si existen dos alternativas materialmente distintas, bloquea la publicación y ofrece evidencia, vista previa y opciones ejecutables al analista.
6. La vista ejecutiva prioriza decisiones; la vista del analista agrega evidencia sin duplicar una herramienta externa.
7. Toda exportación respeta los mismos filtros y permisos de la pantalla.
8. Los datos operacionales y muestras no se envían al LLM. La IA recibe metadatos estructurales, perfiles agregados y decisiones autorizadas.

## 5. Seguridad y auditoría

Los permisos mínimos son `analytics.dashboard.read`, `reports.analytics.export`, `metadata.semantic_resolution.read` y `metadata.semantic_resolution.manage`. La API vuelve a verificar los permisos aunque la acción no esté visible. Se auditan exportaciones, diagnósticos abiertos, propuestas de corrección, decisiones, reejecuciones y cambios de configuración LLM. Las muestras de datos sólo se muestran a roles autorizados, se limitan en cantidad y nunca incluyen credenciales.

## 6. Condición de cierre

- [x] Las cinco especificaciones detalladas están implementadas y sus criterios disponen de pruebas o evidencia funcional controlada.
- [x] El dashboard no publica categorías técnicas como sustituto silencioso de nombres descriptivos.
- [x] La propuesta 54 supera reproducción determinística, calidad semántica y revisión humana.
- [x] La ejecución 7 reemplaza transaccionalmente el datamart defectuoso y conserva los expedientes 6 y 52 como trazabilidad.
- [x] PDF y Excel representan la vista autorizada con filtros, fecha, propuesta y ejecución.
- [x] El alcance académico elimina pronóstico, MAPE y RMSE y documenta la decisión del tutor.
- [x] Manual técnico, informe del Sprint 5, Capítulo III, bitácora y arquitectura quedan actualizados.
- [x] Pruebas automáticas, `make verify`, compilación documental y revisión visual finalizan sin errores.

## 7. Resultado de implementación

El incremento se cerró localmente sobre la propuesta 54 y la ejecución 7. El datamart conserva 121317 líneas conciliadas, 19820 clientes con nombre y tipo, moneda USD comprobada y siete indicadores disponibles. El dashboard, el copiloto contextual, PDF y Excel se validaron con Groq `openai/gpt-oss-120b`. La promoción a `develop` y `main` se realizará mediante los PR protegidos del flujo del repositorio.
