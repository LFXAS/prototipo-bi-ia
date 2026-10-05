# SPR-06-01 — Contexto multifuente SQL Server

## Objetivo

Permitir que una misma organización mantenga varias bases operacionales SQL Server
habilitadas al mismo tiempo y ejecute, para cada una, el ciclo completo y trazable:
metadatos, catálogo analítico, propuesta BI, aprobación, ETL y analítica.

La primera validación interoperable usa `AdventureWorks2022` y
`WideWorldImporters`. Ninguna regla funcional puede depender de esos nombres ni de
nombres concretos de tablas o columnas.

## Decisiones de arquitectura

1. **Disponibilidad no equivale a selección.** Una conexión habilitada puede ser
   utilizada por procesos nuevos; la fuente en contexto es una preferencia de la
   sesión del navegador y se envía explícitamente a la API.
2. **No existe una base activa global.** Dos analistas pueden trabajar sobre fuentes
   distintas sin cambiar el contexto del otro.
3. **La instantánea es la frontera de evidencia.** Toda propuesta conserva el
   `metadata_snapshot_id`, que a su vez identifica inequívocamente la conexión y la
   base de origen.
4. **Contrato universal, configuración aislada.** Todas las fuentes usan el mismo motor,
   las mismas reglas y el mismo contrato de ventas. Preguntas y periodicidades se guardan
   por `(data_connection_id, domain_code)` sólo para evitar que una configuración del
   analista afecte otro giro de negocio; esto no habilita código ni reglas particulares por
   nombre de base.
5. **ETL y analítica por expediente.** La ejecución usa siempre la conexión asociada a
   la instantánea aprobada. Los resultados analíticos exponen fuente, base, propuesta y
   ejecución para impedir mezclas silenciosas.
6. **Compatibilidad progresiva.** En este incremento se admite SQL Server. El contrato
   de selección es agnóstico al nombre de la base y prepara la incorporación posterior
   de otros conectores sin alterar el ciclo BI.

## Propiedad del catálogo y de la evidencia

El término **catálogo analítico** no significa que el LLM diseñe libremente el sistema ni
que exista una plantilla técnica copiada entre bases. Se separan cuatro responsabilidades:

| Responsable | Contenido | Regla de seguridad |
|---|---|---|
| Analista BI | Preguntas de negocio, etiquetas comprensibles y periodicidades que desea ofrecer en una fuente. | La configuración se guarda únicamente para `(data_connection_id, domain_code)`. |
| Plataforma | Tablas, columnas, PK, FK, tipos, rutas de unión, cardinalidad y evidencia disponible en la instantánea seleccionada. | Se vuelve a descubrir al cambiar la instantánea; no se hereda de otra fuente. |
| LLM | Sugerencias de necesidades desde el esquema, reformulación y análisis del objetivo, y propuesta explicada de dimensiones, medidas, KPI y transformaciones. | Sólo puede citar los metadatos entregados; su declaración de respaldo debe ser comprobada por el servidor. |
| Validadores determinísticos | Existencia, tipo, relación, unicidad, granularidad, fórmula, cobertura y trazabilidad. | Una propuesta inválida no puede aprobarse ni materializarse, aunque el proveedor la presente como correcta. |

La pantalla **Catálogo analítico** muestra ambos planos sin mezclarlos: arriba expone la
cobertura técnica calculada para la instantánea vigente y abajo permite administrar la
orientación funcional. Una capacidad aparece como verificable únicamente si existen
referencias actuales y coherentes con ventas. Tablas de compras, archivos históricos y
relaciones de auditoría como `CreatedBy`, `ModifiedBy` o `LastEditedBy` no se usan como
rutas de negocio sólo por acortar el grafo.

La línea base histórica contiene cuatro preguntas estándar definidas por el perfil del
producto: evolución temporal, desempeño por producto, cliente y territorio. No fueron
generadas por un LLM. En AdventureWorks, el analista añadió posteriormente dos preguntas
personalizadas —costos y rentabilidad, y ventas y costos por unidad— a partir de una
recomendación conversacional. Esas decisiones humanas no se copian a una nueva fuente:
cada conexión parte de la línea base y el analista decide si incorpora orientación adicional.

## Flujo funcional

