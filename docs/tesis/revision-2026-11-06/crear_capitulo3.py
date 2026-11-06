from pathlib import Path
from copy import deepcopy
from decimal import Decimal
import json, re, hashlib, zipfile
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START, WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image

B=Path(__file__).parent
REF=Path('/home/ceo/Proyectos/Información adicional proyecto BI/Versiones/2026-11-06_v01/03_Tesis_y_manuales_academicos/Revision_capitulo_III/Capitulo_III_Propuesta_tecnologica_y_encuesta_real.docx')
OUT=B/'output/Capitulo_III_Propuesta_tecnologica_revisada.docx'
E=json.loads((B/'encuesta/resultados_encuesta.json').read_text())
G=json.loads((B/'ingenieria/ingenieria_clara.json').read_text())
P=json.loads((B/'presupuesto/presupuesto_estimado_4_meses.json').read_text())
D=Document(REF)
assert hashlib.sha256(REF.read_bytes()).hexdigest()=='f71232cb57cbce9601b33ff502e3c062fd3978e288d4b07aa5dbfa704bdeb9bb'
for ch in list(D._element.body):
    if ch.tag!=qn('w:sectPr'): D._element.body.remove(ch)

def sty(name): return next(s for s in D.styles if s.name==name)
normal=sty('Normal')
heads={i:sty(f'Heading {i}') for i in (1,2,3)}
def setfont(s,size=12,bold=None):
    s.font.name='Times New Roman'; s.font.size=Pt(size);s.font.color.rgb=RGBColor(0,0,0);s.font.underline=False
    if bold is not None: s.font.bold=bold
    rf=s.element.get_or_add_rPr().get_or_add_rFonts()
    for a in ['asciiTheme','hAnsiTheme','eastAsiaTheme','cstheme']:
        if rf.get(qn('w:'+a)) is not None: del rf.attrib[qn('w:'+a)]
    for a in ['ascii','hAnsi','eastAsia','cs']: rf.set(qn('w:'+a),'Times New Roman')
for s in [normal,sty('Title'),sty('Caption'),*heads.values()]: setfont(s)
normal.paragraph_format.line_spacing=2
normal.paragraph_format.space_before=Pt(0);normal.paragraph_format.space_after=Pt(0)
normal.paragraph_format.first_line_indent=Cm(1.27)
normal.paragraph_format.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
normal.paragraph_format.widow_control=True
for i,s in heads.items():
    setfont(s,12,True);pf=s.paragraph_format;pf.first_line_indent=Cm(0)
    pf.space_before=Pt(12);pf.space_after=Pt(6);pf.line_spacing=2
    pf.keep_with_next=True;pf.keep_together=True
    pf.alignment=WD_ALIGN_PARAGRAPH.LEFT
    pf.page_break_before=False
setfont(sty('Title'),14,True)
sty('Title').paragraph_format.first_line_indent=Cm(0)
sty('Title').paragraph_format.alignment=WD_ALIGN_PARAGRAPH.CENTER
sty('Title').paragraph_format.line_spacing=2
for s in [sty('Title'),*heads.values()]:
    pp=s.element.get_or_add_pPr()
    for z in list(pp):
        if z.tag==qn('w:pBdr'):pp.remove(z)

def geometry(s,land=False):
    s.orientation=WD_ORIENT.LANDSCAPE if land else WD_ORIENT.PORTRAIT
    s.page_width=Cm(29.7 if land else 21)
    s.page_height=Cm(21 if land else 29.7)
    s.left_margin=Cm(3.81);s.right_margin=Cm(2.54)
    s.top_margin=Cm(2.54);s.bottom_margin=Cm(2.54)
    s.header_distance=Cm(1.27);s.footer_distance=Cm(1.27)
    s.different_first_page_header_footer=False
    sp=s._sectPr
    for x in list(sp):
        if x.tag in [qn('w:pgNumType'),qn('w:titlePg')]:sp.remove(x)
geometry(D.sections[0])
for part in [D.sections[0].header,D.sections[0].footer]:
    for p in part.paragraphs: p.clear()
fp=D.sections[0].footer.paragraphs[0];fp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
fp.paragraph_format.first_line_indent=Cm(0);fp.paragraph_format.line_spacing=1
r=fp.add_run();r.font.name='Times New Roman';r.font.size=Pt(10)
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE')
rr=OxmlElement('w:r');tt=OxmlElement('w:t');tt.text='1';rr.append(tt);fld.append(rr);fp._p.append(fld)
settings=D.settings.element
uf=OxmlElement('w:updateFields');uf.set(qn('w:val'),'true');settings.append(uf)
D.core_properties.title='Capítulo III Propuesta tecnológica del sistema inteligente de datamarts de ventas'
D.core_properties.subject='Tesis de prueba de concepto de datamarts de ventas'
D.core_properties.author='Robles Emily; Velásquez Lesly'
D.core_properties.comments=''

def readable(s):
    replacements={
      'operación del servidor no permitido':'dirección de servicio no permitida',
      'relaciones declaradas y relaciones declaradas':'claves y relaciones declaradas',
      'analista inteligencia de negocios':'analista de inteligencia de negocios',
      'El indicadores':'Los indicadores',
      'day/week/month/quarter/year':'día, semana, mes, trimestre y año',
      'daily/weekly/monthly/quarterly/yearly':'diaria, semanal, mensual, trimestral y anual',
      'make verify':'la verificación automática del proyecto',
      'CP11':'la prueba de continuidad de la necesidad',
      '403':'acceso denegado',
      '409':'conflicto de la operación',
      'benchmark':'comparación de rendimiento',
      'timeout':'tiempo de espera máximo',
      'PII':'datos personales identificables',
      'WCAG':'pautas de accesibilidad del contenido web',
      'SLA':'acuerdo de nivel de servicio',
      'proveedor modelo de lenguaje':'proveedor de modelos de lenguaje',
      'Cada indicadores':'Cada indicador',
      'No se traduce datos personales':'No se traducen datos personales',
      'fuente/base/offset':'fuente, base y desplazamiento horario',
      'moneda ISO':'código internacional de moneda',
      'La revisión vigente es revisión de necesidad vigente.':'La revisión aplica las reglas vigentes de interpretación de la necesidad.',
      'contrato inteligencia de negocios estructurado':'diseño estructurado de inteligencia de negocios',
      'NumberOfUnits sin semántica de identificador puede ser cantidad.':'Una columna denominada número de unidades puede ser una cantidad cuando su significado y su tipo lo respaldan.',
      'devuelve 409':'informa un conflicto',
      'recibe 409 y exige hija actual o regeneración':'se rechaza por conflicto y exige una nueva versión compatible o regeneración',
      'igualdad real de hashes':'coincidencia real de las huellas de contenido',
      'El replay':'La reproducción del diseño',
      'sin failover silencioso':'sin cambiar de proveedor de forma silenciosa',
      'no hay failover silencioso':'no se cambia de proveedor de forma silenciosa',
      'Los presets':'Las configuraciones predefinidas',
      'nombres ES/EN':'nombres en español e inglés',
      'exclusiones ES/EN':'exclusiones expresadas en español e inglés',
      'Reserva para consultas servicios del servidor de modelos modelo de lenguaje':'Reserva para consultas a modelos de inteligencia artificial',
      'Conectividad, energía, API y materiales':'Conectividad, energía, inteligencia artificial y materiales'
    }
    for a,b in replacements.items():s=s.replace(a,b)
    for a,b in [('backend','servidor'),('UI','interfaz'),('replay','reproducción'),('hashes','huellas de contenido'),('presets','configuraciones predefinidas'),('failover','cambio de proveedor'),('ES/EN','español e inglés'),('CI','integración continua')]:
      s=re.sub(r'\b'+re.escape(a)+r'\b',b,s)
    fixes=json.loads((B/'qa/concordancias_aplicadas_finales.json').read_text())['hallazgos']
    for fix in sorted(fixes,key=lambda x:-len(x['buscar'])):
        s=s.replace(fix['buscar'],fix['sustituir_por'])
    return s

TABLE=0;FIG=0;LOG=[]
def text(v):
    if v is None:return 'No aplica'
    if isinstance(v,list):return '\n'.join(text(x) for x in v)
    if isinstance(v,dict):return '\n'.join(f'{k}: {text(x)}' for k,x in v.items())
    return readable(str(v))
