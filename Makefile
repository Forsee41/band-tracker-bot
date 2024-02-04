-include .env

MAKEFLAGS += --no-print-directory

OBJS = band_tracker tests updater.py bot.py notifier.py

.PHONY: check
check: check-flake8 check-pyright check-mypy check-debug-marks
	@echo "All checks passed"

.PHONY: test
test: --test-db
	python -m pytest -vv --asyncio-mode=auto -m "not slow"

.PHONY: fulltest
fulltest: --test-db
	python -m pytest -vv --asyncio-mode=auto

.PHONY: prepare
prepare: --db-down --db migrations load_dump
	@echo "Database is ready"

.PHONY: dump
dump:
	$(eval CONTAINER_ID=$(shell docker ps -a | grep -w band_tracker_db | awk '{print $$1}'))
	@if [ -z "$(CONTAINER_ID)" ]; then \
		echo "No container found."; \
	else \
		docker exec -t $(CONTAINER_ID) pg_dump -U postgres -d postgres > db.sql; \
		mv db.sql $(CURDIR)/dump.sql; \
		echo "Database dump created"; \
	fi

.PHONY: load_dump
load_dump: --db
	@echo "Loading dump..."
	@PGPASSWORD=$(DB_PASSWORD) psql -p $(DB_PORT) -U $(DB_LOGIN) -h $(DB_IP) -d $(DB_NAME) -f dump.sql -a > /dev/null 2>&1

.PHONY: psql
psql: --db
	@PGPASSWORD=$(DB_PASSWORD) psql -p $(DB_PORT) -U $(DB_LOGIN) -h $(DB_IP) -d $(DB_NAME)

.PHONY: bot
bot:
	@python bot.py 2>&1 | tee .log 


.PHONY: pre-commit
pre-commit: fulltest check

.PHONY: debug
debug: --test-db
	python -m pytest -vv --asyncio-mode=auto -m debug

.PHONY: revision 
revision: --db-down --db migrations
	@echo "Database is ready for a new revision."
	@echo "Use the following command to autogenerate a new revision:"
	@echo
	@echo "alembic revision --autogenerate -m \"revision_name\""

.PHONY: rm_git-lock 
rm_git-lock:
	rm -f .git/index.lock

.PHONY: migrations 
migrations: --db
	@echo "Applying migrations..."
	@alembic upgrade head > /dev/null 2>&1

.PHONY: check-flake8 
check-flake8:
	flake8 $(OBJS) --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 $(OBJS) --count --max-complexity=10 --max-line-length=120 --statistics

.PHONY: check-pyright 
check-pyright:
	pyright $(OBJS) 

.PHONY: check-mypy
check-mypy:
	mypy $(OBJS) 

.PHONY: check-debug-marks 
check-debug-marks:
	@if grep -r --include=\*.py "@pytest.mark.debug" tests; then \
		echo "Debug mark found in tests. Debug marks are not allowed in prs."; \
		echo "Use 'make debug' command to check which tests have debug mark."; \
		exit 1; \
	fi;

.PHONY: down
down:
	docker compose -f docker-compose-dev.yaml down &> /dev/null

.PHONY: up
up:
	docker compose -f docker-compose-dev.yaml up -d &> /dev/null

.PHONY: clean
clean: --test-db-down --db-down --rabbit-down

--rabbit:
	$(eval CONTAINER_ID=$(shell docker ps -q -f name=band_tracker_rabbitmq))
	@if [ -z "$(CONTAINER_ID)" ]; then \
		echo "Spawning RabbitMQ..." \
		docker compose -f docker-compose-dev.yaml up band_tracker_rabbitmq -d &> /dev/null; \
		sleep 1.5; \
	fi;

--rabbit-down:
	$(eval CONTAINER_ID=$(shell docker ps -q -f name=band_tracker_rabbitmq))
	@if [ -z "$(CONTAINER_ID)" ]; then \
		echo "Killing RabbitMQ..." \
		docker compose -f docker-compose-dev.yaml up band_tracker_rabbitmq &> /dev/null; \
		sleep 1.5; \
	fi;

--test-db:
	$(eval CONTAINER_ID=$(shell docker ps -q -f name=band_tracker_test_db))
	@if [ -z "$(CONTAINER_ID)" ]; then \
		echo "Spawning Test DB..."; \
		docker compose -f docker-compose-dev.yaml up band_tracker_test_db -d &> /dev/null; \
		sleep 1.5; \
	fi;

--test-db-down:
	$(eval CONTAINER_ID=$(shell docker ps -q -f name=band_tracker_test_db))
	@if [ "$(CONTAINER_ID)" ]; then \
		echo "Killing Test DB..."; \
		docker compose -f docker-compose-dev.yaml down band_tracker_test_db &> /dev/null; \
	fi;

--db:
	$(eval CONTAINER_ID=$(shell docker ps -q -f name=band_tracker_db))
	@if [ -z "$(CONTAINER_ID)" ]; then \
		echo "Spawning DB..."; \
		docker compose -f docker-compose-dev.yaml up band_tracker_db -d &> /dev/null; \
		sleep 1.5; \
	fi;

--db-down:
	$(eval CONTAINER_ID=$(shell docker ps -q -f name=band_tracker_db))
	@if [ "$(CONTAINER_ID)" ]; then \
		echo "Killing DB..."; \
		docker compose -f docker-compose-dev.yaml down band_tracker_db &> /dev/null; \
	fi;
