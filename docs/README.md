# Índice de documentación técnica

La documentación forma parte del producto versionado. Las fuentes Markdown y LaTeX se revisan mediante pull request; los tres PDF oficiales se regeneran dentro de Docker y CI comprueba que coincidan con sus fuentes.

## Entregables oficiales del Sprint 1

- [`manual-tecnico/manual-tecnico.pdf`](manual-tecnico/manual-tecnico.pdf): instalación, operación, reconstrucción y explicación detallada del ciclo Docker, Git y CI/CD.
- [`sprints/sprint-01-entorno.pdf`](sprints/sprint-01-entorno.pdf): objetivo, backlog, ejecución, trazabilidad, evidencias, incidentes, revisión y retrospectiva del Sprint 1.
- [`logbook/bitacora.pdf`](logbook/bitacora.pdf): registro cronológico de decisiones, cambios, verificaciones, incidentes y pendientes.

Las fuentes editables se encuentran junto a cada PDF. `referencia-devops-sprint1.tex` y `detalle-tecnico-sprint-01.tex` son capítulos incluidos desde los documentos principales para mantener legible su estructura.

## Documentos de gobierno y diseño

- [`scope.md`](scope.md): alcance técnico vigente y exclusiones.
- [`architecture.md`](architecture.md): contenedores, ambientes, módulos y reglas arquitectónicas.
- [`decisions/`](decisions/): decisiones duraderas de arquitectura (ADR), incluido el catálogo inicial de proveedores LLM configurables.
- [`git-workflow.md`](git-workflow.md): ramas, PR, protecciones, revisión y promoción.
- [`replication-guide.md`](replication-guide.md): comandos de instalación y réplica.
- [`sdd-workflow.md`](sdd-workflow.md) y [`specs/`](specs/README.md): proceso y contratos SDD desde el Sprint 2.

## Regeneración y verificación

Desde la raíz del repositorio:

```bash
make docs
make verify
```

`make docs` compila los tres PDF con la imagen LaTeX del proyecto. `make verify` agrega validación Compose, política de ramas y pruebas de frontend/backend. Un cambio documental no se considera terminado hasta que las fuentes y los PDF estén actualizados y legibles.

## Separación de material externo

Los manuales docentes genéricos o anónimos no pertenecen a este repositorio público. Deben mantenerse en una ubicación independiente para evitar asociar materiales de clase con las estudiantes, cuentas o detalles del prototipo.
