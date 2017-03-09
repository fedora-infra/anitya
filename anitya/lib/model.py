# -*- coding: utf-8 -*-

"""
 (c) 2014-2016 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

anitya mapping of python classes to Database Tables.
"""

import datetime
import inspect
import logging
import re
import sys
import time

__requires__ = ['SQLAlchemy >= 0.7']  # NOQA
import pkg_resources  # NOQA
from packaging import version as pep440_version
import semantic_version

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from anitya.lib import exceptions
import anitya


BASE = declarative_base()


_log = logging.getLogger(__name__)


# Check for a leading 'v' in versions
_leading_v = re.compile(r'v\d.*')


# Constants for the various versions we support
GENERIC_VERSION = u'Generic Version'
PEP440_VERSION = u'PEP-440'
SEMANTIC_VERSION = u'Semantic Version'


def _paginate_query(query, page):
    ''' Paginate a given query to returned the specified page (if any).
    '''
    if page:
        try:
            page = int(page)
        except ValueError:
            page = None

    if page:
        limit = 50
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

    return query


class Log(BASE):
    ''' Simple table to store/log action occuring in the database. '''
    __tablename__ = 'logs'

    id = sa.Column(sa.Integer, primary_key=True)
    user = sa.Column(sa.String(200), index=True, nullable=False)
    project = sa.Column(sa.String(200), index=True, nullable=True)
    distro = sa.Column(sa.String(200), index=True, nullable=True)
    description = sa.Column(sa.Text, nullable=False)
    created_on = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    def __init__(self, user, project=None, distro=None, description=None):
        ''' Constructor.
        '''
        self.user = user
        self.project = project
        self.distro = distro
        self.description = description

    @classmethod
    def insert(cls, session, user, project=None, distro=None,
               description=None):
        """ Insert the given log entry into the database.

        :arg session: the session to connect to the database with
        :arg user: the username of the user doing the action
        :arg project: the `Project` object of the project changed
        :arg distro: the `Distro` object of the distro changed
        :arg description: a short textual description of the action
            performed

        """
        project_name = None
        if project:
            project_name = project.name

        distro_name = None
        if distro:
            distro_name = distro.name

        log = Log(user=user, project=project_name, distro=distro_name,
                  description=description)
        session.add(log)
        session.flush()

    @classmethod
    def search(cls, session, project_name=None, from_date=None, user=None,
               limit=None, offset=None, count=False):
        """ Return the list of the last Log entries present in the database.

        :arg cls: the class object
        :arg session: the database session used to query the information.
        :kwarg project_name: the name of the project to restrict the logs to.
        :kwarg from_date: the date from which to give the entries.
        :kwarg user: the name of the user to restrict the logs to.
        :kwarg limit: limit the result to X rows.
        :kwarg offset: start the result at row X.
        :kwarg count: a boolean to return the result of a COUNT query
            if true, returns the data if false (default).

        """
        query = session.query(
            cls
        )

        if project_name:
            query = query.filter(cls.project == project_name)

        if from_date:
            query = query.filter(cls.created_on >= from_date)

        if user:
            if isinstance(user, (list, tuple)):
                query = query.filter(cls.user.in_(user))
            else:
                query = query.filter(cls.user == user)

        query = query.order_by(cls.created_on.desc())

        if count:
            return query.count()

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()


class Backend(BASE):
    __tablename__ = 'backends'

    name = sa.Column(sa.String(200), primary_key=True)
    default_ecosystem = relationship("Ecosystem", uselist=False,
                                     back_populates="default_backend")

    @classmethod
    def all(cls, session):
        query = session.query(cls).order_by(cls.name)
        return query.all()

    @classmethod
    def by_name(cls, session, name):
        return session.query(cls).filter_by(name=name).first()

    get = by_name


class Ecosystem(BASE):
    __tablename__ = 'ecosystems'

    name = sa.Column(sa.String(200), primary_key=True)
    default_backend_name = sa.Column(
        sa.String(200),
        sa.ForeignKey(
            "backends.name",
            ondelete="cascade",
            onupdate="cascade"),
        unique=True
    )
    default_backend = relationship("Backend",
                                   back_populates="default_ecosystem")
    projects = relationship("Project", back_populates="ecosystem")

    @classmethod
    def all(cls, session):
        query = session.query(cls).order_by(cls.name)
        return query.all()

    @classmethod
    def by_name(cls, session, name):
        try:
            return session.query(cls).filter_by(name=name).one()
        except NoResultFound:
            return None

    get = by_name


