# Operación del asistente de BI la carga y el análisis de ventas

Lectura del código y de evidencia documental conservada. No se ejecutó aplicación, IA, ETL, base de datos ni pruebas funcionales nuevas al redactar este insumo.

## Antes de empezar piense qué decisión necesita apoyar

**Objetivo.** Distinguir la pregunta comercial, el evento y el nivel de detalle antes de pedir un datamart.

Un datamart reúne datos organizados para un análisis concreto. En este proyecto el punto de partida es una necesidad de ventas escrita por una persona. La plataforma ayuda a relacionarla con la estructura disponible y conserva las decisiones que llevan hasta el tablero.

Antes de abrir el asistente, escriba qué quiere comparar, con qué indicador, por qué entidades y en qué período. Elija si observa pedidos o facturas. Un pedido representa una solicitud de venta; una factura representa otro evento. Sus importes no demuestran por sí solos cobro, entrega realizada o utilidad.

La interfaz ofrece un proceso común para fuentes distintas. La demostración comprobada utiliza dos bases SQL Server. Cambian sus tablas, claves y significados; no debe copiarse la elección técnica de una base a otra sólo porque los botones son iguales.

### Conceptos para entender la pantalla

- **Hecho.** Registro del evento que se analizará, por ejemplo una línea de pedido o una línea de factura.

- **Granularidad o grano.** Qué representa exactamente una fila del hecho. Decir una línea de factura permite comprobar qué se conserva y evita llamar factura a cada línea.

- **Dimensión.** Información que permite agrupar y describir el hecho: fecha, producto, cliente o territorio. Una clave identifica; un nombre ayuda a interpretar.

- **Medida.** Valor asociado al hecho, como cantidad, importe de línea o identificador del documento que se contará de forma distinta.

- **Indicador.** Cálculo con una finalidad comercial: total de unidades, facturas distintas o importe por factura. Debe tener fórmula, unidad, alcance y procedencia.

- **Agregación.** Forma de resumir varias filas. Sumar, contar y promediar responden preguntas distintas.

- **Procedencia.** Cadena que identifica fuente, instantánea de metadatos, propuesta, ejecución y relaciones empleadas.

### Campos y botones

- **Fuente en contexto.** Base elegida para trabajar. Debe coincidir con la necesidad, los metadatos y el resultado consultado.

- **Dominio Ventas.** Perfil funcional implementado. No convierte automáticamente en ventas todas las tablas de la base.

### Paso a paso

1. Escriba una decisión concreta, por ejemplo priorizar productos según unidades registradas cada mes. Resultado: Una necesidad que se puede contrastar con datos, sin pedir todavía una conclusión causal.

2. Precise el evento: pedido o factura, y la fila mínima que desea conservar. Resultado: Un grano explícito, como una línea de pedido.

3. Anote los indicadores y sus unidades. Resultado: Por ejemplo importe, unidades, pedidos distintos e importe por pedido, sin confundirlos.

4. Identifique la fuente y revise su esquema antes de generar la propuesta. Resultado: Tablas y relaciones de esa base, sin suponer que tener un nombre parecido demuestra el significado.

### Qué hace la IA

En esta preparación la persona define el propósito. La IA podrá sugerir una redacción y un diseño, pero todavía no existe evidencia de que una propuesta haya sido aprobada o cargada.

### Qué comprueba la plataforma

Los controles posteriores comprobarán referencias, relaciones y recetas. La disponibilidad de una columna no demuestra por sí sola calidad, vigencia histórica o suficiencia de registros.

### Qué decide la persona

El analista decide el evento y los significados; la gerencia aporta la decisión comercial que desea apoyar.

### Si aparece un problema

- **El objetivo dice analizar todas las ventas para mejorar el negocio.** Acótelo: indique evento, indicador, comparación y límite. Evite pedir que el sistema demuestre por adelantado un aumento de ventas.

### Ejercicio y respuesta

Con un pedido que tiene tres líneas, indique cuántas filas de hecho y cuántos pedidos distintos habría.

Tres filas a grano de línea y un pedido distinto. Contar filas no da el número de pedidos.

### Compruebe lo que aprendió

**¿Un gráfico de importe prueba rentabilidad?**
No. Harían falta costos comparables y una definición de margen, entre otros datos.

**¿Una base nueva exige programar un tablero específico con su nombre?**
El recorrido es común; primero se configuran y comprueban sus metadatos y decisiones. La compatibilidad real requiere los adaptadores y operaciones implementados.

## Asistente paso 1 escribir o elegir una necesidad

**Objetivo.** Completar el objetivo, las preguntas, la periodicidad y la autorización de metadatos sin perder el propósito comercial.

Entre a Asistente de datamart con la fuente correcta y seleccione el dominio de ventas. El recorrido tiene cinco etapas: Necesidad, Conceptos, Propuesta, Personalización y Revisión.

Puede comenzar con su propio texto o pedir sugerencias con la estructura de la fuente. Las sugerencias no sustituyen el objetivo automáticamente: primero se leen su explicación, evidencia y límites; después se pulsa Usar esta necesidad.

### Conceptos para entender la pantalla

- **Objetivo del análisis.** Describe qué necesita conocer la persona. Debe conservar el evento y las limitaciones que importan al negocio.

- **Preguntas de negocio.** Orientaciones del catálogo de esta fuente. Seleccionarlas no fija por sí solo tablas, dimensiones ni fórmulas.

- **Periodicidad.** Forma temporal de resumir o presentar el análisis. Elegir Mensual no significa programar una recarga automática cada mes ni reducir el hecho necesariamente a una fila mensual.

### Campos y botones

- **Objetivo del análisis.** Texto de 20 a 2.000 caracteres. Escriba qué comparar, indicadores, grano y límites. No escriba SQL.

- **Destino.** Identifica el proveedor/configuración que recibirá la necesidad y los metadatos autorizados.

- **Autorizo enviar estos metadatos y la necesidad al proveedor indicado para esta revisión.** Habilita la asistencia para ese destino. Si cambia el proveedor se debe revisar de nuevo el consentimiento.

- **Preguntas de negocio disponibles.** Casillas con etiqueta y explicación. Una pregunta no disponible no se convierte en viable por forzar su selección.

- **Periodicidad.** Seleccione una opción disponible del catálogo, por ejemplo Mensual.

- **Sugerir necesidades con esta fuente.** Solicita posibles objetivos desde los metadatos; no necesita que ya haya una propuesta.

- **Ayúdame a formular la necesidad.** Propone una redacción a partir del objetivo y preguntas existentes. Requiere un objetivo suficiente y preguntas seleccionadas.

- **Usar esta redacción / Mantener mi redacción.** Permite aceptar la propuesta textual o conservar el texto propio.

### Paso a paso

1. Compruebe nombre de fuente e instantánea visibles antes de redactar. Resultado: El objetivo quedará asociado a esa estructura, no a otra base.

2. Seleccione preguntas que respondan a la decisión, sin marcar todo por costumbre. Resultado: Alcance entendible y coherente con el catálogo de esta fuente.

3. Elija periodicidad y autorice el destino que aparece en pantalla. Resultado: Asistencia habilitada para el proveedor indicado.

4. Escriba la necesidad o pulse Sugerir necesidades con esta fuente. Resultado: Texto propio o varias opciones con fundamento y limitaciones.

5. Si usa Ayúdame a formular la necesidad, compare la propuesta con el original. Resultado: La redacción conserva el evento, indicadores y límites; no añade pronósticos ni otra fuente.

6. Use sólo el texto que represente su necesidad y compruebe su viabilidad. Resultado: La plataforma inicia una revisión previa; todavía no se aprueba ni se ejecuta ETL.

### Qué hace la IA

Sugiere objetivos y mejora redacciones con el contexto estructural autorizado. Su respuesta pasa controles de formato y de referencias antes de ofrecerse como utilizable.

### Qué comprueba la plataforma

Existencia de instantánea, catálogo y proveedor utilizables; longitud y selección requeridas; destino del consentimiento; referencias y semántica admitida en la revisión de necesidad. Cambiar objetivo, preguntas o periodicidad invalida la revisión anterior.

### Qué decide la persona

El analista elige si usa una sugerencia y confirma que el texto representa la necesidad. Autorizar metadatos no equivale a aprobar el diseño ni la carga.

### Si aparece un problema

- **No se habilita el botón de asistencia.** Revise permiso de generación, proveedor activo y probado, autorización, instantánea y los campos requeridos.

- **La IA cambió el evento o añadió costos no solicitados.** Mantenga su texto o corríjalo antes de continuar; no acepte una ampliación sólo por estar bien redactada.

- **No aparecen sugerencias utilizables.** Lea el aviso, redacte un alcance más sencillo y compruebe la viabilidad; no se inventan datos faltantes.

### Ejercicio y respuesta

Redacte dos versiones del mismo objetivo: una vaga y otra que precise evento, grano, indicador y comparación.

La segunda debe permitir reconocer qué salida se revisará; por ejemplo unidades por producto y mes conservando cada línea de pedido.

### Compruebe lo que aprendió

**¿Usar esta necesidad ejecuta una carga?**
No. Sólo coloca el texto elegido; se revisan preguntas y viabilidad antes de generar.

**¿Mensual programa el ETL?**
No. Es periodicidad analítica; el inicio de la carga sigue siendo una acción explícita.

## Comprender la viabilidad antes de generar

**Objetivo.** Interpretar directo, derivable, ambiguo y no disponible sin confundir la estructura con datos ya comprobados.

La revisión actual combina un análisis de la IA con reglas de la plataforma. Su objetivo es relacionar la necesidad con nombres, tipos, claves y relaciones de la instantánea. No consulta todas las filas del negocio para demostrar resultados.

Una derivación inequívoca puede resolverse al construir la propuesta mediante una ruta declarada o una fórmula controlada. Una interpretación candidata de IA sigue pendiente de validación: su frase no se ejecuta como fórmula libre.

### Conceptos para entender la pantalla

- **Directo.** Existe una referencia estructural adecuada comprobada para el requisito.

- **Derivable por relación.** El requisito puede obtenerse recorriendo vínculos verificados sin cambiar indebidamente el grano.

- **Derivable por fórmula.** Puede calcularse con entradas compatibles y una operación permitida, por ejemplo precio × tasa de descuento × cantidad.

- **Ambiguo.** Existen opciones o significados que requieren una definición del analista; una relación válida no basta para decidir su rol comercial.

- **No disponible.** La revisión no encuentra respaldo suficiente para esa capacidad dentro del alcance actual.

- **Limitación aceptada.** Constancia de que se entiende una ausencia; no crea una fuente ni demuestra que el requisito se cumpla.

### Campos y botones

- **Viabilidad contra los metadatos.** Resumen de requisitos y evidencia. Lea cada tarjeta además del total de estados.

- **Ver evidencia técnica.** Muestra las referencias/rutas que sustentan el requisito.

- **Fórmula controlada.** Receta propuesta por las reglas con entradas identificadas.

- **Interpretación propuesta por IA no ejecutable.** Descripción que todavía debe convertirse y validarse en un contrato permitido.

- **Comprendo esta limitación y acepto continuar sin que el sistema invente una solución.** Aceptación individual de requisitos ambiguos o ausentes; no debe marcarse sin leer.

- **Generar conceptos y propuesta.** Usa la revisión vigente y las limitaciones expresamente aceptadas para generar una propuesta.

### Paso a paso

1. Lea el resumen de viabilidad y abra la evidencia de cada requisito importante. Resultado: Identifica qué está respaldado y qué requiere una decisión.

2. En las derivaciones, compruebe si se trata de relación o fórmula y qué entradas usa. Resultado: No se pide completar SQL ni buscar una columna sólo para quitar el aviso.

3. Si un requisito imprescindible es ambiguo o ausente, vuelva a la necesidad y aclárelo. Resultado: El objetivo no promete una salida imposible.

4. Acepte sólo limitaciones que permitan todavía responder la pregunta útil del caso. Resultado: Queda un alcance válido y las ausencias no se ocultan.

5. Genere y después revise De la necesidad al datamart. Resultado: Cada requisito debe aparecer cubierto, resuelto, limitado o pendiente, sin descarte silencioso.

### Qué hace la IA

Examina la necesidad dentro del contexto de la fuente y aporta requisitos y explicaciones. La respuesta se combina con el análisis estructural y los controles de referencias.

### Qué comprueba la plataforma

Referencias, relaciones, semántica admitida, alcance del evento y huella de entrada. La aprobación posterior vuelve a comprobar el contrato; aceptar una limitación no omite los controles bloqueantes.

### Qué decide la persona

El analista aclara ambigüedades, reduce alcance cuando corresponde y decide qué limitaciones son aceptables.

### Si aparece un problema

- **La necesidad tiene respaldo estructural y luego falla la propuesta.** Son controles distintos. La viabilidad no garantiza que el proveedor entregue un contrato válido; revise el error y reintente o ajuste el diseño.

