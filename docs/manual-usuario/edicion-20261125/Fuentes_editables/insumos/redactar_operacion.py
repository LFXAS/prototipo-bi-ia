from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from hashlib import sha256
import json

W=Path(__file__).resolve().parents[1]
if (Path(__file__).resolve().parent/'actualizacion_20261125'/'actualizaciones_operacion.json').exists():
    raise SystemExit('Guion histórico del 18 de noviembre: no sobrescribe la edición 2.0. Edite los JSON vigentes y ejecute fuentes/generar_manual.py.')

R=Path('/home/ceo/Proyectos/BI')
OLD=R/'docs/manual-usuario/edicion-2026-11-06/contenido_formacion.json'
old=json.loads(OLD.read_text())
historic={s['clave']:s for s in old['unidades'] if s['clave'] in {'caso_aw','caso_wwi'}}
sections=[]
def sec(code,title,role,objective,intro,concepts,fields,steps,ai,rules,approval,result,errors,exercise,qa,**extra):
    item={'codigo':code,'titulo':title,'roles':role,'objetivo_de_aprendizaje':objective,
          'introduccion':intro,'conceptos':[{'termino':a,'explicacion':b} for a,b in concepts],
          'campos_y_controles':[{'campo':a,'significado_y_criterio':b} for a,b in fields],
          'pasos':[{'numero':i,'accion':a,'resultado_que_debe_observar':b} for i,(a,b) in enumerate(steps,1)],
          'que_hace_la_IA':ai,'que_valida_la_plataforma':rules,'que_decide_o_aprueba_la_persona':approval,
          'resultado_esperado':result,'errores_y_recuperacion':[{'situacion':a,'accion':b} for a,b in errors],
          'ejercicio':exercise,'autoevaluacion':[{'pregunta':a,'respuesta_orientativa':b} for a,b in qa],**extra}
    sections.append(item)

sec('BI01','Antes de empezar piense qué decisión necesita apoyar',['Analista de BI','Gerente comercial'],
'Distinguir la pregunta comercial, el evento y el nivel de detalle antes de pedir un datamart.',
['Un datamart reúne datos organizados para un análisis concreto. En este proyecto el punto de partida es una necesidad de ventas escrita por una persona. La plataforma ayuda a relacionarla con la estructura disponible y conserva las decisiones que llevan hasta el tablero.',
 'Antes de abrir el asistente, escriba qué quiere comparar, con qué indicador, por qué entidades y en qué período. Elija si observa pedidos o facturas. Un pedido representa una solicitud de venta; una factura representa otro evento. Sus importes no demuestran por sí solos cobro, entrega realizada o utilidad.',
 'La interfaz ofrece un proceso común para fuentes distintas. La demostración comprobada utiliza dos bases SQL Server. Cambian sus tablas, claves y significados; no debe copiarse la elección técnica de una base a otra sólo porque los botones son iguales.'],
[('Hecho','Registro del evento que se analizará, por ejemplo una línea de pedido o una línea de factura.'),
 ('Granularidad o grano','Qué representa exactamente una fila del hecho. Decir una línea de factura permite comprobar qué se conserva y evita llamar factura a cada línea.'),
 ('Dimensión','Información que permite agrupar y describir el hecho: fecha, producto, cliente o territorio. Una clave identifica; un nombre ayuda a interpretar.'),
 ('Medida','Valor asociado al hecho, como cantidad, importe de línea o identificador del documento que se contará de forma distinta.'),
 ('Indicador','Cálculo con una finalidad comercial: total de unidades, facturas distintas o importe por factura. Debe tener fórmula, unidad, alcance y procedencia.'),
 ('Agregación','Forma de resumir varias filas. Sumar, contar y promediar responden preguntas distintas.'),
 ('Procedencia','Cadena que identifica fuente, instantánea de metadatos, propuesta, ejecución y relaciones empleadas.')],
[('Fuente en contexto','Base elegida para trabajar. Debe coincidir con la necesidad, los metadatos y el resultado consultado.'),
 ('Dominio Ventas','Perfil funcional implementado. No convierte automáticamente en ventas todas las tablas de la base.')],
[('Escriba una decisión concreta, por ejemplo priorizar productos según unidades registradas cada mes.','Una necesidad que se puede contrastar con datos, sin pedir todavía una conclusión causal.'),
 ('Precise el evento: pedido o factura, y la fila mínima que desea conservar.','Un grano explícito, como una línea de pedido.'),
 ('Anote los indicadores y sus unidades.','Por ejemplo importe, unidades, pedidos distintos e importe por pedido, sin confundirlos.'),
 ('Identifique la fuente y revise su esquema antes de generar la propuesta.','Tablas y relaciones de esa base, sin suponer que tener un nombre parecido demuestra el significado.')],
['En esta preparación la persona define el propósito. La IA podrá sugerir una redacción y un diseño, pero todavía no existe evidencia de que una propuesta haya sido aprobada o cargada.'],
['Los controles posteriores comprobarán referencias, relaciones y recetas. La disponibilidad de una columna no demuestra por sí sola calidad, vigencia histórica o suficiencia de registros.'],
['El analista decide el evento y los significados; la gerencia aporta la decisión comercial que desea apoyar.'],
'Una ficha de necesidad que se pueda leer y explicar antes de pulsar Generar.',
[('El objetivo dice analizar todas las ventas para mejorar el negocio.','Acótelo: indique evento, indicador, comparación y límite. Evite pedir que el sistema demuestre por adelantado un aumento de ventas.')],
{'consigna':'Con un pedido que tiene tres líneas, indique cuántas filas de hecho y cuántos pedidos distintos habría.','respuesta_orientativa':'Tres filas a grano de línea y un pedido distinto. Contar filas no da el número de pedidos.'},
[('¿Un gráfico de importe prueba rentabilidad?','No. Harían falta costos comparables y una definición de margen, entre otros datos.'),('¿Una base nueva exige programar un tablero específico con su nombre?','El recorrido es común; primero se configuran y comprueban sus metadatos y decisiones. La compatibilidad real requiere los adaptadores y operaciones implementados.')])

sec('BI02','Asistente paso 1 escribir o elegir una necesidad',['Analista de BI'],
'Completar el objetivo, las preguntas, la periodicidad y la autorización de metadatos sin perder el propósito comercial.',
['Entre a Asistente de datamart con la fuente correcta y seleccione el dominio de ventas. El recorrido tiene cinco etapas: Necesidad, Conceptos, Propuesta, Personalización y Revisión.',
 'Puede comenzar con su propio texto o pedir sugerencias con la estructura de la fuente. Las sugerencias no sustituyen el objetivo automáticamente: primero se leen su explicación, evidencia y límites; después se pulsa Usar esta necesidad.'],
[('Objetivo del análisis','Describe qué necesita conocer la persona. Debe conservar el evento y las limitaciones que importan al negocio.'),
 ('Preguntas de negocio','Orientaciones del catálogo de esta fuente. Seleccionarlas no fija por sí solo tablas, dimensiones ni fórmulas.'),
 ('Periodicidad','Forma temporal de resumir o presentar el análisis. Elegir Mensual no significa programar una recarga automática cada mes ni reducir el hecho necesariamente a una fila mensual.')],
[('Objetivo del análisis','Texto de 20 a 2.000 caracteres. Escriba qué comparar, indicadores, grano y límites. No escriba SQL.'),
 ('Destino','Identifica el proveedor/configuración que recibirá la necesidad y los metadatos autorizados.'),
 ('Autorizo enviar estos metadatos y la necesidad al proveedor indicado para esta revisión','Habilita la asistencia para ese destino. Si cambia el proveedor se debe revisar de nuevo el consentimiento.'),
 ('Preguntas de negocio disponibles','Casillas con etiqueta y explicación. Una pregunta no disponible no se convierte en viable por forzar su selección.'),
 ('Periodicidad','Seleccione una opción disponible del catálogo, por ejemplo Mensual.'),
 ('Sugerir necesidades con esta fuente','Solicita posibles objetivos desde los metadatos; no necesita que ya haya una propuesta.'),
 ('Ayúdame a formular la necesidad','Propone una redacción a partir del objetivo y preguntas existentes. Requiere un objetivo suficiente y preguntas seleccionadas.'),
 ('Usar esta redacción / Mantener mi redacción','Permite aceptar la propuesta textual o conservar el texto propio.')],
[('Compruebe nombre de fuente e instantánea visibles antes de redactar.','El objetivo quedará asociado a esa estructura, no a otra base.'),
 ('Seleccione preguntas que respondan a la decisión, sin marcar todo por costumbre.','Alcance entendible y coherente con el catálogo de esta fuente.'),
 ('Elija periodicidad y autorice el destino que aparece en pantalla.','Asistencia habilitada para el proveedor indicado.'),
 ('Escriba la necesidad o pulse Sugerir necesidades con esta fuente.','Texto propio o varias opciones con fundamento y limitaciones.'),
 ('Si usa Ayúdame a formular la necesidad, compare la propuesta con el original.','La redacción conserva el evento, indicadores y límites; no añade pronósticos ni otra fuente.'),
 ('Use sólo el texto que represente su necesidad y compruebe su viabilidad.','La plataforma inicia una revisión previa; todavía no se aprueba ni se ejecuta ETL.')],
['Sugiere objetivos y mejora redacciones con el contexto estructural autorizado. Su respuesta pasa controles de formato y de referencias antes de ofrecerse como utilizable.'],
['Existencia de instantánea, catálogo y proveedor utilizables; longitud y selección requeridas; destino del consentimiento; referencias y semántica admitida en la revisión de necesidad. Cambiar objetivo, preguntas o periodicidad invalida la revisión anterior.'],
['El analista elige si usa una sugerencia y confirma que el texto representa la necesidad. Autorizar metadatos no equivale a aprobar el diseño ni la carga.'],
'Una necesidad vigente, entendida y lista para la comprobación previa.',
[('No se habilita el botón de asistencia.','Revise permiso de generación, proveedor activo y probado, autorización, instantánea y los campos requeridos.'),
 ('La IA cambió el evento o añadió costos no solicitados.','Mantenga su texto o corríjalo antes de continuar; no acepte una ampliación sólo por estar bien redactada.'),
 ('No aparecen sugerencias utilizables.','Lea el aviso, redacte un alcance más sencillo y compruebe la viabilidad; no se inventan datos faltantes.')],
{'consigna':'Redacte dos versiones del mismo objetivo: una vaga y otra que precise evento, grano, indicador y comparación.','respuesta_orientativa':'La segunda debe permitir reconocer qué salida se revisará; por ejemplo unidades por producto y mes conservando cada línea de pedido.'},
[('¿Usar esta necesidad ejecuta una carga?','No. Sólo coloca el texto elegido; se revisan preguntas y viabilidad antes de generar.'),('¿Mensual programa el ETL?','No. Es periodicidad analítica; el inicio de la carga sigue siendo una acción explícita.')])

sec('BI03','Comprender la viabilidad antes de generar',['Analista de BI'],
'Interpretar directo, derivable, ambiguo y no disponible sin confundir la estructura con datos ya comprobados.',
['La revisión actual combina un análisis de la IA con reglas de la plataforma. Su objetivo es relacionar la necesidad con nombres, tipos, claves y relaciones de la instantánea. No consulta todas las filas del negocio para demostrar resultados.',
 'Una derivación inequívoca puede resolverse al construir la propuesta mediante una ruta declarada o una fórmula controlada. Una interpretación candidata de IA sigue pendiente de validación: su frase no se ejecuta como fórmula libre.'],
[('Directo','Existe una referencia estructural adecuada comprobada para el requisito.'),
 ('Derivable por relación','El requisito puede obtenerse recorriendo vínculos verificados sin cambiar indebidamente el grano.'),
 ('Derivable por fórmula','Puede calcularse con entradas compatibles y una operación permitida, por ejemplo precio × tasa de descuento × cantidad.'),
 ('Ambiguo','Existen opciones o significados que requieren una definición del analista; una relación válida no basta para decidir su rol comercial.'),
 ('No disponible','La revisión no encuentra respaldo suficiente para esa capacidad dentro del alcance actual.'),
 ('Limitación aceptada','Constancia de que se entiende una ausencia; no crea una fuente ni demuestra que el requisito se cumpla.')],
[('Viabilidad contra los metadatos','Resumen de requisitos y evidencia. Lea cada tarjeta además del total de estados.'),
 ('Ver evidencia técnica','Muestra las referencias/rutas que sustentan el requisito.'),
 ('Fórmula controlada','Receta propuesta por las reglas con entradas identificadas.'),
 ('Interpretación propuesta por IA no ejecutable','Descripción que todavía debe convertirse y validarse en un contrato permitido.'),
 ('Comprendo esta limitación y acepto continuar sin que el sistema invente una solución','Aceptación individual de requisitos ambiguos o ausentes; no debe marcarse sin leer.'),
 ('Generar conceptos y propuesta','Usa la revisión vigente y las limitaciones expresamente aceptadas para generar una propuesta.')],
[('Lea el resumen de viabilidad y abra la evidencia de cada requisito importante.','Identifica qué está respaldado y qué requiere una decisión.'),
 ('En las derivaciones, compruebe si se trata de relación o fórmula y qué entradas usa.','No se pide completar SQL ni buscar una columna sólo para quitar el aviso.'),
 ('Si un requisito imprescindible es ambiguo o ausente, vuelva a la necesidad y aclárelo.','El objetivo no promete una salida imposible.'),
 ('Acepte sólo limitaciones que permitan todavía responder la pregunta útil del caso.','Queda un alcance válido y las ausencias no se ocultan.'),
 ('Genere y después revise De la necesidad al datamart.','Cada requisito debe aparecer cubierto, resuelto, limitado o pendiente, sin descarte silencioso.')],
['Examina la necesidad dentro del contexto de la fuente y aporta requisitos y explicaciones. La respuesta se combina con el análisis estructural y los controles de referencias.'],
['Referencias, relaciones, semántica admitida, alcance del evento y huella de entrada. La aprobación posterior vuelve a comprobar el contrato; aceptar una limitación no omite los controles bloqueantes.'],
['El analista aclara ambigüedades, reduce alcance cuando corresponde y decide qué limitaciones son aceptables.'],
'Una revisión vigente y un alcance defendible antes del diseño.',
[('La necesidad tiene respaldo estructural y luego falla la propuesta.','Son controles distintos. La viabilidad no garantiza que el proveedor entregue un contrato válido; revise el error y reintente o ajuste el diseño.'),
 ('El sistema pide validar otra vez.','Compruebe si cambió el objetivo, periodicidad, preguntas, fuente o destino del proveedor; una aceptación anterior no debe reutilizarse a ciegas.'),
 ('Una casilla de limitación parece desbloquear todo.','El botón puede permitir continuar con un alcance parcial, pero no fabrica la capacidad ausente ni habilita SQL libre.')],
{'consigna':'Explique qué haría si se pide margen y sólo se encuentra importe de venta.','respuesta_orientativa':'No afirmar margen; comprobar si hay costo comparable verificable, aclarar el alcance o aceptar que esa salida no estará disponible.'},
[('¿Derivable significa que la alumna debe escribir una fórmula SQL?','No. Las rutas/fórmulas inequívocas se resuelven mediante operaciones controladas. Una ambigüedad se decide con evidencia.'),('¿Viabilidad demuestra que todas las filas están bien?','No. Acredita respaldo estructural; la carga y conciliación revisarán datos concretos.')])

