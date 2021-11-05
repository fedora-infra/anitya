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
	$(call container-tool) exec -it postgres \bash -c 'rm /dump/anitya.dump.xz'
endef

up:
	$(call compose-tool) up -d
	sleep 3
ifneq ($(wildcard .container/postgresql/data/.*),)
	@echo "Database files are already exists, so they will be used."
else
	@echo "No database files exists, db initialization started."
	$(MAKE) init-db
endif
restart:
	$(MAKE) halt && $(MAKE) up
halt:
	$(call compose-tool) down -t1
bash-web:
	$(call container-tool) exec -it anitya-web bash -c "cat /app/.container/web/motd; bash;"
bash-consumer:
	$(call container-tool) exec -it anitya-librariesio-consumer bash -c "cat /app/.container/consumer/motd; bash;"
init-db:
	$(call container-tool) exec -it anitya-web bash -c "python3 createdb.py"
dump-restore: init-db
	$(call download_dump)
	$(call container-tool) exec -it postgres \bash -c 'runuser -l postgres -c "createuser anitya" && xzcat /dump/anitya.dump.xz | runuser -l postgres -c "psql anitya"'
	$(call remove_dump)
logs:
	$(call container-tool) logs -f anitya-web anitya-librariesio-consumer rabbitmq postgres

.PHONY: up restart halt bash-web bash-consumer \
	init-db dump-restore logs
