from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib
W=Path(__file__).resolve().parents[1]
I=json.loads((W/'insumos/inventario_postgresql_real.json').read_text())
L=json.loads((W/'insumos/linaje_ids_demostracion.json').read_text())
V=json.loads((W/'insumos/version_migracion_aplicada.json').read_text())
P={
'users':('Seguridad','La cuenta de una persona: identidad, estado de acceso y hash de contraseña.','Administración y acceso a la plataforma. No confundir al usuario de la aplicación con el usuario técnico de PostgreSQL o SQL Server.'),
'roles':('Seguridad','Agrupa responsabilidades de acceso, como administración, análisis o gerencia.','Administración de roles; el nombre visible no sustituye los permisos asignados.'),
'permissions':('Seguridad','Catálogo de operaciones que el servidor autoriza.','Permisos de lectura, escritura, revisión o ejecución según el módulo. Un menú visible no concede el permiso.'),
'user_roles':('Seguridad','Relaciona cuentas con roles mediante dos FK y una PK compuesta.','Asignar uno o varios roles a una cuenta; un rol puede pertenecer a varias cuentas.'),
'role_permissions':('Seguridad','Relaciona roles con permisos mediante dos FK y una PK compuesta.','Conceder a un rol las operaciones autorizadas.'),
'menus':('Seguridad','Define entradas de navegación, ruta, agrupación y orden.','La barra lateral muestra las opciones permitidas. La autorización efectiva se comprueba en FastAPI.'),
'menu_permissions':('Seguridad','Relaciona entradas de navegación con permisos.','Determina qué requisito de permiso acompaña a una entrada del menú; no es una asignación directa de menú a rol.'),
'audit_events':('Seguridad','Registra quién realizó una acción y sobre qué recurso, conservando contexto técnico.','Auditoría de operaciones. La columna detail es JSON, no JSONB; actor_user_id es la FK de usuario, pero resource_id es una referencia textual, no una FK universal.'),
'parameters':('Configuración y metadatos','Conserva parámetros del producto, su tipo y límites configurados.','Pantalla Parámetros. value se conserva como texto; el servidor interpreta el tipo y valida los límites.'),
'secrets':('Configuración y metadatos','Conserva valores cifrados de credenciales mediante ciphertext.','No se consultan sus valores desde la interfaz ni desde este inventario. La raíz de cifrado está en un volumen separado de PostgreSQL.'),
'llm_configurations':('Configuración y metadatos','Configura proveedor, modelo, endpoint, razonamiento y prueba de conectividad.','Pantalla Configuración IA. secret_id es opcional y único dentro de esta tabla; un proveedor local puede no necesitar API key.'),
'data_connections':('Configuración y metadatos','Identifica una fuente de datos, sus propiedades de conexión y la referencia a una credencial cifrada.','Pantalla Conexiones de datos y selector de fuente. Ambas conexiones pueden estar habilitadas; seleccionar una no fusiona sus datos.'),
'metadata_snapshots':('Configuración y metadatos','Guarda una captura estructural inmutable de una fuente y sus huellas.','Explorador de esquema. El JSONB describe tablas, columnas y relaciones declaradas de la fuente, no contiene filas de ventas.'),
'analysis_catalogs':('Configuración y metadatos','Guarda orientación funcional por conexión y dominio, con versión.','Catálogo analítico: preguntas de negocio y periodicidades. No define un modelo dimensional físico fijo. La combinación conexión/dominio es única.'),
'business_need_reviews':('Propuestas y ejecución','Conserva la evaluación previa de una necesidad, contexto y huellas.','Paso Necesidad. La revisión evalúa viabilidad antes de generar; no crea tablas ni garantiza la calidad de todos los datos.'),
'bi_proposals':('Propuestas y ejecución','Conserva versiones del diseño BI, sus documentos, proveedor, validación y revisión humana.','Asistente de datamart: conceptos, propuesta, personalización y revisión. Aprobar no ejecuta la carga. Una versión derivada enlaza con su origen mediante source_proposal_id.'),
'semantic_advice':('Propuestas y ejecución','Conserva asesoría contextual sobre un concepto de una propuesta.','Ayuda para una decisión semántica del diseño. No es una tabla de conversaciones completas del copiloto analítico.'),
'etl_executions':('Propuestas y ejecución','Conserva el expediente de preparación y ejecución: selección, plan, validación, métricas y fechas.','Datamart de ventas e historial de ejecuciones. El registro del expediente no es la tabla de hechos; los datos cargados viven en el esquema analítico de esa ejecución.')}
D={
'id':'Identificador interno de esta entidad; su PK distingue cada registro.',
'email':'Identificador de inicio de sesión; su índice único impide cuentas duplicadas con el mismo valor.',
'full_name':'Nombre visible de la persona de la cuenta.',
'password_hash':'Hash de contraseña, no contraseña en texto ni credencial recuperable. Este inventario sólo lee el nombre y tipo de la columna.',
'is_active':'Estado de habilitación del registro; su efecto depende de las reglas del módulo.',
'is_system_protected':'Marca de un registro base protegido para conservar administración y navegación esenciales.',
'code':'Código estable de la entidad; no depende de su etiqueta visible.',
'name':'Nombre o denominación visible en el módulo.',
'description':'Explicación de la entidad o parámetro.',
'user_id':'FK a app.users.id; identifica una cuenta en la tabla de asociación.',
'role_id':'FK a app.roles.id; identifica un rol en la tabla de asociación.',
'permission_id':'FK a app.permissions.id; identifica una operación autorizable.',
'menu_id':'FK a app.menus.id; identifica una entrada de navegación.',
'label':'Etiqueta de navegación que se presenta a la persona usuaria.',
'path':'Ruta de la pantalla; no es una credencial ni una regla de autorización.',
'position':'Orden de presentación dentro de la navegación.',
'module_code':'Código del módulo o agrupación funcional.',
'module_label':'Nombre visible de la agrupación de menús.',
'actor_user_id':'FK opcional al usuario que realizó la acción; ON DELETE SET NULL conserva el evento si se retira la cuenta.',
'actor_label':'Etiqueta histórica del actor. Es texto de evidencia y no otra FK.',
'action':'Código de la operación registrada en auditoría.',
'resource_type':'Clase de recurso afectado por la operación.',
'resource_id':'Identidad del recurso guardada como texto; PostgreSQL no la impone como FK a todas las tablas.',
'detail':'Documento JSON con detalle de auditoría; no se leyó su contenido.',
'key':'Clave única de un parámetro del producto.',
'value_type':'Tipo lógico con el que el servidor interpreta el valor textual.',
'value':'Valor del parámetro guardado como texto; no se extrajo su contenido.',
'default_value':'Valor previsto por defecto para el parámetro; no se extrajo su contenido.',
'min_value':'Límite inferior configurado para valores numéricos compatibles.',
'max_value':'Límite superior configurado para valores numéricos compatibles.',
'kind':'Clase de credencial cifrada.',
'ciphertext':'Contenido cifrado del secreto; no se leyó ni se incluye en los documentos.',
'provider_kind':'Tipo de proveedor de IA. En los expedientes conserva la procedencia como texto, sin FK a la configuración que después puede cambiar.',
'base_url':'Dirección del servicio de IA configurado; no se extrajo su valor.',
'model_id':'Identificador del modelo utilizado o configurado, distinto de una API key.',
'reasoning_level':'Nivel de razonamiento admitido por la configuración y el adaptador.',
'credential_reference':'Referencia técnica de la credencial; no equivale a una clave en texto.',
'secret_id':'FK a app.secrets.id. La credencial se recupera y descifra sólo bajo controles del servidor.',
'last_test_status':'Resultado de la última prueba de conexión del registro.',
'last_test_message':'Descripción del resultado de la última prueba; no se extrajo su texto.',
'last_tested_at':'Fecha de la última prueba de conectividad.',
'connector_kind':'Tipo de conector de la fuente; las dos fuentes ensayadas usan el adaptador SQL Server.',
'host':'Servidor de origen configurado; no se extrajo su valor.',
'port':'Puerto de la conexión de origen; no se extrajo su valor.',
'database_name':'Nombre de la base de origen. En una instantánea conserva la identidad de la captura.',
'username':'Cuenta técnica de lectura de la fuente; no es la cuenta con la que una persona entra a la aplicación. No se extrajo su valor.',
'encrypt':'Opción de cifrado de transporte hacia la fuente.',
'trust_server_certificate':'Opción de validación del certificado de la conexión de origen.',
'data_connection_id':'FK a app.data_connections.id; preserva el contexto de fuente.',
'connector_code':'Código del adaptador que realizó la captura estructural.',
'contract_version':'Versión del contrato estructural guardado; no es el número de propuesta ni de ejecución.',
'content_hash':'Huella del documento estructural canónico; permite detectar cambios y evitar duplicar capturas iguales.',
'schema_document':'JSONB de los metadatos de origen: estructura, tipos, claves y relaciones declaradas. No son filas de negocio.',
'schema_count':'Número de esquemas descritos en la instantánea de origen.',
'table_count':'Número de tablas descritas en la instantánea de origen.',
'column_count':'Número de columnas descritas en la instantánea de origen.',
'relationship_count':'Número de relaciones declaradas descritas; no cuenta ventas ni coincidencias de datos.',
'captured_by_user_id':'FK opcional al usuario que obtuvo la instantánea.',
'captured_by_label':'Etiqueta histórica de la persona que obtuvo la instantánea.',
'captured_at':'Fecha de captura de los metadatos.',
'domain_code':'Dominio analítico; ventas es el dominio implementado.',
'version':'Versión de configuración del catálogo; no representa un expediente de ejecución.',
'configuration_document':'JSONB de preguntas de negocio y periodicidades administradas para esta conexión y dominio.',
'updated_by_user_id':'FK opcional al usuario que actualizó el catálogo.',
'updated_by_label':'Etiqueta histórica de la persona que actualizó el catálogo.',
'metadata_snapshot_id':'FK a app.metadata_snapshots.id; enlaza el artefacto a una estructura de origen conservada.',
'input_hash':'Huella de entradas y contexto de la solicitud; no es el hash de contraseña de una persona.',
'assessment_hash':'Huella del resultado de la revisión previa.',
'assessment_document':'JSONB de la evaluación de viabilidad, sus requisitos y límites; no se ejecuta como SQL.',
'created_by_user_id':'FK opcional a la persona que creó el artefacto o expediente.',
'created_by_label':'Etiqueta histórica de la persona creadora.',
'source_proposal_id':'FK opcional a otra fila de app.bi_proposals; registra el origen de una versión derivada.',
'business_goal':'Necesidad comercial redactada o adoptada por la persona analista.',
'business_questions':'JSONB de las preguntas seleccionadas para esa necesidad.',
'requested_dimensions':'Campo JSONB conservado en el contrato histórico; no implica que el catálogo actual fije dimensiones predeterminadas.',
'periodicity':'Agrupación temporal solicitada; no cambia por sí sola el grano físico de las filas.',
'scope_document':'JSONB del alcance y contexto verificados para el diseño.',
'semantic_map_document':'JSONB de conceptos, explicaciones y correspondencias con la estructura.',
'status':'Estado del ciclo de vida del artefacto. Una propuesta aprobada no equivale a una ejecución terminada.',
'prompt_version':'Versión de las instrucciones utilizadas para preparar el artefacto.',
'proposal_document':'JSONB del diseño BI declarativo: hechos, dimensiones, medidas, indicadores y plan propuesto. No es el datamart cargado.',
'validation_document':'JSONB de comprobaciones, errores o advertencias del artefacto o ejecución.',
'review_comment':'Justificación o comentario de la revisión humana.',
'warnings_confirmed':'Indica si se confirmaron las advertencias sujetas a decisión humana.',
'reviewed_by_user_id':'FK opcional a la persona que revisó la propuesta; puede diferir de quien la creó.',
'reviewed_by_label':'Etiqueta histórica de la persona revisora.',
'reviewed_at':'Fecha de la decisión de revisión.',
'proposal_id':'FK a app.bi_proposals.id; vincula la asesoría o ejecución con una propuesta concreta.',
'concept_code':'Identificador del concepto sobre el que se pidió asesoría.',
'question':'Consulta contextual sobre un concepto del diseño.',
'response_document':'JSONB de la asesoría semántica; no se leyó su contenido.',
'builder_version':'Versión del constructor determinístico que preparó el plan de ejecución.',
'proposal_hash':'Huella del contrato de propuesta usado para la ejecución.',
'snapshot_hash':'Huella de los metadatos conservados utilizados para la ejecución.',
'selection_document':'JSONB de indicadores y decisiones seleccionados para materializar.',
'plan_document':'JSONB del plan compilado y su destino; el nombre de un esquema en un documento no constituye una FK de PostgreSQL.',
'metrics_document':'JSONB de métricas y comprobaciones de la carga; no contiene la tabla física de hechos.',
'started_at':'Fecha de comienzo de la ejecución.',
'finished_at':'Fecha de finalización de la ejecución.',
'created_at':'Fecha de creación del registro; su opcionalidad física consta en el inventario.',
'updated_at':'Fecha de actualización del registro; su opcionalidad física consta en el inventario.'}
areas=[]
for t in I['catalogo']['tables']:
 if t['schema_name']!='app':continue
 name=t['table_name'];area,purpose,operation=P[name]
 cols=[]
 for c in t['columns']:
  assert c['name'] in D, (name,c['name'])
  cols.append({**c,'explicacion':D[c['name']],'clave_primaria':any(k['kind']=='p' and c['name'] in k['columns'] for k in t['constraints']),'relaciones_fk':[r for r in I['relaciones_fisicas'] if r['child']=='app.'+name and c['name'] in r['child_columns']]})
 areas.append({'tabla':'app.'+name,'area':area,'que_guarda':purpose,'como_se_usa':operation,'numero_columnas':len(cols),'columnas':cols,'restricciones':t['constraints'],'indices_unicos':t['unique_indexes']})
