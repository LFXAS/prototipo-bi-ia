# Operación, configuración y catálogo

Fuente editorial para el manual operativo y de aprendizaje; las prácticas descritas son propuestas de capacitación y no nuevas pruebas ejecutadas durante esta auditoría de código.

Corte de código: 39383d65bda89eff123e04f28f84fd2e482909e8

## 1. Ingresar y reconocer una sesión autorizada

**Opción:** Pantalla de acceso

**Dirigido a:** Todos los perfiles

Abra la dirección de la plataforma proporcionada por la administración. En el repositorio de desarrollo, el puerto predeterminado es 5173; una entrega release o portable puede publicar otro puerto. Use la dirección de la guía de la instalación que está encendiendo. El puerto identifica el servicio: no determina sus permisos ni la base de datos que analizará.

Una cuenta representa a la persona que realiza las acciones. Sus roles reúnen permisos; por eso dos personas pueden iniciar sesión y ver opciones diferentes. La contraseña permite autenticar la cuenta, mientras que los permisos determinan si puede consultar, modificar o ejecutar una operación. Conocer la contraseña de una cuenta no convierte automáticamente a esa cuenta en administradora.

Al ingresar, compruebe el nombre mostrado en Sesión activa y los menús disponibles. Trabaje con su cuenta asignada. La cuenta administrativa inicial está protegida porque permite recuperar la administración del entorno. Su contraseña se entrega por un canal de administración y no forma parte de este manual.

La sesión puede caducar. El sistema puede recuperar el módulo y un borrador mínimo después de autenticarse otra vez. Recuperar una sesión no equivale a aprobar una propuesta ni a repetir una carga. Antes de continuar, confirme la fuente y la versión que aparecen en pantalla.

### Conceptos

- **Autenticación:** Comprobación de la identidad de una cuenta mediante sus credenciales.
- **Autorización:** Comprobación de que la cuenta tiene permiso para la acción solicitada.
- **Sesión:** Acceso temporal de una cuenta autenticada; puede vencer sin borrar los expedientes almacenados.

### Paso a paso

1. Escriba el correo de su cuenta en Correo y la clave suministrada por la administración en Contraseña.
2. Pulse Iniciar sesión una sola vez y espere a que aparezca el espacio de trabajo.
3. Compruebe su nombre en Sesión activa. Si no coincide con la cuenta que esperaba usar, pulse Cerrar sesión e ingrese con la cuenta correcta.
4. Despliegue el grupo de menú correspondiente a su tarea. Si una opción no está disponible, solicite revisar los permisos en lugar de utilizar la cuenta de otra persona.
5. Cuando termine, pulse Cerrar sesión. Esta acción cierra su acceso y elimina el borrador local del asistente; los expedientes ya guardados permanecen en el servidor.

### Campos y botones

**Correo.** Identifica la cuenta registrada. Ejemplo: El correo asignado a la estudiante; no un nombre de rol. Resultado: Se consulta esa cuenta al autenticar.

**Contraseña.** Acredita el acceso; se presenta enmascarada. Ejemplo: La clave entregada para esa cuenta. Resultado: Se valida sin devolver la contraseña guardada.

**Iniciar sesión.** Solicita la autenticación. Ejemplo: Acceder como Analista de BI con su propia cuenta. Resultado: Muestra el espacio de trabajo permitido o una explicación del rechazo.

**Cerrar sesión.** Finaliza el acceso del navegador. Ejemplo: Concluir una práctica en un equipo compartido. Resultado: Regresa al formulario de acceso; no elimina propuestas ni datamarts.

### Práctica y comprobación

**Reconocer la cuenta antes de operar.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. Ingrese con una cuenta de práctica.
2. Anote el nombre mostrado y tres opciones disponibles.
3. Cierre sesión y compruebe que vuelve el formulario.

**Resultados esperados:** La cuenta mostrada coincide con la utilizada. No se crean propuestas ni cargas por iniciar o cerrar sesión.

**Criterio:** La estudiante explica la diferencia entre acceso a la plataforma y permiso para ejecutar ETL.

### Qué hacer cuando hay problemas

**Credenciales inválidas o acceso rechazado.** Correo o clave incorrectos, cuenta desactivada o servicio no disponible. **Acción:** Verifique la dirección de la plataforma y el correo; solicite a la administración revisar el estado de la cuenta. No cambie la configuración de las bases para resolver un problema de acceso. **Comprobación:** La cuenta correcta aparece en Sesión activa.

**Token inválido o vencido.** La sesión temporal terminó. **Acción:** Autentíquese nuevamente y revise fuente, borrador y versión recuperados antes de continuar. **Comprobación:** La consulta del expediente funciona y no se ha repetido una ejecución.

**La clave aparece dentro de otro campo por autocompletado.** El navegador insertó datos guardados en un formulario. **Acción:** Limpie el dato que no corresponde y revise cada etiqueta antes de guardar. No capture ni comparta contraseñas. **Comprobación:** Correo y nombre contienen los datos previstos; los campos de claves siguen enmascarados.

### Preguntas para la sustentación

**¿La IA decide quién puede entrar?** No. El acceso y los permisos los comprueba el servidor mediante las cuentas y los roles configurados.

**¿Cerrar sesión elimina un datamart?** No. Finaliza el acceso local; los resultados persistidos se conservan. Un borrador local no guardado sí puede perderse.

## 2. Comenzar desde Inicio y completar la preparación

**Opción:** Inicio

**Dirigido a:** Administración, Analista de BI, Gerencia para reconocer su contexto

Inicio es el punto de orientación. Para una cuenta con consulta de propuestas, resume tres componentes: Fuente de ventas, Metadatos y Asistente de IA. Los tres deben estar preparados para crear una propuesta nueva. Una fuente habilitada no sustituye a sus metadatos; un modelo activo no garantiza que la pregunta comercial sea factible.

Todo está listo significa que se cumplen los prerrequisitos del asistente en ese contexto. Todavía faltan la necesidad concreta, la evaluación de su viabilidad, el diseño, la revisión humana y la ejecución del ETL. El mensaje no acredita anticipadamente que cualquier necesidad pueda resolverse.

Si el perfil no tiene consulta de propuestas, Inicio puede presentar cantidades de roles, permisos y opciones visibles en lugar de las tarjetas del asistente. Es una diferencia de acceso prevista. Para gerencia, el recorrido principal se dirige a Analítica de ventas, donde se consulta un datamart existente.

### Conceptos

- **Prerrequisito:** Condición que debe cumplirse antes de comenzar una etapa. Ejemplo: Una instantánea de metadatos antes de interpretar el esquema.
- **Metadatos:** Descripción de tablas, columnas, tipos y relaciones; no las filas comerciales.
- **Proveedor de IA:** Servicio configurado para interpretar y explicar dentro de las reglas de la plataforma.

### Paso a paso

1. Abra Inicio y compruebe Fuente en contexto.
2. Lea el estado de Fuente de ventas, Metadatos y Asistente de IA si su perfil muestra esas tarjetas.
3. Si aparece Faltan prerrequisitos, pulse Completar configuración inicial.
4. Recorra la preparación con Continuar y Atrás; use Completar este paso para abrir el módulo pendiente.
5. Si aparece Todo está listo, pulse Crear propuesta de datamart cuando vaya a iniciar un diseño. Para revisar una configuración ya válida, utilice Revisar configuración.
6. Para terminar la ayuda de preparación, utilice Cerrar preparación.

### Campos y botones

**Crear propuesta de datamart.** Abre el asistente. Ejemplo: Iniciar un diseño sobre WideWorldImporters. Resultado: Abre la etapa Necesidad; no aprueba ni carga datos.

**Completar configuración inicial.** Muestra la preparación guiada. Ejemplo: Faltan los metadatos de la conexión elegida. Resultado: Permite localizar el módulo pendiente.

**Revisar configuración.** Abre el repaso de la preparación. Ejemplo: Confirmar qué proveedor está activo. Resultado: Muestra cinco pasos de preparación sin modificar registros por sí mismo.

**Continuar / Atrás.** Recorre la ayuda inicial. Ejemplo: Pasar de Proveedor de IA a Fuente de ventas. Resultado: Cambia el paso informativo, no ejecuta una carga.

### Práctica y comprobación

**Distinguir preparación de resultados.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. Seleccione AdventureWorks y lea sus tarjetas.
2. Cambie a WideWorldImporters y repita la lectura.
3. Explique qué falta para disponer de un análisis nuevo.

**Resultados esperados:** El nombre y los metadatos se corresponden con la fuente seleccionada. La estudiante identifica que el panel analítico requiere una ejecución conciliada.

**Criterio:** No confunde Todo está listo con ETL ejecutado o propuesta aprobada.

### Qué hacer cuando hay problemas

**No se muestran las tarjetas del asistente.** El perfil carece de consulta de propuestas o no hay fuente seleccionable. **Acción:** Revise el perfil y la existencia de fuentes; gerencia puede operar el panel sin crear propuestas. **Comprobación:** La pantalla corresponde a los permisos reales, no a una supuesta cuenta universal.

**Asistente de IA no preparado.** Configuración ausente, inactiva o sin prueba vigente. **Acción:** La administración revisa Configuración LLM y realiza la prueba del registro correcto. **Comprobación:** Inicio reconoce el proveedor preparado después de la prueba válida.

### Preguntas para la sustentación

**¿Todo está listo significa que la IA ya conoce el negocio?** No. Solo indica preparación técnica. La necesidad y su compatibilidad con los metadatos se revisan en la etapa siguiente.

## 3. Navegar y conservar la fuente de trabajo

**Opción:** Fuente en contexto y navegación lateral

**Dirigido a:** Todos los perfiles autorizados

La navegación organiza la plataforma por preparación del entorno, diseño y transformación BI, análisis y decisiones, y administración y seguridad. Siga ese orden al preparar una fuente nueva. Para revisar resultados existentes, puede ir directamente a la etapa de consulta correspondiente, siempre que tenga permiso.

Cambiar fuente selecciona el origen de trabajo de su sesión. No apaga las demás conexiones ni une sus registros. Las dos bases pueden permanecer habilitadas simultáneamente. La plataforma conserva por separado sus instantáneas, catálogos, propuestas, ejecuciones y resultados.

Antes de interpretar un importe, confirme fuente, propuesta y ejecución. El nombre del origen no se debe inferir a partir de un color del gráfico. En una demostración, verbalice esta identidad al cambiar de AdventureWorks a WideWorldImporters. Si el listado no muestra una fuente, no reutilice una propuesta de otra base para simular su disponibilidad.

### Conceptos

- **Fuente:** Conexión a una base de datos concreta. Ejemplo: AdventureWorks2022 y WideWorldImporters pueden estar en el mismo servidor y seguir siendo fuentes distintas.
- **Contexto:** Selección que identifica de qué fuente y ejecución proviene la información consultada.
- **Linaje:** Relación entre origen, instantánea, propuesta, ejecución y resultado que permite explicar su procedencia.

### Paso a paso

1. Despliegue el grupo de navegación de la tarea que realizará.
2. Use Cambiar fuente y elija el nombre de la conexión y su base.
3. Espere a que se cargue el nuevo contexto antes de leer tablas, tarjetas o gráficos.
4. En el Explorador, confirme la instantánea; en el asistente, la propuesta; en el datamart o panel, la ejecución.
5. Si necesita más espacio, utilice Ocultar navegación lateral. Para recuperarla, utilice Mostrar navegación lateral.
6. En una pantalla estrecha, el botón Menú muestra las opciones disponibles.

### Campos y botones