- **El sistema pide validar otra vez.** Compruebe si cambió el objetivo, periodicidad, preguntas, fuente o destino del proveedor; una aceptación anterior no debe reutilizarse a ciegas.

- **Una casilla de limitación parece desbloquear todo.** El botón puede permitir continuar con un alcance parcial, pero no fabrica la capacidad ausente ni habilita SQL libre.

### Ejercicio y respuesta

Explique qué haría si se pide margen y sólo se encuentra importe de venta.

No afirmar margen; comprobar si hay costo comparable verificable, aclarar el alcance o aceptar que esa salida no estará disponible.

### Compruebe lo que aprendió

**¿Derivable significa que la alumna debe escribir una fórmula SQL?**
No. Las rutas/fórmulas inequívocas se resuelven mediante operaciones controladas. Una ambigüedad se decide con evidencia.

**¿Viabilidad demuestra que todas las filas están bien?**
No. Acredita respaldo estructural; la carga y conciliación revisarán datos concretos.

## Asistente paso 2 revisar los conceptos

**Objetivo.** Seleccionar conceptos a partir de evidencia y usar el copiloto como apoyo a una decisión explícita.

La pantalla Conceptos encontrados traduce la necesidad en conceptos vinculados a referencias técnicas. La confianza alta no reemplaza revisar qué tabla representa el evento. Los conceptos con evidencia débil pueden quedar excluidos preventivamente.

El copiloto de conceptos es distinto del chat del tablero: aquí explica la conveniencia de incluir una entidad en el diseño, no analiza todavía los importes cargados.

### Conceptos para entender la pantalla

- **Concepto de negocio.** Idea que la persona reconoce, como producto, cliente o territorio, asociada a columnas o tablas verificables.

- **Confianza.** Orientación de revisión; no es una medición de precisión universal del LLM.

- **Inclusión excepcional.** Decisión consciente de incluir un concepto cuya evidencia exige atención. Después debe superar la nueva validación.

### Campos y botones

- **Incluir.** Casilla que conserva o excluye el concepto de la siguiente propuesta.

- **Ver evidencia y cómo resolver.** Expone origen técnico, comprobaciones y orientación.

- **Confirmar inclusión excepcional.** Se usa si el concepto con evidencia débil se mantiene incluido; no inventa una relación.

- **Consultar al copiloto.** Abre conversación del concepto con objetivo, referencias y expediente.

- **Pregunta para el copiloto.** Entre 10 y 500 caracteres. Pregunte qué significa la relación o qué riesgo tiene incluirla.

- **Aplicar recomendación.** Cambia la selección según la recomendación de incluir/excluir; exige una acción de la persona.

- **Generar propuesta BI.** Continúa con la selección; si cambia el alcance de conceptos puede generar otra versión con IA.

### Paso a paso

1. Lea nombre, descripción, confianza y estado de cada tarjeta. Resultado: Identifica por qué una entidad está incluida o excluida.

2. Abra la evidencia de los conceptos con revisión requerida. Resultado: Relaciona el nombre comercial con las referencias reales.

3. Pregunte al copiloto por riesgos, claves y consecuencias si aún no puede justificar la selección. Resultado: Obtiene una explicación contextual con evidencia citada.

4. Excluya lo que no responda al objetivo o confirme expresamente una inclusión excepcional sustentada. Resultado: No quedan decisiones pendientes de inclusión.

5. Pulse Generar propuesta BI. Resultado: Se obtiene el contrato para revisar; se conserva trazabilidad si se generó otra versión.

### Qué hace la IA

Explica riesgo, consecuencias de incluir/excluir y recomendación. La conversación no modifica selecciones por sí sola.

### Qué comprueba la plataforma

Las referencias y el contrato resultante vuelven a validarse. No se permite continuar sin conceptos ni con decisiones de inclusión pendientes.

### Qué decide la persona

El analista decide la selección y aplica o rechaza la recomendación.

### Si aparece un problema

- **La IA recomienda incluir pero la evidencia no demuestra la relación.** No aplique la recomendación sólo por su tono. Excluya o defina el negocio y revise una nueva propuesta.

- **Quedan conceptos por confirmar.** Confirme únicamente los que entiende y puede sostener, o desmárquelos para continuar con un alcance menor.

### Ejercicio y respuesta

Pregunte: ¿qué riesgo tendría incluir este concepto en el datamart? Registre una evidencia y una decisión.

La decisión debe relacionar el concepto con la necesidad; la recomendación de IA no equivale a aprobación.

### Compruebe lo que aprendió

**¿Consultar al copiloto carga datos?**
No. Esta conversación usa el expediente y metadatos del diseño; no ejecuta el ETL.

**¿Excluir un concepto elimina información del origen?**
No. Lo retira del alcance de la propuesta.

## Asistente paso 3 leer el diseño propuesto

**Objetivo.** Explicar grano, hecho, medidas, dimensiones, indicadores y cobertura antes de personalizar o aprobar.

La propuesta es un contrato de diseño que responde a la necesidad. Empiece por el grano y el evento; después revise medidas y relaciones.

Una propuesta puede tener más indicadores que los cuatro de una práctica. La cantidad depende de la generación. Revise cuáles responden al objetivo y no memorice una cantidad universal de tarjetas.

### Conceptos para entender la pantalla

- **Clave del grano.** Columna o combinación que identifica la fila mínima. En una fuente puede ser una clave simple y en otra una combinación.

- **Proveniencia de una medida.** Referencias y fórmula que explican de dónde sale el valor.

- **Identidad descriptiva.** Nombre reconocible de la entidad y su tipo cuando corresponde. No basta mostrar sólo una clave técnica.

- **Cobertura.** Correspondencia entre cada requisito del objetivo y las salidas que realmente incluye el contrato.

### Campos y botones

- **Granularidad y Clave del grano.** Qué conserva el hecho; no confundir periodicidad mensual con grano físico de línea.

- **Hecho y medidas.** Para cada medida se muestran nombre, agregación, origen y fórmula.

- **Dimensiones y Columnas de origen.** Atributos con los que se describirán y agruparán los hechos.

- **Campos que creará el ETL.** Nombres/tipos descriptivos derivados por rutas verificadas; no son columnas que ya existan necesariamente en la fuente.

- **KPIs propuestos.** Funciones analíticas planteadas; compare su significado con medida y denominador.

- **De la necesidad al datamart.** Muestra cobertura directa, resolución automática, limitación aceptada o decisión pendiente.

- **Comprobar nombres y cobertura.** Con permiso apropiado realiza una muestra controlada de la fuente para revisar identidad descriptiva. La muestra permanece en la plataforma y no se envía al LLM.

- **Plan ETL declarativo.** Explica operaciones permitidas; esta vista no ejecuta la carga.

- **Ajustes automáticos / Validaciones y advertencias.** Lea qué se corrigió y qué sigue exigiendo revisión.

- **Detalles técnicos y trazabilidad.** Instantánea, huella, proveedor/modelo y observaciones originales. Una observación del proveedor no es una comprobación de la plataforma.

### Paso a paso

1. Lea resumen y explicación de negocio. Resultado: El evento coincide con lo solicitado.

2. Compruebe grano y claves. Resultado: Puede explicar qué representa una fila y cómo se identifica.

3. Compare cada medida con origen y fórmula. Resultado: Una tasa no está presentada como dinero ni un promedio de línea como promedio por pedido.

4. Revise dimensiones, rutas e identidad descriptiva. Resultado: Cliente y territorio representan el rol solicitado, con nombre y origen claros.

5. Lea la cobertura requisito por requisito. Resultado: No se promete una salida omitida.

6. Revise el plan, ajustes y errores/advertencias. Resultado: Cero errores bloqueantes antes de aprobar; los avisos se entienden.

7. Elija Personalizar propuesta o Continuar a revisión. Resultado: Pasa a una decisión humana sustentada.

### Qué hace la IA

Propone el modelo y una explicación. Las decisiones originales se conservan para trazabilidad aunque el contrato validado haya aplicado correcciones.

### Qué comprueba la plataforma

Existencia de tablas/columnas, tipos, claves, rutas de relación, coherencia del contrato y operaciones calculables; cobertura de requisitos y reglas semánticas implementadas.

### Qué decide la persona

El analista decide si el modelo representa el evento comercial y si necesita ajustes.

### Si aparece un problema

- **Aparecen compras u otro evento en una necesidad de ventas.** No apruebe por tener referencias existentes. Revise alcance y genere una versión que corresponda al evento.

- **Hay nombres como Cliente 123 en lugar de identidad comprobada.** Revise nombres y cobertura con el permiso necesario; no dé por demostrada una entidad descriptiva sólo por su clave.

- **Error bloqueante en una fórmula.** Abra Personalización y excluya o reasigne una receta compatible; si faltan entradas, genere una propuesta nueva con alcance sustentado.

### Ejercicio y respuesta

Explique al jurado una medida sin leer sólo su nombre: indique origen, operación, unidad y grano.

Por ejemplo importe registrado de línea, sumado sobre líneas de pedido; no denominarlo cobro ni utilidad.

### Compruebe lo que aprendió

**¿Todos los campos mostrados ya existen en el origen?**
No. Algunos son campos descriptivos que el ETL creará a partir de relaciones verificadas.

**¿Comprobar nombres y cobertura envía nombres de clientes al LLM?**
La muestra controlada permanece en la plataforma según la interfaz; no se remite al modelo para esa comprobación.

## Asistente paso 4 ajustar medidas y relaciones con criterio

**Objetivo.** Crear una versión corregida sin inventar estructuras ni perder las decisiones anteriores.

Personalizar crea una versión nueva. El contrato original conserva su historia. Compare siempre la regla del contrato actual con la regla del borrador: marcar algo en el borrador todavía no lo vuelve ejecutable.

Hay dos acciones de guardado diferentes. Guardar como nueva versión aplica los ajustes generales; Crear versión con relación corregida registra la decisión guiada de relación de manera independiente. Guarde y revise cada resultado antes de encadenar otra corrección.

### Conceptos para entender la pantalla

- **Suma.** Combina importes o unidades aditivos del mismo significado y alcance.

- **Conteo.** Cuenta valores no nulos de la columna seleccionada. A grano de línea no equivale automáticamente a documentos.

- **Conteo distinto.** Cuenta una vez cada identificador distinto. Un pedido con varias líneas se cuenta una vez en el universo consultado.

- **Promedio.** Media de los valores de las filas; AVG de importe de línea mide importe medio por línea, no por pedido.

- **Mínimo y máximo.** Extremos de los valores del campo. La línea de mayor importe no identifica necesariamente al producto con mayor suma de ventas.

- **Relación muchos a uno.** Varias filas del hecho apuntan a una fila única de dimensión; la unicidad ayuda a conservar el detalle.

- **Rol de una relación.** Significado del vínculo. Comprador y destinatario de facturación pueden ser clientes válidos, pero responden preguntas diferentes.

### Campos y botones

- **Resumen de negocio.** Hasta 160 caracteres; describe el ajuste sin alterar lo que las fuentes pueden demostrar.

- **Granularidad propuesta.** Hasta 240 caracteres; el texto debe corresponder a claves y hechos reales, no basta renombrar el grano.

- **Dimensiones incluidas / Medidas incluidas.** Conserve al menos las necesarias para la pregunta y sus dependencias.

- **Agregación.** Suma, Conteo, Conteo distinto, Promedio, Mínimo o Máximo según el significado.

- **Definir cálculo controlado.** Permite operaciones sumar, multiplicar, restar o dividir sobre columnas numéricas disponibles.

- **Primer valor / Segundo valor.** En resta y división el orden cambia el resultado; no intercambie costo e importe o cantidad y precio.

- **Factores o componentes en orden.** Para suma/multiplicación se seleccionan entradas permitidas; el editor limita la cantidad y el servidor comprueba tipos y referencias.

- **KPIs incluidos y medida asociada.** La asociación requiere una medida de función semántica compatible y las entradas de la receta.

- **Dimensión que desea corregir / Ruta de relación comprobada.** Permite elegir entre vínculos existentes. Las opciones bloqueadas explican riesgo de duplicación, tipos o unicidad.

- **Justificación de esta corrección / Justificación del ajuste.** Entre 10 y 500 caracteres. Explique el concepto de negocio y por qué corresponde, no escriba sólo porque funciona.

### Paso a paso

1. Abra Personalizar propuesta y anote qué problema concreto va a corregir. Resultado: Ajuste motivado por la necesidad, no por conseguir una luz verde.

2. Revise cada origen y agregación; marque o desmarque dimensiones, medidas e indicadores. Resultado: El borrador mantiene las dependencias necesarias.

3. Si corrige un cálculo, seleccione sólo entradas comprobadas y respete el orden. Resultado: Fórmula legible y controlada, sin SQL libre.

4. Para una ruta ambigua elija dimensión, vínculo y justificación. Resultado: La evidencia muestra tipos, cardinalidad, destino único y riesgo.

