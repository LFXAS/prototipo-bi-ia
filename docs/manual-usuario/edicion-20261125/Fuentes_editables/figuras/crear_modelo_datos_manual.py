"""Diagramas determinísticos del esquema observado. No conecta a bases de datos."""
from pathlib import Path
from html import escape
from PIL import ImageFont
import json,hashlib,shutil
W=Path(__file__).resolve().parents[1];OUT=W/'figuras'
DATA=json.loads((W/'insumos/inventario_postgresql_real.json').read_text())
F='/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf';B='/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf'
C='#253E53';LINE='#567184';PALE='#EBF2F7';RECORD=[]
class Figure:
 def __init__(self,name,title):
  self.name=name;self.title=title;self.labels=[];self.layers=[];self.nodes=[]
 def text(self,x,y,s,bold=False,maxw=None,center=False,size=15):
  font=ImageFont.truetype(B if bold else F,size*10);width=font.getlength(s)/10
  if maxw is not None:assert width<=maxw,(self.name,s,width,maxw)
  self.labels.append({'texto':s,'tamano_svg':size,'tamano_a_23cm_pt':round(size*23/2.54*72/900,2)})
  return f'<text x="{x}" y="{y}" font-family="Times New Roman" font-size="{size}" font-weight="{700 if bold else 400}" text-anchor="{"middle" if center else "start"}" fill="{C}">{escape(s)}</text>'
 def table(self,x,y,w,name,rows,ref=False):
  h=31+len(rows)*18+6
  self.nodes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="white" stroke="{LINE}" stroke-width="1.4"/><path d="M{x} {y+31} H{x+w}" stroke="{LINE}"/><rect x="{x+1}" y="{y+1}" width="{w-2}" height="29" fill="{PALE}"/>'+self.text(x+9,y+22,name,bold=True,maxw=w-18))
  for i,s in enumerate(rows):self.nodes.append(self.text(x+9,y+49+18*i,s,maxw=w-18))
  return h
 def path(self,pts,dash=False):
  d='M'+' L'.join(f'{x} {y}' for x,y in pts)
  self.layers.append(f'<path d="{d}" fill="none" stroke="{LINE}" stroke-width="1.5"'+(' stroke-dasharray="6 4"' if dash else '')+'/>')
 def card(self,x,y,s):
  width=ImageFont.truetype(F,150).getlength(s)/10
  self.nodes.append(f'<rect x="{x-2}" y="{y-13}" width="{width+4}" height="17" fill="white"/>'+self.text(x,y,s))
 def foot(self,lines):
  base=472 if len(lines)==1 else 454
  for i,s in enumerate(lines):self.nodes.append(self.text(20,base+i*18,s,maxw=860))
 def save(self,note):
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="23cm" height="12.26667cm" viewBox="0 0 900 480"><title>{escape(self.title)}</title><desc>{escape(note)}</desc><rect width="900" height="480" fill="white"/>'+''.join(self.layers+self.nodes)+'</svg>'
  p=OUT/(self.name+'.svg');p.write_text(svg)
  RECORD.append({'archivo_svg':p.name,'archivo_png':p.with_suffix('.png').name,'titulo':self.title,'nota':note,'ancho_cm':23,'alto_cm':23*480/900,'tamano_minimo_pt':10.87,'fuente':'Times New Roman','etiquetas':self.labels,'sha256_svg':hashlib.sha256(p.read_bytes()).hexdigest()})

