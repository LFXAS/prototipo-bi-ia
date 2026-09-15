# SPR-03-01: conexión e introspección de AdventureWorks

- Estado: **borrador para revisión y aprobación**.
- Pertenece a: [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md).
- Fecha de creación: 2026-09-14.
- Rama prevista de implementación: `feature/sprint-03-metadata-copilot`.
- PR de implementación: pendiente.

## 1. Problema y objetivo

El prototipo ya puede probar técnicamente la conexión a AdventureWorks, pero todavía no ofrece una representación versionada de su esquema ni una experiencia que permita comprender las estructuras disponibles. El Copiloto no puede proponer un modelo BI de manera trazable sin una instantánea determinística que sea su única fuente técnica de verdad.

El objetivo es implementar una introspección de sólo lectura que obtenga tablas, columnas, tipos, nulabilidad, claves primarias, claves foráneas y relaciones declaradas; normalice esos metadatos; calcule una huella reproducible; y conserve una instantánea inmutable en PostgreSQL.

## 2. Alcance y exclusiones

### Incluido

- Fuente fija `adventureworks`, configurada exclusivamente mediante variables de entorno.
- Prueba de conectividad y confirmación segura del modo de sólo lectura.
- Introspección de esquemas y tablas de usuario, columnas, tipos, nulabilidad, claves primarias y foráneas.
- Normalización, orden estable y hash SHA-256 del documento canónico.
- Persistencia de instantáneas inmutables y consulta de la última captura.
- Búsqueda, filtros y detalle de tabla a partir de la instantánea, no mediante consultas repetidas al origen.
- Métricas técnicas: cantidad de esquemas, tablas, columnas y relaciones.
- Glosario `adventureworks-sales-v1` que relaciona conceptos visibles en español con identificadores técnicos sin modificar el origen.

### Excluido

- Filas o muestras de datos, mínimos, máximos, cardinalidad, perfiles estadísticos o datos personales.
- Vistas, procedimientos, funciones, disparadores, índices no necesarios y código fuente SQL.
- Configuración de otra fuente o edición de credenciales desde la aplicación.
- Cambios en AdventureWorks y consultas de negocio.
- Inferencia de relaciones que no estén declaradas; podrán registrarse como advertencias futuras, no como hechos.

## 3. Actores, flujo y reglas

### Flujo principal

1. La persona con `metadata.read` consulta el estado de Fuente AdventureWorks.
2. La persona con `metadata.refresh` selecciona **Probar conexión**.
3. FastAPI abre una conexión con `ApplicationIntent=ReadOnly`, ejecuta una consulta mínima de catálogo y devuelve un mensaje seguro.
4. La persona selecciona **Actualizar metadatos**.
5. FastAPI obtiene los metadatos en una transacción de lectura con tiempo máximo, los transforma al contrato canónico y los valida.
6. Se calcula `content_hash`. Si coincide con la última instantánea exitosa, la API informa “Sin cambios” y reutiliza la captura vigente sin duplicarla.
7. Si cambió, PostgreSQL conserva una nueva instantánea inmutable y registra el evento de auditoría.
8. El explorador consulta la instantánea y muestra su fecha, origen, hash abreviado y totales.

### Reglas obligatorias

- La base permitida es la configurada en `SQLSERVER_DATABASE`; no se recibe nombre de servidor, base, usuario o contraseña desde el cliente.
- Los identificadores de tabla usados en consultas de catálogo proceden del resultado del servidor y se tratan como datos, no se concatenan para ejecutar SQL arbitrario.
- Se excluyen objetos del sistema y se ordena por esquema, tabla, posición de columna y relación para obtener un hash estable.
- Una falla no elimina la última instantánea válida ni la reemplaza con contenido parcial.
- La API nunca devuelve la cadena ODBC, contraseña, IP interna ni traza de excepción.
- Las acciones simultáneas de actualización se serializan o responden con conflicto; no crean capturas duplicadas.

## 4. Datos, API e interfaz

### 4.1 Persistencia propuesta

Tabla `app.metadata_snapshots`:

| Campo | Regla |
|---|---|
| `id` | Identificador interno. |
| `source_code` | Valor controlado `adventureworks`. |
| `database_name` | Nombre no secreto de la base consultada. |
| `contract_version` | Versión del documento canónico, inicialmente `1`. |
| `content_hash` | SHA-256 único por fuente y versión contractual. |
| `schema_document` | JSONB canónico con metadatos; nunca filas ni secretos. |
| `schema_count`, `table_count`, `column_count`, `relationship_count` | Totales calculados y no negativos. |
| `captured_by_user_id` | Usuario que inició la captura; `SET NULL` si la cuenta se elimina. |
| `captured_by_label` | Etiqueta histórica segura del actor. |
| `captured_at` | Fecha UTC generada por el servidor. |

Las instantáneas no tienen edición ni eliminación desde la interfaz. Una política de retención futura requerirá un parámetro aprobado y otra especificación.

### 4.2 Contrato canónico de metadatos

```json
{
  "contract_version": 1,
  "source": {"code": "adventureworks", "database": "AdventureWorks2022"},
  "schemas": [
    {
      "name": "Sales",
      "tables": [
        {
          "name": "SalesOrderHeader",
          "columns": [
            {
              "name": "SalesOrderID",
              "ordinal": 1,
              "data_type": "int",
              "nullable": false,
              "primary_key": true
            }
          ],
          "foreign_keys": [
            {
              "name": "FK_SalesOrderHeader_Customer_CustomerID",
              "columns": ["CustomerID"],
              "referenced_schema": "Sales",
              "referenced_table": "Customer",
              "referenced_columns": ["CustomerID"]
            }
          ]
        }
      ]
    }
  ]
}
```

No se fija en esta especificación la cantidad exacta de objetos: las pruebas comparan el resultado con los catálogos de la instancia restaurada y con invariantes, no con una cifra frágil.

### 4.3 Glosario semántico controlado

La instantánea conserva los nombres técnicos originales como fuente de verdad. De forma separada, el backend mantiene un glosario versionado para presentar equivalencias comprensibles, por ejemplo `Sales.SalesOrderHeader` como **Venta**, `Production.Product` como **Producto** y `Sales.SalesTerritory` como **Territorio**.

Cada entrada contiene `concept_code`, `display_name_es`, `description_es`, referencias técnicas permitidas y versión. El glosario se mantiene como catálogo versionado del producto, no es una traducción física de AdventureWorks ni una respuesta libre del LLM. Una referencia inexistente en la instantánea invalida el alcance derivado.

### 4.4 Endpoints previstos

| Método y ruta | Permiso | Resultado |
|---|---|---|
| `GET /api/v1/sources/adventureworks` | `metadata.read` | Identidad no secreta, estado conocido, última prueba y última instantánea. |
| `POST /api/v1/sources/adventureworks/test` | `metadata.refresh` | Prueba mínima segura; puede reutilizar internamente el control existente de parámetros. |
| `POST /api/v1/metadata/snapshots` | `metadata.refresh` | Crea o reutiliza una instantánea completa. |
| `GET /api/v1/metadata/snapshots` | `metadata.read` | Lista paginada de capturas, más reciente primero. |
| `GET /api/v1/metadata/snapshots/{id}` | `metadata.read` | Resumen y documento canónico. |
| `GET /api/v1/metadata/snapshots/{id}/tables` | `metadata.read` | Tablas paginadas con búsqueda y filtro de esquema. |
| `GET /api/v1/metadata/snapshots/{id}/tables/{schema}/{table}` | `metadata.read` | Columnas, claves y relaciones de una tabla. |
| `GET /api/v1/metadata/snapshots/{id}/business-concepts` | `metadata.read` | Conceptos en español, referencias técnicas y versión del glosario aplicable. |

Parámetros de paginación: `limit` de 1 a 100 y `offset` no negativo. La búsqueda tiene longitud máxima y no se usa para construir SQL dinámico sobre AdventureWorks.

### 4.5 Pantallas y menús

- Grupo **Datos**.
- **Fuente AdventureWorks**: ficha de fuente, estado, última prueba, última captura, totales y acciones autorizadas.
- **Explorador de esquema**: vista avanzada definida en [SPR-03-03](SPR-03-03-explorador-esquema-y-trazabilidad.md); no es un prerrequisito de navegación para el gerente.

## 5. Seguridad y auditoría

