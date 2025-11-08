COMPOSE_FILE = docker-compose.yml

.PHONY: setup up migrate seed

# Full first-time setup (build + up + migrate)
setup:
	docker compose -f $(COMPOSE_FILE) down -v
	docker compose -f $(COMPOSE_FILE) up -d --build
	
	docker compose exec web flask db downgrade base
	docker compose exec web flask db upgrade
	
	docker compose exec web python seed_redis.py
	@echo "✅ setup complete!"

loadtest:
	docker compose run --rm k6