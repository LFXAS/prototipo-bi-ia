# Prototipo web de inteligencia de negocios asistido por IA

Base técnica del proyecto de titulación **“Prueba de concepto de un prototipo funcional de BI asistido por IA para la construcción semiautomatizada y supervisada de un datamart de ventas”**. El entorno **Docker-first** ejecuta React + Vite, FastAPI, PostgreSQL y AdventureWorks en SQL Server con un usuario de solo lectura. El producto permite configurar desde la web la fuente y sus secretos, capturar su estructura, generar una propuesta dimensional asistida por IA, aprobarla y materializar un datamart trazable. FastAPI construye el ETL desde plantillas y referencias verificadas, calcula KPI variables y concilia origen y destino; nunca ejecuta SQL libre producido por el LLM.

La versión seleccionada puede verificarse desde la misma plataforma: se comprueban integridad, referencias, calidad y reproducción determinística sin consumir nuevamente el LLM. Sprint 4 amplió el expediente con conciliación OLTP--datamart, KPI sugeridos por IA y recetas controladas. Sprint 5 añadió resolución descriptiva de entidades, dashboard por perfil, hallazgos explicables, copiloto contextual y exportaciones PDF/Excel fieles a la selección. Véanse el [plan acumulativo de validación](docs/validation-plan.md) y las [especificaciones del Sprint 5](docs/specs/SPR-05-analitica-reporteria-y-calidad.md).

La guía operativa completa para replicar, restaurar, publicar y probar el entorno está en [docs/replication-guide.md](docs/replication-guide.md).

Desde el Sprint 2 el proyecto aplica desarrollo guiado por especificaciones (SDD). Antes de crear una funcionalidad se redacta su especificación, criterios de aceptación, riesgos y evidencia de prueba en [`docs/specs/`](docs/specs/README.md). El flujo completo está en [`docs/sdd-workflow.md`](docs/sdd-workflow.md).

La trazabilidad del trabajo se mantiene en LaTeX y PDF. La bitácora vive en `docs/logbook/`, el informe académico del primer sprint en `docs/sprints/` y el manual técnico detallado en `docs/manual-tecnico/`. El [índice documental](docs/README.md) explica la finalidad y custodia de cada artefacto. Todos se regeneran de forma reproducible con `make docs`.

## Alcance confirmado

El alcance vigente define una prueba de concepto académica con una sola fuente SQL Server/AdventureWorks, introspección de metadatos, propuestas de un LLM sujetas a aprobación humana y validaciones determinísticas, ETL hacia PostgreSQL, KPI variables, visualizaciones, hallazgos explicables, copiloto contextual y reportería. El pronóstico fue retirado por decisión del tutor porque corresponde a un problema predictivo distinto del objetivo central.

El Sprint 1 implementó el entorno y la observabilidad mínima. El Sprint 2 implementó autenticación, RBAC, auditoría, parámetros y credenciales LLM cifradas desde la web. El Sprint 3 incorporó la fuente SQL Server, introspección determinística y el asistente supervisado. Sprint 4 materializó la propuesta 52 en la ejecución 6. Sprint 5 corrigió la identidad del cliente mediante la propuesta 54 y la ejecución 7: 121317 líneas sin diferencia, 19820 clientes con nombre y tipo, moneda USD comprobada, panel ejecutivo/analítico, conversación contextual y reportes profesionales. Véanse el [informe técnico del Sprint 5](docs/sprints/sprint-05-analitica-y-reporteria.pdf), el [Capítulo III académico](docs/tesis/capitulo-03-propuesta-tecnologica.pdf) y las [especificaciones](docs/specs/README.md).

Consulta [docs/scope.md](docs/scope.md) y [docs/architecture.md](docs/architecture.md) para el detalle.

## Requisitos

- Docker Engine 24 o superior con Docker Compose v2.
- Al menos 8 GB de memoria disponibles para ejecutar el conjunto de contenedores. Para la alternativa local con Ollama se recomiendan 16 GB de memoria total y al menos 8 GB adicionales de disco libre para la imagen y el modelo.
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

La comprobación `live` confirma que FastAPI funciona. `ready` confirma además la conexión a PostgreSQL. En un volumen vacío, SQL Server descarga el respaldo oficial de AdventureWorks 2022, lo restaura y crea el usuario `bi_reader` sin permisos de escritura. Para usarla como fuente de negocio, abra **Parámetros generales > Conexiones de datos**, registre servidor `sqlserver`, puerto `1433`, base y usuario configurados para la instalación, pruebe el modo de sólo lectura, active el registro y seleccione **Actualizar metadatos**. El resultado se consulta en **Datos > Explorador de esquema**.

