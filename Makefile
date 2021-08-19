up:
	docker-compose -f container-compose.yml up -d anitya-web anitya-librariesio-consumer
restart:
	docker-compose -f container-compose.yml restart
halt:
	docker-compose -f container-compose.yml down
bash-web:
	docker-compose -f container-compose.yml exec anitya-web bash -c "cat /app/ansible/roles/anitya-dev/files/motd; bash;"
bash-consumer:
	docker-compose -f container-compose.yml exec anitya-librariesio-consumer bash -c "cat /app/ansible/roles/anitya-dev/files/motd; bash;"
logs:
	docker-compose -f container-compose.yml logs -f