5. Pulse Crear versión con relación corregida cuando corresponda y revise la nueva versión antes de otro ajuste. Resultado: La corrección queda registrada; una decisión intermedia puede precisar una ruta sin cambiar la entidad final.

6. Para ajustes generales complete Justificación del ajuste y pulse Guardar como nueva versión. Resultado: Una versión derivada pasa de nuevo las reglas; la fuente y la versión original no se reescriben.

7. Revise cobertura, rutas y errores del resultado y vuelva a Revisión. Resultado: Sólo se aprueba una versión corregida comprobada.

### Qué hace la IA

Puede haber propuesto las opciones iniciales; el ajuste general y la elección de relaciones son decisiones del analista sujetas a validadores. No hace falta pedir a la IA SQL para modificar la estructura.

### Qué comprueba la plataforma

Tablas/columnas y tipos, número de entradas, dependencias de KPI, función semántica, clave destino única y conservación del grano; una relación contradictoria o multiplicadora se bloquea.

### Qué decide la persona

La persona elige inclusiones, operaciones y roles comerciales, y justifica por escrito la corrección.

### Si aparece un problema

- **Al retirar una medida desaparece un KPI.** Revise sus dependencias; no es pérdida de datos del origen. Restituya una medida compatible o acepte excluir el KPI.

- **El vínculo es válido pero representa facturación en lugar de comprador.** Use la decisión guiada y justifique el rol; que coincidan las filas no demuestra que el rol comercial sea correcto.

- **La nueva versión está bloqueada.** Lea el motivo; cancele o ajuste el borrador. No cambie reglas ni huellas a mano para forzar la aprobación.

### Ejercicio y respuesta

Un documento tiene líneas de 100 y 50 y otro una línea de 90. Calcule promedio por línea y por documento.

Importe total 240; tres líneas: 80 por línea; dos documentos distintos: 120 por documento. Son indicadores diferentes.

### Compruebe lo que aprendió

**¿Editar el texto de granularidad cambia por sí solo las claves?**
No. El contrato debe conservar una estructura compatible y superar validación.

**¿Una relación uno a muchos desde el hecho es segura por existir?**
No necesariamente: puede multiplicar líneas e importes. Revise dirección, unicidad y motivo de bloqueo.

## Asistente paso 5 aprobar y consultar versiones

**Objetivo.** Distinguir validación técnica, aprobación humana, retiro de aprobación y consulta histórica.

La aprobación es una decisión sobre una versión concreta. La plataforma vuelve a ejecutar sus reglas y registra responsable, fecha y comentario. No crea tablas ni carga datos al pulsar Aprobar propuesta.

Consultar una versión o Verificar evidencia no debe retirar su aprobación por sí solo. Una diferencia de reconstrucción causada por el motor puede quedar como advertencia de compatibilidad; su efecto sobre nuevas cargas se comprueba por separado.

### Conceptos para entender la pantalla

- **Lista para revisión.** Contrato que puede recibir decisión humana si conserva las condiciones requeridas.

- **Aprobada.** Versión con decisión humana registrada; su aptitud para otra carga también depende de las reglas actuales y la fuente.

- **Retirada.** Aprobación retirada expresamente para impedir nuevas ejecuciones; no borra datamarts ya generados.

- **Descartada.** Fuera de las listas operativas; se conservan auditoría y trazabilidad.

- **Huella.** Resumen de contenido usado para detectar cambios. No se corrige editando el valor para que coincida.

### Campos y botones

- **Comentario de revisión.** Hasta 500 caracteres. Para rechazar se exige un motivo suficiente, al menos 10 caracteres en la interfaz.

- **Leí y comprendí las advertencias y las acciones indicadas.** Aceptación requerida si hay avisos. Cero errores no significa cero aspectos que revisar.

- **Aprobar propuesta / Rechazar propuesta.** Decisión humana distinta de la ejecución física.

- **Verificar evidencia.** Comprueba instantánea, referencias, contrato y reproducción sin llamar al modelo, sin consultar filas y sin ETL.

- **Mostrar en Versiones generadas.** Filtra el historial; no cambia el estado de las versiones.

- **Abrir resultado.** Recupera la versión guardada sin volver a generar con IA.

- **Crear versión corregida desde ésta.** Permite derivar una corrección conservando la original.

- **Retirar aprobación / Descartar versión.** Acciones explícitas con motivo; no se usan para limpiar un aviso sin entenderlo.

- **Restaurar aprobación.** Disponible en los estados y permisos apropiados; exige justificación, advertencias revisadas y revalidación.

### Paso a paso

1. Lea necesidad, fuente, dominio e instantánea en Revisión. Resultado: Está decidiendo sobre la versión correcta.

2. Confirme cero errores y comprenda cada advertencia. Resultado: Puede explicar qué está comprobado y qué límite conserva.

3. Escriba comentario y apruebe si corresponde; rechace con motivo si no cumple. Resultado: Comprobante de estado, responsable y fecha.

4. Abra después el historial y consulte la misma versión. Resultado: Se puede recorrer el diseño en modo de lectura sin regenerarlo.

5. Si se necesita corregir, cree una derivada y revise su aprobación aparte. Resultado: No cambia silenciosamente la evidencia del caso anterior.

### Qué hace la IA

La IA no aprueba. Verificar evidencia es una comprobación determinística, no una nueva opinión del proveedor.

### Qué comprueba la plataforma

Permisos, estado y reglas de aprobación vigentes; integridad de instantánea y contrato. Los errores bloqueantes no se resuelven marcando el aviso de advertencias.

### Qué decide la persona

Una persona autorizada aprueba/rechaza o retira/restaura con un motivo.

### Si aparece un problema

- **No ve una versión en el filtro actual.** Cambie Mostrar al estado correspondiente y compruebe la fuente. No suponga que se eliminó.

- **La propuesta aprobada no aparece habilitada para una nueva carga.** Consulte motivos en Datamart de ventas. Puede ser histórica o incompatible para otra ejecución aunque sus resultados anteriores sigan disponibles.

- **Verificar evidencia muestra compatibilidad.** Lea la explicación y distinga el registro histórico de la aptitud actual. No retire aprobación sin una decisión deliberada.

### Ejercicio y respuesta

Explique la diferencia entre aprobar propuesta, preparar materialización y materializar.

Aprobar acepta un diseño; preparar fija selección y huellas; materializar lee la fuente y crea/carga el destino.

### Compruebe lo que aprendió

**¿Una aprobada puede ser consultable pero no apta para otra carga?**
Sí. Se conserva historia, pero nuevas ejecuciones deben superar las reglas actuales.

**¿Abrir resultado vuelve a consumir una generación IA?**
No. Recupera una versión persistida.

## Materialización paso 1 elegir una propuesta

**Objetivo.** Escoger un contrato aprobado entendiendo qué puede ejecutarse y qué debe abrirse como histórico.

Entre a Datamart de ventas con la fuente que corresponde. El proceso muestra cinco pasos: Elegir propuesta, Revisar indicadores, Confirmar ejecución, Materializar y cargar, y Validar resultados.

La propuesta recomendada es una ayuda para elegir entre candidatas compatibles. No ejecuta nada automáticamente. Si el mismo contrato y selección ya tienen expediente, se debe abrir ese expediente en lugar de repetir la carga.

### Conceptos para entender la pantalla

- **Propuesta elegible.** Conserva aprobación, metadatos, fuente habilitada y probada, contrato compatible e indicadores calculables.

- **Expediente.** Registro de una preparación o ejecución, con selección, huellas, plan, responsable y resultados.

- **Consulta histórica.** Lectura de lo ocurrido en una ejecución anterior; no es una prueba nueva ni una recarga.

### Campos y botones

- **Tarjeta de versión.** Resumen, necesidad, grano, cantidad de KPI y fecha de aprobación.

- **Seleccionar.** Elige el contrato del recorrido actual.

- **Comparar.** Permite contrastar hasta dos propuestas por grano, medidas e indicadores.

- **Versiones anteriores no habilitadas para una nueva carga.** Explica bloqueos; no significa que se hayan borrado sus datos.

- **Abrir expediente.** Recupera una ejecución previa sin repetir el ETL.

- **Revisar indicadores.** Avanza con la propuesta seleccionada.

### Paso a paso

1. Compruebe la fuente antes de leer las tarjetas. Resultado: No mezcla contratos de otra base.

2. Compare necesidad y grano con su ficha de análisis. Resultado: Selecciona un modelo adecuado, no sólo la versión de número mayor.

3. Use Comparar si existen dos alternativas relevantes. Resultado: Reconoce diferencias que afectan al significado comercial.

4. Si indica Ya ejecutada, abra el expediente para consultar la evidencia. Resultado: No produce otra carga idéntica accidental.

5. Si requiere una carga nueva y la candidata es compatible, pulse Revisar indicadores. Resultado: Continúa con la versión aprobada elegida.

### Qué hace la IA

Los indicadores fueron sugeridos en el diseño; esta selección no exige otra generación con IA.

### Qué comprueba la plataforma

Reglas de compilación actuales, aprobación, instantánea existente, fuente activa en lectura, recetas y preparación dimensional. Contratos históricos anteriores pueden quedar excluidos de nuevas ejecuciones.

### Qué decide la persona

La persona selecciona la versión y decide si consulta lo previo o necesita una derivada corregida.

### Si aparece un problema

- **No hay propuestas habilitadas.** Lea la lista de bloqueos; corrija o genere una propuesta actual. El historial puede seguir disponible.

- **Sólo se ve Abrir expediente.** Es la protección frente a repetición de contrato. Consulte el existente; no trate de borrar la ejecución para forzar otra.

### Ejercicio y respuesta

Elija dos propuestas y explique una diferencia de grano o indicador sin ejecutarlas.

La comparación tiene sentido si cambia la pregunta o su representación; el número de versión por sí solo no mide calidad.

### Compruebe lo que aprendió

**¿Recomendada equivale a aprobada automáticamente por la IA?**
No. Es una recomendación operativa entre contratos que conservan aprobación y compatibilidad.

**¿Histórico bloqueado equivale a datos eliminados?**
No. Puede consultarse el expediente conservado.

## Materialización paso 2 elegir indicadores y recetas

**Objetivo.** Seleccionar salidas calculables y explicar suma, diferencia, razón y participación.

En Revisar indicadores no se redactan fórmulas libres. Se decide cuáles de las recetas admitidas del contrato se necesitan para el objetivo. Debe quedar al menos una.

Desmarcar indicadores puede reducir la cobertura de la necesidad. La preparación registra si la selección es parcial. No presente un ejercicio de dos KPI como si hubiera materializado todos los requisitos de una necesidad avanzada.

### Conceptos para entender la pantalla

- **Agregación.** Suma, conteo, conteo distinto, promedio, mínimo o máximo de una medida comprobada.

- **Diferencia.** Resta entre dos entradas verificadas, por ejemplo importe menos costo comparable.

- **Razón.** Numerador dividido entre denominador. El importe por pedido usa importe total ÷ pedidos distintos del mismo alcance.

- **Participación.** Razón multiplicada por 100. Siempre se debe explicar el universo del denominador.

- **Promedio ponderado por unidad.** Total monetario ÷ total de unidades, distinto de promediar precios de filas sin ponderar.

- **Sin valor.** Una razón sin denominador válido no debe representarse como una división infinita ni como una venta cero demostrada.

### Campos y botones

- **Incluir indicador.** Conserva o retira una receta de esta ejecución.

- **Cálculo controlado.** Describe operación y entradas; compruebe el denominador y la unidad.

- **Unidad.** Unidades, documentos, porcentaje o moneda de origen; un código monetario necesita evidencia.

- **Período.** Hereda o precisa la periodicidad del contrato.

- **Ajuste de seguridad.** Por ejemplo una tasa presentada como dinero o un promedio de línea mal nombrado.

- **Ver trazabilidad técnica.** Entradas verificadas, versión de definición y unidad originalmente sugerida.

- **Revisar transformaciones.** Avanza con las recetas seleccionadas.

### Paso a paso

1. Lea nombre, descripción y cálculo de cada indicador. Resultado: Reconoce qué pregunta responde.

2. Compruebe que el conteo documental sea distinto y que la razón use ese conteo. Resultado: No confunde líneas con pedidos o facturas.

3. Seleccione las salidas necesarias y revise las que retira. Resultado: Queda al menos una receta y el alcance parcial se reconoce.

4. Lea las correcciones de nombre o unidad. Resultado: No denomina neto a precio × cantidad sin descontar una tasa ni promedio por pedido a AVG de línea.

5. Pulse Revisar transformaciones. Resultado: Continúa sin cambiar el contrato físico ni ejecutar todavía.

### Qué hace la IA

Propuso indicadores anteriormente; el cálculo lo controla el motor de recetas. La IA no calcula a mano el total que se publicará.

### Qué comprueba la plataforma

