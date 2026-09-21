# ADR 0003: metadatos determinísticos y propuesta BI supervisada

- Estado: propuesta para aprobación
- Fecha: 2026-09-14

## Contexto

El título y los objetivos de la investigación requieren una construcción semiautomatizada y supervisada útil para una persona de negocio. La fuente debe configurarse desde la plataforma y no mediante archivos o cambios directos en la base interna. AdventureWorks contiene el esquema público de validación, pero el producto no debe depender de nombres codificados para ese caso. Un LLM puede interpretar metadatos técnicos en inglés y explicarlos en español, aunque su salida no es una fuente de verdad y puede contener referencias inventadas. Exigir al gerente seleccionar tablas o a un programador preparar consultas por cada análisis convertiría el prototipo en una herramienta técnica.

## Decisión

Se separan seis artefactos y responsabilidades:

1. **Conexión y secreto:** una persona administra desde la web campos validados de la conexión y su secreto cifrado. SQL Server es el primer adaptador funcional; otros motores requieren adaptadores posteriores bajo la misma interfaz.
2. **Instantánea de metadatos:** FastAPI introspecciona la conexión activa en modo de sólo lectura, normaliza el esquema, calcula un hash y persiste un documento canónico inmutable.
3. **Solicitud de negocio:** un gerente o analista expresa en español el objetivo, preguntas y periodo mediante una experiencia guiada; no selecciona tablas ni escribe SQL en el recorrido principal.
4. **Interpretación semántica:** FastAPI divide los metadatos en bloques y el LLM propone para cada fuente conceptos y explicaciones en español vinculados a identificadores técnicos. El backend descarta cualquier tabla, columna o relación inexistente y combina un alcance compacto. El analista puede comprobar el origen en una vista avanzada de sólo lectura.
5. **Propuesta BI:** el proveedor activo devuelve un JSON versionado y explicado en español con hecho, dimensiones, granularidad, medidas, KPIs, plan ETL declarativo, reglas, supuestos y advertencias.
6. **Validación y aprobación:** validadores determinísticos comprueban referencias y reglas; posteriormente una persona con permiso independiente aprueba o rechaza el significado de negocio. Ninguna de estas etapas genera o ejecuta SQL o ETL.

Las propuestas y decisiones son inmutables; un nuevo intento crea otro registro y conserva la historia. El Sprint 4 sólo podrá materializar artefactos a partir de una propuesta aprobada y deberá añadir un constructor determinístico, validadores, vista previa, confirmación y ejecutor backend. Las programadoras construyen ese motor una vez; no redactan consultas por solicitud y el usuario final no introduce SQL.

## Consecuencias

- Se puede demostrar qué metadatos originaron una propuesta y con qué proveedor/modelo se produjo.
- Una conexión y su credencial se administran sin edición manual; el secreto permanece cifrado y no recuperable desde la UI.
- Cambiar de LLM no modifica el contrato de dominio ni evita la validación.
- El procesamiento por bloques hace viable un modelo de contexto limitado sin fijar equivalencias exclusivas de AdventureWorks.
- Se incorporan persistencia, estados, permisos y UI adicionales, pero se evita una arquitectura de agentes o ejecución autónoma.
- La calidad de negocio sigue requiriendo revisión humana; una respuesta JSON válida no es una aprobación.
- Los datos sintéticos se usan en pruebas controladas de validadores y no como segunda fuente funcional.
- El gerente participa desde Sprint 3 formulando y revisando el análisis, pero recibe KPIs calculados y visualizaciones sólo después de materializar el datamart en Sprint 4.

## Alternativas descartadas

- Enviar todas las tablas y filas al LLM: excede contexto, aumenta riesgo y no es necesario.
- Permitir que el LLM produzca SQL ejecutable: se descarta porque aceptaría instrucciones no determinísticas. La aplicación del Sprint 4 lo construirá desde operaciones tipadas y plantillas autorizadas, y FastAPI lo ejecutará con permisos mínimos después de las validaciones y confirmaciones correspondientes.
- Pedir a un programador que prepare SQL por cada análisis: se descarta porque impediría que el producto funcionara de forma semiautomatizada para el usuario de negocio.
- Obligar al gerente a seleccionar tablas y relaciones: se descarta; el detalle técnico permanece disponible como consulta avanzada de sólo lectura.
- Codificar un glosario exclusivo de AdventureWorks como interpretación semántica: se descarta porque no demostraría la capacidad dinámica del LLM ni abriría el camino a futuras fuentes.
- Exigir editar `.env` o PostgreSQL para registrar una fuente o clave LLM: se descarta como operación del producto; los valores se administran mediante la web y los secretos se cifran.
- Mostrar motores todavía no implementados como opciones activas: se descarta porque produciría una capacidad engañosa; la interfaz de conectores es extensible, pero Sprint 3 habilita sólo SQL Server.
- Conservar sólo el texto de una conversación: no permite validar referencias ni reproducir el resultado.
- Codificar exclusivamente el modelo dimensional final sin propuesta: no demostraría la asistencia metodológica de IA planteada por la investigación.