**Cambiar fuente.** Selecciona una conexión habilitada para la sesión. Ejemplo: Alternar AdventureWorks2022 y WideWorldImporters. Resultado: Recarga los componentes dependientes de esa fuente.

**Ocultar navegación lateral / Mostrar navegación lateral.** Aprovecha el ancho de la pantalla. Ejemplo: Examinar un modelo o gráfico amplio. Resultado: Cambia la presentación; no cambia permisos ni resultados.

**Menú.** Abre la navegación en pantallas estrechas. Ejemplo: Uso en un equipo con menor resolución. Resultado: Presenta las opciones autorizadas.

**Anterior / Siguiente.** Recorre un listado paginado cuando tiene más registros. Ejemplo: Buscar una instantánea más antigua. Resultado: Cambia el tramo de resultados del listado, no la fuente por sí mismo.

### Práctica y comprobación

**Comprobar el aislamiento visible.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. Abra el Explorador con AdventureWorks y anote base e instantánea.
2. Cambie a WideWorldImporters y anote los mismos datos.
3. Abra el catálogo de cada fuente y compare su contexto.

**Resultados esperados:** Cada módulo identifica el origen elegido. No se presupone que los números de instantánea o preguntas sean iguales en otra instalación.

**Criterio:** La estudiante puede señalar la fuente y el artefacto correspondiente antes de describir un resultado.

### Qué hacer cuando hay problemas

**Falta el selector o no aparecen fuentes.** No existen conexiones habilitadas o falta Consultar metadatos, requerido por el selector actual. **Acción:** Solicite revisar las conexiones y el permiso Consultar metadatos de la cuenta. No conceda ejecución ETL para corregir un permiso de lectura. **Comprobación:** La fuente puede seleccionarse sin habilitar acciones de escritura innecesarias.

**Parece permanecer información de otra fuente.** Se leyó la pantalla antes de terminar la actualización, hay una incidencia de contexto o se abrió un expediente histórico distinto. **Acción:** Espere la carga y compruebe fuente y expediente. Si persiste, registre pantalla y pasos y detenga la interpretación de esas cifras; informe la incidencia. **Comprobación:** Los identificadores visibles y los resultados pertenecen a la misma fuente.

### Preguntas para la sustentación

**¿Por qué una empresa puede tener dos fuentes activas?** Porque cada conexión representa un origen independiente. La selección de contexto permite trabajar con una sin deshabilitar la otra.

**¿Universal significa que admite cualquier motor inmediatamente?** El flujo y los contratos se reutilizan por fuente. En este corte se implementó y validó SQL Server; otro motor necesita su conector y pruebas.

## 4. Crear y mantener cuentas de usuario

**Opción:** Administración y seguridad > Usuarios

**Dirigido a:** Administración

Una cuenta se crea para una persona, no para una base de datos. Los roles asignados determinan sus permisos efectivos en toda la plataforma. La misma cuenta de analista puede seleccionar las fuentes habilitadas para el flujo disponible; el sistema no crea automáticamente una cuenta por conexión.

En Usuarios, el formulario se encuentra en la propia pantalla. Para crear se completan Correo, Nombre completo, Contraseña y Roles asignados, y se pulsa Crear registro. En edición, el correo identifica a la cuenta y permanece en consulta. Una contraseña vacía conserva la existente; escribir una nueva la sustituye.

No es necesario escribir identificadores numéricos: los roles se eligen por nombre y descripción. Si falla la carga de roles, el formulario queda bloqueado y aparece Reintentar carga de opciones. Un error de red no debe resolverse guardando una cuenta sin sus roles previstos.

El estado true de la tabla significa activo; false significa inactivo. Una cuenta desactivada conserva su registro, pero no puede usar una sesión válida. Eliminar es una operación diferente y solicita confirmación. Los registros Protegido y la recuperación administrativa tienen controles adicionales; la administración inicial no debe desaparecer como parte de una práctica.

### Conceptos

- **Cuenta:** Identidad de acceso con correo y nombre.
- **Rol:** Conjunto de permisos asignable a una cuenta. Ejemplo: Analista BI o Gerente comercial son nombres de perfiles configurados.
- **Permisos efectivos:** Unión de permisos activos de los roles activos de la cuenta.

### Paso a paso

1. Abra Usuarios y compruebe si va a crear una cuenta o editar una existente.
2. Para una cuenta de práctica, escriba un correo no utilizado y un nombre que identifique a la persona. Defina una clave de al menos 12 caracteres sin incluirla en capturas o documentos.
3. En Roles asignados, marque los perfiles necesarios y lea su descripción.
4. Pulse Crear registro y verifique la nueva fila.
5. Para editar, pulse Editar en la fila exacta. Cambie el nombre o roles; deje Contraseña vacía si no desea cambiarla.
6. Pulse Guardar cambios y vuelva a abrir la misma fila para comprobar las asociaciones. Utilice Cancelar si no desea guardar.
7. La prueba completa del perfil requiere iniciar sesión con esa cuenta y verificar operaciones permitidas y denegadas; la lista de casillas por sí sola no lo demuestra.

### Campos y botones

**Correo.** Identifica una cuenta nueva y no se edita después desde esta pantalla. Ejemplo: Correo asignado a la persona. Resultado: Evita que se confunda el nombre visible con el identificador de acceso.

**Nombre completo.** Permite reconocer a quien opera y atribuirle acciones. Ejemplo: Nombre de la estudiante, no su correo. Resultado: Se usa como identificación visible de la cuenta.

**Contraseña.** Establece o cambia la clave. Ejemplo: Al editar, dejar vacío para conservarla. Resultado: Se guarda protegida y no vuelve a mostrarse.

**Roles asignados.** Concede los roles seleccionados. Ejemplo: Marcar Gerente comercial para consulta. Resultado: La cuenta recibe los permisos de sus roles activos.

**Desactivar / Activar.** Cambia la disponibilidad de una cuenta no protegida. Ejemplo: Desactivar una cuenta de práctica que ya no se usa. Resultado: El registro permanece; el acceso se deniega si está inactivo.

**Eliminar.** Solicita eliminación definitiva de una cuenta no protegida. Ejemplo: Retirar una cuenta temporal autorizada. Resultado: El servidor valida dependencias y conserva la evidencia histórica segura que corresponda.

### Práctica y comprobación

**Editar sin cambiar la contraseña.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. En un entorno de capacitación, abra una cuenta no protegida.
2. Cambie únicamente su Nombre completo y deje Contraseña vacía.
3. Guarde y vuelva a consultar la fila.
4. Compruebe acceso con las credenciales conocidas de esa cuenta cuando corresponda.

**Resultados esperados:** El nombre se actualiza. No se simula un cambio de correo ni se exige reemplazar la clave para editar los roles.

**Criterio:** La cuenta conserva el correo y la contraseña previstos y recibe solo los roles seleccionados.

### Qué hacer cuando hay problemas

**No se pueden cargar los roles.** Permiso Consultar roles ausente o fallo al consultar el catálogo. **Acción:** Solicite revisar el permiso complementario y utilice Reintentar carga de opciones. No guarde hasta que la tabla sea la correcta. **Comprobación:** El formulario vuelve a habilitarse y muestra los roles esperados.

**El correo no cambia al editar.** Es un campo de consulta en la edición vigente. **Acción:** Mantenga el correo original. Si se necesita otra identidad de acceso, acuerde con la administración el tratamiento de la cuenta; no anuncie un cambio no admitido. **Comprobación:** La fila conserva el correo que identifica la cuenta.

**No se permite eliminar o desactivar.** Cuenta protegida, sesión propia o control de recuperación/dependencias. **Acción:** Lea la causa y utilice una cuenta de práctica autorizada. No altere directamente PostgreSQL para eludir el control. **Comprobación:** La vía de administración permanece disponible.

### Preguntas para la sustentación

**¿Por qué no se cambia el correo al editar?** La cuenta se identifica con ese correo y el contrato de edición no admite modificarlo. La pantalla lo muestra en consulta para evitar simular un cambio.

**¿Ver las casillas marcadas prueba la seguridad del rol?** No. Permite revisar la configuración; la verificación operativa exige autenticar la cuenta y probar permisos permitidos y denegados.

## 5. Definir roles según las responsabilidades

**Opción:** Administración y seguridad > Roles

**Dirigido a:** Administración

Diseñe primero la responsabilidad y después sus permisos. La administración prepara el entorno y el acceso; el analista convierte necesidades en diseños y resultados verificados; la gerencia consulta, interpreta y exporta. El nombre del rol es una etiqueta: llamar a un rol Gerente comercial no le concede automáticamente permisos de lectura.

En Crear rol se escriben Nombre y Descripción y se marcan Permisos otorgados. El sistema genera la clave interna. Use los nombres y las explicaciones de la tabla; no necesita conocer códigos técnicos para operar. Al editar un rol, una casilla retirada deja de formar parte de sus permisos al guardar.

La instalación base garantiza el rol administrativo protegido; Analista BI, Gerente comercial y otros perfiles pueden ser configuraciones locales de la demostración. Una copia limpia puede requerir crearlos o asignarlos. Por eso este manual distingue la matriz recomendada de la evidencia de una instalación concreta.

Tras una modificación, vuelva a abrir el rol para comprobar nombre y casillas. La edición de datos y de permisos utiliza operaciones separadas: si aparece un error después de una actualización parcial, revise qué quedó guardado y complete la corrección. No dé por sentado que todo se guardó por haber pulsado el botón.

Eliminar y Desactivar tienen efectos distintos. Eliminar borra definitivamente un rol no protegido y exige que ya no tenga asignaciones a usuarios ni permisos asociados; también cuentan las asociaciones existentes aunque el usuario o el permiso estén inactivos. La plataforma no retira esas relaciones automáticamente para permitir el borrado. Si se busca suspender el uso del perfil y conservar su definición, debe evaluarse Desactivar en lugar de eliminarlo.

### Conceptos

- **Mínimo privilegio:** Conceder solo las operaciones necesarias para una responsabilidad.
- **Consulta y administración:** Leer un recurso y modificarlo son permisos diferentes. Ejemplo: Consultar catálogo no equivale a Administrar catálogo.
- **Rol protegido:** Perfil del sistema con controles que conservan la recuperación administrativa.

### Paso a paso

1. Liste las tareas del perfil que va a crear. Para gerencia: consultar el panel, seleccionar fuentes y exportar resultados.
2. Abra Roles y complete Nombre y Descripción.
3. Marque los permisos necesarios en Permisos otorgados. Para un rol con selector de fuentes, incluya Consultar metadatos.
4. Pulse Crear registro. Para modificar uno existente, abra Editar, ajuste las casillas y pulse Guardar cambios.
5. Vuelva a abrir el rol y coteje sus permisos con la matriz acordada.
6. Asigne el rol a una cuenta en Usuarios y compruebe el recorrido autenticado. Si se retiró un permiso, verifique también que la operación correspondiente se deniega.

### Campos y botones

**Nombre.** Identifica el perfil en Usuarios y Roles. Ejemplo: Gerente comercial. Resultado: Produce una etiqueta legible y una clave interna generada.

**Descripción.** Explica qué puede hacer ese perfil. Ejemplo: Consulta resultados y exporta informes, sin ejecutar ETL. Resultado: Facilita una asignación de cuentas con criterio.

**Permisos otorgados.** Define el alcance real de las acciones. Ejemplo: Consultar análisis visual y Exportar reportes analíticos. Resultado: El servidor utiliza estos permisos al autorizar.

**Editar.** Abre el perfil concreto. Ejemplo: Revisar un rol existente antes de agregar otro similar. Resultado: Muestra sus datos y permisos actuales.