Operaciones soportadas y entradas comprobadas. Las diferencias, razones y participaciones requieren dos entradas válidas. La división con divisor cero conserva un resultado nulo/no calculable.

### Qué decide la persona

El analista selecciona qué indicadores quiere materializar y acepta conscientemente un alcance parcial cuando corresponda.

### Si aparece un problema

- **Un KPI no tiene medida compatible.** Vuelva al asistente para corregir o excluir; este paso no permite inventar la entrada.

- **La razón aparece Sin valor.** Revise denominador y universo. No reemplace el resultado por cero para ocultar una división no definida.

- **Las facturas por producto no suman las facturas globales.** El conteo distinto no es aditivo: una factura puede contener varios productos.

### Ejercicio y respuesta

Tres líneas: pedido A 100 y 50; pedido B 90. Calcule total, conteo de líneas, pedidos distintos e importe por pedido.

240; 3; 2; 120. Sumar los pedidos distintos de grupos de producto puede contar el mismo pedido varias veces.

### Compruebe lo que aprendió

**¿Por qué 10 % y 40 % no se promedian siempre como 25 %?**
Si tienen distintos denominadores, hay que usar totales compatibles o ponderar; el promedio simple puede cambiar el significado.

**¿Cambiar la etiqueta corrige una receta incorrecta?**
No. Debe corresponder fórmula, medida y unidad, no sólo el texto.

## Materialización paso 3 confirmar el plan

**Objetivo.** Leer extracción, limpieza, transformación, carga y validación antes de fijar el expediente.

Esta pantalla permite explicar el proceso sin escribir SQL. Revise la tabla de hechos, el grano, las dimensiones y las medidas. Luego lea cada operación de la secuencia.

Las operaciones opcionales marcadas Revisar en el paso 5 preparan candidatos de etiquetas en español. No existe una lista para aprobar etiquetas aquí: esa revisión aparecerá después de la carga si hay candidatos.

### Conceptos para entender la pantalla

- **Extracción.** Lectura controlada de columnas del origen autorizado.

- **Limpieza y calidad.** Tratamiento previsto de claves, nulos, textos o duplicados según el plan; no es una promesa de corregir cualquier dato defectuoso.

- **Transformación.** Derivaciones y enriquecimientos permitidos que respetan la granularidad.

- **Clave sustituta.** Identificador interno de la dimensión analítica, separado de la clave comercial del origen.

- **Carga dimensional.** Creación y carga del hecho y dimensiones del destino de la ejecución.

- **Conciliación.** Contraste de cantidades e importes de origen y destino del mismo alcance.

### Campos y botones

- **Tabla de hechos / Granularidad / Dimensiones / Medidas.** Resumen del modelo que se va a materializar.

- **Etapas del plan.** Extracción, Limpieza y calidad, Transformación y enriquecimiento, Carga dimensional y Conciliación y evidencia.

- **Advertencias heredadas.** Avisos de la propuesta que siguen siendo relevantes para la carga.

- **Registro de decisión.** Comentario de 10 a 500 caracteres que explica la decisión sobre plan y KPI.

- **Confirmo el plan de ejecución.** Acepta el contrato y entiende que las etiquetas candidatas se revisarán después.

- **Preparar materialización.** Guarda selección, plan y huellas. No lee ni altera filas de la fuente en esta confirmación.

### Paso a paso

1. Compare el resumen con la propuesta aprobada. Resultado: Mismo evento y grano.

2. Lea las operaciones de cada etapa y advertencias. Resultado: Puede explicar qué se leerá y qué se calculará.

3. Compruebe que no se confunda una etiqueta en español con un valor original nuevo. Resultado: Entiende la política de conservar originales.

4. Escriba una decisión concreta y marque la confirmación. Resultado: Registro humano suficiente.

5. Pulse Preparar materialización una sola vez y anote el número de ejecución. Resultado: Expediente preparado con propuesta, instantánea, responsable y huellas; aún no hay nueva carga física.

### Qué hace la IA

No genera SQL libre en esta confirmación. La interpretación posterior de categorías puede usar IA bajo la política de valores aptos y revisión humana.

### Qué comprueba la plataforma

Permiso de escritura ETL, aprobación y compatibilidad actuales, recetas seleccionadas, cobertura y duplicidad de contrato/selección.

### Qué decide la persona

Una persona autorizada confirma el plan y la selección que quedará registrada.

### Si aparece un problema

- **La preparación informa que el contrato ya corresponde a otra ejecución.** Abra ese expediente; el conflicto evita repetir la carga idéntica.

- **El botón sigue deshabilitado.** Revise permiso, casilla de confirmación y longitud del comentario.

- **Faltan etiquetas para aprobar en esta pantalla.** Es normal: primero se materializa, después se revisan los candidatos en Validar resultados.

### Ejercicio y respuesta

Explique por qué preparar no significa que ya se pueda mostrar un nuevo tablero.

Se guardó el contrato; faltan lectura, carga, conciliación y condiciones de publicación.

### Compruebe lo que aprendió

**¿Qué se conserva al preparar?**
Selección de KPI, comentario, plan, huellas de propuesta e instantánea y responsable.

**¿Quién ejecuta la lectura?**
El materializador controlado después del inicio explícito del paso 4.

## Materialización paso 4 cargar sin repetir accidentalmente

**Objetivo.** Iniciar una carga entendiendo sus efectos y recuperar el expediente ante una interrupción.

Antes de pulsar Materializar y cargar datamart, compruebe fuente, propuesta y número de expediente. La operación leerá columnas aprobadas de la fuente y creará un destino analítico propio de esa ejecución.

El hecho y las dimensiones se cargan con controles transaccionales. Un fallo bloqueante no debe dejar un datamart parcial publicado ni sustituir los resultados anteriores. No pulse repetidamente el botón porque tarde la respuesta.

### Conceptos para entender la pantalla

- **Esquema por ejecución.** Espacio analítico identificado para separar resultados de distintas ejecuciones; la base de origen no se sobrescribe.

- **Transacción.** Conjunto de operaciones que se confirma completo o se revierte ante un fallo.

- **Preparada / En ejecución / Validada / Revisión pendiente / Fallida.** Estados del expediente que se deben leer antes de intentar otra acción.

### Campos y botones

- **Contrato preparado correctamente.** Confirma el registro previo; revise huellas y selección.

- **Materializar y cargar datamart.** Inicia extracción, transformación, creación y carga según el contrato validado.

- **Ver trazabilidad técnica.** Constructor, huellas, responsable y fecha.

- **Expedientes recientes.** Permite recuperar la ejecución para ver qué ocurrió, sin iniciar otra.

### Paso a paso

1. Lea el comprobante y confirme que sigue siendo el expediente esperado. Resultado: No carga un modelo de otra fuente o versión.

2. Pulse Materializar y cargar datamart una vez y mantenga la pantalla abierta. Resultado: Estado de procesamiento; no cambia la fuente a modo escritura.

3. Espere el resultado. Resultado: Avanza al paso 5 con validación, revisión pendiente o fallo.

4. Si se interrumpe el navegador, recupere sesión y abra el expediente antes de reintentar. Resultado: Reconoce si terminó, sigue preparada o falló; no crea cargas duplicadas por incertidumbre.

5. Registre identificadores y estado final. Resultado: Evidencia de una ejecución nueva o de una consulta histórica, claramente distinguidas.

### Qué hace la IA

El diseño puede proceder de IA, pero la lectura y carga se realizan con el materializador y operaciones permitidas. La IA no recibe autorización para ejecutar instrucciones SQL libres.

### Qué comprueba la plataforma

Contrato y fuente al ejecutar, trazabilidad, claves, relaciones exactas, tipos y condiciones de carga. El destino conserva el aislamiento por ejecución.

### Qué decide la persona

La persona inicia la materialización; si hay fallo investiga y prepara una corrección en lugar de alterar a mano el expediente.

### Si aparece un problema

- **Error de conexión o sesión vencida.** Vuelva a entrar y revise Expedientes recientes antes de reenviar. El servidor puede haber terminado aunque el navegador perdiera la respuesta.

- **Fallida y mensaje de reversión.** Revise conexión y contrato con el administrador; si cambió la estructura capture metadatos y genere la versión correcta. Conserve el estado fallido hasta resolver la causa y comprobar la nueva ejecución.

- **La etapa dice Materialización ya ejecutada.** Es consulta. Pase a Validar resultados; esa pantalla no vuelve a cargar por recorrer los pasos.

### Ejercicio y respuesta

Simule sólo en la bitácora la decisión ante una pantalla que no responde: ¿qué revisa antes de volver a pulsar?

Estado del expediente existente, fuente, propuesta y sesión. No ejecutar de nuevo sin conocer si la carga terminó.

### Compruebe lo que aprendió

**¿Se reemplaza AdventureWorks por el datamart?**
No. Se usa como fuente de lectura y el destino analítico queda separado.

**¿Abrir un paso histórico repite la lectura de origen?**
No. Permite consultar evidencia de la ejecución ya realizada.

## Materialización paso 5 revisar conciliación y calidad

**Objetivo.** Comprobar cantidades y valores y distinguir una conciliación numérica de una interpretación comercial correcta.

Una carga no se da por buena sólo por mostrar un mensaje verde. Lea Filas de origen, Filas cargadas, Diferencia, Tablas creadas y las métricas de cada tabla. Compare también indicadores y procedencia.

La conciliación de la ejecución contrasta filas y totales de medidas de origen/destino. Un resultado de diferencia cero demuestra consistencia de ese alcance; no demuestra por sí solo que se eligió el cliente, fecha o territorio comercial correctos.

### Conceptos para entender la pantalla

- **Duplicados controlados en dimensión.** Repeticiones agrupadas al conformar una dimensión. Muchas facturas del mismo día pueden producir una sola fila de fecha sin eliminar líneas del hecho.

- **Diferencia cero.** Coinciden los controles de ese universo. Hay que comprobar además evento, rutas, unidades y criterios comerciales.

- **Indicador conciliado.** Valor calculado a partir de entradas y recetas del expediente; un resultado no calculable debe revisarse por separado.

- **Revisión pendiente.** Puede significar diferencia de carga o interpretación semántica pendiente. Lea el motivo concreto, no sólo el color.

### Campos y botones

- **Conciliación OLTP–datamart.** Comprobante de filas, diferencias y medidas de la ejecución.

- **Calidad por tabla.** Filas de origen/carga y duplicados controlados; distinga hecho y dimensión.

- **Indicadores calculados.** Valores, unidad y estado. Algunos se muestran abreviados; el valor exacto y los reportes permiten contrastar decimales.

- **Interpretación semántica.** Estado y revisión de candidatos de etiquetas; se explica en la siguiente unidad.

- **Comprobar divisa sin repetir el ETL.** Acción aparte si falta evidencia del código monetario.

### Paso a paso

1. Revise que origen y destino correspondan al mismo expediente y grano. Resultado: No compara el filtro de un tablero con un total global de otro caso.

2. Compare filas y diferencia. Resultado: El hecho conserva el número esperado sin rechazo o multiplicación indebida.

3. Revise por tabla las agrupaciones de valores repetidos en las dimensiones. Resultado: Entiende por qué la fecha puede tener menos filas que documentos sin perder hechos.

4. Compare indicadores, unidades y razones con su fórmula. Resultado: No hay denominador cambiado o unidad inventada.

5. Revise rutas de cliente/territorio además de números. Resultado: Se conserva el rol comercial solicitado.

6. Si la conciliación y publicación cumplen, abra Analítica de ventas. Resultado: Tablero identificado con fuente, propuesta y ejecución correctas.

### Qué hace la IA

Puede apoyar etiquetas y explicar después resultados; el contraste numérico no se obtiene por opinión del modelo.

### Qué comprueba la plataforma

En el materializador actual la conciliación requiere cero filas rechazadas, mismo conteo origen/destino y diferencias de totales de medidas iguales a cero. La condición numérica no reemplaza la revisión semántica del analista.

### Qué decide la persona

La persona revisa métricas, procedencia y alcance antes de usar los resultados para una lectura comercial.

### Si aparece un problema

- **Hay diferencia de filas o importes.** No presente el tablero como verificado sin resolverla. Registre magnitud y alcance, revise claves/uniones/entradas y corrija el contrato.

- **Fecha muestra miles de duplicados controlados.** Compruebe si son días repetidos en documentos; en el caso WWI 22 se conservaron 1.069 días desde 70.510 documentos sin perder 228.265 líneas.

- **Los totales coinciden pero cambia California entre versiones.** Compare roles de comprador/facturación y ciudad de entrega/postal. Distinta clasificación puede explicar el cambio sin mezcla entre bases.

### Ejercicio y respuesta

Conserve 100 líneas de factura sobre 10 días. ¿Es obligatorio tener 100 filas en la dimensión fecha?

No. Puede haber 10 fechas únicas y 100 filas en el hecho; lo importante es que las claves y los controles expliquen esa conformación.