def p(t='',bold=False,small=False,center=False,keep=False):
    pp=D.add_paragraph(style=normal);pp.add_run(text(t)).bold=bold
    if small:
        pp.paragraph_format.first_line_indent=Cm(0);pp.paragraph_format.line_spacing=1
        pp.paragraph_format.space_after=Pt(7)
        pp.paragraph_format.keep_together=True
        pp.alignment=WD_ALIGN_PARAGRAPH.LEFT
        for r in pp.runs:r.font.size=Pt(10.5)
    if center:pp.alignment=WD_ALIGN_PARAGRAPH.CENTER;pp.paragraph_format.first_line_indent=Cm(0)
    pp.paragraph_format.keep_with_next=keep
    LOG.append({'tipo':'parrafo','texto':text(t)})
    return pp
def h(t,level=1,page=False):
    pp=D.add_paragraph(text(t),style=heads[level]);pp.paragraph_format.page_break_before=page
    LOG.append({'tipo':'titulo','nivel':level,'texto':text(t)});return pp
def cap(kind,title):
    global TABLE,FIG
    if kind=='Tabla':TABLE+=1;num=TABLE
    else:FIG+=1;num=FIG
    pp=p('',small=True,keep=True)
    pp.alignment=WD_ALIGN_PARAGRAPH.LEFT
    pp.paragraph_format.space_before=Pt(8)
    rr=pp.add_run(f'{kind} 3.{num}');rr.bold=True;rr.font.size=Pt(11)
    rr=pp.add_run('\n'+readable(title));rr.italic=True;rr.font.size=Pt(11)
    return num
def table(title,headers,rows,widths=None,note='Elaboración propia a partir de las especificaciones y evidencias del proyecto.',size=11):
    cap('Tabla',title)
    tb=D.add_table(rows=1,cols=len(headers));tb.alignment=WD_TABLE_ALIGNMENT.CENTER;tb.autofit=False
    usable=23.35 if D.sections[-1].orientation==WD_ORIENT.LANDSCAPE else 14.65
    widths=widths or [usable/len(headers)]*len(headers)
    # Explicit fixed grid with native, editable rows.
    for col,w in zip(tb.columns,widths):col.width=Cm(w)
    pr=tb._tbl.tblPr
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:
        x=OxmlElement('w:'+edge);x.set(qn('w:val'),'single' if edge in ['top','bottom'] else 'nil')
        x.set(qn('w:sz'),'8');x.set(qn('w:color'),'000000');borders.append(x)
    old=pr.find(qn('w:tblBorders'))
    if old is not None:pr.remove(old)
    pr.append(borders)
    mar=OxmlElement('w:tblCellMar')
    for edge,sz in [('top',65),('bottom',65),('left',75),('right',75)]:
        x=OxmlElement('w:'+edge);x.set(qn('w:w'),str(sz));x.set(qn('w:type'),'dxa');mar.append(x)
    pr.append(mar)
    allrows=[headers]+[[text(x) for x in row] for row in rows]
    for ix,rowvals in enumerate(allrows):
        row=tb.rows[0] if ix==0 else tb.add_row()
        trPr=row._tr.get_or_add_trPr();ns=OxmlElement('w:cantSplit');trPr.append(ns)
        if ix==0:
            z=OxmlElement('w:tblHeader');z.set(qn('w:val'),'true');trPr.append(z)
        for j,(cell,val,w) in enumerate(zip(row.cells,rowvals,widths)):
            cell.width=Cm(w);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp=cell._tc.get_or_add_tcPr()
            if ix==0:
                cb=OxmlElement('w:tcBorders');bo=OxmlElement('w:bottom');bo.set(qn('w:val'),'single');bo.set(qn('w:sz'),'6');cb.append(bo);cp.append(cb)
            # Each line is a native paragraph; keep flow within row only.
            for k,line in enumerate(str(val).split('\n')):
                pp=cell.paragraphs[0] if k==0 else cell.add_paragraph()
                pp.paragraph_format.first_line_indent=Cm(0)
                pp.paragraph_format.line_spacing=1.05;pp.paragraph_format.space_after=Pt(2)
                pp.paragraph_format.space_before=Pt(0);pp.paragraph_format.keep_with_next=False
                pp.paragraph_format.keep_together=True
                pp.alignment=WD_ALIGN_PARAGRAPH.LEFT
                rr=pp.add_run(line);rr.font.name='Times New Roman';rr.font.size=Pt(size);rr.bold=(ix==0)
                if j>0 and re.fullmatch(r'[0-9., %—–-]+',line):pp.alignment=WD_ALIGN_PARAGRAPH.CENTER
    if note:
        for cell in tb.rows[-1].cells:
            for pp in cell.paragraphs:pp.paragraph_format.keep_with_next=True
        p('Nota. '+note,small=True)
    if len(rows)<=6 and sum(len(text(v).split()) for row in rows for v in row)<165:
        for row in tb.rows[:-1]:
            for cell in row.cells:
                for pp in cell.paragraphs:pp.paragraph_format.keep_with_next=True
    if title.startswith('Historia de usuario') and len(tb.rows)>=3:

        for cell in tb.rows[-2].cells:
            for pp in cell.paragraphs:pp.paragraph_format.keep_with_next=True
    LOG.append({'tipo':'tabla','numero':TABLE,'titulo':title,'filas':rows})
    return tb
def image(title,path,note,maxh=None):
    path=Path(path)
    if not path.is_absolute():path=B/path
    cap('Figura',title)
    wpx,hpx=Image.open(path).size
    land=D.sections[-1].orientation==WD_ORIENT.LANDSCAPE
    maxw=23.35 if land else 14.65
    maxh=maxh or (12.4 if land else 21.5)
    ratio=min(maxw/wpx,maxh/hpx)
    pp=D.add_paragraph();pp.paragraph_format.first_line_indent=Cm(0);pp.paragraph_format.line_spacing=1
    pp.paragraph_format.space_after=Pt(5);pp.paragraph_format.keep_with_next=True;pp.alignment=WD_ALIGN_PARAGRAPH.CENTER
    shape=pp.add_run().add_picture(str(path),width=Cm(wpx*ratio),height=Cm(hpx*ratio))
    shape._inline.docPr.set('descr',title)
    p('Nota. '+note,small=True)
    LOG.append({'tipo':'figura','numero':FIG,'titulo':title,'ruta':str(path)})
def money(v):return f'{Decimal(str(v)):,.2f}'.replace(',','X').replace('.',',').replace('X','.')
def decimal_prose(v):return re.sub(r'(?<=\d)\.(?=\d)',',',v)
def clean_title(t):return re.sub(r'^(?:Tabla\s*\d+\.\s*)?','',t).strip()
def paragraphs(values):
    for x in values:p(x)
def clean_names(t):return re.sub(r'^(?:CU|HU)-\d+\.\s*','',clean_title(t))


# Este capítulo sustituye la versión anterior; los documentos originales se conservan.
DOCNOTE='Elaboración propia a partir de las especificaciones y registros del proyecto.'
def block(t,vals,level=1,page=False):
 h(t,level,page)
 paragraphs(vals)
def visible(t):
 # Identificadores y nombres de archivos se conservan sólo en los recursos de trazabilidad.
 return re.sub(r'\b(ETL|LLM|KPI|OLTP|API)\b',lambda m:{'ETL':'extracción, transformación y carga de datos','LLM':'modelo de lenguaje','KPI':'indicador','OLTP':'base transaccional','API':'servicios del servidor'}[m.group(0)],str(t))
def pending(title,rows):
 h(title,2)
 table(title,['Información necesaria','Espacio para completar'],[[x,'[POR COMPLETAR]\n________________________________'] for x in rows],[7.0,7.65],note='Los espacios se completarán con información y documentos efectivamente disponibles; no representan resultados obtenidos.')

