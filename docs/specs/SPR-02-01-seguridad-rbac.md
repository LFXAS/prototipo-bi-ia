# SPR-02-01: seguridad, usuarios, roles, permisos, menús y auditoría

- Estado: **implementado y verificado localmente; pendiente de revisión colaborativa y cierre mediante PR hacia `develop`**.
- Pertenece a: [SPR-02-rbac-y-parametros.md](SPR-02-rbac-y-parametros.md).
- Última revisión funcional: 2026-09-10.

## 1. Objetivo

Permitir administrar de forma segura y comprensible las cuentas y autorizaciones del prototipo. La administración se basa en el modelo RBAC: una persona usuaria recibe uno o varios roles; cada rol reúne permisos; los permisos autorizan operaciones en FastAPI y determinan qué menús pueden mostrarse.

El modelo interno conserva códigos estables porque los endpoints necesitan una regla inequívoca. La experiencia administrativa, sin embargo, trabaja con nombres, descripciones, categorías y controles de selección, nunca con números o códigos que la persona tenga que memorizar.

## 2. Modelo y reglas de protección

| Entidad | Datos visibles y administrables | Datos internos / regla |
|---|---|---|
| Usuario | correo, nombre completo, estado, roles seleccionados. | Contraseña sólo se ingresa al crear o cambiarla; nunca se muestra. |
| Rol | nombre, descripción, estado y permisos seleccionados. | La clave técnica identifica un rol de sistema; no se edita desde una pantalla común. |
| Permiso | nombre, descripción, categoría y estado de disponibilidad. | El código enlaza endpoint y autorización; lo registra una especificación/migración, no se digita libremente. |
| Menú | etiqueta, módulo visible, orden, estado y permisos asociados presentados por nombre. | Código y ruta deben provenir de un catálogo de pantallas implementadas. |
| Auditoría | fecha, actor, acción legible, recurso y resultado seguro. | Es inmutable y nunca expone secretos. |

### 2.1 Invariantes de recuperación

1. El administrador inicial y el rol administrativo inicial son registros de sistema protegidos por una marca persistida, no por un ID numérico ni por texto libre de la interfaz.
2. No se puede desactivar el usuario administrador inicial ni quitarle todos los roles administrativos protegidos.
3. No se puede desactivar, renombrar técnicamente, eliminar ni dejar sin permisos mínimos de seguridad al rol administrativo inicial.
4. Antes de guardar cualquier cambio de estado, roles o permisos, el backend comprueba que continúe al menos una cuenta activa asociada a un rol activo con las capacidades mínimas de recuperación: administrar usuarios, roles, permisos y menús.
5. Si la acción pone en riesgo esa condición, FastAPI responde con un mensaje claro, no realiza cambios y registra el intento de forma segura. La interfaz deshabilita la acción cuando puede determinarlo, pero la regla definitiva está en FastAPI.
6. Ninguna recuperación normal debe requerir editar tablas directamente. Un procedimiento de emergencia, fuera del uso cotidiano, se documentará para el despliegue y exigirá acceso controlado al entorno.

## 3. Flujos de usuario

### 3.1 Usuarios

1. La persona administradora abre **Seguridad > Usuarios** y ve una lista paginada, con buscador por correo o nombre, estado y roles visibles por nombre.
2. Al elegir **Crear usuario**, el formulario inicia vacío y presenta correo, nombre, contraseña inicial y una tabla de casillas de roles activos. Cada fila muestra nombre y descripción; no se escriben `role_ids`.
3. Al elegir **Editar** en una fila, sólo se carga esa cuenta. La tabla marca sus roles actuales; la contraseña queda vacía, no es obligatoria y sólo cambia si se escribe una nueva.
4. Al desactivar, se muestra confirmación con la consecuencia. Si es una cuenta protegida o deja sin recuperación administrativa, el control explica por qué no está disponible.
5. Guardar muestra éxito o un error comprensible y devuelve el formulario a un estado limpio. Cambiar de pantalla descarta la edición sin guardar tras pedir confirmación cuando corresponda.

### 3.2 Roles y permisos por rol