### Compruebe lo que aprendió

**¿Diferencia cero prueba que el territorio era históricamente el del cliente?**
No. Haría falta una historia de vigencias; el prototipo lee los atributos del estado disponible durante el ETL.

**¿Revisión pendiente siempre significa carga fallida?**
No. Puede haber conciliación correcta con etiquetas aún pendientes; lea el detalle.

## Revisar etiquetas en español y comprobar la moneda

**Objetivo.** Publicar sólo interpretaciones revisadas y conservar el significado original y la divisa demostrable.

La interpretación semántica añade etiquetas españolas a categorías aptas; conserva los valores originales. No traduce identificadores, nombres de personas, direcciones, texto libre ni categorías de alta cardinalidad.

La moneda es un control diferente. Un importe conciliado no autoriza a escribir USD. Si la fuente no demuestra un código único adecuado, el resultado correcto es moneda de origen. No confunda el país del cliente con la divisa del importe.

### Conceptos para entender la pantalla

- **Mapeo.** Correspondencia entre categoría original y etiqueta española revisada.

- **Publicación supervisada.** Las etiquetas sólo se publican después de la revisión individual y la confirmación humana.

- **Divisa comprobada.** Código respaldado por evidencia relacional de fuente/base; no elegido por el modelo por intuición.

### Campos y botones

- **Publicar.** Casilla por mapeo para conservarlo o excluirlo.

- **Etiqueta en español.** Texto editable, hasta 100 caracteres, que debe preservar el significado.

- **Comentario de revisión.** Entre 10 y 500 caracteres sobre la decisión tomada.

- **Confirmo que revisé los mapeos que se publicarán.** Confirmación distinta de la aprobación del diseño y de la preparación del ETL.

- **Publicar etiquetas revisadas.** Publica sólo los mapeos aceptados como columnas adicionales auditables.

- **Reintentar interpretación sin repetir el ETL.** Recupera una interpretación pendiente sin recargar el hecho.

- **Comprobar divisa sin repetir el ETL.** Consulta evidencia de moneda y actualiza su contexto sin otra materialización.

### Paso a paso

1. Lea el estado de Interpretación semántica. Resultado: Reconoce si no hay candidatos, están pendientes, requieren revisión o ya fueron publicados.

2. Compare cada original con la etiqueta, corrija lo necesario y excluya códigos que no convenga traducir. Resultado: No cambia el valor original ni acepta una etiqueta por rutina.

3. Escriba comentario, marque confirmación y publique. Resultado: Recibo con responsable, fecha y mapeos revisados.

4. Si está pendiente por proveedor, revise la configuración y use el reintento semántico. Resultado: No se repite el ETL para corregir sólo etiquetas.

5. Revise la divisa y compruébela si la acción está disponible. Resultado: Código verificado o moneda de origen con el límite conservado.

### Qué hace la IA

Propone etiquetas para categorías seguras dentro de la política implementada. No debería convertir códigos, nombres propios o información ausente en traducciones inventadas.

### Qué comprueba la plataforma

Aptitud de categorías, formato de mapeos, conservación del original y publicación autorizada. La comprobación de moneda usa evidencia de la fuente, no una respuesta libre del LLM.

### Qué decide la persona

El analista publica, corrige o excluye cada etiqueta y confirma la revisión. No elige una divisa sin evidencia para mejorar la apariencia.

### Si aparece un problema

- **No aparece ninguna etiqueta para aprobar.** Si no hay candidatos aptos no existe una tarea de publicación. No hay que fabricar un mapeo.

- **El proveedor falla después de una carga conciliada.** Reintente sólo interpretación; antes compruebe el expediente para conservar la carga existente.

- **WWI no demuestra USD.** Conserve moneda de origen. Cambiar el rótulo manualmente no convierte el dato en dólares.

### Ejercicio y respuesta

En el caso AW 21 se propusieron Europe, North America, Pacific y códigos AU, CA, DE, FR, GB, US. Explique la revisión documentada.

Se publicaron Europa, América del Norte y Pacífico; los seis códigos se excluyeron de traducción. Se conservaron originales.

### Compruebe lo que aprendió

**¿Publicar etiquetas altera los importes?**
No. Añade interpretación categórica auditada; no cambia las medidas originales.

**¿Siempre debe resolverse un código monetario?**
No. La ausencia de evidencia suficiente debe conservarse como límite.

## Elegir el datamart y filtrar el análisis

**Objetivo.** Leer los identificadores y usar filtros sin confundir vistas, bases ni universos.

Analítica de ventas consulta los datos físicos de una ejecución conciliada, no vuelve a extraer cada vez la base transaccional. Compruebe la fuente y los identificadores del encabezado antes de interpretar cifras.

Vista ejecutiva resume la información para gerencia. Vista analítica añade controles y tablas de respaldo. Cambiar de vista no otorga un rol nuevo ni añade datos que no se hayan materializado.

### Conceptos para entender la pantalla

- **Datamart analizado.** Ejecución concreta cuyos datos físicos se consultan; puede haber varios expedientes de la misma fuente.

- **Filtro.** Delimita las filas que participan en el cálculo. Año y territorio se combinan en el mismo alcance.

- **Indicador de los gráficos.** Métrica que explica las visualizaciones. No confundirla con todos los KPI del encabezado.

- **Última actualización.** Fecha de finalización del expediente o de su creación si no existe otra; no equivale a una recarga automática al abrir el panel.

### Campos y botones

- **Fuente en contexto.** Selecciona la base de trabajo. Cambiarla limpia ejecución, filtros y conversación y vuelve a pedir resultados de esa fuente.

- **Datamart analizado.** Combobox cuando hay más de una ejecución con datos físicos consultables. Si sólo hay una se muestra Datamart activo.

- **Vista ejecutiva / Vista analítica.** Presentación según necesidad de lectura. En la ejecutiva se omite el visual de clientes; en la analítica se muestran controles/datos adicionales.

- **Indicador de los gráficos.** En vista analítica lista agregaciones que admiten visualización segura. Las recetas derivadas pueden existir como KPI sin aparecer en ese selector.

- **Año / Territorio.** Opciones obtenidas del datamart disponible; no inventan años futuros.

- **Restablecer filtros.** Retira año y territorio; no cambia la fuente ni ejecuta otro ETL.

- **Consultar respaldo / Ver expediente técnico.** Abre la evidencia de la ejecución que respalda el panel.

### Paso a paso

1. Compruebe fuente, base, propuesta, ejecución, moneda y período en el encabezado. Resultado: Contexto correcto antes de leer tarjetas.

2. Seleccione el datamart deseado si hay varios. Resultado: Se reinician métrica y filtros para evitar arrastrar otro contexto.

3. Abra Vista analítica y elija el indicador de los gráficos. Resultado: Las gráficas representan la métrica elegida.

4. Seleccione año y territorio y espere Actualizando resultados. Resultado: KPI, gráficos y hallazgos se recalculan para ese alcance.

5. Compare un valor exacto de tabla con una tarjeta abreviada. Resultado: Comprende la diferencia de formato sin declarar un error de cálculo.

6. Use Restablecer filtros y vuelva a seleccionar la otra fuente cuando termine. Resultado: No quedan mezclados filtros ni conversación del caso anterior.

### Qué hace la IA

No hace falta una generación LLM para consultar o filtrar el panel. Los valores se calculan mediante recetas y consultas controladas.

### Qué comprueba la plataforma

Correspondencia de fuente y ejecución, disponibilidad física, recetas y filtros permitidos; el servidor comprueba procedencia además de los controles del navegador.

### Qué decide la persona

La persona elige el universo e interpreta los resultados dentro del evento materializado.

### Si aparece un problema

- **Primero complete el expediente del datamart.** No hay ejecución conciliada con datos físicos disponibles. Vuelva a Datamart de ventas y revise preparación, carga y validación.

- **Falta el combobox de datamart.** Puede ser correcto si sólo una ejecución tiene datos físicos; no se debe crear otra para obtener el selector.

- **Aparece un resultado anterior mientras carga el filtro.** Espere a que termine y confirme el contexto del encabezado antes de copiar cifras. Si persiste una fuente equivocada, registre incidencia.

- **El chat se vació tras cambiar año o fuente.** Es protección de contexto: la respuesta anterior no se reutiliza como si perteneciera a la nueva selección.

### Ejercicio y respuesta

Explique por qué los 109,8 millones globales de AW 21 no se comparan directamente con 6.015.174,74 del filtro 2013/Northwest.

Son universos diferentes. La comparación necesita la misma ejecución y filtros.

### Compruebe lo que aprendió

**¿Cambiar Año vuelve a cargar el origen?**
No. Recalcula sobre el datamart.

**¿Todas las recetas pueden graficarse por entidad?**
No. El selector ofrece las agregaciones que admiten visualización agrupada segura en la implementación.

## Leer gráficos y hallazgos con criterio comercial

**Objetivo.** Diferenciar tendencia, ranking y distribución y explicar sus denominadores y límites.

Una línea temporal compara períodos; las barras ordenan entidades; una distribución muestra participaciones. Antes de decir que un producto es el mejor, precise si lo ordenó por importe o unidades y qué filtros utilizó.

Los hallazgos del panel se construyen con reglas sobre los resultados visibles. Aunque la pantalla los llame Copiloto analítico, no todos sus textos proceden de una nueva llamada LLM. La conversación inferior sí utiliza el proveedor de IA.

### Conceptos para entender la pantalla

- **Top o ranking.** Lista limitada de entidades ordenadas por un indicador. El máximo de una línea no equivale a la mayor suma por producto.

- **Participación visible.** Porcentaje respecto del total definido para esa visualización. En el panel los rankings limitados pueden usar la suma de lo mostrado; en consultas agregadas del copiloto se informa el universo filtrado completo.

- **Asociación.** Patrón observado en datos. No prueba por sí solo causalidad, preferencia del cliente, demanda de mercado o eficacia de una campaña.

- **Detalle seleccionado.** Valor y contexto de un punto, barra o categoría. Seleccionarlo no cambia filtros sin una acción adicional.

### Campos y botones

- **Punto, barra o categoría.** Clic o teclado permiten ver valor exacto y participación del dato seleccionado.

- **Filtrar tablero por territorio.** Botón explícito en el detalle territorial. Abrir el detalle no aplica el filtro automáticamente.

- **Cerrar detalle.** Cierra la selección puntual sin modificar el universo.

- **Tabla de respaldo en vista analítica.** Permite contrastar cifras de la gráfica.

- **Cómo se generaron.** Explica la procedencia y reglas de los hallazgos.

### Paso a paso

1. Lea título, subtítulo, indicador, unidad y filtros de la gráfica. Resultado: Identifica el universo que está comparando.

2. Seleccione el dato que desee revisar. Resultado: Detalle con valor exacto sin cambio inesperado del panel.

3. Compare con la tabla de respaldo. Resultado: La cifra representada tiene soporte verificable.

4. Si desea restringir por territorio, pulse el botón de filtro explícito. Resultado: Se recalcula el panel para ese alcance.

5. Lea hallazgo, evidencia y Cómo se generaron. Resultado: Distingue una descripción numérica de una conclusión sobre causas.

6. Redacte una lectura y una comprobación comercial adicional. Resultado: Por ejemplo revisar composición de productos antes de atribuir una caída a un proveedor.

### Qué hace la IA

Los hallazgos automáticos del panel son determinísticos. La IA conversacional puede explicar la evidencia después, pero su prosa requiere revisión.

### Qué comprueba la plataforma

Cálculo de agregados y visualizaciones sobre el datamart identificado. La gráfica no certifica hipótesis comerciales ajenas a los registros.

### Qué decide la persona

La persona decide qué dato merece atención y qué comprobaciones adicionales necesita antes de actuar.

### Si aparece un problema

- **El Top 8 no suma el total global.** Es un subconjunto; revise su denominador. No ajuste la gráfica para que aparente cubrir todo.

- **Pedidos distintos por producto superan los pedidos globales al sumarlos.** Un pedido puede contener varios productos; el conteo distinto no es aditivo entre grupos.

- **La IA dice que un producto domina el mercado.** El ranking interno no demuestra cuota de mercado. Reformule como posición dentro del universo consultado.

### Ejercicio y respuesta

Un producto lidera por importe y otro por unidades. Escriba dos conclusiones válidas.

Liderazgo por importe y liderazgo por unidades son distintos; ninguno demuestra automáticamente mayor margen o preferencia del mercado.

### Compruebe lo que aprendió

**¿Un gráfico por provincia demuestra dónde ocurrió físicamente la entrega?**
No, salvo evidencia específica. En WWI el caso usa provincia de la ciudad de entrega registrada en la ficha.

**¿Abrir una barra filtra todo el tablero?**
No. El filtro territorial exige su botón explícito.

## Conversar con el copiloto y revisar su respuesta

**Objetivo.** Formular preguntas respondibles y contrastar consulta interpretada, evidencia y conclusión.