**Desactivar / Activar.** Cambia el uso de un rol no protegido. Ejemplo: Retirar temporalmente un perfil de capacitación. Resultado: Los permisos de un rol inactivo no aportan acceso efectivo.

**Protegido.** Identifica controles especiales del registro. Ejemplo: Rol Administrador inicial. Resultado: No equivale a una acción que deba pulsarse ni a un error.

**Eliminar.** Borra físicamente un rol no protegido que no conserve asignaciones a usuarios ni permisos. Aparece en las filas no protegidas cuando la cuenta puede administrar roles. Ejemplo: Un rol de práctica vacío y sin asignaciones; es un ejemplo propuesto, no un borrado realizado durante esta edición. Resultado: Solicita confirmación: «Eliminar definitivamente… Esta acción no se puede deshacer». Cancelar conserva el registro. Tras confirmar, el servidor comprueba permisos, protección y dependencias; si autoriza el borrado, la fila desaparece al actualizarse la lista y se registra el evento en Auditoría.

### Práctica y comprobación

**Explicar un perfil de gerencia.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. Consulte el rol de gerencia si existe o prepare su matriz antes de crearlo.
2. Identifique consulta del panel, exportación y consulta de metadatos.
3. Confirme que no requiere preparar materializaciones ni revisar propuestas.

**Resultados esperados:** Se distingue lectura analítica de escritura técnica. La estudiante explica la dependencia del selector de fuentes.

**Criterio:** Puede justificar cada permiso del perfil sin conceder administración general por comodidad.

### Qué hacer cuando hay problemas

**La tabla de permisos no carga.** Falta Consultar permisos o hay un fallo de red. **Acción:** Revise el permiso complementario y pulse Reintentar carga de opciones. **Comprobación:** No queda habilitado el guardado de una selección vacía por error.

**El rol parece correcto, pero la cuenta no accede.** El rol o la cuenta están inactivos, falta la asignación o no se concedió una dependencia de interfaz. **Acción:** Revise estado, asignación y permisos; autentique otra vez para actualizar la navegación. **Comprobación:** La operación se autoriza en el servidor y la navegación corresponde a la cuenta.

**No se permite retirar ciertos permisos del administrador.** La modificación dañaría la recuperación del entorno. **Acción:** Mantenga el rol protegido y cree un perfil separado para la práctica. **Comprobación:** Permanece una administración activa y recuperable.

**Eliminar informa que primero se resuelvan asignaciones a usuarios o de permisos.** El rol tiene relaciones persistidas. No basta con que esté inactivo ni con que no haya usuarios activos. **Acción:** Lea la dependencia indicada y decida con la responsable de acceso si corresponde conservar, desactivar o retirar deliberadamente las asignaciones. No vacíe un perfil en uso sólo para completar una práctica. Si se autoriza su retiro, revise primero las cuentas afectadas. **Comprobación:** Un rechazo conserva el rol y sus relaciones. Un borrado autorizado elimina la fila de la lista y deja en Auditoría el evento de eliminación de rol.

**No aparece Eliminar o el servidor informa «El rol protegido no puede eliminarse».** Es el perfil administrativo protegido, o faltan permisos para administrar roles. **Acción:** Conserve el rol protegido y use un perfil de práctica no protegido para estudiar sus opciones. La interfaz muestra Protegido y oculta Eliminar en ese caso. **Comprobación:** El perfil de recuperación administrativo sigue disponible. La protección se comprueba también en el servidor.

### Preguntas para la sustentación

**¿Scrum Master es un rol de la plataforma?** No. Es una responsabilidad del proyecto de desarrollo. Product Owner y Scrum Master no conceden permisos de la aplicación.

**¿Es lo mismo ocultar ETL que denegar ETL?** No. El menú refleja permisos, pero la autorización de la operación se comprueba también en el servidor.

**¿Eliminar un rol equivale a desactivarlo y se puede deshacer?** No. Desactivar conserva la definición. Eliminar ejecuta un borrado físico, después de confirmar y sólo si el rol no es protegido y no tiene asignaciones de usuarios o permisos. No existe una papelera ni un botón de restauración. Crear otro perfil con el mismo nombre produce otro registro y exige volver a configurar sus permisos y asignaciones.

## 6. Interpretar el catálogo de permisos

**Opción:** Administración y seguridad > Permisos

**Dirigido a:** Administración, Personas autorizadas para consulta

Permisos es el diccionario de operaciones que los módulos conocen. Consultar propuestas BI, Generar propuestas BI y Revisar propuestas BI son capacidades distintas: consultar una versión no permite generarla ni aprobarla. La separación evita conceder escritura por el simple hecho de necesitar leer un expediente.

La pantalla vigente es informativa. Presenta nombre, descripción y estado en un listado paginado; no ofrece crear un permiso libre. Escribir un nombre como Administrar inventario no implementaría inventario ni protegería una operación real. Los permisos técnicos se incorporan cuando se desarrolla la funcionalidad correspondiente.

Algunas descripciones históricas del catálogo utilizan verbos como crear permisos o menús, pero la operación actual de la pantalla se rige por sus controles y por el servidor. Para asignar privilegios se trabaja en Roles; para conocer el significado de un permiso se consulta esta lista.

### Conceptos

- **Permiso:** Autorización concreta que protege una operación implementada.
- **Permiso de lectura:** Permite consultar sin modificar el recurso.
- **Permiso declarado:** Entrada del catálogo; no demuestra por sí misma que exista una nueva función utilizable.

### Paso a paso

1. Abra Permisos.
2. Lea el nombre y la descripción de las operaciones que correspondan a su tarea.
3. Use Anterior o Siguiente si el listado tiene más de una página.
4. Regrese a Roles para conceder o retirar esos permisos del perfil correspondiente.
5. Compruebe el resultado con una cuenta de ese perfil; no modifique códigos internos ni datos directamente.

### Campos y botones

**Elemento.** Presenta el nombre del permiso. Ejemplo: Revisar propuestas BI. Resultado: Permite identificar una capacidad con lenguaje comprensible.

**Detalle.** Describe el alcance funcional. Ejemplo: Aprobar o rechazar propuestas validadas. Resultado: Ayuda a diferenciar revisión de mera consulta.

**Estado.** Indica si el permiso está activo. Ejemplo: true en el catálogo aprobado. Resultado: Un permiso inactivo no aporta acceso efectivo.

**Anterior / Siguiente.** Recorre el catálogo vigente. Ejemplo: Consultar la segunda página de los 29 permisos base. Resultado: Muestra otro tramo del listado sin crear registros.

### Práctica y comprobación

**Separar tres permisos del asistente.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. Localice Consultar propuestas BI, Generar propuestas BI y Revisar propuestas BI.
2. Asocie a cada uno una tarea.
3. Explique cuál requiere un analista revisor y cuál puede necesitar una persona que solo consulta.

**Resultados esperados:** Las tareas se vinculan con permisos diferentes.

**Criterio:** La estudiante no atribuye aprobación al permiso de lectura.

### Qué hacer cuando hay problemas

**No existe el permiso que se desea escribir.** La capacidad no está implementada o se está buscando por un nombre diferente. **Acción:** Revise el catálogo por su descripción y consulte la especificación; no intente crear códigos desde el navegador. **Comprobación:** Se asigna una capacidad existente o se reconoce correctamente una ampliación pendiente de desarrollo.

### Preguntas para la sustentación

**¿Agregar un permiso implementa una función?** No. Un permiso protege una operación existente. La funcionalidad requiere código, controles y pruebas propios.

## 7. Ajustar los nombres y el orden de los menús

**Opción:** Administración y seguridad > Menús

**Dirigido a:** Administración

Un menú es la entrada visible a una pantalla ya implementada. Cambiar su etiqueta ayuda a la navegación, pero no crea un nuevo módulo ni cambia el contrato de la operación. La aplicación conserva las rutas y claves internas; el formulario permite ajustar Etiqueta visible, Posición y Permisos requeridos.

Primero seleccione Editar en un menú registrado. No hay una operación normal para inventar una ruta o agregar una pantalla desde esta lista. En el catálogo base, los menús están protegidos: puede haber datos de presentación editables, pero no se permite eliminarlos o desactivarlos como si fueran registros de práctica.

Los grupos de navegación tienen un orden común y las opciones se organizan dentro de ellos. Un número de posición menor sitúa antes una opción dentro del orden aplicable. Con varios permisos asociados, el servidor de navegación muestra actualmente el menú si la cuenta posee al menos uno de ellos; cada acción sigue exigiendo su permiso específico. Por ello, la configuración del menú no sustituye al control de acceso.

### Conceptos

- **Menú:** Acceso de navegación a una pantalla registrada.
- **Etiqueta:** Nombre que lee la persona usuaria; es distinto de la ruta técnica.
- **Posición:** Valor de orden; no es un identificador de permiso ni una prioridad comercial.

### Paso a paso

1. Abra Menús y localice la entrada que necesita ajustar.
2. Pulse Editar en esa fila.
3. Cambie Etiqueta visible solo si mejora la comprensión y mantiene la función real.
4. Ajuste Posición y revise Permisos requeridos.
5. Pulse Guardar cambios o Cancelar.
6. Actualice la sesión para volver a consultar la navegación y compruebe la etiqueta con la cuenta destinataria.

### Campos y botones

**Etiqueta visible.** Define el nombre de navegación. Ejemplo: Conservar Analítica de ventas como nombre preciso. Resultado: Modifica la presentación del menú registrado.

**Posición.** Ordena la entrada. Ejemplo: Una posición anterior dentro de su grupo. Resultado: Reordena la navegación aplicable, no concede permisos.

**Permisos requeridos.** Asocia condiciones de visibilidad del menú. Ejemplo: Consultar análisis visual para la entrada del panel. Resultado: Influye en la navegación; el servidor sigue validando la operación.

**Guardar cambios / Cancelar.** Confirma o abandona la edición. Ejemplo: Ajustar una etiqueta sin cambiar una ruta. Resultado: El registro se actualiza o se conserva como estaba.

### Práctica y comprobación

**Reconocer menú y operación.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. Consulte la entrada Datamart de ventas y la entrada Analítica de ventas.
2. Identifique sus funciones y los permisos de consulta asociados.
3. Explique por qué abrir el panel no permite ejecutar una carga.

**Resultados esperados:** Se distingue navegación, consulta y ejecución.

**Criterio:** Puede justificar la separación sin intentar crear rutas nuevas.

### Qué hacer cuando hay problemas

**No aparece Crear menú.** La UI solo edita pantallas ya registradas. **Acción:** Use Editar sobre una entrada existente. Para otra pantalla se necesita desarrollo e incorporación controlada. **Comprobación:** No se presenta una ruta inventada como una función operativa.

**La etiqueta cambió, pero la cuenta no ve el menú.** La sesión conserva su navegación anterior o faltan los permisos efectivos. **Acción:** Vuelva a autenticar y revise el rol; no retire la autorización del servidor para forzar la visualización. **Comprobación:** La navegación actual refleja los permisos y la etiqueta guardada.

### Preguntas para la sustentación

**¿Puedo agregar inventario escribiéndolo en Menús?** No. La pantalla, las reglas de inventario y sus pruebas deben desarrollarse antes de registrar una entrada operativa.

## 8. Consultar la auditoría y reportar una incidencia

**Opción:** Administración y seguridad > Auditoría

**Dirigido a:** Administración, Personas con Consultar auditoría

La auditoría registra acciones críticas y ayuda a reconstruir quién actuó sobre un recurso. Sirve para investigar una modificación o acompañar un expediente. No reemplaza la conciliación de importes: un evento de ejecución informa que hubo una acción, mientras que el expediente muestra las comprobaciones y sus resultados.