sec('BI04','Asistente paso 2 revisar los conceptos',['Analista de BI'],
'Seleccionar conceptos a partir de evidencia y usar el copiloto como apoyo a una decisión explícita.',
['La pantalla Conceptos encontrados traduce la necesidad en conceptos vinculados a referencias técnicas. La confianza alta no reemplaza revisar qué tabla representa el evento. Los conceptos con evidencia débil pueden quedar excluidos preventivamente.',
 'El copiloto de conceptos es distinto del chat del tablero: aquí explica la conveniencia de incluir una entidad en el diseño, no analiza todavía los importes cargados.'],
[('Concepto de negocio','Idea que la persona reconoce, como producto, cliente o territorio, asociada a columnas o tablas verificables.'),
 ('Confianza','Orientación de revisión; no es una medición de precisión universal del LLM.'),
 ('Inclusión excepcional','Decisión consciente de incluir un concepto cuya evidencia exige atención. Después debe superar la nueva validación.')],
[('Incluir','Casilla que conserva o excluye el concepto de la siguiente propuesta.'),
 ('Ver evidencia y cómo resolver','Expone origen técnico, comprobaciones y orientación.'),
 ('Confirmar inclusión excepcional','Se usa si el concepto con evidencia débil se mantiene incluido; no inventa una relación.'),
 ('Consultar al copiloto','Abre conversación del concepto con objetivo, referencias y expediente.'),
 ('Pregunta para el copiloto','Entre 10 y 500 caracteres. Pregunte qué significa la relación o qué riesgo tiene incluirla.'),
 ('Aplicar recomendación','Cambia la selección según la recomendación de incluir/excluir; exige una acción de la persona.'),
 ('Generar propuesta BI','Continúa con la selección; si cambia el alcance de conceptos puede generar otra versión con IA.')],
[('Lea nombre, descripción, confianza y estado de cada tarjeta.','Identifica por qué una entidad está incluida o excluida.'),
 ('Abra la evidencia de los conceptos con revisión requerida.','Relaciona el nombre comercial con las referencias reales.'),
 ('Pregunte al copiloto por riesgos, claves y consecuencias si aún no puede justificar la selección.','Obtiene una explicación contextual con evidencia citada.'),
 ('Excluya lo que no responda al objetivo o confirme expresamente una inclusión excepcional sustentada.','No quedan decisiones pendientes de inclusión.'),
 ('Pulse Generar propuesta BI.','Se obtiene el contrato para revisar; se conserva trazabilidad si se generó otra versión.')],
['Explica riesgo, consecuencias de incluir/excluir y recomendación. La conversación no modifica selecciones por sí sola.'],
['Las referencias y el contrato resultante vuelven a validarse. No se permite continuar sin conceptos ni con decisiones de inclusión pendientes.'],
['El analista decide la selección y aplica o rechaza la recomendación.'],
'Un conjunto de conceptos que la alumna pueda justificar en lenguaje de negocio.',
[('La IA recomienda incluir pero la evidencia no demuestra la relación.','No aplique la recomendación sólo por su tono. Excluya o defina el negocio y revise una nueva propuesta.'),
 ('Quedan conceptos por confirmar.','Confirme únicamente los que entiende y puede sostener, o desmárquelos para continuar con un alcance menor.')],
{'consigna':'Pregunte: ¿qué riesgo tendría incluir este concepto en el datamart? Registre una evidencia y una decisión.','respuesta_orientativa':'La decisión debe relacionar el concepto con la necesidad; la recomendación de IA no equivale a aprobación.'},
[('¿Consultar al copiloto carga datos?','No. Esta conversación usa el expediente y metadatos del diseño; no ejecuta el ETL.'),('¿Excluir un concepto elimina información del origen?','No. Lo retira del alcance de la propuesta.')])

sec('BI05','Asistente paso 3 leer el diseño propuesto',['Analista de BI'],
'Explicar grano, hecho, medidas, dimensiones, indicadores y cobertura antes de personalizar o aprobar.',
['La propuesta es un contrato de diseño que responde a la necesidad. Empiece por el grano y el evento; después revise medidas y relaciones.',
 'Una propuesta puede tener más indicadores que los cuatro de una práctica. La cantidad depende de la generación. Revise cuáles responden al objetivo y no memorice una cantidad universal de tarjetas.'],
[('Clave del grano','Columna o combinación que identifica la fila mínima. En una fuente puede ser una clave simple y en otra una combinación.'),
 ('Proveniencia de una medida','Referencias y fórmula que explican de dónde sale el valor.'),
 ('Identidad descriptiva','Nombre reconocible de la entidad y su tipo cuando corresponde. No basta mostrar sólo una clave técnica.'),
 ('Cobertura','Correspondencia entre cada requisito del objetivo y las salidas que realmente incluye el contrato.')],
[('Granularidad y Clave del grano','Qué conserva el hecho; no confundir periodicidad mensual con grano físico de línea.'),
 ('Hecho y medidas','Para cada medida se muestran nombre, agregación, origen y fórmula.'),
 ('Dimensiones y Columnas de origen','Atributos con los que se describirán y agruparán los hechos.'),
 ('Campos que creará el ETL','Nombres/tipos descriptivos derivados por rutas verificadas; no son columnas que ya existan necesariamente en la fuente.'),
 ('KPIs propuestos','Funciones analíticas planteadas; compare su significado con medida y denominador.'),
 ('De la necesidad al datamart','Muestra cobertura directa, resolución automática, limitación aceptada o decisión pendiente.'),
 ('Comprobar nombres y cobertura','Con permiso apropiado realiza una muestra controlada de la fuente para revisar identidad descriptiva. La muestra permanece en la plataforma y no se envía al LLM.'),
 ('Plan ETL declarativo','Explica operaciones permitidas; esta vista no ejecuta la carga.'),
 ('Ajustes automáticos / Validaciones y advertencias','Lea qué se corrigió y qué sigue exigiendo revisión.'),
 ('Detalles técnicos y trazabilidad','Instantánea, huella, proveedor/modelo y observaciones originales. Una observación del proveedor no es una comprobación de la plataforma.')],
[('Lea resumen y explicación de negocio.','El evento coincide con lo solicitado.'),
 ('Compruebe grano y claves.','Puede explicar qué representa una fila y cómo se identifica.'),
 ('Compare cada medida con origen y fórmula.','Una tasa no está presentada como dinero ni un promedio de línea como promedio por pedido.'),
 ('Revise dimensiones, rutas e identidad descriptiva.','Cliente y territorio representan el rol solicitado, con nombre y origen claros.'),
 ('Lea la cobertura requisito por requisito.','No se promete una salida omitida.'),
 ('Revise el plan, ajustes y errores/advertencias.','Cero errores bloqueantes antes de aprobar; los avisos se entienden.'),
 ('Elija Personalizar propuesta o Continuar a revisión.','Pasa a una decisión humana sustentada.')],
['Propone el modelo y una explicación. Las decisiones originales se conservan para trazabilidad aunque el contrato validado haya aplicado correcciones.'],
['Existencia de tablas/columnas, tipos, claves, rutas de relación, coherencia del contrato y operaciones calculables; cobertura de requisitos y reglas semánticas implementadas.'],
['El analista decide si el modelo representa el evento comercial y si necesita ajustes.'],
'Un diseño comprensible y defendible, o una lista concreta de correcciones.',
[('Aparecen compras u otro evento en una necesidad de ventas.','No apruebe por tener referencias existentes. Revise alcance y genere una versión que corresponda al evento.'),
 ('Hay nombres como Cliente 123 en lugar de identidad comprobada.','Revise nombres y cobertura con el permiso necesario; no dé por demostrada una entidad descriptiva sólo por su clave.'),
 ('Error bloqueante en una fórmula.','Abra Personalización y excluya o reasigne una receta compatible; si faltan entradas, genere una propuesta nueva con alcance sustentado.')],
{'consigna':'Explique al jurado una medida sin leer sólo su nombre: indique origen, operación, unidad y grano.','respuesta_orientativa':'Por ejemplo importe registrado de línea, sumado sobre líneas de pedido; no denominarlo cobro ni utilidad.'},
[('¿Todos los campos mostrados ya existen en el origen?','No. Algunos son campos descriptivos que el ETL creará a partir de relaciones verificadas.'),('¿Comprobar nombres y cobertura envía nombres de clientes al LLM?','La muestra controlada permanece en la plataforma según la interfaz; no se remite al modelo para esa comprobación.')])

sec('BI06','Asistente paso 4 ajustar medidas y relaciones con criterio',['Analista de BI'],
'Crear una versión corregida sin inventar estructuras ni perder las decisiones anteriores.',
['Personalizar crea una versión nueva. El contrato original conserva su historia. Compare siempre la regla del contrato actual con la regla del borrador: marcar algo en el borrador todavía no lo vuelve ejecutable.',
 'Hay dos acciones de guardado diferentes. Guardar como nueva versión aplica los ajustes generales; Crear versión con relación corregida registra la decisión guiada de relación de manera independiente. Guarde y revise cada resultado antes de encadenar otra corrección.'],
[('Suma','Combina importes o unidades aditivos del mismo significado y alcance.'),
 ('Conteo','Cuenta valores no nulos de la columna seleccionada. A grano de línea no equivale automáticamente a documentos.'),
 ('Conteo distinto','Cuenta una vez cada identificador distinto. Un pedido con varias líneas se cuenta una vez en el universo consultado.'),
 ('Promedio','Media de los valores de las filas; AVG de importe de línea mide importe medio por línea, no por pedido.'),
 ('Mínimo y máximo','Extremos de los valores del campo. La línea de mayor importe no identifica necesariamente al producto con mayor suma de ventas.'),
 ('Relación muchos a uno','Varias filas del hecho apuntan a una fila única de dimensión; la unicidad ayuda a conservar el detalle.'),
 ('Rol de una relación','Significado del vínculo. Comprador y destinatario de facturación pueden ser clientes válidos, pero responden preguntas diferentes.')],
[('Resumen de negocio','Hasta 160 caracteres; describe el ajuste sin alterar lo que las fuentes pueden demostrar.'),
 ('Granularidad propuesta','Hasta 240 caracteres; el texto debe corresponder a claves y hechos reales, no basta renombrar el grano.'),
 ('Dimensiones incluidas / Medidas incluidas','Conserve al menos las necesarias para la pregunta y sus dependencias.'),
 ('Agregación','Suma, Conteo, Conteo distinto, Promedio, Mínimo o Máximo según el significado.'),
 ('Definir cálculo controlado','Permite operaciones sumar, multiplicar, restar o dividir sobre columnas numéricas disponibles.'),
 ('Primer valor / Segundo valor','En resta y división el orden cambia el resultado; no intercambie costo e importe o cantidad y precio.'),
 ('Factores o componentes en orden','Para suma/multiplicación se seleccionan entradas permitidas; el editor limita la cantidad y el servidor comprueba tipos y referencias.'),
 ('KPIs incluidos y medida asociada','La asociación requiere una medida de función semántica compatible y las entradas de la receta.'),
 ('Dimensión que desea corregir / Ruta de relación comprobada','Permite elegir entre vínculos existentes. Las opciones bloqueadas explican riesgo de duplicación, tipos o unicidad.'),
 ('Justificación de esta corrección / Justificación del ajuste','Entre 10 y 500 caracteres. Explique el concepto de negocio y por qué corresponde, no escriba sólo porque funciona.')],
[('Abra Personalizar propuesta y anote qué problema concreto va a corregir.','Ajuste motivado por la necesidad, no por conseguir una luz verde.'),
 ('Revise cada origen y agregación; marque o desmarque dimensiones, medidas e indicadores.','El borrador mantiene las dependencias necesarias.'),
 ('Si corrige un cálculo, seleccione sólo entradas comprobadas y respete el orden.','Fórmula legible y controlada, sin SQL libre.'),
 ('Para una ruta ambigua elija dimensión, vínculo y justificación.','La evidencia muestra tipos, cardinalidad, destino único y riesgo.'),
 ('Pulse Crear versión con relación corregida cuando corresponda y revise la nueva versión antes de otro ajuste.','La corrección queda registrada; una decisión intermedia puede precisar una ruta sin cambiar la entidad final.'),
 ('Para ajustes generales complete Justificación del ajuste y pulse Guardar como nueva versión.','Una versión derivada pasa de nuevo las reglas; la fuente y la versión original no se reescriben.'),
 ('Revise cobertura, rutas y errores del resultado y vuelva a Revisión.','Sólo se aprueba una versión corregida comprobada.')],
['Puede haber propuesto las opciones iniciales; el ajuste general y la elección de relaciones son decisiones del analista sujetas a validadores. No hace falta pedir a la IA SQL para modificar la estructura.'],
['Tablas/columnas y tipos, número de entradas, dependencias de KPI, función semántica, clave destino única y conservación del grano; una relación contradictoria o multiplicadora se bloquea.'],
['La persona elige inclusiones, operaciones y roles comerciales, y justifica por escrito la corrección.'],
'Nueva versión identificable, revalidada y con decisiones acumuladas.',
[('Al retirar una medida desaparece un KPI.','Revise sus dependencias; no es pérdida de datos del origen. Restituya una medida compatible o acepte excluir el KPI.'),
 ('El vínculo es válido pero representa facturación en lugar de comprador.','Use la decisión guiada y justifique el rol; que coincidan las filas no demuestra que el rol comercial sea correcto.'),
 ('La nueva versión está bloqueada.','Lea el motivo; cancele o ajuste el borrador. No cambie reglas ni huellas a mano para forzar la aprobación.')],
{'consigna':'Un documento tiene líneas de 100 y 50 y otro una línea de 90. Calcule promedio por línea y por documento.','respuesta_orientativa':'Importe total 240; tres líneas: 80 por línea; dos documentos distintos: 120 por documento. Son indicadores diferentes.'},
[('¿Editar el texto de granularidad cambia por sí solo las claves?','No. El contrato debe conservar una estructura compatible y superar validación.'),('¿Una relación uno a muchos desde el hecho es segura por existir?','No necesariamente: puede multiplicar líneas e importes. Revise dirección, unicidad y motivo de bloqueo.')])

sec('BI07','Asistente paso 5 aprobar y consultar versiones',['Analista de BI con permiso de revisión'],
'Distinguir validación técnica, aprobación humana, retiro de aprobación y consulta histórica.',
['La aprobación es una decisión sobre una versión concreta. La plataforma vuelve a ejecutar sus reglas y registra responsable, fecha y comentario. No crea tablas ni carga datos al pulsar Aprobar propuesta.',
 'Consultar una versión o Verificar evidencia no debe retirar su aprobación por sí solo. Una diferencia de reconstrucción causada por el motor puede quedar como advertencia de compatibilidad; su efecto sobre nuevas cargas se comprueba por separado.'],
[('Lista para revisión','Contrato que puede recibir decisión humana si conserva las condiciones requeridas.'),
 ('Aprobada','Versión con decisión humana registrada; su aptitud para otra carga también depende de las reglas actuales y la fuente.'),
 ('Retirada','Aprobación retirada expresamente para impedir nuevas ejecuciones; no borra datamarts ya generados.'),
 ('Descartada','Fuera de las listas operativas; se conservan auditoría y trazabilidad.'),
 ('Huella','Resumen de contenido usado para detectar cambios. No se corrige editando el valor para que coincida.')],
[('Comentario de revisión','Hasta 500 caracteres. Para rechazar se exige un motivo suficiente, al menos 10 caracteres en la interfaz.'),
 ('Leí y comprendí las advertencias y las acciones indicadas','Aceptación requerida si hay avisos. Cero errores no significa cero aspectos que revisar.'),
 ('Aprobar propuesta / Rechazar propuesta','Decisión humana distinta de la ejecución física.'),
 ('Verificar evidencia','Comprueba instantánea, referencias, contrato y reproducción sin llamar al modelo, sin consultar filas y sin ETL.'),
 ('Mostrar en Versiones generadas','Filtra el historial; no cambia el estado de las versiones.'),
 ('Abrir resultado','Recupera la versión guardada sin volver a generar con IA.'),
 ('Crear versión corregida desde ésta','Permite derivar una corrección conservando la original.'),
 ('Retirar aprobación / Descartar versión','Acciones explícitas con motivo; no se usan para limpiar un aviso sin entenderlo.'),
 ('Restaurar aprobación','Disponible en los estados y permisos apropiados; exige justificación, advertencias revisadas y revalidación.')],
[('Lea necesidad, fuente, dominio e instantánea en Revisión.','Está decidiendo sobre la versión correcta.'),
 ('Confirme cero errores y comprenda cada advertencia.','Puede explicar qué está comprobado y qué límite conserva.'),
 ('Escriba comentario y apruebe si corresponde; rechace con motivo si no cumple.','Comprobante de estado, responsable y fecha.'),
 ('Abra después el historial y consulte la misma versión.','Se puede recorrer el diseño en modo de lectura sin regenerarlo.'),
 ('Si se necesita corregir, cree una derivada y revise su aprobación aparte.','No cambia silenciosamente la evidencia del caso anterior.')],
['La IA no aprueba. Verificar evidencia es una comprobación determinística, no una nueva opinión del proveedor.'],
['Permisos, estado y reglas de aprobación vigentes; integridad de instantánea y contrato. Los errores bloqueantes no se resuelven marcando el aviso de advertencias.'],
['Una persona autorizada aprueba/rechaza o retira/restaura con un motivo.'],
'Una decisión trazable y versiones que conservan su historia.',
[('No ve una versión en el filtro actual.','Cambie Mostrar al estado correspondiente y compruebe la fuente. No suponga que se eliminó.'),
 ('La propuesta aprobada no aparece habilitada para una nueva carga.','Consulte motivos en Datamart de ventas. Puede ser histórica o incompatible para otra ejecución aunque sus resultados anteriores sigan disponibles.'),
 ('Verificar evidencia muestra compatibilidad.','Lea la explicación y distinga el registro histórico de la aptitud actual. No retire aprobación sin una decisión deliberada.')],
{'consigna':'Explique la diferencia entre aprobar propuesta, preparar materialización y materializar.','respuesta_orientativa':'Aprobar acepta un diseño; preparar fija selección y huellas; materializar lee la fuente y crea/carga el destino.'},
[('¿Una aprobada puede ser consultable pero no apta para otra carga?','Sí. Se conserva historia, pero nuevas ejecuciones deben superar las reglas actuales.'),('¿Abrir resultado vuelve a consumir una generación IA?','No. Recupera una versión persistida.')])

