# Prototipo web de BI asistido por IA

Base técnica del proyecto de titulación de Emily Robles y Lesly Velásquez. Esta primera entrega deja un entorno **Docker-first** ejecutable con React + Vite, FastAPI, PostgreSQL y la configuración para consultar AdventureWorks en SQL Server con un usuario de solo lectura. No contiene todavía lógica de negocio.

La guía operativa completa para replicar, restaurar, publicar y probar el entorno está en [docs/replication-guide.md](docs/replication-guide.md).

Desde el Sprint 2 el proyecto aplica desarrollo guiado por especificaciones (SDD). Antes de crear una funcionalidad se redacta su especificación, criterios de aceptación, riesgos y evidencia de prueba en [`docs/specs/`](docs/specs/README.md). El flujo completo está en [`docs/sdd-workflow.md`](docs/sdd-workflow.md).

La trazabilidad del trabajo se mantiene en LaTeX y PDF. La bitácora vive en `docs/logbook/`, el informe académico del primer sprint en `docs/sprints/` y el manual técnico detallado en `docs/manual-tecnico/`. El [índice documental](docs/README.md) explica la finalidad y custodia de cada artefacto. Todos se regeneran de forma reproducible con `make docs`.

## Alcance confirmado

El anteproyecto define una prueba de concepto académica con una sola fuente SQL Server/AdventureWorks, introspección de metadatos, propuestas de un LLM sujetas a aprobación humana y validaciones determinísticas, ETL básico hacia un datamart PostgreSQL, cinco KPIs, tres gráficos, insights explicables y un pronóstico mensual por regresión lineal evaluado con MAPE y RMSE.

Esta fase implementa únicamente el entorno, la observabilidad mínima y la estructura modular. El RBAC es obligatorio por los requisitos académicos del módulo de seguridad, pero aquí queda sólo previsto; no hay autenticación, usuarios, roles, permisos ni menús funcionales todavía.

Consulta [docs/scope.md](docs/scope.md) y [docs/architecture.md](docs/architecture.md) para el detalle.

## Requisitos

- Docker Engine 24 o superior con Docker Compose v2.
- Al menos 8 GB de memoria disponibles para ejecutar el conjunto de contenedores.
- Conexión a Internet en el primer arranque para descargar las imágenes base y el respaldo oficial de AdventureWorks.

No es necesario instalar Node.js ni Python en el equipo anfitrión.

## Inicio rápido autocontenido

1. Crea la configuración local:

   ```bash
   cp .env.example .env
   ```

2. Reemplaza en `.env` todas las claves `ChangeMe_*`. Los puertos de base predeterminados son `55432` y `51433` para no cruzarse con instancias habituales en `5432` y `1433`.

3. Levanta PostgreSQL, SQL Server/AdventureWorks, backend y frontend:

   ```bash
   docker compose up --build -d
   ```

4. Comprueba:

   - Frontend: <http://localhost:5173>
   - API: <http://localhost:8000>
   - Documentación OpenAPI: <http://localhost:8000/docs>
   - Estado básico: <http://localhost:8000/api/v1/health/live>
   - Estado de PostgreSQL: <http://localhost:8000/api/v1/health/ready>

La comprobación `live` confirma que FastAPI funciona. `ready` confirma además la conexión a PostgreSQL. En un volumen vacío, SQL Server descarga el respaldo oficial de AdventureWorks 2022, lo restaura y crea el usuario `bi_reader` sin permisos de escritura. La conexión de negocio a AdventureWorks se implementará en la siguiente iteración; sus variables y controlador ODBC ya forman parte del entorno.

La alternativa más automática es `make bootstrap`: crea `.env` si falta, construye todo, espera la restauración y no finaliza hasta que los servicios estén saludables.

### Vista local de entrega sin detener desarrollo

Con el entorno de desarrollo activo, se puede añadir el frontend compilado servido por Nginx sin reemplazar ningún contenedor ni duplicar las bases:

```bash
make delivery-preview-up
```

Quedan disponibles simultáneamente:

- desarrollo con recarga automática: <http://localhost:5173>;
- vista de entrega Nginx: <http://localhost:8080>;
- API y bases compartidas: <http://localhost:8000>.

Esta vista comprueba el artefacto web de producción, pero sigue usando el backend de desarrollo. Para probar las cinco imágenes publicadas como un ambiente completamente independiente, copia `.env.release.example` a `.env.release` y ejecuta `make release-up`; ese segundo proyecto usa API `18000`, PostgreSQL `55433` y SQL Server `51434`, por lo que puede convivir con desarrollo.

## Flujo diario

