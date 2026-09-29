# SPR-05-04: capacidades y compatibilidad de proveedores LLM

- Estado: **implementada para los proveedores y modelos registrados**
- Dependencia: configuración LLM del Sprint 2 y proveedores del Sprint 3
- Proveedores actuales: Gemini Cloud, Groq Cloud, Anthropic Claude, Qwen Cloud y Ollama local

## 1. Problema y objetivo

La pantalla permite seleccionar niveles de razonamiento que no necesariamente son aceptados por todas las combinaciones de proveedor, modelo y endpoint. Un error HTTP 400 al elegir nivel medio o alto en Groq no debe exponerse como fallo genérico ni obligar al usuario a probar valores al azar.

La plataforma mantendrá una matriz de capacidades validada por adaptador y modelo. Sólo ofrecerá parámetros compatibles, registrará la causa segura de un rechazo y propondrá una corrección concreta sin revelar la credencial.

## 2. Reglas

1. Proveedor, modelo y modalidad determinan niveles admitidos; no se aplica una lista universal.
2. El adaptador traduce el nivel interno al parámetro exacto esperado por el proveedor o lo omite si no corresponde.
3. La prueba de conexión valida el mismo contrato que se utilizará en generación, con una solicitud mínima.
4. Un `400` de capacidad se traduce a un mensaje como: modelo no admite este nivel, valor esperado y opción segura disponible.
5. La interfaz deshabilita opciones no admitidas conocidas y explica por qué.
6. Si la capacidad no está catalogada, se usa el valor seguro por defecto y se informa que debe comprobarse; nunca se escala silenciosamente el esfuerzo.
7. Cambiar el nivel no reemplaza ni expone el API key.
8. Para Anthropic Claude, la modalidad inicial omite pensamiento extendido y usa
   el nivel interno `minimal`; esto maximiza el presupuesto disponible para la
   respuesta JSON y evita enviar parámetros incompatibles. El modelo sigue siendo
   editable y la prueba usa el mismo endpoint `/v1/messages` que la generación.
9. Todos los proveedores reciben un contrato funcional canónico. El adaptador puede
   traducir parámetros, presupuesto, formato estructurado y política de reintentos
   según las capacidades del modelo, pero no puede cambiar la semántica BI ni omitir
   las validaciones determinísticas.
10. El esquema de descubrimiento semántico se deriva automáticamente del bloque de
    metadatos vigente. Las referencias permitidas son únicamente objetos reales de
    ese bloque y su cardinalidad no puede limitarse con un máximo artificial inferior
    a la evidencia disponible.
11. Una respuesta estructurada rechazada por el proveedor se clasifica según su causa:
    incompatibilidad de contrato, presupuesto, límite temporal o parámetro no
    admitido. Un error de contrato no se presentará como falta de alcance de negocio.
12. Si el proveedor falla antes de entregar conceptos, la necesidad y su análisis de
    viabilidad permanecen disponibles. La interfaz permite reintentar la misma
    solicitud o cambiar de proveedor sin obligar a reescribirla.
13. Los resultados se aceptan sólo después de la validación local de referencias,
    relaciones y reglas BI. Adaptar el transporte a un modelo nunca autoriza tablas,
    columnas, relaciones, métricas ni cálculos inventados.
14. Los límites temporales se reintentan respetando la ventana `retry-after` informada
    por el proveedor, acotada a 45 segundos por espera. No se reintentan de forma
    indefinida ni se pide al usuario que adivine el momento adecuado.
15. Todos los documentos JSON se contrastan localmente con el contrato canónico. Si
    Groq agota los reintentos de esquema estricto por `json_validate_failed`, el
    adaptador puede realizar un único intento con `json_object` y el mismo esquema
    incluido en la instrucción. Esta adaptación sólo cambia el transporte: una salida
    que incumpla el contrato local se descarta y nunca llega a la propuesta BI.
16. La evaluación de viabilidad y las derivaciones son independientes del proveedor.
    Cambiar de Claude a Groq o viceversa no cambia las relaciones, fórmulas ni
    requisitos aceptados; sólo cambia quién propone el documento estructurado.

## 3. Datos, API e interfaz

La configuración conserva `provider`, `model`, `reasoning_level` y resultado de la última prueba. El backend expone capacidades efectivas de la selección. El formulario actualiza las opciones al cambiar proveedor/modelo y presenta errores junto al campo, no como texto técnico aislado.

## 4. Seguridad y costos

Sólo `parameters.llm.manage` modifica la configuración. La prueba usa el mínimo de salida posible, limita tiempo y registra proveedor/modelo/nivel sin almacenar prompts sensibles ni respuestas completas. Nunca se registra la clave.

## 5. Criterios de aceptación

