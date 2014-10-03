%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           anitya
Version:        0.1.3
Release:        1%{?dist}
Summary:        Monitor upstream releases and announce them on fedmsg

License:        GPLv2+
URL:            http://fedorahosted.org/anitya/
Source0:        https://fedorahosted.org/releases/a/n/anitya/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python-flask
BuildRequires:  python-flask-wtf
BuildRequires:  python-flask-openid
BuildRequires:  python-wtforms
BuildRequires:  python-openid
BuildRequires:  python-docutils
BuildRequires:  python-dateutil
BuildRequires:  python-markupsafe
BuildRequires:  python-bunch
BuildRequires:  python-straight-plugin
BuildRequires:  python-setuptools
BuildRequires:  fedmsg

# EPEL6
%if ( 0%{?rhel} && 0%{?rhel} == 6 )
BuildRequires:  python-sqlalchemy0.8
Requires:  python-sqlalchemy0.8
%else
BuildRequires:  python-sqlalchemy > 0.8
Requires:  python-sqlalchemy > 0.8
%endif

Requires:  python-flask
Requires:  python-flask-wtf
Requires:  python-flask-openid
Requires:  python-wtforms
Requires:  python-openid
Requires:  python-docutils
Requires:  python-dateutil
Requires:  python-markupsafe
Requires:  python-bunch
Requires:  python-straight-plugin
Requires:  python-setuptools
Requires:  mod_wsgi
Requires:  fedmsg

%description
We monitor upstream releases and broadcast them on fedmsg, the FEDerated MeSsaGe
(fedmsg) bus.

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Install apache configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/
install -m 644 files/anitya.conf \
    $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/anitya.conf

# Install configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/anitya
install -m 644 files/anitya.cfg.sample \
    $RPM_BUILD_ROOT/%{_sysconfdir}/anitya/anitya.cfg

mkdir -p $RPM_BUILD_ROOT/%{_datadir}/anitya

# Install WSGI file
install -m 644 files/anitya.wsgi $RPM_BUILD_ROOT/%{_datadir}/anitya/anitya.wsgi

# Install the createdb script
install -m 644 createdb.py $RPM_BUILD_ROOT/%{_datadir}/anitya/anitya_createdb.py

# Install the migrate_wiki script
install -m 644 files/migrate_wiki.py $RPM_BUILD_ROOT/%{_datadir}/anitya/anitya_migrate_wiki.py

# Install the cron script
install -m 644 files/anitya_cron.py $RPM_BUILD_ROOT/%{_datadir}/anitya/anitya_cron.py

# Install the alembic files
#cp -r alembic $RPM_BUILD_ROOT/%{_datadir}/anitya/
#install -m 644 files/alembic.ini $RPM_BUILD_ROOT/%{_sysconfdir}/anitya/alembic.ini

## Running the tests would require having flask >= 0.10 which is not present in
## epel6
#%check
#./runtests.sh

%files
%doc README.rst LICENSE
%config(noreplace) %{_sysconfdir}/httpd/conf.d/anitya.conf
%config(noreplace) %{_sysconfdir}/anitya/anitya.cfg
#config(noreplace) %{_sysconfdir}/anitya/alembic.ini
%dir %{_sysconfdir}/anitya/
%{_datadir}/anitya/
%{python_sitelib}/anitya/
%{python_sitelib}/%{name}*.egg-info
%{_bindir}/anitya_cron.py


%changelog
* Fri Oct 03 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.3-1
- Update to 0.1.3
- Fix mapping a project onto an existing distribution

* Fri Oct 03 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.2-1
- Update to 0.1.2
- Fix redirection after logging in
- Fix redirection after logging out
- Set the redirection on the log out button
- Instanciate fedmsg correctly (thanks to Ralph Bean)
- Drop the recorded versions from the DB when dropping a project

* Thu Oct 02 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.1-1
- Update to 0.1.1
- Include the project id in its project representation
- Grammar fixes
- Specify on which server is the IRC channel for feedbacks

* Wed Oct 01 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-3
- Install the cron script

* Wed Oct 01 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-2
- Install the migrate_wiki script

* Mon Sep 29 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-1
- Initial packaging work for Fedora
