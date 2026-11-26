"""Inventario documental, solo lectura; no consulta valores de negocio ni secretos."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess,json,hashlib,ast

W=Path(__file__).resolve().parents[1]
REPO=Path('/home/ceo/Proyectos/BI')
SQL="""
BEGIN READ ONLY;
SELECT json_build_object(
 'database',current_database(),
 'server_version',current_setting('server_version'),
 'schemas',(SELECT json_agg(json_build_object('name',n.nspname,'table_count',(SELECT count(*) FROM pg_class c WHERE c.relnamespace=n.oid AND c.relkind IN ('r','p'))) ORDER BY n.nspname) FROM pg_namespace n WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname<>'information_schema'),
 'tables',COALESCE((SELECT json_agg(x ORDER BY x.schema_name,x.table_name) FROM (
 SELECT n.nspname AS schema_name,c.relname AS table_name,c.relkind AS relation_kind,
 COALESCE((SELECT json_agg(json_build_object('position',a.attnum,'name',a.attname,'type',format_type(a.atttypid,a.atttypmod),'nullable',NOT a.attnotnull,'identity',a.attidentity,'generated',a.attgenerated,'has_default',a.atthasdef) ORDER BY a.attnum) FROM pg_attribute a WHERE a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped),'[]'::json) AS columns,
 COALESCE((SELECT json_agg(json_build_object('name',k.conname,'kind',k.contype,'columns',(SELECT json_agg(a.attname ORDER BY q.ord) FROM unnest(k.conkey) WITH ORDINALITY q(attnum,ord) JOIN pg_attribute a ON a.attrelid=k.conrelid AND a.attnum=q.attnum),'reference_schema',rn.nspname,'reference_table',rc.relname,'reference_columns',(SELECT json_agg(a.attname ORDER BY q.ord) FROM unnest(k.confkey) WITH ORDINALITY q(attnum,ord) JOIN pg_attribute a ON a.attrelid=k.confrelid AND a.attnum=q.attnum),'delete_action',k.confdeltype,'update_action',k.confupdtype,'deferrable',k.condeferrable) ORDER BY k.contype,k.conname) FROM pg_constraint k LEFT JOIN pg_class rc ON rc.oid=k.confrelid LEFT JOIN pg_namespace rn ON rn.oid=rc.relnamespace WHERE k.conrelid=c.oid AND k.contype IN ('p','u','f')),'[]'::json) AS constraints,
 COALESCE((SELECT json_agg(json_build_object('name',i.relname,'primary',ix.indisprimary,'unique',ix.indisunique,'partial',ix.indpred IS NOT NULL,'expression',ix.indexprs IS NOT NULL,'columns',(SELECT json_agg(a.attname ORDER BY q.ord) FROM unnest(ix.indkey::smallint[]) WITH ORDINALITY q(attnum,ord) LEFT JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum=q.attnum)) ORDER BY i.relname) FROM pg_index ix JOIN pg_class i ON i.oid=ix.indexrelid WHERE ix.indrelid=c.oid AND ix.indisunique),'[]'::json) AS unique_indexes
 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
 WHERE c.relkind IN ('r','p') AND n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%'
 ) x),'[]'::json)
);
ROLLBACK;
"""
r=subprocess.run(['docker','exec','-i','bi-ia-prototype-postgres-1','psql','-X','-q','-U','bi_app','-d','bi_prototype','-At','-v','ON_ERROR_STOP=1'],input=SQL,text=True,capture_output=True,check=True)
data=json.loads(r.stdout.strip())
now=datetime.now(ZoneInfo('America/Guayaquil')).isoformat()
models={};model_sources=[]
for p in sorted((REPO/'backend/app/modules').glob('*/models.py')):
 model_sources.append({'ruta':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 tree=ast.parse(p.read_text())
 for node in tree.body:
  if isinstance(node,ast.ClassDef):
   table=None;cols=[]
   for a in node.body:
    if isinstance(a,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='__tablename__' for t in a.targets):table=ast.literal_eval(a.value)
    if isinstance(a,ast.AnnAssign) and isinstance(a.value,ast.Call) and isinstance(a.value.func,ast.Name) and a.value.func.id=='mapped_column':cols.append(a.target.id)
   if table:models[table]={'clase':node.name,'columnas':cols,'fuente':str(p)}
  if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='Table':
   table=ast.literal_eval(node.value.args[0]);cols=[]
   for arg in node.value.args:
    if isinstance(arg,ast.Call) and isinstance(arg.func,ast.Name) and arg.func.id=='Column':cols.append(ast.literal_eval(arg.args[0]))
   models[table]={'clase':'tabla de asociación','columnas':cols,'fuente':str(p)}
comparisons=[]
for t in data['tables']:
 if t['schema_name']!='app':continue
 real={c['name'] for c in t['columns']};m=models.get(t['table_name']);declared=set(m['columnas']) if m else set()
 comparisons.append({'tabla':t['table_name'],'clase':m['clase'] if m else None,'columnas_solo_bd':sorted(real-declared),'columnas_solo_orm':sorted(declared-real),'columnas_coinciden':m is not None and real==declared})
links=[]
for t in data['tables']:
 for f in t['constraints']:
  if f['kind']!='f':continue
  col=set(f['columns']); unique=any(i['unique'] and not i['partial'] and not i['expression'] and set(i['columns'])==col for i in t['unique_indexes'])
  nullable=any(c['nullable'] for c in t['columns'] if c['name'] in col)
  links.append({'constraint':f['name'],'child':t['schema_name']+'.'+t['table_name'],'child_columns':f['columns'],'parent':f['reference_schema']+'.'+f['reference_table'],'parent_columns':f['reference_columns'],'parents_per_child':'0..1' if nullable else '1','children_per_parent':'0..1' if unique else '0..*','derived_only_from':'FK, nullability and non-partial unique index','delete_action':f['delete_action']})
head=subprocess.run(['git','-C',str(REPO),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
migrations=[{'archivo':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted((REPO/'backend/migrations/versions').glob('*.py'))]
result={'titulo':'Inventario físico real PostgreSQL para manual operativo','fecha':now,'modo':'Catálogos PostgreSQL en transacción READ ONLY; sin SELECT de valores de negocio, JSON, credenciales o hashes de acceso. AST de modelos y archivos de migración leídos; sin importar ni ejecutar la aplicación.','contenedor':'bi-ia-prototype-postgres-1','repositorio_consultado':str(REPO),'commit':head,'catalogo':data,'relaciones_fisicas':links,'comparacion_orm':comparisons,'fuentes_modelos':model_sources,'migraciones_archivos':migrations,'reglas_interpretacion':['Las cardinalidades mínimas de hijos no se infieren de FK: un padre puede tener cero hijos.','Una FK nullable permite cero o un padre; obligatoria exige un padre por fila hija.','Un índice único completo sobre exactamente las columnas de la FK limita a un hijo; no aplica si la unicidad solo afecta un subconjunto distinto o un índice parcial.','Los enlaces dentro de JSON o de un documento no se presentan como restricciones FK físicas.']}
out=W/'insumos/inventario_postgresql_real.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'salida':str(out),'tablas':len(data['tables']),'tablas_app':sum(t['schema_name']=='app' for t in data['tables']),'fk':len(links),'fk_app':sum(x['child'].startswith('app.') for x in links),'orm_coincide':all(x['columnas_coinciden'] for x in comparisons),'migraciones_archivos':len(migrations)},ensure_ascii=False))