f=Figure('ER_01_seguridad','Modelo físico de seguridad y navegación')
f.table(20,20,245,'app.users',['id [PK]','email [único]','full_name','password_hash','is_active','is_system_protected'])
f.table(330,20,240,'app.roles',['id [PK]','code [único]','name [único]','is_active','is_system_protected'])
f.table(640,20,240,'app.permissions',['id [PK]','code [único]','name','is_active','is_system_protected'])
f.table(175,215,235,'app.user_roles',['user_id [PK, FK users.id]','role_id [PK, FK roles.id]'])
f.table(490,215,250,'app.role_permissions',['role_id [PK, FK roles.id]','permission_id [PK, FK]'])
f.table(330,340,240,'app.menus',['id [PK]','code [único]','label / path [path único]','module_code / position'])
f.table(640,340,240,'app.menu_permissions',['menu_id [PK, FK menus.id]','permission_id [PK, FK]'])
f.table(20,340,245,'app.audit_events',['id [PK]','actor_user_id [FK opcional]','action / resource_type','detail [JSON]'])
for pts,cards in [([(205,215),(205,190),(140,190),(140,165)],[(211,207,'0..*'),(146,183,'1')]), ([(375,215),(375,147)],[(381,207,'0..*'),(381,165,'1')]), ([(525,215),(525,175),(500,175),(500,147)],[(531,207,'0..*'),(505,166,'1')]), ([(690,215),(690,175),(760,175),(760,147)],[(696,207,'0..*'),(766,166,'1')]), ([(760,340),(760,312),(840,312),(840,147)],[(765,333,'0..*'),(846,165,'1')]), ([(640,380),(570,380)],[(610,371,'0..*'),(580,371,'1')]), ([(100,340),(100,195),(70,195),(70,165)],[(107,330,'0..*'),(75,185,'0..1')])]:
 f.path(pts)
 for c in cards:f.card(*c)
f.foot(['Líneas: FK reales. PK: clave primaria. Las tres tablas de asociación tienen PK compuesta.'])
f.save('Se muestran las ocho tablas de seguridad y siete relaciones físicas. Campos principales; el diccionario enumera todas las columnas. La auditoría conserva actor opcional y una etiqueta histórica separada.')

f=Figure('ER_02_configuracion_metadatos','Modelo físico de configuración y metadatos')
f.table(20,20,245,'app.secrets',['id [PK]','kind','ciphertext [valor cifrado]'])
f.table(330,20,245,'app.data_connections',['id [PK]','connector_kind / database_name','secret_id [FK, único]','name / host / port','is_active / last_test_status'])
f.table(635,20,245,'app.metadata_snapshots',['id [PK]','data_connection_id [FK]','schema_document [JSONB]','content_hash / contract_version','captured_by_user_id [FK]'])
f.table(20,280,245,'app.llm_configurations',['id [PK]','provider_kind / model_id','secret_id [FK opcional, único]','is_active / last_test_status','reasoning_level'])
f.table(330,280,245,'app.parameters',['id [PK]','key [único] / module_code','value_type / value','default_value / min_value','max_value / is_active'])
f.table(635,280,245,'app.analysis_catalogs',['id [PK]','data_connection_id [FK]','domain_code / version','configuration_document [JSONB]','updated_by_user_id [FK]'])
for pts,cards in [([(330,90),(265,90)],[(298,82,'0..1'),(273,82,'1')]), ([(140,280),(140,111)],[(146,270,'0..1'),(146,130,'0..1')]), ([(635,90),(575,90)],[(605,82,'0..*'),(581,82,'1')]), ([(635,320),(605,320),(605,180),(550,180),(550,147)],[(612,310,'0..*'),(554,166,'1')])]:
 f.path(pts)
 for c in cards:f.card(*c)
f.foot(['Las FK de autoría hacia users se muestran en ER_04. No se muestran valores de conexión ni credenciales.'])
f.save('Seis tablas de configuración y metadatos. Cuatro relaciones físicas; las dos FK de autoría aparecen en el esquema separado de responsables. Catálogo único por conexión y dominio; instantánea única por conexión, versión de contrato y huella.')

f=Figure('ER_03_propuestas_ejecuciones','Modelo físico de necesidades, propuestas y ejecuciones')
f.table(20,170,245,'app.metadata_snapshots',['id [PK]','data_connection_id [FK]','content_hash','schema_document [JSONB]'])
f.table(330,20,245,'app.business_need_reviews',['id [PK]','metadata_snapshot_id [FK]','input_hash / assessment_hash','assessment_document [JSONB]'])
f.table(330,235,245,'app.bi_proposals',['id [PK]','metadata_snapshot_id [FK]','source_proposal_id [FK propia]','business_goal / status','proposal_document [JSONB]','validation_document [JSONB]','autoría: ver ER_04 (*)'])
f.table(635,20,245,'app.etl_executions',['id [PK]','proposal_id [FK]','metadata_snapshot_id [FK]','status / builder_version','plan_document [JSONB]','metrics_document [JSONB]'])
f.table(635,285,245,'app.semantic_advice',['id [PK]','proposal_id [FK]','concept_code / question','response_document [JSONB]'])
for pts,cards in [([(330,78),(290,78),(290,195),(265,195)],[(301,70,'0..*'),(269,185,'1')]), ([(330,300),(265,300),(265,270)],[(299,291,'0..*'),(272,284,'1')]), ([(635,48),(608,48),(608,8),(140,8),(140,170)],[(611,40,'0..*'),(147,160,'1')]), ([(635,132),(608,132),(608,280),(575,280)],[(612,123,'0..*'),(582,270,'1')]), ([(635,340),(575,340)],[(607,331,'0..*'),(581,331,'1')]), ([(390,398),(390,430),(550,430),(550,398)],[(399,425,'0..*'),(515,418,'0..1')])]:
 f.path(pts)
 for c in cards:f.card(*c)
