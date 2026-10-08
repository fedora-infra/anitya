.SILENT:

_CHECK_PODMAN := $(shell command -v podman 2> /dev/null)
define compose-tool
	PODMAN_COMPOSE_WARNING_LOGS=false $(if $(_CHECK_PODMAN), podman compose, docker compose) -f container-compose.yml
endef

define container-tool
	$(if $(_CHECK_PODMAN), podman, docker)
endef

define download_dump
	wget -P ./.container/dump/ -nc https://infrastructure.fedoraproject.org/infra/db-dumps/anitya.dump.xz
endef

define remove_dump
	rm -f .container/dump/anitya.dump.xz
endef

up:
	mkdir -p ./.container/dump/
	$(call compose-tool) up -d --wait
	$(MAKE) init-db
	@echo "Empty database initialized. Run dump-restore to fill it by production dump."
restart:
	$(MAKE) halt && $(MAKE) up
build:
	$(call compose-tool) build
halt:
	$(call compose-tool) stop
bash-web:
	$(call container-tool) exec -it anitya-web bash -c "bash"
bash-check:
	$(call container-tool) exec -it anitya-check-service bash -c "bash"
init-db:
	$(call container-tool) exec -it anitya-web bash -c "poetry run python3 createdb.py"
dump-restore:
	$(call download_dump)
# Anitya containers need to be stopped before doing dump restore
	$(call container-tool) stop anitya-check-service anitya-web
	$(call container-tool) exec -it postgres bash -c "dropdb --if-exists anitya; createuser anitya 2>/dev/null || true; xzcat /dump/anitya.dump.xz | psql -U postgres"
	$(call container-tool) start anitya-web anitya-check-service
logs:
	$(call compose-tool) logs -f anitya-web anitya-check-service rabbitmq postgres
clean:
	$(call compose-tool) down -v
	$(call remove_dump)
	$(call container-tool) rmi "anitya-base:latest" "localhost/anitya-base:latest" "docker.io/library/postgres:16.13" "docker.io/library/rabbitmq:3.8.16-management-alpine" 2>/dev/null || true
	rm -rf .coverage coverage.xml htmlcov .pytest_cache
tests:
	$(call container-tool) exec -it anitya-web bash -c "ANITYA_WEB_CONFIG= poetry run pytest $(PARAM)"
lint:
	$(call container-tool) exec -it anitya-web bash -c "poetry run flake8 anitya/ $(PARAM)"
format:
	$(call container-tool) exec -it anitya-web bash -c "poetry run black --check --diff $${PARAM:-anitya/}"
mypy:
	$(call container-tool) exec -it anitya-web bash -c "poetry run mypy --config-file mypy.cfg anitya $(PARAM)"
diff-cover:
	$(call container-tool) exec -it anitya-web bash -c "poetry run diff-cover coverage.xml --compare-branch=origin/master --exclude debug.py --fail-under=100 $(PARAM)"
tox:
	$(call container-tool) exec -it anitya-web bash -c "tox $(PARAM)"

.PHONY: up restart build halt bash-web \
	init-db dump-restore logs clean tests \
	lint format mypy diff-cover tox
