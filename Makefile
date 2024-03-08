.SILENT:

_CHECK_PODMAN := $(shell command -v podman 2> /dev/null)
define compose-tool
	$(if $(_CHECK_PODMAN), podman-compose, docker-compose) -f container-compose.yml
endef

define container-tool
	$(if $(_CHECK_PODMAN), podman, docker)
endef

define download_dump
	wget https://infrastructure.fedoraproject.org/infra/db-dumps/anitya.dump.xz -O ./.container/dump/anitya.dump.xz
endef

define remove_dump
	rm -f .container/dump/anitya.dump.xz
endef

up:
	$(call compose-tool) up -d
# It takes some time before the postgres container is up, we need to wait before calling
# the next step
	sleep 10
	$(MAKE) init-db
	@echo "Empty database initialized. Run dump-restore to fill it by production dump."
restart:
	$(MAKE) halt && $(MAKE) up
halt:
	$(call compose-tool) down -t1
bash-web:
	$(call container-tool) exec -it anitya-web bash -c "cat /app/.container/web/motd; bash;"
init-db:
	$(call container-tool) exec -it anitya-web bash -c "python3 createdb.py"
dump-restore: init-db
	$(call download_dump)
	$(call container-tool) exec -it postgres bash -c 'createuser anitya && xzcat /dump/anitya.dump.xz | psql anitya'
	$(call remove_dump)
logs:
	$(call container-tool) logs -f anitya-web rabbitmq postgres
clean: halt
	$(call container-tool) rmi "localhost/anitya-base:latest" "docker.io/library/postgres:13.4" "docker.io/library/rabbitmq:3.8.16-management-alpine"

.PHONY: up restart halt bash-web \
	init-db dump-restore logs clean