```bash
make up             # construir y levantar
make delivery-preview-up # anadir Nginx en 8080 sin detener Vite
make logs           # seguir los registros
make test           # pruebas de backend y frontend en imagenes Docker
make lint           # calidad estatica en contenedores
make compose-check  # validar las dos variantes de Compose
make docs           # regenerar bitacora, informe de sprint y manual
make down           # detener la aplicacion
```

Los volúmenes del código habilitan recarga automática en FastAPI y Vite. Las dependencias permanecen dentro de las imágenes/volúmenes Docker.

## Seguridad de AdventureWorks

`SQLSERVER_APPLICATION_INTENT=ReadOnly` expresa la intención de conexión, pero **no reemplaza los permisos del motor**. El usuario configurado en `SQLSERVER_USER` debe tener sólo `CONNECT` y lectura (`db_datareader` o permisos `SELECT` más restringidos), sin pertenecer a `db_owner`, `db_ddladmin` ni roles de escritura. Las credenciales reales viven únicamente en `.env`, archivo ignorado por Git.

## Git, CI y CD

El repositorio usa `develop` como rama predeterminada de integración y `main` como rama estable de entrega. Las ramas `feature/*`, `fix/*`, `docs/*` y `chore/*` nacen desde `develop` y regresan mediante pull request. Sólo una promoción revisada `develop` -> `main` publica una entrega. Los commits siguen Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, etc.). Antes de enviar cambios:

```bash
make verify
```

GitHub Actions incluye:

- **CI:** valida el flujo de ramas, Compose, código, pruebas e informes PDF en cada pull request y push a `develop` o `main`. Un PR hacia `main` falla si no procede de `develop`.
- **CD:** después de cambios en `main` o una etiqueta `v*`, construye y publica imágenes versionadas en GitHub Container Registry (GHCR). Publicar imágenes constituye entrega continua; el despliegue a un ambiente se añadirá cuando se elija el proveedor.
- **Imágenes:** se publican frontend, backend, PostgreSQL inicializado y SQL Server con restauración automática. Los volúmenes no se publican; se reconstruyen de forma determinística.
- **Dependabot:** crea ramas temporales y pull requests hacia la rama predeterminada. En npm agrupa sólo cambios menores y parches; los cambios mayores requieren una actualización intencional y aislada.

Las ramas y los ambientes cumplen funciones distintas: `develop`/`main` controlan qué código se integra, mientras Compose controla dónde se ejecuta. CI no necesita mantener contenedores permanentes: crea comprobaciones efímeras para cada cambio. CD publica imágenes sólo desde `main` o una etiqueta `v*`; cada computador o servidor decide después qué etiqueta desplegar mediante `compose.release.yaml`.

Para cerrar el ciclo con una demostración en nube se propone **Azure for Students** y una VM Linux x64 con Docker Compose. GitHub Actions se autenticará mediante OIDC, sin guardar una contraseña permanente de Azure; después de aprobar el ambiente `production`, la VM descargará la etiqueta GHCR seleccionada, iniciará `compose.release.yaml` y ejecutará sondas de salud. La cuenta, la VM y el flujo de despliegue todavía no se crean: requieren activar primero la suscripción académica y definir presupuesto, región y nombre del recurso.

La estrategia completa, incluidos los comandos y la promoción de versiones, está en [`docs/git-workflow.md`](docs/git-workflow.md).

La documentación también es código de entrega: un cambio que modifique arquitectura, configuración, comandos, comportamiento de despliegue o decisiones debe actualizar los documentos afectados, regenerar los PDF con `make docs` y superar CI antes de fusionarse.

El repositorio es público y tiene protecciones activas en `develop` y `main`: exige pull request, una aprobación, conversaciones resueltas y los controles de CI; además bloquea force-push y eliminación. La excepción administrativa se conserva sólo para recuperación y debe registrarse en la bitácora.

Para vincular este repositorio local con GitHub, confirma la sesión y crea el remoto después de elegir nombre y visibilidad:

```bash
gh auth status || gh auth login -h github.com
gh repo create NOMBRE_REPOSITORIO --private --source=. --remote=origin --push
```

La sesión actual está asociada a la cuenta `LFXAS`. Cambia `--private` por `--public` si el código y las imágenes deben ser públicos desde el inicio.

## Estructura

```text
backend/                 FastAPI, configuración, salud y módulos futuros
frontend/                React + Vite y pantalla técnica de estado
docs/                    alcance, arquitectura y decisiones
.github/workflows/       integración y entrega continua
compose*.yaml            desarrollo autocontenido, publicación y producción
```

## Próxima iteración

1. Crear la migración inicial del RBAC y los parámetros de conexión.
2. Implementar autenticación y autorización en el backend antes del menú dinámico.
3. Probar la conexión de sólo lectura e introspección contra AdventureWorks.
4. Registrar auditoría de aprobaciones y SQL validado desde el primer flujo de negocio.
