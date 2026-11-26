# SPR-06-02: continuidad de operación y OpenAI

Fecha: 25 de noviembre de 2026. Incremento correctivo del flujo multifuente;
no constituye evidencia de compatibilidad con motores de datos no implementados.
Solicitud: correcciones de navegación, sesión y selección de preguntas del PDF
aportado por el tutor, más integración de OpenAI en la configuración LLM.

## Problemas observados

- La recarga inicializaba la página en Inicio y las transiciones perdían su origen.
- Entrar desde la preparación de Inicio o desde Consultar respaldo no ofrecía
  retorno al punto de partida.
- El vencimiento de sesión se descubría al recibir un error de API. El usuario sustituyó la indicación inicial del PDF por una duración mayor y
  parametrizable desde la plataforma.
- Un borrador conservaba códigos de preguntas retiradas del catálogo. El servidor
  impedía correctamente su uso antes de llamar al proveedor, pero el mensaje no
  permitía resolver la selección desde la interfaz. La captura de WideWorldImporters
  muestra este problema; no demuestra un fallo del modelo ni corrupción del datamart.
- OpenAI aún no estaba registrado como proveedor propio. Groq compatible con OpenAI
  es un servicio distinto y no permite utilizar créditos de la API de OpenAI.

## Contrato y aceptación

1. Conservar módulo por pestaña y usuario al recargar; restaurarlo sólo si la cuenta
   mantiene permiso. No persistir tokens en la navegación ni abrir rutas arbitrarias.
2. Ofrecer Atrás sólo en entradas guiadas. Desde Revisar configuración volver al
   paso previo de preparación; desde Crear propuesta al Inicio; desde Consultar
   respaldo al panel. Entrar por el menú lateral no debe añadir ese botón.
3. Emitir JWT con fecha de emisión y expiración según **Duración de la sesión
   (minutos)**, parámetro `AUTH_SESSION_MINUTES`, inicial 60 y rango 15–240.
   Cada login consulta el valor vigente. El cambio sólo afecta tokens nuevos; no
   renueva los existentes ni extiende la sesión por actividad. El entorno conserva
   un valor de respaldo, pero el parámetro activo tiene precedencia.
4. Comunicar el vencimiento sin esperar otra solicitud y conservar un borrador mínimo
   recuperable. La autorización efectiva permanece en FastAPI, no en el reloj del cliente.
5. Reconciliar la selección mutable contra el catálogo vigente de su propia fuente:
   conservar texto y opciones válidas, explicar las opciones retiradas, invalidar
   viabilidad y consentimiento cuando cambie el alcance y exigir otra revisión.
   No sustituir preguntas por etiquetas similares ni modificar propuestas históricas.
6. Backend comprueba selección y periodicidad antes de cualquier llamada LLM, aunque
   un cliente antiguo envíe un borrador inválido. La recuperación no debilita esa puerta.
7. Registrar `openai-cloud` con URL permitida `https://api.openai.com/v1`, credencial
   cifrada y modelo editable. No usar una API key de OpenAI en Groq ni viceversa.
8. Usar Responses API con `store: false`, contrato estructurado y validación local
   posterior. Manejar rechazo, salida incompleta, cuota, acceso y errores sin mostrar
   claves ni respuestas crudas. Nunca activar otro proveedor de forma silenciosa.
9. Preset económico final: `gpt-6-luna`, esfuerzo bajo, por petición posterior
   del usuario de reducir gasto. Se verificó su conexión y salida estructurada.
   Los dos recorridos completos se realizaron con `gpt-6.2-sol`, esfuerzo medio;
   se conservan atribuidos a ese modelo. El acceso depende de la organización.
   No hay escalamiento automático a Sol ni afirmación de igual calidad o costo
   por tarea. La tabla de precios y pruebas distingue ambos alcances.
10. La misma canalización debe comprobarse con AdventureWorks y WideWorldImporters;
    no se añaden excepciones por sus nombres, idioma o identificadores de catálogo.

## Evidencias y límites

Regresiones automatizadas y auditoría operativa se registran en
`docs/testing/qa-continuidad-openai-2026-11-25.md` con su resultado efectivo.
Las pruebas de transporte simuladas no se contarán como llamadas reales a OpenAI.
La clave será registrada por el usuario desde la pantalla; no forma parte de esta
especificación, Git, documentos, capturas ni archivos de prueba.

## Fuentes oficiales consultadas

- [OpenAI Responses API](https://developers.openai.com/api/docs/guides/text).
- [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).
- [GPT-6.2 Sol](https://developers.openai.com/api/docs/models/gpt-6.2-sol).
- [Créditos para suscriptores elegibles](https://developers.openai.com/api/docs/guides/chatgpt-api-credits).

Los precios, modelos y condiciones de créditos son externos y pueden variar.

### Cambio de requisito durante la revisión

La solicitud directa posterior del usuario pide más tiempo y parametrización.
Sustituye el máximo de diez minutos del PDF inicial. No se conserva ese techo en
la implementación final. La migración `20261125_20` incorpora el parámetro sin
restablecer datos existentes; el seed mantiene su valor elegido por administración.

## Cobertura operativa y conservación de evidencia

El ensayo detectó dos causas internas: recorte de referencias comprobadas antes
de enviar el contrato y omisión de un KPI solicitado aunque existía la medida.
El prompt v9 preserva evidencia revisada en todos los paquetes. Compilación 6
requiere una salida analítica seleccionable para métricas solicitadas y puede
completar una agregación única y segura antes de la decisión humana. Una exclusión
posterior no se repone silenciosamente. Los históricos de reglas 1–5 siguen
congelados. Véase la adenda SDD específica de cobertura y el informe QA del corte.
