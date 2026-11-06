from pathlib import Path
import json,re,copy,hashlib
B=Path(__file__).resolve().parent
original=json.loads((B/'ingenieria_actualizada.json').read_text())
# Códigos y nombres de rutas permanecen en el control de autoría; el capítulo usa nombres completos.
replacements=[
 (r'CP-ACT-(\d{2})',lambda m:f'Prueba {int(m[1])}'),
 (r'RNF-?(\d{2})',lambda m:f'Requisito no funcional {int(m[1])}'),
 (r'RF-?(\d{2})',lambda m:f'Requisito funcional {int(m[1])}'),
 (r'CU-(\d{2})',lambda m:f'Caso de uso {int(m[1])}'),
 (r'HU-(\d{2})',lambda m:f'Historia de usuario {int(m[1])}'),
 (r'SPR-(\d{2})(?![-\d])',lambda m:f'Sprint {int(m[1])}'),
]
words={
 'CI/CD':'integración y entrega continuas', 'PK/FK':'claves principales y relaciones declaradas',
 'need-review-6':'revisión de necesidad vigente','sales-bi-v7':'contrato vigente de propuesta',
 'role_ids':'identificadores de roles','source_proposal_id':'referencia a la propuesta original',
 'data_connection_id':'identificación de la fuente','connection_id':'identificación de la fuente',
 'metadata_snapshot_id':'versión de metadatos asociada','etl_execution_id':'identificación de la ejecución',
 'mart_ventas_e{id}':'un esquema independiente para cada ejecución','mart_ventas':'el esquema analítico anterior',
 'fact_ventas':'la tabla de hechos de ventas','surrogate_key':'clave sustituta','<alias_dimensión>_sk':'referencias a las dimensiones',
 'MS-E2E03/04':'pruebas de cambio de fuente y rechazo de ejecuciones ajenas',
 'PREP-02/03':'pruebas de preparación de ambas fuentes','CAT-01':'prueba del catálogo',
 'snapshot':'versión de metadatos','payload':'contenido enviado','endpoint':'operación del servidor',
 'dashboards':'paneles analíticos','dashboard':'panel analítico','forecast':'pronósticos',
 'rate_limit_exceeded':'límite de cuota del proveedor','retry_after':'espera indicada',
 'Top N':'ranking de las primeras categorías','commit':'revisión del código',
 'La API':'El servidor','la API':'el servidor','en FastAPI':'en el servidor',
}
whole={
 'JWT':'token de sesión firmado','RBAC':'control de acceso por roles y permisos',
 'LLM':'modelo de lenguaje','LLMs':'modelos de lenguaje','ETL':'carga de datos',
 'KPI':'indicadores','SDD':'desarrollo guiado por especificaciones',
 'BI':'inteligencia de negocios','IA':'inteligencia artificial',
 'AW':'AdventureWorks','WWI':'WideWorldImporters','OLTP':'sistema transaccional de origen',
 'PK':'clave principal','FK':'relación entre tablas','DDL':'definición física de las tablas',
 'ORM':'modelo de persistencia de la aplicación','JSONB':'documentos estructurados',
 'JSON':'documentos estructurados','XLSX':'Excel','CDC':'captura automática de cambios',
 'GHCR':'registro de imágenes de la aplicación','API':'servidor',
}
def clear(text):
 if not isinstance(text,str):return text
 s=text
 # Primero se sustituyen los identificadores de campos, antes de abreviaturas genéricas.
 for a,b in sorted(words.items(),key=lambda x:-len(x[0])):s=s.replace(a,b)
 for a,b in whole.items():s=re.sub(r'\b'+re.escape(a)+r'\b',lambda m:b,s)
 for pat,fn in replacements:s=re.sub(pat,fn,s)
 s=s.replace('Prueba 12 yRequisito no funcional 1','Prueba 12 y requisito no funcional 1')
 s=s.replace('La servidor','El servidor').replace('la servidor','el servidor')
 s=s.replace('configuración modelo de lenguaje','configuración del modelo de lenguaje')
 s=s.replace('prueba modelo de lenguaje','prueba del modelo de lenguaje')
 s=s.replace('Analista inteligencia de negocios','Analista de inteligencia de negocios')
 s=s.replace('Proveedor modelo de lenguaje','Proveedor de inteligencia artificial')
 s=s.replace('operación del servidor permitido','dirección permitida del servicio del proveedor')
 s=s.replace('operación del servidor permitidos','dirección permitida del servicio del proveedor')
 s=s.replace('compilation_rules_version=3','las reglas vigentes de compilación')
 s=s.replace('ready_for_review','lista para revisión')
 s=s.replace('analytics.panel analítico.read y reports.analytics.export','los permisos de consulta del panel y de exportación de informes')
 s=s.replace('reglas 3','reglas de validación actuales').replace('reglas 2','reglas anteriores conservadas')
 s=s.replace('v4/v5','revisiones anteriores').replace('v6/','revisión vigente y ')
 # Huellas técnicas y versiones de implementación se conservan sólo en control_interno.
 s=re.sub(r';?\s*huella(?: del contrato)?\s+[0-9a-f]{10,64}\s*reproducida sin diferencias\.', '; reproducción del contrato sin diferencias.',s,flags=re.I)
 s=s.replace('huella b5872c3bbd6d reproducida sin diferencias','reproducción del contrato sin diferencias')
 s=s.replace('Contratos históricos preservados','Contratos históricos preservados')
 return s

