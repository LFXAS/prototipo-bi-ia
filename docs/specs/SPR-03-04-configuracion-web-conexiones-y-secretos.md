# SPR-03-04: configuración web de conexiones, parámetros y secretos

- Estado: **borrador para revisión y aprobación**.
- Pertenece a: [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md).
- Fecha de creación: 2026-09-14.
- Rama prevista de implementación: `feature/sprint-03-metadata-copilot`.
- PR de implementación: pendiente.

## 1. Problema y objetivo

La operación del producto no puede depender de que un gerente, analista o administrador edite `.env`, Compose, código o registros directamente en PostgreSQL para registrar una fuente o una credencial LLM. A la vez, guardar contraseñas o claves API en texto legible convertiría la parametrización web en un riesgo.

El objetivo es proporcionar pantallas y APIs para administrar configuraciones de aplicación, conexiones externas y secretos de forma segura. Sprint 3 implementará el conector funcional `sqlserver` y validará AdventureWorks como fuente pública principal, pero el contrato permitirá incorporar PostgreSQL, MySQL u otros motores mediante adaptadores posteriores sin rediseñar la experiencia ni el modelo de datos.

## 2. Límites de parametrización

### Administrable desde la plataforma web

- Nombre visible, motor, servidor, puerto, base de datos y opciones permitidas de una conexión externa.
- Usuario y contraseña de la fuente mediante entrada secreta, cifrada y nunca recuperable en claro desde la UI.
- Activación de una sola fuente para el flujo BI del prototipo.
- Proveedor, URL autorizada, modelo y credencial secreta de una configuración LLM.
- Parámetros operativos aprobados: idioma visible, tamaño de página, tiempos máximos dentro de rangos seguros y límites del asistente.
- Prueba de conexión, validación de permisos de sólo lectura, desactivación y eliminación controlada.

### No administrable en tiempo de ejecución

- Puertos publicados por Docker, nombres de contenedores, volúmenes, imágenes, redes y recursos del host.
- Credenciales internas de PostgreSQL, cuenta inicial de recuperación y clave maestra de cifrado.
- Migraciones de esquema, políticas de red del servidor o instalación de controladores.

Estos valores pertenecen al despliegue. El proceso de instalación deberá generarlos o aprovisionarlos automáticamente; no se presentarán como una tarea cotidiana del usuario final.

## 3. Catálogo de conectores

Cada motor se implementa mediante una interfaz backend común:

```text
Connector
  validate_settings(settings)
  test_connection(secret)
  inspect_capabilities()
  introspect_schema()
  verify_read_only()
  close()
```

El catálogo expone código, nombre visible, puerto sugerido, campos requeridos, opciones permitidas y estado `available` o `planned`. En Sprint 3:

| Código | Estado | Alcance |
|---|---|---|
| `sqlserver` | disponible | Conexión, prueba de sólo lectura e introspección. |
| otros motores | no publicados en la UI | Se incorporarán únicamente con especificación, adaptador y pruebas propias. |

La arquitectura queda abierta a nuevos conectores, pero la interfaz no mostrará opciones que todavía no funcionen. AdventureWorks es una instancia configurada mediante el conector `sqlserver`, no una condición codificada en el formulario.

## 4. Persistencia y secretos

### 4.1 Conexiones externas

Tabla `app.data_connections`:

| Campo | Regla |
|---|---|
| `id` | Identificador interno. |
| `name` | Nombre visible único. |
| `connector_code` | Código existente en el catálogo de conectores. |
| `host`, `port`, `database_name` | Datos técnicos validados; nunca contienen contraseña. |
| `settings_document` | JSONB limitado al esquema de opciones permitido por el adaptador. |
| `secret_id` | Referencia opaca al almacén de secretos. |
| `is_active` | Sólo una fuente puede estar activa para este prototipo. |
| `is_system_protected` | Protege la fuente demostrativa cuando la instalación la provea. |
| `last_test_status`, `last_tested_at` | Resultado y fecha sin detalles sensibles. |
| `created_by`, `updated_by`, fechas | Trazabilidad con etiqueta histórica segura. |

### 4.2 Almacén de secretos

Tabla `app.secrets` o repositorio equivalente:

- conserva únicamente un sobre cifrado autenticado, versión de algoritmo, identificador de clave y fechas;
- nunca persiste el valor en claro, una variable de entorno indicada por el usuario ni una copia en auditoría;
- no ofrece endpoint para leer el secreto; sólo permite reemplazarlo o eliminarlo cuando no tenga dependencias;
- descifra exclusivamente en memoria del backend durante una operación autorizada y elimina la referencia al finalizar;
- diferencia secretos de fuente y de proveedor LLM.

La clave maestra no se guarda en PostgreSQL. En el entorno académico local se genera automáticamente durante el primer arranque y se conserva con permisos restrictivos en un volumen Docker independiente. En producción, la misma interfaz deberá admitir un gestor externo de secretos. El administrador no edita manualmente la clave para operar la plataforma.

