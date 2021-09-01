define download_dump
	wget https://infrastructure.fedoraproject.org/infra/db-dumps/anitya.dump.xz -O ./.container/dump/anitya.dump.xz
endef

define remove_dump
	$(call compose) exec postgres \bash -c 'rm /dump/anitya.dump.xz'
endef

_CHECK_PODMAN := $(shell command -v podman 2> /dev/null)
define compose
	$(if $(_CHECK_PODMAN), podman-compose, docker-compose) -f container-compose.yml
endef

up:
	$(call compose) up -d anitya-web anitya-librariesio-consumer
restart:
	$(call compose) restart
halt:
	$(call compose) down
bash-web:
	$(call compose) exec anitya-web bash -c "cat /app/ansible/roles/anitya-dev/files/motd; bash;"
bash-consumer:
	$(call compose) exec anitya-librariesio-consumer bash -c "cat /app/ansible/roles/anitya-dev/files/motd; bash;"
logs:
	$(call compose) logs -f
init-db:
	$(call compose) exec anitya-web bash -c "python3 createdb.py"
dump-restore: init-db
	$(call download_dump)
	$(call compose) exec postgres \bash -c 'runuser -l postgres -c "createuser anitya" && xzcat /dump/anitya.dump.xz | runuser -l postgres -c "psql anitya"'
	$(call remove_dump)
