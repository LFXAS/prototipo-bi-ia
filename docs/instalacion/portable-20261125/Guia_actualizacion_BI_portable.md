---
lang: es-EC
papersize: a4
fontsize: 10pt
geometry: margin=20mm,headheight=15pt
mainfont: DejaVu Sans
monofont: DejaVu Sans Mono
colorlinks: true
linkcolor: NavyBI
urlcolor: TealBI
---

\begin{titlepage}
\vspace*{12mm}
{\color{TealBI}\sffamily\bfseries PROYECTO BI + IA\par}
\vspace{10mm}
{\color{NavyBI}\sffamily\bfseries\fontsize{29}{34}\selectfont Actualizar BI Portable\par}
\vspace{5mm}
{\Large Guía de instalación limpia para las programadoras\par}
\vspace{10mm}
{\large Desarrollo y release · Una orden a la vez\par}
\vspace{12mm}
\begin{tcolorbox}[colback=PaleBI,colframe=TealBI,boxrule=.6pt,arc=2mm]
\textbf{Esta guía prepara la siguiente entrega.} El paquete nuevo todavía debe construirse, recibir su nombre definitivo y superar sus verificaciones. Esta guía no convierte el portable del 17 de noviembre en una versión actualizada.
\end{tcolorbox}
\vspace{8mm}
La instalación se realizará en el computador receptor. Los contenedores y datos del computador del tutor no se retirarán ni se copiarán por este procedimiento.
\vfill
{\color{TealBI}\bfseries Edición documental: 25 de noviembre de 2026\par}
\vspace{4mm}
El PDF explica el recorrido. El archivo Markdown conserva cada comando completo para copiarlo sin los saltos de línea de la página impresa. Ambos son documentación, no instaladores ni scripts.
\end{titlepage}

\tableofcontents
\clearpage

# Antes de empezar

El resultado buscado es una **instalación limpia** con el código nuevo, los servicios de desarrollo y release, la estructura PostgreSQL completa, un administrador y las dos bases públicas de demostración en SQL Server. Las API keys, conexiones, propuestas, ejecuciones y datamarts privados del tutor no se trasladan.

Cada ambiente conserva sus propias bases, credenciales y clave de cifrado. Con **8 GB de RAM se utilizará un solo ambiente a la vez**. No iniciar Ollama ni otra instancia SQL adicional durante la demostración.

## Cómo usar esta guía

1. Leer y verificar el paquete nuevo antes de retirar el anterior.
2. Identificar los recursos antiguos por sus etiquetas Docker.
3. Detener y eliminar sólo los recursos BI comprobados.
4. Iniciar desarrollo y comprobarlo; detenerlo antes de probar release.
5. Configurar cada ambiente y repetir el recorrido BI con ambas fuentes.

**No copie bloques completos a la terminal.** Ejecute una orden, compruebe el resultado y continúe. Los comandos que comienzan con `read` piden escribir un nombre real observado. No escriba el símbolo `$` del indicador de la terminal.

## Comprobar el Ubuntu receptor

Si trabaja en Windows, lea el siguiente apartado de preparación WSL y continúe con la sección común del paquete nuevo. La identidad `ls-va@Lenovo` corresponde únicamente al Ubuntu de la programadora que reemplazará su instalación anterior.

```bash
whoami
```

```bash
printf '%s\n' "$HOME"
```

```bash
hostname -s
```

En el Ubuntu conocido deben aparecer **ls-va**, **/home/ls-va** y **Lenovo**. Si aparece `ceo`, `/home/ceo` o un equipo distinto, detenerse. Las órdenes de retirada incluyen esa comprobación para que no operen en el equipo del tutor. No cambie la comprobación para hacer desaparecer un error.

```bash
uname -m
```

```bash
free -h
```

```bash
df -h "$HOME"
```

```bash
docker version
```

```bash
docker compose version
```

Se requiere arquitectura `x86_64`, Docker con cliente y servidor disponibles y el complemento Compose. Hay que disponer de espacio para el archivo recibido, las imágenes importadas y los volúmenes nuevos. Conservar Docker ya instalado; un fallo de la aplicación no exige reinstalarlo.

\clearpage

# Preparar Windows para una instalación inicial

