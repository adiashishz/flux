COMPOSE = docker compose -f docker/docker-compose.yml --env-file docker/.env

.PHONY: up down dev backend-start worker test eval logs shell makemigrations migrate

## Start everything (builds if needed, migrations run automatically)
up:
	$(COMPOSE) up -d --build

## Stop all containers
down:
	$(COMPOSE) down

## Dev mode — start only the database and Redis
dev:
	$(COMPOSE) up -d db redis

## Start the Celery worker locally (requires make dev first)
worker:
	cd backend && uv run celery -A config worker --loglevel=info --concurrency=2

## Run the backend test suite (requires make dev first)
test:
	cd backend && uv run pytest

## Measure search quality (add ARGS=--live to also score tool calling against the Anthropic API)
eval:
	cd backend && uv run python manage.py run_evals $(ARGS)

## Start backend dev server (requires make dev first)
backend-start:
	cd backend && uv run python manage.py runserver 7000


## Tail logs (all services, or pass s=backend/frontend/db)
logs:
	$(COMPOSE) logs -f $(s)

## Open a Django shell inside the backend container
shell:
	$(COMPOSE) exec backend python manage.py shell

## Generate migration files from model changes (runs locally)
makemigrations:
	cd backend && uv run python manage.py makemigrations

## Apply migrations (containers must be up)
migrate:
	$(COMPOSE) exec backend python manage.py migrate
