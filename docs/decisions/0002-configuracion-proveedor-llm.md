# ADR 0002: configuración de proveedor LLM

- Estado: aceptada
- Fecha: 2026-09-04; ampliada el 2026-09-23, 2026-09-26 y 2026-11-25

## Contexto

El prototipo BI asistido por IA necesita una conexión LLM que pueda funcionar tanto en una demostración local reproducible como con servicios cloud. La clave de un proveedor no puede quedar en texto legible en PostgreSQL, React, archivos versionados ni auditoría. La tesis tampoco debe depender de que una cuota gratuita o un modelo cloud específico continúe disponible.

## Decisión

Sprint 2 implementará una única configuración LLM activa, administrable por un permiso específico. Sólo se admiten inicialmente estos adaptadores internos de FastAPI:

| Tipo | Servicio | Referencia de secreto | Modelo/configuración inicial |
|---|---|---|---|
| `gemini` | Gemini API Cloud | Secreto cifrado registrado desde la web | Modelo Gemini Flash permitido por la cuenta. |
| `openai-cloud` | OpenAI Responses API | Secreto cifrado registrado desde la web | `gpt-6-luna`, razonamiento bajo como preset económico final; Sol medio fue el modelo de los dos ensayos completos. Modelo editable según acceso de la organización. |
| `groq-cloud` | Groq Cloud, API compatible con OpenAI | Secreto cifrado registrado desde la web | `openai/gpt-oss-120b`; razonamiento bajo recomendado para equilibrar rapidez y profundidad. |
| `anthropic-cloud` | Anthropic Messages API | Secreto cifrado registrado desde la web | `claude-haiku-4-5-20251001`; nivel mínimo recomendado para rapidez y control de costo. |
| `qwen-cloud` | Alibaba Cloud Model Studio / DashScope | Secreto cifrado registrado desde la web | Modelo Qwen habilitado para la cuenta. |
| `ollama-local` | Ollama en Docker dentro de la red del proyecto | `none` | `qwen2.5:3b` recomendado para desarrollo y demostración local ágil; `qwen3:4b` queda como alternativa de mayor capacidad. |

La configuración conserva tipo, URL base validada, modelo, tiempos máximos, límite de salida, estado y referencia de credencial. Desde la corrección final del Sprint 2, la API key se registra una vez desde la web y PostgreSQL conserva únicamente su texto cifrado autenticado. La raíz criptográfica se genera automáticamente fuera de la base en el volumen Docker `secret_key_data`; React y auditoría nunca reciben el valor. La prueba de conexión se ejecuta exclusivamente desde FastAPI, usa una solicitud mínima sin datos del negocio y conserva sólo su resultado seguro y su auditoría. La respuesta de prueba se descarta.

En Sprint 2 no se generan propuestas BI ni se envían metadatos al LLM. Estas funciones quedan para el módulo `copilot`, el cual utilizará el mismo contrato y exigirá validación determinística y aprobación humana antes de cualquier ejecución.

## Consecuencias

- La aplicación puede cambiar entre nube y local sin acoplar ETL, metadatos o analítica a un proveedor.
- Las claves continúan fuera del código y de `.env`; la base conserva sólo el texto cifrado y la interfaz muestra únicamente su estado.
- Qwen Cloud, Gemini, Groq y Anthropic pueden tener costos, límites o modelos cambiantes; se deberán revisar las condiciones de la cuenta antes de realizar pruebas y configurar límites de consumo. Groq queda validado contra el host exclusivo `api.groq.com`, usa salida JSON Schema estricta para GPT-OSS y nunca habilita las herramientas remotas del proveedor. Anthropic queda restringido a `api.anthropic.com`, usa Messages API, no activa pensamiento extendido y valida localmente el JSON solicitado.
- Ollama evita dependencia de cuota cloud, pero exige recursos locales. Se inicia explícitamente con el perfil Docker `local-llm`, conserva el modelo por equipo en `ollama_models`, no expone un puerto público y no se descarga durante CI/CD ni se publica en GHCR. El valor predeterminado `qwen2.5:3b` usa un contexto de 4096 para que el contrato JSON del asistente disponga de espacio suficiente; se puede seleccionar un modelo de mayor capacidad cuando la infraestructura lo justifique.
- OpenAI se restringe al host `api.openai.com` y a Responses API. Cada solicitud usa
  `store: false`, sin herramientas remotas ni conversación persistida. El esquema de
  transporte se adapta al subconjunto estricto admitido y el resultado se valida
  contra el contrato original de la aplicación. Rechazos y salidas incompletas no
  se convierten en propuestas. No se reintenta una falta de saldo como si fuera
  una saturación temporal. `store: false` no equivale a una aprobación de Zero Data
  Retention ni modifica las condiciones de retención del proveedor.
- Groq compatible con OpenAI y OpenAI son servicios y credenciales distintos.
  La aplicación no puede consultar el saldo o confirmar un beneficio de suscripción
  mediante una prueba mínima. Esos datos se revisan en el panel de la organización.
- Agregar otro proveedor requerirá actualizar esta decisión, la especificación SPR-02, los controles de secretos y las pruebas.
