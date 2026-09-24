# ADR 0002: configuración de proveedor LLM

- Estado: aceptada
- Fecha: 2026-09-04; ampliada el 2026-09-23

## Contexto

El prototipo BI asistido por IA necesita una conexión LLM que pueda funcionar tanto en una demostración local reproducible como con servicios cloud. La clave de un proveedor no puede quedar en texto legible en PostgreSQL, React, archivos versionados ni auditoría. La tesis tampoco debe depender de que una cuota gratuita o un modelo cloud específico continúe disponible.

## Decisión

Sprint 2 implementará una única configuración LLM activa, administrable por un permiso específico. Sólo se admiten inicialmente estos adaptadores internos de FastAPI:

| Tipo | Servicio | Referencia de secreto | Modelo/configuración inicial |
|---|---|---|---|
| `gemini` | Gemini API Cloud | Secreto cifrado registrado desde la web | Modelo Gemini Flash permitido por la cuenta. |
| `groq-cloud` | Groq Cloud, API compatible con OpenAI | Secreto cifrado registrado desde la web | `openai/gpt-oss-120b`; razonamiento bajo recomendado para equilibrar rapidez y profundidad. |
| `qwen-cloud` | Alibaba Cloud Model Studio / DashScope | Secreto cifrado registrado desde la web | Modelo Qwen habilitado para la cuenta. |
| `ollama-local` | Ollama en Docker dentro de la red del proyecto | `none` | `qwen2.5:3b` recomendado para desarrollo y demostración local ágil; `qwen3:4b` queda como alternativa de mayor capacidad. |

La configuración conserva tipo, URL base validada, modelo, tiempos máximos, límite de salida, estado y referencia de credencial. Desde la corrección final del Sprint 2, la API key se registra una vez desde la web y PostgreSQL conserva únicamente su texto cifrado autenticado. La raíz criptográfica se genera automáticamente fuera de la base en el volumen Docker `secret_key_data`; React y auditoría nunca reciben el valor. La prueba de conexión se ejecuta exclusivamente desde FastAPI, usa una solicitud mínima sin datos del negocio y conserva sólo su resultado seguro y su auditoría. La respuesta de prueba se descarta.

En Sprint 2 no se generan propuestas BI ni se envían metadatos al LLM. Estas funciones quedan para el módulo `copilot`, el cual utilizará el mismo contrato y exigirá validación determinística y aprobación humana antes de cualquier ejecución.

## Consecuencias

- La aplicación puede cambiar entre nube y local sin acoplar ETL, metadatos o analítica a un proveedor.
- Las claves continúan fuera del código y de `.env`; la base conserva sólo el texto cifrado y la interfaz muestra únicamente su estado.
- Qwen Cloud, Gemini y Groq pueden tener costos, límites o modelos cambiantes; se deberán revisar las condiciones de la cuenta antes de realizar pruebas y configurar límites de consumo. Groq queda validado contra el host exclusivo `api.groq.com`, usa salida JSON Schema estricta para GPT-OSS y nunca habilita las herramientas remotas del proveedor.
- Ollama evita dependencia de cuota cloud, pero exige recursos locales. Se inicia explícitamente con el perfil Docker `local-llm`, conserva el modelo por equipo en `ollama_models`, no expone un puerto público y no se descarga durante CI/CD ni se publica en GHCR. El valor predeterminado `qwen2.5:3b` usa un contexto de 4096 para que el contrato JSON del asistente disponga de espacio suficiente; se puede seleccionar un modelo de mayor capacidad cuando la infraestructura lo justifique.
- Agregar otro proveedor requerirá actualizar esta decisión, la especificación SPR-02, los controles de secretos y las pruebas.
