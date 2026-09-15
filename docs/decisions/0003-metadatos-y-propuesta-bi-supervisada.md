# ADR 0003: metadatos determinísticos y propuesta BI supervisada

- Estado: propuesta para aprobación
- Fecha: 2026-09-14

## Contexto

El título y los objetivos de la investigación requieren una construcción semiautomatizada y supervisada. AdventureWorks contiene el esquema relacional público; un LLM puede interpretar ese esquema, pero su salida no es una fuente de verdad y puede contener referencias inventadas. El futuro ETL necesita una entrada reproducible y aprobada, no una conversación ni SQL libre.

## Decisión

Se separan cuatro artefactos y responsabilidades:

1. **Instantánea de metadatos:** FastAPI introspecciona AdventureWorks en modo de sólo lectura, normaliza el esquema, calcula un hash y persiste un documento canónico inmutable.
2. **Paquete LLM:** FastAPI deriva de la instantánea un alcance compacto confirmado por una persona. Sólo contiene metadatos permitidos.
3. **Propuesta BI:** el proveedor activo devuelve un JSON versionado con hecho, dimensiones, granularidad, medidas, KPIs, plan ETL declarativo, reglas, supuestos y advertencias.
4. **Aprobación:** validadores determinísticos comprueban la propuesta; posteriormente una persona con permiso independiente aprueba o rechaza. Ninguna de estas etapas ejecuta SQL o ETL.

Las versiones aprobadas son inmutables y una sustitución conserva la historia. El Sprint 4 sólo podrá materializar artefactos a partir de una propuesta aprobada y deberá añadir sus propios validadores, vista previa y confirmación.

## Consecuencias

- Se puede demostrar qué metadatos originaron una propuesta y con qué proveedor/modelo se produjo.
- Cambiar de LLM no modifica el contrato de dominio ni evita la validación.
- El alcance seleccionado reduce el consumo y hace viable Ollama local con contexto limitado.
- Se incorporan persistencia, estados, permisos y UI adicionales, pero se evita una arquitectura de agentes o ejecución autónoma.
- La calidad de negocio sigue requiriendo revisión humana; una respuesta JSON válida no es una aprobación.
- Los datos sintéticos se usan en pruebas controladas de validadores y no como segunda fuente funcional.

## Alternativas descartadas

- Enviar todas las tablas y filas al LLM: excede contexto, aumenta riesgo y no es necesario.
- Ejecutar SQL propuesto por IA: contradice el alcance y elimina el control determinístico.
- Conservar sólo el texto de una conversación: no permite validar referencias ni reproducir el resultado.
- Codificar exclusivamente el modelo dimensional final sin propuesta: no demostraría la asistencia metodológica de IA planteada por la investigación.