En el primer inicio el servicio `migrate` aplica automáticamente las migraciones y el servicio `seed` carga de forma idempotente el catálogo protegido aprobado: permisos, menús, rol administrador y usuario inicial definidos por `BOOTSTRAP_ADMIN_EMAIL` y `BOOTSTRAP_ADMIN_PASSWORD`. Ingrese desde el frontend con esos valores; cámbielos antes de cualquier demostración compartida. Las claves de Gemini, Groq y Qwen se registran con **Registrar credencial** en **Configuración LLM**; no se agregan a `.env`. FastAPI las cifra y la raíz criptográfica se genera automáticamente en el volumen Docker `secret_key_data`, separado de PostgreSQL. El catálogo no copia cuentas de prueba, auditoría, configuraciones LLM, claves ni volúmenes entre equipos.

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

### Alternativa LLM local con Ollama

Ollama es opcional: no se inicia con `make up`, no reemplaza Gemini o Qwen Cloud y no requiere una API key. Se usa como respaldo local cuando no se desea depender de cuotas cloud. Desde la raíz del repositorio:

```bash
make ollama-up
make ollama-pull
make ollama-status
```

La primera descarga guarda `qwen2.5:3b` en el volumen Docker `ollama_models`; se conserva al detener el servicio y cada programadora debe descargarlo una vez en su propio equipo. Es el modelo local recomendado por su respuesta ágil y directa en español. El contexto predeterminado es 4096 para que las respuestas JSON del asistente puedan completarse. No se sincroniza con Git, no se publica en GHCR y CI/CD nunca lo descarga. Luego, en **Configuración LLM**, cree un registro inactivo con proveedor **Ollama local**, URL `http://ollama:11434` y modelo `qwen2.5:3b`; use **Probar conexión**. `qwen3:4b` permanece como alternativa de mayor capacidad, pero puede tardar más por su razonamiento interno. La aplicación confirma tanto el servicio como la presencia del modelo. Para detener Ollama sin borrar el modelo:

```bash
make ollama-down
```

Ollama sólo es accesible desde los contenedores del proyecto; el puerto `11434` no se publica en el computador anfitrión.

## Flujo diario

```bash
make up             # construir y levantar
make seed           # volver a aplicar el catálogo base aprobado sin duplicarlo
make delivery-preview-up # anadir Nginx en 8080 sin detener Vite
make ollama-up      # iniciar alternativa local de LLM, sin descargar aún
make ollama-pull    # descargar qwen2.5:3b una vez por equipo
make ollama-down    # detener Ollama y conservar el modelo
make logs           # seguir los registros
make test           # pruebas de backend y frontend en imagenes Docker
make lint           # calidad estatica en contenedores
make compose-check  # validar desarrollo, entrega y perfil local de Ollama
make docs           # regenerar bitácora, informes de sprint, Capítulo III y manual
make down           # detener la aplicacion
```

Los volúmenes del código habilitan recarga automática en FastAPI y Vite. Las dependencias permanecen dentro de las imágenes/volúmenes Docker.

## Seguridad de AdventureWorks

`SQLSERVER_APPLICATION_INTENT=ReadOnly` expresa la intención de conexión, pero **no reemplaza los permisos del motor**. El usuario configurado en `SQLSERVER_USER` debe tener sólo `CONNECT` y lectura (`db_datareader` o permisos `SELECT` más restringidos), sin pertenecer a `db_owner`, `db_ddladmin` ni roles de escritura. Las variables de `.env` aprovisionan el contenedor local; la credencial que usa el flujo BI se registra desde la web, se cifra en `app.secrets` y no vuelve al navegador.

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

## Cierre funcional y trabajo restante

El flujo principal de la prueba de concepto está completo: configurar, introspectar, proponer, revisar, aprobar, materializar, conciliar, analizar, conversar y exportar. Antes de la entrega académica definitiva faltan actividades de validación y presentación, no otro módulo central:

1. ejecutar pruebas formales de usabilidad y juicio de expertos con instrumentos y actas;
2. documentar el contraste secundario con AdventureWorksDW sólo donde exista equivalencia semántica demostrada;
3. cerrar conclusiones, anexos, evidencias y referencias del documento académico completo;
4. promover el Sprint 5 por PR a `develop` y después a `main` con CI aprobada;
5. mantener inventario, otros dominios, otros motores y despliegue Azure como extensiones futuras, no como requisitos para demostrar el núcleo actual.
