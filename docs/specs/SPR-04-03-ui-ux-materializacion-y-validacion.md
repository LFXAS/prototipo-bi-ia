# SPR-04-03: UI/UX profesional para materialización y validación

- Estado: **recorrido principal e historial recuperable implementados**.
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

Las transformaciones marcadas **Revisar en el paso 5** no requieren aprobación individual antes de cargar. La preparación sólo informa qué candidatos semánticos podrían aparecer; después de materializar, el mismo expediente conduce a **Validar resultados > Interpretación semántica**, donde el analista publica, corrige o excluye cada mapeo con evidencia. La confirmación general del ETL no publica etiquetas por anticipado.

El analista puede salir y volver sin perder la ejecución persistida. La interfaz distingue siempre entre borrador, propuesta aprobada, ejecución en curso, ejecución completada, resultado validado, resultado con advertencias y resultado fallido.

## 3. Principios de diseño

- Lenguaje de negocio en español como nivel principal: ``Ventas netas'', ``Clientes con compras en el período'' y ``Venta promedio por pedido''. Los nombres técnicos se muestran sólo en un panel ``Ver trazabilidad técnica''.
- Una decisión relevante por pantalla y una acción primaria inequívoca. Las acciones destructivas, como descartar un borrador de ejecución, requieren confirmación y motivo.
- Contexto persistente: dominio, fuente, instantánea, propuesta seleccionada, período y estado de ejecución permanecen visibles sin ocupar el área principal.
- Comparación útil: las diferencias entre propuestas o KPI resaltan granularidad, medidas, recetas, advertencias y fecha; no presentan bloques JSON como resultado principal.
- Seguridad operacional: ninguna pantalla acepta SQL libre, fórmula escrita a mano, nombres de columnas libres ni credenciales.
- Evidencia entendible: cada control indica qué compara, resultado esperado, resultado obtenido, tolerancia, diferencia y acción sugerida cuando falla.

## 4. Espacio de trabajo mínimo del analista BI

La plataforma debe reunir en un recorrido único lo que un analista necesita para asumir la responsabilidad del resultado, no sólo para pulsar un botón:

1. contexto de negocio, fuente, instantánea y propuesta aprobada;
2. perfil y calidad de datos antes de cargar: nulos, duplicados, tipos, rangos, cardinalidad y claves;
3. modelo dimensional, granularidad, relaciones y linaje desde OLTP hasta destino;
4. limpieza, conversiones, reglas de nulos, deduplicación y columnas calculadas;
5. KPI sugeridos por IA, su significado, receta controlada, unidad, período y dependencias;
6. interpretación en español de metadatos ingleses y, sólo cuando sea seguro, etiquetas de categorías de baja cardinalidad;
7. controles previos bloqueantes con una corrección concreta, no advertencias ambiguas;
8. progreso persistido, reintento seguro e historial de ejecuciones;
9. conciliación cuantitativa OLTP--datamart y expediente exportable de evidencia;
10. comparación entre versiones y trazabilidad del responsable de cada decisión.

La vista principal usa lenguaje de negocio. Las referencias técnicas permanecen disponibles en paneles expandibles para auditoría, sin obligar al analista a escribir SQL.

### 4.1. Decisión semántica guiada antes de la propuesta

La confianza emitida por el LLM no constituye por sí sola una comprobación. La aplicación conserva cada candidato para auditoría y añade un expediente determinístico basado en la instantánea: existencia de la referencia, columnas, clave primaria y relaciones declaradas. La interfaz traduce ese expediente a una acción concreta:

- confianza alta: incluida y confirmada automáticamente;
- confianza media con clave y relación verificadas: incluida como estructuralmente respaldada;
- confianza media sin evidencia estructural suficiente: excluida preventivamente;
- confianza baja: excluida preventivamente y marcada como decisión de negocio requerida.

El analista puede abrir **Ver evidencia y cómo resolver** para conocer origen, justificación, controles y consecuencias. Si decide incluir excepcionalmente un concepto de revisión, debe confirmarlo expresamente antes de continuar. La selección afecta únicamente a la nueva propuesta: no modifica la fuente ni elimina metadatos. El recorrido normal no requiere DBeaver ni una consola SQL; una futura consola avanzada, si se incorpora, será de sólo lectura, limitada, auditada y ajena a la decisión cotidiana.

### 4.2. Copiloto contextual de decisión

Cada concepto puede abrir un diálogo persistente con la IA. El copiloto recibe únicamente el objetivo de negocio, las preguntas seleccionadas y la evidencia estructural comprobada de ese concepto; no recibe filas, credenciales ni una consola SQL. Sus respuestas distinguen conclusión, nivel de confianza, evidencia citada, riesgo y consecuencias de incluir o excluir el concepto.