La interfaz actual presenta una lista paginada de eventos recientes, con acción, actor y tipo de recurso. Algunas acciones aparecen con claves técnicas, como copilot.catalog.update o etl.execution.run. Deben interpretarse como actualización del catálogo y ejecución de carga, respectivamente. No son instrucciones que la estudiante deba ejecutar.

Esta pantalla es de consulta. No se crean, corrigen ni eliminan eventos para que una demostración parezca exitosa. Si una cuenta fue retirada, la evidencia puede conservar su etiqueta histórica. Para un reporte útil, acompañe la pantalla con la fuente, la propuesta o ejecución afectada y los pasos que reprodujeron la incidencia.

### Conceptos

- **Evento de auditoría:** Registro de una acción realizada sobre un recurso.
- **Actor:** Cuenta atribuida a la acción.
- **Recurso:** Objeto sobre el que se actuó. Ejemplo: Una propuesta, un catálogo, una conexión o una ejecución.

### Paso a paso

1. Abra Auditoría.
2. Lea los eventos más recientes y distinga acción, actor y recurso.
3. Use Siguiente o Anterior para revisar eventos anteriores.
4. Si investiga un caso, abra por separado su expediente para comprobar estado y cifras.
5. Describa la incidencia con pasos, fuente e identificadores; adjunte la captura sin claves ni tokens.

### Campos y botones

**Elemento.** Muestra la acción registrada. Ejemplo: Inicio de sesión o copilot.catalog.update. Resultado: Identifica qué tipo de operación ocurrió.

**Detalle.** Permite reconocer al actor histórico. Ejemplo: Nombre y correo de la cuenta de práctica. Resultado: Ayuda a atribuir la acción sin mostrar credenciales.

**Estado.** En esta tabla puede representar el tipo de recurso. Ejemplo: etl_execution. Resultado: No debe interpretarse automáticamente como éxito o fracaso del ETL.

**Anterior / Siguiente.** Recorre los eventos. Ejemplo: Revisar operaciones anteriores de una campaña. Resultado: Cambia la página de consulta; no filtra por actor automáticamente.

### Práctica y comprobación

**Relacionar un evento con su expediente.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. Consulte un evento de ejecución existente.
2. Identifique su tipo de recurso.
3. Abra el expediente correspondiente desde Datamart de ventas y revise conciliación.

**Resultados esperados:** Se usan dos evidencias complementarias: acción auditada y resultado cuantitativo.

**Criterio:** La estudiante no utiliza la mera presencia del evento como prueba de igualdad de importes.

### Qué hacer cuando hay problemas

**No encuentra filtros por fecha o actor.** La UI de este corte solo ofrece paginación. **Acción:** Revise las páginas disponibles o solicite apoyo técnico para una consulta autorizada. No siga instrucciones de un manual anterior que anuncien filtros inexistentes. **Comprobación:** La investigación documenta el alcance real de la consulta.

**Aparece una acción técnica difícil de comprender.** El evento conserva el nombre interno de la operación. **Acción:** Asóciela con el módulo y consulte el expediente; registre la clave literal si necesita reportar una incidencia. **Comprobación:** El reporte identifica qué se hizo, sin inventar su resultado.

### Preguntas para la sustentación

**¿Se puede borrar un error de la auditoría?** No desde la interfaz. La auditoría conserva acciones y aporta trazabilidad; la solución del problema se registra mediante nuevas acciones válidas.

## 9. Registrar, probar y habilitar fuentes de datos

**Opción:** Preparación del entorno > Conexiones de datos

**Dirigido a:** Administración

Una conexión identifica dónde se encuentra una base de datos y con qué cuenta de lectura puede consultarla la aplicación. En este corte, Motor muestra SQL Server y no es una opción libre para escoger otros motores. El sistema reutiliza el mismo flujo para diferentes bases SQL Server; registrar el nombre de MySQL no incorpora un conector que no existe.

Servidor se interpreta desde el contenedor del backend. En una instalación Compose del proyecto, sqlserver es el nombre interno del servicio y 1433 su puerto interno. No lo sustituya por localhost ni por el puerto publicado del host por costumbre: localhost dentro de un contenedor se refiere a ese mismo contenedor. Para un servidor externo, la administración proporciona el host y puerto accesibles desde el backend.

AdventureWorks2022 y WideWorldImporters pueden compartir servidor y puerto, pero llevan conexiones distintas porque cambia Base de datos y pueden cambiar sus credenciales. Nunca use una cuenta administrativa de escritura para el flujo BI. La prueba verifica acceso de lectura y ausencia de privilegios de escritura relevantes; una prueba rechazada por tener escritura exige corregir el usuario del origen.

Registrar conserva una configuración deshabilitada; Probar conexión comprueba sus condiciones; Habilitar la ofrece en el selector. Son tres acciones diferentes. Varias fuentes pueden estar habilitadas a la vez. Una fila habilitada muestra Probar conexión, Leer metadatos y Deshabilitar cuando la cuenta tiene los permisos correspondientes; no muestra Editar. El código ofrece edición solo para una conexión deshabilitada. No elimine una conexión que tiene expedientes para intentar corregir una captura: el servidor controla sus dependencias.

### Conceptos

- **Servidor y base:** El servidor aloja una o varias bases; la base selecciona el origen concreto.
- **Solo lectura:** Cuenta destinada a consultar el origen sin modificar sus tablas.
- **Cifrar transporte:** Protección de la conexión hacia el servidor.
- **Confiar en certificado local:** Aceptación del certificado de la instalación local prevista; no equivale a validar públicamente su identidad.

### Paso a paso

1. Abra Conexiones de datos y revise si la conexión ya está registrada.
2. Si necesita una nueva, complete Nombre visible, Servidor, Puerto, Base de datos y Usuario de sólo lectura con los datos de la instalación.
3. Introduzca la contraseña suministrada para ese usuario. Revise Cifrar transporte y Confiar en certificado local con la administración.
4. Pulse Registrar conexión y compruebe su fila.
5. Pulse Probar conexión; continúe cuando Validación indique Sólo lectura validada.
6. Pulse Habilitar para que aparezca en Cambiar fuente.
7. Pulse Leer metadatos si tiene permiso de actualización, o continúe desde el Explorador.
8. No busque Editar en una fila habilitada. Si la administración necesita cambiar esa conexión, debe planificar su deshabilitación; la edición está prevista para el estado deshabilitado. No deshabilite una fuente solo para reproducir una captura del manual.

### Campos y botones

**Nombre visible.** Distingue la fuente en los módulos. Ejemplo: AdventureWorks local o WideWorldImporters local. Resultado: Se reconoce el origen sin depender del orden del selector.

**Motor.** Indica el conector implementado. Ejemplo: SQL Server, deshabilitado para edición. Resultado: Evita presentar soporte de un motor inexistente.

**Servidor / Puerto.** Determina el destino de red visto por el backend. Ejemplo: sqlserver y 1433 en Compose, cuando corresponde a esa instalación. Resultado: Se intenta conectar al servidor definido.

**Base de datos.** Selecciona la base dentro del servidor. Ejemplo: AdventureWorks2022 o WideWorldImporters. Resultado: Los metadatos posteriores se capturan de esa base.

**Usuario de sólo lectura / Contraseña.** Acredita el acceso de consulta al origen. Ejemplo: Usuario preparado por la administración de la instalación. Resultado: La contraseña se guarda cifrada y no se devuelve al navegador.

**Cifrar transporte / Confiar en certificado local.** Configura las condiciones de transporte admitidas. Ejemplo: Certificado local del contenedor de demostración. Resultado: Permite la conexión prevista sin confundir certificado local con identidad pública.

**Probar conexión.** Comprueba lectura y permisos relevantes. Ejemplo: Probar cada una de las dos fuentes. Resultado: Registra estado y fecha de la prueba.

**Habilitar / Deshabilitar.** Ofrece o retira la fuente del contexto seleccionable. Ejemplo: Mantener ambas habilitadas para alternar análisis. Resultado: No fusiona bases ni borra sus expedientes.

**Leer metadatos.** Captura la estructura de una fuente habilitada. Ejemplo: Crear la instantánea inicial de WideWorldImporters. Resultado: Genera o reutiliza una instantánea, sin enviar filas a la IA.

**Eliminar.** Retira una conexión deshabilitada sin dependencias que lo impidan. Ejemplo: Conexión temporal creada por error, con autorización. Resultado: No sirve para borrar indiscriminadamente el historial BI.

### Práctica y comprobación

**Reconocer dos bases en un mismo servidor.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. Consulte las dos conexiones existentes.
2. Compare servidor, puerto y Base de datos.
3. Seleccione cada una desde Cambiar fuente y compruebe su nombre.

**Resultados esperados:** Pueden coincidir servidor y puerto, pero las bases y sus contextos son diferentes.

**Criterio:** La estudiante distingue conexión, servidor y base sin cambiar credenciales para la práctica.

### Qué hacer cuando hay problemas

**No se puede conectar al servidor.** Host o puerto incorrectos desde el backend, servicio apagado o red no disponible. **Acción:** Revise los datos con la guía de instalación. En Compose, compruebe el nombre interno del servicio; no cambie a localhost por ensayo sin criterio. **Comprobación:** Probar conexión responde y registra una fecha actual.

**La prueba detecta permisos de escritura.** El usuario del origen tiene privilegios superiores a los admitidos. **Acción:** Solicite un usuario de lectura o ajuste sus permisos en SQL Server mediante la administración. No se corrige desmarcando Cifrar transporte. **Comprobación:** La prueba acredita solo lectura antes de habilitar.

**Habilitar no está disponible.** No hay prueba satisfactoria vigente. **Acción:** Corrija la causa y use Probar conexión. **Comprobación:** La fila pasa a Sólo lectura validada y permite habilitar.

**Eliminar es rechazado.** La conexión está activa o tiene dependencias. **Acción:** Deshabilite solo si corresponde y lea las dependencias. Mantenga los registros que respaldan propuestas o ejecuciones. **Comprobación:** No se destruye el origen de los expedientes para resolver un problema de configuración.

### Preguntas para la sustentación

**¿Registrar ya lee todas las ventas?** No. Conserva la conexión. La prueba consulta condiciones de acceso, la introspección lee estructura y la ejecución ETL posterior obtiene las filas autorizadas.

**¿Habilitar WideWorldImporters apaga AdventureWorks?** No. Las fuentes se habilitan independientemente y la sesión elige con cuál trabajar.

## 10. Ajustar parámetros con un propósito concreto

**Opción:** Preparación del entorno > Parámetros

**Dirigido a:** Administración

Los parámetros son ajustes operativos aprobados, no un lugar para guardar claves, contraseñas o fórmulas del negocio. La pantalla muestra el nombre, una explicación, el valor actual, el rango admitido y el predeterminado. Modifique un parámetro cuando pueda explicar qué problema operativo intenta resolver.

Tiempo máximo del asistente expresa cuánto esperará la aplicación una solicitud; no concede más capacidad semántica al modelo. Si un proveedor devuelve un contrato inválido, aumentar el tiempo no vuelve correcto ese contrato. Elementos por bloque de metadatos controla la organización del contexto técnico; no selecciona cuántas filas de ventas se cargarán.

Cada tarjeta tiene su propio Guardar y Restaurar. Guardar una tarjeta no debe darse por entendido como guardar todas las demás. Anote el valor anterior y cambie una cosa a la vez para poder observar el efecto. Restaurar recupera el predeterminado de ese parámetro, no la configuración completa de la aplicación.

En el código de este corte, los listados de la pantalla principal solicitan diez registros de forma explícita. Aunque Registros por página puede guardarse, no se debe prometer que cambie todos los listados inmediatamente. La capacitación debe comprobar el efecto visible antes de utilizarlo como demostración de parametrización.