p('CAPÍTULO III',bold=True,center=True)
D.add_paragraph('PROPUESTA TECNOLÓGICA',style=sty('Title'))
p('La propuesta consiste en un sistema inteligente que acompaña la construcción supervisada de datamarts de ventas. Un datamart es una estructura de datos preparada para analizar un área del negocio; en este caso, ventas. El sistema parte de una necesidad escrita por el analista, comprueba su relación con los metadatos disponibles, propone un modelo y permite revisar su aprobación antes de ejecutar la transformación de los datos.')
p('El capítulo presenta la factibilidad, la investigación y los resultados de la encuesta; después explica la organización del desarrollo con Scrum, los requisitos, el diseño y las pruebas del prototipo. La validación técnica utiliza AdventureWorks2022 y WideWorldImporters, dos bases demostrativas alojadas en SQL Server. Los resultados de opinión y los resultados de funcionamiento se analizan por separado.')
block('Alcance de la propuesta',[
 'El recorrido comprende preparación de fuentes y permisos, lectura de metadatos, configuración del catálogo de ventas, formulación y revisión de necesidades, generación de propuestas, aprobación humana, carga del datamart y consulta de indicadores. Los metadatos describen tablas, columnas, tipos y relaciones; no son las filas comerciales de la base.',
 'La inteligencia artificial interpreta, sugiere y explica. La aplicación comprueba las referencias y las operaciones permitidas, mientras que la persona autorizada decide la aprobación y confirma la ejecución. La aprobación del diseño y la ejecución de la carga son decisiones distintas.',
 'La arquitectura utiliza reglas y contratos comunes, con configuración independiente por fuente. Las dos bases de prueba permiten comprobar la reutilización del procedimiento; otros motores o modelos requieren sus adaptadores y verificaciones. El pronóstico de ventas quedó fuera del alcance aprobado.'])

block('Análisis de factibilidad',[
 'La factibilidad se examina desde la operación, la tecnología, las condiciones de uso y los recursos estimados. El propósito es determinar si la prueba de concepto puede construirse, demostrarse y mantenerse en el entorno académico disponible.'])
block('Factibilidad operacional',[
 'La plataforma organiza el trabajo por responsabilidades. El administrador prepara las conexiones, las cuentas y el proveedor de inteligencia artificial. El analista expresa la necesidad, revisa las propuestas y ejecuta las operaciones para las que tiene permiso. El gerente comercial consulta los resultados autorizados y sus explicaciones.',
 'El asistente muestra pasos y comprobaciones antes de aceptar una decisión. Cuando una solicitud no tiene respaldo suficiente, debe explicar la limitación y conservar el trabajo para su revisión. Los manuales y los casos demostrativos facilitan la capacitación, pero su existencia no sustituye una evaluación formal de aprendizaje.'],2)
table('Responsabilidades operativas previstas',['Perfil','Trabajo principal','Resultado esperado'],[
 ['Administrador','Configurar fuentes, inteligencia artificial y acceso.','Servicios y permisos preparados para el trabajo.'],
 ['Analista de inteligencia de negocios','Definir la necesidad y supervisar diseño, carga y conciliación.','Datamart con procedencia y resultados revisables.'],
 ['Gerente comercial','Consultar indicadores, filtros, explicaciones y reportes permitidos.','Información comercial que pueda interpretar y contrastar.']
],[3.4,6.0,5.25],note=DOCNOTE)
block('Factibilidad técnica',[
 'El prototipo utiliza una aplicación web, servicios de negocio, dos motores de base de datos y una integración configurable con modelos de lenguaje. Los contenedores permiten reproducir sus servicios sin instalar manualmente todas las bibliotecas en cada computador. El uso académico de ocho gigabytes de memoria exige operar un ambiente a la vez y comprobar la disponibilidad de recursos.'],2)
table('Tecnologías y función en el prototipo',['Tecnología','Función','Condición de operación'],[
 ['React y TypeScript','Presentar formularios, asistente y panel analítico.','Navegador y conexión con los servicios del sistema.'],
 ['Python y FastAPI','Aplicar permisos, comprobar propuestas y coordinar la carga.','Servicios del servidor disponibles.'],
 ['PostgreSQL','Guardar configuración, propuestas, evidencias y datamarts.','Volúmenes persistentes y migraciones aplicadas.'],
 ['SQL Server 2022','Alojar las bases transaccionales de demostración.','Lectura del origen con credenciales restringidas.'],
 ['Docker Compose','Organizar servicios, redes y volúmenes.','Instalación compatible y recursos locales disponibles.'],
 ['Modelo de lenguaje configurable','Interpretar necesidades y producir sugerencias estructuradas.','Credencial, modelo admitido y cuota del proveedor.'],
 ['Git y verificaciones automáticas','Conservar cambios y comprobar el código antes de integrarlo.','Repositorio y controles vinculados a la versión.']
],[3.45,6.3,4.9],note=DOCNOTE)
block('Factibilidad legal y manejo de la información',[
 'Las fuentes utilizadas son bases de demostración y no corresponden a una empresa participante. SQL Server Developer se emplea para desarrollo y pruebas, conforme a su licencia; la denominación release de un ambiente no lo convierte en un servidor autorizado para explotación productiva (Microsoft, s. f.).',
 'PostgreSQL permite el uso y distribución bajo su licencia abierta. Docker Desktop establece condiciones específicas para educación y otros tipos de uso; su elegibilidad debe comprobarse en cada instalación. Estas condiciones se consideran parte de la preparación técnica (PostgreSQL Global Development Group, s. f.; Docker, s. f.).',
 'Las credenciales se almacenan cifradas y no deben aparecer en capturas, reportes o respuestas del asistente. La revisión de necesidades y propuestas utiliza la estructura autorizada de la fuente. El copiloto analítico trabaja con resultados agregados del contexto seleccionado.',
 'La encuesta recibida es anónima y se presenta mediante frecuencias y porcentajes. Su archivo no contiene nombres ni correos; por ello no se intenta reconstruir la identidad de quienes respondieron.'],2)
block('Factibilidad económica y presupuesto estimado',[
 'El presupuesto se estima para cuatro meses y se expresa en dólares de los Estados Unidos. Se distinguen los desembolsos previstos de los aportes de trabajo y de equipos disponibles. Las cantidades son supuestos de planificación académica; no se presentan como facturas o gastos históricos.',
 'Se supone una dedicación de cuarenta horas mensuales por tesista, durante cuatro meses. Las dos integrantes aportarían trescientas veinte horas en conjunto. La valoración de seis dólares por hora permite estimar el recurso humano sin afirmar que se pagó ese salario.'],2)
table('Presupuesto del trabajo académico',['Participación','Horas estimadas','Valor por hora','Aporte estimado'],[
 ['Lesly Samay Velásquez Anchundia',160,'6,00','960,00'],['Emily Dayan Robles Alvarado',160,'6,00','960,00'],['Total cuantificado',320,'','1.920,00']
],[6.05,2.8,2.8,3.0],note='Valores en dólares. Las funciones de análisis, programación, pruebas y documentación son asumidas por las mismas dos tesistas; no se cuentan como contrataciones adicionales.')
table('Distribución estimada del esfuerzo',['Actividad','Horas del equipo'],[
 ['Análisis y especificación de necesidades',40],['Diseño del sistema y de los datos',30],['Construcción e integración',130],['Pruebas y correcciones',70],['Documentación y preparación de demostración',50],['Total',320]
],[11.0,3.65],note='Estimación de dedicación, no registro histórico de las horas de cada iteración.')
table('Equipos y licencias considerados',['Recurso','Tratamiento presupuestario','Valor estimado'],[
 ['Dos computadores existentes','Uso asignado al proyecto durante cuatro meses.','66,67 de aporte'],
 ['PostgreSQL y componentes abiertos','Sin compra adicional de licencias en este escenario.','0,00 de licencia'],
 ['SQL Server Developer','Edición para desarrollo y pruebas.','0,00 de licencia'],
 ['Contenedores y repositorio','Uso académico dentro de las condiciones disponibles.','0,00 adicional']
],[4.0,7.3,3.35],note='La valoración de equipos es 2 × 600 ÷ 36 × 4 × 0,50 = 66,67. Los 600 dólares por equipo y los 36 meses de uso son supuestos; no son cotizaciones ni una depreciación contable certificada.')
table('Gastos de operación previstos',['Concepto','Base de cálculo','Total estimado'],[[visible(x['recurso']),str(x['cantidad'])+' '+x['unidad']+' × '+money(x['costo_unitario_usd']),money(x['efectivo_usd'])] for x in P['operacion']],[5.25,6.0,3.4],note='Valores estimados para cuatro meses. La reserva del proveedor de inteligencia artificial es un límite de planificación, no consumo ya facturado.')
table('Resumen del presupuesto estimado',['Rubro','Desembolso previsto','Aporte valorizado','Total económico'],[[x[0]]+[money(y) for y in x[1:]] for x in P['resumen']['filas']],[5.35,3.1,3.1,3.1],note='Valores en dólares. Total económico = desembolso previsto + aporte valorizado. La contingencia del 10 % se aplica sólo al efectivo base.')
p('El escenario cuantificado requiere prever 147,22 dólares de desembolso, incluida una contingencia de 13,38. Los aportes estimados suman 1.986,67 dólares y el costo económico base alcanza 2.133,89. Este cálculo permite planificar recursos; no demuestra ahorro, rentabilidad ni una mejora de productividad frente al procedimiento tradicional.')
p('La participación del docente como Scrum Master forma parte de la organización del proyecto. Su dedicación y su eventual valoración no se han cuantificado en los antecedentes recibidos; se reservan para completar el presupuesto si la institución exige incluir ese aporte.')
pending('Información presupuestaria por completar',[
 'Horas y criterio de valoración del acompañamiento del Scrum Master, si corresponde.',
 'Confirmación de dedicación de las tesistas y respaldo de los valores estimados.',
 'Comprobantes de consumos o gastos reales, cuando se desee contrastar la estimación.'])