Las referencias `GEMINI_API_KEY`, `DASHSCOPE_API_KEY` y `SQLSERVER_PASSWORD` existentes se consideran mecanismo de transición. La implementación deberá permitir importar su valor una sola vez desde backend sin mostrarlo y reemplazarlo desde la UI; el cierre del Sprint 3 eliminará su necesidad para la operación ordinaria.

### 4.3 Catálogo de parámetros operativos

La tabla existente `app.parameters` se ampliará por migración para convertirse en el catálogo tipado:

| Campo | Regla |
|---|---|
| `key` | Clave estable creada por migración; no puede ser inventada desde la interfaz. |
| `name`, `description` | Nombre y explicación comprensibles en español. |
| `data_type` | Tipo cerrado: texto, entero, decimal, booleano o selección. |
| `value_document` | Valor vigente validado de acuerdo con el tipo y las restricciones. |
| `default_document` | Valor seguro de restauración. |
| `validation_document` | Rango, longitud u opciones admitidas, definido por el módulo consumidor. |
| `module_code` | Módulo propietario del parámetro. |
| `is_editable`, `is_sensitive` | Los secretos no se administran como parámetros y usan `app.secrets`. |
| `updated_by`, `updated_at` | Trazabilidad del último cambio. |

Cada módulo que incorpore un ajuste operativo deberá registrar primero su definición por migración y consumirlo mediante un servicio común de parámetros. El administrador podrá consultar, filtrar, modificar y restaurar valores desde la web; no podrá crear claves libres, alterar el tipo ni omitir las restricciones. Los valores de despliegue descritos en la sección 2 no forman parte de este catálogo. No se crea una tabla paralela ni se pierde compatibilidad con la estructura del Sprint 2.

## 5. Reglas de negocio

1. Sólo una conexión de datos puede estar activa en el alcance académico.
2. Activar requiere una prueba exitosa reciente y verificación de sólo lectura.
3. Sprint 3 sólo permite activar conexiones cuyo `connector_code` sea `sqlserver`.
4. La cuenta fuente no puede pertenecer a roles de escritura o administración; si el adaptador detecta permisos incompatibles, la prueba falla.
5. React nunca recibe el secreto guardado. En edición, el campo aparece vacío con la indicación **Conservar credencial actual**.
6. Una credencial nueva reemplaza el sobre cifrado anterior de forma transaccional.
7. No se puede eliminar una conexión con instantáneas o propuestas asociadas; primero se desactiva y se conserva como referencia histórica. La eliminación física futura requerirá una política de retención.
8. Host y puerto se validan contra una política de red. Se bloquean loopback del backend, metadatos cloud, esquemas de URL, rutas, credenciales embebidas y destinos no permitidos.
9. Las opciones específicas del motor se aceptan sólo si están declaradas en su esquema; no se reciben fragmentos de cadena de conexión.
10. Toda modificación genera auditoría sin contraseña, clave API ni sobre cifrado.

## 6. API prevista

| Método y ruta | Permiso | Resultado |
|---|---|---|
| `GET /api/v1/connectors` | `connections.read` | Conectores realmente disponibles y sus campos públicos. |
| `GET /api/v1/connections` | `connections.read` | Lista paginada y enmascarada. |
| `POST /api/v1/connections` | `connections.write` | Crea configuración y secreto cifrado. |
| `GET /api/v1/connections/{id}` | `connections.read` | Detalle sin secreto. |
| `PUT /api/v1/connections/{id}` | `connections.write` | Actualiza valores y reemplaza opcionalmente el secreto. |
| `POST /api/v1/connections/{id}/test` | `connections.test` | Prueba conectividad, capacidades y sólo lectura. |
| `POST /api/v1/connections/{id}/activate` | `connections.write` | Activa una fuente probada y desactiva la anterior en una transacción. |
| `POST /api/v1/connections/{id}/deactivate` | `connections.write` | Desactiva sin borrar trazabilidad. |
| `DELETE /api/v1/connections/{id}` | `connections.write` | Elimina sólo cuando no tiene dependencias y no está protegida. |
| `PUT /api/v1/llm-configurations/{id}/secret` | `llm.write` | Registra o reemplaza la credencial cifrada del proveedor. |
| `GET /api/v1/parameters` | `parameters.read` | Lista paginada de parámetros autorizados, con tipo, descripción, valor y origen. |
| `PUT /api/v1/parameters/{key}` | `parameters.write` | Modifica el valor después de validar tipo, rango y concurrencia. |
| `POST /api/v1/parameters/{key}/reset` | `parameters.write` | Restaura el valor predeterminado y registra auditoría. |

Las escrituras usan control de concurrencia y respuestas de error por campo. Ninguna respuesta incluye secretos, valores anteriores, cadenas completas o trazas.

## 7. Interfaz

### Parámetros generales > Conexiones de datos