class Distro(BASE):
    __tablename__ = 'distros'

    name = sa.Column(sa.String(200), primary_key=True)

    def __init__(self, name):
        ''' Constructor. '''
        self.name = name

    def __json__(self):
        return dict(name=self.name)

    @classmethod
    def by_name(cls, session, name):
        query = session.query(
            cls
        ).filter(
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
        ''' Search the distribuutions by their name '''

        if '*' in pattern:
            pattern = pattern.replace('*', '%')

        query = session.query(
            cls
        ).filter(
            sa.or_(
                sa.func.lower(cls.name).like(sa.func.lower(pattern)),
            )
        ).order_by(
            cls.name
        ).distinct()

        query = _paginate_query(query, page)

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def get_or_create(cls, session, name):
        distro = cls.by_name(session, name)
        if not distro:
            distro = cls(
                name=name
            )
            session.add(distro)
            session.flush()
        return distro


class Packages(BASE):
    __tablename__ = 'packages'

    id = sa.Column(sa.Integer, primary_key=True)
    distro = sa.Column(
        sa.String(200),
        sa.ForeignKey(
            "distros.name",
            ondelete="cascade",
            onupdate="cascade"))
    project_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(
            "projects.id",
            ondelete="cascade",
            onupdate="cascade")
    )

    package_name = sa.Column(sa.String(200))

    __table_args__ = (
        sa.UniqueConstraint('distro', 'package_name'),
    )

    project = sa.orm.relation('Project')

    def __repr__(self):
        return '<Packages(%s, %s: %s)>' % (
            self.project_id, self.distro, self.package_name)

    def __json__(self):
        return dict(
            package_name=self.package_name,
            distro=self.distro,
        )

    @classmethod
    def by_id(cls, session, pkg_id):
        return session.query(cls).filter_by(id=pkg_id).first()

    @classmethod
    def get(cls, session, project_id, distro, package_name):
        query = session.query(
            cls
        ).filter(
            cls.project_id == project_id
        ).filter(
            sa.func.lower(cls.distro) == sa.func.lower(distro)
        ).filter(
            cls.package_name == package_name
        )
        return query.first()

    @classmethod
    def by_package_name_distro(cls, session, package_name, distro):
        query = session.query(
            cls
        ).filter(
            cls.package_name == package_name
        ).filter(
            sa.func.lower(cls.distro) == sa.func.lower(distro)
        )
        return query.first()


