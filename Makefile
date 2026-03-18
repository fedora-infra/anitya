.SILENT:

_CHECK_PODMAN := $(shell command -v podman 2> /dev/null)
define compose-tool
	$(if $(_CHECK_PODMAN), podman-compose, docker-compose) -f container-compose.yml
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
	$(call compose-tool) up -d
# Wait till the anitya-web container is ready
	@until $(call container-tool) healthcheck run anitya-web >/dev/null 2>&1; do \
		printf '.'; \
		sleep 1; \
	done
	@echo ""
	$(MAKE) init-db
	@echo "Empty database initialized. Run dump-restore to fill it by production dump."
restart:
	$(MAKE) halt && $(MAKE) up
halt:
	$(call compose-tool) stop
bash-web:
	$(call container-tool) exec -it anitya-web bash -c "bash"
bash-check:
	$(call container-tool) exec -it anitya-check-service bash -c "bash"
init-db:
	$(call container-tool) exec -it anitya-web bash -c "poetry run python3 createdb.py"
dump-restore: init-db
	$(call download_dump)
# Anitya containers need to be stopped before doing dump restore
	$(call container-tool) stop anitya-check-service anitya-web
	$(call container-tool) exec -it postgres bash -c 'createuser anitya && xzcat /dump/anitya.dump.xz | psql anitya'
	$(MAKE) up
logs:
	$(call container-tool) logs -f anitya-web anitya-check-service rabbitmq postgres
clean:
	$(call compose-tool) down
	$(call remove_dump)
	$(call container-tool) rmi "localhost/anitya-base:latest" "docker.io/library/postgres:16.13" "docker.io/library/rabbitmq:3.8.16-management-alpine"
tests:
	$(call container-tool) exec -it anitya-web bash -c "tox $(PARAM)"

.PHONY: up restart halt bash-web \
	init-db dump-restore logs clean tests
