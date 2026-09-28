# Comparativa integral Groq vs. Claude para propuestas BI

- Fecha de ejecución: **27 de septiembre de 2026**
- Fuente: AdventureWorks local, instantánea `#2`
- Dominio: ventas
- Propósito: seleccionar proveedor y nivel operativo para el asistente de datamart
- Seguridad: se usaron credenciales cifradas ya registradas; no se imprimieron claves,
  prompts internos, filas de negocio ni trazas de razonamiento

## 1. Pregunta experimental

¿Qué combinación ofrece mayor probabilidad de producir una propuesta BI completa,
trazable y aprobable al repetir la misma necesidad con el contrato y los validadores
determinísticos de la plataforma?

La prueba no considera suficiente que el botón **Probar conexión** responda correctamente.
También exige generación completa, JSON interpretable, referencias existentes, procedencia
`tabla.columna`, fórmulas controladas, cobertura de requisitos y cero errores bloqueantes.

## 2. Entrada controlada

Las cuatro ejecuciones usaron la misma necesidad de la propuesta `#73`, periodicidad
mensual y las mismas seis preguntas de negocio: evolución, productos, clientes,
territorios, costos/rentabilidad y comparación por unidad. La comprobación previa encontró
9 requisitos directos, 10 derivables, 0 ambiguos y 0 no disponibles.

No se aprobó ninguna propuesta experimental ni se ejecutó ETL. Los registros `#78` a
`#81` se conservaron sólo como evidencia auditable. Al terminar se restauró Claude Haiku
4.5 en nivel bajo como configuración activa y se volvió a probar su conexión.

## 3. Resultados observados

| Proveedor y modelo | Nivel configurado | Conexión | Generación integral | Tiempo de propuesta | Resultado determinístico |
|---|---|---:|---|---:|---|
| Groq `openai/gpt-oss-120b` | medio | correcta, 1 s | propuesta `#78` | 3 s | `provider_failed`: no completó el JSON estructurado dentro del presupuesto |
| Groq `openai/gpt-oss-120b` | alto | correcta, 1 s | propuesta `#79` | 21 s | `provider_failed`: límite temporal de solicitudes o tokens tras reintentos acotados |
| Claude `claude-haiku-4-5-20251001` | medio | correcta, 1 s | propuesta `#80` | 21 s | contrato completo, pero bloqueado por 2 errores y 3 advertencias |
| Claude `claude-haiku-4-5-20251001` | alto | correcta, 1 s | propuesta `#81` | 21 s | contrato completo, pero bloqueado por 2 errores y 3 advertencias |

Las propuestas Claude incluyeron 10 tablas, cuatro dimensiones y seis medidas. Las reglas
rechazaron en ambos casos una medida de clientes que usó `CustomerID` sin una ruta válida
desde el hecho y una procedencia que no coincidía con referencias verificadas. También
excluyeron recetas de costo o KPI dependientes que no pudieron compilarse de forma segura.
Medio produjo 13 KPI y alto 11; la diferencia no implica mayor razonamiento efectivo.

## 4. Interpretación de los niveles

Groq admite `reasoning_effort` bajo, medio y alto, pero el razonamiento comparte el
presupuesto de finalización y la cuenta está sujeta a límites temporales. Una prueba corta
puede pasar aunque el contrato BI completo se trunque o alcance cuota. Por ello conexión
correcta no equivale a propuesta funcional.

El adaptador Anthropic vigente omite pensamiento extendido para Haiku 4.5. Los valores
medio y alto quedaron registrados para el experimento, pero no se enviaron como un
parámetro de razonamiento distinto; ambas celdas prueban variabilidad de generación y la
eficacia del validador, no una comparación auténtica de esfuerzo Claude. Para este modelo
la interfaz debe recomendar bajo/mínimo mientras no exista una traducción de capacidad
implementada y probada.

## 5. Contraste con la línea base válida

