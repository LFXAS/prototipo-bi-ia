# SPR-03-04: parametrización web mínima de conexiones y secretos

- Estado: **implementada salvo validación de dependencias futuras**.
- Pertenece a: [SPR-03-metadatos-y-propuesta-bi.md](SPR-03-metadatos-y-propuesta-bi.md).
- Complementa la corrección de credenciales LLM de [SPR-02-03](SPR-02-03-parametros-y-llm.md).
- Fecha de revisión: 2026-09-14.

## 1. Objetivo

Una persona administradora debe poder preparar el prototipo desde la plataforma web. No debe editar `.env`, Compose, código ni registros de PostgreSQL para configurar Gemini, Qwen o la fuente de ventas.

La implementación se limita a una solución académica segura y comprobable:

- un formulario LLM que registra o reemplaza la API key;
- un formulario de conexión SQL Server;
- una sola fuente activa;
- un almacén cifrado común para ambas credenciales;
- cuatro parámetros numéricos y un catálogo analítico por dominio, con permisos separados, realmente consumidos por el Sprint 3.

No se construirá una plataforma universal de conexiones ni un gestor empresarial de secretos.

## 2. Valor para el producto y la investigación

La parametrización web permite que el software sea operado por sus perfiles reales:

- el administrador prepara la fuente y el LLM sin intervenir archivos;
- el analista BI utiliza el asistente sin conocer credenciales y el gerente consume posteriormente los resultados del negocio;
- el experimento puede repetirse en otra instalación registrando los valores desde la misma interfaz;
- el equipo puede demostrar separación entre configuración, interpretación del LLM, validación del sistema y decisión humana.

Este soporte no es la contribución principal de la tesis, pero elimina una barrera técnica que impediría usar y evaluar el asistente como producto para usuario final.

## 3. Alcance obligatorio

### 3.1 Corrección del Sprint 2: credencial LLM

En **Parámetros generales > Configuración LLM**, Gemini y Qwen Cloud incorporan la acción **Registrar/Reemplazar credencial**. La clave se envía una vez, se cifra en FastAPI y posteriormente la pantalla sólo muestra **Credencial configurada**. Ollama local conserva el estado **No requiere credencial**.

Cada configuración incorpora un **Nivel de razonamiento** controlado: automático, mínimo, bajo, medio o alto. El adaptador Gemini aplica el valor soportado por el modelo; mínimo es el valor inicial para priorizar rapidez y evitar que una respuesta JSON acotada consuma su presupuesto en razonamiento interno. Cambiar proveedor, URL, modelo o nivel invalida la última prueba y exige ejecutar **Probar conexión** nuevamente. Ollama y Qwen conservan en este sprint el comportamiento seguro definido por sus adaptadores; la interfaz no promete niveles que el modelo no soporte.

La transición de una instalación existente es manual y controlada: el administrador vuelve a ingresar la clave en la web y prueba el proveedor. `GEMINI_API_KEY` y `DASHSCOPE_API_KEY` se retiraron de la plantilla y de Compose; no se implementa importación automática.

### 3.2 Conexión SQL Server

En **Parámetros generales > Conexiones de datos**, el formulario contiene:

- nombre visible;
- servidor;
- puerto;
- base de datos;
- usuario;
- contraseña;
- cifrado de transporte y confianza del certificado mediante opciones controladas.

La pantalla permite crear, editar, probar, activar, desactivar y eliminar cuando no existan dependencias. Sprint 3 implementa sólo SQL Server y valida el recorrido con AdventureWorks2022. El nombre del servidor y de la base no quedan codificados en la aplicación.

### 3.3 Parámetros generales consumidos

Se reutiliza la tabla `app.parameters` del Sprint 2. Únicamente se habilitan parámetros con uso concreto:

| Clave | Uso | Rango inicial |
|---|---|---|
| `UI_PAGE_SIZE` | Cantidad predeterminada de registros por página. | 10 a 100 |
| `CONNECTION_TIMEOUT_SECONDS` | Tiempo máximo para probar la fuente. | 3 a 30 |
| `LLM_TIMEOUT_SECONDS` | Tiempo máximo para una llamada del asistente. | 10 a 120 |
| `METADATA_BLOCK_MAX_ITEMS` | Máximo de elementos técnicos por bloque enviado al LLM. | 25 a 200 |

Cada registro muestra nombre, explicación, módulo, tipo, valor, rango y valor predeterminado. El administrador puede modificarlo o restaurarlo. No puede crear claves nuevas desde la interfaz y ningún secreto se guarda como parámetro.

## 4. Diseño técnico mínimo

### 4.1 Datos

`app.data_connections` conserva configuración no secreta, estado de prueba y referencia al secreto. `app.secrets` conserva exclusivamente el valor cifrado y su tipo (`llm` o `data_source`). La tabla `app.parameters` se amplía sólo con los campos necesarios para tipo, módulo, valor predeterminado y restricciones.

No se almacenan contraseñas ni API keys en claro. No existe una operación para leerlas desde API o interfaz.

### 4.2 Cifrado

FastAPI usa una biblioteca mantenida de cifrado autenticado y una única clave local generada automáticamente durante el primer arranque. La clave se conserva en un volumen Docker separado de PostgreSQL. El prototipo no implementa rotación, múltiples claves ni integración con bóvedas externas; esas capacidades quedan como evolución productiva.

### 4.3 Conector

El backend implementa `SqlServerConnector` con cuatro responsabilidades: validar campos, probar conexión, comprobar sólo lectura e introspeccionar metadatos. Una interfaz interna pequeña permitirá agregar otro conector en el futuro, pero Sprint 3 no implementa ni muestra otros motores.

## 5. Reglas obligatorias

1. Sólo una conexión puede estar activa.
2. Una conexión sólo puede activarse después de una prueba exitosa.
3. La prueba debe confirmar conexión y ausencia de permisos de escritura con las comprobaciones disponibles para SQL Server.
4. Editar sin ingresar una nueva contraseña conserva la anterior.
5. React nunca recibe el secreto guardado.
6. Los errores y eventos de auditoría no contienen claves, contraseñas ni cadenas completas.
7. No se elimina una conexión vinculada a una instantánea o propuesta.
8. Servidor, puerto, base y opciones se validan por campo; no se acepta una cadena de conexión libre.
9. Los parámetros sólo aceptan el tipo y rango definidos.
10. Las operaciones administrativas requieren los permisos correspondientes del Sprint 2.

## 6. API mínima

| Método y ruta | Finalidad |
|---|---|
| `GET /api/v1/connections` | Listar conexiones sin secretos. |
| `POST /api/v1/connections` | Crear conexión y secreto cifrado. |
| `PUT /api/v1/connections/{id}` | Editar y reemplazar opcionalmente la contraseña. |
| `POST /api/v1/connections/{id}/test` | Probar conexión y sólo lectura. |
| `POST /api/v1/connections/{id}/activate` | Activar una fuente probada. |
| `POST /api/v1/connections/{id}/deactivate` | Desactivar sin perder historial. |
| `DELETE /api/v1/connections/{id}` | Eliminar si no tiene dependencias. |
| `PUT /api/v1/llm-configurations/{id}/secret` | Registrar o reemplazar la API key cifrada. |
| `GET /api/v1/parameters` | Listar parámetros habilitados. |
| `PUT /api/v1/parameters/{key}` | Cambiar un valor permitido. |
| `POST /api/v1/parameters/{key}/reset` | Restaurar el valor predeterminado. |
| `GET /api/v1/analysis-catalog/domains` | Listar dominios con catálogo implementado. |
| `GET/PUT /api/v1/analysis-catalog/domains/{code}` | Consultar o guardar preguntas y periodicidades del dominio. |
| `POST /api/v1/analysis-catalog/domains/{code}/reset` | Restaurar el catálogo validado. |