1. El administrador registra y prueba una o más conexiones.
2. Las conexiones probadas se habilitan de manera independiente.
3. El usuario elige una fuente en el selector del espacio de trabajo.
4. El explorador captura o consulta exclusivamente las instantáneas de esa fuente.
5. El catálogo analítico se consulta y personaliza exclusivamente para esa fuente.
6. La cobertura técnica del catálogo se recalcula contra la instantánea vigente; la IA
   no decide por sí sola qué capacidades existen.
7. El asistente permite escribir, reformular o elegir una necesidad sugerida desde la
   instantánea vigente de la fuente elegida. El analista autoriza el destino LLM visible
   antes de enviar estructura; adopta el texto explícitamente y obtiene una revisión
   IA/reglas persistida antes de generar. La sugerencia no cambia el catálogo por fuente.
8. La propuesta aprobada conserva la procedencia y el ETL usa esa conexión, aunque
   existan otras fuentes habilitadas.
9. Analítica filtra los expedientes por fuente y permite cambiar de contexto sin
   eliminar ni desactivar las demás bases.
10. Al cambiar la fuente, la interfaz descarta inmediatamente tablero, filtros, chat y
    solicitudes pendientes del contexto anterior. No vuelve a mostrar resultados hasta
    que la API confirme conjuntamente `connection_id` y `execution_id`.
11. Inicio muestra la misma fuente seleccionada para el espacio de trabajo y consulta su
    preparación mediante `connection_id`; no puede presentar el estado de otra conexión.
12. El explorador muestra siempre la versión de metadatos vigente, aunque exista una sola,
    y al cambiar de fuente descarta búsqueda, tabla, detalle, paginación, mensajes y
    respuestas pendientes del contexto anterior.
13. La migración al catálogo por fuente conserva en la conexión preexistente las preguntas
    personalizadas del catálogo legado. Una fuente añadida después parte del contrato
    universal sin heredar personalizaciones de otra empresa o base.

## Contratos API

| Operación | Contrato |
|---|---|
| `GET /api/v1/sources` | Lista fuentes habilitadas/probadas y su última instantánea. |
| `GET /api/v1/sources/{id}` | Devuelve una fuente concreta sin secretos. |
| `POST /api/v1/metadata/snapshots?connection_id={id}` | Captura metadatos de la fuente indicada. |
| `GET /api/v1/metadata/snapshots?connection_id={id}` | Lista instantáneas de la fuente indicada. |
| `GET /api/v1/copilot/readiness?connection_id={id}` | Valida preparación del contexto elegido. |
| `POST /api/v1/copilot/needs/suggest` | Usa la instantánea vigente y el catálogo de su conexión; devuelve necesidades con evidencia, límites y posibilidad de adopción. |
| `POST /api/v1/copilot/needs/formulate` | Reformula el objetivo bajo los límites de esa misma instantánea. |
| `POST /api/v1/copilot/needs/viability` | Persiste la revisión IA/reglas del actor, instantánea y entrada; devuelve una huella exigida al generar. |
| `GET /api/v1/copilot/catalog?...` | Exige que la instantánea pertenezca a la fuente indicada. |
| `GET/PUT /api/v1/analysis-catalog/domains/{code}?connection_id={id}` | Catálogo aislado por fuente. |
| `GET /api/v1/copilot/proposals?connection_id={id}` | Versiones generadas para la fuente. |
| `GET /api/v1/etl/proposals?connection_id={id}` | Propuestas materializables para la fuente. |
| `GET /api/v1/analytics/executions?connection_id={id}` | Expedientes conciliados de la fuente. |
| `GET /api/v1/analytics/dashboard?connection_id={id}&execution_id={execution}` | Tablero sólo si la ejecución pertenece a la fuente indicada. |
| `POST /api/v1/analytics/copilot` | Exige `data_connection_id` y rechaza una ejecución de otra fuente. |
| `GET /api/v1/analytics/reports/{format}?connection_id={id}&execution_id={execution}` | Exporta exclusivamente el tablero validado para esa fuente. |

## Reglas y criterios de aceptación

- Activar una conexión no desactiva otras.
- No se aceptan identificadores de conexión inexistentes, deshabilitados o no probados.
- Una instantánea sólo puede usarse con la conexión a la que pertenece.
- Sugerencias, reformulación y revisión previa usan únicamente los metadatos de esa
  instantánea. No pueden incorporar columnas, relaciones ni evaluaciones de otra fuente.
- La generación exige una revisión persistida del mismo actor, objetivo, preguntas,
  período e instantánea. Cambiar de fuente o necesidad invalida la revisión y descarta
  respuestas en curso; un borrador restaurado no restaura consentimiento de envío.
