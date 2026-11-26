# Verificación del manual de operación y aprendizaje

**Edición de formación 2.0 · 25 de noviembre de 2026 · Resultado documental: aprobado**

El manual completo se actualizó dentro de su secuencia didáctica. El PDF final tiene **272 páginas**, frente a las 258 de la edición base. Conserva sus 13 capítulos, las explicaciones de negocio y BI, los recorridos por cada pantalla, las actividades de práctica, los perfiles, la arquitectura, los siete diagramas de datos y el diccionario. No se reemplazó el manual por una adenda.

## Cambios integrados

| Parte del manual | Actualización |
|---|---|
| Arquitectura y fundamentos | OpenAI se incorpora como otro adaptador. Se mantiene la separación entre interpretación del modelo, validación del servidor y aprobación humana. |
| Ingreso y navegación | Sesión absoluta de 60 minutos predeterminada, rango 15–240, efecto sobre nuevos ingresos, recuperación mínima y diferencia con Cerrar sesión. Retorno guiado y contexto analítico por fuente. |
| Preparación y Configuración LLM | Alta, credencial privada, prueba y activación de OpenAI. Luna bajo como opción económica actual y Sol medio como modelo ensayado en los recorridos completos. |
| Selección del modelo | Tabla de cinco opciones y tarifas oficiales consultadas el 25 de noviembre. Estimación común de tokens separada del consumo real, reserva de razonamiento y recomendaciones para evitar llamadas innecesarias. |
| Catálogo | Recuperación de preguntas retiradas, conservación del objetivo, revisión de selección y nueva viabilidad. Distinción entre borrador mutable y expediente histórico. |
| Propuesta BI | Cobertura explícita de requisitos, diferencia entre medida física e indicador y complemento seguro con procedencia de plataforma. Compilación 6 para nuevos contratos; historia 1–5 sin reescribir. |
| ETL y analítica | Conciliación, cifras independientes de origen, unidad monetaria y denominadores, recuperación de filtros y control de respuestas de chat tardías. |
| Práctica | Necesidades exactas usadas con ambas fuentes, periodicidad mensual, cuatro orientaciones, cuatro indicadores, recetas y criterios para replicar. |
| Base de datos | Auditoría estructural local: 93 tablas/860 columnas; app conserva 18 tablas/174 columnas/24 FK. Migración 20261125_20. Lineaje vigente 135/23 y 136/24 y referentes históricos 129/21 y 131/22 separados. |

Los identificadores son propios de la instalación auditada. Un portable limpio no debe contener las API keys privadas ni todo su historial local; los expedientes nuevos tendrán otros números.

## Evidencia y límites

- Los recorridos nuevos completos fueron **AdventureWorks 136/24 y WideWorldImporters 135/23**, con OpenAI Sol y razonamiento medio. Los valores se contrastaron con agregados independientes del origen, sin usar filas en esta documentación.
- Luna bajo tiene **una prueba mínima real de conexión y salida JSON estructurada**. No se presenta como si ya se hubiese probado con ese modelo toda la generación, el ETL o el copiloto.
- Se conservaron **52 capturas históricas** sin alterar sus archivos y se incorporaron tres vistas reales del 25 de noviembre. Las vistas nuevas son estrechas: mantienen la proporción original, no se estiran y no se anuncian como capturas nuevas de escritorio completo.
- Las siete figuras ER anteriores se conservaron sin cambiar sus archivos. La arquitectura vectorial se actualizó para mencionar OpenAI; los esquemas físicos históricos se identifican por fecha y expediente.
- El manual permite repetir procesos y evaluar rechazos correctos. No garantiza que cualquier texto, motor o modelo produzca una propuesta idéntica o aprobable.
- La edición documental no ejecutó nuevas llamadas de IA, ETL ni modificaciones de configuración. Integra las pruebas de la campaña autorizada ya realizadas. Tampoco repite las 656 pruebas backend y 80 frontend que constan en el informe general del proyecto.

## Comprobaciones de integridad