sec('ETL01','Materialización paso 1 elegir una propuesta',['Analista de BI'],
'Escoger un contrato aprobado entendiendo qué puede ejecutarse y qué debe abrirse como histórico.',
['Entre a Datamart de ventas con la fuente que corresponde. El proceso muestra cinco pasos: Elegir propuesta, Revisar indicadores, Confirmar ejecución, Materializar y cargar, y Validar resultados.',
 'La propuesta recomendada es una ayuda para elegir entre candidatas compatibles. No ejecuta nada automáticamente. Si el mismo contrato y selección ya tienen expediente, se debe abrir ese expediente en lugar de repetir la carga.'],
[('Propuesta elegible','Conserva aprobación, metadatos, fuente habilitada y probada, contrato compatible e indicadores calculables.'),
 ('Expediente','Registro de una preparación o ejecución, con selección, huellas, plan, responsable y resultados.'),
 ('Consulta histórica','Lectura de lo ocurrido en una ejecución anterior; no es una prueba nueva ni una recarga.')],
[('Tarjeta de versión','Resumen, necesidad, grano, cantidad de KPI y fecha de aprobación.'),
 ('Seleccionar','Elige el contrato del recorrido actual.'),
 ('Comparar','Permite contrastar hasta dos propuestas por grano, medidas e indicadores.'),
 ('Versiones anteriores no habilitadas para una nueva carga','Explica bloqueos; no significa que se hayan borrado sus datos.'),
 ('Abrir expediente','Recupera una ejecución previa sin repetir el ETL.'),
 ('Revisar indicadores','Avanza con la propuesta seleccionada.')],
[('Compruebe la fuente antes de leer las tarjetas.','No mezcla contratos de otra base.'),
 ('Compare necesidad y grano con su ficha de análisis.','Selecciona un modelo adecuado, no sólo la versión de número mayor.'),
 ('Use Comparar si existen dos alternativas relevantes.','Reconoce diferencias que afectan al significado comercial.'),
 ('Si indica Ya ejecutada, abra el expediente para consultar la evidencia.','No produce otra carga idéntica accidental.'),
 ('Si requiere una carga nueva y la candidata es compatible, pulse Revisar indicadores.','Continúa con la versión aprobada elegida.')],
['Los indicadores fueron sugeridos en el diseño; esta selección no exige otra generación con IA.'],
['Reglas de compilación actuales, aprobación, instantánea existente, fuente activa en lectura, recetas y preparación dimensional. Contratos históricos anteriores pueden quedar excluidos de nuevas ejecuciones.'],
['La persona selecciona la versión y decide si consulta lo previo o necesita una derivada corregida.'],
'Un contrato correcto seleccionado o un expediente histórico abierto de forma consciente.',
[('No hay propuestas habilitadas.','Lea la lista de bloqueos; corrija o genere una propuesta actual. El historial puede seguir disponible.'),
 ('Sólo se ve Abrir expediente.','Es la protección frente a repetición de contrato. Consulte el existente; no trate de borrar la ejecución para forzar otra.')],
{'consigna':'Elija dos propuestas y explique una diferencia de grano o indicador sin ejecutarlas.','respuesta_orientativa':'La comparación tiene sentido si cambia la pregunta o su representación; el número de versión por sí solo no mide calidad.'},
[('¿Recomendada equivale a aprobada automáticamente por la IA?','No. Es una recomendación operativa entre contratos que conservan aprobación y compatibilidad.'),('¿Histórico bloqueado equivale a datos eliminados?','No. Puede consultarse el expediente conservado.')])

sec('ETL02','Materialización paso 2 elegir indicadores y recetas',['Analista de BI'],
'Seleccionar salidas calculables y explicar suma, diferencia, razón y participación.',
['En Revisar indicadores no se redactan fórmulas libres. Se decide cuáles de las recetas admitidas del contrato se necesitan para el objetivo. Debe quedar al menos una.',
 'Desmarcar indicadores puede reducir la cobertura de la necesidad. La preparación registra si la selección es parcial. No presente un ejercicio de dos KPI como si hubiera materializado todos los requisitos de una necesidad avanzada.'],
[('Agregación','Suma, conteo, conteo distinto, promedio, mínimo o máximo de una medida comprobada.'),
 ('Diferencia','Resta entre dos entradas verificadas, por ejemplo importe menos costo comparable.'),
 ('Razón','Numerador dividido entre denominador. El importe por pedido usa importe total ÷ pedidos distintos del mismo alcance.'),
 ('Participación','Razón multiplicada por 100. Siempre se debe explicar el universo del denominador.'),
 ('Promedio ponderado por unidad','Total monetario ÷ total de unidades, distinto de promediar precios de filas sin ponderar.'),
 ('Sin valor','Una razón sin denominador válido no debe representarse como una división infinita ni como una venta cero demostrada.')],
[('Incluir indicador','Conserva o retira una receta de esta ejecución.'),
 ('Cálculo controlado','Describe operación y entradas; compruebe el denominador y la unidad.'),
 ('Unidad','Unidades, documentos, porcentaje o moneda de origen; un código monetario necesita evidencia.'),
 ('Período','Hereda o precisa la periodicidad del contrato.'),
 ('Ajuste de seguridad','Por ejemplo una tasa presentada como dinero o un promedio de línea mal nombrado.'),
 ('Ver trazabilidad técnica','Entradas verificadas, versión de definición y unidad originalmente sugerida.'),
 ('Revisar transformaciones','Avanza con las recetas seleccionadas.')],
[('Lea nombre, descripción y cálculo de cada indicador.','Reconoce qué pregunta responde.'),
 ('Compruebe que el conteo documental sea distinto y que la razón use ese conteo.','No confunde líneas con pedidos o facturas.'),
 ('Seleccione las salidas necesarias y revise las que retira.','Queda al menos una receta y el alcance parcial se reconoce.'),
 ('Lea las correcciones de nombre o unidad.','No denomina neto a precio × cantidad sin descontar una tasa ni promedio por pedido a AVG de línea.'),
 ('Pulse Revisar transformaciones.','Continúa sin cambiar el contrato físico ni ejecutar todavía.')],
['Propuso indicadores anteriormente; el cálculo lo controla el motor de recetas. La IA no calcula a mano el total que se publicará.'],
['Operaciones soportadas y entradas comprobadas. Las diferencias, razones y participaciones requieren dos entradas válidas. La división con divisor cero conserva un resultado nulo/no calculable.'],
['El analista selecciona qué indicadores quiere materializar y acepta conscientemente un alcance parcial cuando corresponda.'],
'Selección de indicadores útil, con fórmula y unidad entendidas.',
[('Un KPI no tiene medida compatible.','Vuelva al asistente para corregir o excluir; este paso no permite inventar la entrada.'),
 ('La razón aparece Sin valor.','Revise denominador y universo. No reemplace el resultado por cero para ocultar una división no definida.'),
 ('Las facturas por producto no suman las facturas globales.','El conteo distinto no es aditivo: una factura puede contener varios productos.')],
{'consigna':'Tres líneas: pedido A 100 y 50; pedido B 90. Calcule total, conteo de líneas, pedidos distintos e importe por pedido.','respuesta_orientativa':'240;3;2;120. Sumar los pedidos distintos de grupos de producto puede contar el mismo pedido varias veces.'},
[('¿Por qué 10% y 40% no se promedian siempre como25%?','Si tienen distintos denominadores, hay que usar totales compatibles o ponderar; el promedio simple puede cambiar el significado.'),('¿Cambiar la etiqueta corrige una receta incorrecta?','No. Debe corresponder fórmula, medida y unidad, no sólo el texto.')])

sec('ETL03','Materialización paso 3 confirmar el plan',['Analista de BI con permiso de ejecución'],
'Leer extracción, limpieza, transformación, carga y validación antes de fijar el expediente.',
['Esta pantalla permite explicar el proceso sin escribir SQL. Revise la tabla de hechos, el grano, las dimensiones y las medidas. Luego lea cada operación de la secuencia.',
 'Las operaciones opcionales marcadas Revisar en el paso 5 preparan candidatos de etiquetas en español. No existe una lista para aprobar etiquetas aquí: esa revisión aparecerá después de la carga si hay candidatos.'],
[('Extracción','Lectura controlada de columnas del origen autorizado.'),
 ('Limpieza y calidad','Tratamiento previsto de claves, nulos, textos o duplicados según el plan; no es una promesa de corregir cualquier dato defectuoso.'),
 ('Transformación','Derivaciones y enriquecimientos permitidos que respetan la granularidad.'),
 ('Clave sustituta','Identificador interno de la dimensión analítica, separado de la clave comercial del origen.'),
 ('Carga dimensional','Creación y carga del hecho y dimensiones del destino de la ejecución.'),
 ('Conciliación','Contraste de cantidades e importes de origen y destino del mismo alcance.')],
[('Tabla de hechos / Granularidad / Dimensiones / Medidas','Resumen del modelo que se va a materializar.'),
 ('Etapas del plan','Extracción, Limpieza y calidad, Transformación y enriquecimiento, Carga dimensional y Conciliación y evidencia.'),
 ('Advertencias heredadas','Avisos de la propuesta que siguen siendo relevantes para la carga.'),
 ('Registro de decisión','Comentario de 10 a 500 caracteres que explica la decisión sobre plan y KPI.'),
 ('Confirmo el plan de ejecución','Acepta el contrato y entiende que las etiquetas candidatas se revisarán después.'),
 ('Preparar materialización','Guarda selección, plan y huellas. No lee ni altera filas de la fuente en esta confirmación.')],
[('Compare el resumen con la propuesta aprobada.','Mismo evento y grano.'),
 ('Lea las operaciones de cada etapa y advertencias.','Puede explicar qué se leerá y qué se calculará.'),
 ('Compruebe que no se confunda una etiqueta en español con un valor original nuevo.','Entiende la política de conservar originales.'),
 ('Escriba una decisión concreta y marque la confirmación.','Registro humano suficiente.'),
 ('Pulse Preparar materialización una sola vez y anote el número de ejecución.','Expediente preparado con propuesta, instantánea, responsable y huellas; aún no hay nueva carga física.')],
['No genera SQL libre en esta confirmación. La interpretación posterior de categorías puede usar IA bajo la política de valores aptos y revisión humana.'],
['Permiso de escritura ETL, aprobación y compatibilidad actuales, recetas seleccionadas, cobertura y duplicidad de contrato/selección.'],
['Una persona autorizada confirma el plan y la selección que quedará registrada.'],
'Un expediente preparado, trazable y aún separado de la ejecución física.',
[('La preparación informa que el contrato ya corresponde a otra ejecución.','Abra ese expediente; el conflicto evita repetir la carga idéntica.'),
 ('El botón sigue deshabilitado.','Revise permiso, casilla de confirmación y longitud del comentario.'),
 ('Faltan etiquetas para aprobar en esta pantalla.','Es normal: primero se materializa, después se revisan los candidatos en Validar resultados.')],
{'consigna':'Explique por qué preparar no significa que ya se pueda mostrar un nuevo tablero.','respuesta_orientativa':'Se guardó el contrato; faltan lectura, carga, conciliación y condiciones de publicación.'},
[('¿Qué se conserva al preparar?','Selección de KPI, comentario, plan, huellas de propuesta e instantánea y responsable.'),('¿Quién ejecuta la lectura?','El materializador controlado después del inicio explícito del paso4.')])

sec('ETL04','Materialización paso 4 cargar sin repetir accidentalmente',['Analista de BI con permiso de ejecución'],
'Iniciar una carga entendiendo sus efectos y recuperar el expediente ante una interrupción.',
['Antes de pulsar Materializar y cargar datamart, compruebe fuente, propuesta y número de expediente. La operación leerá columnas aprobadas de la fuente y creará un destino analítico propio de esa ejecución.',
 'El hecho y las dimensiones se cargan con controles transaccionales. Un fallo bloqueante no debe dejar un datamart parcial publicado ni sustituir los resultados anteriores. No pulse repetidamente el botón porque tarde la respuesta.'],
[('Esquema por ejecución','Espacio analítico identificado para separar resultados de distintas ejecuciones; la base de origen no se sobreescribe.'),
 ('Transacción','Conjunto de operaciones que se confirma completo o se revierte ante un fallo.'),
 ('Preparada / En ejecución / Validada / Revisión pendiente / Fallida','Estados del expediente que se deben leer antes de intentar otra acción.')],
[('Contrato preparado correctamente','Confirma el registro previo; revise huellas y selección.'),
 ('Materializar y cargar datamart','Inicia extracción, transformación, creación y carga según el contrato validado.'),
 ('Ver trazabilidad técnica','Constructor, huellas, responsable y fecha.'),
 ('Expedientes recientes','Permite recuperar la ejecución para ver qué ocurrió, sin iniciar otra.')],
[('Lea el comprobante y confirme que sigue siendo el expediente esperado.','No carga un modelo de otra fuente o versión.'),
 ('Pulse Materializar y cargar datamart una vez y mantenga la pantalla abierta.','Estado de procesamiento; no cambia la fuente a modo escritura.'),
 ('Espere el resultado.','Avanza al paso5 con validación, revisión pendiente o fallo.'),
 ('Si se interrumpe el navegador, recupere sesión y abra el expediente antes de reintentar.','Reconoce si terminó, sigue preparada o falló; no crea cargas duplicadas por incertidumbre.'),
 ('Registre identificadores y estado final.','Evidencia de una ejecución nueva o de una consulta histórica, claramente distinguidas.')],
['El diseño puede proceder de IA, pero la lectura y carga se realizan con el materializador y operaciones permitidas. La IA no recibe autorización para ejecutar instrucciones SQL libres.'],
['Contrato y fuente al ejecutar, trazabilidad, claves, relaciones exactas, tipos y condiciones de carga. El destino conserva el aislamiento por ejecución.'],
['La persona inicia la materialización; si hay fallo investiga y prepara una corrección en lugar de alterar a mano el expediente.'],
'Expediente de carga con métricas o fallo controlado y resultados anteriores conservados.',
[('Error de conexión o sesión vencida.','Vuelva a entrar y revise Expedientes recientes antes de reenviar. El servidor puede haber terminado aunque el navegador perdiera la respuesta.'),
 ('Fallida y mensaje de reversión.','Revise conexión y contrato con el administrador; si cambió la estructura capture metadatos y genere la versión correcta. Conserve el estado fallido hasta resolver la causa y comprobar la nueva ejecución.'),
 ('La etapa dice Materialización ya ejecutada.','Es consulta. Pase a Validar resultados; esa pantalla no vuelve a cargar por recorrer los pasos.')],
{'consigna':'Simule sólo en la bitácora la decisión ante una pantalla que no responde: ¿qué revisa antes de volver a pulsar?','respuesta_orientativa':'Estado del expediente existente, fuente, propuesta y sesión. No ejecutar de nuevo sin conocer si la carga terminó.'},
[('¿Se reemplaza AdventureWorks por el datamart?','No. Se usa como fuente de lectura y el destino analítico queda separado.'),('¿Abrir un paso histórico repite la lectura de origen?','No. Permite consultar evidencia de la ejecución ya realizada.')])

