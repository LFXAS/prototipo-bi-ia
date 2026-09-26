# SPR-05-03: calidad semántica y resolución de entidades

- Estado: **implementada y verificada en el dominio de ventas**
- Dependencias: metadatos del Sprint 3 y materializador del Sprint 4
- Usuario operativo: analista BI

## 1. Problema y objetivo

La conciliación cuantitativa no garantiza que una dimensión sea útil. Una entidad puede cargar correctamente sus claves y, sin embargo, carecer del nombre que una persona necesita para reconocerla. La ejecución 6 evidenció este riesgo: `dim_cliente` conservó `CustomerID`, `PersonID`, `StoreID` y `AccountNumber`, pero no recorrió las relaciones hacia los atributos descriptivos de la persona o la tienda. El tablero terminó mostrando números de cuenta.

La solución debe ser general. No buscará literalmente tablas denominadas `Customer`, `Person` o `Store`; analizará el concepto de negocio, el grafo de relaciones, claves, tipos, cardinalidad, cobertura y atributos descriptivos para construir una identidad legible y verificable.

## 2. Regla de población y regla de identidad

Son decisiones distintas:

- **Población**: la dimensión contiene las entidades que participan en el hecho de negocio. En AdventureWorks, `Sales.Customer` es la población comercial correcta; no corresponde reemplazarla por todas las filas de `Person.Person`, que también contiene empleados y otros individuos.
- **Identidad**: la etiqueta visible se obtiene recorriendo relaciones válidas. Para una fila individual podrá combinar atributos de persona; para una organización utilizará su razón o nombre relacionado; si ninguna rama aplica, conserva una etiqueta de respaldo explícita y registra la incidencia.

Por tanto, un `PersonID` nulo no es automáticamente un error cuando existe otra rama válida como `StoreID`. Sí es un error publicar la clave técnica como si fuera el nombre sin explicar la falta de identidad descriptiva.

## 3. Detección automática estándar

El resolutor debe:

1. partir de la dimensión propuesta y su función semántica declarada por la IA;
2. recorrer relaciones verificadas de la instantánea con profundidad limitada y sin adivinar joins;
3. encontrar atributos textuales candidatos mediante función semántica, perfil agregado, cobertura, cardinalidad y patrones de identificador;
4. diferenciar persona, organización u otra variante mediante las ramas de relación y nulabilidad;
5. proponer una receta controlada `concat`, `coalesce` o `first_non_empty` sobre referencias existentes;
6. calcular cobertura total y por rama con consultas de sólo lectura;
7. rechazar como etiqueta principal códigos, cuentas, hashes, correos o identificadores, salvo respaldo declarado;
8. comprobar unicidad de la clave de negocio y que el enriquecimiento no multiplique filas;
9. materializar nombre visible, tipo de entidad, componentes auditables y linaje;
10. bloquear la publicación ejecutiva cuando la cobertura no alcance el umbral aprobado.

Las muestras de valores se usan sólo dentro del motor determinístico y la vista autorizada; no se envían al LLM.

## 4. Resolución automática y supervisada

- **Automática**: una única ruta satisface relación, cardinalidad, cobertura y tipo. El sistema la aplica, muestra el resultado y conserva evidencia.
- **Supervisada**: hay varias rutas válidas o cobertura incompleta. La plataforma presenta candidatos, relación, razón, cobertura, efecto sobre filas y una muestra limitada antes/después.
- **Bloqueada**: no existe ruta verificable o una unión multiplica el grano. No se materializa ni publica hasta corregir la fuente, cambiar el concepto o aprobar una alternativa permitida.

El analista no escribe SQL. Puede elegir una ruta verificada, ordenar componentes de una etiqueta, aceptar una rama o excluir un atributo. La decisión genera una nueva versión de propuesta; nunca altera retrospectivamente el contrato aprobado ni una ejecución histórica.

## 5. Herramienta visual dentro de la plataforma

El paso **Revisar identidad de dimensiones** mostrará:

- entidad y función de negocio;
- población base y número de claves distintas;
- grafo simplificado de relaciones comprobadas;
- etiqueta propuesta y sus componentes;
- cobertura total, cobertura por rama, nulos legítimos, nulos sin resolver y duplicación potencial;
- muestra limitada de clave, tipo y etiqueta resultante;
- recomendación automática, riesgos y acción concreta;
- botón **Aplicar corrección a una nueva versión** cuando requiera decisión.

La interfaz debe ser comprensible para un analista nuevo, con glosario contextual y detalles técnicos plegables. Puede existir una consulta controlada construida por la aplicación, pero no una consola de SQL libre como flujo normal.

## 6. Contrato de propuesta y materialización

Cada dimensión que se use en visualizaciones declara:

- `semantic_role`;
- `business_key`;
- `display_label` con receta tipada y componentes;
- `entity_variants` cuando existan ramas polimórficas;
- rutas de relación por claves verificadas;
- umbral de cobertura;
- respaldo permitido y explicación;
- atributos de linaje.

El compilador reproduce la consulta desde ese contrato y comprueba nuevamente relaciones, cardinalidad y cobertura antes de reemplazar el datamart.

## 7. Seguridad y auditoría

Consultar diagnóstico requiere `metadata.semantic_resolution.read`; crear una versión corregida requiere `metadata.semantic_resolution.manage`. Las muestras se limitan, se auditan y se restringen al analista. La IA no recibe nombres de personas ni valores de negocio. Toda decisión registra usuario, propuesta origen, propuesta nueva, ruta, receta, métricas y fecha.

## 8. Criterios de aceptación

- [x] La plataforma distingue población comercial e identidad descriptiva.
- [x] El resolutor usa relaciones, perfiles y función semántica, no coincidencia literal del nombre de tabla.
- [x] Una relación uno-a-muchos que altera el grano queda bloqueada.
- [x] Una dimensión ejecutiva sin etiqueta descriptiva suficiente no se publica como correcta.
- [x] El caso de ventas resuelve personas y tiendas en una misma etiqueta de cliente, conserva claves y alcanza cobertura verificable.
- [x] Los `PersonID` nulos respaldados por otra rama se explican como válidos; los no resueltos se cuentan.
- [x] El analista puede inspeccionar cobertura, origen y muestra controlada y generar una nueva versión sin DBeaver ni SQL.
- [x] La corrección produjo la propuesta 54 y la ejecución 7; las versiones y ejecuciones previas permanecen auditables.
- [x] El tablero muestra nombres descriptivos y sólo usa cuenta/clave como respaldo visible y marcado.
- [x] Pruebas con referencias neutrales como `SubjectRef` demuestran que la solución no depende de nombres literales de cliente o persona.

## 9. Evidencia esperada

La ejecución 7 materializó 19820 clientes: 19119 personas y 701 organizaciones, con cero etiquetas descriptivas vacías. `dim_cliente` conserva `nombre_cliente`, `tipo_cliente`, claves originales y linaje; el panel y los reportes muestran nombres como Roger Harui o Andrew Dixon en lugar de números de cuenta. El expediente anterior permanece disponible como evidencia del defecto detectado y de su corrección.