- Lista paginada con nombre, motor, base, estado, última prueba y acciones.
- Formulario guiado cuyos campos cambian según el esquema público del conector.
- Campo de contraseña con opción mostrar únicamente antes de enviar; después nunca vuelve a mostrarse.
- Acciones Crear, Editar, Probar, Activar, Desactivar y Eliminar con confirmaciones y validaciones de dependencias.
- Mensaje persistente que explica que la fuente debe ser de sólo lectura.

### Parámetros generales > Configuración LLM

- Mantiene el CRUD del Sprint 2 y añade **Registrar/Reemplazar credencial**.
- Indica `Credencial configurada` o `Credencial pendiente`, nunca su valor ni sus últimos caracteres.
- Probar conexión utiliza el secreto almacenado y no exige editar `.env`.

La pantalla **Parámetros** deja de ser una tabla vacía: muestra exclusivamente parámetros registrados en un catálogo permitido, con búsqueda, filtro por módulo, descripción, tipo, rango, valor vigente y origen. Permite editar y restaurar únicamente los valores marcados como editables. Los secretos no aparecen allí y no existe un formulario para inventar claves sin un módulo consumidor.

## 8. Seguridad y auditoría

- Nuevos permisos: `connections.read`, `connections.write` y `connections.test`; el Administrador protegido los recibe por semilla.
- Cifrado autenticado mediante biblioteca mantenida; nonces únicos y rotación versionada.
- Secretos excluidos de logs, excepciones, eventos, respuestas, exportaciones y copias documentales.
- Protección contra SSRF, tiempo máximo, límites de concurrencia y cierre de conexiones.
- Eventos: `connection.create`, `update`, `test`, `activate`, `deactivate`, `delete`, `secret.replace` y `llm.secret.replace`.
- La auditoría registra actor, conexión, motor, resultado y cambios de campos no sensibles.

## 9. Criterios de aceptación

- [ ] Una persona administradora puede crear, probar, editar y activar AdventureWorks desde la web sin editar `.env` ni PostgreSQL.
- [ ] El formulario se deriva del catálogo `sqlserver` y no concatena una cadena arbitraria suministrada por React.
- [ ] El secreto se cifra antes de persistirse y no puede recuperarse mediante API, interfaz, logs o auditoría.
- [ ] Editar sin contraseña conserva la actual; reemplazarla invalida de forma segura el sobre anterior.
- [ ] Una conexión con permisos de escritura no puede activarse.
- [ ] Sólo una fuente queda activa y el cambio es transaccional.
- [ ] Las dependencias impiden eliminar físicamente una conexión usada por instantáneas o propuestas.
- [ ] La configuración LLM puede recibir o reemplazar su clave desde la web y probarse sin edición manual de archivos.
- [ ] Los parámetros operativos definidos por los módulos pueden consultarse, modificarse y restaurarse desde la web, con validación por tipo y auditoría.
- [ ] No es posible crear claves de parámetro arbitrarias, cambiar su tipo o guardar un secreto en el catálogo general.
- [ ] El catálogo de conectores permite añadir otro adaptador sin cambiar las tablas, rutas generales ni flujo de UI.
- [ ] Motores no implementados no se muestran como opciones utilizables.
- [ ] Todos los formularios y estados funcionan en 320, 768, 1024 y 1440 px y son operables con teclado.

## 10. Pruebas y evidencia

- Unitarias: validación por conector, cifrado/descifrado, reemplazo, enmascaramiento, política de host y esquema de opciones.
- Integración: CRUD, activación única, dependencias, permisos, auditoría y persistencia después de reiniciar contenedores.
- Parámetros: listado paginado, modificación válida, rechazo de tipo/rango incorrectos, restauración y concurrencia.
- SQL Server real: registro web de AdventureWorks, prueba de conexión, verificación de sólo lectura e introspección.
- LLM real o local: registro web del secreto cuando aplique y prueba sin variables editadas por el usuario.
- Seguridad: intento de lectura del secreto, SSRF, opción desconocida, cadena inyectada, escritura detectada y logs sanitizados.
- Frontend: mensajes por campo, contraseña opcional al editar, estados, confirmaciones, paginación y responsive.

## 11. Riesgos y decisiones

- Parametrizable no significa ejecutar cualquier cadena: cada conector define campos y opciones cerradas.
- Guardar secretos exige una raíz de confianza fuera de PostgreSQL; el volumen local automático es aceptable para la prueba de concepto, pero una implantación productiva requerirá un gestor de secretos.
- Implementar varios motores en Sprint 3 ampliaría en exceso el alcance. Se entrega la interfaz extensible y sólo SQL Server se considera funcional y probado.
- La parametrización de infraestructura Docker no pertenece al usuario final y no puede modificarse de forma segura desde la aplicación que depende de ella.

## 12. Resultado de implementación

Pendiente. Al cerrar el PR se registrarán migraciones, mecanismo criptográfico, pruebas, evidencia visual, SHA, desviaciones y estado final.
