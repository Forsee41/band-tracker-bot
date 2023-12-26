-include .env

.PHONY: check
check: --flake8 --pyright --mypy --debug-marks
	@echo "All checks passed"

.PHONY: test
test: --test-db
	python -m pytest -vv --asyncio-mode=auto -m "not slow"

.PHONY: fulltest
fulltest: --test-db
	python -m pytest -vv --asyncio-mode=auto

.PHONY: prepare
prepare:
	$(eval CONTAINER_ID=$(shell docker ps -a -q -f name=band_tracker_db))
	if [ -z "$(CONTAINER_ID)" ]; then \
		docker compose -f docker-compose-dev.yaml up -d &> /dev/null; \
		echo "Waiting for containers to spawn"; \
		sleep 1.5; \
		$(MAKE) migrations; \
		$(MAKE) load_dump; \
	else \
		echo "Shutting down containers"; \
		docker compose -f docker-compose-dev.yaml down &> /dev/null; \
		echo "Waiting for containers to spawn"; \
		docker compose -f docker-compose-dev.yaml up -d &> /dev/null; \
		sleep 1.5; \
		$(MAKE) migrations; \
		$(MAKE) load_dump; \
	fi 

.PHONY: down
down:
	docker compose -f docker-compose-dev.yaml down &> /dev/null

.PHONY: up
up:
	docker compose -f docker-compose-dev.yaml up -d &> /dev/null

.PHONY: dump
dump:
	$(eval CONTAINER_ID=$(shell docker ps -a | grep -w db | awk '{print $$1}'))
	if [ -z "$(CONTAINER_ID)" ]; then \
		echo "No container found."; \
	else \
		docker exec -t $(CONTAINER_ID) pg_dump -U postgres -d postgres > db.sql; \
		mv db.sql $(CURDIR)/dump.sql; \
		echo "Database dump created"; \
	fi

.PHONY: load_dump
load_dump:
	PGPASSWORD=$(DB_PASSWORD) psql -p $(DB_PORT) -U $(DB_LOGIN) -h $(DB_IP) -d $(DB_NAME) -f dump.sql -a

.PHONY: psql
psql:
	PGPASSWORD=$(DB_PASSWORD) psql -p $(DB_PORT) -U $(DB_LOGIN) -h $(DB_IP) -d $(DB_NAME)

.PHONY: bot
bot:
	python bot.py 2>&1 | tee .log 


pre-commit: fulltest check

debug: --test-db
	python -m pytest -vv --asyncio-mode=auto -m debug

rm_git-lock:
	rm -f .git/index.lock

migrations:
	alembic upgrade head

--flake8:
	flake8 band_tracker tests --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 band_tracker tests --count --max-complexity=10 --max-line-length=88 --statistics

--pyright:
	pyright band_tracker tests

--mypy:
	mypy band_tracker tests


--debug-marks:
	@if grep -r --include=\*.py "@pytest.mark.debug" tests; then \
		echo "Debug mark found in tests. Debug marks are not allowed in prs."; \
		echo "Use 'make debug' command to check which tests have debug mark."; \
		exit 1; \
	fi; \

--test-db:
	$(eval CONTAINER_ID=$(shell docker ps -a -q -f name=band_tracker_test_db))
	if [ -z "$(CONTAINER_ID)" ]; then \
		echo "Waiting for containers to spawn"; \
		docker compose -f docker-compose-dev.yaml up -d &> /dev/null; \
		sleep 1.5; \
	fi; \