def recursive(v):
 if isinstance(v,str):return clear(v)
 if isinstance(v,list):return [recursive(x) for x in v]
 if isinstance(v,dict):return {k:recursive(x) for k,x in v.items()}
 return v
r=recursive(copy.deepcopy(original))
r['control_interno']={
 'advertencia':'No imprimir este apartado en el cuerpo del capítulo. Conserva códigos, fuentes, revisiones y métricas originales para trazabilidad.',
 'sha256_ingenieria_origen':hashlib.sha256((B/'ingenieria_actualizada.json').read_bytes()).hexdigest(),
 'corte_original':original['corte'],'fuentes_tecnicas':original['fuentes'],
 'registros_originales':{k:original[k] for k in ['RF','RNF','casos_uso','historias_usuario','sprints','matriz_trazabilidad','plan_pruebas_actualizado','casos_verificados','comparacion_proveedores']},
}
r['corte']={'fecha_documental':'6 de noviembre de 2026','tests_backend':454,'tests_frontend':48,
 'verificacion':'Las suites documentadas completaron 454 pruebas del servidor y 48 de la interfaz; la actualización del capítulo no vuelve a ejecutarlas.',
 'natural':'La evidencia histórica de cargas y conversaciones conserva el alcance de las versiones con las que se obtuvo. Esta revisión es documental.'}
r['introduccion']='La ingeniería de software comprende seis incrementos documentados y sus correcciones posteriores. Las especificaciones describen las funciones, sus condiciones de aceptación y la evidencia disponible. La aplicación separa las fuentes de datos y los proveedores de inteligencia artificial mediante un contexto identificado y reglas comunes de validación. La comprobación funcional disponible corresponde al dominio de ventas y a dos bases SQL Server; otros motores requieren un conector y pruebas propias.'
for key,prefix in [('RF','Requisito funcional'),('RNF','Requisito no funcional'),('casos_uso','Caso de uso'),('historias_usuario','Historia de usuario')]:
 for n,x in enumerate(r[key],1):
  raw=original[key][n-1]
  x['id']=raw['id'] # exclusivamente control; para el capítulo usar etiqueta
  x['etiqueta']=f'{prefix} {n}'
  if 'nombre' in x:x['nombre']=re.sub(r'^(?:Caso de uso|Historia de usuario) \d+\.\s*','',x['nombre'])
  if 'fuentes_SDD' in x:x['fuentes_SDD']='Especificaciones del proyecto y pruebas relacionadas; referencias técnicas conservadas en el control de autoría.'
  if 'estado' in x:x['estado']='Implementado; alcance de verificación indicado en el plan de pruebas.'
  if 'campos' in x:
   x['campos']['Trazabilidad']=clear(raw['campos'].get('Trazabilidad','')).replace('Especificaciones heredadas de los RF relacionados.','Especificaciones de los requisitos relacionados.')
   if 'Permisos' in x['campos']:x['campos']['Permisos']=x['campos']['Permisos'].replace('servidor','operación')
for n,x in enumerate(r['sprints'],1):
 x['sprint']='Sprint '+str(n) if n<=6 else 'Correcciones posteriores al Sprint 6'
 x['etiqueta']=x['sprint'];x['identificador_interno']=original['sprints'][n-1]['sprint']
 x['evidencia']='Informe del incremento, especificaciones y revisiones del proyecto.'
 if n==7:
  x['incremento']='Revisión previa de necesidades, validación de cálculos, conservación de propuestas históricas, formularios protegidos, periodicidad, unidades, procedencia de las respuestas y exportaciones. Manual de formación de 464 páginas.'
  x['limite']='Corresponde al cierre correctivo del sexto incremento; no constituye un séptimo sprint. Esta actualización documental no ejecuta nuevas cargas ni conversaciones.'
for n,x in enumerate(r['plan_pruebas_actualizado'],1):
 x['id']=original['plan_pruebas_actualizado'][n-1]['id'];x['etiqueta']='Prueba '+str(n)
 x['fuentes']='Registro de pruebas y evidencias del manual; fuentes técnicas conservadas en el control de autoría.'
