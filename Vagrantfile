# -*- mode: ruby -*-
# vi: set ft=ruby :

$script = <<SCRIPT
    dnf install -y \
        python-flask \
        python-flask-wtf \
        python-flask-openid \
        python-wtforms \
        python-openid \
        python-docutils \
        python-dateutil \
        python-markupsafe \
        python-bunch \
        python-straight-plugin \
        python-setuptools \
        python-sqlalchemy \
        fedmsg
    cd /opt/anitya/src/ && python createdb.py
SCRIPT

Vagrant.configure("2") do |config|
  config.vm.box = "boxcutter/fedora24"
  config.vm.synced_folder "./", "/opt/anitya/src"
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.provision "shell", inline: $script
  config.vm.provision :shell, inline: "python /opt/anitya/src/runserver.py --host '0.0.0.0' --port 80 &", run: "always"
end