block('Metodología de investigación',[
 'La investigación es aplicada porque desarrolla una solución a un problema concreto: relacionar una necesidad de análisis de ventas con fuentes disponibles y conservar la coherencia de su transformación. Se apoya en ciencia del diseño, que vincula construcción y evaluación de un artefacto con el problema que pretende atender (Hevner y vom Brocke, 2023).',
 'El componente descriptivo utiliza un cuestionario de opinión sobre la utilidad potencial de las funciones propuestas. El componente técnico examina el recorrido del software y contrasta resultados de origen y destino. Estas evidencias responden a preguntas diferentes: la encuesta describe percepciones y las pruebas comprueban condiciones de funcionamiento.'])
table('Actividades de investigación y evidencia',['Actividad','Aplicación en el proyecto','Evidencia'],[
 ['Delimitación del problema','Precisar necesidad, alcance comercial y fuentes.','Problema, objetivos y requisitos.'],
 ['Diseño y construcción','Definir reglas, interfaz, datos y supervisión.','Especificaciones, código y diagramas.'],
 ['Demostración','Recorrer las dos bases de ejemplo.','Propuestas, ejecuciones y reportes conservados.'],
 ['Evaluación técnica','Comparar filas, unidades, importes y contexto.','Resultados de conciliación y pruebas.'],
 ['Consulta de opinión','Describir utilidad potencial percibida.','Ciento dos cuestionarios anónimos.']
],[3.15,6.8,4.7],note=DOCNOTE)
block('Población de referencia y muestra observada',[
 'La población de interés corresponde a estudiantes de inteligencia de negocios e inteligencia artificial de la carrera de Software de la Universidad de Guayaquil. El enlace del formulario se difundió por correo electrónico y la participación fue voluntaria. Se analizaron las ciento dos respuestas finales entregadas por el responsable del estudio.',
 'En la planificación se consideró una población aproximada de trescientos treinta y un estudiantes. La fórmula institucional empleada como referencia fue n = N ÷ [e² × (N − 1) + 1]. Con N = 331 y e = 0,05 se obtiene 181,37, redondeado a una meta de 182. La población certificada y el registro de personas invitadas aún deben incorporarse.',
 'El número efectivamente disponible es 102, no 182. La convocatoria voluntaria no documenta una selección aleatoria; por ello se describe como muestra no probabilística por participación voluntaria. Los porcentajes de este capítulo describen a quienes respondieron y no se presentan como estimaciones representativas de toda la población con un margen de error del cinco por ciento.'],2)
table('Población y participación disponibles',['Concepto','Dato o condición'],[
 ['Población de interés','Estudiantes de inteligencia de negocios e inteligencia artificial.'],
 ['Población aproximada de planificación','331; pendiente de respaldo institucional.'],
 ['Meta de planificación','182, según el cálculo de referencia.'],
 ['Respuestas finales analizadas','102 registros anónimos.'],
 ['Convocatoria','Enlace enviado por correo y respuesta voluntaria.'],
 ['Número efectivo de personas invitadas','[POR COMPLETAR: listado o constancia de convocatoria].']
],[6.0,8.65],note='La meta calculada y las respuestas recibidas son cantidades distintas. El archivo anónimo no permite verificar personas únicas ni caracterizar las asignaturas de cada participante.')
block('Técnica e instrumento de recolección',[
 'Se utilizó una encuesta con diez preguntas cerradas y una escala de cinco opciones de acuerdo. El instrumento consulta si sería útil disponer de un software con determinadas capacidades; no exige haber utilizado previamente el prototipo. Se conserva el enunciado aplicado para evitar cambiar el significado de las respuestas.',
 'Antes de presentar el cuestionario se aclaran sus términos: inteligencia de negocios se refiere al uso de datos para apoyar decisiones; inteligencia artificial es el apoyo del sistema para interpretar y proponer; extracción, transformación y carga es el proceso que prepara datos desde el origen hasta el datamart. Las abreviaturas que aparecen en los enunciados originales mantienen ese significado.'],2)
table('Opciones de respuesta de la encuesta',['Valor de la escala','Opción completa'],[[x['valor'],x['opcion']] for x in E['preguntas'][0]['frecuencias']],[3.15,11.5],note='Escala empleada en el formulario realmente aplicado. El valor numérico sólo representa el orden de las opciones.')
block('Procesamiento y presentación de los datos',[
 'Se revisaron mil veinte respuestas a preguntas: ciento dos registros por diez preguntas. No se encontraron celdas vacías ni valores fuera de la escala. Las tres columnas adicionales sin preguntas ni respuestas se excluyeron de la tabulación. No se eliminaron patrones de opinión repetidos ni se sustituyeron valores.',
 'Para cada opción se contó la frecuencia y se calculó su porcentaje mediante frecuencia ÷ 102 × 100. Los porcentajes se muestran con dos decimales. El redondeo puede ocasionar una diferencia de una centésima al sumar las opciones. Cada pregunta incluye una tabla, un gráfico de barras horizontales y una interpretación.',
 'Las barras conservan las cinco alternativas, incluso cuando su frecuencia es cero. Utilizan la misma escala de cero a cien por ciento, un único color y etiquetas directas con cantidad y porcentaje. Se evita que la cuadrícula, las líneas decorativas o las abreviaturas dificulten la lectura.'],2)

block('Tabulación y análisis de la encuesta',[
 'Las tablas y barras siguientes describen la utilidad potencial percibida en las ciento dos respuestas.'])
