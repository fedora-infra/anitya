#-*- coding: utf-8 -*-

""" Cnucnu mapping of python classes to Database Tables. """

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import datetime
import logging
import time

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

import cnucnu

BASE = declarative_base()

log = logging.getLogger(__name__)


def init(db_url, alembic_ini=None, debug=False, create=False):
    """ Create the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
        information with regards to the database engine, the host to
        connect to, the user and password and the database name.
          ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg alembic_ini, path to the alembic ini file. This is necessary
        to be able to use alembic correctly, but not for the unit-tests.
    :kwarg debug, a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a session that can be used to query the database.

    """
    engine = create_engine(db_url, echo=debug)

    if create:
        BASE.metadata.create_all(engine)

    # Source: http://docs.sqlalchemy.org/en/latest/dialects/sqlite.html
    # see section 'sqlite-foreign-keys'
    if db_url.startswith('sqlite:'):
        def _fk_pragma_on_connect(dbapi_con, con_record):
            dbapi_con.execute("PRAGMA foreign_keys=ON")
        sa.event.listen(engine, 'connect', _fk_pragma_on_connect)

    if alembic_ini is not None:  # pragma: no cover
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


def map_project_distro(
        session, project_id, distro_name, pkg_name, version_url, regex):
    """ Map the provided project into the provided distro with the
    specified version url and regex.
    """
    package = Packages.get(
        session, project_id, distro_name, pkg_name)
    if not package:
        package = Packages.create(
            session, project_id, pkg_name, distro_name, regex, version_url)

    if package.regex != regex:
        package.regex = regex
    if package.version_url != version_url:
        package.version_url = version_url

    session.add(package)
    return package


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
    def search(cls, session, project_name=None, from_date=None, limit=None,
               offset=None, count=False):
        """ Return the list of the last Log entries present in the database.

        :arg cls: the class object
        :arg session: the database session used to query the information.
        :kwarg project_name: the name of the project to restrict the logs to.
        :kwarg limit: limit the result to X row
        :kwarg offset: start the result at row X
        :kwarg from_date: the date from which to give the entries
        :kwarg count: a boolean to return the result of a COUNT query
            if true, returns the data if false (default).

        """
        query = session.query(
            cls
        )

        if count:
            return query.count()

        if project_name:
            query = query.filter(cls.project == project_name)

        if from_date:
            query = query.filter(cls.created_on <= from_date)

        query = query.order_by(cls.created_on.desc())

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()


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

        if page:
            try:
                page = int(page)
            except ValueError:
                page = None

        if page:
            limit = page * 50
            offset = (page - 1) * 50
            query = query.offset(offset).limit(limit)

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

        if page:
            try:
                page = int(page)
            except ValueError:
                page = None

        if page:
            limit = page * 50
            offset = (page - 1) * 50
            query = query.offset(offset).limit(limit)

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
        sa.String(200),
        sa.ForeignKey(
            "projects.id",
            ondelete="cascade",
            onupdate="cascade")
    )

    version_url = sa.Column(sa.String(200), nullable=False)
    regex = sa.Column(sa.String(200), nullable=False)

    version = sa.Column(sa.String(50))
    logs = sa.Column(sa.Text)

    package_name = sa.Column(sa.String(200))

    __table_args__ = (
        sa.UniqueConstraint('distro', 'package_name'),
    )

    project = sa.orm.relation('Project')

    @property
    def full_version_url(self):
        url = cnucnu.convert_url(self.package_name, self.version_url)
        return url

    def __repr__(self):
        return '<Packages(%s, %s: %s)>' % (
            self.project_id, self.distro, self.package_name)

    def __json__(self):
        return dict(
            package_name=self.package_name,
            project=self.project.name,
            distro=self.distro,
            regex=self.regex,
            version_url=self.version_url,
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
    def create(cls, session, project_id, package_name, distro, regex,
               version_url):
        """ Create a Package object. """
        distro = Distro.get_or_create(session, distro)
        pkg = cls(
            project_id=project_id,
            distro=distro.name,
            package_name=package_name,
            version_url=version_url,
            regex=regex
        )
        session.add(pkg)
        session.flush()
        return pkg

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
    __tablename__ = 'projects'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(200), nullable=False, index=True)
    homepage = sa.Column(sa.String(200), nullable=False, unique=True)

    updated_on = sa.Column(sa.DateTime, server_default=sa.func.now(),
                           onupdate=sa.func.current_timestamp())
    created_on = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    packages = sa.orm.relation('Packages')

    def __repr__(self):
        return '<Project(%s, %s)>' % (self.name, self.homepage)

    def __json__(self):
        return dict(
            name=self.name,
            homepage=self.homepage,
            created_on=time.mktime(self.created_on.timetuple()),
            updated_on=time.mktime(self.updated_on.timetuple()),
            #packages=[pkg.__json__() for pkg in self.packages]
        )

    @classmethod
    def by_name(cls, session, name):
        return session.query(cls).filter_by(name=name).all()

    @classmethod
    def by_id(cls, session, project_id):
        return session.query(cls).filter_by(id=project_id).first()

    get = by_id

    @classmethod
    def by_homepage(cls, session, homepage):
        return session.query(cls).filter_by(homepage=homepage).first()

    @classmethod
    def all(cls, session, page=None, count=False):
        query = session.query(Project).order_by(sa.func.lower(Project.name))

        if page:
            try:
                page = int(page)
            except ValueError:
                page = None

        if page:
            limit = page * 50
            offset = (page - 1) * 50
            query = query.offset(offset).limit(limit)

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def search(cls, session, pattern, page=None, count=False):
        ''' Search the projects by their name or package name '''

        if '*' in pattern:
            pattern = pattern.replace('*', '%')

        query = session.query(
            cls
        ).filter(
            sa.or_(
                cls.name.like(pattern),
            )
        ).order_by(
            cls.name
        ).distinct()

        if page:
            try:
                page = int(page)
            except ValueError:
                page = None

        if page:
            limit = page * 50
            offset = (page - 1) * 50
            query = query.offset(offset).limit(limit)

        if count:
            return query.count()
        else:
            return query.all()

    @classmethod
    def get_or_create(cls, session, name, homepage):
        project = cls.by_homepage(session, homepage)
        if not project:
            project = cls(name=name, homepage=homepage)
            session.add(project)
            session.flush()
        return project