1. En **Seguridad > Roles**, la lista presenta nombre, descripción, estado y número/resumen de permisos; no exige interpretar código interno.
2. Crear un rol solicita nombre y descripción. El sistema genera o reserva su clave técnica de forma controlada y muestra una ayuda: "La clave interna la administra la plataforma". Para un rol nuevo, se puede proponer un identificador derivado del nombre, validado y no ambiguo, pero no se usa un campo libre como contrato de programación.
3. La asignación de permisos usa una tabla de casillas, agrupable por categoría. Cada fila muestra nombre y descripción; la persona marca o desmarca lo que desea conceder y revisa el resultado antes de guardar. No se escriben `permission_ids` ni códigos. La actualización de permisos utiliza el contrato `PUT /roles/{id}/permissions`.
4. El rol administrativo inicial se distingue visualmente como **rol protegido del sistema**. Su clave técnica no se edita, no puede desactivarse y los cambios que dañen la recuperación se rechazan por las invariantes anteriores.
5. La pantalla no selecciona ni transporta un rol a **Permisos**, **Menús**, **Parámetros** ni **LLM**. Si se necesita consultar asignaciones de un rol, se hace dentro de su propia ficha o diálogo.

### 3.3 Catálogo de permisos

La pantalla **Seguridad > Permisos** es un catálogo informativo y controlado, no un editor de contratos técnicos. Presenta nombre, descripción, categoría, módulos que lo usan, estado y roles asociados cuando el permiso de consulta lo permite.

- Los permisos de plataforma se incorporan junto con la funcionalidad que protegen, mediante especificación, migración y prueba; por ejemplo, un endpoint nuevo agrega su permiso correspondiente.
- No se permite crear desde la interfaz un permiso con un código arbitrario, porque no tendría un endpoint o una regla real que proteger.
- Un permiso protegido o requerido por la recuperación administrativa no puede desactivarse. Si un permiso no protegido se puede retirar en una etapa posterior, el sistema muestra los roles y menús afectados, solicita confirmación y conserva auditoría.
- La edición de nombre y descripción puede estar permitida para permisos configurables sólo si no modifica el código interno ni borra el significado funcional; de lo contrario se mantiene como sólo lectura.

### 3.4 Catálogo de menús

La pantalla **Seguridad > Menús** administra la presentación de opciones que ya existen en el producto. No crea rutas inexistentes.

1. El formulario muestra una guía contextual: etiqueta visible, módulo, orden, estado y permisos por nombre. El módulo se elige de una lista de módulos registrados; no se escribe un código de módulo.
2. La ruta y el código técnico son de sólo lectura para los menús del catálogo. Si se requiere una pantalla nueva, se crea primero la funcionalidad, su ruta, permiso, migración, pruebas y especificación; después aparece como opción configurable.
3. Antes de desactivar un menú, el sistema muestra a qué grupo pertenece y si deja sin ruta visible una capacidad. Los menús de recuperación administrativa se protegen según las invariantes.
4. La lista puede filtrar por módulo y estado; el detalle de permisos se lee por nombre y descripción, no por identificador.

### 3.5 Auditoría

**Seguridad > Auditoría** es una vista de consulta paginada y filtrable por periodo, actor, recurso y tipo de acción. No permite crear, modificar ni eliminar eventos. Debe explicar las acciones con verbos comprensibles: por ejemplo, "Se asignó el rol Analista a María Pérez" en lugar de exponer únicamente `security.user.update`. Si la cuenta de un actor fue eliminada, se presenta su etiqueta histórica segura y no un identificador inexistente.

### 3.6 Eliminación física controlada

Los CRUD habilitan **Eliminar definitivamente** sólo para registros no protegidos y después de una confirmación que nombra el recurso. La operación nunca es un borrado en cascada silencioso: FastAPI comprueba primero las dependencias hijas y responde `409` con su cantidad y el paso que debe realizarse antes de borrar el registro padre.

