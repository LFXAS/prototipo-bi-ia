# ADR 0001: entorno Docker-first

- Estado: aceptada
- Fecha: 2026-08-24

## Contexto

El equipo ya administra PostgreSQL y SQL Server mediante Docker y requiere reproducibilidad entre desarrollo, pruebas y CI/CD.

## Decisión

Frontend, backend, herramientas y bases se ejecutan en contenedores exclusivos del proyecto. El host sólo necesita Docker Compose. PostgreSQL usa el puerto anfitrión `55432` y SQL Server `51433` para no interferir con instancias habituales.

Las imágenes usan etapas separadas de desarrollo, prueba y producción. GitHub Actions valida exactamente esas etapas y publica las imágenes de producción en GHCR.

## Consecuencias

- Se reduce la divergencia entre equipos y CI.
- Las primeras construcciones tardan más por descargar dependencias y el controlador ODBC.
- Los secretos se inyectan mediante entorno; nunca se incluyen en imágenes ni Git.
- El primer arranque requiere descargar y restaurar AdventureWorks; los siguientes reutilizan el volumen del proyecto.