- Permisos: `metadata.read` para consultar y `metadata.refresh` para probar/actualizar.
- Las credenciales se leen de `SQLSERVER_*` en el entorno del backend y no se persisten en las nuevas tablas.
- La cuenta SQL `bi_reader` mantiene `DENY INSERT, UPDATE, DELETE, EXECUTE`; la interfaz no sustituye este control.
- El backend aplica tiempo máximo, cancela conexiones y limita concurrencia.
- Eventos auditados:
  - `metadata.connection.test` con resultado seguro y duración;
  - `metadata.snapshot.create` con id, hash abreviado y totales;
  - `metadata.snapshot.unchanged` cuando no existen cambios;
  - `metadata.snapshot.failed` con categoría segura, sin excepción ni credencial.
- Consultar páginas o expandir tablas no genera un evento por clic para evitar ruido; la creación de la instantánea sí queda trazada.

## 6. UI/UX responsive y accesibilidad

- La fuente se presenta como una ficha de estado, no como un CRUD de servidores.
- Durante la actualización se deshabilita la acción y se anuncia progreso mediante texto accesible.
- Estados obligatorios: sin captura, conectando, capturando, sin cambios, captura nueva, origen inaccesible, sesión vencida y acceso denegado.
- En móvil se priorizan estado, última actualización y acción; los detalles técnicos quedan en secciones plegables.
- Las tablas se transforman en lista o detalle apilado cuando no haya ancho suficiente; no se reduce la tipografía ni se fuerza desplazamiento horizontal de toda la página.
- El foco regresa a la confirmación o al error después de una operación. Ningún estado depende sólo del color.

## 7. Criterios de aceptación verificables

- [ ] Con una fuente saludable y permiso suficiente se obtiene una instantánea con tablas, columnas, PK, FK y relaciones declaradas.
- [ ] La misma estructura normalizada produce el mismo hash y no crea un duplicado.
- [ ] Un cambio controlado de metadatos produce otra instantánea sin modificar la anterior.
- [ ] Ninguna instantánea contiene filas, valores de negocio, credenciales o cadenas de conexión.
- [ ] El glosario presenta etiquetas españolas con referencia técnica trazable y rechaza objetos inexistentes.
- [ ] La interrupción de SQL Server conserva la última captura válida y devuelve un error seguro.
- [ ] Un usuario sin `metadata.read` recibe 403; sin `metadata.refresh` puede consultar, pero no probar ni actualizar.
- [ ] Los endpoints de listas respetan paginación, búsqueda limitada y orden estable.
- [ ] La interfaz presenta estados completos y es utilizable en 320, 768, 1024 y 1440 px.
- [ ] La auditoría registra pruebas y capturas sin secretos.
- [ ] Las pruebas confirman que el usuario de fuente no puede ejecutar escritura.

## 8. Plan de pruebas y evidencia

- Unitarias: normalización, orden canónico, hash, tipos compuestos, PK/FK, glosario y sanitización de errores.
- Integración PostgreSQL: migración, inmutabilidad, deduplicación y actor histórico.
- Integración SQL Server: captura real desde AdventureWorks y prueba negativa de escritura.
- API: 401, 403, 404, 409, falla de origen y respuestas paginadas.
- Frontend: estados, búsqueda, permisos y responsive.
- CI: usa dobles determinísticos para la introspección; no descarga AdventureWorks ni depende de red externa adicional.
- Evidencia académica: resumen de captura, hash, totales, ejemplo de relación y prueba de sólo lectura.

## 9. Riesgos y dependencias

- SQL Server puede tardar en restaurar: la interfaz debe distinguir “fuente iniciando” de “fuente inválida”.
- Los tipos SQL Server requieren un mapeo canónico documentado; se conserva el nombre nativo además de la categoría normalizada.
- Un esquema completo puede ser grande para un LLM local; la instantánea completa se conserva, pero el paquete de IA usa sólo el alcance derivado o ajustado definido en SPR-03-02.
- Depende de la seguridad y auditoría de Sprint 2; no implementa autenticación alternativa.

## 10. Resultado de implementación

Pendiente. Al cerrar el PR se registrarán migración, SHA, pruebas, evidencia real, desviaciones aprobadas y estado final.