| Padre | Dependencias que deben quedar resueltas antes | Regla adicional |
|---|---|---|
| Usuario | asignaciones usuario--rol. | Una cuenta protegida no se elimina. Los eventos de auditoría se conservan: al eliminar una cuenta no protegida, su referencia técnica de actor queda vacía y permanece una etiqueta histórica segura del actor; no se borra ni se altera el contenido funcional del evento. |
| Rol | asignaciones usuario--rol y rol--permiso. | Un rol protegido no se elimina. Primero se retiran las asociaciones desde Usuarios y Roles. |
| Permiso | asociaciones rol--permiso y menú--permiso. | Los permisos técnicos/protegidos no se eliminan desde el CRUD. |
| Menú | asociaciones menú--permiso. | Un menú protegido no se elimina. |
| Parámetro | ninguna dependencia no auditada del catálogo consumidor. | Sólo se elimina si el módulo consumidor lo permite. |
| Configuración LLM | ninguna; su evidencia de auditoría se conserva. | Sólo se elimina si está inactiva. |

Toda eliminación exitosa registra actor, fecha, acción `delete`, tipo y identificador del recurso. La auditoría no guarda credenciales ni valores sensibles y jamás permite eliminarse a sí misma.

## 4. API y controles del backend

- Cada operación requiere JWT válido y permiso específico. React nunca reemplaza esta verificación.
- Las respuestas paginadas conservan `items`, `total`, `limit` y `offset`; admiten filtros documentados en cada recurso.
- Los endpoints de selección deben exponer catálogos activos, por ejemplo roles seleccionables, permisos agrupados y módulos de menú. La interfaz no carga listas extensas sin paginar; un selector con búsqueda puede consultar por texto.
- Las actualizaciones de asociaciones reciben IDs sólo desde controles controlados por la aplicación. El contrato API puede usar IDs internamente, pero el campo de texto manual no existe en la interfaz.
- Toda mutación valida dependencias, reglas de protección y concurrencia básica antes de confirmar. Los errores usan 401 para sesión inválida, 403 para permiso insuficiente, 404 para recurso inexistente, 409 para conflicto y 422 para una regla de negocio o validación.
- Se auditan inicio de sesión, alta, edición, cambio de contraseña, cambio de estado, cambio de roles, cambio de permisos y cambio de menú. El detalle no guarda contraseñas, tokens ni datos sensibles.
- Las eliminaciones usan `DELETE`, validan dependencias en el backend y se auditan como eliminación; no dependen de que React o una clave foránea silenciosa decidan el resultado.

## 5. Criterios de aceptación

- [ ] Crear y editar un usuario permite seleccionar uno o varios roles activos en una tabla de casillas con nombre y descripción; no existe entrada manual de IDs. Al editar, una contraseña vacía conserva la existente.
- [ ] Cambiar de Usuarios a cualquier otra vista limpia la selección y no se muestra información, `undefined` ni valores de Usuarios en otro formulario.
- [ ] El administrador inicial no se puede desactivar ni dejar sin rol administrativo protegido mediante API ni interfaz.
- [ ] El rol administrativo inicial no se puede desactivar, modificar en su clave técnica ni dejar sin la capacidad mínima de recuperación.
- [ ] La pantalla Roles permite marcar o desmarcar permisos en una tabla legible, guarda mediante `PUT /roles/{id}/permissions` y no solicita números ni códigos de permiso.
- [ ] Crear o editar un usuario con roles devuelve `201` o `200` y presenta la fila creada/actualizada; la serialización de roles no provoca un error de carga diferida después de confirmar la transacción.
- [ ] Permisos presenta un catálogo explicado por nombre, descripción y categoría. Un permiso arbitrario no se puede dar de alta desde el navegador.
- [ ] Menús usa catálogos y ayudas; no permite configurar una ruta o clave que no corresponda a una pantalla registrada.
- [ ] Todas las listas de Seguridad son paginadas, buscables cuando corresponde, tienen estado vacío/carga/error y exponen acciones sólo si el JWT tiene permiso.
- [ ] FastAPI rechaza de forma verificable una petición directa sin permiso o que viole una invariante de recuperación, incluso si la interfaz fue manipulada.
- [ ] Auditoría registra los cambios administrativos sin secretos y permite consultarlos sin modificarlos.
- [ ] Eliminar un padre con dependencias hijas devuelve `409`, explica qué asociaciones deben resolverse y no borra ningún dato; tras resolverlas, una eliminación permitida queda auditada como `delete`.
- [ ] Un usuario no protegido y sin asignaciones usuario--rol puede eliminarse aunque haya sido actor de eventos de auditoría; los eventos permanecen, conservan su etiqueta histórica segura y su referencia `actor_user_id` queda vacía.