Este recorrido corresponde al equipo Windows de la otra programadora. **No se ha probado su instalación remota.** Se prepara Ubuntu bajo WSL 2 y después se utilizan los mismos archivos portable desde su carpeta Linux. Si Docker y WSL ya funcionan, comprobarlos y conservarlos; no reinstalarlos por rutina.

## Comprobar Windows y WSL desde PowerShell

Abrir PowerShell y ejecutar una orden a la vez:

```powershell
winver
```

```powershell
wsl --version
```

```powershell
wsl -l -v
```

La documentación Docker consultada el 25-11-2026 enumera Windows 10 Pro de 64 bits, versión 22H2, compilación 19045, WSL 2.1.5 o posterior y 8 GB de RAM para esta ruta. Confirmar además las condiciones vigentes de soporte del sistema operativo en la página oficial antes de elegir el instalador.

## Instalar WSL sólo si falta

Abrir **PowerShell como administrador**. Si Ubuntu 24.04 no está instalado, utilizar:

```powershell
wsl --install -d Ubuntu-24.04
```

Reiniciar Windows si se solicita. Abrir **Ubuntu 24.04** desde Inicio, esperar su preparación y crear el usuario y contraseña Linux. La contraseña no se muestra mientras se escribe. No es la contraseña de la aplicación BI.

Si WSL ya existe y requiere actualización, utilizar en PowerShell:

```powershell
wsl --update
```

```powershell
wsl -l -v
```

La distribución elegida debe indicar **VERSION 2**. Si esa distribución exacta aparece como `Ubuntu-24.04` con versión 1, convertirla con:

```powershell
wsl --set-version Ubuntu-24.04 2
```

No cambiar el nombre de una distribución distinta por aproximación. Si falla la virtualización, resolver ese requisito con el responsable del equipo antes de continuar.

\clearpage

## Configurar Docker Desktop y recibir el archivo

Descargar Docker Desktop para Windows **x86_64** desde la página oficial Docker, no desde sitios de terceros. Instalarlo sólo si falta y abrirlo; completar el reinicio solicitado, si corresponde.

En Docker Desktop:

1. En **Settings → General**, utilizar el motor basado en WSL 2.
2. En **Settings → Resources → WSL Integration**, habilitar la distribución Ubuntu utilizada y aplicar los cambios.
3. Utilizar **contenedores Linux**. Si el menú ofrece cambiar a Linux containers, elegir esa opción.
4. Esperar a que Docker indique que su motor está disponible.

Las órdenes siguientes se escriben en la terminal **Ubuntu**, no en PowerShell:

```bash
docker version
```

```bash
docker compose version
```

```bash
docker info --format '{{.OSType}}'
```

Deben responder el cliente y servidor, Compose y el tipo `linux`. No instalar otro servidor Docker dentro de Ubuntu si se está utilizando correctamente la integración de Docker Desktop.

Preparar una carpeta de recepción en el HOME Linux:

```bash
mkdir -p "$HOME/Descargas"
```

```bash
cd "$HOME/Descargas"
```

```bash
explorer.exe .
```

Se abrirá el Explorador de Windows en esa carpeta Ubuntu. Copiar allí el **nuevo** `.tar.gz` y su `.tar.gz.sha256` desde la ubicación donde se recibieron. No extraer el desarrollo directamente en una ruta `C:\...`; la instalación se mantendrá en `~/BI/` dentro de Ubuntu.

Continuar con **Preparar el paquete nuevo sin arrancarlo** y **Identificar nombres, imágenes y proyectos**. Al ser una instalación inicial, **saltar los dos apartados de retirada de contenedores, volúmenes y carpetas Ubuntu Lenovo**. Seguir con Iniciar desarrollo. Con 8 GB, probar un solo ambiente a la vez.

