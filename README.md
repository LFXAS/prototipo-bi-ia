# Prototipo web de BI asistido por IA

Base técnica del proyecto de titulación de Emily Robles y Lesly Velásquez. Esta primera entrega deja un entorno **Docker-first** ejecutable con React + Vite, FastAPI, PostgreSQL y la configuración para consultar AdventureWorks en SQL Server con un usuario de solo lectura. No contiene todavía lógica de negocio.

La guía operativa completa para replicar, restaurar, publicar y probar el entorno está en [docs/replication-guide.md](docs/replication-guide.md).

La trazabilidad del trabajo se mantiene en LaTeX y en su PDF generado dentro de `docs/logbook/`. Se regenera de forma reproducible con `make logbook`.

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

## Flujo diario

```bash
make up             # construir y levantar
make logs           # seguir los registros
make test           # pruebas de backend y frontend en imagenes Docker
make lint           # calidad estatica en contenedores
make compose-check  # validar las dos variantes de Compose
make down           # detener la aplicacion
```

Los volúmenes del código habilitan recarga automática en FastAPI y Vite. Las dependencias permanecen dentro de las imágenes/volúmenes Docker.

## Seguridad de AdventureWorks

`SQLSERVER_APPLICATION_INTENT=ReadOnly` expresa la intención de conexión, pero **no reemplaza los permisos del motor**. El usuario configurado en `SQLSERVER_USER` debe tener sólo `CONNECT` y lectura (`db_datareader` o permisos `SELECT` más restringidos), sin pertenecer a `db_owner`, `db_ddladmin` ni roles de escritura. Las credenciales reales viven únicamente en `.env`, archivo ignorado por Git.

## Git, CI y CD

El repositorio usa la rama principal `main` y Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, etc.). Antes de enviar cambios:

```bash
make test
make lint
```

GitHub Actions incluye:

- **CI:** valida Compose y construye las etapas de prueba de backend y frontend en cada pull request y push a `main`.
- **CD:** después de cambios en `main` o una etiqueta `v*`, construye y publica imágenes versionadas en GitHub Container Registry (GHCR). Publicar imágenes constituye entrega continua; el despliegue a un ambiente se añadirá cuando se elija el proveedor.
- **Imágenes:** se publican frontend, backend, PostgreSQL inicializado y SQL Server con restauración automática. Los volúmenes no se publican; se reconstruyen de forma determinística.
- **Dependabot:** propone actualizaciones semanales de acciones, npm y pip.

Para vincular este repositorio local con GitHub, primero hay que iniciar sesión nuevamente porque el token local actual está vencido:

```bash
gh auth login -h github.com
gh repo create NOMBRE_REPOSITORIO --private --source=. --remote=origin --push
```

El nombre y la visibilidad del repositorio deben elegirse antes de ejecutar el segundo comando.

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
