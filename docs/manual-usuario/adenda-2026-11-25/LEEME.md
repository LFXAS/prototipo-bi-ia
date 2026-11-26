# Adenda del manual: operación y OpenAI

Fecha de contenido: 25 de noviembre de 2026. Destinatarios: administración,
analista BI, gerencia y programadoras en formación.

- `Adenda_operacion_BI_OpenAI_2026-11-25.pdf`: documento final de siete páginas.
- `adenda_operacion.tex`: fuente editable principal del PDF.
- `adenda_operacion.md`: resumen operativo editable; no es el archivo de compilación.
- `Tabla_modelos_OpenAI_2026-11-25.md`: comparación económica y estado de evidencia.
- `recursos/parametros-sesion-60.jpg`: captura real del parámetro de sesión,
  con valor 60 y rango 15 a 240 minutos. Se conserva su proporción original.

Esta adenda complementa el manual principal. No sustituye la evidencia QA de
la entrega, no afirma que todo texto sea viable ni presenta los ejercicios nuevos
como ejecuciones verificadas. El informe QA identifica los resultados efectivos.

Se explica la recuperación de módulo, el retorno contextual desde Inicio y
Analítica, la duración de sesión parametrizable (60 minutos iniciales, rango 15 a 240), la corrección de selecciones
de catálogo retiradas, OpenAI como proveedor distinto de Groq y los controles de
generación y contexto analítico. Los contratos históricos no se reescriben.

## Regeneración con Docker

Desde la raíz del repositorio:

```bash
make user-addendum
```

Este destino también forma parte de `make verify` y CI. El nombre de salida, las
fechas PDF omitidas y el identificador determinístico permiten comprobar que el
PDF versionado coincide con sus fuentes. Para una compilación de trabajo aislada:

```bash
mkdir -p /tmp/bi-adenda-build
```

```bash
docker run --rm --user "$(id -u):$(id -g)" \
  -e HOME=/tmp -e TEXMFVAR=/tmp/texmf-var -e VARTEXFONTS=/tmp/texfonts \
  -v "$PWD/docs/manual-usuario/adenda-2026-11-25:/workspace:ro" \
  -v /tmp/bi-adenda-build:/build -w /workspace bi-ia-docs:local \
  -pdf -jobname=Adenda_operacion_BI_OpenAI_2026-11-25 -outdir=/build \
  -interaction=nonstopmode -halt-on-error adenda_operacion.tex
```

Revise visualmente el PDF y sólo después copie el resultado al nombre final.
Mantenga los archivos auxiliares y las imágenes de revisión fuera del repositorio.
La entrega consolidada se registra por separado en el directorio documental del
proyecto. Esta carpeta no contiene credenciales ni datos de las bases.
