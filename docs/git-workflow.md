# Flujo Git del prototipo

## Objetivo

Separar el trabajo diario de las entregas demostrables:

```text
feature/*, fix/*, docs/*, chore/*
                  |
                  v  pull request + CI + revisión
               develop  (integración y rama predeterminada)
                  |
                  v  pull request de promoción + CI + revisión
                 main    (versión estable y publicación GHCR)
```

`develop` y `main` son las únicas ramas permanentes. Las ramas creadas por Dependabot son temporales y normales: cada una representa una propuesta automática de actualización y desaparece al cerrar o fusionar su pull request.

## Trabajo diario

1. Actualizar `develop` y crear una rama enfocada:

   ```bash
   git switch develop
   git pull --ff-only origin develop
   git switch -c feature/descripcion-corta
   ```

2. Implementar y verificar dentro de Docker:

   ```bash
   make verify
   ```

3. Registrar el cambio con Conventional Commits y publicarlo:

   ```bash
   git add .
   git commit -m "feat: descripcion breve"
   git push -u origin feature/descripcion-corta
   gh pr create --base develop --fill
   ```

4. Fusionar sólo después de CI verde, una aprobación y conversaciones resueltas. Se recomienda `Squash and merge` para las ramas de trabajo.

Prefijos admitidos:

- `feature/*`: funcionalidad nueva;
- `fix/*`: corrección;
- `docs/*`: documentación;
- `chore/*`: infraestructura, dependencias o mantenimiento;
- `hotfix/*`: corrección urgente que parte de `main`; después debe incorporarse también a `develop`.

## Promoción a una entrega

1. Confirmar que `develop` está estable y que `make verify` termina correctamente.
2. Abrir un pull request con base `main` y origen `develop`:

   ```bash
   gh pr create --base main --head develop \
     --title "release: version candidata" \
     --body "Promoción probada de develop a main."
   ```

3. Exigir CI verde, una aprobación y conversaciones resueltas.
4. Fusionar mediante un commit de merge para conservar la relación entre ambas ramas. La actualización de `main` activa CD y publica las cinco imágenes en GHCR.
5. Para una entrega formal, crear una etiqueta `vX.Y.Z` sobre el commit aprobado de `main`.

No se desarrollan funcionalidades directamente en `main` ni se fusiona una rama de trabajo saltándose `develop`.

## Protecciones en GitHub

`develop` y `main` tienen protección activa: impiden force-push y eliminación, exigen pull request, una aprobación, conversaciones resueltas y ocho controles de CI con la rama actualizada. La administración conserva una excepción únicamente para recuperación; cualquier uso debe justificarse en la bitácora.

CI se ejecuta sobre pull requests y pushes a ambas ramas. El control `Validate branch flow` acepta trabajo hacia `develop` y exige que toda promoción hacia `main` tenga origen `develop`. CD se ejecuta únicamente sobre `main` y etiquetas `v*`.

## Relación entre ramas y ambientes

Las ramas controlan el ciclo del código, no crean por sí solas servidores permanentes:

- un cambio de `feature/*` o `fix/*` se prueba mediante contenedores efímeros de CI;
- `develop` mantiene la integración candidata y puede ejecutarse localmente con `compose.yaml`;
- un pull request `develop -> main` vuelve a ejecutar CI;
- al fusionarse en `main`, CD publica cinco imágenes con etiquetas `main` y `sha-*`;
- una etiqueta `vX.Y.Z` publica una versión inmutable que puede fijarse en `.env.release`.

En una computadora pueden convivir el proyecto de desarrollo `bi-ia-prototype` y el proyecto de entrega `bi-ia-prototype-release`, porque usan redes, volúmenes y puertos anfitrión diferentes. La vista Nginx ligera (`make delivery-preview-up`) es una alternativa para probar sólo el frontend compilado sin duplicar las bases.

## Dependabot

Dependabot abre sus pull requests contra la rama predeterminada `develop`. Las actualizaciones npm menores y parches se agrupan; los saltos mayores de versión no se proponen como actualización rutinaria porque requieren revisar compatibilidad y migraciones. Las alertas de seguridad siguen tratándose por separado.

Un pull request automático se revisa igual que cualquier otro: no se fusiona si CI falla. Si un grupo mezcla versiones incompatibles, se cierra explicando la causa y se actualizan las reglas para que el problema no se repita.