sec('ETL05','Materialización paso 5 revisar conciliación y calidad',['Analista de BI','Gerente comercial para lectura autorizada'],
'Comprobar cantidades y valores y distinguir una conciliación numérica de una interpretación comercial correcta.',
['Una carga no se da por buena sólo por mostrar un mensaje verde. Lea Filas de origen, Filas cargadas, Diferencia, Tablas creadas y las métricas de cada tabla. Compare también indicadores y procedencia.',
 'La conciliación de la ejecución contrasta filas y totales de medidas de origen/destino. Un resultado de diferencia cero demuestra consistencia de ese alcance; no demuestra por sí solo que se eligió el cliente, fecha o territorio comercial correctos.'],
[('Duplicados controlados en dimensión','Repeticiones agrupadas al conformar una dimensión. Muchas facturas del mismo día pueden producir una sola fila de fecha sin eliminar líneas del hecho.'),
 ('Diferencia cero','Coinciden los controles de ese universo. Hay que comprobar además evento, rutas, unidades y criterios comerciales.'),
 ('Indicador conciliado','Valor calculado a partir de entradas y recetas del expediente; un resultado no calculable debe revisarse por separado.'),
 ('Revisión pendiente','Puede significar diferencia de carga o interpretación semántica pendiente. Lea el motivo concreto, no sólo el color.')],
[('Conciliación OLTP–datamart','Comprobante de filas, diferencias y medidas de la ejecución.'),
 ('Calidad por tabla','Filas de origen/carga y duplicados controlados; distinga hecho y dimensión.'),
 ('Indicadores calculados','Valores, unidad y estado. Algunos se muestran abreviados; el valor exacto y los reportes permiten contrastar decimales.'),
 ('Interpretación semántica','Estado y revisión de candidatos de etiquetas; se explica en la siguiente unidad.'),
 ('Comprobar divisa sin repetir el ETL','Acción aparte si falta evidencia del código monetario.')],
[('Revise que origen y destino correspondan al mismo expediente y grano.','No compara el filtro de un tablero con un total global de otro caso.'),
 ('Compare filas y diferencia.','El hecho conserva el número esperado sin rechazo o multiplicación indebida.'),
 ('Revise por tabla las deduplicaciones de dimensiones.','Entiende por qué la fecha puede tener menos filas que documentos sin perder hechos.'),
 ('Compare indicadores, unidades y razones con su fórmula.','No hay denominador cambiado o unidad inventada.'),
 ('Revise rutas de cliente/territorio además de números.','Se conserva el rol comercial solicitado.'),
 ('Si la conciliación y publicación cumplen, abra Analítica de ventas.','Tablero identificado con fuente, propuesta y ejecución correctas.')],
['Puede apoyar etiquetas y explicar después resultados; el contraste numérico no se obtiene por opinión del modelo.'],
['En el materializador actual la conciliación requiere cero filas rechazadas, mismo conteo origen/destino y diferencias de totales de medidas iguales a cero. La condición numérica no reemplaza la revisión semántica del analista.'],
['La persona revisa métricas, procedencia y alcance antes de usar los resultados para una lectura comercial.'],
'Expediente comprendido y evidencia concreta para aceptar o investigar.',
[('Hay diferencia de filas o importes.','No presente el tablero como verificado sin resolverla. Registre magnitud y alcance, revise claves/uniones/entradas y corrija el contrato.'),
 ('Fecha muestra miles de duplicados controlados.','Compruebe si son días repetidos en documentos; en el casoWWI22 se conservaron1.069días desde70.510documentos sin perder228.265líneas.'),
 ('Los totales coinciden pero cambia California entre versiones.','Compare roles de comprador/facturación y ciudad de entrega/postal. Distinta clasificación puede explicar el cambio sin mezcla entre bases.')],
{'consigna':'Conserve100líneas de factura sobre10días. ¿Es obligatorio tener100filas en la dimensión fecha?','respuesta_orientativa':'No. Puede haber10fechas únicas y100filas en el hecho; lo importante es que las claves y los controles expliquen esa conformación.'},
[('¿Diferencia cero prueba que el territorio era históricamente el del cliente?','No. Haría falta una historia de vigencias; el prototipo lee los atributos del estado disponible durante elETL.'),('¿Revisión pendiente siempre significa carga fallida?','No. Puede haber conciliación correcta con etiquetas aún pendientes; lea el detalle.')])

sec('ETL06','Revisar etiquetas en español y comprobar la moneda',['Analista de BI'],
'Publicar sólo interpretaciones revisadas y conservar el significado original y la divisa demostrable.',
['La interpretación semántica añade etiquetas españolas a categorías aptas; conserva los valores originales. No traduce identificadores, nombres de personas, direcciones, texto libre ni categorías de alta cardinalidad.',
 'La moneda es un control diferente. Un importe conciliado no autoriza a escribirUSD. Si la fuente no demuestra un código único adecuado, el resultado correcto es moneda de origen. No confunda el país del cliente con la divisa del importe.'],
[('Mapeo','Correspondencia entre categoría original y etiqueta española revisada.'),
 ('Publicación supervisada','Las etiquetas sólo se publican después de la revisión individual y la confirmación humana.'),
 ('Divisa comprobada','Código respaldado por evidencia relacional de fuente/base; no elegido por el modelo por intuición.')],
[('Publicar','Casilla por mapeo para conservarlo o excluirlo.'),
 ('Etiqueta en español','Texto editable, hasta100caracteres, que debe preservar el significado.'),
 ('Comentario de revisión','Entre10y500caracteres sobre la decisión tomada.'),
 ('Confirmo que revisé los mapeos que se publicarán','Confirmación distinta de la aprobación del diseño y de la preparación delETL.'),
 ('Publicar etiquetas revisadas','Publica sólo los mapeos aceptados como columnas adicionales auditables.'),
 ('Reintentar interpretación sin repetir el ETL','Recupera una interpretación pendiente sin recargar el hecho.'),
 ('Comprobar divisa sin repetir el ETL','Consulta evidencia de moneda y actualiza su contexto sin otra materialización.')],
[('Lea el estado de Interpretación semántica.','Reconoce si no hay candidatos, están pendientes, requieren revisión o ya fueron publicados.'),
 ('Compare cada original con la etiqueta, corrija lo necesario y excluya códigos que no convenga traducir.','No cambia el valor original ni acepta una etiqueta por rutina.'),
 ('Escriba comentario, marque confirmación y publique.','Recibo con responsable,fecha y mapeos revisados.'),
 ('Si está pendiente por proveedor, revise la configuración y use el reintento semántico.','No se repite elETL para corregir sólo etiquetas.'),
 ('Revise la divisa y compruébela si la acción está disponible.','Código verificado o moneda de origen con el límite conservado.')],
['Propone etiquetas para categorías seguras dentro de la política implementada. No debería convertir códigos, nombres propios o información ausente en traducciones inventadas.'],
['Aptitud de categorías, formato de mapeos, conservación del original y publicación autorizada. La comprobación de moneda usa evidencia de la fuente, no una respuesta libre delLLM.'],
['El analista publica, corrige o excluye cada etiqueta y confirma la revisión. No elige una divisa sin evidencia para mejorar la apariencia.'],
'Etiquetas comprensibles con original conservado y unidad monetaria honesta.',
[('No aparece ninguna etiqueta para aprobar.','Si no hay candidatos aptos no existe una tarea de publicación. No hay que fabricar un mapeo.'),
 ('El proveedor falla después de una carga conciliada.','Reintente sólo interpretación; antes compruebe el expediente para conservar la carga existente.'),
 ('WWI no demuestraUSD.','Conserve moneda de origen. Cambiar el rótulo manualmente no convierte el dato en dólares.')],
{'consigna':'En el casoAW21se propusieronEurope,NorthAmerica,Pacific y códigosAU,CA,DE,FR,GB,US. Explique la revisión documentada.','respuesta_orientativa':'Se publicaronEuropa,AméricadelNorteyPacífico; los seis códigos se excluyeron de traducción. Se conservaron originales.'},
[('¿Publicar etiquetas altera los importes?','No. Añade interpretación categórica auditada; no cambia las medidas originales.'),('¿Siempre debe resolverse un código monetario?','No. La ausencia de evidencia suficiente debe conservarse como límite.')])

sec('AN01','Elegir el datamart y filtrar el análisis',['Analista de BI','Gerente comercial'],
'Leer los identificadores y usar filtros sin confundir vistas, bases ni universos.',
['Analítica de ventas consulta los datos físicos de una ejecución conciliada, no vuelve a extraer cada vez la base transaccional. Compruebe la fuente y los identificadores del encabezado antes de interpretar cifras.',
 'Vista ejecutiva resume la información para gerencia. Vista analítica añade controles y tablas de respaldo. Cambiar de vista no otorga un rol nuevo ni añade datos que no se hayan materializado.'],
[('Datamart analizado','Ejecución concreta cuyos datos físicos se consultan; puede haber varios expedientes de la misma fuente.'),
 ('Filtro','Delimita las filas que participan en el cálculo. Año y territorio se combinan en el mismo alcance.'),
 ('Indicador de los gráficos','Métrica que explica las visualizaciones. No confundirla con todos losKPI del encabezado.'),
 ('Última actualización','Fecha de finalización del expediente o de su creación si no existe otra; no equivale a una recarga automática al abrir elpanel.')],
[('Fuente en contexto','Selecciona la base de trabajo. Cambiarla limpia ejecución,filtros y conversación y vuelve a pedir resultados de esa fuente.'),
 ('Datamart analizado','Combobox cuando hay más de una ejecución con datos físicos consultables. Si sólo hay una se muestra Datamart activo.'),
 ('Vista ejecutiva / Vista analítica','Presentación según necesidad de lectura. En la ejecutiva se omite el visual de clientes; en la analítica se muestran controles/datos adicionales.'),
 ('Indicador de los gráficos','En vista analítica lista agregaciones que admiten visualización segura. Las recetas derivadas pueden existir comoKPI sin aparecer en ese selector.'),
 ('Año / Territorio','Opciones obtenidas del datamart disponible; no inventan años futuros.'),
 ('Restablecer filtros','Retira año y territorio; no cambia la fuente ni ejecuta otroETL.'),
 ('Consultar respaldo / Ver expediente técnico','Abre la evidencia de la ejecución que respalda elpanel.')],
[('Compruebe fuente,base,propuesta,ejecución,moneda yperíodo en el encabezado.','Contexto correcto antes de leer tarjetas.'),
 ('Seleccione el datamart deseado si hay varios.','Se reinician métrica y filtros para evitar arrastrar otro contexto.'),
 ('Abra Vista analítica y elija el indicador de los gráficos.','Las gráficas representan la métrica elegida.'),
 ('Seleccione año y territorio y espere Actualizando resultados.','KPI,gráficos y hallazgos se recalculan para ese alcance.'),
 ('Compare un valor exacto de tabla con una tarjeta abreviada.','Comprende la diferencia de formato sin declarar un error de cálculo.'),
 ('Use Restablecer filtros y vuelva a seleccionar la otra fuente cuando termine.','No quedan mezclados filtros ni conversación del casoanterior.')],
['No hace falta una generaciónLLM para consultar o filtrar elpanel. Los valores se calculan mediante recetas y consultas controladas.'],
['Correspondencia de fuente y ejecución,disponibilidad física,recetas y filtros permitidos; el servidor comprueba procedencia además de los controles delnavegador.'],
['La persona elige el universo e interpreta los resultados dentro del evento materializado.'],
'Un panel cuyo contexto y alcance puedan explicarse antes de emitir una conclusión.',
[('Primero complete el expediente del datamart.','No hay ejecución conciliada con datos físicos disponibles. Vuelva a Datamart de ventas y revise preparación,carga y validación.'),
 ('Falta el combobox de datamart.','Puede ser correcto si sólo una ejecución tiene datos físicos; no se debe crear otra para obtener elselector.'),
 ('Aparece un resultado anterior mientras carga el filtro.','Espere a que termine y confirme el contexto del encabezado antes de copiar cifras. Si persiste una fuente equivocada,registre incidencia.'),
 ('El chat se vació tras cambiar año o fuente.','Es protección de contexto: la respuesta anterior no se reutiliza como si perteneciera a la nuevaselección.')],
{'consigna':'Explique por qué los109,8millones globales deAW21no se comparan directamente con6.015.174,74del filtro2013/Northwest.','respuesta_orientativa':'Son universos diferentes. La comparación necesita la misma ejecución y filtros.'},
[('¿Cambiar Año vuelve a cargar el origen?','No. Recalcula sobre eldatamart.'),('¿Todas las recetas pueden graficarse por entidad?','No. El selector ofrece las agregaciones que admiten visualización agrupada segura en la implementación.')])

sec('AN02','Leer gráficos y hallazgos con criterio comercial',['Analista de BI','Gerente comercial'],
'Diferenciar tendencia,ranking y distribución y explicar sus denominadores y límites.',
['Una línea temporal compara períodos; las barras ordenan entidades; una distribución muestra participaciones. Antes de decir que un producto es elmejor,precise si lo ordenó por importe o unidades y qué filtros utilizó.',
 'Los hallazgos delpanel se construyen con reglas sobre los resultados visibles. Aunque la pantalla los llame Copiloto analítico,no todos sus textos proceden de una nueva llamadaLLM. La conversación inferior sí utiliza el proveedordeIA.'],
[('Top o ranking','Lista limitada de entidades ordenadas por un indicador. El máximo de una línea no equivale a la mayor suma porproducto.'),
 ('Participación visible','Porcentaje respecto del total definido para esa visualización. En elpanel los rankings limitados pueden usar la suma de lo mostrado; en consultas agregadas delcopiloto se informa eluniverso filtrado completo.'),
 ('Asociación','Patrón observado en datos. No prueba por sí solo causalidad,preferencia delcliente,demanda de mercado o eficacia de una campaña.'),
 ('Detalle seleccionado','Valor y contexto de un punto,barra ocategoría. Seleccionarlo no cambia filtros sin una acción adicional.')],
[('Punto,barra o categoría','Clic o teclado permiten ver valor exacto y participación deldatoseleccionado.'),
 ('Filtrar tablero por territorio','Botón explícito en el detalleterritorial. Abrir el detalle no aplica el filtro automáticamente.'),
 ('Cerrar detalle','Cierra la selección puntual sin modificar eluniverso.'),
 ('Tabla de respaldo en vista analítica','Permite contrastar cifras de lagráfica.'),
 ('Cómo se generaron','Explica la procedencia y reglas de los hallazgos.')],
[('Lea título,subtítulo,indicador,unidad y filtros de lagráfica.','Identifica eluniverso que está comparando.'),
 ('Seleccione el dato que desee revisar.','Detallecon valor exacto sin cambio inesperado delpanel.'),
 ('Compare con la tabla de respaldo.','La cifra representada tiene soporte verificable.'),
 ('Si desea restringir por territorio,pulse el botón de filtro explícito.','Se recalcula elpanelpara esealcance.'),
 ('Lea hallazgo,evidencia y Cómo se generaron.','Distingue una descripción numérica de una conclusión sobre causas.'),
 ('Redacte una lectura y una comprobación comercial adicional.','Por ejemplo revisar composición de productos antes de atribuir una caída a un proveedor.')],
['Los hallazgos automáticos delpanel son determinísticos. La IA conversacional puede explicar laevidencia después,pero su prosa requiere revisión.'],
['Cálculo de agregados y visualizaciones sobre eldatamart identificado. La gráfica no certifica hipótesis comerciales ajenas a los registros.'],
['La persona decide qué dato merece atención y qué comprobaciones adicionales necesita antes deactuar.'],
'Lectura comercial con cifra,unidad,período y límite explícitos.',
[('ElTop8no suma eltotalglobal.','Es un subconjunto;revise su denominador. No ajuste la gráfica para que aparente cubrir todo.'),
 ('Pedidos distintos por producto superan los pedidos globales al sumarlos.','Un pedido puede contener varios productos; elconteo distinto no es aditivo entre grupos.'),
 ('La IA dice que un producto domina elmercado.','Elranking interno no demuestra cuota de mercado. Reformule como posición dentro deluniverso consultado.')],
{'consigna':'Un producto lidera por importe y otro porunidades. Escriba dos conclusiones válidas.','respuesta_orientativa':'Liderazgo por importe y liderazgo por unidades son distintos; ninguno demuestra automáticamente mayor margen o preferenciadelmercado.'},
[('¿Un gráfico por provincia demuestra dónde ocurrió físicamente laentrega?','No,salvo evidencia específica. EnWWIelcaso usa provincia de la ciudad de entrega registrada en laficha.'),('¿Abrir una barra filtra todo eltablero?','No.Elfiltro territorial exige su botón explícito.')])

