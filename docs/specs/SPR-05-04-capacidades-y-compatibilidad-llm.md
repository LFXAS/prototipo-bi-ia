# SPR-05-04: capacidades y compatibilidad de proveedores LLM

- Estado: **implementada para los proveedores y modelos registrados**
- Dependencia: configuración LLM del Sprint 2 y proveedores del Sprint 3
- Proveedores actuales: Gemini Cloud, Groq Cloud y Ollama local

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

## 6. Resultado de implementación

El rechazo HTTP 400 no se debía a que Groq prohibiera el esfuerzo medio o alto para `openai/gpt-oss-120b`, sino a que la prueba consumía su presupuesto reducido antes de completar el JSON. La prueba pasó a reservar 256 tokens de finalización, usa `reasoning_format: hidden` y la generación asigna un presupuesto acorde al contrato. La conexión real se comprobó con esfuerzo alto y el copiloto analítico respondió con Groq sin exponer la traza de razonamiento.