- [x] El error real de Groq medio/alto se reprodujo de forma controlada y se clasificó antes de corregir.
- [x] La combinación `openai/gpt-oss-120b` traduce mínimo a `low` y admite `low`, `medium` y `high`.
- [x] El adaptador usa `max_completion_tokens`, oculta el razonamiento y no envía parámetros incompatibles.
- [x] La prueba de conexión reserva salida suficiente y un rechazo se convierte en un mensaje accionable.
- [x] La prueba de conexión y la generación usan la misma traducción de capacidades.
- [x] Los errores no exponen credenciales ni respuesta interna completa.
- [x] Las pruebas cubren traducción de niveles, omisión automática, presupuesto, esquema JSON estricto y errores seguros.
- [x] Anthropic valida endpoint, cabeceras, modelo, presupuesto, extracción de
      bloques de texto, JSON y clasificación segura de autenticación, autorización,
      modelo inexistente y saturación.
- [x] La misma necesidad compleja se ejecuta con Groq y Claude en medio y alto;
      conexión, tiempo, estado, errores, advertencias y cobertura quedan registrados
      sin aprobar propuestas ni materializar otro datamart.
- [x] Después del experimento, Claude deja de ofrecer medio/alto porque el adaptador
      vigente omite pensamiento extendido; la API aplica la misma restricción y evita
      configuraciones engañosas fuera de la interfaz.
- [x] Una respuesta con cuatro o más referencias técnicas reales no falla por un
      límite interno arbitrario; todas las referencias se deduplican y se vuelven a
      comprobar contra la instantánea.
- [x] Groq, Claude, Gemini y Ollama comparten el mismo contrato funcional, mientras
      cada adaptador aplica automáticamente sólo las capacidades técnicas admitidas.
- [x] `json_validate_failed` distingue un incumplimiento del esquema de una salida
      truncada por presupuesto y conserva código, estado y `request-id` seguros en la
      auditoría.
- [x] Un `provider_failed` no muestra «No se encontró un alcance verificable» si la
      viabilidad ya fue aprobada; ofrece reintento de la misma necesidad sin perder el
      avance.
- [x] Un límite temporal con `retry-after` superior a diez segundos espera la ventana
      indicada, hasta el máximo seguro, antes de consumir el siguiente intento.
- [x] Tras agotar el esquema estricto, Groq dispone de una recuperación JSON única y
      localmente validada, sin reducir requisitos ni cambiar de proveedor.

## 6. Resultado de implementación

El rechazo HTTP 400 no se debía a que Groq prohibiera el esfuerzo medio o alto para `openai/gpt-oss-120b`, sino a que la prueba consumía su presupuesto reducido antes de completar el JSON. La prueba corta reserva salida según el nivel, usa `include_reasoning: false` y la generación asigna un presupuesto acorde al contrato. La conexión real se comprobó con esfuerzo alto y el copiloto analítico respondió con Groq sin exponer la traza de razonamiento.

La comparación integral del 27 de septiembre añadió una distinción necesaria: la
compatibilidad de parámetros no garantiza que un contrato BI complejo finalice. Groq
medio no completó la salida estructurada y Groq alto alcanzó un límite temporal; Claude
medio/alto devolvió contratos completos, pero las reglas bloquearon dos errores de
procedencia. El adaptador Claude omite pensamiento extendido, por lo que esos dos niveles
no representan todavía esfuerzos diferentes. La decisión operativa es Groq bajo como
principal y Claude bajo/mínimo como respaldo. La evidencia completa está en
`docs/experiments/2026-09-27-groq-vs-claude.md`.

## 7. Incidente de cardinalidad del contrato estructurado

Una repetición posterior con Groq en nivel bajo devolvió cuatro referencias técnicas
reales para un candidato, pero el esquema de transporte aceptaba como máximo tres. El
proveedor rechazó correctamente la respuesta con `json_validate_failed`; la aplicación
lo interpretó de forma incorrecta como falta de presupuesto y la interfaz mostró que no
existía alcance verificable. La necesidad no era la causa: su viabilidad contenía nueve
requisitos directos, diez derivables y ninguno ambiguo o no disponible.

La corrección exigida es transversal: construir el esquema semántico a partir de los
objetos reales enviados en cada bloque, adaptar su transmisión a las capacidades del
proveedor y volver a validar localmente la respuesta. No se introducirán excepciones de
negocio para Groq ni instrucciones distintas para Claude; la variación permitida reside
únicamente en el adaptador técnico.

La repetición controlada produjo finalmente la propuesta `#86` con Groq en nivel bajo:
9 requisitos directos, 10 derivables, 6 conceptos, 14 tablas de alcance, 0 errores y 0
advertencias. La expansión determinística siguió dos relaciones de identidad verificadas
y resolvió el cliente mediante `Person.Person` y `Sales.Store`; también conservó medidas
de ventas, unidades, descuento monetario y costo. La propuesta quedó lista para revisión,
sin aprobación ni ejecución ETL automática.