### Conceptos

- **Tiempo máximo:** Límite de espera de una operación, expresado en segundos.
- **Predeterminado:** Valor de referencia que se recupera al restaurar la tarjeta.
- **Bloque de metadatos:** Grupo de elementos estructurales usado para organizar el contexto del asistente; no es un lote de ventas.

### Paso a paso

1. Abra Parámetros y lea la tarjeta que desea ajustar.
2. Anote valor actual, unidad, rango y motivo del cambio.
3. Introduzca un entero dentro del rango.
4. Pulse Guardar en esa tarjeta y compruebe el mensaje de actualización.
5. Repita la lectura del valor. Si el cambio no se justifica, utilice Restaurar en esa misma tarjeta.
6. Verifique el efecto real en la operación correspondiente; no infiera eficacia por el solo hecho de que se guardó.

### Campos y botones

**Tiempo máximo de conexión.** Limita la espera al probar una fuente. Ejemplo: Predeterminado 8 segundos; rango 3–30. Resultado: Afecta el límite de espera de la prueba, no los permisos SQL.

**Tiempo máximo del asistente.** Limita la espera de la solicitud al proveedor. Ejemplo: Predeterminado 600 segundos; rango 10–900. Resultado: Permite acotar la espera sin garantizar éxito.

**Elementos por bloque de metadatos.** Organiza la cantidad de elementos técnicos por bloque. Ejemplo: Predeterminado 100; rango 25–200. Resultado: Cambia el tamaño operativo del contexto, no las filas del ETL.

**Registros por página.** Conserva el ajuste de tamaño predeterminado de listados. Ejemplo: Predeterminado 10; rango 10–100. Resultado: El efecto depende del consumidor; los paginadores actuales envían 10 explícitamente.

**Guardar.** Persiste el valor de esa tarjeta. Ejemplo: Guardar un tiempo acordado para una prueba. Resultado: Muestra un mensaje con el nombre del parámetro actualizado.

**Restaurar.** Recupera el predeterminado de la tarjeta. Ejemplo: Volver Tiempo máximo de conexión a 8. Resultado: Se deshabilita si ya coincide con el predeterminado.

### Práctica y comprobación

**Cambiar y recuperar un parámetro sin llamar a la IA.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. En un entorno de capacitación, anote Tiempo máximo de conexión.
2. Guarde un valor permitido distinto y compruebe el mensaje.
3. Pulse Restaurar y compruebe el predeterminado.

**Resultados esperados:** Se conserva el dato operativo y se puede volver al valor de referencia. No se cambian catálogos, fuentes ni propuestas.

**Criterio:** La estudiante explica qué cambió y qué no demuestra este ejercicio.

### Qué hacer cuando hay problemas

**El valor es rechazado.** Está fuera del rango o no es un entero admitido. **Acción:** Utilice el rango visible; no agregue una clave nueva. **Comprobación:** Se guarda un valor válido y legible.

**El modelo sigue fallando tras aumentar el tiempo.** El problema puede ser cuota, clave, modelo o contrato estructurado. **Acción:** Revise el mensaje del proveedor y su prueba de configuración. No atribuya todos los fallos a tiempo insuficiente. **Comprobación:** La reparación se dirige a la causa observada.

**Guardar Registros por página no cambia el listado.** El componente utiliza su tamaño explícito del corte actual. **Acción:** Registre esta limitación; conserve el valor de referencia si no hay una prueba de efecto. **Comprobación:** La demostración no promete un cambio que el navegador no muestra.

### Preguntas para la sustentación

**¿Subir el tiempo hace más inteligente a la IA?** No. Solo modifica el límite de espera. La calidad de una propuesta sigue dependiendo del contexto, del proveedor y de las reglas de validación.

## 11. Configurar y comprobar el asistente de IA

**Opción:** Preparación del entorno > Configuración LLM

**Dirigido a:** Administración

El modelo de lenguaje interpreta y explica; no autentica usuarios ni ejecuta SQL libre sobre las bases. La plataforma mantiene proveedores como configuraciones separadas y una sola configuración activa a la vez. Cambiar la activa afecta las nuevas solicitudes de la aplicación, por lo que debe coordinarse antes de una demostración compartida.

Seleccione el Proveedor para completar la URL y el modelo sugeridos por el producto. Son valores del corte de software, no una garantía permanente de disponibilidad comercial. El identificador debe existir y estar autorizado en la cuenta del proveedor. La URL se valida contra destinos permitidos; no se usa esta pantalla para enviar datos a un servicio arbitrario.

Para un proveedor cloud, el flujo consiste en crear el registro, registrar la credencial, probar la conexión y activar la configuración prevista. La prueba hace una solicitud mínima, sin el contexto comercial de la demostración. Un resultado satisfactorio acredita ese acceso básico, pero no demuestra todavía la calidad de una propuesta de BI.

Ollama local no necesita API key, pero sí requiere el servicio local y el modelo descargado en la instalación. La pantalla no descarga modelos por escribir su nombre. Si se cambia proveedor, URL, modelo o razonamiento, se invalida la prueba previa; vuelva a probar antes de usar el asistente. Cambiar de tipo de proveedor en un registro activo exige desactivarlo primero.

Nivel de razonamiento es una opción común que los adaptadores traducen a las capacidades admitidas. La modalidad de Claude de este corte ofrece Automático, Mínimo o Bajo; no habilita pensamiento extendido con Medio o Alto. Una opción más alta puede cambiar tiempo y consumo en proveedores compatibles, pero no garantiza mejores respuestas ni sustituye la supervisión.

### Conceptos

- **Proveedor:** Servicio que ofrece el modelo, local o cloud.
- **Modelo:** Identificador concreto de la capacidad solicitada dentro de ese proveedor.
- **Credencial:** Clave que autoriza al proveedor; se almacena cifrada y no se vuelve a mostrar.
- **Activa:** Configuración seleccionada para nuevas solicitudes; no significa que todas sus respuestas serán válidas.

### Paso a paso

1. Abra Configuración LLM y revise los registros existentes para no duplicarlos innecesariamente.
2. En Crear configuración LLM, escriba Nombre de configuración y seleccione Proveedor.
3. Revise URL del servicio, Modelo y Nivel de razonamiento. Use valores autorizados para la instalación.
4. Pulse Crear registro. En cloud, pulse Registrar credencial en su fila, introduzca la API key y pulse Guardar credencial.
5. Pulse Probar conexión y lea el resultado. Corrija clave, cuota, modelo o disponibilidad si falla.
6. Pulse Activar sobre la configuración prevista y compruebe cuál queda activa.
7. Vuelva a Inicio para revisar el asistente preparado. Antes de enviar una necesidad, atienda la autorización de transferencia del contexto que corresponda al destino elegido.
8. Para una clave renovada, use Reemplazar credencial y repita la prueba. No necesita borrar la propuesta histórica para cambiar una configuración de futuras solicitudes.

### Campos y botones

**Nombre de configuración.** Distingue el registro. Ejemplo: Claude demostración o Groq capacitación. Resultado: Permite reconocer la configuración que se prueba y activa.

**Proveedor.** Selecciona el adaptador implementado. Ejemplo: Anthropic Claude, Groq Cloud, Gemini Cloud, Qwen Cloud u Ollama local. Resultado: Completa valores recomendados de URL, modelo y nivel.

**URL del servicio.** Identifica el destino permitido. Ejemplo: URL completada al seleccionar el proveedor. Resultado: Se valida su correspondencia; no admite un destino arbitrario.

**Modelo.** Especifica el identificador que el servicio debe reconocer. Ejemplo: Modelo autorizado de la cuenta y del adaptador. Resultado: La prueba puede detectar ausencia, acceso o incompatibilidad.

**Nivel de razonamiento.** Elige una modalidad admitida. Ejemplo: Mínimo para una solicitud breve en la modalidad de Claude disponible. Resultado: Se conserva en la configuración y forma parte de lo que debe volver a probarse si cambia.

**Registrar credencial / Reemplazar credencial.** Abre el formulario de la clave cloud. Ejemplo: Registrar una clave nueva sin imprimirla ni pegarla en documentación. Resultado: El servidor conserva el secreto cifrado.

**Guardar credencial / Cancelar.** Confirma o abandona el envío de la clave. Ejemplo: Cancelar si se abrió la fila equivocada. Resultado: La clave no vuelve a mostrarse en el listado.

**Probar conexión.** Realiza la comprobación mínima del proveedor y modelo. Ejemplo: Comprobar un modelo local instalado. Resultado: Devuelve un resultado básico, sin generar un datamart.

**Activar / Desactivar.** Selecciona la configuración operativa. Ejemplo: Cambiar de proveedor con conocimiento de quienes usan la plataforma. Resultado: Solo una queda activa para nuevas solicitudes.

**Eliminar.** Retira una configuración inactiva cuando el servidor lo permite. Ejemplo: Limpiar un registro temporal autorizado. Resultado: No sirve para reparar automáticamente un proveedor indisponible.

### Práctica y comprobación

**Identificar los componentes de una configuración existente.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. Consulte un registro sin mostrar la clave.
2. Identifique proveedor, modelo, nivel y estado.
3. Explique cuál usaría la próxima solicitud y qué ocurriría al cambiar el modelo.

**Resultados esperados:** Se distingue registro, prueba, credencial y activación. No se envía una solicitud comercial por consultar el listado.

**Criterio:** La estudiante explica por qué una prueba básica exitosa no es una evaluación completa de las propuestas BI.

### Qué hacer cuando hay problemas

**Credencial pendiente o rechazo de autenticación.** No se registró una clave válida para ese proveedor. **Acción:** Registre o reemplace la clave en la fila correcta y pruebe otra vez. No la escriba en Parámetros ni en el objetivo de negocio. **Comprobación:** La prueba básica resulta satisfactoria sin exponer el secreto.

**Modelo no disponible o sin acceso.** Identificador incorrecto, no instalado o no autorizado para la cuenta. **Acción:** Revise el modelo con la administración; en Ollama compruebe servicio y descarga mediante la guía técnica. **Comprobación:** El servicio reconoce el modelo configurado.

**Cuota, límite de servicio o tiempo agotado.** Restricción externa o recursos insuficientes. **Acción:** Lea la causa y espere o cambie a una configuración previamente preparada con autorización. No describa un cambio silencioso de proveedor como comportamiento del sistema. **Comprobación:** La nueva configuración queda identificada y probada.

**El proveedor devuelve JSON, pero el contrato es rechazado.** La salida no cumple los campos, tipos o reglas que exige la plataforma. **Acción:** Mantenga la necesidad guardada y revise el diagnóstico de recuperación del asistente. Reintente de forma controlada o elija un proveedor probado; no apruebe una respuesta inválida para continuar. **Comprobación:** Se obtiene una versión válida y revisable o un fallo explicado; no se materializa contenido inválido.

**Activar no devuelve un estado de preparación correcto.** La clave puede existir, pero la prueba es inválida o quedó obsoleta tras un cambio. **Acción:** Pruebe exactamente la combinación que está activa y revise Inicio. **Comprobación:** La preparación reconoce proveedor y modelo comprobados.

### Preguntas para la sustentación

**¿Se reemplaza la IA sin cambiar el proceso BI?** Los adaptadores permiten cambiar de proveedor manteniendo los contratos de la aplicación. Cada combinación requiere prueba y validación; no se garantiza que todos los modelos produzcan la misma calidad.

**¿La prueba mínima autoriza enviar datos de ventas completos?** No. La prueba utiliza una solicitud mínima. Las solicitudes posteriores respetan su propósito y autorización: el diseño usa contexto estructural y el copiloto analítico utiliza agregados permitidos.