sections=[
('Dos bases de datos con trabajos diferentes','SQL Server conserva las bases de demostración de origen. PostgreSQL conserva cuentas, configuración, metadatos, propuestas, expedientes y las tablas analíticas cargadas. Registrar una conexión no copia toda la base origen; obtener metadatos tampoco copia ventas. La aplicación lee datos autorizados cuando se confirma la carga. Cada ejecución nueva conserva su propio destino analítico.'),
('Base de datos, esquema, tabla y fila','bi_prototype es la base PostgreSQL auditada. Un esquema es un espacio de nombres dentro de esa base: app agrupa el estado de la plataforma; mart_ventas_e21 y mart_ventas_e22 separan resultados de ejecuciones. Una tabla contiene columnas y filas. Un esquema llamado mart_ventas_e22 no es otra base SQL Server ni un catálogo de preguntas.'),
('Qué se comprobó realmente','Se leyeron catálogos PostgreSQL en modo de solo lectura, no filas comerciales ni contenidos JSON. El inventario incluye 83 tablas y 782 columnas: 18 tablas de app con 174 columnas, 64 tablas analíticas y public.alembic_version. Hay 24 FK físicas, todas en app. Los nombres de columna de las 18 tablas coinciden con el ORM actual. Se cotejaron 19 archivos de migración; la tabla técnica informa la revisión aplicada '+', '.join(V)+'. Esto describe la estructura observada, no acredita por sí solo conciliación o exactitud de todas las cargas históricas.'),
('Claves primarias y claves foráneas','Una PK identifica una fila dentro de una tabla. Las tablas user_roles, role_permissions y menu_permissions usan PK de dos columnas: la pareja es única. Una FK comprueba que un valor hijo exista en una tabla padre. Por ejemplo, una ejecución debe referir una propuesta existente. No se deduce una FK porque una columna termine en _id.'),
('Cómo leer las cardinalidades','1 junto a la tabla padre significa que cada fila hija necesita un padre; 0..1 permite que la referencia sea nula. 0..* junto a la hija indica que un padre puede tener ninguna o muchas hijas. No se deduce que todos los padres ya tengan hijos. Un índice único completo sobre la FK limita a una hija por padre. Por eso secret_id es uno a uno opcional por cada tabla de configuración, pero la unicidad de data_connections y de llm_configurations no es una exclusión global entre ambas tablas.'),
('Autoría, roles y permisos','app.users identifica a la persona de la aplicación. user_roles la relaciona con uno o varios roles, y role_permissions relaciona esos roles con operaciones. menu_permissions vincula navegación con permisos. No existe una FK directa entre roles y menus. La persona puede ver una opción en React únicamente según sus permisos; FastAPI vuelve a comprobarlos antes de operar. Las FK de autoría son opcionales y usan SET NULL para preservar evidencia si se retira una cuenta; las reglas de sesión del servidor siguen siendo obligatorias.'),
('JSON y JSONB no son tablas separadas','JSONB almacena un documento estructurado en una columna: por ejemplo la definición de un catálogo o el contrato de una propuesta. JSON almacena el documento de detalle de auditoría. Estos documentos no se descomponen automáticamente en tablas con FK. Los nombres de tablas, rutas, identificadores o esquemas guardados dentro del documento se comprueban mediante reglas del servidor. No deben dibujarse como FK físicas. El inventario registra únicamente el tipo y nombre de esas columnas, sin leer su contenido.'),
('La revisión previa no está unida por una FK directa a la propuesta','business_need_reviews y bi_proposals apuntan a metadata_snapshots. El servidor comprueba entradas, huellas, actor y contexto al generar. No existe review_id en bi_proposals ni una FK que materialice la correspondencia entre ambos documentos. Esa parte de la trazabilidad es una regla de aplicación, complementaria a las restricciones SQL.'),
('Una propuesta y una ejecución no son lo mismo','bi_proposals guarda el diseño conservado y su decisión. etl_executions guarda un expediente que apunta por FK a esa propuesta y a sus metadatos. Una propuesta puede fundamentar cero o varias ejecuciones. Aprobar el diseño no llena fact_ventas; la materialización requiere la confirmación posterior y controles de conciliación.'),
('Cómo se conservan los resultados físicos','Los esquemas mart_ventas_e21 y mart_ventas_e22 existen en el catálogo y contienen dim_fecha, dim_producto, dim_cliente, dim_territorio y fact_ventas. Las dimensiones tienen PK surrogate_key. En la estructura observada, fact_ventas no tiene PK ni FK declaradas. Sus dim_*_sk se unen lógicamente con surrogate_key, y etl_execution_id es una etiqueta de ejecución sin FK a app.etl_executions. Las líneas discontinuas de sus diagramas no prometen restricciones que PostgreSQL no impone. El constructor y la conciliación deben comprobar esas correspondencias; la PK de una dimensión no demuestra por sí sola que todos los hechos tengan miembro válido.'),
('Por qué las columnas de ventas cambian entre fuentes','Los nombres y atributos físicos dependen del contrato aprobado. AdventureWorks conserva la identidad de pedido y detalle; WideWorldImporters conserva la identidad de línea de factura. Las dos demostraciones comparten el motor general, sin exigir nombres de tablas fuente iguales. Los esquemas físicos de ejecuciones anteriores son evidencia histórica; su mera existencia no garantiza que estén publicados o disponibles en el selector analítico.'),
('Cómo interpretar medidas y conteos','Una columna física llamada numero de pedidos o facturas distintas puede conservar el identificador documental de cada línea para que el lector calcule COUNT DISTINCT en el conjunto filtrado. No se debe sumar ese identificador ni sumar conteos de grupos que pueden repetir documentos. Para el importe promedio por documento, se divide el importe total entre los documentos distintos del filtro. Agrupar por mes no transforma la fila física en un resumen mensual.'),
('Asesoría del diseño y conversación analítica','semantic_advice conserva consultas sobre conceptos de una propuesta. El copiloto analítico conversa sobre agregados de una ejecución y sus filtros. La arquitectura documenta que no conserva el historial completo de chat en una tabla de mensajes: la auditoría registra huella y contexto mínimo. No debe presentarse semantic_advice como un almacén de todos los mensajes analíticos.'),
('Qué garantiza y qué no garantiza este inventario','La coincidencia entre ORM y catálogo acredita los nombres de columnas de app observados. Las FK físicas acreditan integridad referencial de esas relaciones SQL, no el significado comercial de cada importe o territorio. Los documentos JSON, el plan, la selección y los enlaces analíticos necesitan controles de aplicación. El manual debe enseñar a revisar tanto estructura como conciliación, contexto, moneda y denominadores, sin pedir a la persona usuaria que modifique estas tablas con SQL.')]
sections.append(('Una fotografía local, no un requisito del portable','Los 83 registros de tablas describen esta instalación con resultados históricos acumulados. Las 64 tablas analíticas no son un catálogo fijo que deba venir con el portable limpio: aparecen al materializar ejecuciones. El portable limpio conserva la estructura de app y el control de migraciones; los esquemas analíticos se generan después. Los identificadores de propuestas, instantáneas y ejecuciones también se asignan en cada instalación.'))
sections.append(('Roles observados y alcance de la comprobación','Se consultaron únicamente definiciones de roles y permisos, sin cuentas ni asignaciones de personas. En este corte existen Administrador, Operador, Analista BI y Gerente comercial. Gerente comercial tiene lectura analítica, lectura de conexiones, consulta de metadatos y exportación analítica. Consultar metadatos permite cargar el selector de fuentes y también abrir el explorador; no concede escritura ni ETL. Esta lectura de permisos no acredita que se haya iniciado sesión y completado el recorrido con cada perfil.'))
physical=[]
for t in I['catalogo']['tables']:
 if t['schema_name'] not in {'mart_ventas_e21','mart_ventas_e22'}:continue
 entries=[]
 for c in t['columns']:
  name=c['name']
  if name=='surrogate_key':desc='Clave sustituta interna de la dimensión; PK física.'
  elif name=='etl_execution_id':desc='Etiqueta de ejecución obligatoria; no tiene FK física a app.etl_executions.'
  elif name.startswith('dim_') and name.endswith('_sk'):desc='Referencia lógica a surrogate_key de una dimensión; puede ser nula y no tiene FK física.'
  elif name in {'anio','trimestre','mes','dia'}:desc='Componente de calendario derivado de la fecha seleccionada.'
  elif name in {'n_mero_de_pedidos_distintos','facturas_distintas'}:desc='Campo materializado para la medida documental: su receta puede calcular COUNT DISTINCT. No debe sumarse como si cada valor ya fuera un conteo.'
  elif t['table_name']=='fact_ventas':desc='Clave de trazabilidad o medida de origen seleccionada por el contrato de esta ejecución. Su significado y agregación se revisan en la propuesta; el nombre físico no acredita su semántica.'
  else:desc='Atributo de origen o etiqueta descriptiva seleccionada para esta dimensión. La propuesta y la evidencia definen su procedencia; no se deduce significado histórico únicamente del nombre.'
  entries.append({**c,'explicacion':desc})
 physical.append({'tabla':t['schema_name']+'.'+t['table_name'],'columnas':entries,'restricciones':t['constraints']})
