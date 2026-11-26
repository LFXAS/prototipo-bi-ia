# Actualización editorial del capítulo 12: base de datos y linaje

Fecha del corte: 25 de noviembre de 2026, America/Guayaquil.

## Procedimiento y alcance

Se consultaron los catálogos PostgreSQL mediante la sesión interna del backend en Docker, con `engine.echo = False`, sin modificar la aplicación, los contenedores, la configuración o los datos. La inspección leyó nombres y tipos de columnas, esquemas, restricciones físicas y revisión Alembic. Se cotejaron únicamente identificadores, estados y referencias de los expedientes 21 a 24. La única fila de configuración leída fue el parámetro público de duración de sesión, sin credenciales. No se leyeron filas comerciales, documentos JSON completos de propuestas, tokens, claves o contraseñas.

El inventario se contrastó con los modelos ORM importados por la aplicación y con la cadena de archivos Alembic disponible dentro del contenedor. El archivo `actualizacion_bd_20261125.json` conserva los resultados técnicos seguros y su hora de inspección.

## Resultados comprobados

| Elemento | Corte vigente del 25 de noviembre | Referencia anterior del 18 de noviembre |
|---|---:|---:|
| Tablas totales | 93 | 83 |
| Columnas totales | 860 | 782 |
| Tablas de la aplicación, esquema `app` | 18 | 18 |
| Columnas del esquema `app` | 174 | 174 |
| Tablas analíticas | 74 | 64 |
| Claves foráneas físicas | 24, todas en `app` | 24, todas en `app` |
| Archivos Alembic | 20 | 19 |
| Revisión aplicada | `20261125_20` | `20261003_19` |

Los nombres de tablas y columnas de `app` coinciden con los 18 modelos y sus 174 columnas ORM. Hay una sola cabeza de migración, `20261125_20`, descendiente de `20261003_19`. La migración nueva inserta un parámetro con `ON CONFLICT (key) DO NOTHING`, sin crear tablas ni columnas ni reemplazar una elección existente.

El parámetro `AUTH_SESSION_MINUTES`, presentado como «Duración de la sesión (minutos)», está activo y tiene valor 60, valor inicial 60, mínimo 15 y máximo 240. Su efecto se aplica a nuevos inicios de sesión; no amplía tokens emitidos. Esta comprobación no constituye una prueba adicional del emisor de tokens: esa evidencia corresponde al informe de pruebas general.

| Fuente de demostración | Propuesta | Instantánea | Expediente | Estado técnico comprobado | Clasificación en el manual |
|---|---:|---:|---:|---|---|
| AdventureWorks | 136 | 2 | 24 | Propuesta aprobada y ejecución completada | Caso nuevo de esta edición |
| WideWorldImporters | 135 | 3 | 23 | Propuesta aprobada y ejecución completada | Caso nuevo de esta edición |
| AdventureWorks | 129 | 2 | 21 | Propuesta aprobada y ejecución completada | Referencia histórica conservada |
| WideWorldImporters | 131 | 3 | 22 | Propuesta aprobada y ejecución completada | Referencia histórica conservada |

Los destinos e23 y e24 tienen cinco tablas cada uno y, respectivamente, 36 y 42 columnas. Las diez tablas y 78 columnas explican la diferencia respecto del inventario anterior. Las dimensiones de e21, e22, e23 y e24 tienen clave primaria física. Sus tablas `fact_ventas` no tienen PK ni FK declaradas; las uniones de dimensiones y la etiqueta de ejecución se controlan mediante lógica del motor. El capítulo no presenta esos enlaces como restricciones físicas.

## Cambios editoriales

- Se actualizaron los conceptos iniciales, los totales y la revisión aplicada con datos comprobados.
- Se incorporó la duración configurable de sesión como una fila de `app.parameters`, con instrucciones de operación desde la interfaz.
- Se añadieron e23 y e24 al inventario de esquemas, y las cuatro correspondencias al cuadro de linaje.
- Se separaron explícitamente los casos nuevos y los históricos; los números locales no se presentan como requisitos del portable.
- Se preservaron las 28 fichas de diccionario: 18 tablas de `app` y diez tablas históricas de e21/e22. El diccionario analítico está rotulado como histórico y no se hace pasar por el de e23/e24.
- Se conservaron los siete diagramas y sus recursos relativos. Los dos diagramas de destinos e21/e22 se rotularon como referencias históricas; los de `app` siguen correspondiendo a las mismas entidades y restricciones actuales.
- Se añadieron criterios para reconocer fuente, propuesta, ejecución, filtros y significado comercial sin mezclar los resultados de ambos destinos.
- La lectura técnica de estados no se presenta como sustituto de la conciliación o de las pruebas operativas realizadas por el equipo principal.

## Archivos y comprobaciones

Fuente actualizada: `manual_latex/secciones/12_base_datos.tex`.

Copia editorial para la regeneración reproducible: `insumos/actualizacion_20261125/12_base_datos.tex`.

SHA-256 de ambos archivos:

`c2e83ce46e64cd3b2c53d118f8b3988a146722d60b4ee080fb4f0cb5b2081214`

Se comprobó la conservación de las 28 subsecciones de diccionario y los siete recursos de diagramas, así como el equilibrio de los entornos LaTeX de grupos, tablas y listas. No se compiló el manual desde esta subtarea para evitar interferir con la generación principal. La revisión visual del capítulo corresponde a la compilación y revisión final del equipo principal.
