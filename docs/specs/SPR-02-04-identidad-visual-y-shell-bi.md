# SPR-02-04: identidad visual y cascarón de experiencia BI asistida por IA

- Estado: **implementado y verificado localmente; pendiente de revisión colaborativa y cierre mediante PR hacia `develop`**. No autoriza implementar módulos BI fuera de alcance.
- Pertenece a: [SPR-02-rbac-y-parametros.md](SPR-02-rbac-y-parametros.md).
- Última revisión: 2026-09-10.
- Referencia conceptual: propuesta visual compartida por el equipo para el "Copiloto BI".

## 1. Propósito

Esta especificación define una dirección visual estable para que Seguridad y Parámetros, construidos en el Sprint 2, convivan después con Fuentes, Explorador de datos, ETL, Datamart, Dashboard, Alertas, Reportes y Copiloto BI. La referencia inspira un producto analítico moderno, claro y profesional; no se copiará literalmente, no se reutilizarán sus textos ni se dará por implementado ningún módulo que todavía no existe.

La pantalla de cada sprint debe sentirse parte de una sola plataforma: barra superior, navegación lateral, contenido central, tarjetas, estados y —cuando corresponda— un panel de conversación con IA.

## 2. Principios visuales

1. **Datos primero.** La jerarquía favorece título, contexto de la fuente activa, indicador de actualización y acción principal antes que adornos.
2. **IA acompañante, no invasiva.** El copiloto propone, explica y solicita confirmación; no oculta datos, no ejecuta cambios críticos por sí solo ni reemplaza los controles administrativos.
3. **Administración comprensible.** Seguridad, auditoría y parámetros usan el mismo cascarón que los módulos BI, pero priorizan formularios guiados, tablas paginadas y ayudas antes que gráficos decorativos.
4. **Estado visible.** Conexión, carga ETL, actualización de datos, alertas, autorización y fallos se expresan con texto, icono y color; nunca sólo con color.
5. **Responsive desde el diseño.** Una composición de tres zonas en escritorio se reordena, no se encoge hasta volverse ilegible, en tableta y móvil.

## 3. Arquitectura visual objetivo

| Zona | Responsabilidad | Sprint 2 | Futuro |
|---|---|---|---|
| Barra superior | Marca del producto, contexto de fuente activa cuando exista, estado de conexión, cuenta y acciones globales. | Marca, cuenta, cierre de sesión y estado de sesión. | Selector de fuente, salud de conexión, avisos y preferencias. |
| Sidebar | Navegación autorizada por módulos, plegable y ocultable. | Inicio, Seguridad y Parámetros generales. | Fuentes, Explorador, ETL, Datamart, Dashboard, Reportes, Alertas, Predicciones y Copiloto BI. |
| Área principal | Vista actual, título, ruta, acciones, formularios, tablas, estados y evidencia. | Administración RBAC y configuración. | KPIs, gráficos, exploración, flujos, reportes y resultados analíticos. |
| Panel de copiloto | Conversación contextual, sugerencias y acciones que requieren confirmación. | No se implementa; se reserva el patrón visual. | Copiloto BI, explicación de esquema, recomendaciones y solicitudes analíticas. |
| Barra de estado | Información no intrusiva de actualización, proceso o tarea. | Mensajes de operación y sesión. | Última actualización, avance ETL y accesos rápidos de actualización. |

### 3.1 Grupos de navegación

Los grupos sólo se muestran si la persona tiene permisos y si el módulo ya tiene al menos una ruta implementada. Inicio permanece como acceso directo.

| Grupo | Opciones previstas |
|---|---|
| Seguridad | Usuarios, Roles, Permisos, Menús, Auditoría. |
| Parámetros generales | Parámetros, Configuración LLM. |
| Datos | Fuentes de datos, Explorador de esquema, ETL, Datamart. |
| Analítica | Dashboard, Reportes, Alertas, Predicciones. |
| IA | Copiloto BI. |

Seguridad y Parámetros generales son las únicas opciones funcionales en el Sprint 2. Datos, Analítica e IA se documentan para preservar continuidad visual, pero no se mostrarán como menús vacíos ni como promesas funcionales.

## 4. Identidad de color y tipografía

La paleta base combina azul de confianza para navegación y análisis, turquesa para acciones confirmadas y colores semánticos para el estado de datos. Se centralizará como tokens CSS, no como colores dispersos en componentes.