result={'titulo':'Base de datos real explicada para el manual operativo','fecha':datetime.now(ZoneInfo('America/Guayaquil')).isoformat(),'fuente_inventario':'inventario_postgresql_real.json','sha256_inventario':hashlib.sha256((W/'insumos/inventario_postgresql_real.json').read_bytes()).hexdigest(),'estadisticas':{'tablas':83,'columnas':782,'tablas_app':18,'columnas_app':174,'tablas_analiticas':64,'fk_app':24,'fk_analiticas':0,'migraciones':19},'secciones':[{'titulo':a,'texto':b} for a,b in sections],'esquemas_observados':I['catalogo']['schemas'],'linaje_verificado_sin_json':L,'tablas_app':areas,'tablas_fisicas_demostracion':physical,'figuras_manifest':'../figuras/manifest_figuras_datos.json','limites':['Sin cambios de código, base, configuración ni contenedores.','Sin consulta de valores comerciales ni credenciales; solo catálogos y campos técnicos mínimos para linaje y revisión Alembic.','No se afirma una campaña operativa nueva de BI: los dos expedientes se identifican por sus estados técnicos conservados.']}
(W/'insumos/base_datos_manual.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
lines=['# La base de datos de la plataforma, desde cero','']
for heading,text in sections:lines+=['## '+heading,'',text,'']
lines+=['## Linaje observado, sin abrir documentos JSON','', '| Fuente | Conexión | Instantánea | Propuesta | Estado propuesta | Ejecución | Estado ejecución | Esquema físico observado |','| --- | --- | --- | --- | --- | --- | --- | --- |']
for r in L:lines.append('| '+ ' | '.join(str(v) for v in [r['database_name'],r['data_connection_id'],r['metadata_snapshot_id'],r['proposal_id'],r['proposal_status'],r['execution_id'],r['execution_status'],'mart_ventas_e'+str(r['execution_id'])])+' |')
lines+=['','Los identificadores son locales a esta instalación. Una réplica puede asignar otros números. No se debe seleccionar una ejecución por su número sin comprobar la fuente y el estado.','', '## Diccionario de las 18 tablas de la aplicación','']
for t in areas:
 lines+=['### '+t['tabla'],'',t['que_guarda'],'',t['como_se_usa'],'', '| Columna | Tipo físico | Admite nulos | Significado |','| --- | --- | --- | --- |']
 for c in t['columnas']:lines.append('| '+ ' | '.join([c['name'],c['type'],'Sí' if c['nullable'] else 'No',c['explicacion']])+' |')
 lines+=['']
lines+=['## Relaciones físicas completas de app','', '| Hija y columna | Padre | Padres por hija | Hijas por padre |','| --- | --- | --- | --- |']
for r in I['relaciones_fisicas']:lines.append('| '+ ' | '.join([r['child']+'.'+','.join(r['child_columns']),r['parent']+'.'+','.join(r['parent_columns']),r['parents_per_child'],r['children_per_parent']])+' |')
lines+=['','## Estructuras analíticas observadas','', '| Esquema | Tablas físicas |','| --- | --- |']
for s in I['catalogo']['schemas']:lines.append('| '+s['name']+' | '+str(s['table_count'])+' |')
lines+=['','El esquema mart inicial está vacío. mart_ventas es un destino legado; los mart_ventas_eN separan ejecuciones. mart_ventas_e17 contiene cuatro tablas: el inventario no permite inferir por sí solo la causa ni que ese expediente se publique. Para operar se utilizan el estado y el selector autorizado de la aplicación.','', '## Inserción de figuras','', 'Usar PDF vectorial o SVG a 23–25 cm en una página A4 horizontal; conservar proporción. A 23 cm la fuente interior mínima equivale a 10,87 puntos. Cada figura mide 13,33 cm de alto al insertarla a 25 cm. El PNG es un respaldo RGB opaco a 300 dpi. Los conectores continuos representan FK físicas; los discontinuos representan uniones lógicas sin FK. Las áreas ER_01 a ER_04 incluyen las 18 tablas y las 24 relaciones FK de app; sus campos son una selección legible, y este diccionario enumera las 174 columnas.','']
(W/'insumos/base_datos_manual.md').write_text('\n'.join(lines))
print('Diccionario: 18 entidades, 174 columnas, 24 FK; explicación y linaje técnico completos.')
