from pathlib import Path
import json,subprocess,hashlib
from PIL import Image
B=Path(__file__).resolve().parent/'diagramas';B.mkdir(exist_ok=True)
JAR=Path('/home/ceo/Documentos/ChatGPT/Tesis 2026 CII/tesis-coherencia-UG-20261018/tools/plantuml-1.2025.10.jar')
style='''@startuml
skinparam backgroundColor white
skinparam monochrome true
skinparam shadowing false
skinparam defaultFontName DejaVu Sans
skinparam defaultFontSize 16
skinparam ArrowFontSize 15
skinparam NoteFontSize 14
skinparam Padding 6
skinparam nodesep 24
skinparam ranksep 28
skinparam dpi 180
skinparam wrapWidth 220
skinparam maxMessageSize 190
skinparam sequenceMessageAlign center
hide empty members
hide circle
skinparam classAttributeIconSize 0
'''
diagrams=[]
def add(name,title,kind,body,caption,sources):
 p=B/(name+'.puml');p.write_text(style+body+'\n@enduml\n')
 diagrams.append(dict(id=name,titulo=title,tipo=kind,fuente_editable=str(p),svg=str(p.with_suffix('.svg')),png=str(p.with_suffix('.png')),pie=caption,fuentes_verificacion=sources))
add('01_casos_uso','Casos de uso y responsabilidades','Diagrama UML de casos de uso',r'''
left to right direction
actor "Administrador" as ADM
actor "Analista de negocios" as ANA
actor "Gerente comercial" as GER
actor "Proveedor de\ninteligencia artificial" as IA
rectangle "Sistema inteligente de datamarts de ventas" {
 usecase "Administrar acceso\ny configuración" as ACC
 usecase "Preparar fuentes\ny metadatos" as MET
 usecase "Mantener catálogo\nde preguntas" as CAT
 usecase "Formular y comprobar\nla necesidad" as NEC
 usecase "Generar y revisar\nla propuesta" as PROP
 usecase "Aprobar una versión" as APR
 usecase "Cargar y conciliar\nel datamart" as ETL
 usecase "Consultar panel\ny aplicar filtros" as PANEL
 usecase "Preguntar al copiloto\ny exportar resultados" as CHAT
}
ADM -- ACC
ADM -- MET
ADM -- CAT
ANA -- MET
ANA -- CAT
ANA -- NEC
ANA -- PROP
ANA -- APR
ANA -- ETL
ANA -- PANEL
ANA -- CHAT
GER -- PANEL
GER -- CHAT
IA -- NEC
IA -- PROP
IA -- CHAT
note bottom of ETL
La aprobación y la ejecución de la carga
requieren decisiones humanas separadas.
end note
note bottom of ADM
Las asociaciones describen responsabilidades.
Cada acción requiere el permiso del usuario.
end note
''','Vista de responsabilidades funcionales agrupadas. Los permisos se comprueban en el servidor; el proveedor de inteligencia artificial no aprueba ni ejecuta cargas. Los casos detallados se presentan en sus tablas.',['docs/specs/SPR-02-01-seguridad-rbac.md','docs/specs/SPR-03-02-propuesta-bi-asistida-por-ia.md','backend/app/modules/copilot/router.py'])
add('02_actividad_supervision','Actividad del ciclo de análisis supervisado','Diagrama UML de actividad',r'''
skinparam ConditionStyle InsideDiamond
start
:Analista\nElegir fuente y formular necesidad;
:Sistema\nComprobar contexto y permisos;
:Inteligencia artificial\nEvaluar necesidad con los metadatos;
if (¿Viabilidad suficiente?) then (no)
 :Analista\nRevisar limitación y corregir solicitud;
 stop
else (sí)
 :Inteligencia artificial\nProponer conceptos y modelo;
 :Sistema\nVerificar referencias y cálculos;
 if (¿Propuesta válida?) then (no)
  :Sistema\nConservar intento y explicar bloqueo;
  stop
 else (sí)
  :Analista\nRevisar y aprobar una versión;
  :Analista\nElegir indicadores y revisar el plan;
  if (¿Confirma la carga?) then (no)
   stop
  else (sí)
   :Sistema\nLeer origen sin modificarlo;\ncargar y comparar origen con destino;
   if (¿Resultado publicable?) then (no)
    :Sistema\nRegistrar diferencias y bloquear publicación;
    stop
   else (sí)
    :Analista\nRevisar nombres, unidades y advertencias;
    :Usuario autorizado\nAnalizar, conversar y exportar;
    stop
   endif
  endif
 endif
endif

''','El flujo distingue la comprobación de la necesidad, la generación, la aprobación y la ejecución. Una respuesta inválida o una diferencia bloqueante no se presenta como resultado publicado.',['docs/specs/SPR-03-02-propuesta-bi-asistida-por-ia.md','docs/specs/SPR-04-01-seleccion-propuesta-y-validacion-etl.md'])
add('03_secuencia_propuesta','Generación y aprobación de una propuesta','Diagrama UML de secuencia',r'''

autonumber
actor "Analista" as A
participant "Servidor" as S
database "Registro\ndel proyecto" as D
participant "Proveedor de\ninteligencia artificial" as IA
A -> S : Revisar necesidad y fuente
S -> D : Leer contexto autorizado
S -> IA : Evaluar viabilidad
IA --> S : Revisión de la necesidad
S --> A : Revisión validada
A -> S : Solicitar propuesta
S -> IA : Proponer conceptos y modelo
IA --> S : Propuesta estructurada
S -> S : Validar referencias y cálculos
alt Respuesta inválida
 S --> A : Bloquear y explicar
else Respuesta válida
 S -> D : Guardar versión revisable
 S --> A : Propuesta y advertencias
 A -> S : Aprobar tras la revisión
 S -> D : Registrar aprobación validada
 S --> A : Confirmar sin ejecutar carga
end
legend bottom
El servidor conserva el objetivo original y verifica los permisos.
La inteligencia artificial propone; la aprobación es humana.
endlegend

''','La secuencia conserva el objetivo de negocio y la procedencia de los metadatos. Los bloqueos no se omiten y la aprobación permanece bajo control humano.',['backend/app/modules/copilot/router.py','backend/app/modules/copilot/service.py','backend/app/modules/copilot/models.py'])
add('04_secuencia_etl','Carga y conciliación de un datamart','Diagrama UML de secuencia',r'''

autonumber
actor "Analista" as A
participant "Servicio\nde carga" as S
database "Registro\nde ejecución" as R
database "Base\nde origen" as O
database "Datamart\nde destino" as D
A -> S : Preparar propuesta e indicadores
S -> R : Recuperar contrato y metadatos
S -> S : Validar y construir el plan
S --> A : Presentar plan y advertencias
A -> S : Confirmar la ejecución
S -> O : Leer los datos aprobados
O --> S : Datos de origen
S -> D : Cargar el datamart
S -> O : Consultar totales de referencia
S -> D : Consultar totales cargados
S -> S : Conciliar origen y destino
alt Fallo o diferencia bloqueante
 S -> R : Registrar fallo y bloqueo
else Resultado válido
 S -> R : Registrar conciliación
 S --> A : Habilitar revisión del resultado
end
legend bottom
El origen permanece en sólo lectura.
Cada ejecución tiene un destino y una procedencia propios.
endlegend

''','El servicio construye operaciones controladas y registra las diferencias. La existencia de tablas no sustituye la conciliación entre cantidades e importes del origen y del destino.',['backend/app/modules/etl/router.py','backend/app/modules/etl/service.py','backend/app/modules/etl/materializer.py'])
add('05_componentes','Componentes del sistema','Diagrama UML de componentes',r'''
top to bottom direction
component "Interfaz web" as UI
interface "Servicios autorizados" as SERV
rectangle "Aplicación del servidor" {
 component "Acceso y auditoría" as SEC
 component "Fuentes y metadatos" as MET
 component "Diseño y aprobación" as COP
 component "Carga y conciliación" as ETL
 component "Analítica y reportes" as ANA
 component "Validaciones comunes" as VAL
}
database "Registro del proyecto\ny datamarts" as PG
database "Fuente SQL Server" as SQL
cloud "Proveedor de\ninteligencia artificial" as IA
UI --> SERV
SERV --> SEC
SERV --> MET
SERV --> COP
SERV --> ETL
SERV --> ANA
COP ..> MET : utiliza contexto
COP ..> VAL : verifica propuesta
ETL ..> VAL : verifica plan
ETL ..> COP : utiliza aprobación
ANA ..> ETL : utiliza ejecución válida
MET --> SQL : consulta estructura
ETL --> SQL : sólo lectura
COP --> IA : necesidad y metadatos
ANA --> IA : agregados autorizados
SEC --> PG
MET --> PG
COP --> PG
ETL --> PG
ANA --> PG
note bottom of SQL
El conector SQL Server se comprobó con dos bases.
Otros motores requieren conector y pruebas propias.
end note
''','Los componentes separan presentación, acceso, fuentes, propuesta, carga y consumo analítico. Las reglas comunes evitan depender de nombres de una única base o de un único proveedor.',['docs/architecture.md','docs/specs/SPR-06-01-contexto-multifuente-sqlserver.md','compose.yaml'])
add('06_despliegue','Despliegue local de la demostración','Diagrama UML de despliegue',r'''
top to bottom direction
node "Equipo de la demostración" as PC {
 node "Navegador" as NAV
 frame "Entorno Docker del proyecto" {
  node "Contenedor de interfaz" as WEB
  node "Contenedor del servidor" as BACK
  node "Contenedor PostgreSQL" as POST {
   database "Configuración, evidencia\ny datamarts" as PG
  }
  node "Contenedor SQL Server" as SQL {
   database "AdventureWorks" as AW
   database "WideWorldImporters" as WWI
  }
  artifact "Tareas de inicio\nMigraciones y carga básica" as INIT
 }
 artifact "Volumen persistente\nde PostgreSQL" as VP
 artifact "Volumen persistente\nde SQL Server" as VS
 artifact "Volumen separado\nde clave maestra" as VK
}
cloud "Servicio de\ninteligencia artificial" as IA
NAV --> WEB : acceso local
WEB --> BACK : servicios de la aplicación
BACK --> POST : configuración y resultados
BACK --> SQL : lectura de origen
BACK --> IA : canal cifrado
INIT --> POST : preparar estructura
POST --> VP : persistencia
SQL --> VS : persistencia
BACK --> VK : recuperar clave de cifrado
legend bottom
Entorno local comprobado con datos persistentes.
Desarrollo y versión estable mantienen recursos propios.
endlegend
''','Los contenedores de datos conservan su información en volúmenes. La clave maestra se mantiene separada de las credenciales cifradas y las tareas de inicio no son servicios de uso permanente.',['compose.yaml','compose.release.yaml','infra/postgres/initdb/001-schemas.sql'])
add('07_clases_dominio','Entidades del ciclo de diseño y carga','Diagrama UML de clases conceptuales',r'''
skinparam ranksep 64
top to bottom direction
class "Fuente de datos" as FUENTE {
 Nombre de conexión
 Base de datos
 Estado de habilitación
}
class "Versión de metadatos" as META {
 Estructura capturada
 Huella de integridad
}
class "Catálogo de análisis" as CAT {
 Dominio de análisis
 Preguntas y opciones
}
class "Revisión de necesidad" as REV {
 Huella de la necesidad
 Evaluación de viabilidad
}
class "Propuesta" as PROP {
 Modelo y medidas
 Estado de revisión
 Advertencias y decisión
}
class "Ejecución de carga" as EJEC {
 Plan de carga
 Estado y responsable
 Resultados de conciliación
}
class "Credencial cifrada" as CLAVE {
 Tipo de credencial
 Contenido cifrado
}
class "Configuración del proveedor" as IA {
 Proveedor y modelo
 Estado de comprobación
}
FUENTE "1" -- "0..*" META : dispone de
FUENTE "1" -- "0..*" CAT : configura
META "1" -- "0..*" REV : fundamenta
META "1" -- "0..*" PROP : sustenta
META "1" -- "0..*" EJEC : identifica origen
PROP "1" -- "0..*" EJEC
PROP "0..1" <-- "0..*" PROP : versión de origen
CLAVE "1" -- "0..1" FUENTE
CLAVE "0..1" -- "0..1" IA
note bottom of CAT
Cada catálogo corresponde a una fuente y dominio.
Los números indican cuántos registros se relacionan.
end note
note bottom of PROP
Las etiquetas traducen las entidades persistentes.
Se muestran sólo atributos seleccionados.
end note
''','Vista conceptual verificada con las entidades persistentes de la aplicación. Las multiplicidades expresan las relaciones conservadas; la identidad de una propuesta corregida remite a su versión de origen.',['backend/app/modules/parameters/models.py','backend/app/modules/metadata/models.py','backend/app/modules/copilot/models.py','backend/app/modules/etl/models.py'])
add('08_estados_propuesta','Estados y decisiones de una propuesta','Diagrama UML de estados',r'''

hide empty description
state "Generación en curso" as G
state "Fallo del proveedor" as F
state "Validación bloqueante" as V
state "Lista para revisión" as R
state "Aprobada" as A
state "Rechazada" as RE
state "Aprobación retirada" as I
state "Descartada" as D
[*] --> G : solicitar
G --> F : fallo
G --> V : no cumple
G --> R : cumple
R --> A : aprobar
R --> RE : rechazar
R --> V : bloqueo
A --> A : consultar
A --> I : retirar
I --> A : restaurar
R --> D : descartar
V --> D : descartar
F --> D : descartar
RE --> D : descartar
I --> D : descartar
legend bottom
Consultar no retira una aprobación y aprobar no ejecuta la carga.
Las decisiones requieren permiso y las comprobaciones aplicables.
Corregir o regenerar crea otra versión.
endlegend

''','Los estados traducen los valores implementados. La consulta de evidencia no cambia una aprobación; retirar, restaurar o descartar exige una acción autorizada.',['backend/app/modules/copilot/router.py','backend/app/modules/copilot/models.py'])
add('09_modelo_estrella_logico','Modelo dimensional lógico de ventas','Modelo lógico dimensional de referencia',r'''
skinparam ranksep 64

hide methods
class "Producto" as PROD {
 Clave de referencia
 Clave del producto en el origen
 Atributos aprobados
}
class "Cliente" as CLI {
 Clave de referencia
 Clave del cliente en el origen
 Atributos aprobados
}
class "Venta al detalle" as VENTA {
 Claves del registro de origen
 Unidades e importes aprobados
 Referencias de dimensiones
 Ejecución de procedencia
}
class "Fecha" as FECHA {
 Clave de referencia
 Fecha del origen
 Períodos de análisis aprobados
}
class "Territorio" as TER {
 Clave de referencia
 Clave del territorio en el origen
 Atributos aprobados
}
PROD "0..1" -- "0..*" VENTA
CLI "0..1" -- "0..*" VENTA
VENTA "0..*" -- "0..1" FECHA
VENTA "0..*" -- "0..1" TER
legend bottom
Modelo lógico de referencia, no esquema físico fijo.
Las dimensiones dependen del contrato aprobado.
Las referencias sin coincidencia requieren control de calidad.
endlegend

''','Esquema lógico ilustrativo, no un diseño físico fijo para todas las fuentes. Cada ejecución determina sus dimensiones, atributos y medidas a partir del contrato aprobado. Las posibles ausencias de coincidencia se controlan durante la carga.',['backend/app/modules/etl/materializer.py','docs/specs/SPR-04-02-kpis-controlados-y-calculables.md'])
# Renderizado exclusivamente local, sin consultas de red ni ejecución de la aplicación.
assert JAR.is_file()
for fmt in ['svg','png']:
 result=subprocess.run(['java','-Djava.awt.headless=true','-DPLANTUML_LIMIT_SIZE=12000','-jar',str(JAR),'-charset','UTF-8','-t'+fmt,*[str(B/(d['id']+'.puml')) for d in diagrams]],capture_output=True,text=True)
 (B/('render_'+fmt+'.log')).write_text(result.stdout+result.stderr)
 assert result.returncode==0,result.stderr
for d in diagrams:
 png=Path(d['png']);svg=Path(d['svg']);assert png.is_file() and svg.is_file()
 assert 'Syntax Error' not in svg.read_text() and '<svg' in svg.read_text()
 with Image.open(png) as im:d['ancho_px'],d['alto_px']=im.size
 d['sha256']={ext:hashlib.sha256(Path(d[ext]).read_bytes()).hexdigest() for ext in ['png','svg','fuente_editable']}
(B/'manifiesto_diagramas.json').write_text(json.dumps(diagrams,ensure_ascii=False,indent=2)+'\n')
print('9diagramasSVGPNGPUMLgenerados',[(d['id'],d['ancho_px'],d['alto_px']) for d in diagrams])
