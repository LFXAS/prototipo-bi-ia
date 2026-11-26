# Continuar el trabajo y usar OpenAI

Adenda operativa del 25 de noviembre de 2026. Este resumen editable acompaña al
PDF de siete páginas, cuya fuente principal es `adenda_operacion.tex`.

## Lo esencial del recorrido

Los metadatos describen tablas, columnas, tipos, claves y relaciones. La viabilidad
revisa el respaldo de una necesidad; la propuesta plantea el modelo y los indicadores.
Aprobar una propuesta no ejecuta el ETL. La carga y la conciliación tienen sus
propias decisiones y evidencias. El panel debe corresponder a una fuente y ejecución
concretas. La IA propone; las reglas de la aplicación y una persona supervisan.

## Recuperar el módulo y volver al origen

1. Al recargar una pestaña, compruebe que recuperó el módulo y la fuente correctos.
   El módulo sólo se abre si su cuenta mantiene acceso.
2. Desde Inicio, abra **Revisar configuración** y use **Revisar este paso**.
   El botón **Atrás** del destino regresa al paso de preparación de origen.
3. El paso 5, **Elegir datamart**, y **Crear propuesta de datamart** desde Inicio
   también conservan su retorno. La entrada por la barra lateral no añade ese botón.
4. En Analítica, **Consultar respaldo** permite ir al espacio del datamart y volver
   mediante **Atrás**. Se recupera la selección confirmada, sin guardar el chat.

La duración de sesión se configura en **Parámetros > Duración de la sesión (minutos)**
por una persona con permiso de edición. Su valor inicial es **60 minutos** y el rango permitido es **15 a 240**.
Para ensayos largos se puede elegir 60 o 120 minutos. El ajuste técnico se identifica
como `AUTH_SESSION_MINUTES` y afecta a los nuevos inicios de sesión.

El tiempo cuenta desde la autenticación; usar la aplicación no reinicia el contador.
Cambiar el parámetro no extiende un token ya emitido. Ajuste el tiempo antes de un
ejercicio nuevo e inicie otra sesión para aplicarlo. Si vence durante el trabajo,
autentíquese y compruebe fuente, borrador y preguntas; autorice de nuevo el destino
de IA cuando se solicite. El cierre voluntario limpia el borrador local, por lo que
debe considerar ese efecto si ya empezó una necesidad.

## Configurar OpenAI

1. Entre en **Preparación del entorno > Configuración LLM** con permiso administrativo.
2. Cree una configuración con nombre reconocible y seleccione **OpenAI**.
3. Revise URL `https://api.openai.com/v1`, modelo económico `gpt-6-luna` y razonamiento **Bajo**.
   El modelo es editable; su cuenta debe tener acceso al identificador seleccionado.
4. Guarde la configuración. Use **Registrar credencial** para ingresar su API key
   directamente en el campo privado de la aplicación. No la copie al manual o al chat.
5. Pulse **Probar conexión**. Es una solicitud técnica pequeña sin datos de negocio,
   pero puede consumir tokens de API.
6. Si la prueba confirma el acceso, active la configuración y compruebe el proveedor
   visible en Inicio o en el Asistente. Sólo hay un proveedor activo para la aplicación.

OpenAI y Groq tienen cuentas, claves y cuotas distintas. Un modelo de Groq cuyo nombre
contenga «openai» sigue consumiendo la cuota de Groq. Los créditos de API de OpenAI
requieren el proveedor OpenAI y una clave del proyecto de OpenAI correspondiente.

GPT-6 Luna admite Responses y salidas estructuradas y se recomienda con razonamiento
bajo cuando se prioriza el presupuesto. GPT-6.2 Sol, con razonamiento medio, cuenta
con recorridos completos comprobados en ambas bases: propuesta, aprobación, carga
y panel. Con Luna sólo se ejecutó una prueba técnica de conexión y JSON estructurado;
no se ensayaron viabilidad, propuesta ni ETL. Esa comprobación no equivale a la
validación completa de Sol ni demuestra la misma calidad.

Tarifas Standard de texto por millón de tokens, contexto corto, consultadas el
25 de noviembre de 2026:

| Modelo | Entrada | Salida |
| --- | ---: | ---: |
| GPT-6 Luna | USD 0,10 | USD 0,50 |
| GPT-6.2 Sol | USD 2,00 | USD 10,00 |

Las tarifas de Luna son un 95% menores. No significa que cada respuesta cueste un
95% menos: el consumo y los reintentos pueden diferir.

El presupuesto de Responses incluye razonamiento y salida final: el adaptador reserva
4096 tokens para automático/mínimo/bajo, 8192 para medio y 16384 para alto; respeta un
presupuesto mayor de la operación hasta un techo de 32768. Son límites por solicitud,
no importes cobrados completos. Un flujo puede realizar varias solicitudes.

