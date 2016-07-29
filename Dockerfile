FROM fedora
# cffi>=1.1.0->cryptography->fedmsg->-r
RUN dnf install -y gcc python-devel libffi-devel openssl-devel git gcc-c++ redhat-rpm-config

RUN git clone https://github.com/fedora-infra/anitya.git /src
WORKDIR /src

# in Fedora we have ancient cffi atm
# RUN dnf install -y python-cffi
RUN pip install --user -r requirements.txt
RUN python createdb.py
EXPOSE 5000
CMD ./runserver.py