f.foot(['(*) Autoría: ER_04. La revisión previa y la propuesta NO tienen una FK directa entre sí.'])
f.save('Cuatro entidades operativas y referencia a metadatos; seis FK físicas, incluida la relación de versiones derivadas de bi_proposals. Las revisiones previas se comprueban con contexto y huellas por lógica del servidor; no existe una FK review_id en bi_proposals.')

f=Figure('ER_04_autoria','Relaciones físicas con la persona que realiza cada acción')
f.table(330,150,245,'app.users',['id [PK]','email [único]','full_name','is_active','is_system_protected'])
f.table(20,20,245,'app.metadata_snapshots',['id [PK]','captured_by_user_id [FK]'])
f.table(20,205,245,'app.analysis_catalogs',['id [PK]','updated_by_user_id [FK]'])
f.table(20,355,245,'app.business_need_reviews',['id [PK]','created_by_user_id [FK]'])
f.table(635,20,245,'app.bi_proposals',['id [PK]','created_by_user_id [FK]','reviewed_by_user_id [FK]'])
f.table(635,205,245,'app.semantic_advice',['id [PK]','created_by_user_id [FK]'])
f.table(635,355,245,'app.etl_executions',['id [PK]','created_by_user_id [FK]'])
paths=[([(265,65),(295,65),(295,175),(330,175)],[(270,55,'0..*'),(300,166,'0..1')]), ([(265,245),(330,245)],[(270,235,'0..*'),(300,235,'0..1')]), ([(265,398),(295,398),(295,267),(330,267)],[(270,388,'0..*'),(300,285,'0..1')]), ([(635,62),(605,62),(605,170),(575,170)],[(607,52,'0..*'),(578,160,'0..1')]), ([(635,98),(620,98),(620,205),(575,205)],[(635,124,'0..*'),(578,195,'0..1')]), ([(635,245),(575,245)],[(605,235,'0..*'),(578,235,'0..1')]), ([(635,395),(605,395),(605,267),(575,267)],[(610,385,'0..*'),(578,285,'0..1')])]
for pts,cards in paths:
 f.path(pts)
 for c in cards:f.card(*c)
f.foot(['Siete FK opcionales con ON DELETE SET NULL. No significa que la interfaz permita omitir la sesión.','Las etiquetas históricas guardadas en varias entidades no son nuevas FK ni usuarios duplicados.'])
f.save('Siete FK de autoría hacia users. La opcionalidad se obtiene del catálogo real: la eliminación de una cuenta preserva el expediente anulando la referencia. Las reglas del servidor y las etiquetas históricas complementan la FK.')

f=Figure('ER_00_recorrido_identidades','Identidades principales que conectan fuente, diseño y ejecución')
f.table(20,45,245,'app.data_connections',['id [PK]','database_name'])
f.table(330,45,245,'app.metadata_snapshots',['id [PK]','data_connection_id [FK]'])
f.table(635,45,245,'app.bi_proposals',['id [PK]','metadata_snapshot_id [FK]','source_proposal_id [FK propia]'])
f.table(20,285,245,'app.analysis_catalogs',['id [PK]','data_connection_id [FK]','configuration_document [JSONB]'])
f.table(330,285,245,'app.business_need_reviews',['id [PK]','metadata_snapshot_id [FK]','assessment_document [JSONB]'])
f.table(635,285,245,'app.etl_executions',['id [PK]','proposal_id [FK]','metadata_snapshot_id [FK]'])
for pts,cards in [([(330,85),(265,85)],[(300,77,'0..*'),(271,77,'1')]), ([(635,85),(575,85)],[(606,77,'0..*'),(581,77,'1')]), ([(145,285),(145,118)],[(151,275,'0..*'),(151,139,'1')]), ([(455,285),(455,118)],[(461,275,'0..*'),(461,139,'1')]), ([(760,285),(760,136)],[(766,275,'0..*'),(766,157,'1')]), ([(635,335),(610,335),(610,165),(550,165),(550,118)],[(605,325,'0..*'),(556,139,'1')])]:
 f.path(pts)
 for c in cards:f.card(*c)
