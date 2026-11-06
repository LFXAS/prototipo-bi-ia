"""Fuente editable de dos figuras de arquitectura. Sólo genera SVG; no accede a la aplicación."""
from pathlib import Path
from html import escape
import json

ROOT=Path(__file__).resolve().parent
C={'ink':'#142B3D','muted':'#486171','teal':'#008D91','navy':'#21485E','border':'#B6D1DA','pale':'#F1F7FA','mint':'#E5F5F2','white':'#FFFFFF','orange':'#AD6C12','amber':'#FFF5E4'}
FONT='DejaVu Sans, Arial, sans-serif'
class Svg:
 def __init__(self,title,desc):
  self.a=[f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1130" viewBox="0 0 1600 1130" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{C['teal']}"/></marker><marker id="arrowNavy" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="{C['navy']}"/></marker></defs><rect width="1600" height="1130" fill="white"/>''']
 def rect(self,x,y,w,h,fill='white',stroke=None,r=18,sw=2):
  self.a.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke or C["border"]}" stroke-width="{sw}"/>')
 def text(self,x,y,t,size=28,bold=False,color=None,anchor='start'):
  self.a.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color or C["ink"]}" text-anchor="{anchor}">{escape(t)}</text>')
 def line(self,x1,y1,x2,y2,color=None,sw=3,arrow=False,both=False,dash=False):
  c=color or C['teal'];m='arrowNavy' if c==C['navy'] else 'arrow'
  self.a.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{sw}"'+(' stroke-dasharray="9 7"' if dash else '')+(f' marker-end="url(#{m})"' if arrow else '')+(f' marker-start="url(#{m})"' if both else '')+'/>')
 def circle(self,x,y,r,fill=None,stroke=None,sw=2):
  self.a.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill or C["mint"]}" stroke="{stroke or C["teal"]}" stroke-width="{sw}"/>')
 def person(self,x,y):
  self.circle(x+20,y+12,10,C['white'],C['teal'],3)
  self.a.append(f'<path d="M{x+3},{y+47}v-9a17,17 0 0 1 34,0v9" fill="none" stroke="{C["teal"]}" stroke-width="3" stroke-linecap="round"/>')
 def monitor(self,x,y):
  self.rect(x,y,49,31,C['white'],C['teal'],5,3);self.line(x+24,y+32,x+24,y+42,sw=3);self.line(x+11,y+44,x+38,y+44,sw=3)
 def server(self,x,y):
  for yy in [y,y+17,y+34]:
   self.rect(x,yy,47,12,C['white'],C['teal'],3,2);self.circle(x+8,yy+6,2,C['teal'],C['teal'],1)
 def database(self,x,y):
  self.a.append(f'<g transform="translate({x},{y}) scale(0.65)"><path d="M0,9v35c0,12 50,12 50,0V9" fill="{C["white"]}" stroke="{C["teal"]}" stroke-width="3"/><ellipse cx="25" cy="9" rx="25" ry="9" fill="{C["mint"]}" stroke="{C["teal"]}" stroke-width="3"/><path d="M0,27c0,12 50,12 50,0" fill="none" stroke="{C["teal"]}" stroke-width="2"/></g>')
 def node(self,x,y):
  self.line(x+23,y+23,x+4,y+4,sw=3);self.line(x+23,y+23,x+42,y+4,sw=3);self.line(x+23,y+23,x+4,y+42,sw=3);self.line(x+23,y+23,x+42,y+42,sw=3)
  for xx,yy in [(4,4),(42,4),(4,42),(42,42)]:self.circle(x+xx,y+yy,6,C['white'],C['teal'],2)
  self.circle(x+23,y+23,10,C['mint'],C['teal'],3)
 def save(self,path):path.write_text('\n'.join(self.a)+ '\n</svg>\n',encoding='utf-8')

def build(kind):
 detailed=kind=='detallada'
 title='Arquitectura de la plataforma inteligente de BI' if detailed else 'Cómo funciona la plataforma de ventas con IA'
 desc=('Cuatro servicios base en Docker: interfaz React, servidor FastAPI, SQL Server de sólo lectura con AdventureWorks2022 y WideWorldImporters, y PostgreSQL como persistencia y destino analítico. El proveedor de inteligencia artificial configurable intercambia sólo contexto autorizado con FastAPI. Una persona autorizada aprueba antes de la carga controlada y conciliada.')
 s=Svg(title,desc)
 s.text(64,76,title,44,True)
 s.text(64,124,'Acceso y acciones según los permisos de cada persona',30,color=C['muted'])
 roles=[(64,'Administrador','Configura los accesos'),(575,'Analista de BI','Revisa y aprueba'),(1086,'Gerente comercial','Consulta resultados')]
 for x,t,sub in roles:
  s.rect(x,158,450,108,C['white'],C['border'],16);s.person(x+22,181)
  s.text(x+83,200,t,30,True);s.text(x+83,239,sub,28,color=C['muted'])
 labels=[('Necesidad y','viabilidad'),('Propuesta y','revisión'),('Aprobación','humana'),('Carga y','conciliación'),('Analítica y','reportes')]
 for i,(a,b) in enumerate(labels):
  x=64+i*299
  fill=C['amber'] if i==2 else C['mint'];stroke=C['orange'] if i==2 else C['border']
  s.rect(x,300,276,100,fill,stroke,15)
  s.circle(x+34,350,23,C['white'],C['orange'] if i==2 else C['teal'],2)
  s.text(x+34,361,str(i+1),32,True,C['orange'] if i==2 else C['teal'],'middle')
  s.text(x+73,340,a,28,True);s.text(x+73,375,b,28,True)
  if i<4:s.line(x+283,350,x+291,350,sw=2,arrow=True)
 s.rect(64,430,1000,653,C['pale'],C['border'],22)
 s.text(96,466,'Servicios base en contenedores Docker',30,True)
 s.rect(96,486,936,121,C['white'],C['border'],16)
 s.monitor(122,519)
 s.text(190,531,'Interfaz web' if detailed else 'Pantallas para trabajar con ventas',34,True)
 s.text(190,578,'React · Vite en desarrollo · Nginx en entrega' if detailed else 'Necesidades, propuestas, cargas y resultados',28,color=C['muted'])
 s.line(552,616,552,641,sw=1.5,arrow=True)
 s.line(576,641,576,616,sw=1.5,arrow=True)
 s.rect(96,654,936,218,C['white'],C['teal'],18,3)
 s.server(122,680)
 s.text(190,694,'Servidor de aplicación' if detailed else 'La plataforma comprueba y construye',34,True)
 if detailed:s.text(1008,694,'FastAPI',30,True,C['teal'],'end')
 rows=['Permisos, configuración y auditoría','Metadatos, catálogo y propuestas revisadas','Carga controlada, conciliación y análisis'] if detailed else ['Comprueba las fuentes y la propuesta','Ejecuta la carga aprobada y verifica los datos','Prepara los indicadores y las respuestas del copiloto']
 for i,t in enumerate(rows):
  y=748+i*42;s.circle(136,y-9,6,C['teal'],C['teal'],1);s.text(160,y,t,28)
 # Los datos del origen sólo fluyen hacia el servidor. El destino admite carga y lectura.
 s.line(126,937,126,888,sw=2,arrow=True)
 s.text(160,918,'Sólo lectura del origen',28,color=C['muted'])
 s.line(1000,889,1000,935,sw=2,arrow=True,both=True)
 s.text(610,918,'Carga y consulta',28,color=C['muted'])
 s.rect(96,948,430,125,C['white'],C['border'],16)
 s.database(120,962);s.text(168,985,'SQL Server',32,True)
 s.text(120,1025,'AdventureWorks2022',28)
 s.text(120,1060,'WideWorldImporters',28)
 s.rect(602,948,430,125,C['white'],C['border'],16)
 s.database(626,962);s.text(674,985,'PostgreSQL',32,True)
 s.text(626,1025,'Configuración e historial',28)
 s.text(626,1060,'Datamarts de ventas',28)
 # Integración configurable: ningún acceso directo del proveedor a las bases.
 s.text(1120,468,'Contexto autorizado',30,True)
 for y,t in [(515,'Metadatos de estructura'),(555,'Resúmenes analíticos'),(595,'Sin credenciales')]:s.text(1120,y,t,28,color=C['muted'])
 s.rect(1120,654,416,218,C['white'],C['teal'],18,3)
 s.text(1144,693,'Proveedor de',32,True)
 s.text(1144,733,'inteligencia artificial',32,True)
 s.text(1144,778,'Configurable',28,color=C['teal'])
 s.text(1144,824,'Local o en la nube',28,color=C['muted'])
 s.line(1041,741,1110,741,sw=3,arrow=True)
 s.line(1110,824,1041,824,C['navy'],3,True,False,True)
 s.line(1120,921,1173,921,sw=3,arrow=True);s.text(1192,931,'Solicitud permitida',28,color=C['muted'])
 s.line(1173,968,1120,968,C['navy'],3,True,False,True);s.text(1192,978,'Salida revisable',28,color=C['muted'])
 s.text(64,1118,'Las fuentes se leen; no se modifican. La IA propone y una persona autorizada aprueba.',28,True)
 filename='Arquitectura_detallada_BI_IA.svg' if detailed else 'Arquitectura_general_BI_IA.svg'
 s.save(ROOT/filename)
 return {'archivo':filename,'titulo':title,'descripcion':desc,'dimensiones_svg':[1600,1130],'version':'Detalle técnico' if detailed else 'Explicación general para formación'}

if __name__=='__main__':
 out=[build('detallada'),build('general')]
 (ROOT/'figuras.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print('SVG creados:',', '.join(x['archivo'] for x in out))
