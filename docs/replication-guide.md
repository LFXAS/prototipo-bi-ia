# Guía paso a paso: levantar y replicar el entorno

Esta guía cubre dos escenarios: desarrollar con un entorno autocontenido desde cero y ejecutar imágenes publicadas sin compilar el código.

Para comprender cómo se construyó y automatizó esta línea base, consulte también el manual técnico en `docs/manual-tecnico/`. Ese documento comenta variables, Compose, Dockerfiles, Makefile, Git, GitHub Actions, GHCR, persistencia y evidencias; esta guía permanece como referencia breve para ejecutar y replicar.

Las rutas son relativas al repositorio. En este computador el proyecto vive en `/home/ceo/Proyectos/BI`; en otra máquina puede guardarse en cualquier carpeta.

## 1. Qué se comparte y qué no

Se versionan en GitHub:

- código y configuración Compose;
- Dockerfiles de frontend, backend, PostgreSQL y SQL Server;
- scripts para crear los esquemas PostgreSQL;
- script que descarga y restaura AdventureWorks desde el respaldo oficial de Microsoft;
- migraciones y datos sintéticos controlados que se incorporen después;
- flujos CI/CD.

Se publican en GHCR cinco imágenes propias:

- `...-frontend`;
- `...-backend`;
- `...-postgres` (PostgreSQL más inicialización de esquemas);
- `...-sqlserver` (SQL Server más restauración idempotente de AdventureWorks).
- `...-docs` (entorno LaTeX usado para regenerar la bitácora).

No se publican volúmenes Docker ni contraseñas. Los volúmenes son estado local y no forman una imagen reproducible. AdventureWorks se restaura al iniciar un volumen vacío; PostgreSQL se reconstruye mediante scripts/migraciones. Éste es el patrón que permite repetir el entorno con control de versiones.

## 2. Requisitos en cualquier equipo

1. Instalar Docker Desktop en Windows/macOS, o Docker Engine más el complemento Compose en Linux.
2. Asignar al menos 6 GB de memoria a Docker; se recomiendan 8 GB por SQL Server.
3. Tener libres estos puertos o cambiarlos en `.env`:
   - `5173`: frontend de desarrollo;
   - `8080`: vista Nginx local o frontend desde imágenes publicadas;
   - `8000`: API;
   - `55432`: PostgreSQL autocontenido;
   - `51433`: SQL Server autocontenido.
   Si desarrollo y entrega completa se ejecutan a la vez, la entrega usa además `18000`, `55433` y `51434`.
4. En equipos ARM (por ejemplo Apple Silicon), Docker ejecutará SQL Server como `linux/amd64` mediante emulación; el primer inicio puede tardar más.

## 3. Primera ejecución en este computador (desarrollo autocontenido)

```bash
cd "/home/ceo/Proyectos/BI"
cp .env.example .env
```

Abre `.env` y reemplaza todas las claves `ChangeMe_*`. No uses esas claves de ejemplo fuera de desarrollo. Después ejecuta:

```bash
make bootstrap
```

El comando crea contenedores, red y volúmenes exclusivos del proyecto. PostgreSQL se publica en `55432` y SQL Server en `51433`; no usa ni modifica tus contenedores actuales.

Prueba:

```bash
curl http://localhost:8000/api/v1/health/live
curl http://localhost:8000/api/v1/health/ready
```

Abre <http://localhost:5173> y <http://localhost:8000/docs>.

### Añadir la vista Nginx de entrega

Sin detener ni reemplazar los cuatro servicios de desarrollo:

```bash
make delivery-preview-up
```

Vite continúa en <http://localhost:5173> y el frontend compilado con Nginx queda en <http://localhost:8080>. Ambos usan la misma API en `8000` y los mismos volúmenes. Esta modalidad prueba la construcción del frontend, no sustituye la validación del entorno completo publicado.

## 4. Reproducir absolutamente todo desde cero en otra ruta

```bash
cd "/ruta/elegida/BI"
cp .env.example .env
make bootstrap
```

Durante el primer arranque, la imagen SQL Server descarga `AdventureWorks2022.bak` del release oficial de Microsoft, restaura la base y crea `bi_reader` con lectura y denegaciones explícitas de escritura. La descarga/restauración puede tomar varios minutos. Los siguientes arranques reutilizan el volumen.

Revisa el progreso:

```bash
docker compose logs -f sqlserver
```

Cuando todos los servicios estén `healthy`, prueba:

```bash
BACKEND_PORT=8000 FRONTEND_PORT=5173 ./scripts/verify-environment.sh
```

## 5. Compartir el repositorio en GitHub

Una sola vez:

```bash
cd "/home/ceo/Proyectos/BI"
gh auth status || gh auth login -h github.com
gh repo create NOMBRE_REPOSITORIO --private --source=. --remote=origin --push
```

Si las imágenes deben descargarse sin autenticación, cambia la visibilidad del repositorio y de cada paquete GHCR a pública desde GitHub. Si se mantienen privadas, cada usuario debe ejecutar `docker login ghcr.io` con un token que tenga `read:packages`.

Flujo habitual:

```bash
git switch develop
git pull --ff-only origin develop
git switch -c feature/nombre-cambio
# editar y verificar todo dentro de Docker
make verify
git add .
git commit -m "feat: descripcion breve"
git push -u origin feature/nombre-cambio
```