f.foot(['Vista de las FK principales; seguridad, secretos, asesoría y autoría se detallan en ER_01 a ER_04.','Una propuesta aprobada y una ejecución son registros distintos. El datamart físico no es el documento JSON.'])
f.save('Vista inicial de las identidades principales; no incluye todas las FK. El inventario y los cuatro esquemas de área contienen las 18 entidades de app y las 24 relaciones físicas, sin deducir relaciones por parecido de nombres.')

for eid in [21,22]:
 schema=f'mart_ventas_e{eid}';tables={t['table_name']:t for t in DATA['catalogo']['tables'] if t['schema_name']==schema}
 f=Figure(f'ER_05_datamart_e{eid}',f'Estructura física conservada del datamart, ejecución {eid}')
 def rows(t):
  pks={c for k in tables[t]['constraints'] if k['kind']=='p' for c in k['columns']}
  return [c['name']+(' [PK]' if c['name'] in pks else '') for c in tables[t]['columns']]
 f.table(20,45,245,'dim_producto',rows('dim_producto'))
 f.table(20,290,245,'dim_cliente',rows('dim_cliente'))
 f.table(330,5,245,'dim_fecha',rows('dim_fecha'))
 f.table(635,135,245,'dim_territorio',rows('dim_territorio'))
 f.table(330,215,245,'fact_ventas',rows('fact_ventas'))
 f.path([(265,140),(300,140),(300,280),(330,280)],True)
 f.path([(265,360),(330,360)],True)
 f.path([(455,168),(455,215)],True)
 f.path([(575,300),(635,300)],True)
 f.foot([schema+': líneas discontinuas = enlaces lógicos; NO son restricciones FK de PostgreSQL.','Las dimensiones tienen PK; fact_ventas no tiene PK ni FK. etl_execution_id tampoco tiene FK a app.'])
 f.save('Todas las columnas de las cinco tablas físicas observadas. Los nombres y atributos corresponden a esta ejecución, no son un modelo fijo universal. Las líneas discontinuas representan la unión que efectúa el motor entre dim_*_sk y surrogate_key; la base no las impone como FK. No se atribuyen cardinalidades garantizadas a esas líneas.')

previous=Path('/home/ceo/Documentos/ChatGPT/Tesis 2026 CII/revision-capitulo3-20261117/nueva_revision/arquitectura')
for ext in ['svg','png']:
 p=previous/('Arquitectura_BI_IA_legible.'+ext);q=OUT/('Arquitectura_plataforma.'+ext)
 if not q.exists():shutil.copy2(p,q)  # La copia distribuida ya contiene el SVG/PNG; no requiere la ruta de autoría.
 if ext=='svg':q.write_text(q.read_text().replace('autorizado, sin claves.','autorizado, sin credenciales.'))
RECORD.append({'archivo_svg':'Arquitectura_plataforma.svg','archivo_png':'Arquitectura_plataforma.png','titulo':'Arquitectura de la plataforma inteligente de datamarts de ventas','nota':'Arquitectura reutilizada desde la revisión final legible: interfaz React, servidor FastAPI, fuentes SQL Server de solo lectura, PostgreSQL y proveedor de IA configurable. La IA propone y explica; el servidor comprueba y una persona autorizada aprueba. La carga se confirma por separado.','ancho_cm':23,'alto_cm':23*480/900,'tamano_minimo_pt':10.87,'fuente':'Times New Roman','origen':str(previous),'sha256_svg':hashlib.sha256((OUT/'Arquitectura_plataforma.svg').read_bytes()).hexdigest()})
(OUT/'manifest_figuras_datos.json').write_text(json.dumps(RECORD,ensure_ascii=False,indent=2)+'\n')
print('Generados siete ER y arquitectura legible: SVG de 900×480, TNR 10,87 pt a 23 cm.')