sec('AN03','Conversar con elcopiloto y revisar su respuesta',['Analista de BI','Gerente comercial'],
'Formular preguntas respondibles y contrastar consulta interpretada,evidencia y conclusión.',
['Elcopiloto recibe contexto agregado y procedencia deldatamart. Interpreta indicador,dimensión,filtros yTopN,y la plataforma puede ejecutar una consulta agregada permitida antes de pedir una explicación.',
 'Una pregunta puede solicitar otroaño o territorio disponible aunque no esté seleccionado enpantalla. Por eso revise Consulta interpretada: larespuesta puede corresponder a otroalcance solicitado y no al filtro actualmente visible.',
 'Las reglas acotan formato,consultas y cautelas; no existe un validador universal de verdad para cada frase delmodelo. Laalumna debe verificar cifras,denominadores y límites antes de usar larespuesta.'],
[('Consulta interpretada','Indicador,agrupación,filtros,límite y orden que la plataforma entendió de lapregunta.'),
 ('Agregado permitido','Cálculo cerrado sobre dimensiones materializadas de producto,cliente oterritorio,con recetas aprobadas; noSQLlibre.'),
 ('Evidencia','Valores y alcance que respaldan laexplicación; debe poder contrastarse con elpanelo tablas.'),
 ('Pregunta de seguimiento','Sugerencia ejecutable construida desde capacidades verificadas; no debe asumirse que abre un nuevo módulo de análisis.')],
[('Escriba su pregunta','Entre5y500caracteres. Indique indicador,comparación,período,territorio yqué quiere comprender.'),
 ('Guía de preguntas sugeridas','Ejemplos adaptados alcontexto; pueden usarse como punto departida.'),
 ('Preguntar al copiloto','Solicita interpretación/explicación. No crea unapropuesta ni ejecuta otroETL.'),
 ('Consulta interpretada','Revisealcance ydenominador antes de leer la narración.'),
 ('Evidencia y cautela','Permiten reconocer lo calculado y lo que no se ha demostrado.'),
 ('Proveedor ymodelo','Identifican quién generó larespuesta; cambiar deproveedor no debe cambiar lasreglas deldatamart.')],
[('Confirme ejecución,indicador yfiltros antes depreguntar.','Tiene un contexto inicial claro.'),
 ('Escriba una pregunta concreta,por ejemplo Top5deproductosporunidades con losfiltrosactuales.','Solicitud respondible con capacidades presentes.'),
 ('Espere larespuesta sin enviar variasveces.','Elcopiloto muestra interpretación y evidencia si la operacióncumple.'),
 ('LeaConsulta interpretada y compare indicador,año,territorio,límite ydenominador.','Reconoce cuándo la pregunta pidió unalcance distinto delpanel.'),
 ('Contraste almenos una cifra con tabla oconsulta agregada y revise loslímites comerciales.','Noacepta una redacción coherente si contradice datos.'),
 ('Pregunte de nuevo para aclarar un denominador o límite, sin atribuir causas que no se han comprobado.','Conversación útil y controlada.')],
['Interpreta la intención y redacta respuesta con evidenciaagregada. Hay dos generaciones diferenciadas:intención estructurada yexplicación. La plataforma aporta seguimiento ycautelas.' ],
['Permisos,fuente/ejecución,indicadores ydimensiones disponibles,filtros,cantidadesTopNentre1y20,consultas agregadas eidentificadores permitidos; no aceptaSQLlibre delmodelo.'],
['La personaformula,revisa y decide si la explicación permite una conclusión. Una recomendación es una comprobación por realizar,no unhecho demostrado.'],
'Respuesta contrastada con significado comercial yalcance reconocibles.',
[('Elproveedor no responde o devuelve formato inválido.','Revise configuración,cuota/tiempo ycredencial con eladministrador. Un fallo dechat no requiere recargar eldatamart.'),
 ('Larespuesta usa el añoactual para un conjuntohistórico.','Recuerde que elreloj delservidor no añade registros futuros; no acepte fechas ajenas a ladisponibilidad.'),
 ('Se pide un pronóstico del próximoperíodo.','Es fuera delalcance. Elresultado correcto es explicar ellímite; no inventar unvalor o año.'),
 ('Larespuesta llama facturación a lospedidosdeAW.','Corrija la interpretación:no se demuestra factura emitida a partir delpedido.'),
 ('Larespuesta es fluida pero cambia lacifra.','No la use como evidencia. Registre pregunta,contexto ydiscrepancia,reintente aclaración ycontraste con cálculos determinísticos.')],
{'consigna':'EnAW21filtre2013/Northwest,indicadorunidades,y pregunte: Resume las unidades vendidas en2013paraNorthwest. Indica eltotal yelmes conmayorcantidad,sinatribuircausasnimezclarimportes.','respuesta_orientativa':'Elcontrol histórico del6noviembre registró17.452unidades yjunio2013con2.494. Una sesión nueva debe contrastarsus propiosresultados; no copiar esa cifra si elalcance o la fuente cambiaron.'},
[('¿Se ejecutaSQLredactado porelLLM?','No. Laintención se limita a consultas agregadas permitidas delservidor.'),('¿Elcopiloto sólo puede responder elfiltro visible?','Puedeinterpretar otrofiltro disponible solicitado. Debe leer laconsulta interpretadayno asumir quelosdosalcancescoinciden.'),('¿Una respuesta correcta una vez garantiza que elproveedor nunca fallará?','No. Se deben revisar cadarespuesta y sus controles.')])

sec('AN04','Exportar y comprobar antes de compartir',['Analista de BI','Gerente comercial conpermiso deexportación'],
'Obtener informes que conserven universo yprocedencia yrevisarlos contra elpanel.',
['ExportarPDF produce un informe para lectura. ExportarExcel produce tablas ygráficos de respaldo de las visualizaciones visibles. Ninguno es un respaldo de contenedores,volúmenes o todas lasfilas de la fuente.',
 'La exportación se genera desde eldashboard autorizado. No es una exportación automática de laconversación delchat; si desea citar una respuesta debe registrar la pregunta ysucontexto como evidencia aparte.'],
[('Contexto exportado','Fuente,propuesta,ejecución,vista,métrica,filtros yunidad que permiten interpretar elarchivo.'),
 ('Trazabilidad','Información para reconocer qué expediente yselección respaldan lascifras.'),
 ('Redondeo','Presentación con decimales oabreviaturas; no autoriza a cambiarvalores para hacerlos coincidir visualmente.')],
[('ExportarPDF','Descarga elinforme de la vistayselecciónactuales.'),
 ('ExportarExcel','Descarga ellibro con datosque respaldan losgráficos exportados.'),
 ('Vista ejecutiva/Vista analítica','Afecta qué visualizaciones se comparten;revise la vistajunto alosfiltros.'),
 ('CarpetaDescargas','Abra elarchivo recibido yrevíselo, no basta con pulsar elbotón.')],
[('Fije fuente,ejecución,vista,indicador,año yterritorio.','Alcance exacto que se quierecompartir.'),
 ('ExportePDFyespere la descarga.','Archivo con nombre deejecución yvista.'),
 ('ExporteExcel.','Libro derevisión, no volcadocompleto delorigen.'),
 ('Abra ambos archivos ycompare untotal,unaentidady elfiltro con elpanel.','Cifras ycontexto congruentes.'),
 ('Revise unidad,advertencias,denominadores yprocedencia.','Elinforme no pierde ellímite demostrado enpantalla.'),
 ('Registre fecha,nombre ycontexto delarchivo revisado.','Evidencia de revisión real, no sólo descarga.')],
['No se necesita otra llamada alLLM para generar elinforme deldashboard. Elchat no convierte elreporte en una conclusión validada porunmodelo.'],
['Permiso deexportación además de lectura deanalítica;servidor reconstruye elmismo dashboard con filtrosautorizados yregistra laacción.'],
['Lapersona elige selección,vista yformato ycomprueba elarchivo antes decompartirlo.'],
'Dos archivos revisados cuyoalcance puede explicarse sin abrir otrabase.',
[('No haybotones deexportación.','Revise que elrol tenga permisos de lectura delpanel yexportación. No se corrige cambiando de vista.'),
 ('ElPDFtiene menos gráficos que laVistaanalítica.','Compruebe quévista exportó;laejecutiva omite elvisual declientes.'),
 ('Elporcentaje deExcel no coincide.','Compruebe si es escala0a100o fracción yquédenominador se usó;no multiplique otra vez por100porcostumbre.'),
 ('Elarchivo muestra moneda deorigen aunque AWesté enUSD.','Laevidencia históricaAW21conservó unaetiqueta genérica en unarazón delPDF,pese alvalorcorrecto. No presente ese antecedente como perfecciónsemántica; revise elarchivo nuevo.')],
{'consigna':'Explique por qué no es suficiente mostrar que se descargó uninforme para probar que es correcto.','respuesta_orientativa':'Debe abrirseycompararcifras,contexto,filtros,unidades ytrazabilidad con laselección autorizada.'},
[('¿Excelincluye todas lasfilas delOLTP?','No.Incluye respaldo de lasvisualizaciones exportadas.'),('¿Se exigen siempre seis páginas yseis hojas?','No.Esas cantidades pertenecen a loscasoshistóricos concretos;varían con lavista ylasvisualizaciones.')])

# Prácticas: textos exactos de los casos conservados, más rutas básicas nuevas.
aw_goal=historic['caso_aw']['notas_de_aprendizaje'][0].removeprefix('Objetivo exacto para copiar: ')
wwi_goal=historic['caso_wwi']['notas_de_aprendizaje'][0].removeprefix('Objetivo exacto para copiar: ')
practices=[
 {'codigo':'P-AW-B','titulo':'Ruta básica AdventureWorks unidades por mes y producto','nivel':'Inicio',
  'fuente':'AdventureWorks2022','estado':'Ejercicio nuevo propuesto para las alumnas; no ejecutado en esta revisión documental.',
  'necesidad_para_copiar':'Conservar cada línea de pedido de venta para comparar mensualmente la suma de unidades por producto. Usar la fecha del pedido y un nombre de producto comprobable. Mantener la referencia de cada línea a su pedido. Limitar esta práctica al total de unidades y su evolución; no interpretar estos registros como facturas, cobros o pronósticos.',
  'preguntas':'Evolución de ventas en el tiempo y desempeño por producto, según las etiquetas disponibles del catálogo de esa fuente.',
  'periodicidad':'Mensual','grano':'Línea de pedido','indicadores':'Suma de unidades; las salidas adicionales se revisan y excluyen si no son necesarias.',
  'criterios_de_exito':['Objetivo conservado sin ampliar el evento.','Grano de línea y fecha del pedido verificados.','Producto descriptivo y ruta sin multiplicación.','Conciliación del universo nuevo.','Panel por unidades y mes; no se exige que la IA produzca una cantidad fija de tarjetas.'],
  'referencia_numerica':'No se asigna un resultado predeterminado a una ejecución no realizada. Si la copia y alcance equivalen al caso histórico,el total global de referencia es274.914unidades; debe conciliarse el caso propio.'},
 {'codigo':'P-AW-A','titulo':'Ruta avanzada AdventureWorks documentos distintos y razón por pedido','nivel':'Intermedio',
  'fuente':'AdventureWorks2022','estado':'Caso histórico comprobado el6de noviembrede2026:propuesta129,ejecución21. Repetición por lasalumnas pendiente.',
  'necesidad_para_copiar':aw_goal,'preguntas':'Tiempo,producto,cliente yterritorio. Revise el catálogo propio antes de seleccionarlas.','periodicidad':'Mensual','grano':'Línea de pedido',
  'indicadores':'Importe registrado total;unidades totales;pedidos distintos;importe total/pedidos distintos.',
  'rutas_a_comprobar':['Fecha yterritorio comercial delpedido,con territorio procedente deSales.SalesTerritory.','Producto ycliente con nombre verificable;clave de línea ypedido conservadas.'],
  'pasos_especificos':['Use el objetivoexacto y pasepor loscinco pasos delasistente.','Revise que lacuenta deldocumento useconteodistinto yque larazón lo use comodenominador.','Noagregue costoso margenpara igualar unnúmero detarjetas.','Apruebe únicamente cerrores yavisos comprendidos;complete loscinco pasos dematerialización.','Consulte primero global,luego2013/Northwest.','EnVistaanalítica elija unidades;lea tabla mensual;pregunte alchatpor total ymeslíder.','Exporte y abraPDFyExcelcon ese mismoalcance.'],
  'historico':{'fecha':'2026-11-06','propuesta':129,'ejecucion':21,'filas_origen':121317,'filas_destino':121317,'diferencia_filas':0,'tablas':5,
   'global':{'importe_exacto':'109846381.399888','moneda':'USD comprobado','unidades':274914,'pedidos_distintos':31465,'importe_por_pedido_exacto':'3491.065672966407'},
   'filtro':{'anio':2013,'territorio':'Northwest','importe_exacto':'6015174.735836','unidades':17452,'pedidos_distintos':2053,'importe_por_pedido_exacto':'2929.943855740867','mes_mayor_unidades':'junio de2013','unidades_mes_lider':2494},
   'interpretacion':'Europe,North America yPacific publicadas comoEuropa,América delNorte yPacífico;AU,CA,DE,FR,GB,US excluidos detraducción.',
   'exportacion':'PDFde6páginas yExcelde6hojas delaVistaanalítica porunidades2013/Northwest;observación histórica deetiqueta genérica derazón monetaria conservada.'},
  'pregunta_chat_para_copiar':'Resume las unidades vendidas en 2013 para Northwest. Indica el total y el mes con mayor cantidad, sin atribuir causas ni mezclar importes.',
  'criterios_de_exito':['Mismo evento,grano yrolesdelcaso.','Conciliación sin diferencia.','Cuatro indicadores revisados;no promedio delínea rotulado como promedio porpedido.','Unidad demostrada ylímites depedido conservados.','Valores delpanel,chat yarchivoscontrastados con la selección.']},
 {'codigo':'P-WWI-B','titulo':'Ruta básica WideWorldImporters facturas y unidades por mes','nivel':'Inicio',
  'fuente':'WideWorldImporters','estado':'Ejercicio nuevo propuesto para lasalumnas; no ejecutado en esta revisión documental.',
  'necesidad_para_copiar':'Conservar cada línea de factura para comparar mensualmente la suma de unidades facturadas por producto. Usar la fecha de emisión y el producto con nombre verificable. Mantener el identificador de factura y el de línea para conservar la trazabilidad. Limitar la práctica a unidades y evolución; no afirmar moneda, cobro, utilidad ni entrega realizada.',
  'preguntas':'Tiempo yproducto segúnelcatálogo propio.','periodicidad':'Mensual','grano':'Línea de factura','indicadores':'Suma deunidades;otras salidas se revisan antes dematerializar.',
  'criterios_de_exito':['La propuesta usafacturación yfecha deemisión,no pedidos comosustituto.','Producto descriptivo ylínea identificable.','Nose añade monedani utilidad porintuición.','Cargaconciliada ypanelen unidades.'],
  'referencia_numerica':'No se inventa un resultado para esta ejecución nueva. El caso histórico completoWWI22conservó8.950.628unidades; sólo sirve de contraste si copia yalcance son equivalentes.'},
 {'codigo':'P-WWI-A','titulo':'Ruta avanzada WideWorldImporters roles de cliente y territorio','nivel':'Intermedio/avanzado',
  'fuente':'WideWorldImporters','estado':'Caso histórico comprobado el6denoviembrede2026:propuesta131,ejecución22;doscorrecciones guiadas sucesivas. Repeticiónporlasalumnas pendiente.',
  'necesidad_para_copiar':wwi_goal,'preguntas':'Tiempo,producto,cliente yterritorio enelcatálogoWWI.','periodicidad':'Mensual','grano':'Línea de factura',
  'indicadores':'Importe registrado;unidades;facturas distintas;importe total/facturas distintas.',
  'rutas_a_comprobar':['Sales.InvoiceLines→Sales.Invoices porla relación defactura.','Cliente comprador:Invoices.CustomerID→Customers,noBillToCustomerIDparaesta necesidad.','Territorio:Customers.DeliveryCityID→Cities.StateProvinceID→StateProvinces,noPostalCityIDparaesta necesidad.','La provincia es el destino dimensional;una elección intermedia puede precisar la ruta sin reemplazarla porciudad.'],
  'pasos_especificos':['Use elobjetivo exactoyrevise viabilidad.','Compruebe grano defactura,fechadeemisión,medidas ycuatro indicadores.','Si la generación usa otrorol,abraPersonalización yResolver una relación con evidencia.','ElijaCliente yInvoices.CustomerID→Customers;justifique que se analizaalcomprador;creeunaversiónconrelacióncorregida.','Reviseelnuevoresultado;elijaTerritorio yCustomers.DeliveryCityID→Cities;justifiqueubicación registrada deentrega;creeotraversión.','ConfirmequeseconservaCustomerIDyla provincia final deStateProvinces. Noacepteunavía postal odefacturación sólo porque mantienefilas.','Apruebe ymaterialice si cumple;revise conciliación ydivisa.','Enanalítica elija2015/California,contrastecuatro indicadores;pregunte alchat sobrealcance,denominador ylímites;exporte yabraarchivos.'],
  'historico':{'fecha':'2026-11-06','propuesta':131,'ejecucion':22,'filas_origen':228265,'filas_destino':228265,'diferencia_filas':0,'tablas':5,
   'global':{'importe_exacto':'198043439.45','moneda':'moneda deorigen;sin código únicodemostrado','unidades':8950628,'facturas_distintas':70510,'importe_por_factura_exacto':'2808.7283995177986'},
   'filtro':{'anio':2015,'territorio':'California','lineas':3771,'importe_exacto':'3191769.11','unidades':142247,'facturas_distintas':1179,'importe_por_factura_exacto':'2707.1832994062765'},
   'fecha_dimension':{'fechas_unicas':1069,'documentos_origen':70510,'duplicados_controlados':69441},
   'exportacion':'PDFde6páginas yExcelde6hojas/4gráficos delavistafiltrada;es unejemplohistórico,no formatofijo.'},
  'pregunta_chat_para_copiar':'Resume el importe, las unidades y las facturas distintas en 2015 para California. Explica el denominador del importe por factura y qué significa la provincia usada, sin asumir moneda ni entrega realizada.',
  'criterios_de_exito':['Evento defacturaciónconfecha deemisión.','Rutas exactas decomprador yciudad deentrega registradas.','Facturas distintas,no conteo delíneas.','La moneda no seconvierteenUSDsin evidencia.','No seatribuyen ubicaciónhistórica,entregaefectiva o composiciónfiscal no demostradas.','Nose reutilizaelfiltro delexpedientelegado19como oráculodel22.']}
]

