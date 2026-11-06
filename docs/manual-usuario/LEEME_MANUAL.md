# Manuales vigentes de uso y formación

La edición del 6 de noviembre de 2026 ofrece dos recorridos con capturas nuevas completas de escritorio y la misma arquitectura general del capítulo III:

- [Manual de formación](edicion-2026-11-06/Manual_de_formacion_BI_IA.pdf), también en[Word editable](edicion-2026-11-06/Manual_de_formacion_BI_IA.docx). Desarrolla conceptos, criterios comerciales, configuración, catálogo, necesidad, propuesta, decisiones guiadas, aprobación, ETL, conciliación, analítica, copiloto, reportes y ejercicios para la sustentación.
- [Manual universitario](edicion-2026-11-06/Manual_de_usuario_universidad.pdf), también en[Word editable](edicion-2026-11-06/Manual_de_usuario_universidad.docx). Resume el recorrido en 38 páginas con pasos, comprobaciones y resultados esperados.
- [Fuentes y evidencia de esta edición](edicion-2026-11-06/LEEME_EDICION.md).

Los casos principales son AdventureWorks propuesta 129/ejecución 21 y WideWorldImporters propuesta 131/ejecución 22. Las dos cargas se conciliaron contra sus fuentes; la segunda distingue comprador, destinatario de facturación y ciudad de entrega. El número de versión y expediente puede cambiar al replicar la demostración: se verifica el significado y las cifras, no se intenta reproducir sus identificadores.

Las ediciones anteriores permanecen a continuación como antecedentes con su propio corte. Las capturas parciales del manual anterior no describen la política de imágenes de los dos manuales nuevos.

## Referencia histórica anterior

# Manual de usuario y entrenamiento en BI e IA

El manual principal se entrega en Word editable y PDF. Su secuencia comienza con
los conceptos y la preparación del entorno, recorre la configuración, los
metadatos, el catálogo, el asistente, la aprobación, el ETL y la analítica, y
termina con ejercicios de sustentación y un banco de preguntas razonadas.

## Cómo estudiarlo

1. Lea el mapa de trabajo y los conceptos antes de completar los formularios.
2. Siga la preparación de los capítulos 3 a 8 en una instalación disponible.
3. Realice los casos de ventas de los capítulos 9 a 15 y contraste cada resultado.
4. Use el capítulo 16 para diagnosticar una incidencia por etapa y conservar evidencia.
5. Prepare la demostración con los dos planes y las preguntas del capítulo 17.

Los casos detallados observados son AdventureWorks, propuesta 122 y ejecución 18,
y WideWorldImporters, propuesta 124 y ejecución 19. Los identificadores cambian
en otra instalación. Los valores publicados corresponden a las bases de ejemplo
de este ensayo y no son constantes del producto.

El plan A consulta resultados ya conservados. El plan B vuelve a generar con un
proveedor disponible, consentimiento y revisión humana. La generación de un LLM
no ofrece una garantía del cien por ciento; los controles rechazan resultados
inválidos y la revisión debe explicar sus límites. Las pruebas automatizadas y
las operaciones observadas se identifican por separado.

## Recursos editables y evidencia

- `crear_manual.py`: composición del documento; no conecta con la aplicación.
- `contenido*.json`: procedimientos y explicaciones por área.
- `hoja_ruta_capacitacion.json`: recorrido inicial y casos de aprendizaje.
- `banco_preguntas_formacion.json`: preguntas, respuestas y planes de demostración.
- `pruebas_actuales.json`: casos, resultados observados y limitaciones de validación.
- `capturas/registro.json`: fecha, descripción y regiones de cada captura.
- `capturas/`: originales conservados sin reconstruir estados de la aplicación.
- `evidencias_exportaciones/`: informes realmente descargados; las variantes con
  sufijo `final` son las revisadas después de las correcciones de contexto y altura.
- `qa/`: controles seleccionados de procedencia, conciliación y exportación.

Las capturas parciales del manual son recortes de esos originales. El pie lo
indica. Una imagen que no contiene una cifra no se utiliza como prueba visual de
esa cifra; los controles adicionales conservan su propia procedencia. Los
incidentes anteriores permanecen como historial y no son pasos obligatorios del
caso de éxito.

El Word permite corregir directamente el texto sin herramientas de desarrollo.
Las fuentes de composición emplean Python con `python-docx` y Pillow. La autoría
de esta edición utilizó el runtime de documentos de Codex y su LibreOffice
empaquetado para renderizar y revisar el resultado; ese entorno de autoría no es
un requisito para operar el prototipo. El programa conserva las rutas originales
como procedencia y puede resolver las capturas por su nombre en la carpeta local.

## Alcance de esta entrega

Este conjunto enseña la operación de la plataforma y aporta evidencia técnica
para su integración en la tesis. No sustituye una encuesta aplicada, una prueba
de usabilidad con participantes ni una sesión autenticada de cada rol. La
configuración de permisos observada y el recorrido administrativo se describen
con sus límites.

No incluye contraseñas, claves de proveedores, archivos de entorno, bases de
datos ni volúmenes Docker. La migración portable posterior requiere un trabajo
separado; copiar esta documentación no traslada el estado de la aplicación.