for n,x in enumerate(r['casos_verificados'],1):
 x['etiqueta']='Caso demostrado '+str(n)+' en '+('AdventureWorks' if n==1 else 'WideWorldImporters')
 x['evidencia']='Registro de pruebas del manual y verificación del expediente; el contrato se reprodujo sin diferencias.'
 x['version_review']='Revisión histórica de la necesidad conservada con el expediente.'
 x['reglas_compilacion']='Reglas históricas conservadas, distintas de las reglas actuales.'
r['fuentes']=['Especificaciones funcionales del proyecto','Arquitectura y alcance implementado','Informes de los seis incrementos','Registro de pruebas del manual de formación','Informe de pruebas posteriores al cierre','Modelo de persistencia y materializador de datos']
r['precauciones_editoriales']=['Las fechas de los informes pueden solaparse debido a revisiones acumulativas; no representan actas de reuniones no disponibles.','Las historias y tablas son una organización académica de funciones implementadas, sin atribuirles un historial de estimaciones que no esté documentado.','Esta revisión del capítulo no añade pruebas operativas ni atribuye a las cargas anteriores las reglas introducidas posteriormente.']
r['actualizaciones_frente_Oct18']=[
 'Se reemplaza la tabulación simulada por las 102 respuestas reales de la encuesta de necesidad y utilidad.',
 'Se incorporan las condiciones verificables de las funciones, los seis incrementos y las correcciones posteriores al cierre.',
 'Se precisan la separación de fuentes, la revisión de necesidades, la confirmación de la carga y la procedencia de los resultados.',
 'Se presentan las evidencias de 454 pruebas del servidor y 48 de la interfaz, sin afirmar que se ejecutaron otra vez al editar el capítulo.',
 'Se explican las limitaciones de las comparaciones entre proveedores y de las pruebas autenticadas de cada perfil.',
 'Se sustituyen etiquetas técnicas opacas por nombres completos y diagramas conceptuales legibles.',
]
r['comparacion_proveedores'][1]['incidencia']='La cuota disponible impidió completar la solicitud en tres reintentos; el proveedor indicó un límite de texto y una espera de 47 segundos. No se obtuvo revisión ni propuesta en ese intento.'
r['comparacion_proveedores'][0]['comprobacion']='Conectividad y recorridos operativos con AdventureWorks y WideWorldImporters, incluidas propuestas, conciliación y copiloto contextual.'
r['diseno_datos']=[
 'Cada conexión puede tener varias versiones de metadatos. Una propuesta utiliza una versión de metadatos identificada y cada ejecución se vincula con su propuesta y con esa misma versión. El catálogo pertenece a una fuente y un dominio. Una propuesta corregida conserva la referencia a su versión de origen.',
 'La revisión de necesidad se almacena por separado y conserva la referencia a los metadatos utilizados. Las credenciales de conexiones y proveedores se guardan cifradas en un recurso separado de los datos de configuración.',
 'Cada carga crea un esquema analítico independiente. Las dimensiones incluyen una clave sustituta, la clave del origen y los atributos aprobados. La tabla de hechos conserva las claves del origen, las medidas aprobadas, las referencias a dimensiones y la identificación de la ejecución.',
 'El modelo estrella expresa relaciones lógicas verificadas. El materializador actual no crea una clave principal física ni restricciones de relación en la tabla de hechos; sus referencias dimensionales permiten valores vacíos. Esta condición exige controles de integridad y no debe confundirse con una garantía física inexistente. Las dimensiones y medidas dependen de cada propuesta aprobada.',
]
r['metodo_desarrollo'][1]='Las especificaciones en archivos Markdown describen el problema, el alcance, los contratos, la interfaz, la seguridad y los criterios de aceptación. El control de versiones y las solicitudes de integración conservan su relación con los cambios. Las historias presentadas organizan académicamente los requisitos implementados; no acreditan reuniones ni un registro histórico de estimaciones ausente.'
r['metodo_desarrollo'][2]='Una funcionalidad se considera terminada cuando cumple sus criterios, supera las pruebas necesarias y cuenta con documentación actualizada. Los controles de integración compilan y verifican el proyecto; la publicación distribuye cinco imágenes de la aplicación. La incorporación al desarrollo se revisa antes de promover la versión estable. El despliegue acreditado es local y no se atribuye un despliegue en una nube comercial.'
r['limites_IA'][2]='La revisión distingue lo que se solicita de lo que se excluye. Las reglas actuales evitan interpretar identificadores como importes, comprueban los cálculos y conservan la población documental. Las dos cargas demostradas pertenecen a revisiones anteriores conservadas; no se presentan como pruebas retrospectivas de las reglas nuevas.'