| Token | Valor inicial | Uso |
|---|---:|---|
| `--color-brand-700` | `#0B3A82` | Marca, títulos de alto nivel y navegación activa. |
| `--color-brand-600` | `#155EEF` | Enlaces, acciones principales y elementos analíticos. |
| `--color-accent-600` | `#087F7A` | Confirmación, acciones secundarias positivas y estado conectado. |
| `--color-surface` | `#F7F9FC` | Fondo general. |
| `--color-panel` | `#FFFFFF` | Tarjetas, formularios y paneles. |
| `--color-text` | `#14213D` | Texto principal. |
| `--color-muted` | `#5D6B82` | Ayuda, etiquetas secundarias y metadatos. |
| `--color-border` | `#D9E1EC` | Separadores y bordes de controles. |
| `--color-success` | `#1C9C5A` | Éxito, disponible y conectado. |
| `--color-warning` | `#E58A12` | Advertencias y atención requerida. |
| `--color-danger` | `#D92D20` | Errores, acciones irreversibles y alertas críticas. |
| `--color-info` | `#2E6FE7` | Información contextual y progreso. |

- Tipografía inicial: pila del sistema (`Inter`, `Segoe UI`, `Roboto`, `Arial`, sans-serif), priorizando legibilidad y disponibilidad multiplataforma.
- Los gráficos utilizarán series distinguibles con contraste suficiente; ningún gráfico debe requerir color como único medio para identificar una serie.
- El modo oscuro, la paleta por empresa y la personalización de marca se mantienen como una evolución posterior. La paleta actual se implementa con tokens para facilitar esa futura extensión sin reescribir componentes.

## 5. Patrones por tipo de pantalla

### 5.1 Administración actual

Las pantallas del Sprint 2 usan encabezado con título, descripción breve, ruta visible y acción principal. Un formulario aparece en panel separado de la lista; la edición no contamina otras pantallas. Las tablas tienen búsqueda, filtros, paginación, estado vacío y acciones claramente rotuladas.

Los avisos explican el impacto: por ejemplo, al intentar desactivar una cuenta protegida se informa que la cuenta es necesaria para recuperar la administración. Los detalles técnicos se reservan para ayuda contextual o soporte autorizado.

### 5.2 Panel analítico futuro

El Dashboard podrá usar tarjetas KPI, gráficos de tendencia, distribución, alertas y estado ETL. Cada visualización indicará fuente, periodo, última actualización, unidades y una alternativa tabular o resumen textual accesible. El diseño no debe mostrar datos ficticios como si fueran resultados reales.

### 5.3 Copiloto BI futuro

En escritorio, el copiloto puede ocupar un panel derecho ajustable, sin impedir leer el área central. Sus respuestas diferencian claramente: observación basada en datos, sugerencia, advertencia y acción que necesita confirmación. La entrada de pregunta permanece visible sin cubrir contenido crítico.

Una conversación inicial propuesta puede incluir: fuente analizada, resumen del esquema, preguntas sugeridas y pasos recomendados. Ninguna respuesta del modelo debe ejecutar ETL, crear datamarts, modificar permisos ni consultar datos sensibles sin autorización y confirmación explícita.

## 6. Comportamiento responsive

| Contexto | Cascarón BI esperado |
|---|---|
| Móvil, 320–767 px | Barra compacta, sidebar en hamburguesa, una columna y tarjetas apiladas. El copiloto abre como vista completa o panel inferior, nunca reduce el contenido a una columna inutilizable. |
| Tableta, 768–1023 px | Sidebar temporal; el contenido conserva prioridad. El copiloto se abre como panel superpuesto o vista alterna según la tarea. |
| Escritorio, desde 1024 px | Sidebar visible y contraíble; área central prioritaria. El copiloto puede mostrarse en panel derecho si el ancho disponible conserva legibilidad. |
| Amplio, desde 1440 px | Tres zonas opcionales: sidebar, análisis central y copiloto derecho. Paneles con ancho máximo y separación clara. |

## 7. Criterios de aceptación de la dirección visual

- [ ] El cascarón del Sprint 2 usa tokens de color centralizados y no valores dispersos para marca, superficie, texto y estados.
- [ ] Inicio, Seguridad y Parámetros generales respetan la jerarquía de navegación definida; los módulos futuros no se presentan como funciones disponibles.
- [ ] Sidebar, encabezado, panel principal y avisos se comportan correctamente en 320, 768, 1024 y 1440 px.
- [ ] Las pantallas administrativas y el futuro panel de copiloto comparten tipografía, espaciado, tarjetas, estados y contraste verificable.
- [ ] Ningún componente crítico depende únicamente del color, un icono o una interacción de puntero.
- [ ] Antes de crear Dashboard o Copiloto, su especificación funcional detallará datos, permisos, fuentes, riesgos, flujos y criterios adicionales; este documento sólo define el marco visual.
