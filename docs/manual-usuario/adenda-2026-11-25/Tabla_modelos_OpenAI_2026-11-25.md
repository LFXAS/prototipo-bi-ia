# Modelos OpenAI: costo y evidencia para la demostración

Consulta de fuentes oficiales: 25 de noviembre de 2026. La disponibilidad depende
del proyecto de API y debe comprobarse en la aplicación. Todos los modelos de la
tabla declaran soporte de Responses y salidas estructuradas; eso no demuestra por
sí solo que produzcan una propuesta BI correcta.

Las tarifas son **USD por millón de tokens**, procesamiento Standard de texto y
contexto corto. La columna de ejemplo supone exactamente **10000 tokens de entrada
y 2000 de salida**. Es una estimación comparable, sin caché ni tokens adicionales
de razonamiento, reintentos, herramientas, impuestos o ajustes de divisa.

| Modelo de API | Entrada | Salida | Ejemplo estimado | Uso y evidencia en este proyecto |
| --- | ---: | ---: | ---: | --- |
| `gpt-6-luna` | 0,10 | 0,50 | 0,0020 | Alternativa económica vigente con razonamiento bajo; una prueba técnica de conexión y JSON estructurado. Sin ensayos de viabilidad, propuesta ni ETL. |
| `gpt-5.4-mini` | 0,75 | 4,50 | 0,0165 | Compatible según documentación; no ensayado aquí. |
| `gpt-6.1-terra` | 1,00 | 5,00 | 0,0200 | Compatible según documentación; no ensayado aquí. |
| `gpt-6.2-sol` | 2,00 | 10,00 | 0,0400 | Usado con razonamiento medio; flujo completo en AW 136/24 y WWI 135/23. |
| `gpt-6.2-astra` | 8,00 | 40,00 | 0,1600 | No ensayado aquí; no se recomienda para este presupuesto por su tarifa mayor. |

Fórmula del ejemplo: `(10000 / 1000000 × tarifa de entrada) + (2000 / 1000000 × tarifa de salida)`.
Las tarifas de Luna son **95% menores** que las de Sol en entrada y salida. No se
promete el mismo ahorro por respuesta: modelos diferentes pueden consumir distinta
cantidad de tokens o necesitar correcciones.

## Qué modelo se utilizó y qué puede afirmarse del gasto

Se utilizó **GPT-6.2 Sol con razonamiento medio** para los recorridos nuevos completos:

- AdventureWorks: propuesta **136**, ejecución **24**.
- WideWorldImporters: propuesta **135**, ejecución **23**.

No se conservaron tokens facturados ni costos medidos por cada solicitud en la
evidencia de esta campaña. La comparación de tarifas explica por qué Sol puede
resultar más caro, pero no permite atribuir toda variación del saldo a estas pruebas.
El importe real debe contrastarse con el registro de uso y cargos del proyecto en
OpenAI; una resta entre saldos no identifica por sí misma qué operación consumió cada parte.

## Cómo demostrar con un gasto controlado

1. Empiece con Luna y razonamiento bajo si necesita una operación nueva de IA.
2. Prepare antes el objetivo, las preguntas y la fuente correctos.
3. Para enseñar resultados, abra las propuestas aprobadas, expedientes ETL y paneles
   publicados. Abrirlos no requiere otra generación LLM.
4. Genere o consulte sólo lo necesario para la demostración. Sugerencias, revisión
   de viabilidad, propuestas y chat pueden consumir API.
5. Si aparece un fallo, explique el aviso y utilice la evidencia conservada. No
   cambie automáticamente a Sol ni a un esfuerzo mayor para intentar ocultarlo.
6. Compare consumo y saldo en OpenAI. El prototipo no consulta facturación ni cambia
   de modelo por su cuenta.

Luna ofrece una opción de menor tarifa, no una garantía de idéntica calidad. Su única
prueba técnica de conexión y JSON estructurado debe leerse con el informe QA; no se
ejecutó una revisión de viabilidad ni otro recorrido de generación o carga con Luna.

## Fuentes oficiales

- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna).
- [GPT-5.4 mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini).
- [GPT-6.1 Terra](https://developers.openai.com/api/docs/models/gpt-6.1-terra).
- [GPT-6.2 Sol](https://developers.openai.com/api/docs/models/gpt-6.2-sol).
- [GPT-6.2 Astra](https://developers.openai.com/api/docs/models/gpt-6.2-astra).

Los precios, modalidades y modelos pueden cambiar; actualice esta tabla antes de
usarla como una cotización vigente.
