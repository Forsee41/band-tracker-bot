check:
	flake8 band_tracker tests --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 band_tracker tests --count --max-complexity=10 --max-line-length=88 --statistics
	pyright band_tracker tests
	echo "All checks passed"

test:
	$(eval CONTAINER_ID=$(shell docker ps -a -q -f name=test_db))
	if [ -z "$(CONTAINER_ID)" ]; then \
		docker compose -f docker-compose-dev.yaml up -d &> /dev/null; \
		echo "Waiting for containers to spawn"; \
		sleep 1.5; \
	fi
	python -m pytest --asyncio-mode=auto

down:
	docker compose -f docker-compose-dev.yaml down &> /dev/null