analyses=[
 'La opción Totalmente de acuerdo reúne 64 respuestas (62,75 %) y De acuerdo, 34 (33,33 %). Las cuatro restantes se ubican en la alternativa intermedia. En conjunto, el 96,08 % valora el apoyo para expresar necesidades en lenguaje natural. El resultado orienta una función que ayude a precisar qué se quiere analizar antes de escoger tablas o indicadores.',
 'Se registran 62 respuestas en Totalmente de acuerdo (60,78 %) y 35 en De acuerdo (34,31 %). Cinco personas mantienen una posición intermedia. El 95,10 % de acuerdo conjunto muestra interés en revisar primero si la información existente permite atender la necesidad. Para el sistema, esto implica presentar las fuentes disponibles y comunicar lo que no puede sustentarse.',
 'Sesenta respuestas corresponden a Totalmente de acuerdo (58,82 %) y 34 a De acuerdo (33,33 %); ocho son intermedias. El acuerdo conjunto alcanza el 92,16 %. La distribución favorece una propuesta inicial que organice hechos, dimensiones y medidas, acompañada de explicaciones que el analista pueda revisar.',
 'Cincuenta y seis personas seleccionan Totalmente de acuerdo (54,90 %) y 41 De acuerdo (40,20 %). Las cinco restantes eligen la opción intermedia. El 95,10 % de acuerdo respalda el interés por conocer de dónde procede un indicador. Esta función se refleja en la identificación de tablas, columnas, relaciones y cálculos del diseño.',
 'Se obtienen 60 respuestas en Totalmente de acuerdo (58,82 %) y 35 en De acuerdo (34,31 %); siete son intermedias. El acuerdo conjunto es 93,14 %. La explicación de ventas, costos y márgenes resulta relevante para comprender el sentido comercial de una cifra y revisar si su fórmula utiliza los datos apropiados.',
 'La alternativa Totalmente de acuerdo recibe 52 respuestas (50,98 %) y De acuerdo, 42 (41,18 %). Ocho personas se ubican en la categoría intermedia. El 92,16 % de acuerdo conjunto orienta un apoyo para preparar transformaciones, con reglas visibles y confirmación antes de cargar el datamart.',
 'Sesenta y dos respuestas se sitúan en Totalmente de acuerdo (60,78 %) y 34 en De acuerdo (33,33 %); seis permanecen intermedias. El acuerdo conjunto alcanza el 94,12 %. La supervisión humana es parte de la utilidad esperada: el analista necesita revisar la propuesta y decidir su aprobación antes de autorizar cambios.',
 'La presentación gráfica reúne 60 respuestas en Totalmente de acuerdo (58,82 %) y 38 en De acuerdo (37,25 %); cuatro son intermedias. El acuerdo conjunto es 96,08 %. El resultado apoya una interfaz que comunique indicadores y comparaciones de forma comprensible, conservando filtros y unidades a la vista.',
 'Sesenta y una personas seleccionan Totalmente de acuerdo (59,80 %) y 35 De acuerdo (34,31 %). Seis eligen la alternativa intermedia. El acuerdo conjunto de 94,12 % señala interés por conversar sobre un análisis. El copiloto debe explicar con base en el resultado seleccionado y reconocer las preguntas que sus datos no permiten responder.',
 'Cincuenta y nueve respuestas corresponden a Totalmente de acuerdo (57,84 %) y 35 a De acuerdo (34,31 %); ocho son intermedias. El acuerdo conjunto alcanza el 92,16 %. La utilidad esperada incluye trabajar con varias fuentes y conservar separados sus modelos, procesos y resultados. Esa separación se comprueba después mediante pruebas del sistema.'
]
for i,q in enumerate(E['preguntas']):
 qp=p(q['enunciado_literal'],bold=True,keep=True);qp.paragraph_format.first_line_indent=Cm(0);qp.alignment=WD_ALIGN_PARAGRAPH.LEFT
 qp.paragraph_format.page_break_before=True
 table('Respuestas a la pregunta '+str(i+1),['Opción de respuesta','Frecuencia','Porcentaje'],[[f['opcion'],f['frecuencia_absoluta'],f['porcentaje_mostrado']] for f in q['frecuencias']]+[['Total',102,'100,00 %']],[8.65,2.8,3.2],note='Encuesta aplicada a estudiantes; ciento dos respuestas válidas para esta pregunta.',size=11.5)
 image('Distribución de respuestas a la pregunta '+str(i+1),B/'encuesta/graficos'/f'pregunta_{i+1:02}.png','Elaboración propia con las respuestas reales. Cada etiqueta muestra número de respuestas y porcentaje.',maxh=6.45)
 p('Análisis. '+analyses[i])
block('Interpretación general de la encuesta',[
 'El acuerdo conjunto varía entre 92,16 % y 96,08 % según la pregunta. Las mayores frecuencias favorables corresponden a la formulación de necesidades y a la presentación visual, con noventa y ocho respuestas cada una. Las diferencias entre funciones son pequeñas y se interpretan de forma descriptiva, sin establecer una clasificación estadística de prioridades.',
 'Los resultados muestran una valoración favorable de la idea de un sistema inteligente de apoyo al análisis. La identificación de fuentes, las explicaciones de cálculos y la supervisión humana forman parte de esa valoración. La encuesta aporta evidencia de interés y utilidad esperada; las pruebas técnicas siguientes sustentan las afirmaciones sobre el funcionamiento del prototipo.',
 'La convocatoria voluntaria, la ausencia de datos de caracterización y el sentido favorable de los enunciados limitan la generalización. No se dispone de una validación formal del instrumento por especialistas ni de una medición antes y después del uso.'],2,page=True)
table('Síntesis por función consultada',['Función','Respuestas favorables','Porcentaje'],[[q['tema'],q['acuerdo_4_5_n'],q['acuerdo_4_5_mostrado']] for q in E['preguntas']],[9.05,2.8,2.8],note='Se suman De acuerdo y Totalmente de acuerdo. No se agregan las diez preguntas como si fueran diez veces más participantes.')
pending('Respaldo metodológico por completar',[
 'Constancia institucional de la población aproximada de 331 estudiantes.',
 'Número efectivo de estudiantes que recibieron la invitación.',
 'Ficha de revisión del cuestionario por especialistas, si se incorpora esa validación.'])

block('Metodología de desarrollo',[
 'El trabajo se organizó mediante Scrum, un marco de colaboración que estructura el desarrollo en iteraciones llamadas sprints. Se utilizó para ordenar necesidades, revisar avances y priorizar correcciones. La documentación conserva seis incrementos del producto y una etapa posterior de refinamiento. La colaboración y la revisión del trabajo son condiciones centrales de su aplicación (Verwijs y Russo, 2023).',
 'Las especificaciones del proyecto se conservaron en archivos Markdown, un formato de texto legible. En ellas se describen el problema, el alcance, las reglas, la interacción y los criterios de aceptación. Esta práctica de desarrollo guiado por especificaciones permite relacionar el comportamiento esperado con el código y las pruebas. La organización de requisitos, diseño, construcción y verificación se apoya también en la guía de conocimientos de ingeniería de software de IEEE Computer Society (2024).'],page=True)
block('Equipo y responsabilidades de Scrum',[
 'El Ing. Francisco Xavier Álvarez Solís, docente tutor del proyecto, asume el rol de Scrum Master. Las tesistas Lesly Samay Velásquez Anchundia y Emily Dayan Robles Alvarado integran el equipo de desarrollo. La función de responsable del producto se deja por confirmar para evitar asignar una responsabilidad sin respaldo documental.'],2)
table('Roles de organización del proyecto',['Rol','Participante','Responsabilidad'],[
 ['Scrum Master','Ing. Francisco Xavier Álvarez Solís','Facilitar el marco de trabajo, acompañar la organización del equipo y ayudar a resolver impedimentos.'],
 ['Equipo de desarrollo','Lesly Samay Velásquez Anchundia y Emily Dayan Robles Alvarado','Analizar, diseñar, construir, probar y documentar los incrementos.'],
 ['Responsable del producto','[POR COMPLETAR: nombre y designación]','Priorizar las necesidades y acordar los criterios de aceptación del producto.']
],[3.2,5.35,6.1],note='El rol del docente como Scrum Master responde a la confirmación del responsable académico. Los roles del equipo de proyecto son diferentes de los permisos de usuarios de la aplicación.')
table('Prácticas de organización y registros necesarios',['Práctica','Propósito','Registro que la respalda'],[
 ['Lista priorizada del producto','Ordenar funciones y cambios por valor y dependencia.','Requisitos e historias; priorización histórica por completar.'],
 ['Planificación de la iteración','Precisar el objetivo y el trabajo seleccionado.','Informe de la iteración y acuerdos disponibles.'],
 ['Seguimiento del trabajo','Identificar avance, impedimentos y ajustes.','Bitácora; actas periódicas por completar.'],
 ['Revisión del incremento','Mostrar lo construido y contrastar aceptación.','Pruebas, capturas y revisión del cambio.'],
 ['Retrospectiva','Proponer mejoras en la forma de trabajar.','Registro de acuerdos de mejora por completar.']
],[3.8,5.7,5.15],note='Se explican las prácticas del marco de trabajo sin inventar actas, reuniones diarias, velocidades o puntos de esfuerzo que no constan en los registros.')
block('Iteraciones e incrementos documentados',[
 'Los seis sprints se presentan a partir de sus informes y especificaciones. Las fechas que siguen corresponden a períodos documentados y pueden incluir revisiones acumulativas; no se reinterpretan como un calendario uniforme de reuniones. Las correcciones de noviembre se registran aparte del sexto sprint.'],2)