sec('PR01','Practicar con las dos fuentes sin memorizar una respuesta del modelo',['Analista de BI','Gerente comercial'],
'Repetir un recorrido básico y uno avanzado en cada fuente con criterios de aceptación observables.',
['Las cuatro fichas siguientes permiten aprender desde un alcance sencillo hasta documentos distintos,razones yroles de relación. Las básicas son ejercicios propuestos. Las avanzadas conservan objetivos y resultados de la campaña comprobada del6denoviembrede2026.',
 'No se ejecutaron nuevas propuestas niETLen esta revisión de redacción. Una instalación limpia puede no tener los números129/21y131/22. Anote los identificadores que genere supropio entorno. Un proveedor puede variar su primera respuesta,por loque el éxito se evalúa con criterios delmodelo y conciliación,no porobtener tarjetas idénticas.',
 'Si desea demostrar con un caso ya conservado,anuncie que consulta un expediente histórico. Si genera desde cero,diga que está realizando una ejecución nueva yregistre los resultados que realmenteobtenga.'],
[('Referencia histórica','Dato documentado de una campaña anterior,útilpara comparar si copia yalcance coinciden.'),('Práctica nueva','Actividad que debe ejecutarse yregistrarse;no se presenta como realizada por este manual.')],
[('Ficha de práctica','Necesidad copiable,preguntas,periodicidad,grano,indicadores ycriteriosdeéxito.'),('Bitácora de la alumna','Registre fecha,fuente,instantánea,proveedor/modelo,propuesta,ejecución,acciones yresultadospropios.')],
[('Comience por la ruta básica dela primerafuente.','Aprende el recorrido con pocasmedidas.'),('Repita la ruta básica dela segundafuente.','Comprueba qué se mantiene yqué cambió de evento yclaves.'),('Use el caso avanzadoAWpara conteo distinto yrazones.','Puedeexplicar diferencia entre línea ypedido.'),('Use el caso avanzadoWWIpararolesderelación.','Puede justificar comprador yciudad deentrega yconservar suprocedencia.'),('Compare las doslecturas sin sumar monedasni eventos diferentes.','Comprende la arquitectura común ylos significados propios de cadafuente.')],
['La IA puede ofrecer diseños distintos en cada intento. Aprenderá a revisar cada resultado, justificar las decisiones y corregir lo necesario.'],
['Cadapráctica vuelve a pasar autorizaciones,viabilidad,contrato,aprobación,preparación,carga yconciliación que correspondan.'],
['Laalumna ejecuta yregistra;elanalista supervisa;lagerencia explica utilidad ylímitesde lalectura.'],
'Cuatro fichas de trabajo con resultados propios yreferencias históricas separadas.',
[('Los identificadoresdifieren delmanual.','Esnormal en otra instalación. Compruebe fuente,objetivo yevento;no cambie números a mano.'),('ElLLM no entrega lacantidad deKPIesperada.','Revise entradas yrecetas;personalice oexcluya extras yvalide otra versión. Noexistaun número universaldeindicadores.')],
{'consigna':'Registre laevidencia de una práctica yclasifique qué es generaciónnueva yqué es consulta histórica.','respuesta_orientativa':'Laevidenciadebe permitir reconocer fecha,fuente,propuesta yexpediente,con resultado real yno sólo unacaptura antigua.'},
[('¿Se deben forzar las cifras delmanual?','No.Son referencias de una copiaconyalcance concretos;su ejecución debe conciliar datosreales.'),('¿Launiversaldad obliga a usar la mismarelación enambasbases?','No.Elproceso es común;las relaciones ysignificados dependen demetadatos ydecisiones verificadas.')],practicas=practices)

sec('BI08','Costos descuentos y márgenes una ampliación que exige evidencia',['Analista de BI','Gerente comercial'],
'Reconocer cuándo se puede ampliar el análisis financiero y cuándo debe limitarse.',
['Loscasosfinales anteriores se centraron enimporte,unidades,documentos yrazones. No acreditan automáticamenteunmargen histórico. Si se necesita rentabilidad,primero se deben comprobar costos compatibles con la venta ysu fecha.',
 'Uncostounitarioactualdelcatálogo puede servir de referencia,pero no se convierte por su nombre enelcosto real histórico decada línea vendida. Comparar ese costo conunimporte de otroalcance puede producir un cálculo numérico correcto yuna interpretación comercial incorrecta.'],
[('Descuento monetario','Importe derivado de una base yuna tasa;la tasa por sí sola no esdinero.'),('Venta bruta','Precio por cantidad antes deldescuento cuandoesa es lareceta comprobada.'),('Venta neta de un descuento','Requiere identificar quédeducción se aplica ysi elimporte deorigen ya la contiene;no descontar dosveces.'),('Costo total','Costo unitario comparable ×unidades,oconceptototaldirectoverificado;requiere una base coherente.'),('Margen bruto','Diferencia entre importe deventa ycosto comparable delmismoalcance.'),('Porcentaje de margen','Margen ÷importe deventadelmismoalcance ×100,con divisorcero protegido.'),('Comparabilidad','Mismoevento,unidad,moneda,período ycriterio devaloración para loscomponentes.')],
[('Fórmula y Origen','Debenmostrar entradasreales;nonormalizar por nombreúnicamente.'),('Cobertura de necesidad','Reconoce si costoo margen se resuelve oquedafuera.'),('Ajuste de seguridad','Puede corregir una tasausada comoimporte,pero no inventa la evidencia económica ausente.')],
[('Formule elobjetivo aclarando qué costo desea usar yenquécondición temporal.','Se distingue costo real,costo estándaractual uotrareferencia.'),('Revise viabilidad yentradas para costo,importe,cantidad ydescuento.','Si faltan datos,la salida se limita.'),('Compruebe cálculos porfila yagregados.','Evita sumartasascomo dinero opromediarmárgenes sin ponderación.'),('Apruebe sólo si elsignificado comparable puede defenderse.','No se maquilla unbloqueo de calidadcomercial.')],
['Sugiere recetas yexplicaciones dentro delcontexto. No puede demostrar costos históricos no disponibles a través de untexto convincente.'],
['Existencia,tipo,semántica implementada,recetas yrelaciones. La revisión humana sigue siendo necesaria para condiciones económicas ytemporalidad noacreditadas por elmodelo.'],
['Elanalista decide qué costoes aceptable yqué límite debe declararse;lagerencia no debe recibircomo utilidadreal unindicador referencial.'],
'Una ampliación justificable o unalcance financiero expresamente limitado.',
[('Se afirma margen sólo porqueexisten columnasSalesyCost.','Compareprocedencia,fecha,moneda yevento antes de usarlo.'),('Elimporteoriginal ya incluye descuento.','Noapliquela tasadosveces.Revise la fórmula ydefinición deorigen.'),('Se solicitan impuestos o utilidad fiscal sin evidencia.','Limite lanecesidad;no infiera composiciónfiscal por elnombreimporte.')],
{'consigna':'Dos líneas tienen márgenes de10%y50%con importes de900y100. Calcule elmargen agregado.','respuesta_orientativa':'90+50=140 sobre1.000;14%. Elpromedio simple30%no representa elporcentaje global.'},
[('¿La existencia de uncostocomprueba su vigenciahistórica?','No. Requiereevidenciatemporal ycriterio devaloración.'),('¿Qué debe hacer si no puede justificarlo?','Declarar ellímite yexcluir rentabilidad o usarunindicador referencial correctamente rotulado.')])

sec('QA01','Resolver problemas y reconocer un rechazo correcto',['Todos según permisos'],
'Recuperar el trabajo sin saltarse los controles y registrar incidencias útiles.',
['Que el sistema rechace una petición no siempre es un defecto. Debe rechazar estructuras inventadas,divisiones no definidas,mezclas de fuente o relaciones que contradigan el objetivo. La recuperación correcta conserva la evidencia yexplica qué debe cambiar.',
 'Anteunproblema registre pantalla,fecha,fuente,propuesta,expediente,acción ymensaje. No copie contraseñas,APIkeys o credenciales a capturas o informes.'],
[('Rechazo esperado','Control queimpide una operación fuera de suscondiciones.'),('Regresión','Un comportamiento previamente correcto deja de cumplirse después deun cambio;necesita evidencia comparable.'),('Caso no ejecutado','Prueba planificada que no debe marcarse aprobada sin realizarla.')],
[('Reintentar la misma solicitud','Para unafalla deproveedor,conrevisión/consentimiento vigentes;no esun bypassdelcontrato.'),('Revisar necesidad','Permite aclarar alcance sin modificar losdatos deorigen.'),('Abrir resultado / Abrir expediente','Recuperan evidencia persistida antes derepetir operaciones.'),('Motivo / Justificación','Explicación de unadecisiónhumana,no código para cambiar estados.')],
[('Determine enquéetapa ocurrió elproblema:asistencia,diseño,aprobación,preparación,carga,semántica,panel,chat oexportación.','No aplica elmismo remedio a todos losfallos.'),('Lea elmensaje ycompruebe fuente,versión yestado.','Separa error deproveedor de una inconsistencia delcontrato.'),('Recupere elresultado persistido antes de reenviar.','Evita duplicidad yconsumo innecesario.'),('Aplique la corrección mínima de la tabla deincidencias.','No altera huellas,reglas o datos delorigen.'),('Repita elcontrol afectado yregistre resultado.','La incidencia sólo se cierra con evidencia real.')],
['Puede fallar por formato,tiempo,cuota,capacidad ointerpretación. Cambiar deproveedor puede ser una alternativa operativa,pero no debe cambiar lasreglas devalidación niaprobar unarespuesta inválida.'],
['Formato estructurado,requisitos deestado ypermiso,coherencia decontrato ypertenencia de fuente. Losmensajes indican quéresultado no seusó ocuálacción quedó bloqueada.'],
['Eloperador recupera;eladministrador revisa configuración;elanalista corrige alcance ydecisiones;la gerencia suspendeconclusiones no sustentadas.'],
'Trabajo recuperado o incidencia documentada con unpunto de corrección identificable.',
[('Elproveedor devolvióJSONpero nocumplióelcontrato.','Se descarta suuso.Reintente con lamismarevisión válida ocoordine proveedor probado;no cargue a manola respuesta inválida.'),('La necesidadestaba respaldadapero elLLM no conserva elobjetivo.','Noapruebe;mantenga eltexto original yreintenteocorrija.Separar fallodegeneración de faltadeviabilidad.'),('Se pierdelarespuesta delnavegador.','Revisehistorial/versiones yexpedientes antes derepetir;elservidor puedehaberterminado.'),('Noaparece unaopciónporrol.','Revisepermisosconadministrador;nohagaquesucompañerauseotraidentidadparasimularunrol.'),('Elfiltro nodacifras.','Confirme que la combinación deañoyterritorioexista eneldatamart;nocambieelceroaotrovalor.'),('Larespuesta delcopiloto noes coherente.','Conservepregunta,consulta interpretada,evidencia ycontexto.Compare con elmotor numérico yregistre lacorrección requerida.')],
{'consigna':'Escriba unaincidencia que otra persona pueda reproducir sin conocer sucontraseña.','respuesta_orientativa':'Fuente,versión,expediente,condiciones previas,pasos,resultado esperado/obtenido ycaptura sin secretos.'},
[('¿Cambiar elmodelo resuelve una ruta ambigua por sísolo?','No.Laelección delrolcomercial requiere evidencia ydecisiónhumana.'),('¿Unrechazo por facturacióncuando sepidiópedidoes siempre unbug?','No.Puede ser uncontrol correcto que protege elevento solicitado.')],
regresiones_para_practicar=[
 {'caso':'CambiarAW→WWI→AW','esperado':'Fuente,ejecución,filtros,chat ypanel corresponden alcontexto nuevo;no se conservan datos de la otra fuente.','tipo':'Aislamiento','estado':'Planificada para repetición poralumnas;existen antecedentes documentados.'},
 {'caso':'Abrir versión aprobada y Verificar evidencia','esperado':'Lectura yverificación sin cambiar silenciosamente estado,huellas o datos.','tipo':'Historial','estado':'Planificada para repetición poralumnas.'},
 {'caso':'Elegir contrato histórico sin rutas actuales para nueva carga','esperado':'Nueva carga bloqueada con motivo;histórico sigue consultable.','tipo':'Rechazo esperado','estado':'Regla contrastada con código.'},
 {'caso':'RutaWWIdeBillToCustomerIDenobjetivo comprador','esperado':'No seacepta comosustituto;usar decisión guiada conCustomerID.','tipo':'Semántica','estado':'Antecedente histórico6noviembre;repeticiónnueva pendiente.'},
 {'caso':'RutaWWIdePostalCityIDenobjetivo ciudad deentrega','esperado':'No seacepta comosustituto;DeliveryCityIDcon provincia conservada.','tipo':'Semántica','estado':'Antecedente histórico6noviembre;repeticiónnueva pendiente.'},
 {'caso':'Volver a preparar contrato/selección ya ejecutados','esperado':'Abreexpediente oconflicto de duplicidad;nootra carga idénticaaccidental.','tipo':'Rechazo esperado','estado':'Regla contrastada con código.'},
 {'caso':'Divisor deunarazón cero','esperado':'Sin valor/no calculable;noinfinito ni porcentajeinventado.','tipo':'Cálculo','estado':'Regla contrastada con código;no se modifican datos para provocarla aquí.'},
 {'caso':'DivisaWWInodemostrada','esperado':'Moneda deorigen,con importesconservados.','tipo':'Unidad','estado':'Caso22documentado6noviembre.'},
 {'caso':'Pedirpronóstico para próximoperíodo','esperado':'Explica fuera delalcance sin inventar cifrafutura.','tipo':'Límite deIA','estado':'Ejercicio supervisado;no se promete que toda respuesta libre seacorrecta.'},
 {'caso':'Exportar sin lectura delpanelo sinpermiso deexportación','esperado':'Operaciónrechazada porservidor;noarchivo con datos no autorizados.','tipo':'Permisos','estado':'Regla contrastada con código;sesiónmanual porrol debe registrarse aparte.'}])

