# SPR-03-01: conexión parametrizable e introspección SQL Server

- Estado: **implementada y verificada localmente**.
- Pertenece a: [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md).
- Fecha de creación: 2026-09-14.
- Rama prevista de implementación: `feature/sprint-03-metadata-copilot`.
- PR de implementación: pendiente.

## 1. Problema y objetivo

El prototipo ya puede probar técnicamente una conexión definida en el entorno, pero todavía no permite registrarla desde la web ni ofrece una representación versionada de su esquema. El Copiloto no puede proponer un modelo BI de manera trazable sin una conexión activa y una instantánea determinística que sea su única fuente técnica de verdad.

El objetivo es implementar el conector `sqlserver` sobre el catálogo parametrizable de SPR-03-04 y una introspección de sólo lectura que obtenga tablas, columnas, tipos, nulabilidad, claves primarias, claves foráneas y relaciones declaradas; normalice esos metadatos; calcule una huella reproducible; y conserve una instantánea inmutable en PostgreSQL. AdventureWorks2022 será la configuración usada para validar académicamente este contrato, no un host o base codificados en la aplicación.

## 2. Alcance y exclusiones

### Incluido

- Uso de la conexión `sqlserver` activa registrada mediante la plataforma.
- Prueba de conectividad y confirmación segura del modo de sólo lectura.
- Introspección de esquemas y tablas de usuario, columnas, tipos, nulabilidad, claves primarias y foráneas.
- Normalización, orden estable y hash SHA-256 del documento canónico.
- Persistencia de instantáneas inmutables y consulta de la última captura.
- Búsqueda, filtros y detalle de tabla a partir de la instantánea, no mediante consultas repetidas al origen.
- Métricas técnicas: cantidad de esquemas, tablas, columnas y relaciones.

### Excluido

- Filas o muestras de datos, mínimos, máximos, cardinalidad, perfiles estadísticos o datos personales.
- Vistas, procedimientos, funciones, disparadores, índices no necesarios y código fuente SQL.
- Implementación funcional de motores diferentes de SQL Server o uso simultáneo de múltiples fuentes.
- Cambios en AdventureWorks y consultas de negocio.
- Inferencia de relaciones que no estén declaradas; podrán registrarse como advertencias futuras, no como hechos.

## 3. Actores, flujo y reglas

### Flujo principal

1. La persona con `connections.write` registra o edita una conexión en **Parámetros generales > Conexiones de datos** según SPR-03-04.
2. La persona con `connections.test` selecciona **Probar conexión**. FastAPI recupera el secreto cifrado, abre una conexión con intención de lectura, comprueba capacidades y devuelve un mensaje seguro.
3. Después de una prueba exitosa, la persona activa la conexión; sólo una queda activa.
4. La persona con `metadata.read` consulta el estado integrado en **Conexiones de datos**.
5. La persona con `metadata.refresh` selecciona **Actualizar metadatos** desde la conexión activa.
6. FastAPI obtiene los metadatos mediante el adaptador activo, en una transacción de lectura con tiempo máximo, los transforma al contrato canónico y los valida.
7. Se calcula `content_hash`. Si coincide con la última instantánea exitosa de esa conexión, la API informa “Sin cambios” y reutiliza la captura vigente sin duplicarla.
8. Si cambió, PostgreSQL conserva una nueva instantánea inmutable y registra el evento de auditoría.
9. El explorador consulta la instantánea y muestra su fecha, conexión, motor, base, hash abreviado y totales.

### Reglas obligatorias

- Host, puerto, base y usuario se reciben exclusivamente mediante el contrato de configuración de SPR-03-04; el backend los valida y construye la conexión sin aceptar una cadena libre.
- La contraseña llega únicamente al crear o reemplazar el secreto, se cifra antes de persistirse y nunca vuelve al cliente.
- La introspección opera sobre la única conexión activa y rechaza un conector que no implemente la capacidad requerida.
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
| `data_connection_id` | FK a la conexión utilizada; no cambia aunque después se desactive. |
| `connector_code` | Código histórico del adaptador, inicialmente `sqlserver`. |
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
  "source": {"connection_id": 1, "connector": "sqlserver", "database": "AdventureWorks2022"},
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

### 4.3 Endpoints previstos

| Método y ruta | Permiso | Resultado |
|---|---|---|
| `GET /api/v1/sources/active` | `metadata.read` | Identidad no secreta de la conexión activa, estado y última instantánea. |
| `POST /api/v1/metadata/snapshots` | `metadata.refresh` | Crea o reutiliza una instantánea completa de la conexión activa. |
| `GET /api/v1/metadata/snapshots` | `metadata.read` | Lista paginada de capturas, más reciente primero. |
| `GET /api/v1/metadata/snapshots/{id}` | `metadata.read` | Resumen y documento canónico. |
| `GET /api/v1/metadata/snapshots/{id}/tables` | `metadata.read` | Tablas paginadas con búsqueda y filtro de esquema. |
| `GET /api/v1/metadata/snapshots/{id}/tables/{schema}/{table}` | `metadata.read` | Columnas, claves y relaciones de una tabla. |