for i,s in enumerate(G['sprints'][:6],1):
 title='Sprint '+str(i)+' '+s['objetivo']
 table(title,['Elemento','Descripción'],[
 ['Objetivo',visible(s['objetivo'])],['Período registrado',visible(s['periodo_documentado'])],['Trabajo construido',visible(s['incremento'])],['Criterio de cierre',visible(s['limite'])]
 ],[3.6,11.05],note='Elaboración propia a partir del informe de la iteración. Las precisiones del criterio delimitan el resultado acreditado.')
p('Después del cierre se corrigieron situaciones observadas en la revisión de necesidades, el tratamiento de versiones, la periodicidad, los indicadores y las exportaciones. Este refinamiento conserva los seis incrementos y no se presenta como un sprint adicional no planificado.')
block('Historias de usuario y lista priorizada del producto',[
 'Las historias expresan la función esperada desde el punto de vista de quien la necesita. Se presentan con su prioridad, su relación con las iteraciones y condiciones de aceptación. Las siguientes fichas organizan el alcance implementado; los puntos y las horas reales deberán añadirse sólo cuando existan sus registros.'],2)
for i,x in enumerate(G['historias_usuario'],1):
 fields=x['campos'];rows=[]
 for key in ['Historia','Prioridad y sprint','Criterios de aceptación']:
  if key in fields:rows.append((key,fields[key]))
 table('Historia de usuario '+str(i)+' '+clean_names(x['nombre']),['Elemento','Descripción'],rows,[3.7,10.95],note=None,size=11.5)
block('Criterio de trabajo terminado',[
 'Un incremento se considera terminado cuando cumple su comportamiento acordado, conserva las reglas de datos y permisos, supera las pruebas aplicables y dispone de documentación para su revisión. La integración del cambio registra qué versión fue aceptada; publicar imágenes del sistema no sustituye la aceptación funcional.'],2)
table('Riesgos y respuesta prevista',['Riesgo','Efecto posible','Tratamiento'],[
 ['Necesidad sin fuente suficiente','Propuesta comercial no sustentada.','Revisar viabilidad y comunicar exclusiones.'],
 ['Respuesta inválida del proveedor','Interrupción de la generación.','Conservar solicitud, validar formato y permitir recuperación controlada.'],
 ['Mezcla de fuentes o versiones','Indicadores atribuidos al origen incorrecto.','Asociar conexión, metadatos, propuesta y ejecución.'],
 ['Cálculo comercial ambiguo','Razón o importe con interpretación incorrecta.','Revisar fórmula, unidad, denominador y trazabilidad.'],
 ['Recursos o cuota insuficientes','Fallo de demostración o espera.','Comprobar salud y proveedor; disponer de resultados conservados.']
],[4.0,5.0,5.65],note=DOCNOTE)
pending('Registros de gestión por completar',[
 'Designación del responsable del producto.',
 'Fechas y acuerdos de planificación, revisión y retrospectiva disponibles.',
 'Estimaciones y avance por fecha para un gráfico de trabajo pendiente, si se requiere.'])

block('Beneficiarios del proyecto',[
 'Las beneficiarias directas son las tesistas y las personas que estudien el recorrido de inteligencia de negocios con fuentes de demostración. El analista dispone de un proceso guiado para relacionar necesidad, datos y modelo; el perfil gerencial puede consultar información y explicaciones con los permisos correspondientes. El aporte formativo requiere actividades de lectura, práctica y comprobación.'])
table('Productos entregables',['Producto','Contenido','Uso previsto'],[
 ['Prototipo funcional','Aplicación web, persistencia y proceso supervisado.','Demostración y experimentación académica.'],
 ['Especificaciones del sistema','Reglas, requisitos y criterios de aceptación.','Revisión y mantenimiento del comportamiento.'],
 ['Casos y evidencias de prueba','Propuestas, ejecuciones y conciliaciones de ambas bases.','Reproducir y contrastar resultados.'],
 ['Manuales','Operación, formación y documentación técnica.','Aprender el uso y mantener el entorno.'],
 ['Resultados de encuesta','Tablas, barras y análisis de las 102 respuestas.','Describir utilidad potencial percibida.']
],[3.6,6.2,4.85],note=DOCNOTE)

block('Diseño y desarrollo de la propuesta',[
 'El diseño separa la presentación, los servicios, las reglas de comprobación, la persistencia y los adaptadores de fuentes y de inteligencia artificial. La misma cadena de decisiones se aplica a cada fuente configurada; las bases de ejemplo permiten demostrarla con estructuras comerciales diferentes.'],page=True)
block('Requisitos funcionales',[
 'Los requisitos funcionales describen lo que el sistema permite hacer y la condición que debe cumplirse para aceptarlo. La numeración sirve para localizar cada requisito dentro de este capítulo; sus referencias a archivos y pruebas se conservan en la matriz de trabajo del proyecto.'],2)
for start in range(0,len(G['RF']),4):
 group=G['RF'][start:start+4]
 table('Requisitos funcionales '+str(start+1)+' a '+str(start+len(group)),['Número y función','Comportamiento verificable'],[[str(start+j+1)+' '+x['requisito'],x['criterio_aceptacion']+(('\n'+x['precision_corte_noviembre']) if x.get('precision_corte_noviembre') else '')] for j,x in enumerate(group)],[4.5,10.15],note=DOCNOTE,size=11.5)
block('Requisitos no funcionales',[
 'Los requisitos no funcionales precisan condiciones de calidad, como seguridad, conservación del contexto y facilidad de revisión. Se expresan dentro del alcance de la prueba de concepto y no como una certificación general del producto.'],2)
for start in range(0,len(G['RNF']),4):
 group=G['RNF'][start:start+4]
 table('Condiciones de calidad '+str(start+1)+' a '+str(start+len(group)),['Número y atributo','Condición verificable','Límite'],[[str(start+j+1)+' '+x['requisito'],x['condicion_y_comprobacion'],x['limite']] for j,x in enumerate(group)],[3.8,6.95,3.9],note=DOCNOTE,size=11.5)
block('Casos de uso del sistema',[
 'Los casos de uso describen cómo una persona o servicio participa en una función, qué debe estar preparado y qué ocurre cuando la operación termina o se rechaza. Los escenarios alternativos forman parte del diseño: una falta de permiso o una respuesta sin evidencia deben producir una explicación controlada.'],2)
for i,x in enumerate(G['casos_uso'],1):
 h('Caso de uso '+str(i)+' '+clean_names(x['nombre']),3)
 fields=x['campos'];rows=[]
 for key,val in fields.items():
  if any(t in key.lower() for t in ['trazabilidad','evidencia']):continue
  rows.append((key,val))
 table('Descripción del caso de uso '+str(i),['Elemento','Especificación'],rows,[3.7,10.95],note=None,size=11.5)

block('Arquitectura del sistema',[
 'La arquitectura muestra qué responsabilidad cumple cada parte y cómo circula la información. La interfaz del navegador solicita acciones a los servicios del servidor. Estos comprueban los permisos y las reglas, consultan la fuente autorizada y conservan propuestas, ejecuciones y datos analíticos en PostgreSQL.',
 'El proveedor de inteligencia artificial es configurable y no aprueba diseños ni ejecuta escrituras por su cuenta. La aplicación controla el contenido enviado y comprueba lo recibido. La lectura del origen se mantiene separada de la creación del datamart.'],2,page=True)
arch=B/'arquitectura/Arquitectura_general_BI_IA.png'
if arch.exists():
 geometry(D.add_section(WD_SECTION_START.NEW_PAGE),True)
 image('Arquitectura general del sistema inteligente de datamarts',arch,'Elaboración propia a partir de los componentes implementados. Las fuentes de demostración utilizan SQL Server; PostgreSQL conserva el trabajo y los datamarts.',maxh=13.0)
 geometry(D.add_section(WD_SECTION_START.NEW_PAGE),False)
 p('El recorrido puede leerse desde la persona usuaria hacia la interfaz, las comprobaciones y los datos. Cada propuesta conserva su fuente de origen. La aprobación humana habilita la preparación de la carga; la conciliación comprueba el resultado antes de publicarlo para análisis.')
