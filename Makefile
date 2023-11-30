check:
	flake8 band_tracker tests --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 band_tracker tests --count --max-complexity=10 --max-line-length=88 --statistics
	pyright band_tracker tests
	mypy band_tracker tests
	echo "All checks passed"

test:
	$(eval CONTAINER_ID=$(shell docker ps -a -q -f name=test_db))
	if [ -z "$(CONTAINER_ID)" ]; then \
		echo "Waiting for containers to spawn"; \
		docker compose -f docker-compose-dev.yaml up -d &> /dev/null; \
		sleep 1.5; \
	fi
	python -m pytest -vv --asyncio-mode=auto -m "not slow"

fulltest:
	$(eval CONTAINER_ID=$(shell docker ps -a -q -f name=test_db))
	if [ -z "$(CONTAINER_ID)" ]; then \
		echo "Waiting for containers to spawn"; \
		docker compose -f docker-compose-dev.yaml up -d &> /dev/null; \
		sleep 1.5; \
	fi
	python -m pytest -vv --asyncio-mode=auto

prepare:
	$(eval CONTAINER_ID=$(shell docker ps -a -q -f name=db))
	if [ -z "$(CONTAINER_ID)" ]; then \
		docker compose -f docker-compose-dev.yaml up -d &> /dev/null; \
		echo "Waiting for containers to spawn"; \
		sleep 1.5; \
		alembic upgrade head; \
		make load_dump; \
	else \
		echo "Shutting down containers"; \
		docker compose -f docker-compose-dev.yaml down &> /dev/null; \
		echo "Waiting for containers to spawn"; \
		docker compose -f docker-compose-dev.yaml up -d &> /dev/null; \
		sleep 1.5; \
		alembic upgrade head; \
		make load_dump; \
	fi 

down:
	docker compose -f docker-compose-dev.yaml down &> /dev/null

up:
	docker compose -f docker-compose-dev.yaml up -d &> /dev/null

dump:
	$(eval CONTAINER_ID=$(shell docker ps -a | grep -w db | awk '{print $$1}'))
	if [ -z "$(CONTAINER_ID)" ]; then \
		echo "No container found."; \
	else \
		docker exec -t $(CONTAINER_ID) pg_dump -U postgres -d postgres > db.sql; \
		mv db.sql $(CURDIR)/dump.sql; \
		echo "Database dump created"; \
	fi

load_dump:
	PGPASSWORD='postgres' psql -p 5432 -U postgres -h localhost -d postgres -f dump.sql -a

psql:
	PGPASSWORD='postgres' psql -p 5432 -U postgres -h localhost -d postgres

bot:
	python bot.py 2>&1 | tee .log 

pre-commit:
	make test
	make check

debug:
	$(eval CONTAINER_ID=$(shell docker ps -a -q -f name=test_db))
	if [ -z "$(CONTAINER_ID)" ]; then \
		docker compose -f docker-compose-dev.yaml up -d &> /dev/null; \
		echo "Waiting for containers to spawn"; \
		sleep 1.5; \
	fi
	python -m pytest -vv --asyncio-mode=auto -m debug
