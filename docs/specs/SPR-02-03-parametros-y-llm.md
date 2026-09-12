# SPR-02-03: parámetros generales y configuración segura de LLM

- Estado: **implementado y verificado localmente; pendiente de revisión colaborativa y cierre mediante PR hacia `develop`**.
- Pertenece a: [SPR-02-rbac-y-parametros.md](SPR-02-rbac-y-parametros.md).
- Última revisión funcional: 2026-09-10.

## 1. Propósito

Esta capacidad evita confundir dos conceptos diferentes:

- **Parámetros generales**: valores operativos no secretos que un módulo ya implementado reconoce y consume.
- **Configuración LLM**: elección y comprobación del proveedor/modelo que usará una capacidad de IA posterior.

Una pantalla no debe mostrar datos, formularios, selecciones o mensajes pertenecientes a la otra. Tampoco debe mostrar información residual de Roles, Usuarios, Permisos o Menús.

## 2. Parámetros generales

La pantalla existe para consultar y ajustar configuraciones aprobadas sin redeplegar la aplicación. No es una tabla libre para escribir cualquier clave/valor ni una base de datos de negocio.

### 2.1 Catálogo de parámetros

Todo parámetro debe registrarse en un catálogo controlado que define:

| Atributo | Uso |
|---|---|
| Nombre visible | Explica el valor a una persona no técnica. |
| Descripción y módulo consumidor | Indica para qué sirve y qué funcionalidad cambia. |
| Clave interna | Estable y de sólo lectura; la crea una migración/especificación, no la persona usuaria. |
| Tipo y formato | Texto limitado, entero, booleano, lista aprobada o duración; permite validación antes de guardar. |
| Valor predeterminado y límites | Evita configuraciones inválidas o peligrosas. |
| Sensibilidad | Si requiere secreto, no pertenece a esta tabla ni a la interfaz. |

Ejemplos futuros permitidos cuando exista su módulo consumidor: tamaño de lote ETL, zona horaria de reporte, días de retención de auditoría o tamaño de página predeterminado. En el Sprint 2 el catálogo no contiene parámetros consumidos; por ello la pantalla muestra un estado vacío explicando que no hay configuraciones operativas habilitadas aún. El catálogo se incorporará en el sprint que entregue el primer módulo consumidor (por ejemplo ETL, reportería o analítica), junto con su especificación, validaciones, pruebas y auditoría. No debe invitar a ingresar valores arbitrarios ni presentar `undefined`.

Crear o modificar un valor muestra nombre, descripción, formato, rango, efecto y módulo consumidor. El backend valida tipo, lista permitida y límites; guarda la modificación, aplica el cambio sólo al consumidor definido y deja auditoría. Nunca guarda contraseñas, tokens, API keys, cadenas de conexión completas o instrucciones arbitrarias.

## 3. Configuración LLM

La configuración LLM prepara una única integración activa para una fase posterior de BI asistido por IA. No crea análisis, no envía datos del negocio, no produce SQL y no ejecuta más de un proveedor a la vez.

### 3.1 Campos y ayuda visible

| Campo visible | Comportamiento |
|---|---|
| Nombre de configuración | Etiqueta humana para reconocer el registro. |
| Proveedor | Selector cerrado: Gemini Cloud, Qwen Cloud u Ollama local. Cambia las ayudas y validaciones aplicables. |
| URL de servicio | Se propone desde el adaptador del proveedor y se valida. No se acepta una URL arbitraria. |
| Modelo | Selector o campo validado según proveedor, con ejemplo y ayuda. Para Ollama local, `qwen2.5:3b` es la referencia inicial recomendada por agilidad; `qwen3:4b` puede seleccionarse como alternativa de mayor capacidad. |
| Referencia de credencial | Selector informativo de `GEMINI_API_KEY`, `DASHSCOPE_API_KEY` o `No requiere clave en la red interna`; jamás es un campo para pegar una clave. |
| Estado y última prueba | Muestra si la configuración está activa, fecha, duración y resultado seguro de la última prueba. |