else:raise RuntimeError('Falta imagen profesional de arquitectura')
block('Modelos de interacción y datos',[
 'Los diagramas utilizan el Lenguaje Unificado de Modelado para representar responsabilidades, actividades, secuencias, componentes y estados. El modelo dimensional final resume hechos de ventas y dimensiones de análisis. Sus nombres son conceptuales: el modelo físico se deriva de la propuesta y de los metadatos de cada fuente.'],2)
manifest=json.loads((B/'ingenieria/diagramas/manifiesto_diagramas.json').read_text())
for d in manifest:
 if d['id']=='06_despliegue':
  geometry(D.add_section(WD_SECTION_START.NEW_PAGE),True)
  image(d['titulo'],B/'ingenieria/diagramas'/Path(d['png']).name,d.get('pie','Elaboración propia.'),maxh=12.8)
  geometry(D.add_section(WD_SECTION_START.NEW_PAGE),False)
 else:
  h(d['titulo'],3,page=True)
  image(d['titulo'],B/'ingenieria/diagramas'/Path(d['png']).name,d.get('pie','Elaboración propia.'),maxh=18.8)

block('Reglas comerciales y decisiones de diseño',[
 'Una misma cifra puede tener significados diferentes según su grano y su fórmula. El grano expresa qué representa una fila: por ejemplo, una línea de pedido o de factura. Por eso no se confunde el número de líneas con el número de pedidos distintos.',
 'Los descuentos expresados como tasa requieren una operación para obtener un importe monetario. El costo total combina el costo unitario y las unidades cuando las referencias están comprobadas. Las razones por unidad y los márgenes deben declarar su denominador, la base de venta y el alcance utilizado.'],2)
table('Reglas que conservan el significado del análisis',['Situación','Criterio aplicado'],[
 ['Conteo de documentos','Contar identificadores distintos del pedido o factura, sin sustituirlos por filas.'],
 ['Cálculo de descuento','Distinguir una tasa de un importe; utilizar una receta comprobada cuando corresponda.'],
 ['Costo y margen','Usar las fuentes verificadas y declarar la operación de cálculo.'],
 ['Moneda sin comprobación','Presentar moneda de origen; no asignar dólares por conveniencia.'],
 ['Periodicidad','Conservar la periodicidad efectiva de la propuesta y de la ejecución.'],
 ['Cliente y territorio','Utilizar relaciones verificadas; no inferir historia de entregas a partir de una dirección actual.'],
 ['Fuentes y ejecuciones','Consultar indicadores dentro de la conexión y la ejecución seleccionadas.']
],[4.3,10.35],note=DOCNOTE)
block('Construcción e integración del prototipo',[
 'La construcción se implementó por módulos conectados mediante servicios. Las verificaciones se ejecutan en el servidor y no dependen solamente de que un botón esté visible. Los cambios se conservan mediante control de versiones y se revisan antes de integrar la rama de desarrollo y promover una versión de referencia.',
 'La puesta en marcha utiliza contenedores independientes y volúmenes persistentes. La entrega portable incorpora las imágenes y las bases de demostración para reproducir el entorno; los secretos de una instalación anterior no forman parte de una copia limpia.'],2)
table('Módulos y resultado de cada etapa',['Etapa','Función de la plataforma','Resultado'],[
 ['Preparación','Conexiones, permisos y modelo de inteligencia artificial.','Fuente habilitada y acceso controlado.'],
 ['Comprensión de la fuente','Lectura y exploración de metadatos.','Instantánea estructural identificada.'],
 ['Contexto comercial','Catálogo y necesidad del análisis.','Preguntas y objetivo que orientan la propuesta.'],
 ['Diseño supervisado','Conceptos, modelo y revisión humana.','Versión aprobada y trazable.'],
 ['Transformación y carga','Preparación, confirmación y ejecución.','Tablas analíticas y expediente de resultados.'],
 ['Conciliación y consulta','Contraste, panel, copiloto y reportes.','Datos revisables para el análisis.']
],[3.3,6.2,5.15],note=DOCNOTE)

block('Validación de la propuesta',[
 'La validación reúne criterios de aceptación, pruebas del software y conciliaciones numéricas. El encadenamiento fuente, metadatos, propuesta y ejecución permite identificar el origen de cada resultado. Los casos principales corresponden a la campaña operativa del seis de noviembre de 2026, con nuevas propuestas y cargas sobre ambas fuentes. Los antecedentes del cinco de noviembre se identifican por separado y conservan su historial.'],page=True)
table('Condiciones para ejecutar y cerrar una prueba',['Momento','Condiciones'],[
 ['Antes de la prueba','Servicios disponibles; fuente identificada; credenciales de lectura; metadatos y permisos preparados; proveedor disponible cuando la función lo requiera.'],
 ['Al terminar','Resultado esperado contrastado; cantidades y contexto revisados; incidencias registradas; evidencia conservada; limitaciones comunicadas.']
],[3.3,11.35],note=DOCNOTE)
block('Plan de pruebas y resultados documentados',[
 'Cada prueba se presenta con una situación, un resultado esperado y el resultado obtenido que consta en las evidencias. Cuando no existe una campaña completa, el estado se conserva como pendiente. Las pruebas automáticas complementan los recorridos de uso; no se sustituyen por la opinión recogida en la encuesta.'],2)
for i,x in enumerate(G['plan_pruebas_actualizado'],1):
 status='Pendiente de campaña específica' if i==12 else 'Comprobación documentada'
 table('Prueba '+str(i)+' '+x['escenario'],['Elemento','Descripción'],[
 ['Situación de prueba',x['escenario']],['Resultado esperado',x['resultado_esperado']],['Resultado obtenido',x['resultado_documentado']],['Estado',status]
 ],[3.7,10.95],note='Elaboración propia con verificaciones automáticas, recorridos de la interfaz y expedientes del proyecto. Cada resultado indica si corresponde a la campaña del 6 de noviembre o a un antecedente.',size=11.5)
block('Resultados de las verificaciones automáticas',[
 'El cierre de la campaña registra quinientas treinta pruebas de servicios y cincuenta pruebas de interfaz satisfactorias. Se comprobaron además el análisis de tipos, el formato, la compilación y los controles de integración aplicables. Estos resultados acreditan las condiciones ensayadas y no una ausencia de errores para cualquier situación o entorno.'],2)
block('Corrección de relaciones y conservación del historial',[
 'La auditoría permitió identificar una dificultad que los totales generales no detectan: dos relaciones pueden conservar el número de filas y, aun así, representar funciones comerciales diferentes. En la fuente de facturas se distinguió al comprador del destinatario de facturación y la ciudad de entrega de la dirección postal. La necesidad revisada exigía al comprador y la ciudad de entrega de su ficha actual.',
 'La corrección incorporó la conservación de las relaciones exactas revisadas. Esos vínculos se comprobaron contra las claves de la instantánea y se utilizaron tanto en la carga como en la procedencia del análisis. Las dos selecciones contradictorias se rechazaron desde la interfaz. Si la evidencia no permite resolver una alternativa de forma inequívoca, se requiere una decisión guiada del analista antes de aprobar.',
 'Las nuevas versiones utilizaron las reglas de compilación 5. Los contratos anteriores conservaron sus reglas, huellas y expedientes para consulta; las nuevas cargas requieren una versión derivada revisada con las reglas actuales. Por ello, una diferencia entre roles comerciales no se interpreta como pérdida de datos ni se corrige retirando automáticamente una aprobación histórica.'],2)
