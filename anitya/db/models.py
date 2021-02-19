# -*- coding: utf-8 -*-
# This file is a part of the Anitya project.
#
# Copyright © 2017-2020 Michal Konecny <mkonecny@redhat.com>
# Copyright © 2014-2020 Pierre-Yves Chibon <pingou@pingoured.fr>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""SQLAlchemy database models."""

try:
    # The Python 3.6+ API
    from secrets import choice as random_choice
except ImportError:  # pragma: no cover
    # Fall back to random with os.urandom
    import random

    random = random.SystemRandom()
    random_choice = random.choice
import datetime
import arrow
import logging
import time
import string
import uuid

import six
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.types import TypeDecorator, CHAR

from anitya.config import config as anitya_config
from anitya.lib.versions import GLOBAL_DEFAULT as DEFAULT_VERSION_SCHEME
from anitya.lib.plugins import ECOSYSTEM_PLUGINS, BACKEND_PLUGINS, VERSION_PLUGINS
from .meta import Base


_log = logging.getLogger(__name__)

DEFAULT_PAGE_LIMIT = 50


def _paginate_query(query, page):
    """Paginate a given query to returned the specified page (if any)."""
    if page:
        try:
            page = int(page)
        except ValueError:
            page = None

    if page:
        limit = DEFAULT_PAGE_LIMIT
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

    return query


class Distro(Base):
    __tablename__ = "distros"

    name = sa.Column(sa.String(200), primary_key=True)

    def __init__(self, name):
        """ Constructor. """
        self.name = name

    def __json__(self):
        return dict(name=self.name)

    @classmethod
    def by_name(cls, session, name):
        query = session.query(cls).filter(
            sa.func.lower(cls.name) == sa.func.lower(name)
        )

        return query.first()

    get = by_name

    @classmethod
    def all(cls, session, page=None, count=False):
        query = session.query(cls).order_by(cls.name)

        query = _paginate_query(query, page)

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def search(cls, session, pattern, page=None, count=False):
        """ Search the distribuutions by their name """

        if "*" in pattern:
            pattern = pattern.replace("*", "%")

        query = (
            session.query(cls)
            .filter(sa.or_(sa.func.lower(cls.name).like(sa.func.lower(pattern))))
            .order_by(cls.name)
            .distinct()
        )

        query = _paginate_query(query, page)

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def get_or_create(cls, session, name):
        distro = cls.by_name(session, name)
        if not distro:
            distro = cls(name=name)
            session.add(distro)
            session.flush()
        return distro


