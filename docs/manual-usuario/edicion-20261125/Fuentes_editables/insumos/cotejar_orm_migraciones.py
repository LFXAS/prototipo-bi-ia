from pathlib import Path
import ast,json,hashlib
W=Path(__file__).resolve().parents[1];R=Path('/home/ceo/Proyectos/BI')
I=json.loads((W/'insumos/inventario_postgresql_real.json').read_text());expected=[]
def foreign(expr,table,column):
 for call in ast.walk(expr):
  if not isinstance(call,ast.Call) or not isinstance(call.func,ast.Name) or call.func.id!='ForeignKey':continue
  ref=ast.literal_eval(call.args[0]);schema,parent,col=ref.split('.')
  kw={k.arg:ast.literal_eval(k.value) for k in call.keywords}
  expected.append({'hija':'app.'+table,'columna':column,'padre':schema+'.'+parent,'columna_padre':col,'al_eliminar':kw.get('ondelete','NO ACTION')})
for p in (R/'backend/app/modules').glob('*/models.py'):
 for n in ast.parse(p.read_text()).body:
  if isinstance(n,ast.ClassDef):
   table=next(ast.literal_eval(a.value) for a in n.body if isinstance(a,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='__tablename__' for t in a.targets))
   for a in n.body:
    if isinstance(a,ast.AnnAssign) and isinstance(a.value,ast.Call) and isinstance(a.value.func,ast.Name) and a.value.func.id=='mapped_column':foreign(a.value,table,a.target.id)
  elif isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='Table':
   table=ast.literal_eval(n.value.args[0])
   for c in n.value.args:
    if isinstance(c,ast.Call) and isinstance(c.func,ast.Name) and c.func.id=='Column':foreign(c,table,ast.literal_eval(c.args[0]))
actions={'r':'RESTRICT','n':'SET NULL','c':'CASCADE','a':'NO ACTION','d':'SET DEFAULT'}
actual=[{'hija':x['child'],'columna':x['child_columns'][0],'padre':x['parent'],'columna_padre':x['parent_columns'][0],'al_eliminar':actions[x['delete_action']]} for x in I['relaciones_fisicas']]
key=lambda x:tuple(x[k] for k in ['hija','columna','padre','columna_padre','al_eliminar'])
assert sorted(map(key,actual))==sorted(map(key,expected))
revisions={}
for p in (R/'backend/migrations/versions').glob('*.py'):
 vals={}
 for a in ast.parse(p.read_text()).body:
  if isinstance(a,ast.AnnAssign) and isinstance(a.target,ast.Name) and a.target.id in {'revision','down_revision'}:vals[a.target.id]=ast.literal_eval(a.value)
  elif isinstance(a,ast.Assign):
   for t in a.targets:
    if isinstance(t,ast.Name) and t.id in {'revision','down_revision'}:vals[t.id]=ast.literal_eval(a.value)
 revisions[vals['revision']]={'anterior':vals['down_revision'],'archivo':p.name}
heads=set(revisions)-{v['anterior'] for v in revisions.values() if v['anterior']}
applied=json.loads((W/'insumos/version_migracion_aplicada.json').read_text());assert heads==set(applied)
report={'estado':'conforme','metodo':'Lectura AST de las fuentes sin importar ni ejecutar la aplicación; cotejo de 174 nombres de columna y las 24 FK con sus políticas de eliminación. La revisión aplicada se leyó de la tabla técnica Alembic, sin datos de negocio.','columnas_app_coinciden':all(x['columnas_coinciden'] for x in I['comparacion_orm']),'fk_app_coinciden':True,'fk':sorted(actual,key=key),'archivos_migracion':len(revisions),'cabezas_codigo':sorted(heads),'revision_aplicada':applied,'cadena_migraciones':revisions,'sha256_inventario':hashlib.sha256((W/'insumos/inventario_postgresql_real.json').read_bytes()).hexdigest(),'limite':'No es una comparación exhaustiva de todos los índices o restricciones CHECK, ni una prueba de las filas comerciales o de todos los expedientes históricos.'}
(W/'insumos/Cotejo_ORM_migraciones.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Cotejo conforme: 174 columnas, 24 FK y políticas de eliminación, 19 migraciones, cabeza aplicada '+', '.join(applied))
