# SPR-04-03: UI/UX profesional para materialización y validación

- Estado: **aprobación técnica previa a la implementación de Sprint 4**.
- Dependencias: `SPR-04-01`, `SPR-04-02` y una propuesta de ventas aprobada.
- Usuario operativo: analista BI o responsable de datos.

## 1. Propósito de experiencia

La materialización del datamart debe operar como una herramienta profesional guiada. El analista BI entiende la necesidad comercial y los datos, pero no debe navegar JSON, elegir tablas técnicas ni redactar SQL para completar el proceso. La interfaz debe mostrar qué se usará, por qué es válido, qué falta, qué se ejecutará y cómo interpretar el resultado.

El gerente comercial no participa en la operación ETL. Posteriormente consumirá los KPI y visualizaciones calculadas con una vista orientada a resultados. La administración técnica conserva sus pantallas separadas de conexiones, secretos, permisos y configuraciones. La interfaz no contiene un catálogo fijo de indicadores: muestra y explica las sugerencias variables que produjo la IA para la necesidad seleccionada.

## 2. Recorrido principal

La opción de menú para el analista será **Datamart de ventas** y mostrará un recorrido continuo con cinco etapas visibles:

1. **Elegir propuesta**: lista y compara sólo versiones aprobadas y compatibles. La más reciente aparece sugerida, nunca ejecutada automáticamente.
2. **Revisar indicadores sugeridos**: muestra definición, período, medida base, receta y dependencia de cada KPI propuesto por la IA. El analista puede retirar un KPI o elegir una medida compatible ya comprobada, con justificación.
3. **Confirmar ejecución**: presenta el modelo dimensional, el plan ETL declarativo, controles previos y una confirmación explícita. Los detalles técnicos son expandibles, no dominan la pantalla.
4. **Materializar y cargar**: comunica progreso por etapa, inicio, resultado, advertencia o fallo recuperable. Nunca aparenta que una tarea larga terminó antes de recibir confirmación del backend.
5. **Validar resultados**: presenta conciliación OLTP--datamart, valores de referencia, diferencias, tolerancias y los KPI calculados. Permite abrir el detalle de evidencia de cada control.

El analista puede salir y volver sin perder la ejecución persistida. La interfaz distingue siempre entre borrador, propuesta aprobada, ejecución en curso, ejecución completada, resultado validado, resultado con advertencias y resultado fallido.

## 3. Principios de diseño

- Lenguaje de negocio en español como nivel principal: ``Ventas netas'', ``Clientes con compras en el período'' y ``Venta promedio por pedido''. Los nombres técnicos se muestran sólo en un panel ``Ver trazabilidad técnica''.
- Una decisión relevante por pantalla y una acción primaria inequívoca. Las acciones destructivas, como descartar un borrador de ejecución, requieren confirmación y motivo.
- Contexto persistente: dominio, fuente, instantánea, propuesta seleccionada, período y estado de ejecución permanecen visibles sin ocupar el área principal.
- Comparación útil: las diferencias entre propuestas o KPI resaltan granularidad, medidas, recetas, advertencias y fecha; no presentan bloques JSON como resultado principal.
- Seguridad operacional: ninguna pantalla acepta SQL libre, fórmula escrita a mano, nombres de columnas libres ni credenciales.
- Evidencia entendible: cada control indica qué compara, resultado esperado, resultado obtenido, tolerancia, diferencia y acción sugerida cuando falla.

## 4. Estados y recuperación

| Situación | Mensaje y acción esperada |
|---|---|
| No existe propuesta elegible | Explica que debe aprobarse una propuesta válida en el asistente y enlaza al recorrido correspondiente. |
| La propuesta perdió compatibilidad | Explica la diferencia, bloquea la ejecución y ofrece abrir, corregir o seleccionar otra versión. |
| Falta una receta de KPI | Identifica el KPI y permite retirarlo o volver a personalizar la propuesta; no intenta calcular una fórmula aproximada. |
| La IA propuso demasiados KPI | Muestra hasta doce sugerencias ordenadas por relación con la necesidad; el analista retira las que no aporten a la decisión antes de confirmar. |
| Validación previa fallida | Muestra el control fallido y no habilita la confirmación de carga. |
| Ejecución en curso | Expone etapa actual y evita duplicar la solicitud con botones deshabilitados y estado persistido. |
| Fallo de carga | Conserva el identificador, mensaje seguro, controles superados y una acción de reintento controlado. |
| Diferencia de conciliación | Señala la métrica, fuente, valor, diferencia y tolerancia; no publica el resultado como validado. |
| Éxito validado | Resume tablas materializadas, KPI calculados y controles aprobados; permite abrir el expediente de evidencia. |

## 5. Diseño responsive y accesible

- Escritorio: progreso lateral o superior, área central de decisión y panel técnico plegable.
- Tableta y móvil desde 320 px: etapas apiladas, controles táctiles, tablas convertidas en filas legibles y acciones primarias a ancho completo.
- Teclado: orden de foco visible, expansión de detalles, confirmación y retorno al paso anterior sin depender del puntero.
- Lectores de pantalla: títulos jerárquicos, etiquetas de formulario, regiones para progreso y alertas, y mensajes que no dependan sólo del color.
- Rendimiento: carga progresiva de historiales y evidencias; la interfaz no descarga objetos JSON completos ni reconsulta el proveedor LLM para mostrar resultados guardados.

## 6. Criterios de aceptación

- [ ] El analista completa una ejecución seleccionando una propuesta aprobada, sin SQL ni navegación obligatoria por metadatos técnicos.
- [ ] La aplicación preselecciona pero exige confirmar la propuesta y la ejecución.
- [ ] La revisión de KPI explica fórmula, medida, período y trazabilidad en español.
- [ ] Un estado bloqueante comunica causa y siguiente acción concreta.
- [ ] El progreso y el resultado de una ejecución persisten después de recargar la página.
- [ ] La conciliación se entiende sin abrir el detalle técnico, aunque éste permanezca disponible para auditoría.
- [ ] El flujo es utilizable en escritorio, tableta y móvil, y supera los controles de accesibilidad definidos por el proyecto.

## 7. Límites

- No se implementa un editor visual libre de ETL ni un constructor de SQL.
- No se presenta un dashboard ejecutivo como sustituto de la validación del analista.
- No se evalúa el pronóstico, MAPE o RMSE en esta pantalla hasta que exista el módulo predictivo.