La respuesta nunca modifica la propuesta silenciosamente. **Aplicar recomendación** sólo marca o desmarca el concepto en la pantalla y deja la decisión final al analista antes de generar una versión nueva. Las citas quedan restringidas a tablas comprobadas de la instantánea, la conversación se conserva en el expediente y cada intervención registra proveedor, modelo, responsable y fecha. Si la evidencia no basta, el copiloto debe pedir una definición de negocio en lugar de inventar relaciones o resultados.

## 5. Estados y recuperación

| Situación | Mensaje y acción esperada |
|---|---|
| No existe propuesta elegible | Explica que debe aprobarse una propuesta válida en el asistente y enlaza al recorrido correspondiente. |
| La propuesta perdió compatibilidad | Explica la diferencia, bloquea la ejecución y ofrece abrir, corregir o seleccionar otra versión. |
| Falta una receta de KPI | Identifica el KPI y permite retirarlo o volver a personalizar la propuesta; no intenta calcular una fórmula aproximada. |
| La IA propuso demasiados KPI | Muestra hasta doce sugerencias ordenadas por relación con la necesidad; el analista retira las que no aporten a la decisión antes de confirmar. |
| Validación previa fallida | Muestra el control fallido y no habilita la confirmación de carga. |
| Ejecución en curso | Expone etapa actual y evita duplicar la solicitud con botones deshabilitados y estado persistido. |
| Contrato ya ejecutado | Identifica el expediente y su estado, reemplaza la acción de carga por **Abrir expediente** y explica que no es necesario volver a ejecutar el ETL. La API aplica el mismo bloqueo aunque se invoque fuera de la interfaz. |
| Fallo de carga | Conserva el identificador, mensaje seguro, controles superados y una acción de reintento controlado. |
| Diferencia de conciliación | Señala la métrica, fuente, valor, diferencia y tolerancia; no publica el resultado como validado. |
| Divisa sin comprobar | Conserva `moneda de origen`, evita asumir un símbolo y ofrece **Comprobar divisa sin repetir el ETL**. Si obtiene una moneda única, muestra el código ISO y la referencia técnica; si es mixta o ambigua, explica la evidencia faltante. |
| Éxito validado | Resume tablas materializadas, KPI calculados y controles aprobados; permite abrir el expediente de evidencia. Una interpretación ya publicada muestra su comprobante y no vuelve a solicitar confirmación. |

## 6. Diseño responsive y accesible

- Escritorio: progreso lateral o superior, área central de decisión y panel técnico plegable.
- Tableta y móvil desde 320 px: etapas apiladas, controles táctiles, tablas convertidas en filas legibles y acciones primarias a ancho completo.
- Teclado: orden de foco visible, expansión de detalles, confirmación y retorno al paso anterior sin depender del puntero.
- Lectores de pantalla: títulos jerárquicos, etiquetas de formulario, regiones para progreso y alertas, y mensajes que no dependan sólo del color.
- Rendimiento: carga progresiva de historiales y evidencias; la interfaz no descarga objetos JSON completos ni reconsulta el proveedor LLM para mostrar resultados guardados.

## 7. Criterios de aceptación

- [x] El analista completa una ejecución seleccionando una propuesta aprobada, sin SQL ni navegación obligatoria por metadatos técnicos.
- [x] La aplicación preselecciona pero exige confirmar la propuesta y la ejecución.
- [x] La revisión de KPI explica fórmula, medida, período y trazabilidad en español.
- [x] Los conceptos de confianza baja o evidencia insuficiente nacen desmarcados; una inclusión excepcional exige confirmación guiada y conserva trazabilidad.
- [x] Cada concepto muestra evidencia estructural y una acción recomendada sin exigir consultas SQL externas.
- [x] El copiloto contextual explica una decisión con evidencia exacta, riesgo y consecuencias; conserva la conversación y sólo aplica una recomendación mediante confirmación humana.
- [x] Un estado bloqueante comunica causa y siguiente acción concreta.
- [x] El progreso y el resultado de una ejecución persisten después de recargar la página y pueden reabrirse desde **Expedientes recientes**.
- [x] Una propuesta y selección de KPI ya ejecutadas muestran su número de expediente y no ofrecen una segunda carga idéntica; un intento duplicado queda bloqueado también en el backend.
- [x] Una decisión semántica publicada conserva responsable, comentario y mapeos aplicados; al reabrir el expediente presenta el resultado final sin repetir el formulario de confirmación.
- [x] Los importes usan código ISO sólo cuando la fuente lo demuestra; la pantalla muestra la referencia y permite enriquecer un expediente existente sin repetir el ETL.
- [x] La conciliación se entiende sin abrir el detalle técnico, aunque éste permanezca disponible para auditoría.
- [x] El flujo dispone de maquetación responsive, controles etiquetados y mensajes que no dependen sólo del color.

## 8. Límites

- No se implementa un editor visual libre de ETL ni un constructor de SQL.
- No se presenta un dashboard ejecutivo como sustituto de la validación del analista.
- No se evalúa el pronóstico, MAPE o RMSE en esta pantalla hasta que exista el módulo predictivo.