La interfaz explica que una clave se registra en el entorno de despliegue y no en esta pantalla. Los campos se inicializan exclusivamente con una configuración LLM seleccionada; abrir la vista sin registro muestra un estado vacío propio.

### 3.2 Prueba de conexión

1. La persona guarda una configuración válida o elige una ya creada.
2. Selecciona **Probar conexión** y confirma que la prueba no enviará datos de negocio.
3. FastAPI toma la credencial referenciada desde el entorno, usa el adaptador del proveedor, un tiempo máximo y una solicitud mínima sin contexto de la plataforma.
4. La interfaz informa éxito en una notificación verde con icono o texto de confirmación, o una causa segura en una notificación roja: clave no disponible, URL no permitida, servicio inaccesible, modelo no descargado/disponible o tiempo agotado. Para Ollama, consultar `/api/tags` valida primero el servicio y después comprueba que el modelo seleccionado esté realmente descargado. El estado visual no se reutiliza entre éxito y error.
5. Se persisten y auditan resultado, fecha y duración; no se persiste ni presenta la clave ni el contenido de la respuesta.

## 4. Reglas técnicas

- Sólo una configuración puede estar activa. Activar una desactiva la anterior en una operación auditada.
- Una configuración LLM sólo se elimina físicamente si está inactiva y tras confirmación explícita; la auditoría de su creación, prueba, actualización y eliminación se conserva.
- Gemini usa referencia `GEMINI_API_KEY`; Qwen Cloud, `DASHSCOPE_API_KEY`; Ollama local, `none` dentro de la red Docker. La interfaz sólo informa disponibilidad de la referencia, no su contenido.
- Ollama se inicia sólo bajo el perfil Compose `local-llm`. El modelo inicial `qwen2.5:3b` se descarga explícitamente con `make ollama-pull`, usa un contexto predeterminado de 2048, se conserva en el volumen local `ollama_models` y no se descarga en CI/CD ni se publica en GHCR. `qwen3:4b` es una alternativa opcional que puede requerir más tiempo y recursos.
- La configuración de Ollama Docker usa la URL interna `http://ollama:11434`. No se publica el puerto de Ollama en el host ni se requiere una API key.
- La prueba ocurre desde FastAPI, no desde React. Se validan proveedor, URL aprobada, modelo, permiso y límites antes de la llamada.
- La API responde con errores consistentes y seguros; las listas son paginadas.
- `parameters.read`/`parameters.write` protegen parámetros generales; `parameters.llm.read`, `parameters.llm.write` y `parameters.connections.test` separan la administración y prueba LLM.

## 5. Criterios de aceptación

- [ ] Parámetros generales sólo presenta configuraciones del catálogo aprobado, con nombre humano, propósito, tipo, validación y módulo consumidor; no permite claves libres ni secretos.
- [ ] Cuando no hay parámetros habilitados, se muestra estado vacío propio y no datos residuales ni `undefined` de otra pantalla.
- [ ] Configuración LLM muestra sólo sus datos y ayudas contextuales; nunca hereda el registro seleccionado de Roles, Usuarios, Permisos, Menús o Parámetros.
- [ ] El proveedor se selecciona de Gemini Cloud, Qwen Cloud u Ollama local; referencia de credencial y URL/modelo se validan según esa elección.
- [ ] La prueba de conexión se ejecuta en FastAPI, no contiene datos de negocio, no revela secretos y deja resultado seguro/auditable.
- [ ] Con Ollama local, la prueba falla de manera comprensible si el servicio no está disponible o si el modelo indicado aún no fue descargado; sólo confirma éxito cuando ambas condiciones se cumplen.
- [ ] El perfil local de Ollama es opcional, no se inicia en el flujo normal ni en CI/CD, conserva sus modelos por equipo en un volumen propio y no expone un puerto público.
- [ ] Una prueba LLM exitosa se muestra como confirmación visual verde y accesible; un fallo se muestra como alerta roja. No se presenta un éxito con estilo de error.
- [ ] La API no devuelve ni persiste claves de proveedor, contraseñas ni cadenas de conexión completas.
- [ ] Sólo una configuración LLM queda activa y el cambio conserva auditoría.
