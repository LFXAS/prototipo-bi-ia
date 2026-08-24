.PHONY: help env bootstrap build up release-up down logs ps test lint format-check compose-check doctor docs-image logbook sprint-report technical-manual docs verify

COMPOSE := docker compose

help:
	@echo "Comandos disponibles:"
	@echo "  make env            Crea .env desde .env.example si no existe"
	@echo "  make bootstrap      Prepara y levanta todo desde cero"
	@echo "  make build          Construye las imagenes de desarrollo"
	@echo "  make up             Levanta frontend y backend"
	@echo "  make release-up     Levanta imagenes ya publicadas en GHCR"
	@echo "  make down           Detiene los servicios"
	@echo "  make logs           Sigue los logs de los servicios"
	@echo "  make test           Ejecuta todas las pruebas dentro de Docker"
	@echo "  make lint           Ejecuta los analizadores dentro de Docker"
	@echo "  make compose-check  Valida la configuracion de Compose"
	@echo "  make logbook        Regenera la bitacora PDF con LaTeX en Docker"
	@echo "  make sprint-report  Regenera el informe PDF del Sprint 1"
	@echo "  make technical-manual Regenera el manual tecnico PDF"
	@echo "  make docs           Regenera todos los documentos PDF"
	@echo "  make doctor         Muestra estado de contenedores y endpoints"
	@echo "  make verify         Ejecuta toda la validacion local automatizada"

env:
	@test -f .env || cp .env.example .env

bootstrap:
	./scripts/bootstrap.sh

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up --build -d

release-up:
	$(COMPOSE) -f compose.release.yaml pull
	$(COMPOSE) -f compose.release.yaml up -d

down:
	$(COMPOSE) down --remove-orphans

logs:
	$(COMPOSE) logs -f --tail=100

ps:
	$(COMPOSE) ps

test:
	docker build --target test -t bi-ia-backend:test backend
	docker build --target test -t bi-ia-frontend:test frontend

lint:
	$(COMPOSE) run --build --rm backend ruff check .
	$(COMPOSE) run --build --rm backend mypy app
	$(COMPOSE) run --build --rm frontend npm run lint

format-check:
	$(COMPOSE) run --build --rm backend ruff format --check .

compose-check:
	$(COMPOSE) config --quiet
	$(COMPOSE) -f compose.release.yaml config --quiet

doctor:
	$(COMPOSE) ps
	@curl --fail --silent http://localhost:$${BACKEND_PORT:-8000}/api/v1/health/live || true
	@echo
	@curl --fail --silent http://localhost:$${FRONTEND_PORT:-5173} >/dev/null && echo "Frontend: disponible" || echo "Frontend: no disponible"

docs-image:
	docker build --target production -t bi-ia-docs:local infra/docs

logbook: docs-image
	docker run --rm --user "$$(id -u):$$(id -g)" \
		-v "$$(pwd)/docs/logbook:/workspace" -w /workspace \
		bi-ia-docs:local -pdf -interaction=nonstopmode -halt-on-error bitacora.tex

sprint-report: docs-image
	docker run --rm --user "$$(id -u):$$(id -g)" \
		-v "$$(pwd)/docs:/workspace" -w /workspace/sprints \
		bi-ia-docs:local -pdf -interaction=nonstopmode -halt-on-error sprint-01-entorno.tex

technical-manual: docs-image
	docker run --rm --user "$$(id -u):$$(id -g)" \
		-v "$$(pwd)/docs:/workspace" -w /workspace/manual-tecnico \
		bi-ia-docs:local -pdf -interaction=nonstopmode -halt-on-error manual-tecnico.tex

docs: logbook sprint-report technical-manual

verify: compose-check test docs