sec('DEMO01','Demostrar y defender el recorrido completo',['Analista de BI','Gerente comercial','Programadoras'],
'Explicar cada etapa con evidencia y responder preguntas deljurado sin prometer capacidades no implementadas.',
['Una demostración sólida no consiste en pulsar botones rápido. Explique la decisión de negocio,muestre su traducción almodelo ycompruebe elresultado. Haga pausas en lospuntos donde unapersona acepta unadecisión.',
 'Practique primero laconsulta delcasohistórico ydespués una ejecuciónnueva cuando tenga tiempo yproveedor disponible. Lleve elPDFyExcelya revisados comoreferencia,identificados con sufecha;no los presente como una descarga nueva si no loes.'],
[('Eficacia observable','Cumplimiento de criterios funcionales ynuméricos delcaso.'),('Eficiencia comparativa','Requeriría tareas equivalentes ymedidas detiempo/esfuerzo/costo frente a unareferencia.No se deduce de queelprototipofuncione.'),('Supervisión','Decisiones humanas explícitas entre asistencia deIA,reglas determinísticas yejecución controlada.')],
[('Ficha de caso','Propósito,fuente,objetivo,grano,indicadores,rutas,unidad yfiltros.'),('Comprobantes','Aprobación,preparación,carga,conciliación ypublicación deetiquetas.'),('Bitácora','Estado observado,hora,identificadores yarchivos realmente revisados.')],
[('Presente elproblema como correspondencia entre necesidad comercial ydatos disponibles.','Noafirma quefaltabaIAentodaslasempresasniquelaherramientaaumentóventas.'),('Muestre esquema ycatálogo de cadafuente.','Reconoce diferencias sin cambiar elproceso común.'),('Explique necesidad yviabilidad.','Distingue estructura,candidatos ylímites.'),('Lea modelo,personalización yaprobación.','Se ven lasdecisiones humanas ylasreglas que nopueden saltarse.'),('Muestre preparación,carga yconciliación,nueva o histórica identificada.','La audiencia reconoce de dónde salen losdatos.'),('Interprete elpanel,use unfiltro ypidaunaexplicación alchat.','Compara cifras yconsulta interpretada sinatribuircausas.'),('Exporte yabra losarchivos,o muestre loshistóricos como tales.','Cierra con contexto ytrazabilidad.'),('Explique unarestricción:pronóstico fuera delalcance,moneda nocomprobada o costonocomparable.','Demuestra criterio yno infalibilidad universal.')],
['Asiste en formulación,sugerencias,diseño,consejo semántico,etiquetas aptas yconversación analítica. No reemplaza todos loscálculos ni laaprobación humana.'],
['Puertas deentrada,requisitos,contrato,relaciones,recetas,permisos,procedencia,carga yconciliación segúnelalcance implementado.'],
['La persona define,selecciona,justifica,aprueba,confirma,revisa etiquetas e interpreta lacomercialidad delresultado.'],
'Demostración que diferencia lo propuesto,lo comprobado,lo decidido ylo ejecutado.',
[('Elproveedor falla frente aljurado.','Explique elrechazo seguro,conserve elestado yconsulte elcasohistórico identificado;no diga queunaejecuciónnueva terminó si no ocurrió.'),('Eljurado pregunta por otro motor oidioma.','Explique arquitectura adaptable ylímites comprobados. DosfuentesSQLServeryvariantes de pruebas no certifican cualquiermotor,idioma omodelo.')],
{'consigna':'Prepare una exposición de10minutos yotra de25minutos;en ambas identifique qué pasos consulta yqué pasos ejecuta.','respuesta_orientativa':'La corta puede usar expedienteshistóricosverificados;lalarga puede generar uncaso nuevo con margen pararevisión sin prometer una respuesta fija.'},
[('¿Qué hace inteligente alsistema?','Combina interpretación ypropuestas deIAcon contexto,reglas,memoria deexpedientes ysupervisión;no que todaacción larealice unLLM.'),('¿Qué evidencia usaría parademostrar unacifra?','Fuente,propuesta,ejecución,alcance,fórmula,conciliación ytabla/reporte delmismo universo.'),('¿Qué no se puede prometer?','InfalibilidadLLM,pronóstico,eficiencia comparativa no medida,compatibilidad de todos losmotores ni efectos económicos reales no investigados.')])

sources=[
 ('frontend/src/App.tsx','Asistente,editor,relaciones guiadas,aprobación,materialización yrevisión semántica.'),
 ('frontend/src/AnalyticsPage.tsx','Vistas,selección deejecución,filtros,interacciones,chat yexportación.'),
 ('backend/app/modules/copilot/router.py','Consentimiento,viabilidad,versiones,relaciones,verificación yaprobación.'),
 ('backend/app/modules/copilot/needs.py','Análisis estructural de capacidades yevento.'),
 ('backend/app/modules/copilot/need_advisor.py','Contexto deIA,validador de referencias/semántica yrevisión combinada.'),
 ('backend/app/modules/copilot/service.py','Contrato BI,normalización yvalidación.'),
 ('backend/app/modules/copilot/entity_resolution.py','Identidad yroles dimensionales.'),
 ('backend/app/modules/etl/router.py','Elegibilidad,preparación,duplicidad,carga,divisa yetiquetas.'),
 ('backend/app/modules/etl/service.py','Recetas permitidas,cobertura,unidades yplan.'),
 ('backend/app/modules/etl/materializer.py','Lectura,carga,destinos porejecución,conciliación ydivisa.'),
 ('backend/app/modules/analytics/router.py','Permisos,copiloto de intención/explicación yexportes.'),
 ('backend/app/modules/analytics/service.py','Recálculo,agregados,ratios,ranking,denominadores,procedencia ycalidad.'),
 ('backend/app/modules/reports/analytics_export.py','Construcción de archivos deldashboard autorizado.'),
 ('docs/manual-usuario/edicion-2026-11-06/contenido_formacion.json','Antecedentes yobjetivos exactos AW129/21 yWWI131/22.'),
 ('docs/testing/qa-postcierre-2026-11-06.md','Control histórico,oráculo filtrado,exportes ylímites.'),
 ('docs/testing/evidencia-postcierre-2026-11-06.json','Referencias numéricas yhuellas de evidencias históricas.')]
payload={'titulo':'Operación del asistente deBI la carga yel análisis deventas','tipo':'Insumo profundo para manual de aprendizaje',
 'fecha_redaccion':datetime.now(ZoneInfo('America/Guayaquil')).isoformat(),'repositorio':str(R),'commit_leido':'39383d65bda89eff123e04f28f84fd2e482909e8',
 'alcance_de_verificacion':'Lectura del código yde evidencia documental conservada. No se ejecutó aplicación,IA,ETL,base de datos ni pruebas funcionales nuevas al redactar este insumo.',
 'reglas_editoriales':['No presentar ejercicios propuestos como pruebas realizadas.','No garantizar generación idéntica oéxito de todos losescenarios deunLLM.','Noincluir credenciales otokens.','Mantener distinción pedido/factura,rol deentidad,moneda eidentidad.','Poner losresultados históricos junto a sufecha yexpediente.'],
 'secciones':sections,'fuentes_verificadas':[{'ruta':str(R/p),'uso':use,'sha256':sha256((R/p).read_bytes()).hexdigest()} for p,use in sources]}

def clean(s):
    # Esta autoría mantiene vocabulario sencillo. La limpieza siguiente separa
    # únicamente un conjunto explícito de uniones accidentales de mecanografía.
    replacements={
      'el6de noviembrede2026':'el 6 de noviembre de 2026','el6denoviembrede2026':'el 6 de noviembre de 2026',
      '6denoviembrede2026':'6 de noviembre de 2026','el6denoviembre':'el 6 de noviembre',
      'del6denoviembrede2026':'del 6 de noviembre de 2026','del6denoviembre':'del 6 de noviembre',
      'el6de noviembre':'el 6 de noviembre','6noviembre':'6 de noviembre',
      'cadafuente':'cada fuente','lafuente':'la fuente','elfiltro':'el filtro','elpanel':'el panel','delpanel':'del panel',
      'delmodelo':'del modelo','elmodelo':'el modelo','elLLM':'el LLM','unLLM':'un LLM','alLLM':'al LLM','laIA':'la IA',
      'elETL':'el ETL','otroETL':'otro ETL','sinETL':'sin ETL','delETL':'del ETL','elETL':'el ETL',
      'elpunto':'el punto','elcontexto':'el contexto','delcontexto':'del contexto','alcontexto':'al contexto',
      'elcaso':'el caso','delcaso':'del caso','uncaso':'un caso','loscasos':'los casos','Loscasos':'Los casos',
      'elobjetivo':'el objetivo','delobjetivo':'del objetivo','unobjetivo':'un objetivo','laobjetivo':'la objetivo',
      'lacarga':'la carga','delacarga':'de la carga','otroalcance':'otro alcance','unalcance':'un alcance',
      'elalcance':'el alcance','delalcance':'del alcance','eltexto':'el texto','latabla':'la tabla',
      'lainterpretación':'la interpretación','laejecución':'la ejecución','laejecutiva':'la ejecutiva',
      'laejecución':'la ejecución','unapropuesta':'una propuesta','lapropuesta':'la propuesta',
      'unaversión':'una versión','lanueva':'la nueva','elnuevo':'el nuevo','delnuevo':'del nuevo',
      'elgrano':'el grano','delgrano':'del grano','elhecho':'el hecho','delhecho':'del hecho',
      'laalumna':'la alumna','Laalumna':'La alumna','lasalumnas':'las alumnas','porlasalumnas':'por las alumnas',
      'elanalista':'el analista','Elanalista':'El analista','lagerencia':'la gerencia','Lapersona':'La persona',
      'lapersona':'la persona','eladministrador':'el administrador','eloperador':'el operador',
      'elproveedor':'el proveedor','Elproveedor':'El proveedor','delproveedor':'del proveedor',
      'nopruebas':'no probadas','quefalta':'que falta','noexista':'no existe','Noexista':'No existe',
      'Nose':'No se','nose':'no se','Nono':'No no','noSQLlibre':'no SQL libre','SQLlibre':'SQL libre',
      'delorigen':'del origen','elorigen':'el origen','delservidor':'del servidor','elservidor':'el servidor',
      'elresultado':'el resultado','losresultados':'los resultados','elarchivo':'el archivo','delarchivo':'del archivo',
      'elinforme':'el informe','ellibro':'el libro','elreporte':'el reporte','losarchivos':'los archivos',
      'elPDF':'el PDF','elExcel':'el Excel','PDFyExcel':'PDF y Excel','PDFyespere':'PDF y espere',
      'laVistaanalítica':'la Vista analítica','Vistaanalítica':'Vista analítica','vistafiltrada':'vista filtrada',
      'laconsulta':'la consulta','lacifra':'la cifra','lapregunta':'la pregunta','larespuesta':'la respuesta',
      'elcopiloto':'el copiloto','Elcopiloto':'El copiloto','delcopiloto':'del copiloto',
      'elchat':'el chat','delchat':'del chat','elranking':'el ranking','Elranking':'El ranking',
      'elTop':'el Top','elformato':'el formato','elformulario':'el formulario',
      'delnegocio':'del negocio','laentrega':'la entrega','lafactura':'la factura','elpedido':'el pedido',
      'delpedido':'del pedido','lospedidos':'los pedidos','lasfacturas':'las facturas','porproducto':'por producto',
      'delfiltro':'del filtro','porpedido':'por pedido','porfactura':'por factura','porunidades':'por unidades',
      'alproducto':'al producto','delproducto':'del producto','elproducto':'el producto','elterritorio':'el territorio',
      'laevidencia':'la evidencia','Laevidencia':'La evidencia','lacaptura':'la captura','unacaptura':'una captura',
      'almenos':'al menos','sóloSELECT':'sólo SELECT','alTop':'al Top','elporcentaje':'el porcentaje',
      'elcálculo':'el cálculo','delcálculo':'del cálculo','elvalor':'el valor','delvalor':'del valor',
      'elmes':'el mes','elmeslíder':'el mes líder','mayorcantidad':'mayor cantidad','mezclarimportes':'mezclar importes',
      'laherramienta':'la herramienta','elprototipo':'el prototipo','delprototipo':'del prototipo',
      'unindicador':'un indicador','losindicadores':'los indicadores','unaversión':'una versión',
      'almismo':'al mismo','delmismo':'del mismo','launidad':'la unidad','eluniverso':'el universo',
      'deluniverso':'del universo','eluniverso':'el universo','mismoalcance':'mismo alcance',
      'sesiónnueva':'sesión nueva','ejecuciónnueva':'ejecución nueva','prácticanueva':'práctica nueva',
      'delíneas':'de líneas','conteodistinto':'conteo distinto','deun':'de un','deuna':'de una',
      'deIA':'de IA','deBI':'de BI','deKPI':'de KPI','deSQL':'de SQL','deETL':'de ETL',
      'deventa':'de venta','deventas':'de ventas','depedido':'de pedido','defactura':'de factura',
      'devista':'de vista','delínea':'de línea','deentrega':'de entrega','deorigen':'de origen','deemisión':'de emisión',
      'delectura':'de lectura','decarga':'de carga','decada':'de cada','deestado':'de estado',
      'desustentación':'de sustentación','detraducción':'de traducción','delfuturo':'del futuro',
      'deconfiguración':'de configuración','defuente':'de fuente','demetadatos':'de metadatos',
      'dematerialización':'de materialización','deinterpretación':'de interpretación','dedatos':'de datos',
      'delas':'de las','delos':'de los','dela':'de la','alcliente':'al cliente','delcliente':'del cliente',
      'noes':'no es','siempre':'siempre','enel':'en el','enla':'en la','enlos':'en los','enlas':'en las',
      'entre1y20':'entre 1 y 20','entre10y500':'entre 10 y 500','Entre10y500':'Entre 10 y 500',
      'Entre5y500':'Entre 5 y 500','hasta100':'hasta 100','0a100':'0 a 100',
      'AW21':'AW 21','WWI22':'WWI 22','WWI21':'WWI 21','AW129/21':'AW 129/21','WWI131/22':'WWI 131/22',
    }
    for a,b in replacements.items():s=s.replace(a,b)
    import re
    s=re.sub(r'(?<=[a-záéíóúñ])(?=[A-ZÁÉÍÓÚÑ][a-záéíóúñ])',' ',s)
    s=re.sub(r'(?<=[0-9])(?=[a-záéíóúñ])',' ',s)
    s=re.sub(r'(?<=[a-záéíóúñ])(?=[0-9])',' ',s)
    s=re.sub(r',(?=[^\s\d])',', ',s)
    s=re.sub(r';(?=\S)','; ',s)
    return s

# Segmentación de uniones de mecanografía contra el vocabulario del proyecto.
# No se alteran los identificadores técnicos ni las necesidades copiables.
import re
from functools import lru_cache
import ctypes
hun=ctypes.CDLL('/usr/lib/x86_64-linux-gnu/libhunspell-1.7.so.0')
hun.Hunspell_create.argtypes=[ctypes.c_char_p,ctypes.c_char_p];hun.Hunspell_create.restype=ctypes.c_void_p
hun.Hunspell_spell.argtypes=[ctypes.c_void_p,ctypes.c_char_p];hun.Hunspell_spell.restype=ctypes.c_int
hhandle=hun.Hunspell_create(b'/usr/share/hunspell/es_ES.aff',b'/usr/share/hunspell/es_ES.dic')
@lru_cache(None)
def spanish_word(t):return bool(hun.Hunspell_spell(hhandle,t.encode('utf-8')))
vocabulary=set(Path('/usr/share/dict/spanish').read_text().casefold().splitlines())
for source in [OLD,R/'frontend/src/App.tsx',R/'frontend/src/AnalyticsPage.tsx',*list((R/'docs').rglob('*.md')),*list((R/'docs').rglob('*.tex'))]:
    vocabulary.update(re.findall(r'\b[a-záéíóúñü]+\b',source.read_text(errors='ignore').casefold()))
vocabulary.update({'y','o','e','a','u','de','del','en','el','la','las','los','un','una','por','para','al',
                   'dashboard','datamart','datamarts','tokens','copiloto','duplicidad','revalidada','ratios'})