## 12. Leer y comprender el esquema antes de diseñar

**Opción:** Preparación del entorno > Explorador de esquema

**Dirigido a:** Analista de BI, Administración, Gerencia con consulta de metadatos

El Explorador muestra una fotografía estructural de la fuente: esquemas, tablas, columnas, tipos, claves principales y relaciones declaradas. Es el primer paso para comprobar qué información existe y cómo puede relacionarse. No muestra las filas del negocio ni demuestra por sí solo que un atributo tenga el significado comercial que usted necesita.

Un esquema es una agrupación de objetos dentro de la base. Una tabla reúne registros de una entidad o evento; una columna representa un atributo. La clave principal identifica una fila de la tabla. Una relación declarada vincula columnas de tablas mediante una clave foránea. Dos columnas con el mismo nombre no prueban una relación válida si el esquema no la respalda.

La instantánea conserva versión, fecha y huella de contenido. Si la estructura no cambió, una actualización puede reutilizar la captura existente; no es obligatorio que aumente el número de versión. Versionar metadatos permite saber con qué estructura se revisó una propuesta histórica. Actualizar metadatos no actualiza las filas del datamart ni repite el ETL.

En AdventureWorks, una línea de pedido y su cabecera permiten distinguir la cantidad de líneas de la cantidad de pedidos. En WideWorldImporters, la línea de factura corresponde a otro evento comercial. Estos son ejemplos de lectura del esquema: el programa no exige esos nombres a una fuente nueva, pero sí necesita relaciones y tipos compatibles con la necesidad.

Para la demostración, encuentre al menos el detalle comercial, su fecha de evento y una relación hacia producto, cliente o territorio. Explique qué significa cada enlace antes de usarlo. Una relación hacia la persona que creó o modificó un registro no demuestra quién compró ni dónde se realizó la operación.

### Conceptos

- **Tabla:** Conjunto de filas del mismo tipo de entidad o evento.
- **Columna:** Atributo con un nombre y un tipo de dato.
- **PK:** Clave principal; identifica una fila de la tabla. Ejemplo: Puede incluir más de una columna.
- **Relación saliente:** Enlace desde la tabla consultada hacia otra mediante sus columnas.
- **Relación entrante:** Enlace de otra tabla hacia la tabla que se consulta.
- **Huella:** Resumen calculado del contenido estructural para comprobar si la captura cambió.

### Paso a paso

1. Seleccione la fuente correcta en Cambiar fuente.
2. Si no hay metadatos, pulse Crear primera instantánea si tiene permiso de actualización.
3. Lea el resumen de esquemas, tablas, columnas y relaciones y la versión vigente.
4. Use Versión de metadatos para una captura histórica cuando exista más de una.
5. En Buscar tabla o columna escriba parte del nombre; opcionalmente escriba el nombre exacto del esquema en Esquema y pulse Buscar.
6. Seleccione una tabla de la lista y revise Columna, Tipo, Permite nulos y Clave.
7. Lea Relaciones salientes y Relaciones entrantes. Anote las columnas del enlace y la tabla relacionada.
8. Para quitar un filtro, vacíe los campos y pulse Buscar. Al cambiar de fuente, compruebe que se cargan su propia instantánea y tablas.

### Campos y botones

**Crear primera instantánea.** Captura estructura cuando aún no existe una versión. Ejemplo: Preparar una fuente SQL Server nueva. Resultado: Conserva tablas, columnas y relaciones, sin filas ni credenciales.

**Actualizar metadatos.** Vuelve a consultar la estructura de la fuente. Ejemplo: Se agregó una tabla o cambió una relación declarada. Resultado: Crea una versión si hay cambios o reutiliza la equivalente.

**Versión de metadatos.** Permite revisar una captura conservada. Ejemplo: Abrir la estructura de una propuesta histórica. Resultado: Con una única versión, el selector está deshabilitado y lo explica.

**Buscar tabla o columna.** Filtra por un texto de estructura. Ejemplo: SalesOrderDetail o InvoiceLines en los ejemplos instalados. Resultado: Presenta coincidencias, no filas comerciales.

**Esquema.** Acota la búsqueda por agrupación estructural. Ejemplo: Sales, si corresponde a la fuente. Resultado: No es un selector de base de datos.

**Buscar.** Aplica los campos escritos. Ejemplo: Buscar InvoiceLines dentro de Sales. Resultado: Actualiza la lista desde la instantánea elegida.

**Tablas.** Permite elegir el objeto que se examina. Ejemplo: Detalle de una venta o factura. Resultado: Presenta columnas y relaciones de la tabla seleccionada.

**Relaciones salientes / Relaciones entrantes.** Explica los enlaces declarados. Ejemplo: Detalle hacia cabecera; otra tabla hacia cliente. Resultado: Permite reconocer el sentido y columnas de una relación sin inventarla.

### Práctica y comprobación

**Comparar pedido y factura.** Ejercicio de consulta propuesto; los nombres corresponden a las dos fuentes públicas de demostración y deben comprobarse en la instalación.

1. Seleccione AdventureWorks y busque SalesOrderDetail; revise sus claves y un enlace con SalesOrderHeader.
2. Cambie a WideWorldImporters y busque InvoiceLines; revise sus claves y un enlace con Invoices.
3. Explique por qué una línea no es un pedido ni una factura completa.

**Resultados esperados:** Se distinguen las estructuras de dos eventos comerciales. La estudiante identifica las referencias de la fuente sin proponer todavía un ETL.

**Criterio:** Puede justificar un conteo distinto de documentos frente a un conteo de líneas.

### Qué hacer cuando hay problemas

**No aparecen coincidencias.** Texto o esquema no coinciden con la instantánea. **Acción:** Vacíe los filtros, pulse Buscar y localice una tabla de la lista. No concluya que faltan las ventas por una búsqueda mal escrita. **Comprobación:** La lista vuelve a mostrar objetos de la fuente correcta.

**Versión de metadatos aparece deshabilitada.** Solo existe una captura disponible. **Acción:** Lea la nota y consulte esa versión. No necesita generar versiones artificiales. **Comprobación:** Se reconoce la única instantánea sin interpretarla como un fallo.

**No hay una relación de negocio que el analista esperaba.** El origen no la declara o enlaza otro rol del negocio. **Acción:** Registre la limitación y formule una necesidad compatible. No una tablas por nombres parecidos para forzar cobertura. **Comprobación:** La propuesta posterior usa enlaces respaldados o informa la insuficiencia.

**Actualizar no cambia el número de versión.** La huella estructural es equivalente. **Acción:** Compruebe el mensaje y la estructura; una captura reutilizada es un resultado válido. **Comprobación:** No se confunde ausencia de cambio de estructura con error de actualización de ventas.

### Preguntas para la sustentación

**¿La instantánea permite comprobar que los importes están bien?** Permite comprobar estructura y referencias. La comprobación numérica corresponde a la conciliación posterior a una carga.

**¿Por qué conservar nombres técnicos en inglés?** Identifican las referencias reales del origen. La explicación puede estar en español, pero no debe cambiar los nombres que permiten rastrear tablas y columnas.

## 13. Construir un catálogo de preguntas con criterio de negocio

**Opción:** Diseño y transformación BI > Catálogo analítico > Preguntas de negocio

**Dirigido a:** Analista responsable del catálogo con permiso de administración, Administración, Consulta para comprender el alcance

El catálogo es un conjunto de orientaciones comerciales que el analista podrá seleccionar al formular una necesidad. No es el datamart, no es una consulta SQL y no determina automáticamente qué tablas se cargarán. Su función es describir qué decisiones interesa apoyar con esa fuente.

La pantalla separa dos planos. Cobertura técnica de la fuente muestra qué referencias se descubren en la instantánea. Preguntas de negocio contiene las orientaciones que una persona autorizada administra. La IA utiliza el alcance y los metadatos en las etapas de necesidad y propuesta; la pantalla del catálogo no tiene un botón que genere libremente su configuración mediante la IA.

La línea base del producto contiene cuatro preguntas: evolución temporal, productos, clientes y territorio. No fueron creadas por un LLM en cada base. En el entorno histórico de AdventureWorks se incorporaron otras dos orientaciones, sobre costos y rentabilidad y sobre ventas y costos por unidad, por decisión del analista a partir de una recomendación conversacional. Ver seis preguntas en una fuente no significa que la plataforma deba copiar seis a todas las demás.

Cada catálogo pertenece a una conexión y a un dominio. Antes de editar, confirme el nombre en Fuente en contexto. Guardar un catálogo de AdventureWorks no debe modificar WideWorldImporters. Una nueva fuente comienza con las orientaciones del perfil y requiere su propio criterio comercial; la evidencia técnica se obtiene de su estructura, no de la fuente anterior.

Verificable significa que el descubrimiento dispone de referencias que pueden revisarse; Por validar conserva una orientación cuya evidencia tendrá que comprobarse antes de aprobar una propuesta; No disponible informa insuficiencia técnica. Ninguno de esos rótulos demuestra que ya se calcularon ventas o que la interpretación comercial sea incuestionable. Abra Referencias detectadas y lea su alcance.

Redacte una pregunta para una decisión concreta. Productos con mayor desempeño es una orientación; una instrucción útil especifica si se comparan sumas de importe o de unidades y advierte que un ranking no prueba preferencias del consumidor. No introduzca nombres de columnas inventadas ni convierta una limitación en una orden para que la IA la ignore.

Habilitada conserva la pregunta y controla si se ofrece para nuevos análisis. Retirar pregunta la quita del borrador de catálogo y el cambio se hace persistente al Guardar catálogo. Deshabilitar es adecuado cuando quiere conservar la redacción para un uso futuro. No utilice retirar como si fuera una aprobación o rechazo de las propuestas que ya existen.

Restaurar catálogo validado aplica inmediatamente la configuración predeterminada del perfil a la fuente elegida; no es un historial de deshacer ni recupera automáticamente las últimas preguntas personalizadas. En este corte puede sustituir las dos preguntas adicionales de AdventureWorks por las cuatro iniciales. Antes de utilizarlo, conserve por escrito las orientaciones que desea volver a incorporar y confirme que está trabajando en la fuente adecuada.

### Conceptos

- **Pregunta de negocio:** Tema comercial que orienta una necesidad, sin fijar por sí mismo el diseño físico. Ejemplo: Comparar el importe vendido por producto y mes.
- **Etiqueta:** Nombre breve que el analista reconocerá en la selección de preguntas.
- **Explicación para el analista:** Describe para qué decisión resulta útil la pregunta.
- **Instrucción funcional para la IA:** Precisa el resultado y sus límites en términos comerciales; no habilita SQL ni referencias inexistentes.
- **Cobertura técnica:** Respaldo estructural detectado para las orientaciones del dominio.
- **Personalización por fuente:** Configuración independiente que pertenece a una conexión concreta.

### Paso a paso

1. Abra Catálogo analítico y confirme Fuente en contexto y Dominio habilitado.
2. Lea Cobertura técnica de la fuente. Abra Referencias detectadas en las tarjetas que la ofrezcan.
3. Revise las preguntas existentes antes de añadir otra: puede bastar con mejorar su explicación.
4. Pulse Agregar pregunta. Sustituya la redacción de ejemplo de los tres campos por una orientación comercial concreta.
5. Escriba Etiqueta, Explicación para el analista e Instrucción funcional para la IA. Revise Habilitada.
6. Pulse Guardar catálogo y espere el mensaje de actualización.
7. Vuelva al catálogo y compruebe los textos. Después, abra un análisis nuevo para comprobar qué orientaciones ofrece el asistente.
8. Cambie a la otra fuente y confirme que sus preguntas se mantienen propias.
9. Si necesita retirar una orientación, considere primero desmarcar Habilitada. Si elige Retirar pregunta, revise el borrador restante y pulse Guardar catálogo.
10. No utilice Restaurar catálogo validado como prueba de aprendizaje sobre un catálogo con personalizaciones que necesite conservar.

