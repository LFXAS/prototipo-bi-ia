# Guía paso a paso: levantar y replicar el entorno

Esta guía cubre dos escenarios: desarrollar con un entorno autocontenido desde cero y ejecutar imágenes publicadas sin compilar el código.

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
   - `8080`: frontend desde imágenes publicadas;
   - `8000`: API;
   - `55432`: PostgreSQL autocontenido;
   - `51433`: SQL Server autocontenido.
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
git checkout -b feat/nombre-cambio
git add .
git commit -m "feat: descripcion breve"
git push -u origin feat/nombre-cambio
```

Abre un pull request. CI valida Compose, compila la bitácora y construye las etapas de prueba. Al fusionar en `main`, CD publica las cinco imágenes con las etiquetas `main` y `sha-*`. Una etiqueta Git `v1.0.0` produce además la imagen `v1.0.0`.

## 6. Levantar el entorno publicado en otra máquina (sin compilar)

La persona puede clonar el repositorio o descargar únicamente `compose.release.yaml` y `.env.release.example`.

```bash
cp .env.release.example .env
```

En `.env`, configura:

```dotenv
IMAGE_PREFIX=ghcr.io/PROPIETARIO/NOMBRE_REPOSITORIO
IMAGE_TAG=main
```

Luego:

```bash
docker compose -f compose.release.yaml pull
docker compose -f compose.release.yaml up -d
docker compose -f compose.release.yaml ps
```

La aplicación quedará en <http://localhost:8080> y la API en <http://localhost:8000>.

Para fijar una entrega académica reproducible, usa una etiqueta inmutable:

```dotenv
IMAGE_TAG=v1.0.0
```

## 7. Detener, conservar o reiniciar datos

Detener conservando bases:

```bash
docker compose down
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
docker compose -f compose.release.yaml pull
docker compose -f compose.release.yaml up -d
```

Las migraciones futuras se ejecutarán como un paso controlado antes de iniciar una nueva versión del backend; nunca se copiará un volumen manualmente como mecanismo normal de despliegue.

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
