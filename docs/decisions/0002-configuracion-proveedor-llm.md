# ADR 0002: configuración de proveedor LLM

- Estado: aceptada
- Fecha: 2026-09-04

## Contexto

El prototipo BI asistido por IA necesita una conexión LLM que pueda funcionar tanto en una demostración local reproducible como con servicios cloud. La clave de un proveedor no puede quedar almacenada en PostgreSQL, React, archivos versionados ni auditoría. La tesis tampoco debe depender de que una cuota gratuita o un modelo cloud específico continúe disponible.

## Decisión

Sprint 2 implementará una única configuración LLM activa, administrable por un permiso específico. Sólo se admiten inicialmente estos adaptadores internos de FastAPI:

| Tipo | Servicio | Referencia de secreto | Modelo/configuración inicial |
|---|---|---|---|
| `gemini` | Gemini API Cloud | `GEMINI_API_KEY` | Modelo Gemini Flash permitido por la cuenta. |
| `qwen-cloud` | Alibaba Cloud Model Studio / DashScope | `DASHSCOPE_API_KEY` | Modelo Qwen habilitado para la cuenta. |
| `ollama-local` | Ollama en Docker dentro de la red del proyecto | `none` | `qwen3:4b` recomendado para la demostración local. |

Sólo se persisten valores no secretos: tipo, URL base validada, modelo, tiempos máximos, límite de salida, estado y referencia de credencial. La prueba de conexión se ejecuta exclusivamente desde FastAPI, usa una solicitud mínima sin datos del negocio y conserva sólo su resultado seguro y su auditoría. La respuesta de prueba se descarta.

En Sprint 2 no se generan propuestas BI ni se envían metadatos al LLM. Estas funciones quedan para el módulo `copilot`, el cual utilizará el mismo contrato y exigirá validación determinística y aprobación humana antes de cualquier ejecución.

## Consecuencias

- La aplicación puede cambiar entre nube y local sin acoplar ETL, metadatos o analítica a un proveedor.
- Las claves continúan fuera del código y de la base; la interfaz sólo muestra si la referencia requerida está disponible.
- Qwen Cloud y Gemini pueden tener costos, límites o modelos cambiantes; se deberán revisar las condiciones de la cuenta antes de realizar pruebas y configurar límites de consumo.
- Ollama evita dependencia de cuota cloud, pero exige recursos locales y su perfil Docker no se expone públicamente.
- Agregar otro proveedor requerirá actualizar esta decisión, la especificación SPR-02, los controles de secretos y las pruebas.
