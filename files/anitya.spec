%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           anitya
Version:        0.3.0
Release:        2%{?dist}
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
BuildRequires:  python-sqlalchemy > 0.7
Requires:  python-sqlalchemy > 0.7
%endif

Requires:  python-alembic
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
install -m 755 files/anitya_cron.py $RPM_BUILD_ROOT/%{_datadir}/anitya/anitya_cron.py

# Install the alembic files
cp -r alembic $RPM_BUILD_ROOT/%{_datadir}/anitya/
install -m 644 files/alembic.ini $RPM_BUILD_ROOT/%{_sysconfdir}/anitya/alembic.ini

## Running the tests would require having flask >= 0.10 which is not present in
## epel6
#%check
#./runtests.sh

%files
%doc README.rst LICENSE
%config(noreplace) %{_sysconfdir}/httpd/conf.d/anitya.conf
%config(noreplace) %{_sysconfdir}/anitya/anitya.cfg
%config(noreplace) %{_sysconfdir}/anitya/alembic.ini
%dir %{_sysconfdir}/anitya/
%{_datadir}/anitya/
%{python_sitelib}/anitya/
%{python_sitelib}/%{name}*.egg-info
%{_bindir}/anitya_cron.py


%changelog
* Tue Mar 31 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.3.0-2
- Fix changelog of version 0.3.0-1
- Include and install the alembic files

* Tue Mar 31 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.3.0-1
- Converted Google project name to lower case in their URL (Aayush Kasurde)
- Fix the casing of GitHub (Aayush Kasurde)
- Allow projects to make insecure http calls
- Update the GNOME backend to rely on the cache.json if present
- Include in the fedmsg message if the new version found is odd or not
- Strip leading v from versions before we compare them (Ralph Bean)
- Update instructions in the README (Shagufta)
- Only place the name in the regex if it is asked for
- When searching show first the results of exact match search then the
  results of a broader search

* Thu Feb 26 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2.0
- Fix doc typos (reported by tibbs, fixed by Ralph Bean)
- Fix typo when unable to retrieve the latest version (Thomas Spura)
- Autocomplete distribution name when mapping a project
- Dynamically check existing projects while adding a new one
- Check now button available after an edit
- More information for the custom backend
- Fix the drupal backends to make them suppor project named 'drupal6: foo'
  or 'drupal7: bar'
- Fix pagination on quite some pages
- Allow users to browse their own log
- On postgresql '_' is a special character that we should escape
- User friendly url for example: /project/guake
- More info when mapping a project fails (including a link to the project
  causing the failure to map)

* Tue Feb 10 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.17-1
- Update to 0.1.17
- Bring back from cnucnu support for URLs including '*', ie:
  http://download.tuxfamily.org/xmoto/xmoto/*/ where anitya will go down the
  folder structure to find the latest version

* Thu Jan 29 2015 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.16-1
- Update to 0.1.16
- In the documentation (about page) adjust the code to store the url in a
  variable making it easier for people to copy/paste the code (Elan Ruusamäe)
- Add api to query for a project by homepage. (Ralph Bean)
- Typofix in the API docs generation. (Ralph Bean)

* Thu Dec 18 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.15-1
- Fix changelog to include the release in addition to the version
- Update to 0.1.15
- Fix links to the documentation to the proper github project
- Mention the-new-hotness in the README file
- Replace CNUCNU_* configuration keys by ANITYA_* keys
- Adjust the unit-tests to test the logic in jenkins (while skipping the backend
  plugins)
- Fix editing a project when version_url and regex are empty
- Fix button text for project and distro edit (Praveen Kumar)
- Display error message from the OpenID process (Patrick Uiterwijk)
- Fix pagination when browsing the packages of a distro
- Replace /api/projects/wiki by /api/packages/wiki and adjust the documentation
- Adjust the case of the name of the backends
- Allow an initial mapping when creating a project via GET arguments (Ralph
  Bean)
- update distro page text (Elan Ruusamäe)
- Replace "check now" button with spinner while ajax in transit (Ralph Bean)
- Fix sorting version from newest to oldest (Ralph Bean)
- Add the possibility for admins to delete a distro
- Adjust the launchpad backend to rely on the project name rather than the
  project homepage
- Strip all the inputs submitted by the user
- Fix mail_logging for when we cannot retrieve the process information
- Set a handler to the anitya logger to stderr

* Mon Nov 24 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.14-1
- Update to 0.1.14
- Simplify tagline at the top of the projects page. (Ralph Bean)
- Add fields to filter logs
- Enable admins to delete specific versions (useful while debugging)
- Add the /api endpoint documenting the API
- Expand the current API
- Check if there was a latest_version before complaining about the order
- Fill pattern input if provided. (Ralph Bean)
- Fill in form fields from query string if available. (Ralph Bean)

* Thu Oct 23 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.13-1
- Update to 0.1.13
- Add a keyboard shortcut on `c` to check the version
- Log the error when calling a certain website of a project and something
  goes wrong
- Support filtering by project name and log when viewing the list of project
  that failed to update at the last cron run
- Add a way to find the projects that simply never updated

* Wed Oct 22 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.12-1
- Update to 0.1.12
- Update the project's log if we retrieved an update w/o problems
- Add log handler on the cron job to monitor its progress
- Handle the situation where the folder backend is used against a FTP source
- Document a way to test a regular expression for anitya
- Update the sourceforge url to use the new one
- Escape the '+' symbols in the name of the projects in the regular expression

* Tue Oct 21 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.11-1
- Update to 0.1.11
- Adjust the default regex to handle project releasing as <project>src-<version>
  (ie: with no '-' or '_' between the project and src/source/srcmin)
- Adjust the project's log as soon as we properly retrieved a version which
  should reduce the list of failed projects nicely

* Tue Oct 21 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.10-1
- Update to 0.1.10
- Display the number of items returns in the projects, updates and search
  templates
- Always display the `Check now` button to admins
- Allow overriding the project's name for the Sourceforge backend
- Use urllib2 for FTP urls instead of requests
- Adjust the default regex for project having src|source before the
  version number
- Adjust the default regex for project using srcmin instead of src/source
- Adjust the drupal backend to try '_' instead of '-' if the first attempt
  didn't work
- Set the FROM header when making http/ftp queries
- Add keyboard shortcut `e` on the project page to access the edit page
- Add keyboard shortcut `esc` when editing/creating a project to leave
- Adjust the launchpad backend to rely on the project's homepage instead of
  its name

* Sat Oct 18 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.9-1
- Update to 0.1.9
- Add the possibility to view the project according to their update status

* Tue Oct 07 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.8.1-1
- Update to 0.1.8.1
- Fix typo in the cron script

* Tue Oct 07 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.8-1
- Update to 0.1.8
- Add option to debug the cron script
- Better fedmsg doc
- Announce any new release found, not just the latest one

* Tue Oct 07 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.7-1
- Update to 0.1.7
- Add logging to the DB when finding a new version

* Tue Oct 07 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.6-1
- Update to 0.1.6
- Fix the search for projects that are not mapped in any distribution

* Tue Oct 07 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.5-1
- Update to 0.1.5
- Add the possiblity to find all the packages/projects related to a distro
- Add the possibility to search the projects related to a distro
- Add basic anitya/fedmsg documentation
- Adjust unit-tests

* Mon Oct 06 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.4-1
- Update to 0.1.4
- Add a dedicated log handler reporting errors by email
- Fix yahoo and google login

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