El copiloto recibe contexto agregado y procedencia del datamart. Interpreta indicador, dimensión, filtros y Top N, y la plataforma puede ejecutar una consulta agregada permitida antes de pedir una explicación.

Una pregunta puede solicitar otro año o territorio disponible aunque no esté seleccionado en pantalla. Por eso revise Consulta interpretada: la respuesta puede corresponder a otro alcance solicitado y no al filtro actualmente visible.

Las reglas acotan formato, consultas y cautelas; no existe un validador universal de verdad para cada frase del modelo. La alumna debe verificar cifras, denominadores y límites antes de usar la respuesta.

### Conceptos para entender la pantalla

- **Consulta interpretada.** Indicador, agrupación, filtros, límite y orden que la plataforma entendió de la pregunta.

- **Agregado permitido.** Cálculo cerrado sobre dimensiones materializadas de producto, cliente o territorio, con recetas aprobadas; no SQL libre.

- **Evidencia.** Valores y alcance que respaldan la explicación; debe poder contrastarse con el panel o tablas.

- **Pregunta de seguimiento.** Sugerencia ejecutable construida desde capacidades verificadas; no debe asumirse que abre un nuevo módulo de análisis.

### Campos y botones

- **Escriba su pregunta.** Entre 5 y 500 caracteres. Indique indicador, comparación, período, territorio y qué quiere comprender.

- **Guía de preguntas sugeridas.** Ejemplos adaptados al contexto; pueden usarse como punto de partida.

- **Preguntar al copiloto.** Solicita interpretación/explicación. No crea una propuesta ni ejecuta otro ETL.

- **Consulta interpretada.** Revise alcance y denominador antes de leer la narración.

- **Evidencia y cautela.** Permiten reconocer lo calculado y lo que no se ha demostrado.

- **Proveedor y modelo.** Identifican quién generó la respuesta; cambiar de proveedor no debe cambiar las reglas del datamart.

### Paso a paso

1. Confirme ejecución, indicador y filtros antes de preguntar. Resultado: Tiene un contexto inicial claro.

2. Escriba una pregunta concreta, por ejemplo Top 5 de productos por unidades con los filtros actuales. Resultado: Solicitud respondible con capacidades presentes.

3. Espere la respuesta sin enviar varias veces. Resultado: El copiloto muestra interpretación y evidencia si la operación cumple.

4. Lea Consulta interpretada y compare indicador, año, territorio, límite y denominador. Resultado: Reconoce cuándo la pregunta pidió un alcance distinto del panel.

5. Contraste al menos una cifra con tabla o consulta agregada y revise los límites comerciales. Resultado: No acepta una redacción coherente si contradice datos.

6. Pregunte de nuevo para aclarar un denominador o límite, sin atribuir causas que no se han comprobado. Resultado: Conversación útil y controlada.

### Qué hace la IA

Interpreta la intención y redacta respuesta con evidencia agregada. Hay dos generaciones diferenciadas: intención estructurada y explicación. La plataforma aporta seguimiento y cautelas.

### Qué comprueba la plataforma

Permisos, fuente/ejecución, indicadores y dimensiones disponibles, filtros, cantidades Top N entre 1 y 20, consultas agregadas e identificadores permitidos; no acepta SQL libre del modelo.

### Qué decide la persona

La persona formula, revisa y decide si la explicación permite una conclusión. Una recomendación es una comprobación por realizar, no un hecho demostrado.

### Si aparece un problema

- **El proveedor no responde o devuelve formato inválido.** Revise configuración, cuota/tiempo y credencial con el administrador. Un fallo de chat no requiere recargar el datamart.

- **La respuesta usa el año actual para un conjunto histórico.** Recuerde que el reloj del servidor no añade registros futuros; no acepte fechas ajenas a la disponibilidad.

- **Se pide un pronóstico del próximo período.** Es fuera del alcance. El resultado correcto es explicar el límite; no inventar un valor o año.

- **La respuesta llama facturación a los pedidos de AW.** Corrija la interpretación: no se demuestra factura emitida a partir del pedido.

- **La respuesta es fluida pero cambia la cifra.** No la use como evidencia. Registre pregunta, contexto y discrepancia, reintente aclaración y contraste con cálculos determinísticos.

### Ejercicio y respuesta

En AW 21 filtre 2013/Northwest, indicador unidades, y pregunte: Resume las unidades vendidas en 2013 para Northwest. Indica el total y el mes con mayor cantidad, sin atribuir causas ni mezclar importes.

El control histórico del 6 noviembre registró 17.452 unidades y junio 2013 con 2.494. Una sesión nueva debe contrastar sus propios resultados; no copiar esa cifra si el alcance o la fuente cambiaron.

### Compruebe lo que aprendió

**¿Se ejecuta SQL redactado por el LLM?**
No. La intención se limita a consultas agregadas permitidas del servidor.

**¿El copiloto sólo puede responder el filtro visible?**
Puede interpretar otro filtro disponible solicitado. Debe leer la consulta interpretada y no asumir que los dos alcances coinciden.

**¿Una respuesta correcta una vez garantiza que el proveedor nunca fallará?**
No. Se deben revisar cada respuesta y sus controles.

## Exportar y comprobar antes de compartir

**Objetivo.** Obtener informes que conserven universo y procedencia y revisarlos contra el panel.

Exportar PDF produce un informe para lectura. Exportar Excel produce tablas y gráficos de respaldo de las visualizaciones visibles. Ninguno es un respaldo de contenedores, volúmenes o todas las filas de la fuente.

La exportación se genera desde el dashboard autorizado. No es una exportación automática de la conversación del chat; si desea citar una respuesta debe registrar la pregunta y su contexto como evidencia aparte.

### Conceptos para entender la pantalla

- **Contexto exportado.** Fuente, propuesta, ejecución, vista, métrica, filtros y unidad que permiten interpretar el archivo.

- **Trazabilidad.** Información para reconocer qué expediente y selección respaldan las cifras.

- **Redondeo.** Presentación con decimales o abreviaturas; no autoriza a cambiar valores para hacerlos coincidir visualmente.

### Campos y botones

- **Exportar PDF.** Descarga el informe de la vista y selección actuales.

- **Exportar Excel.** Descarga el libro con datos que respaldan los gráficos exportados.

- **Vista ejecutiva/Vista analítica.** Afecta qué visualizaciones se comparten; revise la vista junto a los filtros.

- **Carpeta Descargas.** Abra el archivo recibido y revíselo, no basta con pulsar el botón.

### Paso a paso

1. Fije fuente, ejecución, vista, indicador, año y territorio. Resultado: Alcance exacto que se quiere compartir.

2. Exporte PDF y espere la descarga. Resultado: Archivo con nombre de ejecución y vista.

3. Exporte Excel. Resultado: Libro de revisión, no volcado completo del origen.

4. Abra ambos archivos y compare un total, una entidad y el filtro con el panel. Resultado: Cifras y contexto congruentes.

5. Revise unidad, advertencias, denominadores y procedencia. Resultado: El informe no pierde el límite demostrado en pantalla.

6. Registre fecha, nombre y contexto del archivo revisado. Resultado: Evidencia de revisión real, no sólo descarga.

### Qué hace la IA

No se necesita otra llamada al LLM para generar el informe del dashboard. El chat no convierte el reporte en una conclusión validada por un modelo.

### Qué comprueba la plataforma

Permiso de exportación además de lectura de analítica; servidor reconstruye el mismo dashboard con filtros autorizados y registra la acción.

### Qué decide la persona

La persona elige selección, vista y formato y comprueba el archivo antes de compartirlo.

### Si aparece un problema

- **No hay botones de exportación.** Revise que el rol tenga permisos de lectura del panel y exportación. No se corrige cambiando de vista.

- **El PDF tiene menos gráficos que la Vista analítica.** Compruebe qué vista exportó; la ejecutiva omite el visual de clientes.

- **El porcentaje de Excel no coincide.** Compruebe si es escala 0 a 100 o fracción y qué denominador se usó; no multiplique otra vez por 100 por costumbre.

- **El archivo muestra moneda de origen aunque AW esté en USD.** La evidencia histórica AW 21 conservó una etiqueta genérica en una razón del PDF, pese al valor correcto. No presente ese antecedente como perfección semántica; revise el archivo nuevo.

### Ejercicio y respuesta

Explique por qué no es suficiente mostrar que se descargó un informe para probar que es correcto.

Debe abrirse y comparar cifras, contexto, filtros, unidades y trazabilidad con la selección autorizada.

### Compruebe lo que aprendió

**¿Excel incluye todas las filas del OLTP?**
No. Incluye respaldo de las visualizaciones exportadas.

**¿Se exigen siempre seis páginas y seis hojas?**
No. Esas cantidades pertenecen a los casos históricos concretos; varían con la vista y las visualizaciones.

## Practicar con las dos fuentes sin memorizar una respuesta del modelo

**Objetivo.** Repetir un recorrido básico y uno avanzado en cada fuente con criterios de aceptación observables.

Las cuatro fichas siguientes permiten aprender desde un alcance sencillo hasta documentos distintos, razones y roles de relación. Las básicas son ejercicios propuestos. Las avanzadas conservan objetivos y resultados de la campaña comprobada del 6 de noviembre de 2026.

No se ejecutaron nuevas propuestas ni ETL en esta revisión de redacción. Una instalación limpia puede no tener los números 129/21 y 131/22. Anote los identificadores que genere su propio entorno. Un proveedor puede variar su primera respuesta, por lo que el éxito se evalúa con criterios del modelo y conciliación, no por obtener tarjetas idénticas.

Si desea demostrar con un caso ya conservado, anuncie que consulta un expediente histórico. Si genera desde cero, diga que está realizando una ejecución nueva y registre los resultados que realmente obtenga.

### Conceptos para entender la pantalla

- **Referencia histórica.** Dato documentado de una campaña anterior, útil para comparar si copia y alcance coinciden.

- **Práctica nueva.** Actividad que debe ejecutarse y registrarse; no se presenta como realizada por este manual.

### Campos y botones

- **Ficha de práctica.** Necesidad copiable, preguntas, periodicidad, grano, indicadores y criterios de éxito.

- **Bitácora de la alumna.** Registre fecha, fuente, instantánea, proveedor/modelo, propuesta, ejecución, acciones y resultados propios.

### Paso a paso

1. Comience por la ruta básica de la primera fuente. Resultado: Aprende el recorrido con pocas medidas.

2. Repita la ruta básica de la segunda fuente. Resultado: Comprueba qué se mantiene y qué cambió de evento y claves.

3. Use el caso avanzado AW para conteo distinto y razones. Resultado: Puede explicar diferencia entre línea y pedido.

4. Use el caso avanzado WWI para roles de relación. Resultado: Puede justificar comprador y ciudad de entrega y conservar su procedencia.

5. Compare las dos lecturas sin sumar monedas ni eventos diferentes. Resultado: Comprende la arquitectura común y los significados propios de cada fuente.

### Qué hace la IA

La IA puede ofrecer diseños distintos en cada intento. Aprenderá a revisar cada resultado, justificar las decisiones y corregir lo necesario.

### Qué comprueba la plataforma

Cada práctica vuelve a pasar autorizaciones, viabilidad, contrato, aprobación, preparación, carga y conciliación que correspondan.

### Qué decide la persona

La alumna ejecuta y registra; el analista supervisa; la gerencia explica utilidad y límites de la lectura.

### Si aparece un problema

- **Los identificadores difieren del manual.** Es normal en otra instalación. Compruebe fuente, objetivo y evento; no cambie números a mano.

- **El LLM no entrega la cantidad de KPI esperada.** Revise entradas y recetas; personalice o excluya extras y valide otra versión. No existe un número universal de indicadores.

### Ejercicio y respuesta

Registre la evidencia de una práctica y clasifique qué es generación nueva y qué es consulta histórica.

La evidencia debe permitir reconocer fecha, fuente, propuesta y expediente, con resultado real y no sólo una captura antigua.

### Compruebe lo que aprendió

**¿Se deben forzar las cifras del manual?**
No. Son referencias de una copia y alcance concretos; su ejecución debe conciliar datos reales.

**¿La universalidad obliga a usar la misma relación en ambas bases?**
No. El proceso es común; las relaciones y significados dependen de metadatos y decisiones verificadas.

### Ruta básica AdventureWorks unidades por mes y producto

Ejercicio nuevo propuesto para las alumnas; no ejecutado en esta revisión documental.

**Necesidad para copiar**

Conservar cada línea de pedido de venta para comparar mensualmente la suma de unidades por producto. Usar la fecha del pedido y un nombre de producto comprobable. Mantener la referencia de cada línea a su pedido. Limitar esta práctica al total de unidades y su evolución; no interpretar estos registros como facturas, cobros o pronósticos.

**Preguntas.** Evolución de ventas en el tiempo y desempeño por producto, según las etiquetas disponibles del catálogo de esa fuente.

