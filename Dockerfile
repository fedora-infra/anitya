FROM fedora
# cffi>=1.1.0->cryptography->fedmsg->-r
RUN dnf install -y gcc python-devel libffi-devel openssl-devel gcc-c++ redhat-rpm-config rpm-python && \
    dnf autoremove -y && \
    dnf clean all -y

COPY ./ /src
WORKDIR /src

RUN pip install --user -r requirements.txt
RUN python createdb.py
EXPOSE 5000
ENTRYPOINT python runserver.py --host '0.0.0.0'

