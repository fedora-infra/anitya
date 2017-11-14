FROM fedora
FROM fedora:24
ENV ANITYA_WEB_CONFIG /etc/anitya/config.py
# Updating libnghttp2 is required in Fedora 24
RUN dnf update -y libnghttp2 && \
    dnf install -y \
        python-flask \
        python-flask-wtf \
        python-wtforms \
        python-dateutil \
        python-straight-plugin \
        python-setuptools \
        python-sqlalchemy \
        python-psycopg2 \
        python-mysql \
        fedmsg \
        httpd \
        mod_wsgi && \
    dnf autoremove -y && \
    dnf clean all -y

COPY ./ /opt/anitya/src
WORKDIR /opt/anitya/src

RUN mkdir /etc/anitya
RUN rm -f /etc/httpd/conf.d/welcome.conf
RUN cp /opt/anitya/src/files/docker_apache.conf /etc/httpd/conf.d/anitya.conf
RUN chown -R apache:apache /opt/anitya
RUN chmod +x /opt/anitya/src/files/docker.sh

EXPOSE 80
ENTRYPOINT /opt/anitya/src/files/docker.sh
