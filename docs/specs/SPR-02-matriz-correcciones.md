# SPR-02: matriz de trazabilidad de observaciones funcionales

- Fuente revisada: `Observaciones sprint 2 - Funcionalidad de los módulos.pdf`.
- Fecha de análisis: 2026-09-10.
- Estado: implementación completada y verificada localmente; cada observación queda sujeta a revisión colaborativa mediante el PR de cierre del Sprint 2 antes de promover a `main`.

Esta matriz convierte las observaciones de revisión en requisitos comprobables. No se trata de una lista de deseos: cada fila debe cerrarse con prueba automatizada o manual, captura sin datos sensibles y referencia al cambio correspondiente.

| ID | Observación | Decisión | Especificación y evidencia esperada |
|---|---|---|---|
| OBS-01 | El grupo activo no se podía plegar. | Corregir: todo padre puede plegarse, incluso el que contiene la ruta activa. | [UX §2.1](SPR-02-02-navegacion-y-experiencia.md); prueba de interfaz y captura. |
| OBS-02 | "Principal" no aporta valor. | Eliminar como grupo; Inicio queda como acceso directo. | [UX §2](SPR-02-02-navegacion-y-experiencia.md); captura escritorio/móvil. |
| OBS-03 | Falta ocultar sidebar. | Añadir control de contraer/ocultar en escritorio y hamburguesa en móvil/tableta. | [UX §2.1](SPR-02-02-navegacion-y-experiencia.md); prueba responsive. |
| OBS-04 | Roles de usuario se escriben por ID. | Sustituir por selector múltiple con nombre, descripción y búsqueda. | [RBAC §3.1](SPR-02-01-seguridad-rbac.md); prueba de alta/edición. |
| OBS-05 | Se pudo desactivar al administrador inicial. | Proteger cuenta y recuperación administrativa en backend e interfaz. | [RBAC §2.1](SPR-02-01-seguridad-rbac.md); prueba negativa API. |
| OBS-06 | Código de rol y privilegios por IDs son difíciles y riesgosos. | Código interno controlado; permisos por selector agrupado y resumen. | [RBAC §3.2](SPR-02-01-seguridad-rbac.md); prueba de rol. |
| OBS-07 | Se puede dañar o desactivar el rol Administrador. | Rol protegido, clave inmutable e invariantes de recuperación. | [RBAC §2.1](SPR-02-01-seguridad-rbac.md); prueba negativa API. |
| OBS-08 | Catálogo de permisos poco amigable y peligroso. | Catálogo explicado/controlado; no alta arbitraria de códigos ni desactivación que rompa la recuperación. | [RBAC §3.3](SPR-02-01-seguridad-rbac.md); prueba y revisión. |
| OBS-09 | Menús piden ruta, módulo y permisos técnicos. | Menús se derivan de pantallas registradas; UI usa catálogos, ayudas y campos técnicos de sólo lectura. | [RBAC §3.4](SPR-02-01-seguridad-rbac.md); prueba de edición segura. |
| OBS-10 | Datos de edición se filtran entre pantallas y aparece `undefined`. | Estado aislado por ruta; limpiar selección al cambiar de pantalla. | [UX §3](SPR-02-02-navegacion-y-experiencia.md); prueba de navegación cruzada. |
| OBS-11 | Parámetros no explica su propósito ni debe aceptar claves libres. | Convertir en catálogo de valores aprobados con consumidor, tipo y validación. | [Parámetros §2](SPR-02-03-parametros-y-llm.md); estado vacío y prueba. |
| OBS-12 | LLM carece de ayuda y de prueba de conexión. | Formulario contextual por proveedor y prueba desde FastAPI sin datos del negocio. | [Parámetros §3](SPR-02-03-parametros-y-llm.md); doble de prueba/evidencia segura. |
| OBS-13 | Los selectores de permisos cortan textos extensos. | Los listbox de permisos otorgados y requeridos ocupan la fila completa y ajustan su ancho al contenido legible, dentro de límites responsive. | [UX §4](SPR-02-02-navegacion-y-experiencia.md); prueba visual en Roles y Menús. |
| OBS-14 | El botón textual para ocultar navegación ocupa espacio y no sigue el patrón visual deseado. | Sustituirlo en escritorio por un control compacto de chevrón superpuesto al borde del sidebar, visible también al estar oculto y sin desplazar el menú; conservar hamburguesa en móvil/tableta. | [UX §2.1](SPR-02-02-navegacion-y-experiencia.md); prueba de ocultar/restaurar. |
| OBS-15 | Un error de validación de usuario se muestra como `[object Object]`. | Traducir las respuestas estructuradas de FastAPI a mensajes por campo y usar control HTML de correo con ejemplo visible. | [UX §5](SPR-02-02-navegacion-y-experiencia.md); prueba de creación con correo inválido. |
| OBS-16 | Los CRUD requieren eliminación física segura y trazable. | Añadir eliminación confirmada, validación explícita de dependencias hijas, protección de registros de sistema y auditoría `delete`; Auditoría permanece inmutable. | [RBAC §3.6](SPR-02-01-seguridad-rbac.md); pruebas negativa y positiva de API. |
| OBS-17 | La edición de permisos de un rol responde `Method Not Allowed`, y los selectores múltiples son poco claros. | Usar `PUT /roles/{id}/permissions`; reemplazar listas de selección por tablas de casillas para roles de usuario, permisos de rol y permisos de menú. La contraseña sólo se exige al crear; vacía al editar conserva la existente. | [RBAC §3.1-3.2](SPR-02-01-seguridad-rbac.md); [UX §4](SPR-02-02-navegacion-y-experiencia.md); prueba de actualización. |
| OBS-18 | Una prueba LLM satisfactoria se presenta con estilo de error. | Separar mensajes de éxito y error: confirmación verde accesible para conexión validada; alerta roja sólo para fallos. | [Parámetros/LLM §3.2](SPR-02-03-parametros-y-llm.md); prueba de interfaz. |
| OBS-19 | La alternativa local de LLM no tenía servicio operativo ni comprobaba si el modelo estaba listo. | Añadir Ollama como perfil Docker opcional, persistir el modelo por equipo sin exponer puertos ni incorporarlo a CI, y validar servicio más modelo descargado. | [Parámetros/LLM §3.2 y §4](SPR-02-03-parametros-y-llm.md); prueba unitaria y prueba real controlada. |
| OBS-20 | Un usuario con un rol desactivado no podía retirar esa asignación y, por tanto, no podía cumplir la validación previa a su eliminación. | Al editar, mostrar el rol inactivo ya asignado con una marca visible y permitir únicamente retirarlo; las altas nuevas siguen mostrando sólo roles activos. | [RBAC §3.1](SPR-02-01-seguridad-rbac.md); prueba de interfaz para rol inactivo previamente asignado. |