class Project(BASE):
    """
    Models an upstream project and maps it to a database table.

    Attributes:
        id (sa.Integer): The database primary key.
        name (sa.String): The upstream project's name.
        homepage (sa.String): The URL for the project's home page.
        backend (sa.String): The name of the backend to use when fetching updates;
            this is a foreign key to a :class:`Backend`.
        ecosystem_name (sa.String): The name of the ecosystem this project is a part
            of. This is a foreign key to :class:`Ecosystem` and may be null.
        ecosystem (Ecosystem): The :class:`Ecosystem` this project is a part of.
        version_url (sa.String): The url to use when polling for new versions. This
            may be ignored if this project is part of an ecosystem with a fixed
            URL (e.g. Cargo projects are on https://crates.io).
        regex (sa.String): A Python ``re`` style regular expression that is applied
            to the HTML from ``version_url`` to find versions.
        insecure (sa.Boolean): Whether or not to validate the x509 certificate
            offered by the server at ``version_url``. Defaults to ``False``.
        latest_version (sa.Boolean): The latest version for the project, as determined
            by the version sorting algorithm.
        logs (sa.Text): The result of the last update.
        updated_on (sa.DateTime): When the project was last updated.
        created_on (sa.DateTime): When the project was created in Anitya.
        packages (list): List of :class:`Package` objects which represent the
            downstream packages for this project.
        version_scheme (sa.String): The version scheme to use for this project.
            This needs to be a valid value for the ``type`` column of ProjectVersion.
    """

    __tablename__ = 'projects'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(200), nullable=False, index=True)
    homepage = sa.Column(sa.String(200), nullable=False)

    # TODO: Define ORM forward/backward references for backend as for ecosystem
    backend = sa.Column(
        sa.String(200),
        sa.ForeignKey(
            "backends.name",
            ondelete="cascade",
            onupdate="cascade"),
        default='custom',
    )
    ecosystem_name = sa.Column(
        sa.String(200),
        sa.ForeignKey(
            "ecosystems.name",
            ondelete="set null",
            onupdate="cascade",
            name="FK_ECOSYSTEM_FOR_PROJECT"),
        nullable=True
    )
    version_scheme = sa.Column(sa.String(50), nullable=False, default=PEP440_VERSION)

    ecosystem = relationship("Ecosystem", back_populates="projects")
    version_url = sa.Column(sa.String(200), nullable=True)
    regex = sa.Column(sa.String(200), nullable=True)
    version_prefix = sa.Column(sa.String(200), nullable=True)
    insecure = sa.Column(sa.Boolean, nullable=False, default=False)

    latest_version = sa.Column(sa.String(50))
    logs = sa.Column(sa.Text)

    updated_on = sa.Column(sa.DateTime, server_default=sa.func.now(),
                           onupdate=sa.func.current_timestamp())
    created_on = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    packages = sa.orm.relation('Packages')

    __table_args__ = (
        sa.UniqueConstraint('name', 'homepage'),
        sa.UniqueConstraint('name', 'ecosystem_name',
                            name="UNIQ_PROJECT_NAME_PER_ECOSYSTEM"),
    )

    @property
    def versions(self):
        ''' Return list of all versions stored, sorted from newest to oldest.
        '''
        try:
            versions = [str(v) for v in sorted(self.versions_obj)]
        except anitya.lib.exceptions.InvalidVersion:
            versions = [v.version for v in self.versions_obj]

        return list(reversed(versions))

    @property
    def version_class(self):
        """The model class for the version scheme used on this project"""
        return version_classes[self.version_scheme]

    def __repr__(self):
        return '<Project(%s, %s)>' % (self.name, self.homepage)

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
            created_on=time.mktime(self.created_on.timetuple()),
            updated_on=time.mktime(self.updated_on.timetuple()),
        )
        if detailed:
            output['packages'] = [pkg.__json__() for pkg in self.packages]

        return output

    @classmethod
    def get_or_create(cls, session, name, homepage, backend='custom'):
        project = cls.by_name_and_homepage(session, name, homepage)
        if not project:
            # Before creating, make sure the backend already exists
            backend_obj = Backend.get(session, name=backend)
            if not backend_obj:
                # We don't want to automatically create these.  They must have
                # code associated with them in anitya.lib.backends
                raise ValueError("No such backend %r" % backend)

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
        query = session.query(
            cls
        ).filter(
            cls.name == name
        ).filter(
            cls.homepage == homepage
        )
        return query.first()

    @classmethod
    def by_name_and_ecosystem(cls, session, name, ecosystem):
        try:
            query = session.query(
                cls
            ).filter(
                cls.name == name
            ).join(
                Project.ecosystem
            ).filter(
                Ecosystem.name == ecosystem
            )
            return query.one()
        except NoResultFound:
            return None

    @classmethod
    def all(cls, session, page=None, count=False):
        query = session.query(
            Project
        ).order_by(
            sa.func.lower(Project.name)
        )

        query = _paginate_query(query, page)

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def by_distro(cls, session, distro, page=None, count=False):
        query = session.query(
            Project
        ).filter(
            Project.id == Packages.project_id
        ).filter(
            sa.func.lower(Packages.distro) == sa.func.lower(distro)
        ).order_by(
            sa.func.lower(Project.name)
        )

        query = _paginate_query(query, page)

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def updated(
            cls, session, status='updated', name=None, log=None,
            page=None, count=False):
        ''' Method used to retrieve projects according to their logs and
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

        '''

        query = session.query(
            Project
        ).order_by(
            sa.func.lower(Project.name)
        )

        if status == 'updated':
            query = query.filter(
                Project.logs.isnot(None),
                Project.logs == 'Version retrieved correctly',
            )
        elif status == 'failed':
            query = query.filter(
                Project.logs.isnot(None),
                Project.logs != 'Version retrieved correctly',
                ~Project.logs.ilike('Something strange occured%'),
            )
        elif status == 'odd':
            query = query.filter(
                Project.logs.isnot(None),
                Project.logs != 'Version retrieved correctly',
                Project.logs.ilike('Something strange occured%'),
            )

        elif status == 'new':
            query = query.filter(
                Project.logs.is_(None),
            )
        elif status == 'never_updated':
            query = query.filter(
                Project.logs.isnot(None),
                Project.logs != 'Version retrieved correctly',
                Project.latest_version.is_(None),
            )

        if name:
            if '*' in name:
                name = name.replace('*', '%')
            else:
                name = '%' + name + '%'

            query = query.filter(
                Project.name.ilike(name),
            )

        if log:
            if '*' in log:
                log = log.replace('*', '%')
            else:
                log = '%' + log + '%'

            query = query.filter(
                Project.logs.ilike(log),
            )

        query = _paginate_query(query, page)

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def search(cls, session, pattern, distro=None, page=None, count=False):
        ''' Search the projects by their name or package name '''

        query1 = session.query(
            cls
        )

        if pattern:
            pattern = pattern.replace('_', '\_')
            if '*' in pattern:
                pattern = pattern.replace('*', '%')
            if '%' in pattern:
                query1 = query1.filter(
                    Project.name.ilike(pattern)
                )
            else:
                query1 = query1.filter(
                    Project.name == pattern
                )

        query2 = session.query(
            cls
        ).filter(
            Project.id == Packages.project_id
        )

        if pattern:
            if '%' in pattern:
                query2 = query2.filter(
                    Packages.package_name.ilike(pattern)
                )
            else:
                query2 = query2.filter(
                    Packages.package_name == pattern
                )

        if distro is not None:
            query1 = query1.filter(
                Project.id == Packages.project_id
            ).filter(
                sa.func.lower(Packages.distro) == sa.func.lower(distro)
            )

            query2 = query2.filter(
                sa.func.lower(Packages.distro) == sa.func.lower(distro)
            )

        query = query1.distinct().union(
            query2.distinct()
        ).order_by(
            cls.name
        )

        query = _paginate_query(query, page)

        if count:
            return query.count()
        else:
            return query.all()