| Línea base | Estado | Errores | Advertencias | Evidencia funcional |
|---|---|---:|---:|---|
| Groq bajo, propuesta `#73` | aprobada | 0 | 0 | ejecución `#9`, 121.317 filas conciliadas, KPI financieros completos |
| Claude bajo, propuesta `#77` | lista para revisar | 0 | 7 | contrato válido; costos y KPI inseguros fueron excluidos antes del ETL |

La comparación demuestra que la estandarización no significa aceptar literalmente la
salida de cualquier modelo. Significa conservar la misma necesidad, normalizar recetas y
bloquear referencias o fórmulas no demostrables. En esta prueba, los errores Claude no se
materializaron y los fallos Groq no alteraron el datamart publicado.

## 6. Decisión recomendada

1. **Proveedor principal para generar el datamart:** Groq GPT-OSS 120B con nivel bajo.
   Es la única combinación de la evidencia vigente que produjo la necesidad completa sin
   errores ni advertencias y llegó a una ejecución totalmente conciliada.
2. **Proveedor de respaldo:** Claude Haiku 4.5 con nivel bajo/mínimo. Es útil cuando Groq
   está saturado y suele devolver un contrato completo, pero requiere atender las
   advertencias y no debe aprobarse si la cobertura financiera queda parcial.
3. **No usar medio/alto como valor operativo predeterminado** para la generación integral.
   En Groq elevan el riesgo de agotar salida o cuota; en el adaptador Claude actual no
   representan un esfuerzo distinto.
4. Mantener siempre la validación determinística, revisión de cobertura y aprobación
   humana. Cambiar de proveedor no autoriza a relajar referencias, fórmulas ni grano.

## 7. Límites del experimento

- Se evaluó un modelo por proveedor y una sola necesidad compleja de ventas.
- Los tiempos son observaciones de esta ejecución local, no un benchmark contractual.
- No se comparó costo monetario exacto porque la plataforma no almacena facturación del
  proveedor y exponer paneles externos o credenciales estaría fuera del alcance.
- Una repetición puede variar por límites de cuenta y naturaleza generativa; los registros
  auditables y las reglas determinísticas permiten repetir y contrastar el resultado.

## 8. Repetición posterior y endurecimiento del contrato

Una nueva ejecución con la misma necesidad y Groq bajo expuso un problema de la
plataforma, no del modelo de negocio. En las propuestas `#82` y `#83`, Groq generó cuatro
referencias técnicas reales para un candidato, mientras el esquema de transporte aceptaba
como máximo tres. El proveedor devolvió `json_validate_failed` y la interfaz lo presentó
incorrectamente como falta de presupuesto y luego como ausencia de alcance verificable.

Se sustituyó ese máximo artificial por un esquema construido automáticamente con las
referencias reales de cada bloque. Los adaptadores conservan diferencias de transporte
- JSON Schema estricto, esquema del proveedor o instrucción más validación local -, pero
comparten el mismo contrato BI y las mismas reglas determinísticas. También se corrigió la
política de reintentos para respetar `retry-after` hasta 45 segundos y se añadió una ruta de
recuperación que conserva la necesidad cuando falla el proveedor.

La primera repetición corregida (`#84`) produjo seis conceptos y diez tablas, pero se
detuvo por límite temporal antes del plano final. La siguiente (`#85`) completó el JSON y
permitió detectar que la identidad del cliente necesitaba recorrer dos relaciones
declaradas. La expansión se generalizó sin depender de nombres de tablas y la propuesta
`#86` quedó `ready_for_review` con 0 errores, 0 advertencias, 6 conceptos y 14 tablas. La
dimensión cliente resolvió variantes comprobadas desde `Person.Person` y `Sales.Store`, y
las medidas cubrieron ventas, unidades, descuento monetario y costo. No se aprobó la
propuesta ni se ejecutó ETL.

Este resultado refuerza la decisión: la estandarización no consiste en escribir prompts
distintos por modelo, sino en adaptar el protocolo automáticamente, comprobar toda salida
contra la instantánea y resolver de forma determinística aquello que la evidencia permite.