## Si una pregunta del catálogo desapareció

1. Lea el aviso. El objetivo y las preguntas todavía válidas se conservan.
2. Compruebe la fuente. Las preguntas de una conexión no deben heredarse en otra.
3. Revise preguntas y periodicidad. No reemplace una pregunta retirada por una etiqueta
   parecida si representa otra necesidad.
4. Autorice el destino y valide la viabilidad otra vez: cambió el alcance de la selección.
5. Revise las referencias y límites antes de generar la propuesta.

**Directo** significa que hay referencia estructural; no prueba calidad de valores.
**Derivable** exige una relación o fórmula controlada y validación posterior.
**Ambiguo** requiere aclarar el evento, la fecha o la entidad.
**No disponible** exige reducir el alcance o aportar una fuente autorizada con respaldo.

El incidente del borrador de WideWorldImporters ocurrió antes de llamar a la IA por
preguntas retiradas. No demuestra por sí mismo un fallo de Claude o un cruce de datos.
Consultar una propuesta histórica debe conservar sus decisiones; los cambios se hacen
mediante una versión nueva y revisada.

## Ejercicios de aprendizaje

Estos son textos de ensayo, no una garantía de aceptación ni un registro de pruebas.

**AdventureWorks:** Analizar mensualmente los importes registrados y las unidades
vendidas por producto, para revisar su evolución y comparar los productos con mayor
resultado, sin atribuir causas ni añadir fuentes externas.

**WideWorldImporters:** Analizar mensualmente los importes y cantidades de las líneas
facturadas por producto, para comparar su evolución y desempeño, sin suponer una moneda
ni una composición fiscal que los datos no demuestren.

Para cada fuente: confirme esquema e instantánea; revise su catálogo; seleccione las
preguntas pertinentes y período mensual; valide el objetivo; genere y revise la propuesta;
apruebe sólo si cumple; prepare y confirme el ETL autorizado; contraste conciliación;
pruebe panel, filtros, vistas, exportaciones y preguntas del copiloto.

Una línea, un pedido y una factura no son el mismo nivel de detalle. Cuente documentos
distintos con su identificador respaldado; contar líneas no satisface ese requisito.
Compruebe que cada resultado solicitado tenga un indicador disponible: la presencia
de una columna de cantidad no demuestra que el panel publique un KPI de unidades.
Una asociación en las ventas no acredita causalidad.

## Resolver problemas

| Aviso o situación | Acción |
| --- | --- |
| Sesión vencida | Autentíquese y revise el punto recuperado. |
| No aparece Atrás | Compruebe si entró por el recorrido guiado o por el menú directo. |
| Cambio de catálogo | Revise opciones y periodicidad y repita consentimiento y viabilidad. |
| Clave rechazada | Reemplace la credencial en su campo privado. |
| Saldo o acceso insuficiente | Compruebe crédito, proyecto y modelo en OpenAI. Repetir continuamente no corrige el saldo. |
| Salida incompleta o contrato inválido | Revise el aviso, la complejidad y la configuración; la respuesta descartada no se aprueba. |
| Propuesta bloqueada | Compruebe respaldo, evento y fórmulas; no oculte un requisito para forzar su aceptación. |
| Contexto o datos diferentes | Deténgase y contraste fuente, propuesta, ejecución, filtros y unidades con el respaldo. |
| Filtros o chat pendientes | Espere la confirmación. Las respuestas de otro contexto se descartan y los filtros fallidos no se guardan como resultado confirmado. |

El tratamiento de la propuesta conserva todos los requisitos revisados y deja de
excluir referencias documentales necesarias por su nombre. Las instrucciones nuevas
son `sales-bi-v9`; los contratos nuevos usan reglas de compilación 6, que comprueban
también la cobertura de indicadores solicitados. Se conservan los contratos y evidencias
históricos de reglas 1 a 5. El informe QA de la entrega identifica lo realmente probado.

Referencias oficiales consultadas el 25 de noviembre de 2026:
[GPT-6.2 Sol](https://developers.openai.com/api/docs/models/gpt-6.2-sol),
[GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna),
[elección de modelos](https://developers.openai.com/api/docs/guides/latest-model),
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs),
[razonamiento](https://developers.openai.com/api/docs/guides/reasoning) y
[créditos API](https://developers.openai.com/api/docs/guides/chatgpt-api-credits).

La selección confirmada se conserva separadamente para cada conexión dentro de
la pestaña. Al volver a una fuente se recupera su propio expediente, indicador,
año, territorio y vista. Restablecer sólo limpia esa fuente; cerrar sesión limpia
todas. No se almacenan cifras ni conversaciones.
