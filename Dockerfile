FROM fedora:32

COPY . /app
WORKDIR /app

RUN dnf install -y ansible
# Reuse Ansible playbooks for installing packages
RUN ansible-playbook ansible/docker-playbook.yml --tags packages,install
RUN dnf autoremove -y && \
    dnf clean all -y


RUN mkdir /etc/anitya
RUN chmod +x /app/files/docker.sh

EXPOSE 80
ENTRYPOINT /app/files/docker.sh