**Periodicidad.** Mensual

**Grano.** Línea de pedido

**Indicadores.** Suma de unidades; las salidas adicionales se revisan y excluyen si no son necesarias.

**Referencia.** No se asigna un resultado predeterminado a una ejecución no realizada. Si la copia y alcance equivalen al caso histórico, el total global de referencia es 274.914 unidades; debe conciliarse el caso propio.

**Criterios de éxito**

- Objetivo conservado sin ampliar el evento.

- Grano de línea y fecha del pedido verificados.

- Producto descriptivo y ruta sin multiplicación.

- Conciliación del universo nuevo.

- Panel por unidades y mes; no se exige que la IA produzca una cantidad fija de tarjetas.

### Ruta avanzada AdventureWorks documentos distintos y razón por pedido

Caso histórico comprobado el 6 de noviembre de 2026: propuesta 129, ejecución 21. Repetición por las alumnas pendiente.

**Necesidad para copiar**

Conservar cada línea de pedido de venta en un datamart. Para priorizar productos y territorios, comparar mensualmente cuatro indicadores: suma del importe registrado de las líneas, suma de unidades, conteo de identificadores de pedido distintos e importe total dividido entre pedidos distintos. Usar fecha y territorio comercial del pedido, producto y cliente con nombre verificable. Los rankings comparan sumas por entidad. Mantener la trazabilidad de cada línea al pedido. La moneda se reportará sólo si se comprueba en la fuente.

**Preguntas.** Tiempo, producto, cliente y territorio. Revise el catálogo propio antes de seleccionarlas.

**Periodicidad.** Mensual

**Grano.** Línea de pedido

**Indicadores.** Importe registrado total; unidades totales; pedidos distintos; importe total/pedidos distintos.

**Pregunta al copiloto.** Resume las unidades vendidas en 2013 para Northwest. Indica el total y el mes con mayor cantidad, sin atribuir causas ni mezclar importes.

**Acciones específicas**

- Use el objetivo exacto y pase por los cinco pasos del asistente.

- Revise que la cuenta del documento use conteo distinto y que la razón lo use como denominador.

- No agregue costos o margen para igualar un número de tarjetas.

- Apruebe únicamente cero errores y avisos comprendidos; complete los cinco pasos de materialización.

- Consulte primero global, luego 2013/Northwest.

- En Vista analítica elija unidades; lea tabla mensual; pregunte al chat por total y mes líder.

- Exporte y abra PDF y Excel con ese mismo alcance.

**Rutas a comprobar**

- Fecha y territorio comercial del pedido, con territorio procedente de Sales.SalesTerritory.

- Producto y cliente con nombre verificable; clave de línea y pedido conservadas.

**Criterios de éxito**

- Mismo evento, grano y roles del caso.

- Conciliación sin diferencia.

- Cuatro indicadores revisados; no promedio de línea rotulado como promedio por pedido.

- Unidad demostrada y límites de pedido conservados.

- Valores del panel, chat y archivos contrastados con la selección.

**Resultados históricos documentados**

```json
{
  "fecha": "2026-11-06",
  "propuesta": 129,
  "ejecucion": 21,
  "filas_origen": 121317,
  "filas_destino": 121317,
  "diferencia_filas": 0,
  "tablas": 5,
  "global": {
    "importe_exacto": "109846381.399888",
    "moneda": "USD comprobado",
    "unidades": 274914,
    "pedidos_distintos": 31465,
    "importe_por_pedido_exacto": "3491.065672966407"
  },
  "filtro": {
    "anio": 2013,
    "territorio": "Northwest",
    "importe_exacto": "6015174.735836",
    "unidades": 17452,
    "pedidos_distintos": 2053,
    "importe_por_pedido_exacto": "2929.943855740867",
    "mes_mayor_unidades": "junio de 2013",
    "unidades_mes_lider": 2494
  },
  "interpretacion": "Europe, North America y Pacific publicadas como Europa, América del Norte y Pacífico; AU, CA, DE, FR, GB, US excluidos de traducción.",
  "exportacion": "PDF de 6 páginas y Excel de 6 hojas de la Vista analítica por unidades 2013/Northwest; observación histórica de etiqueta genérica de razón monetaria conservada."
}
```

### Ruta básica WideWorldImporters facturas y unidades por mes

Ejercicio nuevo propuesto para las alumnas; no ejecutado en esta revisión documental.

**Necesidad para copiar**

Conservar cada línea de factura para comparar mensualmente la suma de unidades facturadas por producto. Usar la fecha de emisión y el producto con nombre verificable. Mantener el identificador de factura y el de línea para conservar la trazabilidad. Limitar la práctica a unidades y evolución; no afirmar moneda, cobro, utilidad ni entrega realizada.

**Preguntas.** Tiempo y producto según el catálogo propio.

**Periodicidad.** Mensual

**Grano.** Línea de factura

**Indicadores.** Suma de unidades; otras salidas se revisan antes de materializar.

**Referencia.** No se inventa un resultado para esta ejecución nueva. El caso histórico completo WWI 22 conservó 8.950.628 unidades; sólo sirve de contraste si copia y alcance son equivalentes.

**Criterios de éxito**

- La propuesta usa facturación y fecha de emisión, no pedidos como sustituto.

- Producto descriptivo y línea identificable.

- No se añade moneda ni utilidad por intuición.

- Carga conciliada y panel en unidades.

### Ruta avanzada WideWorldImporters roles de cliente y territorio

Caso histórico comprobado el 6 de noviembre de 2026: propuesta 131, ejecución 22; dos correcciones guiadas sucesivas. Repetición por las alumnas pendiente.

**Necesidad para copiar**

Diseñar un datamart cuyo grano físico sea una línea de factura. Sobre ese detalle, resumir mensualmente el importe registrado de la línea, las unidades y las facturas distintas por producto y cliente. Usar la fecha de emisión. Para el territorio, usar la provincia de la ciudad de entrega registrada en la ficha del cliente y aclarar que no representa necesariamente su ubicación histórica. Conservar el importe de origen sin asumir moneda, utilidad ni composición fiscal. Limitar los indicadores a importe total, unidades totales, facturas distintas e importe promedio por factura. Los rankings deben comparar totales por producto; el máximo de una sola línea no identifica al producto líder.

**Preguntas.** Tiempo, producto, cliente y territorio en el catálogo WWI.

**Periodicidad.** Mensual

**Grano.** Línea de factura

**Indicadores.** Importe registrado; unidades; facturas distintas; importe total/facturas distintas.

**Pregunta al copiloto.** Resume el importe, las unidades y las facturas distintas en 2015 para California. Explica el denominador del importe por factura y qué significa la provincia usada, sin asumir moneda ni entrega realizada.

**Acciones específicas**

- Use el objetivo exacto y revise viabilidad.

- Compruebe grano de factura, fecha de emisión, medidas y cuatro indicadores.

- Si la generación usa otro rol, abra Personalización y Resolver una relación con evidencia.

- Elija Cliente y Invoices.CustomerID→Customers; justifique que se analiza al comprador; cree una versión con relación corregida.

- Revise el nuevo resultado; elija Territorio y Customers.DeliveryCityID→Cities; justifique ubicación registrada de entrega; cree otra versión.

- Confirme que se conserva CustomerID y la provincia final de StateProvinces. No acepte una vía postal o de facturación sólo porque mantiene filas.

- Apruebe y materialice si cumple; revise conciliación y divisa.

- En analítica elija 2015/California, contraste cuatro indicadores; pregunte al chat sobre alcance, denominador y límites; exporte y abra archivos.

**Rutas a comprobar**

- Sales.InvoiceLines→Sales.Invoices por la relación de factura.

- Cliente comprador: Invoices.CustomerID→Customers, no BillToCustomerID para esta necesidad.

- Territorio: Customers.DeliveryCityID→Cities.StateProvinceID→StateProvinces, no PostalCityID para esta necesidad.

- La provincia es el destino dimensional; una elección intermedia puede precisar la ruta sin reemplazarla por ciudad.

**Criterios de éxito**

- Evento de facturación con fecha de emisión.

- Rutas exactas de comprador y ciudad de entrega registradas.

- Facturas distintas, no conteo de líneas.

- La moneda no se convierte en USD sin evidencia.

- No se atribuyen ubicación histórica, entrega efectiva o composición fiscal no demostradas.

- No se reutiliza el filtro del expediente legado 19 como oráculo del 22.

**Resultados históricos documentados**

```json
{
  "fecha": "2026-11-06",
  "propuesta": 131,
  "ejecucion": 22,
  "filas_origen": 228265,
  "filas_destino": 228265,
  "diferencia_filas": 0,
  "tablas": 5,
  "global": {
    "importe_exacto": "198043439.45",
    "moneda": "moneda de origen; sin código único demostrado",
    "unidades": 8950628,
    "facturas_distintas": 70510,
    "importe_por_factura_exacto": "2808.7283995177986"
  },
  "filtro": {
    "anio": 2015,
    "territorio": "California",
    "lineas": 3771,
    "importe_exacto": "3191769.11",
    "unidades": 142247,
    "facturas_distintas": 1179,
    "importe_por_factura_exacto": "2707.1832994062765"
  },
  "fecha_dimension": {
    "fechas_unicas": 1069,
    "documentos_origen": 70510,
    "duplicados_controlados": 69441
  },
  "exportacion": "PDF de 6 páginas y Excel de 6 hojas/4 gráficos de la vista filtrada; es un ejemplo histórico, no formato fijo."
}
```

## Costos descuentos y márgenes una ampliación que exige evidencia

**Objetivo.** Reconocer cuándo se puede ampliar el análisis financiero y cuándo debe limitarse.

Los casos finales anteriores se centraron en importe, unidades, documentos y razones. No acreditan automáticamente un margen histórico. Si se necesita rentabilidad, primero se deben comprobar costos compatibles con la venta y su fecha.

Un costo unitario actual del catálogo puede servir de referencia, pero no se convierte por su nombre en el costo real histórico de cada línea vendida. Comparar ese costo con un importe de otro alcance puede producir un cálculo numérico correcto y una interpretación comercial incorrecta.

### Conceptos para entender la pantalla

- **Descuento monetario.** Importe derivado de una base y una tasa; la tasa por sí sola no es dinero.

- **Venta bruta.** Precio por cantidad antes del descuento cuando esa es la receta comprobada.

- **Venta neta de un descuento.** Requiere identificar qué deducción se aplica y si el importe de origen ya la contiene; no descontar dos veces.

- **Costo total.** Costo unitario comparable × unidades, o concepto total directo verificado; requiere una base coherente.

- **Margen bruto.** Diferencia entre importe de venta y costo comparable del mismo alcance.

- **Porcentaje de margen.** Margen ÷ importe de venta del mismo alcance × 100, con divisor cero protegido.

- **Comparabilidad.** Mismo evento, unidad, moneda, período y criterio de valoración para los componentes.

### Campos y botones

- **Fórmula y Origen.** Deben mostrar entradas reales; no normalizar por nombre únicamente.

- **Cobertura de necesidad.** Reconoce si costo o margen se resuelve o queda fuera.

- **Ajuste de seguridad.** Puede corregir una tasa usada como importe, pero no inventa la evidencia económica ausente.

### Paso a paso

1. Formule el objetivo aclarando qué costo desea usar y en qué condición temporal. Resultado: Se distingue costo real, costo estándar actual u otra referencia.

2. Revise viabilidad y entradas para costo, importe, cantidad y descuento. Resultado: Si faltan datos, la salida se limita.

3. Compruebe cálculos por fila y agregados. Resultado: Evita sumar tasas como dinero o promediar márgenes sin ponderación.

4. Apruebe sólo si el significado comparable puede defenderse. Resultado: No se maquilla un bloqueo de calidad comercial.

### Qué hace la IA

Sugiere recetas y explicaciones dentro del contexto. No puede demostrar costos históricos no disponibles a través de un texto convincente.

### Qué comprueba la plataforma

Existencia, tipo, semántica implementada, recetas y relaciones. La revisión humana sigue siendo necesaria para condiciones económicas y temporalidad no acreditadas por el modelo.

### Qué decide la persona

El analista decide qué costo es aceptable y qué límite debe declararse; la gerencia no debe recibir como utilidad real un indicador referencial.

### Si aparece un problema

- **Se afirma margen sólo porque existen columnas Sales y Cost.** Compare procedencia, fecha, moneda y evento antes de usarlo.

- **El importe original ya incluye descuento.** No aplique la tasa dos veces. Revise la fórmula y definición de origen.

- **Se solicitan impuestos o utilidad fiscal sin evidencia.** Limite la necesidad; no infiera composición fiscal por el nombre importe.

### Ejercicio y respuesta

Dos líneas tienen márgenes de 10 % y 50 % con importes de 900 y 100. Calcule el margen agregado.

90+50=140 sobre 1.000; 14 %. El promedio simple 30 % no representa el porcentaje global.