for source in G['casos_verificados']:
 name=source['base_de_datos'];isaw=name=='AdventureWorks2022'
 h('Caso de demostración con '+name,2)
 rows=[['Grano del análisis','Línea de pedido' if isaw else 'Línea de factura'],['Filas del origen',f"{source['filas_origen']:,}".replace(',','.')],['Filas del datamart',f"{source['filas_destino']:,}".replace(',','.')],['Diferencia de filas','0'],['Importe total','109.846.381,40 dólares' if isaw else '198.043.439,45 en moneda de origen'],['Unidades','274.914' if isaw else '8.950.628'],['Documentos distintos','31.465 pedidos' if isaw else '70.510 facturas'],['Promedio por documento','3.491,07 dólares por pedido' if isaw else '2.808,73 en moneda de origen por factura'],['Periodicidad','Mensual: 38 períodos' if isaw else 'Mensual: 41 períodos'],['Relación territorial','Territorio comercial registrado en el pedido.' if isaw else 'Provincia de la ciudad de entrega de la ficha actual del comprador de la factura.'],['Resultado conservado',f"Propuesta aprobada {source['propuesta']} y ejecución {source['ejecucion']}"]]
 table('Resultados conciliados de '+name,['Elemento revisado','Resultado documentado'],rows,[5.35,9.3],note='Los números de propuesta y ejecución permiten localizar el resultado en la plataforma. Los importes se redondean a dos decimales para su lectura; la evidencia conserva la precisión de cálculo.')
 if isaw:p('El caso conserva la línea de venta y el identificador del pedido. El promedio por pedido divide el importe por pedidos distintos y no por líneas. En el filtro de 2013 y Northwest se documentaron 6.015.174,74 dólares, 17.452 unidades y 2.053 pedidos; el promedio filtrado fue 2.929,94 dólares por pedido.')
 else:p('El caso utiliza facturas y mantiene la denominación moneda de origen porque no se acreditó una moneda única. Para 2015 y California se documentaron 3.191.769,11, 142.247 unidades y 1.179 facturas; el promedio filtrado fue 2.707,18 por factura. Se contrastaron también 3.771 líneas con una consulta independiente del sistema de origen que utilizó al comprador y su ciudad de entrega. Estos valores pertenecen a esta fuente y no se combinan con AdventureWorks ni se comparan como equivalentes al filtro de un expediente histórico basado en otro rol de cliente.')
block('Revisión del copiloto y las exportaciones',[
 'El copiloto debe responder sobre la fuente, la ejecución y los filtros seleccionados. En los rankings, la participación se calcula sobre el total filtrado completo, no sobre la suma de los elementos visibles. Las explicaciones deben distinguir una descripción de los datos de una relación causal que no ha sido demostrada.',
 'Las exportaciones revisadas conservaron el contexto, las unidades y los filtros. En AdventureWorks se comprobó un informe de seis páginas y un libro de seis hojas en vista analítica: resumen, cuatro visualizaciones y trazabilidad. Los archivos de WideWorldImporters se revisaron con el contexto de la ejecución 22. El número de páginas y hojas depende de la vista y de los gráficos incluidos; no se fija como condición universal del producto.'],2)
block('Comparación operativa de proveedores de inteligencia artificial',[
 'La evidencia disponible permite describir qué ocurrió con cada proveedor dentro de la campaña documentada. Para establecer superioridad de calidad o eficiencia sería necesario repetir las mismas tareas, los mismos metadatos y criterios, y registrar intentos, tiempos y consumo en condiciones comparables.'],2)
table('Resultados disponibles por proveedor',['Proveedor','Resultado observado','Interpretación'],[
 ['Anthropic Claude','Recorridos documentados con ambas fuentes, propuestas, conciliación y copiloto; correcciones comunes tras incidencias iniciales.','Es el proveedor con el recorrido más completo de esta campaña.'],
 ['Groq','Conectividad mínima comprobada; el intento de generación comparable encontró un límite de cuota.','El intento incompleto no permite una comparación equivalente de calidad.'],
 ['Otros proveedores configurables','No se dispone de una campaña homogénea completa en el registro utilizado.','Compatibilidad de configuración no equivale a resultado comparativo demostrado.']
],[3.4,6.45,4.8],note='La disponibilidad y las cuotas son condiciones de operación. No se declara un ganador universal ni equivalencia automática de niveles de razonamiento entre proveedores.')
pending('Evaluación formal por especialistas',[
 'Nombres, perfiles, experiencia y aceptación de participación de los especialistas.',
 'Instrumento y criterios de revisión técnica, comercial y de facilidad de uso.',
 'Dictámenes, observaciones y firmas de las evaluaciones realmente realizadas.'])
block('Alcance de la validación y trabajo pendiente',[
 'Los dos recorridos conservados muestran la construcción supervisada y la conciliación de resultados en las fuentes de demostración. La generalidad del diseño se apoya en reglas comunes y contexto por fuente; su ampliación a otros motores y situaciones requiere nuevas comprobaciones.',
 'Quedan por completar la campaña autenticada de todos los perfiles, la evaluación formal por especialistas y, si se desea sostener eficiencia comparativa, la medición equivalente de tiempo, esfuerzo y costo. Estos elementos se identifican como información pendiente, no como resultados ya obtenidos.'],2)
table('Información pendiente para completar el cierre académico',['Información','Qué debe incorporarse','Dónde se utilizará'],[
 ['Población e invitación','Constancia del universo y número de estudiantes invitados.','Descripción de población y participación.'],
 ['Validación del instrumento','Revisión de contenido por especialistas, si se realiza.','Calidad del cuestionario.'],
 ['Gestión de Scrum','Designación del responsable del producto y acuerdos disponibles.','Equipo, planificación y seguimiento.'],
 ['Horas y gastos','Dedicación del tutor y respaldo de los supuestos.','Presupuesto y valoración de aportes.'],
 ['Perfiles de usuario','Sesiones y resultados por analista, gerente y operador.','Validación de permisos y navegación.'],
 ['Juicio de especialistas','Dictámenes y observaciones firmadas.','Aceptación formal de la propuesta.']
],[3.65,6.5,4.5],note='Esta matriz permite incorporar los respaldos cuando estén disponibles, sin sustituirlos por datos inventados.')

h('Referencias citadas en el capítulo',page=True)
refs=[
 'Docker. (s. f.). Docker Desktop license agreement. Recuperado el 6 de noviembre de 2026, de https://docs.docker.com/subscription-billing/desktop-license/',
 'Hevner, A. R., y vom Brocke, J. (2023). A proficiency model for design science research education. Journal of Information Systems Education, 34(3), 264-278. https://jise.org/volume34/n3/JISE2023v34n3pp264-278.html',
 'IEEE Computer Society. (2024). Guide to the Software Engineering Body of Knowledge Version 4.0 (H. Washizaki, Ed.). https://www.computer.org/education/bodies-of-knowledge/software-engineering',
 'Microsoft. (s. f.). Editions and supported features of SQL Server 2022. Recuperado el 6 de noviembre de 2026, de https://learn.microsoft.com/en-us/sql/sql-server/editions-and-components-of-sql-server-2022?view=sql-server-ver16',
 'PostgreSQL Global Development Group. (s. f.). PostgreSQL License. Recuperado el 6 de noviembre de 2026, de https://www.postgresql.org/about/licence/',
 'Universidad de Guayaquil. (s. f.). Guía Elaboración Trabajo Integración Curricular Proyecto Desarrollo [Guía institucional proporcionada para este trabajo].',
 'Verwijs, C., y Russo, D. (2023). A theory of Scrum team effectiveness. ACM Transactions on Software Engineering and Methodology, 32(3), artículo 74, 1-51. https://doi.org/10.1145/3571849'
]
for ref in refs:
 pp=p(ref);pp.paragraph_format.left_indent=Cm(1.27);pp.paragraph_format.first_line_indent=Cm(-1.27);pp.alignment=WD_ALIGN_PARAGRAPH.LEFT

# Mantener sólo las relaciones efectivamente utilizadas por el capítulo reconstruido.
used=set()
for elem in D.part.element.iter():
 for a in ['embed','link','id']:
  v=elem.get(qn('r:'+a))
  if v:used.add(v)
for rid,rel in list(D.part.rels.items()):
 if 'comments' in rel.reltype.lower() or (rid not in used and any(token in rel.reltype for token in ['/image','/hyperlink','/header','/footer'])):D.part.drop_rel(rid)
D.save(OUT)
(B/'contenido_capitulo3_revisado.json').write_text(json.dumps({'titulo':D.core_properties.title,'tablas':TABLE,'figuras':FIG,'contenido':LOG},ensure_ascii=False,indent=2))
print(json.dumps({'docx':str(OUT),'tablas':TABLE,'figuras':FIG,'parrafos':len(D.paragraphs),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()},ensure_ascii=False))