class ProjectVersion(BASE):
    """
    Represents a version for a project.

    Attributes:
        project_id (sa.Integer): A foreign key to the project this version is
            associated with.
        project (Project): The project object with the ``project_id`` foreign
            key.
        version (str): A string representing a version.
        type (str): The version type (e.g. 'PEP-440', 'Semantic Version', etc.).
            This must match the polymorphic identity of a sub-class. SQLAlchemy
            will use this to determine the Python class to use when creating the
            object from the database row.
    """
    __tablename__ = 'projects_versions'

    project_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(
            "projects.id",
            ondelete="cascade",
            onupdate="cascade"),
        primary_key=True,
    )
    version = sa.Column(sa.String(50), primary_key=True)
    type = sa.Column(sa.String(50))

    project = sa.orm.relation('Project', backref='versions_obj')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': GENERIC_VERSION,
    }

    def __str__(self):
        """
        Return a parsed, string version of this instance's version.

        If parsing fails, the original version string is returned.
        """
        try:
            return str(self.parse())
        except anitya.lib.exceptions.InvalidVersion:
            return self.version

    def parse(self):
        """
        Parse the version string to an object representing the version.

        When sub-classing this class to support SQLAlchemy's single-table
        inheritance, this method must return an object that supports comparison
        operations, or re-implement the comparison functions.

        Returns:
            str: The version string. Sub-classes may return a different type.
        """
        # If there's a prefix set on the project, strip it if it's present
        version = self.version
        if self.project:
            prefix = self.project.version_prefix
            if prefix and self.version.startswith(prefix):
                version = self.version[len(prefix):]

        # Many projects prefix their tags with 'v', so strip it if it's present
        if _leading_v.match(version):
            version = version.lstrip('v')

        return version

    def prerelease(self):
        """
        Check if a version is a pre-release version.

        This basic version implementation does not have a concept of
        pre-releases.
        """
        return False

    def postrelease(self):
        """
        Check if a version is a post-release version.

        This basic version implementation does not have a concept of
        post-releases.
        """
        return False

    def newer(self, other_versions):
        """
        Check a version against a set of other versions to see if it's newer.

        Example:
            >>> version = ProjectVersion(version='1.1.0')
            >>> version.newer([ProjectVersion(version='1.0.0')])
            True
            >>> version.newer(['1.0.0', '0.0.1'])  # You can pass strings!
            True
            >>> version.newer(['1.2.0', '2.0.1'])
            False

        Args:
            other_versions (list): A list of version strings or ProjecVersion
                objects to check the `version` string against.

        Returns:
            bool: True if self is the newest version, ``False otherwise``.

        Raises:
            anitya.exceptions.InvalidVersion: if one or more of the version
                strings provided cannot be parsed.
        """
        if isinstance(other_versions, (ProjectVersion, str)):
            other_versions = [other_versions]
        cast_versions = []
        for version in other_versions:
            if not isinstance(version, type(self)):
                version = type(self)(version=version)
            cast_versions.append(version)
        return all([self.parse() > v.parse() for v in cast_versions])

    def __lt__(self, other):
        """Support < comparison via objects returned from :meth:`parse`"""
        try:
            parsed_self = self.parse()
        except exceptions.InvalidVersion:
            parsed_self = None
        try:
            parsed_other = other.parse()
        except exceptions.InvalidVersion:
            parsed_other = None

        # Handle the cases where one or both aren't parsable. Parsable versions
        # always sort higher than unparsable versions.
        if not parsed_self and not parsed_other:
            return self.version.__lt__(other.version)
        if not parsed_other:
            return False
        if not parsed_self:
            return True

        return parsed_self.__lt__(parsed_other)

    def __le__(self, other):
        """Support <= comparison via objects returned from :meth:`parse`"""
        try:
            parsed_self = self.parse()
        except exceptions.InvalidVersion:
            parsed_self = None
        try:
            parsed_other = other.parse()
        except exceptions.InvalidVersion:
            parsed_other = None

        # Handle the cases where one or both aren't parsable. Parsable versions
        # always sort higher than unparsable versions.
        if not parsed_self and not parsed_other:
            return self.version.__le__(other.version)
        if not parsed_other:
            return False
        if not parsed_self:
            return True
        return parsed_self.__le__(parsed_other)

    def __gt__(self, other):
        """Support > comparison via objects returned from :meth:`parse`"""
        try:
            parsed_self = self.parse()
        except exceptions.InvalidVersion:
            parsed_self = None
        try:
            parsed_other = other.parse()
        except exceptions.InvalidVersion:
            parsed_other = None

        # Handle the cases where one or both aren't parsable. Parsable versions
        # always sort higher than unparsable versions.
        if not parsed_self and not parsed_other:
            return self.version.__gt__(other.version)
        if not parsed_other:
            return True
        if not parsed_self:
            return False
        return parsed_self.__gt__(parsed_other)

    def __ge__(self, other):
        """Support >= comparison via objects returned from :meth:`parse`"""
        try:
            parsed_self = self.parse()
        except exceptions.InvalidVersion:
            parsed_self = None
        try:
            parsed_other = other.parse()
        except exceptions.InvalidVersion:
            parsed_other = None

        # Handle the cases where one or both aren't parsable. Parsable versions
        # always sort higher than unparsable versions.
        if not parsed_self and not parsed_other:
            return self.version.__ge__(other.version)
        if not parsed_other:
            return True
        if not parsed_self:
            return False
        return parsed_self.__ge__(parsed_other)

    def __eq__(self, other):
        """Support == comparison via objects returned from :meth:`parse`"""
        try:
            parsed_self = self.parse()
        except exceptions.InvalidVersion:
            parsed_self = None
        try:
            parsed_other = other.parse()
        except exceptions.InvalidVersion:
            parsed_other = None

        if not parsed_self or not parsed_other:
            return self.version.__eq__(other.version)
        return parsed_self.__eq__(parsed_other)