### Compruebe lo que aprendió

**¿La existencia de un costo comprueba su vigencia histórica?**
No. Requiere evidencia temporal y criterio de valoración.

**¿Qué debe hacer si no puede justificarlo?**
Declarar el límite y excluir rentabilidad o usar un indicador referencial correctamente rotulado.

## Resolver problemas y reconocer un rechazo correcto

**Objetivo.** Recuperar el trabajo sin saltarse los controles y registrar incidencias útiles.

Que el sistema rechace una petición no siempre es un defecto. Debe rechazar estructuras inventadas, divisiones no definidas, mezclas de fuente o relaciones que contradigan el objetivo. La recuperación correcta conserva la evidencia y explica qué debe cambiar.

Ante un problema registre pantalla, fecha, fuente, propuesta, expediente, acción y mensaje. No copie contraseñas, claves API o credenciales a capturas o informes.

### Conceptos para entender la pantalla

- **Rechazo esperado.** Control que impide una operación fuera de sus condiciones.

- **Regresión.** Un comportamiento previamente correcto deja de cumplirse después de un cambio; necesita evidencia comparable.

- **Caso no ejecutado.** Prueba planificada que no debe marcarse aprobada sin realizarla.

### Campos y botones

- **Reintentar la misma solicitud.** Para una falla de proveedor, con revisión/consentimiento vigentes; no es un atajo del contrato.

- **Revisar necesidad.** Permite aclarar alcance sin modificar los datos de origen.

- **Abrir resultado / Abrir expediente.** Recuperan evidencia persistida antes de repetir operaciones.

- **Motivo / Justificación.** Explicación de una decisión humana, no código para cambiar estados.

### Paso a paso

1. Determine en qué etapa ocurrió el problema: asistencia, diseño, aprobación, preparación, carga, semántica, panel, chat o exportación. Resultado: No aplica el mismo remedio a todos los fallos.

2. Lea el mensaje y compruebe fuente, versión y estado. Resultado: Separa error de proveedor de una inconsistencia del contrato.

3. Recupere el resultado persistido antes de reenviar. Resultado: Evita duplicidad y consumo innecesario.

4. Aplique la corrección mínima de la tabla de incidencias. Resultado: No altera huellas, reglas o datos del origen.

5. Repita el control afectado y registre resultado. Resultado: La incidencia sólo se cierra con evidencia real.

### Qué hace la IA

Puede fallar por formato, tiempo, cuota, capacidad o interpretación. Cambiar de proveedor puede ser una alternativa operativa, pero no debe cambiar las reglas de validación ni aprobar una respuesta inválida.

### Qué comprueba la plataforma

Formato estructurado, requisitos de estado y permiso, coherencia de contrato y pertenencia de fuente. Los mensajes indican qué resultado no se usó o cuál acción quedó bloqueada.

### Qué decide la persona

El operador recupera; el administrador revisa configuración; el analista corrige alcance y decisiones; la gerencia suspende conclusiones no sustentadas.

### Si aparece un problema

- **El proveedor devolvió JSON pero no cumplió el contrato.** Se descarta su uso. Reintente con la misma revisión válida o coordine proveedor probado; no cargue a mano la respuesta inválida.

- **La necesidad estaba respaldada pero el LLM no conserva el objetivo.** No apruebe; mantenga el texto original y reintente o corrija. Separar fallo de generación de falta de viabilidad.

- **Se pierde la respuesta del navegador.** Revise historial/versiones y expedientes antes de repetir; el servidor puede haber terminado.

- **No aparece una opción por rol.** Revise permisos con administrador; no haga que su compañera use otra identidad para simular un rol.

- **El filtro no da cifras.** Confirme que la combinación de año y territorio exista en el datamart; no cambie el cero a otro valor.

- **La respuesta del copiloto no es coherente.** Conserve pregunta, consulta interpretada, evidencia y contexto. Compare con el motor numérico y registre la corrección requerida.

### Ejercicio y respuesta

Escriba una incidencia que otra persona pueda reproducir sin conocer su contraseña.

Fuente, versión, expediente, condiciones previas, pasos, resultado esperado/obtenido y captura sin secretos.

### Compruebe lo que aprendió

**¿Cambiar el modelo resuelve una ruta ambigua por sí solo?**
No. La elección del rol comercial requiere evidencia y decisión humana.

**¿Un rechazo por facturación cuando se pidió pedido es siempre un defecto?**
No. Puede ser un control correcto que protege el evento solicitado.

**Cambiar AW→WWI→AW**
Fuente, ejecución, filtros, chat y panel corresponden al contexto nuevo; no se conservan datos de la otra fuente.
Estado: Planificada para repetición por alumnas; existen antecedentes documentados.

**Abrir versión aprobada y Verificar evidencia**
Lectura y verificación sin cambiar silenciosamente estado, huellas o datos.
Estado: Planificada para repetición por alumnas.

**Elegir contrato histórico sin rutas actuales para nueva carga**
Nueva carga bloqueada con motivo; histórico sigue consultable.
Estado: Regla contrastada con código.

**Ruta WWI de BillToCustomerID en objetivo comprador**
No se acepta como sustituto; usar decisión guiada con CustomerID.
Estado: Antecedente histórico 6 noviembre; repetición nueva pendiente.

**Ruta WWI de PostalCityID en objetivo ciudad de entrega**
No se acepta como sustituto; DeliveryCityID con provincia conservada.
Estado: Antecedente histórico 6 noviembre; repetición nueva pendiente.

**Volver a preparar contrato/selección ya ejecutados**
Abre expediente o conflicto de duplicidad; no otra carga idéntica accidental.
Estado: Regla contrastada con código.

**Divisor de una razón cero**
Sin valor/no calculable; no infinito ni porcentaje inventado.
Estado: Regla contrastada con código; no se modifican datos para provocarla aquí.

**Divisa WWI no demostrada**
Moneda de origen, con importes conservados.
Estado: Caso 22 documentado 6 noviembre.

**Pedir pronóstico para próximo período**
Explica fuera del alcance sin inventar cifra futura.
Estado: Ejercicio supervisado; no se promete que toda respuesta libre sea correcta.

**Exportar sin lectura del panel o sin permiso de exportación**
Operación rechazada por servidor; no archivo con datos no autorizados.
Estado: Regla contrastada con código; sesión manual por rol debe registrarse aparte.

## Demostrar y defender el recorrido completo

**Objetivo.** Explicar cada etapa con evidencia y responder preguntas del jurado sin prometer capacidades no implementadas.

Una demostración sólida no consiste en pulsar botones rápido. Explique la decisión de negocio, muestre su traducción al modelo y compruebe el resultado. Haga pausas en los puntos donde una persona acepta una decisión.

Practique primero la consulta del caso histórico y después una ejecución nueva cuando tenga tiempo y proveedor disponible. Lleve el PDF y Excel ya revisados como referencia, identificados con su fecha; no los presente como una descarga nueva si no lo es.

### Conceptos para entender la pantalla

- **Eficacia observable.** Cumplimiento de criterios funcionales y numéricos del caso.

- **Eficiencia comparativa.** Requeriría tareas equivalentes y medidas de tiempo/esfuerzo/costo frente a una referencia. No se deduce de que el prototipo funcione.

- **Supervisión.** Decisiones humanas explícitas entre asistencia de IA, reglas determinísticas y ejecución controlada.

### Campos y botones

- **Ficha de caso.** Propósito, fuente, objetivo, grano, indicadores, rutas, unidad y filtros.

- **Comprobantes.** Aprobación, preparación, carga, conciliación y publicación de etiquetas.

- **Bitácora.** Estado observado, hora, identificadores y archivos realmente revisados.

### Paso a paso

1. Presente el problema como correspondencia entre necesidad comercial y datos disponibles. Resultado: No afirma que faltaba IA en todas las empresas ni que la herramienta aumentó ventas.

2. Muestre esquema y catálogo de cada fuente. Resultado: Reconoce diferencias sin cambiar el proceso común.

3. Explique necesidad y viabilidad. Resultado: Distingue estructura, candidatos y límites.

4. Lea modelo, personalización y aprobación. Resultado: Se ven las decisiones humanas y las reglas que no pueden saltarse.

5. Muestre preparación, carga y conciliación, nueva o histórica identificada. Resultado: La audiencia reconoce de dónde salen los datos.

6. Interprete el panel, use un filtro y pida una explicación al chat. Resultado: Compara cifras y consulta interpretada sin atribuir causas.

7. Exporte y abra los archivos, o muestre los históricos como tales. Resultado: Cierra con contexto y trazabilidad.

8. Explique una restricción: pronóstico fuera del alcance, moneda no comprobada o costo no comparable. Resultado: Demuestra criterio y no infalibilidad universal.

### Qué hace la IA

Asiste en formulación, sugerencias, diseño, consejo semántico, etiquetas aptas y conversación analítica. No reemplaza todos los cálculos ni la aprobación humana.

### Qué comprueba la plataforma

Puertas de entrada, requisitos, contrato, relaciones, recetas, permisos, procedencia, carga y conciliación según el alcance implementado.

### Qué decide la persona

La persona define, selecciona, justifica, aprueba, confirma, revisa etiquetas e interpreta el significado comercial del resultado.

### Si aparece un problema

- **El proveedor falla frente al jurado.** Explique el rechazo seguro, conserve el estado y consulte el caso histórico identificado; no diga que una ejecución nueva terminó si no ocurrió.

- **El jurado pregunta por otro motor o idioma.** Explique arquitectura adaptable y límites comprobados. Dos fuentes SQL Server y variantes de pruebas no certifican cualquier motor, idioma o modelo.

### Ejercicio y respuesta

Prepare una exposición de 10 minutos y otra de 25 minutos; en ambas identifique qué pasos consulta y qué pasos ejecuta.

La corta puede usar expedientes históricos verificados; la larga puede generar un caso nuevo con margen para revisión sin prometer una respuesta fija.

### Compruebe lo que aprendió

**¿Qué hace inteligente al sistema?**
Combina interpretación y propuestas de IA con contexto, reglas, memoria de expedientes y supervisión; no que toda acción la realice un LLM.

**¿Qué evidencia usaría para demostrar una cifra?**
Fuente, propuesta, ejecución, alcance, fórmula, conciliación y tabla/reporte del mismo universo.

**¿Qué no se puede prometer?**
Infalibilidad LLM, pronóstico, eficiencia comparativa no medida, compatibilidad de todos los motores ni efectos económicos reales no investigados.

## Fuentes locales contrastadas

- /home/ceo/Proyectos/BI/frontend/src/App.tsx — Asistente, editor, relaciones guiadas, aprobación, materialización y revisión semántica.

- /home/ceo/Proyectos/BI/frontend/src/AnalyticsPage.tsx — Vistas, selección de ejecución, filtros, interacciones, chat y exportación.

- /home/ceo/Proyectos/BI/backend/app/modules/copilot/router.py — Consentimiento, viabilidad, versiones, relaciones, verificación y aprobación.

- /home/ceo/Proyectos/BI/backend/app/modules/copilot/needs.py — Análisis estructural de capacidades y evento.

- /home/ceo/Proyectos/BI/backend/app/modules/copilot/need_advisor.py — Contexto de IA, validador de referencias/semántica y revisión combinada.

- /home/ceo/Proyectos/BI/backend/app/modules/copilot/service.py — Contrato BI, normalización y validación.

- /home/ceo/Proyectos/BI/backend/app/modules/copilot/entity_resolution.py — Identidad y roles dimensionales.

- /home/ceo/Proyectos/BI/backend/app/modules/etl/router.py — Elegibilidad, preparación, duplicidad, carga, divisa y etiquetas.

- /home/ceo/Proyectos/BI/backend/app/modules/etl/service.py — Recetas permitidas, cobertura, unidades y plan.

- /home/ceo/Proyectos/BI/backend/app/modules/etl/materializer.py — Lectura, carga, destinos por ejecución, conciliación y divisa.

- /home/ceo/Proyectos/BI/backend/app/modules/analytics/router.py — Permisos, copiloto de intención/explicación y exportes.

- /home/ceo/Proyectos/BI/backend/app/modules/analytics/service.py — Recálculo, agregados, ratios, ranking, denominadores, procedencia y calidad.

- /home/ceo/Proyectos/BI/backend/app/modules/reports/analytics_export.py — Construcción de archivos del dashboard autorizado.

- /home/ceo/Proyectos/BI/docs/manual-usuario/edicion-2026-11-06/contenido_formacion.json — Antecedentes y objetivos exactos AW 129/21 y WWI 131/22.

- /home/ceo/Proyectos/BI/docs/testing/qa-postcierre-2026-11-06.md — Control histórico, oráculo filtrado, exportes y límites.

- /home/ceo/Proyectos/BI/docs/testing/evidencia-postcierre-2026-11-06.json — Referencias numéricas y huellas de evidencias históricas.
