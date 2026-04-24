.PHONY: up down test backend-test frontend-install

up:
	docker compose up --build

down:
	docker compose down -v

test:
	docker compose run --rm backend pytest

backend-test:
	cd backend && pytest

frontend-install:
	cd frontend && npm install