### Campos y botones

**Dominio habilitado.** Selecciona un perfil analítico implementado. Ejemplo: Datamart de ventas, único dominio operativo del corte. Resultado: No crea inventario, compras u otro dominio por cambiar una etiqueta.

**Cobertura técnica de la fuente.** Presenta el descubrimiento de referencias de la instantánea vigente. Ejemplo: Comprobar qué estructura respalda análisis temporal o territorial. Resultado: Distingue evidencia técnica de una preferencia comercial escrita.

**Verificable / Por validar / No disponible.** Resume el respaldo de una orientación. Ejemplo: Una pregunta personalizada puede permanecer Por validar. Resultado: Guía la revisión; no acredita una cifra calculada.

**Referencias detectadas.** Despliega las referencias que sustentan una tarjeta. Ejemplo: Leer las tablas o columnas citadas y su pertenencia al origen. Resultado: Permite una comprobación explícita del respaldo.

**Agregar pregunta.** Añade un borrador de orientación. Ejemplo: Una orientación sobre documentos e importe promedio. Resultado: Genera un identificador interno; máximo doce preguntas en total, no doce adicionales.

**Habilitada.** Ofrece o retira de las selecciones futuras sin eliminar el texto. Ejemplo: Deshabilitar temporalmente una orientación de costos. Resultado: Conserva la redacción al guardar, pero no la ofrece como pregunta habilitada.

**Etiqueta.** Nombre reconocible de la orientación; de 3 a 120 caracteres. Ejemplo: Costos y rentabilidad de las ventas. Resultado: Se muestra en el catálogo y en las selecciones que correspondan.

**Explicación para el analista.** Explica utilidad y decisión; de 10 a 300 caracteres. Ejemplo: Permite comparar el importe vendido con costos respaldados para revisar diferencias por producto. Resultado: La persona comprende para qué seleccionar esa orientación.

**Instrucción funcional para la IA.** Delimita la interpretación comercial; de 10 a 500 caracteres. Ejemplo: Usar únicamente costos verificables; declarar si son actuales y no atribuirles validez histórica. Resultado: Orienta las solicitudes futuras sin sustituir los validadores.

**Identificador interno.** Mantiene la identidad de la pregunta. Ejemplo: Código automático custom_… de una pregunta nueva. Resultado: No es un campo que deba inventar ni editar la operadora.

**Retirar pregunta.** Quita la tarjeta del borrador. Ejemplo: Retirar una orientación duplicada con autorización. Resultado: Necesita Guardar catálogo para persistir; no permite retirar la última tarjeta por ese botón.

**Guardar catálogo.** Persiste preguntas y periodicidades de la fuente. Ejemplo: Guardar una pregunta aclarada en WideWorldImporters. Resultado: Los nuevos análisis usan la configuración actualizada; no reescribe propuestas previas.

**Restaurar catálogo validado.** Reaplica la línea base del perfil a la fuente actual. Ejemplo: Recuperar las cuatro orientaciones estándar en un entorno limpio. Resultado: Sustituye personalizaciones del catálogo; no revierte una propuesta ni una ejecución.

### Práctica y comprobación

**Examinar el catálogo sin modificarlo.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. Seleccione AdventureWorks y cuente las orientaciones que realmente conserva la instalación.
2. Identifique las cuatro estándar y las personalizadas si existen.
3. Cambie a WideWorldImporters y compare etiquetas, instrucciones y cobertura.

**Resultados esperados:** Se reconoce la configuración propia de cada origen. No se asume que la cantidad seis sea obligatoria o generada por IA.

**Criterio:** Puede explicar quién redacta las preguntas y de dónde procede la evidencia técnica.

**Añadir una orientación comercial acotada.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. En el entorno de capacitación, seleccione una fuente y conserve los textos iniciales.
2. Agregue una pregunta sobre importe por documento, indicando conteo distinto de pedidos o facturas según el evento real.
3. Guarde el catálogo y compruebe la nueva tarjeta.
4. Consulte la otra fuente para verificar que no recibió la tarjeta.
5. En la etapa de necesidad, someta cualquier nueva solicitud a su evaluación de viabilidad.

**Resultados esperados:** La pregunta queda guardada únicamente en la fuente elegida. La tarjeta no crea automáticamente una medida, propuesta o ETL. Una cobertura Por validar no se describe como fallo si aún no se ha construido una propuesta.

**Criterio:** La estudiante distingue guardar orientación de demostrar su factibilidad sobre metadatos.

### Qué hacer cuando hay problemas

**La pregunta aparece Por validar.** No tiene evidencia técnica suficiente en el descubrimiento inicial o es una orientación personalizada. **Acción:** Revise sus términos y referencias; formule una necesidad concreta y utilice la evaluación de viabilidad. No la fuerce como Verificable por cambiar su etiqueta. **Comprobación:** La factibilidad se acredita mediante referencias y reglas, o se informa una limitación.

**No se puede guardar el catálogo.** Campos fuera de longitud, tarjetas inválidas, fuente no habilitada o falta de permiso. **Acción:** Lea el mensaje, complete los tres campos de cada pregunta y revise la fuente. Compruebe también las periodicidades del mismo formulario. **Comprobación:** Aparece El catálogo analítico fue actualizado y una nueva consulta conserva los textos.

**Faltan las dos preguntas adicionales después de restaurar.** Restaurar sustituyó la personalización por la línea base de cuatro preguntas. **Acción:** Recupere los textos conservados o una evidencia histórica y vuelva a incorporarlos en la fuente correcta; no anuncie una recuperación automática inexistente. **Comprobación:** Las orientaciones adicionales vuelven a estar guardadas y habilitadas solo donde corresponde.

**La pregunta pide costos, pero no hay un costo confiable.** El deseo comercial supera la evidencia del origen o solo existe un costo actual. **Acción:** Acote la necesidad a las medidas disponibles o declare el alcance del costo actual. No llame costo histórico de la venta a un atributo actual sin respaldo. **Comprobación:** La propuesta no publica un margen supuesto ni confunde factibilidad estructural con criterio contable.

**Agregar pregunta está deshabilitado.** Ya existen doce tarjetas. **Acción:** Revise duplicados y retire o reformule una orientación si corresponde. Deshabilitar una tarjeta no reduce el número total. **Comprobación:** El catálogo cumple el máximo de doce, con las preguntas necesarias.

### Preguntas para la sustentación

**¿La IA construyó las cuatro preguntas iniciales?** No. Proceden del perfil del producto. Una persona autorizada puede ampliarlas; la IA interviene al sugerir o revisar necesidades y al proponer el diseño a partir de los metadatos.

**¿Por qué una pregunta guardada no demuestra que puede responderse?** Porque el catálogo expresa intención. La evaluación de viabilidad y los validadores deben comprobar referencias, relaciones, grano y cálculos para esa necesidad.

**¿Por qué el catálogo no fija las tablas?** Para separar el propósito comercial del esquema físico. El mismo objetivo puede requerir estructuras diferentes en cada fuente.

**¿Qué ocurre al restaurar?** Se aplica la configuración predeterminada del perfil en esa fuente; las personalizaciones del catálogo pueden sustituirse. Las propuestas y ejecuciones previas no se reescriben.

## 14. Elegir periodicidades sin confundirlas con el detalle de los datos

**Opción:** Diseño y transformación BI > Catálogo analítico > Periodicidades

**Dirigido a:** Analista responsable del catálogo, Administración, Personas en formación BI

Periodicidad indica cómo se agrupan temporalmente los resultados: día, semana, mes, trimestre o año. Granularidad indica qué representa una fila del hecho, como una línea de pedido o una línea de factura. Frecuencia de actualización indica cuándo se ejecutaría otra carga. Son tres decisiones distintas y no deben utilizarse como sinónimos.

Un caso puede conservar cada línea de venta y presentar sus importes agrupados mensualmente. En ese caso, Mensual no reduce por sí sola el hecho a una fila por mes. Tampoco agenda una carga mensual: el prototipo realiza cargas completas confirmadas por una persona; no implementa un calendario de refresco automático por habilitar esta opción.

La etiqueta temporal debe corresponder al evento de negocio. En AdventureWorks puede usarse la fecha del pedido cuando esa es la elegida y validada; en WideWorldImporters puede ser la fecha de la factura. Una comparación mensual de pedidos no debe llamarse facturación mensual solo porque ambas usan meses. La propuesta y su expediente conservan la fecha de evento y el alcance.

Las estrategias están implementadas como un catálogo cerrado de cinco opciones. Se pueden ofrecer varias y retirar alguna, pero escribir Bimestral como etiqueta de Mensual no crea una agregación bimestral. La etiqueta ayuda a leer la opción; no cambia el código de cálculo que la plataforma admite.

En un análisis particular se selecciona una de las periodicidades habilitadas. Los KPI pueden declarar una periodicidad explícita o heredar la de la propuesta; el lector analítico resuelve esa configuración al agrupar los resultados. Cambiar la configuración de un catálogo no debe reetiquetar una ejecución histórica que ya conserva su propio contrato.

### Conceptos

- **Granularidad:** Significado de una fila del hecho. Ejemplo: Una línea de pedido puede contener cantidad e importe.
- **Periodicidad:** Agrupación temporal usada para presentar un resultado. Ejemplo: Sumar importes de las líneas correspondientes a un mes.
- **Fecha de evento:** Fecha cuyo significado comercial organiza el análisis. Ejemplo: Fecha del pedido frente a fecha de factura.
- **Actualización:** Obtención de datos mediante otra ejecución. Ejemplo: No es un efecto de habilitar Mensual en el catálogo.
- **Herencia de periodicidad:** Un indicador utiliza la periodicidad de su propuesta cuando así lo declara su receta.

### Paso a paso

1. Revise primero qué fecha comercial respalda la fuente y la necesidad.
2. En Periodicidades lea cada opción y su Explicación.
3. Conserve habilitadas las que desea ofrecer al analista y desmarque las que no correspondan.
4. Para reincorporar una estrategia retirada, selecciónela en Agregar periodicidad y pulse Agregar.
5. Revise la Etiqueta y Explicación sin cambiar su significado temporal.
6. Pulse Guardar catálogo y compruebe las opciones disponibles al iniciar una necesidad nueva.
7. En la propuesta, confirme aparte la granularidad. En el expediente y el panel, compruebe la periodicidad efectiva de la serie.

### Campos y botones

**Habilitada.** Ofrece una periodicidad para nuevas selecciones. Ejemplo: Mantener Mensual habilitada para una comparación comercial. Resultado: Conserva la estrategia y controla su disponibilidad.

**Etiqueta.** Nombre legible de la periodicidad; de 3 a 100 caracteres. Ejemplo: Mensual. Resultado: No altera por sí mismo la agrupación implementada.

**Explicación.** Describe cuándo y para qué usar la opción; de 10 a 240 caracteres. Ejemplo: Agrupa por mes usando una fecha comercial verificable. Resultado: Orienta la selección del analista.

**Retirar periodicidad.** Quita una estrategia del borrador de configuración. Ejemplo: Retirar temporalmente Diaria si no se ofrecerá. Resultado: No permite retirar la última tarjeta desde ese botón; el cambio necesita guardarse.