Parámetros de paginación: `limit` de 1 a 100 y `offset` no negativo. La búsqueda tiene longitud máxima y no se usa para construir SQL dinámico sobre AdventureWorks.

### 4.4 Pantallas y menús

- Grupo **Datos**.
- **Conexiones de datos**: integra conexión seleccionada, motor, base, estado, última prueba, última captura, totales y acciones autorizadas sin mostrar secretos.
- **Explorador de esquema**: vista avanzada definida en [SPR-03-03](SPR-03-03-explorador-esquema-y-trazabilidad.md); no es un prerrequisito de navegación para el gerente.

## 5. Seguridad y auditoría

- Permisos: `metadata.read` para consultar y `metadata.refresh` para probar/actualizar.
- Las credenciales se recuperan por `secret_id` según SPR-03-04 y se descifran únicamente en memoria durante la operación.
- La cuenta configurada debe mantener sólo lectura; para la evidencia de AdventureWorks, `bi_reader` conserva `DENY INSERT, UPDATE, DELETE, EXECUTE`. La interfaz no sustituye este control del motor.
- El backend aplica tiempo máximo, cancela conexiones y limita concurrencia.
- Eventos auditados:
  - `metadata.snapshot.create` con id, hash abreviado y totales;
  - `metadata.snapshot.unchanged` cuando no existen cambios;
  - `metadata.snapshot.failed` con categoría segura, sin excepción ni credencial.
- Consultar páginas o expandir tablas no genera un evento por clic para evitar ruido; la creación de la instantánea sí queda trazada.

## 6. UI/UX responsive y accesibilidad

- La fuente activa se presenta como ficha de estado; el CRUD de conexiones vive en Parámetros generales según SPR-03-04.
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
- [ ] La interrupción de SQL Server conserva la última captura válida y devuelve un error seguro.
- [ ] Un usuario sin `metadata.read` recibe 403; sin `metadata.refresh` puede consultar, pero no probar ni actualizar.
- [ ] Los endpoints de listas respetan paginación, búsqueda limitada y orden estable.
- [ ] La interfaz presenta estados completos y es utilizable en 320, 768, 1024 y 1440 px.
- [ ] La auditoría registra pruebas y capturas sin secretos.
- [ ] Las pruebas confirman que el usuario de fuente no puede ejecutar escritura.

## 8. Plan de pruebas y evidencia

- Unitarias: normalización, orden canónico, hash, tipos compuestos, PK/FK y sanitización de errores.
- Integración PostgreSQL: migración, inmutabilidad, deduplicación y actor histórico.
- Integración SQL Server: conexión creada desde la API, captura real desde AdventureWorks y prueba negativa de escritura.
- API: 401, 403, 404, 409, falla de origen y respuestas paginadas.
- Frontend: estados, búsqueda, permisos y responsive.
- CI: usa dobles determinísticos para la introspección; no descarga AdventureWorks ni depende de red externa adicional.
- Evidencia académica: resumen de captura, hash, totales, ejemplo de relación y prueba de sólo lectura.

## 9. Riesgos y dependencias

- SQL Server puede tardar en restaurar: la interfaz debe distinguir “fuente iniciando” de “fuente inválida”.
- Los tipos SQL Server requieren un mapeo canónico documentado; se conserva el nombre nativo además de la categoría normalizada.
- Un esquema completo puede ser grande para un LLM local; la instantánea completa se conserva y SPR-03-02 la procesa dinámicamente en bloques compactos.
- Depende de la seguridad y auditoría de Sprint 2; no implementa autenticación alternativa.
- Depende del catálogo de conexiones y almacén de secretos de SPR-03-04.

## 10. Resultado de implementación

La migración `20260918_08` crea `app.metadata_snapshots` con documento JSONB, hash, totales, actor histórico, unicidad por fuente/contrato/hash y claves foráneas que conservan la trazabilidad. FastAPI incorpora los seis endpoints previstos, serializa capturas concurrentes mediante un bloqueo asesor de PostgreSQL y registra creación, ausencia de cambios o falla segura.

La captura real desde la conexión activa AdventureWorks produjo 6 esquemas, 71 tablas, 444 columnas y 90 relaciones. Una segunda ejecución generó el mismo hash SHA-256, reutilizó la instantánea y mantuvo estable el total. El explorador permite buscar por esquema, tabla o columna y consultar columnas, PK, relaciones entrantes y salientes sin leer filas del negocio.

La interfaz sincroniza el identificador seleccionado con las instantáneas disponibles al cambiar de módulo o actualizar la lista; si una versión deja de pertenecer a la página actual, selecciona automáticamente la primera válida, limpia la carga anterior y descarta respuestas atrasadas. Así, una lectura persistida no depende de presionar nuevamente **Actualizar metadatos**.

La validación automatizada incluye orden canónico, hash reproducible, claves foráneas, búsqueda segura, recorrido React del explorador y compilación frontend. El SHA y el PR se incorporarán al publicar esta rama hacia `develop`.