class Pep440Version(ProjectVersion):
    """
    A PEP-440-compliant version.
    """

    __mapper_args__ = {
        'polymorphic_identity': PEP440_VERSION,
    }

    def __str__(self):
        """Parse the version, allowing for LegacyVersions"""
        return str(pep440_version.parse(self.version))

    def parse(self):
        """
        Parse the version string.

        This accounts for and strips leading 'v' characters for version strings.

        Returns:
            packaging.version.Version: If the string is a PEP-440 compliant version.
            packaging.version.LegacyVersion: If the string isn't PEP-440 compliant,
                but can still be parsed.

        Raises:
            anitya.exceptions.InvalidVersion: if one or more of the version
                strings provided cannot be parsed.
        """
        version = super(Pep440Version, self).parse()
        try:
            return pep440_version.Version(version)
        except pep440_version.InvalidVersion as e:
            raise exceptions.InvalidVersion(version, e)

    def prerelease(self):
        """
        Check if a version is a pre-release version.

        Example:

            >>> version = Pep440Version(version='1.0a1')
            >>> version.prerelease()
            True
            >>> version = Pep440Version(version='1.0')
            >>> version.prerelease()
            False

        Returns:
            bool: True if this is a pre-release, False otherwise.
        """
        try:
            return self.parse().is_prerelease
        except pep440_version.InvalidVersion:
            return False

    def postrelease(self):
        """
        Check if a version is a post-release version.

        Example:
            >>> version = Pep440Version(version='1.0.post1')
            >>> version.postrelease()
            True
            >>> version = Pep440Version(version='1.0')
            >>> version.prerelease()
            False

        Returns:
            bool: True if this is a post-release, False otherwise.
        """
        try:
            return self.parse().is_postrelease
        except pep440_version.InvalidVersion:
            return False


