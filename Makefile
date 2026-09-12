.PHONY: help env bootstrap build up seed delivery-preview-up ollama-up ollama-pull ollama-status ollama-down release-up release-down down logs ps test lint format-check compose-check workflow-test doctor docs-image logbook sprint-report sprint2-report technical-manual docs verify

COMPOSE := docker compose

help:
	@echo "Comandos disponibles:"
	@echo "  make env            Crea .env desde .env.example si no existe"
	@echo "  make bootstrap      Prepara y levanta todo desde cero"
	@echo "  make build          Construye las imagenes de desarrollo"
	@echo "  make up             Levanta frontend y backend"
	@echo "  make seed           Aplica de forma idempotente el catálogo base aprobado"
	@echo "  make delivery-preview-up Anade Nginx en 8080 sin reemplazar desarrollo"
	@echo "  make ollama-up     Inicia Ollama local opcional, sin descargar modelo"
	@echo "  make ollama-pull   Descarga una vez el modelo local configurado"
	@echo "  make ollama-status Muestra los modelos locales descargados"
	@echo "  make ollama-down   Detiene Ollama y conserva sus modelos"
	@echo "  make release-up     Levanta un entorno GHCR completo y aislado"
	@echo "  make release-down   Detiene el entorno GHCR y conserva sus datos"
	@echo "  make down           Detiene los servicios"
	@echo "  make logs           Sigue los logs de los servicios"
	@echo "  make test           Ejecuta todas las pruebas dentro de Docker"
	@echo "  make lint           Ejecuta los analizadores dentro de Docker"
	@echo "  make compose-check  Valida la configuracion de Compose"
	@echo "  make workflow-test  Prueba la politica de ramas dentro de Docker"
	@echo "  make logbook        Regenera la bitacora PDF con LaTeX en Docker"
	@echo "  make sprint-report  Regenera el informe PDF del Sprint 1"
	@echo "  make sprint2-report Regenera el informe PDF del Sprint 2"
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

seed:
	$(COMPOSE) run --rm seed

delivery-preview-up:
	$(COMPOSE) --profile delivery build frontend-delivery
	$(COMPOSE) --profile delivery up --no-build -d frontend-delivery

ollama-up:
	$(COMPOSE) --profile local-llm up -d ollama

ollama-pull: ollama-up
	$(COMPOSE) --profile local-llm exec ollama ollama pull $${OLLAMA_MODEL:-qwen2.5:3b}

ollama-status:
	$(COMPOSE) --profile local-llm exec ollama ollama list

ollama-down:
	$(COMPOSE) --profile local-llm stop ollama

release-up:
	@test -f .env.release || { echo "Falta .env.release: copie .env.release.example y cambie los secretos."; exit 1; }
	$(COMPOSE) --env-file .env.release -f compose.release.yaml pull
	$(COMPOSE) --env-file .env.release -f compose.release.yaml up -d

release-down:
	@test -f .env.release || { echo "Falta .env.release."; exit 1; }
	$(COMPOSE) --env-file .env.release -f compose.release.yaml down

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
	$(COMPOSE) --profile delivery config --quiet
	$(COMPOSE) --profile local-llm config --quiet
	$(COMPOSE) --env-file .env.release.example -f compose.release.yaml config --quiet

workflow-test:
	docker run --rm -v "$$(pwd):/workspace:ro" -w /workspace alpine:3.22 \
		./scripts/test-branch-flow.sh

doctor:
	$(COMPOSE) ps
	@curl --fail --silent http://localhost:$${BACKEND_PORT:-8000}/api/v1/health/live || true
	@echo
	@curl --fail --silent http://localhost:$${FRONTEND_PORT:-5173} >/dev/null && echo "Frontend: disponible" || echo "Frontend: no disponible"
	@curl --fail --silent http://localhost:$${DELIVERY_FRONTEND_PORT:-8080} >/dev/null && echo "Frontend de entrega: disponible" || echo "Frontend de entrega: no iniciado"

docs-image:
	docker build --target production -t bi-ia-docs:local infra/docs

logbook: docs-image
	docker run --rm --user "$$(id -u):$$(id -g)" \
		-e HOME=/tmp -e TEXMFVAR=/tmp/texmf-var -e VARTEXFONTS=/tmp/texfonts \
		-v "$$(pwd)/docs/logbook:/workspace" -w /workspace \
		bi-ia-docs:local -pdf -interaction=nonstopmode -halt-on-error bitacora.tex

sprint-report: docs-image
	docker run --rm --user "$$(id -u):$$(id -g)" \
		-e HOME=/tmp -e TEXMFVAR=/tmp/texmf-var -e VARTEXFONTS=/tmp/texfonts \
		-v "$$(pwd)/docs:/workspace" -w /workspace/sprints \
		bi-ia-docs:local -pdf -interaction=nonstopmode -halt-on-error sprint-01-entorno.tex

sprint2-report: docs-image
	docker run --rm --user "$$(id -u):$$(id -g)" \
		-e HOME=/tmp -e TEXMFVAR=/tmp/texmf-var -e VARTEXFONTS=/tmp/texfonts \
		-v "$$(pwd)/docs:/workspace" -w /workspace/sprints \
		bi-ia-docs:local -pdf -interaction=nonstopmode -halt-on-error sprint-02-seguridad-y-parametros.tex

technical-manual: docs-image
	docker run --rm --user "$$(id -u):$$(id -g)" \
		-e HOME=/tmp -e TEXMFVAR=/tmp/texmf-var -e VARTEXFONTS=/tmp/texfonts \
		-v "$$(pwd)/docs:/workspace" -w /workspace/manual-tecnico \
		bi-ia-docs:local -pdf -interaction=nonstopmode -halt-on-error manual-tecnico.tex

docs: logbook sprint-report sprint2-report technical-manual

verify: compose-check workflow-test test docs