Fuentes oficiales, consulta del 25-11-2026: [Docker Desktop para Windows](https://docs.docker.com/desktop/setup/install/windows-install/) y [Microsoft: instalar WSL](https://learn.microsoft.com/en-us/windows/wsl/install).

\clearpage

# Preparar el paquete nuevo sin arrancarlo

**Este paso sólo se realizará cuando el tutor entregue el archivo nuevo y su suma SHA-256.** No seleccionar el archivo del 17 de noviembre suponiendo que contiene estas correcciones. El manifiesto nuevo deberá identificar el corte real del código y las imágenes de ambos modos.

Copiar juntos el `.tar.gz` y el `.tar.gz.sha256` a Descargas. Abrir una terminal y mantenerla durante la instalación.

```bash
cd "$HOME/Descargas"
```

```bash
ls -lh BI_portable_*.tar.gz BI_portable_*.tar.gz.sha256
```

Escribir el nombre exacto del paquete nuevo, **sin** la terminación `.tar.gz`. Esta variable evita inventar una fecha o etiqueta futura.

```bash
read -r -p "Nombre real del paquete nuevo, sin .tar.gz: " BI_PACKAGE
```

```bash
sha256sum -c "$BI_PACKAGE.tar.gz.sha256"
```

Debe indicar `OK`. Si no coincide, copiar nuevamente los archivos y detener aquí la instalación.

```bash
mkdir -p "$HOME/BI"
```

```bash
test ! -e "$HOME/BI/$BI_PACKAGE" && tar --keep-old-files -xzf "$HOME/Descargas/$BI_PACKAGE.tar.gz" -C "$HOME/BI"
```

Si la carpeta existe, no extraer encima. Una carpeta usada por desarrollo no debe reemplazarse mientras sus servicios están activos.

```bash
BI_NEW_DIRECTORY="$HOME/BI/$BI_PACKAGE"
```

```bash
cd "$BI_NEW_DIRECTORY"
```

```bash
pwd -P
```

```bash
sha256sum -c SHA256SUMS.txt
```

Todas las sumas deben coincidir. Todavía no editar el código ni las configuraciones.

```bash
chmod 600 config/desarrollo.env config/release.env CREDENCIALES_LOCALES.txt
```

```bash
less MANIFIESTO.json
```

Salir de `less` con la tecla **q**. Comprobar que el manifiesto corresponde al paquete nuevo, explica si es una entrega limpia y registra las pruebas realizadas. Los resultados de noviembre anterior no sustituyen sus verificaciones nuevas.

\clearpage

# Identificar nombres, imágenes y proyectos

Desde la carpeta nueva, validar ambos Compose sin imprimir sus variables privadas.

```bash
docker compose --env-file config/desarrollo.env -f compose.desarrollo.yaml config --quiet
```

```bash
docker compose --env-file config/release.env -f compose.release.yaml config --quiet
```

```bash
sed -n '/^name:/p' compose.desarrollo.yaml compose.release.yaml
```

Estos son los nombres de proyecto **nuevos**. Anotarlos; ninguno se retirará. No añadir `-p` con un nombre de una entrega antigua. Usar el nombre declarado en los archivos recibidos.

```bash
docker compose --env-file config/desarrollo.env -f compose.desarrollo.yaml config --images
```

```bash
docker compose --env-file config/release.env -f compose.release.yaml config --images
```

```bash
docker load -i imagenes.tar
```

El archivo debe cargar las imágenes exactas del manifiesto: backend y frontend para desarrollo y release, PostgreSQL y SQL Server. No usar `--build` ni descargar imágenes para el primer inicio.

## Descubrir el BI anterior aunque su carpeta haya desaparecido

```bash
docker compose ls --all
```

```bash
docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

| Instalación anterior conocida | Nombre de proyecto que puede aparecer |
|---|---|
| Portable de octubre | `bi-limpio-dev` y `bi-limpio-release` |
| Portable del 17 de noviembre | `bi-portable-20261117-dev` y `bi-portable-20261117-release` |
| Clones antiguos | `bi-ia-prototype` y `bi-ia-prototype-release` |

Eliminar una carpeta con Supr **no detiene ni elimina sus contenedores o volúmenes**. Por eso puede quedar ocupado el puerto 11433 aunque el directorio ya no exista. Se puede identificar y retirar el contenedor por sus etiquetas; no hace falta reconstruir el YAML antiguo ni utilizar el nuevo para borrar el anterior.

`bd-stack`, MySQL, MariaDB, pgAdmin, otros proyectos y recursos sin pertenencia BI comprobada quedan fuera de la sustitución.

\clearpage

# Retirar contenedores antiguos, uno por uno

Este paso es exclusivo del Ubuntu receptor identificado. La sustitución limpia del BI antiguo fue autorizada sin respaldo. Sus configuraciones y datos de prueba se perderán cuando se retiren sus volúmenes. **No se ejecutaron estas retiradas durante la elaboración de la guía.**

Elegir un proyecto antiguo de la tabla anterior. Repetir después el procedimiento para cada proyecto que realmente exista, incluido release.

```bash
read -r -p "Proyecto BI antiguo exacto: " BI_OLD_PROJECT
```

```bash
docker ps -a --filter "label=com.docker.compose.project=$BI_OLD_PROJECT" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

```bash
docker volume ls --filter "label=com.docker.compose.project=$BI_OLD_PROJECT"
```

Elegir **un** nombre de contenedor del listado. Por ejemplo, sólo si aparece: `bi-limpio-dev-sqlserver-1`. No escribir un nombre de la instalación nueva.

```bash
read -r -p "Nombre exacto de UN contenedor BI antiguo listado: " BI_OLD_CONTAINER
```

```bash
docker container inspect "$BI_OLD_CONTAINER" --format '{{.Name}} | proyecto={{index .Config.Labels "com.docker.compose.project"}} | carpeta={{index .Config.Labels "com.docker.compose.project.working_dir"}}'
```

Comprobar proyecto y carpeta. Las rutas antiguas conocidas son:

- `~/Descargas/BI_portable_2026-10-29_v02`.
- `~/BI/BI_portable_2026-11-17_v01`.
- Los dos clones BI de `~/Proyectos/`.

Que la carpeta ya no exista no cambia la etiqueta histórica del contenedor.

La orden siguiente sólo admite los proyectos antiguos de la tabla, exige el equipo receptor y vuelve a comprobar la etiqueta del contenedor antes de detenerlo:

```bash
test "$(id -un):$HOME:$(hostname -s)" = 'ls-va:/home/ls-va:Lenovo' && [[ "$BI_OLD_PROJECT" =~ ^(bi-limpio-(dev|release)|bi-portable-20261117-(dev|release)|bi-ia-prototype(-release)?)$ ]] && test "$(docker container inspect "$BI_OLD_CONTAINER" --format '{{index .Config.Labels "com.docker.compose.project"}}')" = "$BI_OLD_PROJECT" && docker stop "$BI_OLD_CONTAINER"
```

Eliminar únicamente ese contenedor, sin forzar:

```bash
test "$(id -un):$HOME:$(hostname -s)" = 'ls-va:/home/ls-va:Lenovo' && [[ "$BI_OLD_PROJECT" =~ ^(bi-limpio-(dev|release)|bi-portable-20261117-(dev|release)|bi-ia-prototype(-release)?)$ ]] && test "$(docker container inspect "$BI_OLD_CONTAINER" --format '{{index .Config.Labels "com.docker.compose.project"}}')" = "$BI_OLD_PROJECT" && docker rm "$BI_OLD_CONTAINER"
```

Repetir **leer nombre → inspeccionar → detener → eliminar** para los demás contenedores listados de ese proyecto. `migrate` y `seed` pueden estar ya terminados; también deben retirarse si pertenecen al BI antiguo. Una lista vacía significa que no hay contenedores de ese proyecto que eliminar.

\clearpage

# Retirar volúmenes y carpetas anteriores

Conservar el valor de `BI_OLD_PROJECT` comprobado. Si se cerró la terminal, repetir la identificación anterior; no suponer que las variables siguen definidas.

```bash
docker ps -a --filter "label=com.docker.compose.project=$BI_OLD_PROJECT"
```

El listado de contenedores debe quedar vacío antes de retirar sus volúmenes.

```bash
docker volume ls --filter "label=com.docker.compose.project=$BI_OLD_PROJECT"
```

```bash
read -r -p "Nombre exacto de UN volumen BI antiguo listado: " BI_OLD_VOLUME
```

```bash
docker volume inspect "$BI_OLD_VOLUME" --format '{{.Name}} | proyecto={{index .Labels "com.docker.compose.project"}} | volumen={{index .Labels "com.docker.compose.volume"}}'
```

Sólo si la etiqueta coincide con el proyecto antiguo elegido:

```bash
test "$(id -un):$HOME:$(hostname -s)" = 'ls-va:/home/ls-va:Lenovo' && [[ "$BI_OLD_PROJECT" =~ ^(bi-limpio-(dev|release)|bi-portable-20261117-(dev|release)|bi-ia-prototype(-release)?)$ ]] && test "$(docker volume inspect "$BI_OLD_VOLUME" --format '{{index .Labels "com.docker.compose.project"}}')" = "$BI_OLD_PROJECT" && docker volume rm "$BI_OLD_VOLUME"
```

Repetir para cada volumen BI antiguo comprobado, incluido release. Si Docker informa que está en uso, localizar primero su contenedor; no añadir una opción de fuerza. Un volumen sin la etiqueta esperada no se borra por parecido de nombre.

## Borrar la carpeta sólo después de validar la instalación nueva

Después de completar los pasos de inicio y acceso de esta guía, abrir el gestor de archivos y seleccionar **únicamente** el directorio antiguo identificado. Revisar su ruta completa y enviarlo a la papelera. Si ya fue eliminado con Supr, omitir esta operación: la retirada Docker anterior sigue siendo necesaria.

No borrar `Descargas`, `BI`, `Proyectos` ni `/home/ls-va` completos. No borrar la carpeta nueva: desarrollo utilizará `fuente/` desde allí. Los clones antiguos `~/Proyectos/prototipo-bi-ia-dev` y `~/Proyectos/prototipo-bi-ia-release` se retiran sólo después de haber comprobado y retirado sus propios recursos Docker.

Las imágenes antiguas que permanezcan son caché y no se ejecutan por sí solas. No son motivo para realizar una limpieza global; una imagen de infraestructura puede ser compartida entre etiquetas de entregas. La guía no utiliza `docker system prune`, `docker volume prune`, borrados generales ni eliminación forzada de imágenes.

\clearpage

# Iniciar desarrollo y comprobar la preparación

Volver a la carpeta **nueva**. Mantener detenidos los proyectos viejos y el ambiente release. Los puertos siguientes corresponden al contrato portable anterior que deberá verificar el manifiesto nuevo.

```bash
cd "$BI_NEW_DIRECTORY"
```

```bash
docker compose --env-file config/desarrollo.env -f compose.desarrollo.yaml config --quiet
```

```bash
docker compose --env-file config/desarrollo.env -f compose.desarrollo.yaml up -d --pull never --wait --wait-timeout 900
```

Esperar a que termine. El primer inicio crea volúmenes vacíos, inicia PostgreSQL, aplica migraciones y carga la semilla. SQL Server restaura las dos muestras incluidas en su imagen y configura el lector. No se importan los volúmenes del tutor.

```bash
docker compose --env-file config/desarrollo.env -f compose.desarrollo.yaml ps -a
```

| Servicio | Estado esperado |
|---|---|
| `postgres`, `sqlserver`, `backend`, `frontend` | Activos y `healthy` |
| `migrate`, `seed` | `Exited (0)`: tareas terminadas correctamente |

**Exited (0) no es un error.** `Exited (1)` en `migrate` o `seed` sí exige revisar sus registros antes de continuar.

```bash
docker compose --env-file config/desarrollo.env -f compose.desarrollo.yaml exec -T backend alembic current
```

El corte actual incorpora la migración **20261125_20** y el parámetro de sesión. El paquete definitivo deberá incluirla o una revisión posterior declarada. No cambiar manualmente el número en PostgreSQL ni marcar una migración como aplicada para ocultar un fallo.

```bash
curl --fail --silent --show-error http://localhost:18080/api/v1/health/live
```

Abrir **http://localhost:15173/**. Consultar las credenciales del ambiente desarrollo en `CREDENCIALES_LOCALES.txt` de forma privada, sin compartir esa pantalla. El archivo contiene las claves nuevas del paquete, no la contraseña habitual del tutor.

Para desarrollar se edita `fuente/backend` y `fuente/frontend` dentro de la carpeta nueva. Esos son los directorios montados por el Compose portable. Conservar la carpeta y su ubicación mientras se utilice.

\clearpage

# Probar release y encender o apagar cada ambiente

En un equipo de 8 GB, detener desarrollo antes de iniciar release. Los dos ambientes tienen almacenamiento independiente; configurar uno no configura automáticamente el otro.

```bash
docker compose --env-file config/desarrollo.env -f compose.desarrollo.yaml stop -t 60
```

```bash
docker compose --env-file config/release.env -f compose.release.yaml config --quiet
```

```bash
docker compose --env-file config/release.env -f compose.release.yaml up -d --pull never --wait --wait-timeout 900
```

```bash
docker compose --env-file config/release.env -f compose.release.yaml ps -a
```

```bash
docker compose --env-file config/release.env -f compose.release.yaml exec -T backend alembic current
```

Abrir **http://localhost:18088/** e ingresar con la credencial **release** del paquete. Este modo sirve el frontend compilado y el backend de entrega. No equivale por sí mismo a una promoción aprobada a `main`: el manifiesto indicará la procedencia del código.

| Uso | Desarrollo | Release |
|---|---|---|
| Web local | `15173` | `18088` |
| API local | `18080` | `18081` |
| PostgreSQL publicado | `15432` | `15433` |
| SQL Server publicado | `11433` | `11434` |
| SQL desde el backend | `sqlserver:1433` | `sqlserver:1433` |

## Volver a desarrollo

```bash
docker compose --env-file config/release.env -f compose.release.yaml stop -t 60
```

```bash
docker compose --env-file config/desarrollo.env -f compose.desarrollo.yaml up -d --pull never --wait --wait-timeout 900
```

## Operación diaria

Para apagar, utilizar el `stop -t 60` del ambiente en uso. Para encender de nuevo, utilizar su `up` anterior. Estos comandos conservan los volúmenes. No repetir extracción, `docker load`, limpieza de contenedores ni configuración inicial cada día.

No añadir `--volumes` o `-v` para apagar. Los volúmenes contienen configuración, usuarios, metadatos y datamarts; la clave de cifrado debe conservarse junto con la base que protege.

\clearpage

# Configurar el sistema limpio

Primero comprobar la URL del ambiente en uso. Repetir esta configuración por separado en desarrollo y release si se utilizarán ambos.

## 1. Registrar las dos conexiones de demostración

En **Conexiones de datos**, crear una conexión para cada base:

| Campo | Valor |
|---|---|
| Motor | SQL Server |
| Servidor | `sqlserver` |
| Puerto interno | `1433` |
| Primera base | `AdventureWorks2022` |
| Segunda base | `WideWorldImporters` |
| Usuario lector | `bi_reader` |
| Contraseña | La del lector SQL del ambiente activo en el archivo privado |

Para el certificado local, usar cifrado y confianza del certificado cuando el formulario los ofrezca. No usar el puerto publicado del computador como puerto interno Docker. No usar la clave de acceso web como clave SQL ni trabajar con `sa` en la operación BI habitual.

En cada conexión: **Probar conexión → comprobar sólo lectura → Habilitar → Leer metadatos**. Ambas pueden quedar habilitadas; el selector de fuente determina el contexto de trabajo.

## 2. Configurar OpenAI con consumo controlado

En **Configuración LLM**, crear una configuración con estos valores:

- Proveedor: **OpenAI**.
- URL: `https://api.openai.com/v1`.
- Modelo inicial: **gpt-6-luna**.
- Nivel de razonamiento: **Bajo**.

Es el preset económico vigente; su acceso y disponibilidad se comprobarán con la cuenta de API utilizada. El campo modelo sigue siendo editable.

Guardar el registro; después usar **Registrar credencial** e ingresar la API key directamente en el campo privado. No escribirla en Parámetros, código, documentos, capturas ni chats. Usar **Probar conexión** y activar la configuración cuando la prueba resulte satisfactoria.

El paquete limpio no lleva la clave ni el crédito del tutor. Las llamadas reales requieren Internet y consumen la cuota de la cuenta configurada. Vigilar el saldo y evitar repetir generaciones sólo para obtener capturas. Una prueba de conexión no demuestra por sí sola la generación correcta de una propuesta BI.

## 3. Revisar duración de sesión

Abrir **Parámetros**, localizar el grupo **Seguridad** y el campo **Duración de la sesión (minutos)**.

Su identificador es `AUTH_SESSION_MINUTES`. El valor inicial es **60** y el rango permitido es **15–240** minutos. Guardar el valor elegido y volver a iniciar sesión. El cambio afecta los tokens nuevos; no alarga uno ya emitido.

## 4. Preparar el catálogo de cada fuente

En **Explorador de esquema**, revisar la cabecera y la instantánea de la fuente elegida. Después, en **Catálogo analítico**, revisar preguntas y periodicidades de esa misma conexión y guardar. Repetir con la otra base. Las preguntas personalizadas no se copian entre bases por coincidencia de nombre.

\clearpage

# Recorrer BI con ambas bases y registrar la prueba

La instalación limpia genera sus propios identificadores. No buscar números de propuestas o ejecuciones que aparezcan en capturas del tutor.

## Primera fuente

1. Elegir AdventureWorks en la cabecera; confirmar base e instantánea.
2. Revisar tablas, claves y relaciones en el Explorador. El evento comercial de los ejemplos de pedidos debe conservar esa interpretación.
3. Revisar el catálogo y seleccionar preguntas pertinentes.
4. En el Asistente, describir una necesidad acotada, por ejemplo comparar mensualmente importes, unidades y pedidos por producto y territorio, con promedio por pedido.
5. Autorizar el destino LLM mostrado y validar la viabilidad de la necesidad. Resolver ambigüedades; el esquema no demuestra por sí solo significado comercial, moneda ni calidad de filas.
6. Generar la propuesta y recorrer Necesidad, Conceptos, Propuesta, Personalización y Revisión. Comprobar granularidad, medidas, KPI y relaciones. Aprobar sólo el resultado compatible.
7. En Datamart de ventas: elegir propuesta, revisar los indicadores, confirmar y materializar. La aprobación anterior no ejecutó el ETL.
8. Revisar conciliación, cantidades, importes, identidad descriptiva y posibles decisiones semánticas antes de interpretar los resultados.
9. En Analítica, comprobar fuente, ejecución y propuesta; aplicar año y territorio; revisar el denominador de cada promedio. Exportar PDF y Excel y contrastarlos con la selección visible.

## Segunda fuente

Repetir el recorrido con WideWorldImporters. Para un caso de facturación, solicitar expresamente ventas facturadas, líneas de factura, comprador y ubicación relacionada pertinente. No convertir pedidos en facturas ni confundir comprador con destinatario de facturación o ciudad postal con ciudad de entrega.

## Comprobar continuidad

- Recargar un módulo: debe conservarse ese módulo autorizado.
- Entrar desde Inicio o Revisar configuración: **Atrás** debe volver al recorrido que lo abrió, conservando el paso. Una entrada directa desde la barra no necesita ese botón contextual.
- En Analítica, usar Consultar respaldo y volver: conservar ejecución, indicador, vista y filtros confirmados.
- Alternar las dos fuentes y regresar: cada conexión conserva su propia selección dentro de la pestaña, sin traer filtros, datos o chat de la otra.
- Si una pregunta del borrador fue retirada del catálogo, el objetivo se conserva y se pide revisar la selección y validar otra vez. Las propuestas históricas conservan su evidencia.
- Un KPI añadido por una regla desde un requisito validado debe explicar que procede de la plataforma; no atribuir esa adición al proveedor IA.

Registrar fecha, equipo, ambiente, corte del manifiesto, fuente, IDs propios, resultado y captura sin secretos. Los ensayos nuevos de un modelo deben anotarse como tales: los resultados observados con otro modelo no los certifican automáticamente.

\clearpage

# Resolver los incidentes que ya ocurrieron

## El directorio anterior fue borrado con Supr

Los contenedores y volúmenes pueden seguir existiendo. Utilizar los pasos de identificación y retirada por etiquetas. No extraer una versión nueva dentro de la carpeta antigua desaparecida para intentar recuperarla ni usar un Compose nuevo con un proyecto viejo.

## Error: puerto 11433 ya ocupado

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}'
```

Buscar el contenedor que publica ese puerto. En la experiencia anterior era `bi-limpio-dev-sqlserver-1`. Si pertenece al BI viejo, aplicar su retirada selectiva. Si es otro proyecto, detener esta sustitución y revisar: no eliminarlo. Después repetir el `up` del ambiente nuevo.

## Error: migrate terminó con código 1

```bash
docker compose --env-file config/desarrollo.env -f compose.desarrollo.yaml logs --tail 120 migrate
```

```bash
docker compose --env-file config/desarrollo.env -f compose.desarrollo.yaml logs --tail 80 postgres seed backend
```

La causa se determina leyendo ese mensaje, no sólo el estado rojo. Comprobar que se usa la carpeta, configuración y proyecto nuevos; que la migración actual está incluida y que no se reutilizó un volumen antiguo con otra configuración. No cambiar contraseñas por aproximación, no editar `alembic_version` y no borrar volúmenes como primer intento.

## SQL Server o la espera de 900 segundos no termina

```bash
docker compose --env-file config/desarrollo.env -f compose.desarrollo.yaml logs --tail 100 sqlserver
```

```bash
free -h
```

```bash
df -h "$HOME"
```

Comprobar que sólo está activo un ambiente, que existe espacio y que la restauración sigue avanzando. Un segundo `up` puede retomar la preparación idempotente; no obliga a eliminar datos. Para release, usar sus dos archivos en las mismas consultas.

## La propuesta o el proveedor falla

Leer el mensaje antes de reintentar. Comprobar catálogo visible, fuente, autorización de metadatos, modelo, credencial, prueba y saldo. Un rechazo del contrato no se corrige aceptando cualquier JSON ni inventando columnas. Conservar la necesidad y la evidencia, resolver la causa y generar una versión nueva cuando corresponda. No repetir llamadas costosas de forma automática.

Los registros se revisan localmente; ocultar datos privados antes de compartirlos. No imprimir `docker compose config` completo, `.env`, credenciales o inspecciones Docker completas en capturas.

\clearpage

# Qué se conserva y cuándo está listo

## Código de desarrollo y código de release

El portable utiliza **una fuente de autoría** en `fuente/`. Desarrollo la monta y permite trabajar en ella. Release utiliza imágenes compiladas del corte declarado; editar `fuente/` no cambia esas imágenes. Una nueva entrega release exige reconstruir y comprobar sus imágenes desde el código elegido.

Los clones viejos `~/Proyectos/prototipo-bi-ia-dev` y `~/Proyectos/prototipo-bi-ia-release` no actualizan este portable ni son la fuente que monta su Compose. No iniciar un tercer conjunto desde `fuente/compose.yaml` o mediante `make up` durante esta instalación. Usar los Compose situados en la raíz del paquete.

## Bases, volúmenes y cifrado

`docker load` importa **imágenes**, no los volúmenes del tutor. PostgreSQL obtiene su estructura por migraciones y semilla. SQL Server obtiene las muestras públicas desde el respaldo incluido en la imagen offline. Los cambios realizados después del inicio viven en los volúmenes del ambiente receptor.

La clave raíz de cifrado se crea en su volumen local `secret_key_data`. Protege las credenciales guardadas por la aplicación. La base PostgreSQL y esa clave deben mantenerse juntas para recuperar secretos existentes. No importar sólo PostgreSQL desde otra instalación ni copiar una clave del tutor sobre la recién creada.

## Lista de aceptación del receptor

- [ ] Sumas externa e internas correctas; imágenes coinciden con el manifiesto nuevo.
- [ ] Ningún contenedor o volumen ajeno al BI antiguo fue retirado.
- [ ] Desarrollo y release se probaron por separado; cuatro servicios saludables y `migrate`/`seed` con salida cero.
- [ ] Migración 20261125_20 o posterior declarada presente; sesión parametrizable comprobada.
- [ ] Administrador accede y utiliza credenciales propias del ambiente.
- [ ] Ambas muestras conectan en sólo lectura y muestran sus metadatos.
- [ ] Catálogo, necesidad, propuesta, ETL y analítica conservan la fuente correcta.
- [ ] Conciliación y exportaciones revisadas; filtros y ejecución conservados al volver a una fuente.
- [ ] IA probada sólo con credencial autorizada y saldo comprobado; limitaciones anotadas.
- [ ] Después de `stop` y `up`, se conserva el trabajo del receptor.
- [ ] Carpeta nueva conservada; carpetas antiguas retiradas sólo al concluir la comprobación.

En Windows, la instalación nueva se realiza desde Ubuntu en WSL 2 con Docker compatible y los archivos dentro del HOME Linux. Las órdenes destructivas protegidas para `ls-va@Lenovo` **no se adaptan automáticamente a ese equipo**. Revisar sus requisitos y usuario propios antes de una sustitución; la otra programadora indicó una instalación inicial, no una limpieza de proyectos ajenos.

## Base documental y alcance de esta edición

Esta guía toma como antecedente la instalación directa y la guía portable del 17-11-2026. Sus comandos de importación, inicio, parada y consulta se conservan, ahora con nombres leídos del paquete definitivo y retirada individual por etiquetas aunque el directorio antiguo falte. Se incorporan las correcciones operativas y la configuración económica OpenAI del 25-11-2026.

La elaboración de este documento no construyó el paquete nuevo ni ejecutó instalaciones o retiradas en el equipo receptor. El manifiesto y el informe de aceptación del nuevo portable deberán registrar sus propios resultados antes de distribuirlo.
