# ADR 0003: metadatos determinísticos y propuesta BI supervisada

- Estado: propuesta para aprobación
- Fecha: 2026-09-14

## Contexto

El título y los objetivos de la investigación requieren una construcción semiautomatizada y supervisada útil para una persona de negocio. AdventureWorks contiene el esquema relacional público; un LLM puede interpretarlo, pero su salida no es una fuente de verdad y puede contener referencias inventadas. Exigir al gerente seleccionar tablas o a un programador preparar consultas por cada análisis convertiría el prototipo en una herramienta técnica. El futuro ETL necesita una entrada reproducible y aprobada, no una conversación ni SQL libre.

## Decisión

Se separan cuatro artefactos y responsabilidades:

1. **Instantánea de metadatos:** FastAPI introspecciona AdventureWorks en modo de sólo lectura, normaliza el esquema, calcula un hash y persiste un documento canónico inmutable.
2. **Solicitud de negocio:** un gerente o analista expresa en español el objetivo, preguntas, periodo y dimensiones mediante una experiencia guiada; no selecciona tablas ni escribe SQL en el recorrido principal.
3. **Alcance y paquete LLM:** FastAPI usa el perfil y glosario `adventureworks-sales-v1` para derivar un alcance compacto mediante relaciones declaradas. Un analista puede ajustarlo en modo avanzado. Sólo se envían la solicitud normalizada y metadatos permitidos.
4. **Propuesta BI:** el proveedor activo devuelve un JSON versionado y explicado en español con hecho, dimensiones, granularidad, medidas, KPIs, plan ETL declarativo, reglas, supuestos y advertencias.
5. **Validación y aprobación:** validadores determinísticos comprueban referencias y reglas; posteriormente una persona con permiso independiente aprueba o rechaza el significado de negocio. Ninguna de estas etapas genera o ejecuta SQL o ETL.

Las versiones aprobadas son inmutables y una sustitución explícita conserva la historia. El Sprint 4 sólo podrá materializar artefactos a partir de una propuesta aprobada y deberá añadir un constructor determinístico, validadores, vista previa, confirmación y ejecutor backend. Las programadoras construyen ese motor una vez; no redactan consultas por solicitud y el usuario final no introduce SQL.

## Consecuencias

- Se puede demostrar qué metadatos originaron una propuesta y con qué proveedor/modelo se produjo.
- Cambiar de LLM no modifica el contrato de dominio ni evita la validación.
- El alcance derivado reduce el consumo y hace viable Ollama local con contexto limitado sin trasladar complejidad técnica al gerente.
- Se incorporan persistencia, estados, permisos y UI adicionales, pero se evita una arquitectura de agentes o ejecución autónoma.
- La calidad de negocio sigue requiriendo revisión humana; una respuesta JSON válida no es una aprobación.
- Los datos sintéticos se usan en pruebas controladas de validadores y no como segunda fuente funcional.
- El gerente participa desde Sprint 3 formulando y revisando el análisis, pero recibe KPIs calculados y visualizaciones sólo después de materializar el datamart en Sprint 4.

## Alternativas descartadas

- Enviar todas las tablas y filas al LLM: excede contexto, aumenta riesgo y no es necesario.
- Permitir que el LLM produzca SQL ejecutable: se descarta porque aceptaría instrucciones no determinísticas. La aplicación del Sprint 4 lo construirá desde operaciones tipadas y plantillas autorizadas, y FastAPI lo ejecutará con permisos mínimos después de las validaciones y confirmaciones correspondientes.
- Pedir a un programador que prepare SQL por cada análisis: se descarta porque impediría que el producto funcionara de forma semiautomatizada para el usuario de negocio.
- Obligar al gerente a seleccionar tablas y relaciones: se descarta como recorrido principal; el detalle técnico permanece disponible únicamente como modo avanzado.
- Conservar sólo el texto de una conversación: no permite validar referencias ni reproducir el resultado.
- Codificar exclusivamente el modelo dimensional final sin propuesta: no demostraría la asistencia metodológica de IA planteada por la investigación.