- Una revisión anterior a la versión de reglas vigente no habilita otra generación:
  `need-review-2` conserva registros históricos, pero exige reevaluar. Las
  comprobaciones de roles precio/costo/tasa/importe y de agrupación temporal son las
  mismas para ambas fuentes; un nombre nuevo no se considera semánticamente conocido
  sólo por tener un tipo compatible.
- El consentimiento de metadatos se vincula a configuración, proveedor, URL y modelo.
  Si cambia el destino debe renovarse antes de cualquier llamada de asesoría.
- Un catálogo personalizado en una fuente no cambia el catálogo de otra.
- Restaurar el catálogo de una fuente recupera su configuración funcional validada,
  pero nunca copia tablas, columnas ni relaciones desde otra base.
- Las preguntas personalizadas de una fuente no aparecen automáticamente en otra; su
  incorporación requiere una decisión explícita del analista y evidencia técnica vigente.
- Toda pregunta estándar comunica su evidencia técnica actual o indica que no está
  disponible. Las preguntas personalizadas continúan siendo orientación de negocio y
  no convierten una referencia inexistente en capacidad técnica.
- Las propuestas, ejecuciones y tableros muestran el nombre de la fuente y la base.
- Tablero, copiloto y exportación rechazan una combinación
  `connection_id`--`execution_id` que no pertenezca al mismo expediente.
- Una respuesta tardía de la fuente anterior no puede reemplazar el tablero de la
  fuente actualmente seleccionada. Durante el cambio se muestra un estado de carga sin
  conservar gráficos, filtros ni conversación anteriores.
- Una respuesta tardía de otro módulo, por ejemplo Roles, tampoco puede
  tratarse como metadatos al navegar hacia Explorador: cada pantalla renderiza
  únicamente el resultado correspondiente a su solicitud vigente.
- El aislamiento técnico no basta para equivalencia comercial: si una fuente
  dispone de pedidos y facturas como eventos distintos, el contrato conserva
  cuál fue materializado y bloquea una solicitud explícita de facturación
  construida sobre pedidos. El control depende de metadatos y relaciones,
  nunca del nombre configurado de la conexión.
- Las preguntas sugeridas del copiloto son neutrales o se construyen con filtros reales
  del tablero; no incluyen territorios fijos procedentes de otra base demostrativa.
- La sugerencia sobre el territorio líder usa el primer territorio verificado del tablero
  de la fuente activa. Si el usuario escribe la expresión genérica "territorio líder", la
  plataforma la resuelve determinísticamente antes de ejecutar la agregación segura.
- Inicio, Explorador de esquema, Catálogo analítico, Asistente, Generación de datamart y
  Analítica identifican explícitamente la fuente activa y conservan el mismo contexto al
  navegar entre módulos.
- Una búsqueda o tabla válida en la fuente anterior no genera el mensaje "Tabla no
  encontrada" después del cambio: el estado dependiente de la instantánea se reinicia.
- El selector "Versión de metadatos" es visible con una o varias instantáneas; queda
  deshabilitado cuando sólo existe una opción, sin ocultar la trazabilidad.
- AdventureWorks conserva las preguntas personalizadas "Costos y rentabilidad de las
  ventas" y "Ventas y costos por unidad" migradas desde el catálogo previo. La conexión
  WideWorldImporters mantiene su catálogo propio y editable.
- AdventureWorks y WideWorldImporters pueden coexistir en el mismo contenedor y usar
  el mismo inicio de sesión de sólo lectura.
- El código de descubrimiento, propuesta, ETL y analítica no contiene bifurcaciones por
  nombre de conexión, base, esquema, tabla o columna. Las dos bases son casos de prueba
  del mismo comportamiento universal.
- Un importe puede ser directo o derivarse de componentes conectados y verificables
  (por ejemplo, precio por cantidad); la plataforma informa la fórmula y nunca asume una
  columna concreta por pertenecer a una base conocida.
- Las dimensiones exigidas por una necesidad viable se incorporan desde evidencia
  directa o derivable aunque el LLM omita alguna; una omisión del proveedor no elimina
  silenciosamente el requisito.
- Las columnas numéricas de identificación no se envían a revisión de traducción como
  categorías. La localización semántica sólo procesa atributos textuales.
- Analítica utiliza la etiqueta descriptiva materializada para filtros y gráficos y
  conserva internamente la clave para la trazabilidad.