class SemanticVersion(ProjectVersion):
    """
    Semantic version compliant version.
    """

    __mapper_args__ = {
        'polymorphic_identity': SEMANTIC_VERSION,
    }

    def parse(self):
        """
        Parse the version string.

        Returns:
            semantic_version.Version: A parsed version object.

        Raises:
            anitya.exceptions.InvalidVersion: if one or more of the version
                strings provided cannot be parsed.
        """
        version = super(SemanticVersion, self).parse()
        try:
            return semantic_version.Version(version, partial=True)
        except ValueError as e:
            raise exceptions.InvalidVersion(version, e)

    def prerelease(self):
        """
        Check if a version is a pre-release version.

        Example:

            >>> version = SemanticVersion(version='1.0.0-alpha')
            >>> version.prerelease()
            True
            >>> version = SemanticVersion(version='1.0.0')
            >>> version.prerelease()
            False
        """
        try:
            if self.parse().prerelease:
                return True
        except ValueError:
            pass
        return False

    def postrelease(self):
        """
        Check if a version is a post-release version.

        Returns:
            False: The semantic version scheme does not include the concept of
                post-releases.
        """
        return False


class ProjectFlag(BASE):
    __tablename__ = 'projects_flags'

    id = sa.Column(sa.Integer, primary_key=True)

    project_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(
            "projects.id",
            ondelete="cascade",
            onupdate="cascade")
    )

    reason = sa.Column(sa.Text, nullable=False)
    user = sa.Column(sa.String(200), index=True, nullable=False)
    state = sa.Column(sa.String(50), default='open', nullable=False)
    created_on = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    updated_on = sa.Column(sa.DateTime, server_default=sa.func.now(),
                           onupdate=sa.func.current_timestamp())

    project = sa.orm.relation('Project', backref='flags')

    def __repr__(self):
        return '<ProjectFlag(%s, %s, %s)>' % (self.project.name, self.user,
                                              self.state)

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
            output['reason'] = self.reason

        return output

    @classmethod
    def all(cls, session, page=None, count=False):
        query = session.query(
            ProjectFlag
        ).order_by(ProjectFlag.created_on)

        return query.all()

    @classmethod
    def search(cls, session, project_name=None, from_date=None, user=None,
               state=None, limit=None, offset=None, count=False):
        """ Return the list of the last Flag entries present in the database.

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
        query = session.query(
            cls
        )

        if project_name:
            query = query.filter(
                cls.project_id == Project.id
            ) .filter(
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
        query = session.query(
            cls
        ).filter(
            cls.id == flag_id)
        return query.first()


class Run(BASE):
    __tablename__ = 'runs'

    status = sa.Column(sa.String(20), primary_key=True)
    created_on = sa.Column(
        sa.DateTime, default=datetime.datetime.utcnow, primary_key=True)

    @classmethod
    def last_entry(cls, session):
        ''' Return the last log about the cron run. '''

        query = session.query(
            cls
        ).order_by(
            cls.created_on.desc()
        )
        return query.first()


#: A dictionary of available version types where the key is their name and the
#: value is the class.
version_classes = dict()
for _name, _object in inspect.getmembers(sys.modules[__name__]):
    if inspect.isclass(_object) and issubclass(_object, ProjectVersion):
        version_classes[_object.__mapper_args__['polymorphic_identity']] = _object