Las listas mantienen la paginación ya implementada. Cada escritura genera auditoría segura.

## 7. Criterios de aceptación

- [x] Gemini o Qwen puede configurarse y probarse desde la web sin depender de una API key en `.env`.
- [x] El nivel de razonamiento se selecciona desde la configuración LLM y un cambio obliga a probar nuevamente proveedor y modelo.
- [x] AdventureWorks puede registrarse, probarse y activarse desde la web sin editar archivos ni PostgreSQL.
- [x] La clave LLM y la contraseña SQL Server se almacenan cifradas y nunca se devuelven al navegador.
- [x] Una conexión con prueba fallida o permisos incompatibles no puede activarse.
- [x] Sólo una fuente permanece activa.
- [x] Los cuatro parámetros numéricos se muestran con explicación y sólo aceptan valores dentro de su rango; el catálogo analítico tiene pantalla, permisos y CRUD separados por dominio.
- [x] La auditoría identifica creación, modificación, prueba y activación sin exponer secretos.
- [ ] Las dependencias impiden eliminar una conexión utilizada.
- [x] Formularios, errores y acciones son utilizables en móvil y escritorio.
- [x] Las pruebas automatizadas y una demostración real verifican el recorrido de parametrización.

## 8. Pruebas obligatorias

- Unitarias: cifrado, ocultamiento, validación de campos, nivel de razonamiento permitido, rangos y activación única.
- API: permisos, CRUD, prueba, reemplazo de secreto, errores seguros y dependencias.
- Integración: reinicio de contenedores sin perder configuración ni capacidad de descifrar.
- Real: Gemini u Ollama para el proveedor y SQL Server/AdventureWorks para la fuente.
- Interfaz: formularios, confirmaciones, estado de credencial, paginación y responsive.

## 9. Preparado arquitectónicamente, no implementado

- Otros motores de bases de datos.
- Varias fuentes activas o combinación de fuentes.
- Campos de conexión generados dinámicamente por un catálogo universal.
- Rotación de claves, bóveda externa y administración empresarial de secretos.
- Importación automática de credenciales desde `.env`.

Documentar estos puntos demuestra evolución posible, pero no forman parte de la aceptación de la tesis ni del Sprint 3.

## 10. Configuración que seguirá perteneciendo al despliegue

Puertos, redes, imágenes, volúmenes, credenciales internas de PostgreSQL, migraciones y recursos de Docker deben aprovisionarse al instalar la aplicación. No pueden modificarse desde la misma plataforma que depende de ellos. Esta frontera no contradice la parametrización: el usuario administra desde la web toda conexión y ajuste operativo usado por el flujo BI.

## 11. Resultado de implementación

La corrección LLM se implementó con la migración `20260918_06`, la tabla `app.secrets`, cifrado autenticado, clave maestra persistente en `secret_key_data`, endpoint de registro/reemplazo, interfaz responsive y auditoría sin secretos. La migración `20260918_07` amplió el catálogo tipado de parámetros y añadió `app.data_connections`, la restricción de una sola fuente activa y los permisos `connections.read`, `connections.write` y `connections.test`.

La pantalla **Conexiones de datos** implementa registro, edición con contraseña opcional, prueba, activación, desactivación y eliminación. La prueba real con AdventureWorks confirmó conectividad y ausencia de privilegios de escritura; el estado probado y la activación permanecieron después de reiniciar FastAPI. PostgreSQL produjo cero coincidencias con las credenciales en claro. Los cuatro parámetros numéricos se pueden modificar dentro de sus rangos y restaurar, con auditoría segura. El catálogo analítico se administra en un menú independiente: permite CRUD de preguntas y varias periodicidades soportadas, pero no almacena objetivos ni dimensiones. La protección por dependencias se completará cuando `metadata_snapshots` introduzca la primera relación consumidora en SPR-03-01; hasta entonces no existe un registro hijo que bloquear.