- El respaldo oficial de WideWorldImporters se restaura de forma idempotente; no se
  almacena el archivo binario en Git.
- Las fuentes externas respetan íntegramente la seguridad definida por su DBA. El
  contenedor demostrativo de WideWorldImporters incorpora al lector de prueba en los
  roles de ventas existentes para que las políticas de seguridad por fila no oculten
  entidades necesarias durante la validación académica.
- No se exponen credenciales en respuestas, registros, documentación ni auditoría.
- Las pruebas cubren aislamiento de fuentes, pertenencia de instantáneas, catálogo por
  fuente, selección ETL, rechazo de relaciones de auditoría, etiquetas descriptivas,
  filtrado analítico, respuestas tardías y rechazo cruzado en tablero, reportes y chat.

## Escenarios integrales de aceptación

| ID | Escenario | Evidencia mínima | Resultado esperado |
|---|---|---|---|
| MS-E2E-01 | Navegar Inicio → metadatos → catálogo → asistente → ETL → analítica en AdventureWorks. | Capturas con fuente, instantánea, catálogo, expediente y tablero. | Todos los módulos permanecen en la conexión 1 y usan su ejecución conciliada. |
| MS-E2E-02 | Repetir el flujo con WideWorldImporters. | Capturas equivalentes y valores propios de WWI. | Todos los módulos permanecen en la conexión 2 y usan su ejecución conciliada. |
| MS-E2E-03 | Cambiar AW → WWI → AW desde explorador y analítica. | Estado de carga y pantalla final por transición. | No quedan tabla, error, filtro, conversación, producto ni territorio de la fuente anterior. |
| MS-E2E-04 | Consultar una ejecución con el `connection_id` de la otra fuente. | Prueba automatizada del contrato. | La API rechaza la combinación con 409. |
| MS-E2E-05 | Revisar catálogos por fuente. | Preguntas y periodicidades visibles. | AW conserva seis preguntas; WWI dispone de su configuración independiente. |
| MS-E2E-06 | Exportar PDF y Excel desde cada ejecución. | Archivos abiertos y datos de cabecera verificados. | Cada reporte identifica únicamente su fuente, ejecución, filtros y métricas. |
| MS-E2E-07 | Consultar al copiloto analítico en cada fuente. | Pregunta, respuesta y procedencia. | La consulta usa el expediente activo y no incorpora categorías de la otra base. |
| MS-E2E-08 | Escribir “territorio líder” sin seleccionar manualmente un territorio. | Alcance, Top 5 y denominador de cada fuente. | La plataforma resuelve el líder desde el ranking conciliado vigente antes de ejecutar la agregación segura. |
| MS-E2E-09 | Abrir y verificar propuestas históricas con ETL conciliado. | Estados antes/después, expediente y cabecera de analítica. | La consulta no retira aprobaciones; Datamart y Analítica conservan la misma pareja ejecución–propuesta. |
| MS-E2E-10 | Crear facturación nueva cuando ya existe un datamart de pedidos en la misma conexión. | Fuente del hecho, fecha, sumas, conteo documental y capturas de ambas ejecuciones. | Ambos expedientes persisten separados; el panel no confunde pedido, factura ni impuesto. |
| MS-E2E-11 | Sugerir o reformular una necesidad y revisar su viabilidad en ambas fuentes. | Proveedor/modelo autorizado, instantánea, texto adoptado, referencias y limitaciones, evaluación persistida y capturas. | Cada necesidad usa sólo su fuente; los fallos se conservan como tales y no alteran propuestas ni ETL anteriores. |
| MS-E2E-12 | Cambiar de fuente o destino LLM mientras existe una revisión o respuesta pendiente. | Pruebas de estado y consentimiento. | Se descarta el resultado anterior; generar requiere revisión y consentimiento vigentes. |

## Evidencia integral del 1 de octubre de 2026

La misma implementación se probó sin bifurcaciones por nombre de base con
AdventureWorks2022 y WideWorldImporters. Para WideWorldImporters, la propuesta 96 fue
generada con Claude Haiku 4.5, corregida por reglas comunes y aprobada tras cubrir los
requisitos viables. La ejecución 13 produjo los siguientes resultados:

| Control | Resultado |
|---|---:|
| Líneas de origen / datamart | 231.412 / 231.412 |
| Diferencia | 0 |
| Pedidos distintos | 73.595 |
| Unidades | 9.310.904 |
| Ventas | 177.634.276,40 en moneda de origen |
| Costo | 88.904.313,90 en moneda de origen |
| Margen bruto | 88.729.962,50 en moneda de origen |
| Margen bruto porcentual | 49,9509 % |
| Calidad descriptiva | 227 productos, 663 clientes y 53 territorios con etiqueta |

La moneda permanece como **moneda de origen** porque la fuente no aportó evidencia ISO
inequívoca; el sistema no inventó USD. El descuento quedó documentado como no disponible
porque no existía una fuente demostrable. En el tablero, los territorios se presentan por
nombre (por ejemplo, Texas o California), no por su identificador numérico.

### Verificación de aislamiento analítico

La inspección física confirmó que la ejecución 12 de AdventureWorks usa el esquema
`mart_ventas_e12` con 121.317 filas, mientras la ejecución 13 de WideWorldImporters usa
`mart_ventas_e13` con 231.412 filas y columnas propias. La prueba funcional cambió el
contexto WideWorldImporters → AdventureWorks → WideWorldImporters: en cada transición se
limpió el tablero y sólo se publicaron la ejecución, productos, territorios y métricas de
la fuente confirmada por la API. También se automatizó una respuesta tardía de la fuente
anterior y se comprobó que no puede sustituir el tablero vigente.

La ejecución formal de MS-E2E-01 a MS-E2E-09, incluidas las capturas, conciliaciones,
exportaciones y defectos corregidos, se conserva en
`docs/testing/Informe_pruebas_integrales_multifuente.pdf`. El informe limita la afirmación
de universalidad al alcance demostrado: dos fuentes SQL Server del dominio ventas.

### Auditoría adicional del 3 de octubre de 2026

Se completó MS-E2E-10 con la propuesta WWI #114 y la ejecución #15, sin modificar
la histórica #13. El hecho nuevo procede de líneas de factura, su período usa
la fecha de factura y la conciliación registró 228.265 filas a cada lado,
70.510 facturas y 198.043.439,45 de importe con impuesto. El importe antes de
impuesto calculado por precio por cantidad (172.261.341,20) y el impuesto
(25.782.098,25) se mantuvieron conceptualmente separados. El tablero permite
volver a #13, cuyo alcance sigue siendo pedidos, y a AdventureWorks #14 sin
retener valores o filtros de otra fuente. La respuesta contextual de Claude
para 2015 coincidió con el expediente #15 y distinguió facturación de cobro.
Las capturas y escenarios están en `docs/testing/auditoria-operativa-2026-10-03.md`.

La ampliación posterior del asesor de necesidades se evalúa separadamente de ese
ciclo ETL. El ensayo autorizado con Claude generó dos sugerencias estructuralmente
usables en AdventureWorks, pero con afirmaciones incorrectas sobre estados; en una
repetición de WideWorldImporters generó una usable y otra bloqueada. Se detectaron
además confusión de precio de venta con costo y una agrupación temporal presentada
como derivación aritmética, que motivaron controles comunes de significado y
feedback acotado. El cierre posterior es funcional y supervisado: no acredita que
toda la explicación del LLM sea correcta ni que estas pruebas hayan repetido otro ETL.

La repetición correctiva de WWI sobre importe mensual de líneas de factura produjo
seis directos, dos derivables, cuatro límites de interpretación y cero requisitos no
disponibles. Se comprobó la habilitación de generar únicamente tras aceptación
explícita de los límites, sin crear otra propuesta ni carga. Una necesidad de clima
externo no se consideró cubierta por los sensores internos existentes y permaneció
bloqueada sin aceptar alcance parcial. Los escenarios y capturas se conservan en la
misma auditoría; el resultado corresponde únicamente al objetivo y contexto probados.

AdventureWorks cerró la revisión del objetivo original con once directos, uno
derivable, cinco ambiguos o advertencias y cero no disponibles. Aceptar los cinco
límites habilitó generar sin crear propuesta. Su reformulación permaneció no
utilizable por una capacidad `other` sin validador tras dos intentos; se verificó
la alternativa de conservar la redacción del analista. Ambas fuentes alcanzaron
la aceptación funcional supervisada de la puerta previa, no una garantía de
reformulación exitosa ni otro ciclo completo de BI/ETL.

## Fuera de alcance

- Pronósticos o modelos de *forecast*.
- Unificación de hechos entre bases distintas.
- Conectores distintos de SQL Server en este incremento.
- Inferencia de equivalencias entre catálogos de negocios diferentes.