class Packages(Base):
    __tablename__ = "packages"

    id = sa.Column(sa.Integer, primary_key=True)
    distro_name = sa.Column(
        sa.String(200),
        sa.ForeignKey("distros.name", ondelete="cascade", onupdate="cascade"),
    )
    project_id = sa.Column(
        sa.Integer, sa.ForeignKey("projects.id", ondelete="cascade", onupdate="cascade")
    )

    package_name = sa.Column(sa.String(200))

    __table_args__ = (sa.UniqueConstraint("distro_name", "package_name"),)

    project = sa.orm.relationship(
        "Project", backref=sa.orm.backref("package", cascade="all, delete-orphan")
    )

    distro = sa.orm.relationship(
        "Distro", backref=sa.orm.backref("package", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return "<Packages(%s, %s: %s)>" % (
            self.project_id,
            self.distro_name,
            self.package_name,
        )

    def __json__(self):
        return dict(package_name=self.package_name, distro=self.distro_name)

    @classmethod
    def by_id(cls, session, pkg_id):
        return session.query(cls).filter_by(id=pkg_id).first()

    @classmethod
    def get(cls, session, project_id, distro_name, package_name):
        query = (
            session.query(cls)
            .filter(cls.project_id == project_id)
            .filter(sa.func.lower(cls.distro_name) == sa.func.lower(distro_name))
            .filter(cls.package_name == package_name)
        )
        return query.first()

    @classmethod
    def by_package_name_distro(cls, session, package_name, distro_name):
        query = (
            session.query(cls)
            .filter(cls.package_name == package_name)
            .filter(sa.func.lower(cls.distro_name) == sa.func.lower(distro_name))
        )
        return query.first()


class Project(Base):
    """
    Models an upstream project and maps it to a database table.

    Attributes:
        id (sa.Integer): The database primary key.
        name (sa.String): The upstream project's name.
        homepage (sa.String): The URL for the project's home page.
        backend (sa.String): The name of the backend to use when fetching updates;
            this is a foreign key to a :class:`Backend`.
        ecosystem_name (sa.String): The name of the ecosystem this project is a part
            of. If the project isn't part of an ecosystem (e.g. PyPI), use the homepage
            URL.
        version_url (sa.String): The url to use when polling for new versions. This
            may be ignored if this project is part of an ecosystem with a fixed
            URL (e.g. Cargo projects are on https://crates.io).
        regex (sa.String): A Python ``re`` style regular expression that is applied
            to the HTML from ``version_url`` to find versions.
        version_prefix (sa.String): A string containing version prefixes delimited by ';'.
            These prefixes will be removed from string showed on page.
        version_pattern (sa.String): A version pattern used for calendar version scheme.
        insecure (sa.Boolean): Whether or not to validate the x509 certificate
            offered by the server at ``version_url``. Defaults to ``False``.
        releases_only (sa.Boolean): Whether or not to check releases instead of tags.
            This is now only used by GitHub backend.
        error_counter (sa.Integer): Counter that contains number of unsuccessful checks.
            This counter will reset each time a successful check is done.
            Doesn't count ratelimit errors.
        latest_version (sa.String): The latest version for the project, as determined
            by the version sorting algorithm.
        logs (sa.Text): The result of the last update.
        check_successful (sa.Boolean): Flag that contains result of last check.
            ``None`` - not checked yet, ``True`` - checked successfully, ``False``
            - error occured during check
        updated_on (sa.DateTime): When the project was last updated.
        created_on (sa.DateTime): When the project was created in Anitya.
        packages (list): List of :class:`Package` objects which represent the
            downstream packages for this project.
        version_scheme (sa.String): The version scheme to use for this project.
            If this is null, a default will be used. See the :mod:`anitya.lib.versions`
            documentation for more information.
        pre_release_filter (sa.String): A string containing filters delimited by ';'.
            Filtered versions will be marked as pre_release.
        archived (sa.Boolean): Marks the project as archived, archived projects can't be edited
            by normal users and are no longer checked for new versions.
        version_filter (sa.String): A string containing filters delimited by ';'.
            Filtered versions will be skipped when retrieving versions.
    """

    __tablename__ = "projects"

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(200), nullable=False, index=True)
    homepage = sa.Column(sa.String(200), nullable=False)

    backend = sa.Column(sa.String(200), default="custom")
    ecosystem_name = sa.Column(sa.String(200), nullable=False, index=True)
    version_url = sa.Column(sa.String(200), nullable=True)
    regex = sa.Column(sa.String(200), nullable=True)
    version_prefix = sa.Column(sa.String(200), nullable=True)
    version_pattern = sa.Column(sa.String(200), nullable=True)
    insecure = sa.Column(sa.Boolean, nullable=False, default=False)
    releases_only = sa.Column(sa.Boolean, nullable=False, default=False)
    error_counter = sa.Column(sa.Integer, index=True, default=0)
    version_scheme = sa.Column(sa.String(50), nullable=True)
    pre_release_filter = sa.Column(sa.String(200), nullable=True)
    archived = sa.Column(sa.Boolean, nullable=False, default=False)
    version_filter = sa.Column(sa.String(200), nullable=True)

    latest_version = sa.Column(sa.String(50))
    logs = sa.Column(sa.Text)
    check_successful = sa.Column(sa.Boolean, default=None, index=True)

    last_check = sa.Column(
        sa.TIMESTAMP(timezone=True), default=lambda: arrow.utcnow().datetime, index=True
    )
    next_check = sa.Column(
        sa.TIMESTAMP(timezone=True), default=lambda: arrow.utcnow().datetime, index=True
    )

    updated_on = sa.Column(
        sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.current_timestamp()
    )
    created_on = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    packages = sa.orm.relationship("Packages", cascade="all, delete-orphan")

    __table_args__ = (
        sa.UniqueConstraint("name", "homepage"),
        sa.UniqueConstraint(
            "name", "ecosystem_name", name="UNIQ_PROJECT_NAME_PER_ECOSYSTEM"
        ),
    )

    @validates("backend")
    def validate_backend(self, key, value):
        if value not in BACKEND_PLUGINS.get_plugin_names():
            raise ValueError('Backend "{}" is not supported.'.format(value))
        return value

    @property
    def versions(self):
        """Return list of all versions stored, sorted from newest to oldest.

        Returns:
           :obj:`list` of :obj:`str`: List of versions
        """
        sorted_versions = self.get_sorted_version_objects()
        return [str(v) for v in sorted_versions]

    @property
    def stable_versions(self):
        """
        Return list of all versions that aren't flagged as pre-release.

        Returns:
           list(`anitya.lib.versions.Base`): List of stable version objects
        """
        sorted_versions = self.get_sorted_version_objects()
        return [version for version in sorted_versions if not version.prerelease()]

    def get_last_created_version(self):
        """
        Returns last obtained release by date.

        Returns:
            (`ProjectVersion`): Version object or None, if project doesn't have any version yet.
        """
        if self.versions_obj:
            skip_no_date_versions = []
            for version in self.versions_obj:
                if version.created_on:
                    skip_no_date_versions.append(version)
            if skip_no_date_versions:
                sorted_versions = sorted(
                    skip_no_date_versions, key=lambda x: x.created_on, reverse=True
                )
                return sorted_versions[0]

        return None

    def get_time_last_created_version(self):
        """
        Returns creation time of latest version sorted by time of creation.

        Returns:
            (`arrow.Arrow`): Time of the latest created version or None,
                if project doesn't have any version yet.
        """
        version = self.get_last_created_version()

        if version and version.created_on:
            return arrow.get(version.created_on)

        return None

    def create_version_objects(self, versions):
        """
        Creates sorted list of version objects defined by `self.version_class` from versions list.

        Args:
            versions (list(str or dict)): List of versions that are not associated with the project.

        Returns:
            list(`anitya.lib.versions.Base`): List of version objects defined by
                `self.version_class`.
        """
        version_class = self.get_version_class()
        versions = sorted(
            [
                version_class(
                    version=version if isinstance(version, str) else version["version"],
                    prefix=self.version_prefix,
                    pre_release_filter=self.pre_release_filter,
                    created_on=datetime.datetime.utcnow(),
                    pattern=self.version_pattern,
                    commit_url=(
                        version["commit_url"]
                        if isinstance(version, dict) and "commit_url" in version
                        else None
                    ),
                )
                for version in versions
            ]
        )

        return versions

    def get_version_url(self):
        """Returns full version url, which is used by backend.

        Returns:
            str: Version url or empty string if backend is not specified
        """
        if not self.backend:
            return ""

        backend = BACKEND_PLUGINS.get_plugin(self.backend)
        return backend.get_version_url(self)

    def get_sorted_version_objects(self):
        """Return list of all version objects stored, sorted from newest to oldest.

        Returns:
           :obj:`list` of :obj:`anitya.lib.versions.Base`: List of version objects
        """
        version_class = self.get_version_class()
        versions = [
            version_class(
                version=v_obj.version,
                prefix=self.version_prefix,
                pre_release_filter=self.pre_release_filter,
                created_on=v_obj.created_on,
                pattern=self.version_pattern,
                commit_url=v_obj.commit_url,
            )
            for v_obj in self.versions_obj
        ]
        sorted_versions = list(reversed(sorted(versions)))
        return sorted_versions

    @property
    def latest_version_object(self):
        sorted_versions = self.get_sorted_version_objects()
        if sorted_versions:
            return sorted_versions[0]
        return None

    def get_version_class(self):
        """
        Get the class for the version scheme used by this project.

        This will take into account the defaults set in the ecosystem, backend,
        and globally. The version scheme locations are checked in the following
        order and the first non-null result is returned:

        1. On the project itself in the ``version_scheme`` column.
        2. The project's ecosystem default, if the project is part of one.
        3. The project's backend default, if the backend defines one.
        4. The global default defined in :data:`anitya.lib.versions.GLOBAL_DEFAULT`

        Returns:
            anitya.lib.versions.Version: A ``Version`` sub-class.
        """
        version_scheme = self.version_scheme
        if not version_scheme and self.ecosystem_name:
            ecosystem = ECOSYSTEM_PLUGINS.get_plugin(self.ecosystem_name)
            if ecosystem is None:
                # This project uses its URL as an ecosystem
                version_scheme = DEFAULT_VERSION_SCHEME
            else:
                version_scheme = ecosystem.default_version_scheme
        if not version_scheme and self.backend:
            backend = BACKEND_PLUGINS.get_plugin(self.backend)
            version_scheme = backend.default_version_scheme
        if not version_scheme:
            version_scheme = DEFAULT_VERSION_SCHEME

        return VERSION_PLUGINS.get_plugin(version_scheme)

    def __repr__(self):
        return "<Project(%s, %s)>" % (self.name, self.homepage)

    def __json__(self, detailed=False):
        output = dict(
            id=self.id,
            name=self.name,
            homepage=self.homepage,
            regex=self.regex,
            backend=self.backend,
            version_url=self.version_url,
            version=self.latest_version,
            versions=self.versions,
            stable_versions=[v.version for v in self.stable_versions],
            created_on=time.mktime(self.created_on.timetuple())
            if self.created_on
            else None,
            updated_on=time.mktime(self.updated_on.timetuple())
            if self.updated_on
            else None,
            ecosystem=self.ecosystem_name,
        )
        if detailed:
            output["packages"] = [pkg.__json__() for pkg in self.packages]

        return output

    @classmethod
    def get_or_create(cls, session, name, homepage, backend="custom"):
        project = cls.by_name_and_homepage(session, name, homepage)
        if not project:
            project = cls(name=name, homepage=homepage, backend=backend)
            session.add(project)
            session.flush()
        return project

    @classmethod
    def by_name(cls, session, name):
        return session.query(cls).filter_by(name=name).all()

    @classmethod
    def by_id(cls, session, project_id):
        return session.query(cls).filter_by(id=project_id).first()

    get = by_id

    @classmethod
    def by_homepage(cls, session, homepage):
        return session.query(cls).filter_by(homepage=homepage).all()

    @classmethod
    def by_name_and_homepage(cls, session, name, homepage):
        query = (
            session.query(cls).filter(cls.name == name).filter(cls.homepage == homepage)
        )
        return query.first()

    @classmethod
    def by_name_and_ecosystem(cls, session, name, ecosystem):
        try:
            query = session.query(cls)
            query = query.filter(cls.name == name, cls.ecosystem_name == ecosystem)
            return query.one()
        except NoResultFound:
            return None

    @classmethod
    def all(cls, session, page=None, count=False):
        query = session.query(Project).order_by(sa.func.lower(Project.name))

        query = _paginate_query(query, page)

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def by_distro(cls, session, distro, page=None, count=False):
        query = (
            session.query(Project)
            .filter(Project.id == Packages.project_id)
            .filter(sa.func.lower(Packages.distro_name) == sa.func.lower(distro))
            .order_by(sa.func.lower(Project.name))
        )

        query = _paginate_query(query, page)

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def updated(
        cls, session, status="updated", name=None, log=None, page=None, count=False
    ):
        """Method used to retrieve projects according to their logs and
        how they performed at the last cron job.

        :kwarg status: used to filter the projects based on how they
            performed at the last cron run
        :kwarg name: if present, will return the entries having the matching
            name
        :kwarg log: if present, will return the entries having the matching
            log
        :kwarg page: The page number of returned, pages contain 50 entries
        :kwarg count: A boolean used to return either the list of entries
            matching the criterias or just the COUNT of entries

        """

        query = session.query(Project)

        if status == "updated":
            query = query.filter(
                Project.check_successful.isnot(None), Project.check_successful.is_(True)
            ).order_by(Project.last_check.desc())
        elif status == "failed":
            query = query.filter(
                Project.check_successful.isnot(None),
                Project.check_successful.is_(False),
                Project.error_counter > 0,
            ).order_by(Project.error_counter.desc())

        elif status == "never_updated":
            query = query.filter(Project.latest_version.is_(None)).order_by(
                Project.created_on
            )
        elif status == "archived":
            query = query.filter(
                Project.archived.isnot(None), Project.archived.is_(True)
            )
        query.order_by(sa.func.lower(Project.name))

        if name:
            if "*" in name:
                name = name.replace("*", "%")
            else:
                name = "%" + name + "%"

            query = query.filter(Project.name.ilike(name))

        if log:
            if "*" in log:
                log = log.replace("*", "%")
            else:
                log = "%" + log + "%"

            query = query.filter(Project.logs.ilike(log))

        query = _paginate_query(query, page)

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def search(cls, session, pattern, distro=None, page=None, count=False):
        """ Search the projects by their name or package name """

        query1 = session.query(cls)

        if pattern:
            pattern = pattern.replace("_", r"\_")
            if "*" in pattern:
                pattern = pattern.replace("*", "%")
            if "%" in pattern:
                query1 = query1.filter(Project.name.ilike(pattern))
            else:
                query1 = query1.filter(Project.name == pattern)

        query2 = session.query(cls).filter(Project.id == Packages.project_id)

        if pattern:
            if "%" in pattern:
                query2 = query2.filter(Packages.package_name.ilike(pattern))
            else:
                query2 = query2.filter(Packages.package_name == pattern)

        if distro is not None:
            query1 = query1.filter(Project.id == Packages.project_id).filter(
                sa.func.lower(Packages.distro_name) == sa.func.lower(distro)
            )
            query2 = query2.filter(
                sa.func.lower(Packages.distro_name) == sa.func.lower(distro)
            )

        query = query1.distinct().union(query2.distinct()).order_by(cls.name)

        query = _paginate_query(query, page)

        if count:
            return query.count()
        else:
            return query.all()


class ProjectVersion(Base):
    """
    Models of version table representing version on project.

    Attributes:
        project_id (sa.Integer): Related project id.
        version (sa.String): Raw version string as obtained from upstream.
        created_on (sa.DateTime): When the version was created in Anitya.
        commit_url (sa.String): URL to commit. Currently only used by GitHub backend.
        project (sa.orm.relationship): Back reference to project.
    """

    __tablename__ = "projects_versions"

    project_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("projects.id", ondelete="cascade", onupdate="cascade"),
        primary_key=True,
    )
    version = sa.Column(sa.String(50), primary_key=True)
    created_on = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    commit_url = sa.Column(sa.String(200), nullable=True)

    project = sa.orm.relationship(
        "Project", backref=sa.orm.backref("versions_obj", cascade="all, delete-orphan")
    )

    @property
    def pre_release(self):
        """
        Is the version pre-release?

        Return:
            (Boolean): Pre-release flag.
        """

        version_class = self.project.get_version_class()
        version = version_class(
            version=self.version,
            prefix=self.project.version_prefix,
            pre_release_filter=self.project.pre_release_filter,
            created_on=self.created_on,
            pattern=self.project.version_pattern,
            commit_url=self.commit_url,
        )
        return version.prerelease()


