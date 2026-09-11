# SPR-02-02: navegación, responsive y experiencia administrativa

- Estado: **implementado y verificado localmente; pendiente de revisión colaborativa y cierre mediante PR hacia `develop`**.
- Pertenece a: [SPR-02-rbac-y-parametros.md](SPR-02-rbac-y-parametros.md).
- Última revisión funcional: 2026-09-10.

## 1. Objetivo

Ofrecer una estructura visual coherente para el Sprint 2 y los módulos BI posteriores. La navegación debe ayudar a orientarse, ocupar un espacio razonable en cualquier pantalla y nunca impedir acceder al contenido o plegar el grupo activo.

## 2. Arquitectura de navegación

| Elemento | Decisión de UX |
|---|---|
| Inicio | Es un acceso directo al panel inicial autorizado. **No** pertenece a un grupo llamado "Principal", porque un único elemento no justifica un acordeón ni aporta significado funcional. |
| Seguridad | Grupo padre plegable con Usuarios, Roles, Permisos, Menús y Auditoría. |
| Parámetros generales | Grupo padre plegable con Parámetros y Configuración LLM. |
| Futuros módulos | Cada módulo posterior (Metadatos, ETL, Analítica, Reportes, Copiloto) aparecerá como grupo padre sólo cuando tenga al menos una ruta autorizada. |

### 2.1 Comportamiento obligatorio del sidebar

1. Todo grupo padre se puede plegar y desplegar por clic, toque, Enter y barra espaciadora. Esto incluye el grupo que contiene la ruta activa.
2. La ruta activa se distingue dentro de su submenú, pero estar activa **no bloquea** el plegado de su padre. Al plegarlo, el contenido continúa en pantalla y el elemento activo sólo deja de verse en la navegación hasta volver a desplegar el grupo.
3. En escritorio (desde 1024 px) existe un control compacto, con icono de chevrón, superpuesto al borde de la barra lateral. Sigue el patrón de aplicaciones como ChatGPT: al activarlo, oculta la barra y el contenido recupera el ancho; el mismo control queda visible en el borde izquierdo para volver a mostrarla. El control no ocupa una celda del layout ni puede desplazar vertical u horizontalmente la barra o el contenido. No se usa un botón textual en el encabezado. El icono incluye etiqueta accesible y ayuda emergente.
4. En tableta y móvil (menos de 1024 px) el sidebar inicia oculto y se abre con un botón de hamburguesa accesible. Se cierra al elegir una subopción, al pulsar Escape, al tocar fuera cuando exista superposición y mediante un botón explícito de cerrar.
5. La preferencia de grupos abiertos y sidebar contraído puede conservarse localmente por sesión/dispositivo, pero no cambia la autorización ni se comparte entre cuentas.
6. Cada grupo informa `aria-expanded`, controla un contenedor con ID único y presenta un texto o icono que no sea la única señal de estado. El botón de hamburguesa y el de ocultar sidebar tienen etiquetas accesibles.

## 3. Aislamiento de pantallas y formularios

Cada ruta administrativa tiene un controlador de estado propio: lista, filtros, paginación, formulario, registro en edición, validación, mensaje y diálogo de confirmación.

- Abrir una fila en edición sólo afecta a la ruta actual.
- Navegar, cerrar formulario, cancelar o completar una operación limpia el registro seleccionado y el formulario correspondiente.
- Si se preserva una edición durante navegación accidental, se solicita confirmación; nunca se reutiliza el objeto seleccionado en una ruta diferente.
- Una pantalla sin registros muestra un estado vacío propio. Los campos no usan valores como `undefined`; se inicializan vacíos y se muestran ayudas que pertenecen al recurso actual.

## 4. Diseño responsive y listas

| Contexto | Requisito |
|---|---|
| 320–767 px | Una columna, sidebar de hamburguesa, formularios apilados, botones alcanzables y listas como tarjetas o tabla simplificada. Sin desplazamiento horizontal involuntario. |
| 768–1023 px | Sidebar oculto por defecto, panel principal flexible y formularios de una o dos columnas según legibilidad. |
| 1024–1439 px | Sidebar visible pero contraíble, tabla administrativa completa cuando el contenido lo permita y ancho legible. |
| 1440 px o más | El contenido mantiene ancho máximo; el espacio adicional no estira formularios o líneas de texto indefinidamente. |

Todas las listas administrativas muestran: filtros aplicados, total de resultados, rango visible, anterior/siguiente, estado sin resultados y error recuperable. Una acción de editar, activar o desactivar pide confirmación si tiene impacto. Los mensajes informan qué ocurrió y qué hacer después; no dependen sólo de color o iconos.

Las asociaciones configurables de **Roles asignados**, **Permisos otorgados** y **Permisos requeridos** usan una tabla de casillas que ocupa toda la fila del formulario. Sus columnas son Asignar, Nombre y Descripción. En escritorio conserva ancho legible y, en móvil, utiliza desplazamiento horizontal sólo dentro de la tabla; no se recorta texto ni se exige usar Ctrl/Command para seleccionar varias opciones.

## 5. Accesibilidad y lenguaje

- Interfaz visible inicialmente en español, con tildes y términos consistentes: **Menús**, **Parámetros**, **Configuración LLM**, **Contraseña**.
- Etiqueta permanente en cada campo; el texto de ayuda aclara propósito y formato cuando sea necesario.
- Los errores de validación estructurados por la API se traducen en un mensaje legible por campo; la interfaz nunca muestra serializaciones técnicas como `object Object`.
- Foco visible, orden lógico de tabulación y manejo de foco en diálogos/siderbar móvil.
- Contraste verificable, mensajes de error asociados al campo y notificaciones que no dependan exclusivamente de color.
- Las transiciones de plegado respetan reducción de movimiento y no son necesarias para comprender el resultado.

## 6. Criterios de aceptación

- [ ] Inicio se presenta como opción directa; no aparece un grupo "Principal" con un único submenú.
- [ ] Seguridad y Parámetros generales se pliegan y despliegan siempre, incluso si contienen la ruta activa, con clic, teclado y táctil.
- [ ] La persona puede ocultar/contraer el sidebar en escritorio y abrir/cerrar el menú de hamburguesa en tableta y móvil.
- [ ] El control de chevrón se superpone al borde del sidebar sin desplazar Inicio, los grupos de menú ni el contenido principal.
- [ ] Navegar entre pantallas nunca transporta el recurso en edición ni textos de ayuda de una ruta a otra.
- [ ] En 320, 768, 1024 y 1440 px no hay solapamiento, texto cortado, control inalcanzable ni desplazamiento horizontal involuntario.
- [ ] Las tablas de casillas de roles y permisos muestran nombre y descripción completos dentro de su límite responsive, sin recorte horizontal ni necesidad de combinaciones de teclado.
- [ ] Listas y formularios comunican carga, vacío, éxito, error y acceso denegado con foco y lenguaje comprensible.
- [ ] Al crear un usuario con un correo inválido, el formulario indica que debe usar una dirección completa y ofrece un ejemplo, sin exponer el objeto técnico de validación.
- [ ] Pruebas de interfaz cubren grupo activo plegable, ocultamiento del sidebar, navegación móvil y limpieza de estado entre al menos dos pantallas administrativas.