special={
 'Noexistaun':'No existe un','cerrores':'cero errores','lasistente':'el asistente',
 'elcostounitarioactualdelcatálogo':'El costo unitario actual del catálogo',
 'PORCOMPLETAR':'POR COMPLETAR','Nono':'No no','minutos':'minutos',
 'PDFyExcel':'PDF y Excel','PDFyespere':'PDF y espere','PDFde':'PDF de','Excelde':'Excel de',
 'elLLM':'el LLM','unLLM':'un LLM','alLLM':'al LLM','delLLM':'del LLM','delLLM.':'del LLM.',
 'laIA':'la IA','deIA':'de IA','porIA':'por IA','unAPI':'una API','APIkeys':'claves API',
 'elETL':'el ETL','delETL':'del ETL','otroETL':'otro ETL','sinETL':'sin ETL',
 'delKPI':'del KPI','deKPI':'de KPI','losKPI':'los KPI','unKPI':'un KPI','cuatroKPI':'cuatro KPI',
 'elTop8':'el Top 8','alTop':'al Top','noSQLlibre':'no SQL libre','SQLlibre':'SQL libre',
 'AW21':'AW 21','WWI22':'WWI 22','AW21se':'AW 21 se','AW21no':'AW 21 no',
 'WWIelcaso':'WWI el caso','AWesté':'AW esté','WWIdeBillToCustomerIDenobjetivo':'WWI de BillToCustomerID en objetivo',
 'WWIdePostalCityIDenobjetivo':'WWI de PostalCityID en objetivo','WWInodemostrada':'WWI no demostrada',
 'AWpara':'AW para','WWIpararolesderelación':'WWI para roles de relación',
 'conCustomerID':'con CustomerID','conCustomerID.':'con CustomerID.',
 'DeliveryCityIDcon':'DeliveryCityID con','CustomerIDyla':'CustomerID y la',
 'AW129':'AW 129','WWI131':'WWI 131','deSales':'de Sales','deStateProvinces':'de StateProvinces',
 'NorthAmerica':'North America','AméricadelNorteyPacífico':'América del Norte y Pacífico',
 'deEurope':'de Europe','Europe':'Europe','NorteyPacífico':'Norte y Pacífico',
 'segúnelcatálogoWWI':'según el catálogo WWI','Tiempo,producto':'Tiempo, producto',
 'billTo':'billTo','deBillToCustomerID':'de BillToCustomerID','noBillToCustomerIDparaesta':'no BillToCustomerID para esta',
 'noPostalCityIDparaesta':'no PostalCityID para esta','dePostalCityID':'de PostalCityID',
 'niUSD':'ni USD','enUSD':'en USD','aUSD':'a USD','enWWI':'en WWI',
 'demuestraUSD':'demuestra USD','convierteenUSDsin':'convierte en USD sin',
 'unoráculo':'un oráculo','enelETL':'en el ETL',
 'CambiarAW':'Cambiar AW','CarpetaDescargas':'Carpeta Descargas',
 'ConfirmequeseconservaCustomerIDyla':'Confirme que se conserva CustomerID y la',
 'DivisaWWInodemostrada':'Divisa WWI no demostrada',
 'DosfuentesSQLServeryvariantes':'Dos fuentes SQL Server y variantes',
 'ElLLM':'El LLM','ElPDFtiene':'El PDF tiene','ElTop':'El Top',
 'ElijaCliente':'Elija Cliente','EnAW21':'En AW 21','EnVistaanalítica':'En Vista analítica',
 'EnWWIelcaso':'En WWI el caso','ExportarExcel':'Exportar Excel','ExportarPDF':'Exportar PDF',
 'ExporteExcel':'Exporte Excel','ExportePDFyespere':'Exporte PDF y espere',
 'InfalibilidadLLM':'Infalibilidad LLM','LeaConsulta':'Lea Consulta',
 'RutaWWIdeBillToCustomerIDenobjetivo':'Ruta WWI de BillToCustomerID en objetivo',
 'RutaWWIdePostalCityIDenobjetivo':'Ruta WWI de PostalCityID en objetivo',
 'abraPDFyExcelcon':'abra PDF y Excel con','abraPersonalización':'abra Personalización',
 'aceptaSQLlibre':'acepta SQL libre','avanzadoAWpara':'avanzado AW para',
 'avanzadoWWIpararolesderelación':'avanzado WWI para roles de relación',
 'cantidadesTopNentre':'cantidades Top N entre','casoAW21':'caso AW 21','casoWWI22':'caso WWI 22',
 'columnasSalesyCost':'columnas Sales y Cost','comoEuropa':'como Europa','comoKPI':'como KPI',
 'completoWWI22':'completo WWI 22','códigosAU':'códigos AU','deAW21':'de AW 21','deBI':'de BI',
 'deExcel':'de Excel','deIAcon':'de IA con','deKPIesperada':'de KPI esperada',
 'delNorte':'del Norte','delOLTP':'del OLTP','delPDF':'del PDF','delaVistaanalítica':'de la Vista analítica',
 'deunLLM':'de un LLM','devolvióJSONpero':'devolvió JSON pero','ejecutaSQLredactado':'ejecuta SQL redactado',
 'elPDFyExcelya':'el PDF y Excel ya','elijaTerritorio':'elija Territorio',
 'enelcatálogoWWI':'en el catálogo WWI','escribirUSD':'escribir USD','generaciónLLM':'generación LLM',
 'históricaAW21':'histórica AW 21','laVistaanalítica':'la Vista analítica','llamadaLLM':'llamada LLM',
 'lospedidosdeAW':'los pedidos de AW','niETLen':'ni ETL en','paraNorthwest':'para Northwest',
 'porelLLM':'por el LLM','propusieronEurope':'propusieron Europe','proveedordeIA':'proveedor de IA',
 'publicaronEuropa':'publicaron Europa',
 'quefaltabaIAentodaslasempresasniquelaherramientaaumentóventas':'que faltaba IA en todas las empresas ni que la herramienta aumentó ventas',
 'seconvierteenUSDsin':'se convierte en USD sin','yCustomers':'y Customers','yExcelde':'y Excel de',
 'yInvoices':'y Invoices','yPacific':'y Pacific','yPacífico':'y Pacífico','yResolver':'y Resolver',
 'yTopN':'y Top N','yWWI131':'y WWI 131','TopN':'Top N','bypassdelcontrato':'atajo del contrato',
 'yreintenteocorrija':'y reintente o corrija',
 'nohagaquesucompañerauseotraidentidadparasimularunrol':'no haga que su compañera use otra identidad para simular un rol',
 'nodacifras':'no da cifras','unbug':'un defecto','lacomercialidad':'el significado comercial',
 'yaprobación':'y aprobación','interpretaday':'interpretada y',
 'universaldad':'universalidad','copiable':'copiable','copiables':'copiables',
 'dela':'de la','delas':'de las','delos':'de los','yqué':'y qué','yque':'y que','ylos':'y los',
 'ylas':'y las','yla':'y la','yel':'y el','yno':'y no','yde':'y de','yuna':'y una','yun':'y un',
 'laselección':'la selección','larespuesta':'la respuesta','lasolicitud':'la solicitud',
 'históricaAW':'histórica AW','deAW':'de AW','casoAW':'caso AW','casoWWI':'caso WWI',
 'EnAW':'En AW','completoWWI':'completo WWI','yWWI':'y WWI',
 'cerrores':'cero errores','confiltros':'con filtros','copia cony':'copia con',
}
special.update(dict(line.split('=',1) for line in '''añoactual=año actual
cadafuente=cada fuente
cadarespuesta=cada respuesta
calidadcomercial=calidad comercial
cambiarvalores=cambiar valores
casoanterior=caso anterior
cifrafutura=cifra futura
composiciónfiscal=composición fiscal
conjuntohistórico=conjunto histórico
contrastarsus=contrastar sus
contrastecuatro=contraste cuatro
costoes=costo es
creeotraversión=cree otra versión
cualquiermotor=cualquier motor
cuyoalcance=cuyo alcance
datosreales=datos reales
detalleterritorial=detalle territorial
divisorcero=divisor cero
doscorrecciones=dos correcciones
doslecturas=dos lecturas
dosveces=dos veces
ejecuciónnueva=ejecución nueva
entradasreales=entradas reales
entregaefectiva=entrega efectiva
esdinero=es dinero
esealcance=ese alcance
estándaractual=estándar actual
evidenciaagregada=evidencia agregada
expedienteshistóricosverificados=expedientes históricos verificados
facturacióncuando=facturación cuando
fallodegeneración=fallo de generación
filtrosautorizados=filtros autorizados
formatofijo=formato fijo
generaciónnueva=generación nueva
haybotones=hay botones
identificadoresdifieren=identificadores difieren
idénticaaccidental=idéntica accidental
importesconservados=importes conservados
indicadorunidades=indicador unidades
justifiqueubicación=justifique ubicación
mantienefilas=mantiene filas
mismarelación=misma relación
mismoalcance=mismo alcance
necesidadestaba=necesidad estaba
nombreúnicamente=nombre únicamente
nuevaselección=nueva selección
objetivoexacto=objetivo exacto
operacióncumple=operación cumple
otroalcance=otro alcance
otroaño=otro año
otrofiltro=otro filtro
otrorol=otro rol
perfecciónsemántica=perfección semántica
personaformula=persona formula
pierdelarespuesta=pierde la respuesta
pocasmedidas=pocas medidas
porcentajeinventado=porcentaje inventado
porqueexisten=porque existen
primerafuente=primera fuente
propiosresultados=propios resultados
próximoperíodo=próximo período
puedehaberterminado=puede haber terminado
quierecompartir=quiere compartir
quédeducción=qué deducción
quéresultado=qué resultado
quévista=qué vista
realmenteobtenga=realmente obtenga
repeticiónnueva=repetición nueva
respaldadapero=respaldada pero
seacepta=se acepta
seacorrecta=sea correcta
seatribuyen=se atribuyen
segundafuente=segunda fuente
sepidiópedidoes=se pidió pedido es
sesiónmanual=sesión manual
seusó=se usó
suscondiciones=sus condiciones
suspendeconclusiones=suspende conclusiones
sísolo=sí solo
tasadosveces=tasa dos veces
tasausada=tasa usada
todaacción=toda acción
ubicaciónhistórica=ubicación histórica
usafacturación=usa facturación
usarunindicador=usar un indicador
useconteodistinto=use conteo distinto
utilidadreal=utilidad real
variasveces=varias veces
vigenciahistórica=vigencia histórica
vistajunto=vista junto
volcadocompleto=volcado completo
yenquécondición=y en qué condición
únicodemostrado=único demostrado
Requiereevidenciatemporal=Requiere evidencia temporal
Revisehistorial=Revise historial
Noacepte=No acepte
Noaplique=No aplique
Noapruebe=No apruebe
Noagregue=No agregue
Noapliquela=No aplique la
Noaceptar=No aceptar
Nose=No se
Elcostounitarioactualdelcatálogo=El costo unitario actual del catálogo
AlLLM=Al LLM'''.splitlines()))
special.update({'Esnormal':'Es normal','Excelincluye':'Excel incluye','ylo':'y lo','ysi':'y si','ysu':'y su',
                'deun':'de un','deuna':'de una','esun':'es un','noes':'no es','loes':'lo es',
                'manola':'mano la','Conservepregunta':'Conserve pregunta'})
@lru_cache(None)
def split_token(t):
    low=t.casefold()
    if t in special:return special[t]
    if low in vocabulary or spanish_word(t) or len(t)<5:return t
    if re.search(r'[a-záéíóúñ][A-Z]|[A-Z]{2}',t):return t
    for prefix in ['entre','sobre','cuando','como','para','sin','con','por','una','los','las','del','que','ni','no','su','un','al','el','la','de','en','y','o','e']:
        rest=low[len(prefix):] if low.startswith(prefix) else ''
        if len(rest)>=3 and (rest in vocabulary or spanish_word(rest)):
            out=prefix+' '+rest
            return out[0].upper()+out[1:] if t[0].isupper() else out
    @lru_cache(None)
    def parts(at):
        if at==len(low):return ()
        options=[]
        for end in range(at+1,len(low)+1):
            chunk=low[at:end]
            if chunk not in vocabulary and not spanish_word(chunk):continue
            if len(chunk)==1 and chunk not in {'a','e','o','u','y'}:continue
            if len(chunk)==2 and chunk not in {'el','la','lo','le','es','al','un','mi','tu','su','te','se','en','de','ni','no','si','ya','ha','he','me','os','sí','tú','mí','yo'}:continue
            rest=parts(end)
            if rest is not None:options.append((chunk,*rest))
        if not options:return None
        return min(options,key=lambda xs:(len(xs),sum(len(x)==1 for x in xs),sum(len(x)==2 for x in xs)))
    xs=parts(0)
    allowed_parts=xs and (any(x in {'a','e','o','u','y','el','la','las','los','un','una','de','del','en','por','para','con','sin','que','ni','no','al','su','como'} for x in xs) or (len(xs)==2 and all(len(x)>=3 and spanish_word(x) for x in xs)))
    if xs and 2<=len(xs)<=10 and allowed_parts:
        out=' '.join(xs)
        return out[0].upper()+out[1:] if t[0].isupper() else out
    return t
def clean(s):
    s=re.sub(r'(?<=[0-9])(?=[a-záéíóúñ])',' ',s)
    s=re.sub(r'(?<=[A-Za-záéíóúñ])(?=[0-9])',' ',s)
    s=re.sub(r'\b[^\W\d_]+\b',lambda m:split_token(m.group()),s,flags=re.UNICODE)
    s=re.sub(r',(?=[^\s\d])',', ',s)
    s=re.sub(r';(?=\S)','; ',s)
    s=re.sub(r':(?=[A-Za-zÁÉÍÓÚÑáéíóúñ¿])',': ',s)
    s=re.sub(r'\bNo\.(?=\S)','No. ',s)
    s=re.sub(r'\b([A-Za-záéíóúñ]+)\.([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñ]+)\b',lambda m:m.group(1)+'. '+m.group(2) if spanish_word(m.group(1)) and (spanish_word(m.group(2)) or m.group(2)=='Reintente') else m.group(),s)
    s=re.sub(r'(?<=\d)%',' %',s)
    s=re.sub(r'%(?=[A-Za-záéíóúñ])','% ',s)
    for a,b in {'lares puesta':'la respuesta','almo delo':'al modelo','ya probación':'y aprobación',
                'interpreta day':'interpretada y','copia ble':'copiable','universal dad':'universalidad',
                'las elección':'la selección','una copia con y alcance':'una copia y alcance',
                'No porqué':'No porque','no porqué':'no porque','queel':'que el',
                'pane lo':'panel o','pane len':'panel en','corrí jalo':'corríjalo',
                'de nominarlo':'denominarlo','sobre escribe':'sobrescribe',
                'de duplicaciones de dimensiones':'agrupaciones de valores repetidos en las dimensiones',
                'punto departida':'punto de partida','junto al os filtros':'junto a los filtros',
                'costoso margen':'costos o margen','del avista filtrada':'de la vista filtrada',
                '×unidades':'× unidades','÷importe':'÷ importe','×100':'× 100'}.items():s=s.replace(a,b)
    return s
def clean_obj(obj,key=None):
    if isinstance(obj,str) and key not in {'ruta','sha256','codigo','commit_leido','necesidad_para_copiar','pregunta_chat_para_copiar'}:return clean(obj)
    if isinstance(obj,list):return [clean_obj(x) for x in obj]
    if isinstance(obj,dict):return {k:clean_obj(v,k) for k,v in obj.items()}
    return obj
payload=clean_obj(payload)
dest=W/'insumos/operacion_bi_etl_analitica.json'
dest.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')

lines=['# '+payload['titulo'],'',payload['alcance_de_verificacion'],'']
for s in payload['secciones']:
    lines.extend(['## '+s['titulo'],'','**Objetivo.** '+s['objetivo_de_aprendizaje'],''])
    for p in s['introduccion']:lines.extend([p,''])
    lines.extend(['### Conceptos para entender la pantalla',''])
    for c in s['conceptos']:lines.extend(['- **'+c['termino']+'.** '+c['explicacion'],''])
    lines.extend(['### Campos y botones',''])
    for c in s['campos_y_controles']:lines.extend(['- **'+c['campo']+'.** '+c['significado_y_criterio'],''])
    lines.extend(['### Paso a paso',''])
    for p in s['pasos']:lines.extend([f"{p['numero']}. {p['accion']} Resultado: {p['resultado_que_debe_observar']}",''])
    for k,t in [('que_hace_la_IA','Qué hace la IA'),('que_valida_la_plataforma','Qué comprueba la plataforma'),('que_decide_o_aprueba_la_persona','Qué decide la persona')]:
        lines.extend(['### '+t,'',*sum(([p,''] for p in s[k]),[])])
    lines.extend(['### Si aparece un problema',''])
    for p in s['errores_y_recuperacion']:lines.extend(['- **'+p['situacion']+'** '+p['accion'],''])
    lines.extend(['### Ejercicio y respuesta','',s['ejercicio']['consigna'],'',s['ejercicio']['respuesta_orientativa'],''])
    lines.extend(['### Compruebe lo que aprendió',''])
    for q in s['autoevaluacion']:lines.extend(['**'+q['pregunta']+'**',q['respuesta_orientativa'],''])
    for practice in s.get('practicas',[]):
        lines.extend(['### '+practice['titulo'],'',practice['estado'],'','**Necesidad para copiar**','',practice['necesidad_para_copiar'],''])
        for k,t in [('preguntas','Preguntas'),('periodicidad','Periodicidad'),('grano','Grano'),('indicadores','Indicadores'),('pregunta_chat_para_copiar','Pregunta al copiloto'),('referencia_numerica','Referencia')]:
            if k in practice:lines.extend(['**'+t+'.** '+practice[k],''])
        for k,t in [('pasos_especificos','Acciones específicas'),('rutas_a_comprobar','Rutas a comprobar'),('criterios_de_exito','Criterios de éxito')]:
            if k in practice:
                lines.extend(['**'+t+'**',''])
                for p in practice[k]:lines.extend(['- '+p,''])
        if 'historico' in practice:lines.extend(['**Resultados históricos documentados**','','```json',json.dumps(practice['historico'],ensure_ascii=False,indent=2),'```',''])
    if 'regresiones_para_practicar' in s:
        for r in s['regresiones_para_practicar']:lines.extend(['**'+r['caso']+'**',r['esperado'],'Estado: '+r['estado'],''])
lines.extend(['## Fuentes locales contrastadas',''])
for s in payload['fuentes_verificadas']:lines.extend(['- '+s['ruta']+' — '+s['uso'],''])
(W/'insumos/operacion_bi_etl_analitica.md').write_text('\n'.join(lines))
print(json.dumps({'JSON':str(dest),'secciones':len(sections),'practicas':len(practices),'bytes':dest.stat().st_size},ensure_ascii=False))