# Las tablas principales muestran trazabilidad por nombres, no rutas de archivos ni códigos de pruebas heredados.
evidence_names=[
 'Pruebas de autenticación y administración. Sigue pendiente una campaña completa con cuentas propias de cada perfil.',
 'Pruebas de conexión a fuentes y de almacenamiento cifrado de credenciales.',
 'Pruebas de cambio de fuente, aislamiento de resultados y comportamiento del panel.',
 'Pruebas de captura y exploración de estructura, con tablas y relaciones separadas por fuente.',
 'Pruebas de configuración de preguntas y opciones del catálogo, sin alterar su identidad.',
 'Pruebas de revisión de necesidad, conservación del objetivo y recuperación ante respuestas inválidas. Parte de la comparación de proveedores permanece incompleta.',
 'Pruebas de generación de propuestas, referencias y cálculos; revisión de bloqueos y advertencias.',
 'Pruebas de personalización, aprobación y verificación de versiones, sin retirar aprobaciones al consultar.',
 'Pruebas de preparación, confirmación y ejecución de cargas controladas.',
 'Pruebas de conciliación y revisión de nombres y unidades en los dos casos demostrados.',
 'Pruebas de filtros, periodicidad y procedencia de los resultados del panel.',
 'Pruebas de respuestas del copiloto y archivos exportados. Sigue pendiente la campaña autenticada completa por perfil.',
]
for n,x in enumerate(r['casos_uso']):
 ids=list(dict.fromkeys(re.findall(r'RF-(\d{2})',original['casos_uso'][n]['campos']['Trazabilidad'])))
 x['campos']['Trazabilidad']='; '.join('Requisito funcional '+str(int(i)) for i in ids)+'.'
 x['campos']['Evidencia y límite']=evidence_names[n]
r['comparacion_proveedores_fuentes']=['Registro de pruebas del manual de formación','Informe de pruebas posteriores al cierre']
r['plan_pruebas_actualizado'][11]['requisitos']='Requisito funcional 1, requisito funcional 2 y requisito no funcional 1'
r['plan_pruebas_actualizado'][11]['resultado_esperado']='Una cuenta con el permiso necesario puede realizar la operación; una cuenta sin ese permiso recibe acceso denegado. Se conserva la recuperación administrativa.'


permisos_visibles=[
 'Sesión válida y permisos de seguridad correspondientes a la operación: administrar cuentas, roles o permisos, o consultar auditoría.',
 'Consultar, registrar y probar conexiones; consultar y modificar la configuración de inteligencia artificial. La modificación de esta configuración permite también probar el proveedor.',
 'Consultar el módulo en el que se selecciona la fuente. El cambio de contexto no concede permisos adicionales.',
 'Consultar metadatos; actualizar metadatos para capturar una nueva versión de la estructura.',
 'Consultar el catálogo analítico; modificar el catálogo para crear, editar o retirar preguntas y opciones.',
 'Generar propuestas, permiso requerido también para sugerir y revisar necesidades comerciales.',
 'Generar propuestas de inteligencia de negocios.',
 'Consultar propuestas; generar propuestas para crear una versión derivada o descartar una versión no aprobada; revisar propuestas para aprobar, rechazar o retirar una aprobación.',
 'Consultar ejecuciones de carga; ejecutar cargas para preparar y confirmar la materialización del datamart.',
 'Consultar ejecuciones de carga; modificar ejecuciones para realizar comprobaciones y registrar decisiones sobre etiquetas.',
 'Consultar el panel analítico de ventas.',
 'Consultar el panel analítico para usar el copiloto; contar además con permiso de exportación de informes para descargar archivos.',
]
for x,permiso in zip(r['casos_uso'],permisos_visibles):x['campos']['Permisos']=permiso
# Se conserva el vocabulario técnico imprescindible, acompañado por su significado en el capítulo.
r['RF'][10]['precision_corte_noviembre']='Las generaciones actuales utilizan el contrato vigente de propuesta y las reglas actuales de compilación. El servidor desarrolla las decisiones resumidas y evita ejecutar instrucciones de consulta redactadas por el modelo de lenguaje.'

# Los casos y requisitos no cambian de cantidad; los identificadores se conservan sin mostrarlos en los títulos.
for key,count in [('RF',26),('RNF',12),('casos_uso',12),('historias_usuario',18),('sprints',7),('plan_pruebas_actualizado',12),('matriz_trazabilidad',26)]:assert len(r[key])==count
r['diagramas_manifest']='diagramas/manifiesto_diagramas.json'
r['instrucciones_lectura_json']={'etiqueta':'Etiqueta visible que debe usarse en tablas y encabezados.','id':'Identificador interno; no imprimir en el cuerpo del capítulo.','control_interno':'Proveniencia técnica y texto original preservado; no imprimir como contenido principal.'}
(B/'ingenieria_clara.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print('ingenieria_clara.json creada; registros y trazabilidad preservados')