Abre un pull request hacia `develop`. CI valida Compose, código, pruebas y los tres documentos PDF. Para publicar una entrega, abre otro pull request de `develop` hacia `main`; sólo esa fusión activa CD y publica las cinco imágenes con las etiquetas `main` y `sha-*`. Una etiqueta Git `v1.0.0` produce además la imagen `v1.0.0`. Consulta `docs/git-workflow.md` para el procedimiento completo y las reglas de protección.

## 6. Levantar el entorno publicado en otra máquina (sin compilar)

La persona puede clonar el repositorio o descargar únicamente `compose.release.yaml` y `.env.release.example`. El proyecto de entrega tiene otro nombre, red, puertos y volúmenes, de modo que no reemplaza el ambiente de desarrollo.

```bash
cp .env.release.example .env.release
```

En `.env.release`, cambia todos los secretos `ChangeMe_*` y confirma:

```dotenv
IMAGE_PREFIX=ghcr.io/lfxas/prototipo-bi-ia
IMAGE_TAG=main
```

Luego:

```bash
make release-up
docker compose --env-file .env.release -f compose.release.yaml ps
```

La aplicación quedará en <http://localhost:8080> y su API aislada en <http://localhost:18000>. PostgreSQL y SQL Server de entrega se publican en `55433` y `51434`. Desarrollo puede seguir activo en `5173`, `8000`, `55432` y `51433`.

Ejecutar ambos ambientes completos duplica PostgreSQL, SQL Server y sus volúmenes; se recomienda disponer de memoria suficiente. Si sólo se necesita revisar el frontend compilado, usa `make delivery-preview-up` en lugar de iniciar el entorno GHCR completo.

Para fijar una entrega académica reproducible, usa una etiqueta inmutable:

```dotenv
IMAGE_TAG=v1.0.0
```

## 7. Detener, conservar o reiniciar datos

Detener conservando bases:

```bash
docker compose down
make release-down
```

Volver a levantar conserva los volúmenes y no restaura de nuevo.

Para reiniciar desde cero, primero confirma que no necesitas ningún dato y luego elimina sólo los volúmenes de este proyecto:

```bash
docker compose down --volumes
make bootstrap
```

La opción `--volumes` borra de forma irreversible las bases del proyecto Compose actual.

## 8. Actualizar otra máquina

Con código fuente:

```bash
git pull --ff-only
docker compose up --build -d
```

Con imágenes GHCR:

```bash
make release-up
```

Las migraciones futuras se ejecutarán como un paso controlado antes de iniciar una nueva versión del backend; nunca se copiará un volumen manualmente como mecanismo normal de despliegue.

Si se actualiza documentación o una especificación SDD, el procedimiento es el mismo: obtener la rama aprobada, ejecutar `make docs` si se modificó LaTeX y comprobar que `git status` sólo muestra los archivos esperados. No se vuelve a clonar el repositorio para cada cambio; se usa `git pull --ff-only` cuando no existen modificaciones locales pendientes.

## 9. Diagnóstico rápido

```bash
docker compose ps
docker compose logs --tail=200 backend
docker compose logs --tail=200 frontend
docker compose logs --tail=200 postgres sqlserver
```

- API viva pero `ready` falla: revisa PostgreSQL, credenciales y puerto.
- SQL Server nunca queda saludable: revisa memoria, política de la clave SA y acceso a GitHub para descargar el `.bak`.
- Puerto ocupado: cambia `*_PORT` o `LOCAL_*_PORT` en `.env`.
- `5173` funciona y `8080` no responde: inicia la vista con `make delivery-preview-up` o la entrega completa con `make release-up`.
- GHCR responde `denied`: el paquete es privado o falta `docker login ghcr.io`.
- En ARM el inicio es lento: verifica que la emulación `linux/amd64` esté habilitada.

## 10. Evidencias para la tesis

Conserva por versión:

- SHA del commit y etiqueta Git;
- etiquetas/digest de las cinco imágenes GHCR;
- salida de CI;
- versión de AdventureWorks (`AdventureWorks2022`);
- hash del respaldo descargado, cuando se congele la beta;
- resultados de pruebas y migraciones aplicadas.

## 11. Cerrar el ciclo CI/CD en Azure

La alternativa recomendada para la demostración académica es Azure for Students: aporta crédito temporal sin exigir tarjeta a estudiantes elegibles. No equivale a alojamiento gratuito permanente; se debe configurar presupuesto, alertas y apagado automático.

Flujo previsto:

1. crear por infraestructura como código una VM Ubuntu x64 de 2 vCPU y 8 GiB;
2. instalar Docker y el complemento Compose mediante inicialización reproducible;
3. crear el ambiente protegido `production` en GitHub;
4. autenticar GitHub Actions con Azure mediante OIDC, sin secreto de cliente persistente;
5. después de CI y aprobación, desplegar una etiqueta `vX.Y.Z` de GHCR;
6. ejecutar sondas HTTP y conservar SHA, digest y evidencia del despliegue;
7. apagar o desasignar la VM cuando no se use para proteger el crédito.

La activación de la cuenta, creación de recursos y configuración OIDC están pendientes. No se incorporará un workflow que falle por secretos inexistentes antes de completar esos prerrequisitos.