| Comprobación | Resultado |
|---|---|
| Capítulos | 13 conservados |
| Unidades base de contenido | 90 renderizadas |
| Columnas de diccionario | 251 renderizadas |
| Capturas | 52 base sin cambios de SHA-256 y 3 actuales |
| Diagramas | 8 incluidos;7 ER base sin cambios de SHA-256 |
| Referencias a recursos | 63 comprobadas;0 faltantes |
| Tipografías | 12 archivos OTF TeX Gyre incluidos, con licencia GUST |
| Compilación final | XeLaTeX, dos pasadas, código 0 |
| Avisos pendientes | 0 Overfull;0 caracteres ausentes;0 referencias pendientes |
| Revisión visual | 40 páginas seleccionadas renderizadas con Poppler e inspeccionadas |
| Copia de entrega | Cotejada por SHA-256 contra las fuentes finales y el PDF compilado |
| Secretos en textos de autoría | Sin coincidencias de claves API reales, contraseña administrativa ni bearer token en la búsqueda de patrones |

La revisión visual comprendió portada, alcance, índice, arquitectura, acceso, navegación, parámetros, configuración de OpenAI, tabla de modelos, catálogo, viabilidad, aprobación, conciliación, divisa, filtros, captura de AdventureWorks 24, fichas vigentes, incidencias, inventario, lineaje y diagramas. Las páginas de PDF revisadas se enumeran en el JSON adjunto. No se observaron bandas blancas que corten la imagen, solapamientos, texto fuera de margen ni deformación de capturas en esas páginas. La inspección seleccionada no se presenta como una revisión visual individual de las 272 páginas.

## Autoría y reproducción

La copia original del 18 de noviembre permanece en su entrega histórica. Se trabajó sobre una copia nueva en `/tmp/bi-auditoria-20261125/manual-completo-v2`. El conjunto limpio está en `Fuentes_editables/`; no incluye AUX, LOG, renders ni cachés de compilación.

Los cambios de texto están en los JSON canónicos y en `insumos/actualizacion_20261125/actualizaciones_operacion.json`. La revisión completa de base de datos es el insumo editorial `insumos/actualizacion_20261125/12_base_datos.tex`. `fuentes/generar_manual.py` integra ambos de forma estable en los capítulos pertinentes. Los guiones históricos `redactar_*` conservan su contenido y se protegen contra la sobrescritura accidental de esta edición.

La fuente puede compilarse con una distribución TeX Live completa y XeLaTeX. Para leer el PDF no se necesita instalar LaTeX, Docker, la aplicación ni una API key.

### Compilación aislada efectivamente usada

La imagen `bi-ia-docs:local` **no trae XeLaTeX por sí sola**. En esta revisión se montó TeX Live 2026 del equipo anfitrión en sólo lectura. Este montaje depende de esa instalación documental local: no es una instrucción de instalación del portable en otro equipo.

Desde `manual_latex/`, se ejecutó la forma siguiente, con los registros guardados únicamente en el directorio de trabajo y excluidos de la entrega:

```bash
docker run --rm --network none \
  --user "$(id -u):$(id -g)" \
  --entrypoint sh \
  -e PATH=/usr/local/texlive/2026/bin/x86_64-linux:/usr/bin:/bin \
  -e TEXMFVAR=/tmp/texmf-var \
  -e TEXMFCONFIG=/tmp/texmf-config \
  -v /usr/local/texlive:/usr/local/texlive:ro \
  -v "$PWD:/work" -w /work bi-ia-docs:local \
  -c 'xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex && xelatex -interaction=nonstopmode -halt-on-error -file-line-error main.tex'
```

La compilación no utilizó red ni volúmenes de la aplicación. El manual de 272 páginas es una verificación documental independiente de los 13 PDF construidos por `make verify` del repositorio.

**SHA-256 del PDF final:** `2f44fbbd4c288dfb5dddf79418ef4ecf7b61acacf00f03ff93359737bde2b0a7`.