class ProjectFlag(Base):
    __tablename__ = "projects_flags"

    id = sa.Column(sa.Integer, primary_key=True)

    project_id = sa.Column(
        sa.Integer, sa.ForeignKey("projects.id", ondelete="cascade", onupdate="cascade")
    )

    reason = sa.Column(sa.Text, nullable=False)
    user = sa.Column(sa.String(200), index=True, nullable=False)
    state = sa.Column(sa.String(50), default="open", nullable=False)
    created_on = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    updated_on = sa.Column(
        sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.current_timestamp()
    )

    project = sa.orm.relationship(
        "Project", backref=sa.orm.backref("flags", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return "<ProjectFlag(%s, %s, %s)>" % (self.project.name, self.user, self.state)

    def __json__(self, detailed=False):
        output = dict(
            id=self.id,
            project=self.project.name,
            user=self.user,
            state=self.state,
            created_on=time.mktime(self.created_on.timetuple()),
            updated_on=time.mktime(self.updated_on.timetuple()),
        )
        if detailed:
            output["reason"] = self.reason

        return output

    @classmethod
    def all(cls, session, page=None, count=False):
        query = session.query(ProjectFlag).order_by(ProjectFlag.created_on)

        return query.all()

    @classmethod
    def search(
        cls,
        session,
        project_name=None,
        from_date=None,
        user=None,
        state=None,
        limit=None,
        offset=None,
        count=False,
    ):
        """Return the list of the last Flag entries present in the database.

        :arg cls: the class object
        :arg session: the database session used to query the information.
        :kwarg project_name: the name of the project to restrict the flags to.
        :kwarg from_date: the date from which to give the entries.
        :kwarg user: the name of the user to restrict the flags to.
        :kwarg state: the flag's status (open or closed).
        :kwarg limit: limit the result to X rows.
        :kwarg offset: start the result at row X.
        :kwarg count: a boolean to return the result of a COUNT query
            if true, returns the data if false (default).

        """
        query = session.query(cls)

        if project_name:
            query = query.filter(cls.project_id == Project.id).filter(
                Project.name == project_name
            )

        if from_date:
            query = query.filter(cls.created_on >= from_date)

        if user:
            query = query.filter(cls.user == user)

        if state:
            query = query.filter(cls.state == state)

        query = query.order_by(cls.created_on.desc())

        if count:
            return query.count()

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    @classmethod
    def get(cls, session, flag_id):
        query = session.query(cls).filter(cls.id == flag_id)
        return query.first()


class Run(Base):
    __tablename__ = "runs"

    total_count = sa.Column(sa.Integer)
    error_count = sa.Column(sa.Integer)
    ratelimit_count = sa.Column(sa.Integer)
    success_count = sa.Column(sa.Integer)
    created_on = sa.Column(
        sa.DateTime, default=datetime.datetime.utcnow, primary_key=True
    )

    @classmethod
    def last_entry(cls, session):
        """ Return the last log about the cron run. """

        query = session.query(cls).order_by(cls.created_on.desc())
        return query.first()


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    If PostgreSQL is being used, use its native UUID type, otherwise use a CHAR(32) type.
    """

    impl = CHAR

    def load_dialect_impl(self, dialect):
        """
        PostgreSQL has a native UUID type, so use it if we're using PostgreSQL.

        Args:
            dialect (sqlalchemy.engine.interfaces.Dialect): The dialect in use.

        Returns:
            sqlalchemy.types.TypeEngine: Either a PostgreSQL UUID or a CHAR(32) on other
                dialects.
        """
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        """
        Process the value being bound.

        If PostgreSQL is in use, just use the string representation of the UUID.
        Otherwise, use the integer as a hex-encoded string.

        Args:
            value (object): The value that's being bound to the object.
            dialect (sqlalchemy.engine.interfaces.Dialect): The dialect in use.

        Returns:
            str: The value of the UUID as a string.
        """
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        """
        Casts the UUID value to the native Python type.

        Args:
            value (object): The database value.
            dialect (sqlalchemy.engine.interfaces.Dialect): The dialect in use.

        Returns:
            uuid.UUID: The value as a Python :class:`uuid.UUID`.
        """
        if value is None:
            return value
        else:
            return uuid.UUID(value)


class User(Base):
    """
    A table for Anitya users.

    This table is intended to work with a table of third-party authentication
    providers. Anitya does not support local users.

    Attributes:
        id (uuid.UUID): The primary key for the table.
        email (str): The user's email.
        username (str): The user's username, as retrieved from third-party authentication.
        active (bool): Indicates whether the user is active. If false, users will not be
            able to log in.
        admin (bool): Determine if this user is an administrator. If True the user is
            administrator.
        social_auth (sqlalchemy.orm.dynamic.AppenderQuery): The list of
            :class:`social_flask_sqlalchemy.models.UserSocialAuth` entries for this user.
    """

    __tablename__ = "users"

    id = sa.Column(GUID, primary_key=True, default=uuid.uuid4)
    # SMTP says 256 is the maximum length of a path:
    # https://tools.ietf.org/html/rfc5321#section-4.5.3
    email = sa.Column(sa.String(256), nullable=False, index=True, unique=True)
    username = sa.Column(sa.String(256), nullable=False, index=True, unique=True)
    active = sa.Column(sa.Boolean, default=True)
    admin = sa.Column(sa.Boolean, default=False)

    @property
    def is_admin(self):
        """
        Determine if this user is an administrator. Set admin flag
        if the user is preconfigured.

        Returns:
            bool: True if the user is an administrator.
        """
        if not self.admin:
            if six.text_type(self.id) in anitya_config.get("ANITYA_WEB_ADMINS", []):
                self.admin = True
        return self.admin

    @property
    def is_active(self):
        """
        Implement the flask-login interface for determining if the user is active.

        If a user is _not_ active, they are not allowed to log in.

        Returns:
            bool: True if the user is active.
        """
        return self.active

    @property
    def is_anonymous(self):
        """
        Implement the flask-login interface for determining if the user is authenticated.

        flask-login uses an "anonymous user" object if there is no authenticated user. This
        indicates to flask-login this user is not an anonymous user.

        Returns:
            bool: False in all cases.
        """
        return False

    @property
    def is_authenticated(self):
        """
        Implement the flask-login interface for determining if the user is authenticated.

        In this case, if flask-login has an instance of :class:`User`, then that user has
        already authenticated via a third-party authentication mechanism.

        Returns:
            bool: True in all cases.
        """
        return True

    def get_id(self):
        """
        Implement the flask-login interface for retrieving the user's ID.

        Returns:
            six.text_type: The Unicode string that uniquely identifies a user.
        """
        return six.text_type(self.id)

    def to_dict(self):
        """
        Creates json compatible dict from `User`.

        Returns:
            dict: `User` object transformed to dictionary.
        """

        return dict(
            id=str(self.id),
            email=self.email,
            username=self.username,
            active=self.active,
        )


def _api_token_generator(charset=string.ascii_letters + string.digits, length=40):
    """
    Generate an API token of a given length using the provided character set.

    Args:
        charset (str): A string of characters to choose from in the token.
        length (int): The number of characters to use in the token.

    Returns:
        str: The API token as a unicode string.
    """
    return "".join(random_choice(charset) for __ in range(length))


class ApiToken(Base):
    """
    A table for user API tokens.

    Attributes:
        token (sa.String): A 40 character string that represents the API token.
            This is the primary key and is, by default, generated automatically.
        created (sa.DateTime): The time this API token was created.
        description (sa.Text): A user-provided description of what the API token is for.
        user (User): The user this API token is associated with.
    """

    __tablename__ = "tokens"

    token = sa.Column(sa.String(40), default=_api_token_generator, primary_key=True)
    created = sa.Column(sa.DateTime, default=datetime.datetime.utcnow, nullable=False)
    user_id = sa.Column(GUID, sa.ForeignKey("users.id"), nullable=False)
    user = sa.orm.relationship(
        "User",
        lazy="joined",
        backref=sa.orm.backref("api_tokens", cascade="all, delete-orphan"),
    )
    description = sa.Column(sa.Text, nullable=True)
