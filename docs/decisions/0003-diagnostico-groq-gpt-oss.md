# ADR 0003: diagnóstico de Groq GPT-OSS y política de resiliencia

- Fecha: 2026-09-25
- Estado: aceptada para implementación
- Alcance: `openai/gpt-oss-120b` mediante Groq Cloud

## Contexto y línea base protegida

Antes del diagnóstico se completó el control de versiones obligatorio:

- checkpoint publicado: `6cd05ea23518935ef209e79b46e0f9ea59b84aa6`;
- tag publicado: `checkpoint-bi-pre-codex-2026-09-25`;
- rama de trabajo: `feature/bi-assistant-hardening`;
- `make verify`: correcto;
- backend: 84 pruebas correctas;
- frontend: 11 pruebas correctas;
- Compose, flujo de ramas, compilación frontend y ocho documentos LaTeX: correctos.

Los reportes locales de `output/` y los archivos `.env` quedaron fuera del checkpoint.

## Método de reproducción

Se utilizó la configuración cifrada ya registrada en la plataforma, sin imprimir ni exportar la API key. Todas las solicitudes emplearon el mismo modelo y una salida JSON mínima. Se capturaron el estado HTTP, el cuerpo sanitizado, `x-request-id`, límites restantes, tiempo y uso de tokens.

## Evidencia

| Caso | Presupuesto | Resultado | Evidencia relevante |
|---|---:|---|---|
| `low` + JSON Schema estricto | 256 | HTTP 200 | request `req_01m3cr7s2eetptepfxtgtxbq5m`; 9 tokens de razonamiento, 32 de salida |
| `medium` + JSON Schema estricto | 256 | HTTP 200 | request `req_01m3cr7sfyebpawsy26ks2facj`; 95 tokens de razonamiento, 118 de salida |
| `high` + JSON Schema estricto | 256 | HTTP 400 | request `req_01m3cr7t01e8xs1r8p810tbpn9`; código `json_validate_failed` |
| `high` + JSON Schema estricto | 512 | HTTP 200 | request `req_01m3cr8nghe8bt45jm0g89msk7`; 144 tokens de razonamiento, 167 de salida |
| `high` + JSON Schema estricto | 1024 | HTTP 200 | request `req_01m3cr8p7ve0dsvjnaps5g47xz`; 139 tokens de razonamiento, 162 de salida |
| `medium` + JSON Object | 32 | HTTP 400 | request `req_01m3cr8qw0e5hrx9ptjrmhjryz`; `json_validate_failed` |
| `high` + JSON Object | 32 | HTTP 400 | request `req_01m3cr8r9teystz1vv5m3tr6t3`; `json_validate_failed` |
| `low` + JSON Object | 32 | HTTP 200 | request `req_01m3cr8qese3btd01ykgcajhg7`; terminó por longitud, pero alcanzó a emitir el JSON |

La evidencia histórica de la aplicación muestra además dos causas independientes:

- la propuesta 57 clasificó incorrectamente un `json_validate_failed` como parámetro incompatible;
- la propuesta 58 falló por HTTP 429 y una nueva ejecución posterior sí avanzó, coherente con un límite transitorio y no con una necesidad inviable.

No existe `x-request-id` histórico para esos dos casos porque el adaptador anterior no lo registraba. Esta ausencia es parte del hallazgo de observabilidad.

## Compatibilidad de parámetros

La documentación oficial vigente de Groq indica que GPT-OSS 20B/120B admite `reasoning_effort` `low`, `medium` y `high`. Para excluir la traza de razonamiento recomienda `include_reasoning: false`; `include_reasoning` y `reasoning_format` son mutuamente excluyentes.

La prueba directa confirmó:

- `include_reasoning: false` funcionó con `low` y `high`;
- la respuesta no incluyó el campo `reasoning`;
- enviar a la vez `include_reasoning: false` y `reasoning_format: hidden` produjo HTTP 400: `cannot specify both include_reasoning and reasoning_format`;
- omitir ambos parámetros devuelve el razonamiento en un campo separado.

Referencias primarias:

- <https://console.groq.com/docs/reasoning>
- <https://console.groq.com/docs/structured-outputs>
- <https://console.groq.com/docs/rate-limits>
- <https://console.groq.com/docs/model/openai/gpt-oss-120b>

## Causa raíz

1. **Medium y high no son parámetros inválidos.** El error observado era una clasificación demasiado amplia de cualquier HTTP 400.
2. **El razonamiento comparte el presupuesto de finalización.** Con presupuestos pequeños, el modelo puede consumir la salida antes de emitir el JSON y Groq responde `json_validate_failed`.
3. **El 429 de low es independiente.** Corresponde a un límite temporal; debe respetarse `retry-after` y reintentarse de forma acotada.
4. **El workaround previo no sigue el contrato documentado actual.** `reasoning_format: hidden` debe sustituirse por `include_reasoning: false` para GPT-OSS.
5. **Falta observabilidad.** El adaptador no conserva request-id, código del proveedor, intento ni encabezados de límite en sus registros técnicos.

## Decisión

- mantener `reasoning_effort` `low`, `medium` y `high` para GPT-OSS;
- usar `include_reasoning: false` y no combinarlo con `reasoning_format`;
- reservar como mínimo 256 tokens en low, 384 en medium y 512 en high para la prueba de conexión;
- clasificar por separado autenticación, permisos/modelo, parámetros, Structured Output, presupuesto/contexto, 429, timeout y 5xx;
- reintentar únicamente 429, timeout y 5xx, con límite, backoff y respeto de `retry-after`;
- no reintentar automáticamente HTTP 400; un `json_validate_failed` debe producir una explicación específica y conservar evidencia técnica sanitizada;
- registrar proveedor, modelo, nivel, intento, estado, código, request-id y límites sin guardar prompts, filas ni credenciales.

## Riesgos y controles

- Un esquema complejo puede requerir más salida aunque el nivel sea low. Los presupuestos funcionales continúan definidos por cada caso de uso y la prueba de conexión sólo fija un mínimo seguro.
- Un 429 puede provenir de RPM, RPD, TPM o TPD. El mensaje al usuario será general pero el registro técnico conservará los encabezados que permitan distinguirlo.
- La validez estructural del JSON no garantiza exactitud semántica; todas las referencias y cálculos continúan sometidos a validación determinística.