**Agregar periodicidad.** Permite elegir una de las estrategias implementadas ausentes. Ejemplo: Seleccionar Trimestral cuando no figura entre las tarjetas. Resultado: No acepta una frecuencia arbitraria.

**Agregar.** Inserta la estrategia seleccionada en el borrador. Ejemplo: Reincorporar Anual. Resultado: La tarjeta aparece y se conserva al Guardar catálogo.

**Guardar catálogo.** Persiste también las opciones temporales del formulario. Ejemplo: Guardar Mensual y Trimestral habilitadas. Resultado: Las nuevas necesidades ofrecen esa configuración.

### Práctica y comprobación

**Explicar un datamart de líneas con análisis mensual.** Práctica propuesta para el entorno de capacitación; no se presenta como una nueva ejecución realizada durante la redacción.

1. Seleccione una propuesta histórica de líneas en el recorrido de formación.
2. Lea su granularidad y su periodicidad.
3. Explique qué se suma durante un mes y qué representa cada fila almacenada.
4. Repita la explicación para la otra fuente con su propio evento comercial.

**Resultados esperados:** Se distingue nivel de detalle, fecha de negocio y agrupación. La estudiante no afirma que habilitar Mensual ejecute un ETL mensual automático.

**Criterio:** Puede responder qué representa una fila y qué representa un punto mensual del gráfico sin confundirlos.

### Qué hacer cuando hay problemas

**No aparece una periodicidad en el asistente.** Está retirada o deshabilitada en el catálogo de esa fuente. **Acción:** Revise las tarjetas y guarde la configuración correspondiente; confirme que inicia una necesidad nueva de la misma fuente. **Comprobación:** La opción habilitada se ofrece en el contexto correcto.

**Se desea una frecuencia que no aparece.** La estrategia no está implementada. **Acción:** Utilice una opción admitida si responde a la necesidad o registre una ampliación de desarrollo. No renombre Mensual para simular Bimestral. **Comprobación:** El título temporal coincide con la agrupación realmente ejecutada.

**No hay fecha de negocio verificable.** La estructura no respalda la agrupación solicitada o la fecha pertenece a otro evento. **Acción:** Revise metadatos y delimite la necesidad. La etiqueta temporal no reemplaza una fecha ausente. **Comprobación:** La propuesta usa una fecha respaldada o informa la limitación.

**Se supone que cambiar el catálogo cambió el panel histórico.** Se confundió la configuración futura con el contrato de una ejecución ya materializada. **Acción:** Consulte la periodicidad y la propuesta de esa ejecución. Cree o revise un nuevo diseño solo cuando se requiera y se autorice. **Comprobación:** La procedencia histórica permanece identificada.

### Preguntas para la sustentación

**¿Mensual es la granularidad?** No necesariamente. En los casos de líneas, el hecho conserva líneas y el análisis agrupa sus importes por mes.

**¿Por qué no usar siempre la fecha de modificación del registro?** Porque suele indicar una acción administrativa. La fecha del evento comercial debe corresponder al pedido, factura u otro evento solicitado.

**¿Se puede refrescar automáticamente al marcar Semanal?** No. La opción agrupa resultados por semana; no programa una nueva carga.

## Seis orientaciones comerciales explicadas

Estos textos son ejemplos de capacitación; no se aplicaron a ningún catálogo durante la redacción.

### Evolución de ventas en el tiempo

Orientación estándar, redacción de capacitación; revisar antes de sustituir el texto local.

**Explicación para el analista:** Permite comparar el importe registrado y las unidades entre periodos de un mismo evento comercial.

**Instrucción funcional para la IA:** Comparar sumas por periodos usando la fecha de negocio verificable. Distinguir pedido de factura; no afirmar una tendencia causal ni comparar periodos incompletos como equivalentes.

### Productos con mayor desempeño

Orientación estándar, ejemplo de instrucción más concreta.

**Explicación para el analista:** Permite identificar productos con mayor importe o unidades dentro de la selección analizada.

**Instrucción funcional para la IA:** Ordenar productos por sumas de importe o unidades respaldadas. Mostrar el alcance de la selección; el ranking no demuestra preferencias, demanda futura ni causalidad.

### Desempeño por cliente

Orientación estándar.

**Explicación para el analista:** Permite comparar ventas atribuidas al cliente mediante relaciones de negocio comprobadas.

**Instrucción funcional para la IA:** Usar la identidad descriptiva del cliente obtenida mediante rutas verificadas. No sustituir cliente por vendedor, empleado que editó el registro o contacto sin respaldo.

### Desempeño por territorio

Orientación estándar; el territorio efectivo depende de la fuente y la propuesta.

**Explicación para el analista:** Permite comparar resultados según la ubicación o el territorio comercial respaldado por la fuente.

**Instrucción funcional para la IA:** Declarar el rol territorial usado y conservar la ruta revisada. Una dirección actual de cliente no acredita lugar de entrega realizado ni ubicación histórica del evento.

### Costos y rentabilidad de las ventas

Orientación personalizada histórica de AdventureWorks; no se garantiza aplicabilidad a otra fuente.

**Explicación para el analista:** Permite revisar la diferencia entre ventas y costos cuando los componentes tienen respaldo y alcance explícitos.

**Instrucción funcional para la IA:** Usar únicamente costos e importes verificables y declarar su fecha y significado. No presentar un costo actual de producto como costo histórico de cada venta ni inventar margen cuando falten componentes.

### Ventas y costos por unidad

Orientación personalizada histórica; precisa revisión de factibilidad y denominadores.

**Explicación para el analista:** Permite comparar importes por unidad conservando un denominador de unidades y el alcance de los costos disponibles.

**Instrucción funcional para la IA:** Calcular razones entre sumas compatibles de importe y unidades, con denominador verificable y tratamiento de cero. Distinguir promedio por unidad, por línea y por documento; declarar costos actuales cuando corresponda.

## Matriz de responsabilidades y permisos

Catálogo base extraído literalmente del código; las columnas de Analista y Gerencia son una propuesta de capacitación, no una lectura de sus asignaciones actuales en PostgreSQL.

- **Consultar usuarios** (security.users.read): Permite consultar usuarios. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Administrar usuarios** (security.users.write): Permite crear y modificar usuarios. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Consultar roles** (security.roles.read): Permite consultar roles. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Administrar roles** (security.roles.write): Permite crear roles y asignar permisos. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Consultar permisos** (security.permissions.read): Permite consultar permisos. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Administrar permisos** (security.permissions.write): Permite crear permisos. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Consultar menús** (security.menus.read): Permite consultar la navegación. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Administrar menús** (security.menus.write): Permite crear y parametrizar menús. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Consultar parámetros** (parameters.read): Permite consultar parámetros operativos. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Administrar parámetros** (parameters.write): Permite crear y modificar parámetros. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Consultar configuración LLM** (parameters.llm.read): Permite consultar proveedores LLM. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Administrar configuración LLM** (parameters.llm.write): Permite parametrizar proveedores LLM. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Consultar conexiones** (connections.read): Permite consultar fuentes sin secretos. Analista: No necesario para el recorrido propuesto. Gerencia: Incluir para el recorrido de consulta propuesto.
- **Administrar conexiones** (connections.write): Permite parametrizar fuentes de datos. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Probar conexiones** (connections.test): Permite validar fuentes de solo lectura. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Consultar metadatos** (metadata.read): Permite consultar instantáneas del esquema. Analista: Incluir según la responsabilidad acordada. Gerencia: Incluir para el recorrido de consulta propuesto.
- **Actualizar metadatos** (metadata.refresh): Permite leer la estructura de una fuente habilitada y seleccionada. Analista: Incluir según la responsabilidad acordada. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Revisar identidad de dimensiones** (metadata.semantic_resolution.read): Permite comprobar relaciones, cobertura y muestras descriptivas controladas. Analista: Incluir según la responsabilidad acordada. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Resolver identidad de dimensiones** (metadata.semantic_resolution.manage): Permite crear una versión corregida desde rutas semánticas verificadas. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto. Declarado en el catálogo; no se identificó una operación autorizada con este código en el recorrido web auditado. No atribuir una capacidad nueva por su mera existencia.
- **Consultar propuestas BI** (copilot.proposals.read): Permite consultar solicitudes, propuestas y decisiones del asistente. Analista: Incluir según la responsabilidad acordada. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Generar propuestas BI** (copilot.proposals.generate): Permite solicitar interpretación semántica y propuestas de ventas. Analista: Incluir según la responsabilidad acordada. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Revisar propuestas BI** (copilot.proposals.review): Permite aprobar o rechazar propuestas validadas. Analista: Incluir según la responsabilidad acordada. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Consultar catálogo analítico** (copilot.catalog.read): Permite consultar preguntas de negocio y periodicidades por dominio. Analista: Incluir según la responsabilidad acordada. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Administrar catálogo analítico** (copilot.catalog.write): Permite crear, modificar, habilitar y retirar guías analíticas por dominio. Analista: Incluir según la responsabilidad acordada. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Consultar materializaciones** (etl.executions.read): Permite revisar propuestas elegibles, planes y evidencia de ejecuciones ETL. Analista: Incluir según la responsabilidad acordada. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Preparar materializaciones** (etl.executions.write): Permite seleccionar una propuesta y preparar una ejecución ETL controlada. Analista: Incluir según la responsabilidad acordada. Gerencia: No necesario para el recorrido de gerencia propuesto.
- **Consultar análisis visual** (analytics.dashboard.read): Permite explorar KPI, visualizaciones e insights sobre un datamart conciliado. Analista: Incluir según la responsabilidad acordada. Gerencia: Incluir para el recorrido de consulta propuesto.
- **Exportar reportes analíticos** (reports.analytics.export): Permite descargar en PDF o Excel la selección analítica visible y autorizada. Analista: Incluir según la responsabilidad acordada. Gerencia: Incluir para el recorrido de consulta propuesto.
- **Consultar auditoría** (audit.read): Permite consultar eventos de auditoría. Analista: No necesario para el recorrido propuesto. Gerencia: No necesario para el recorrido de gerencia propuesto.

### Dependencias de uso

- **Seleccionar fuente y operar pantallas con contexto:** Consultar metadatos (metadata.read). También permite abrir el Explorador en consulta.
- **Editar usuarios no protegidos mediante la UI:** Administrar usuarios y Consultar roles para cargar las opciones.
- **Crear o editar roles y menús mediante la UI:** Administrar el recurso y Consultar permisos para cargar las casillas.
- **Mostrar cobertura técnica del catálogo:** La configuración usa Consultar catálogo analítico; la cobertura consulta el catálogo técnico mediante Consultar propuestas BI. La falta de esa consulta puede dejar la cobertura sin mostrar.
- **Exportar PDF o Excel:** Consultar análisis visual y Exportar reportes analíticos conjuntamente.
- **Revisar o generar una propuesta:** Consulta de propuestas más el permiso de generar o revisar correspondiente; no se confunden.

### Alcance de la matriz

- El rol de Analista responsable del catálogo incluye Administrar catálogo solo si esa responsabilidad se le asignó. Un perfil de analista que únicamente crea propuestas puede mantener el catálogo en consulta.
- Actualizar metadatos puede reservarse a administración y retirarse del analista si la preparación de fuentes se realiza centralmente.
- La propuesta de Gerente comercial incluye lectura de conexiones sin secretos, lectura de metadatos por dependencia del selector, panel y exportación. No incluye materialización, revisión ni administración del catálogo.
- Administrador es el perfil base sembrado. Los nombres locales Analista BI, Gerente comercial u Operador no garantizan por sí mismos ninguna lista de permisos.
- Product Owner y Scrum Master son responsabilidades del proyecto académico y no perfiles de autorización de la aplicación.
