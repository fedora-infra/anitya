# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

anitya mapping of python classes to Database Tables.
"""


__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import datetime
import logging
import time

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base


BASE = declarative_base()

log = logging.getLogger(__name__)


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
            query = query.filter(cls.created_on >= from_date)

        query = query.order_by(cls.created_on.desc())

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()


class Backend(BASE):
    __tablename__ = 'backends'

    name = sa.Column(sa.String(200), primary_key=True)

    @classmethod
    def all(cls, session):
        query = session.query(cls).order_by(cls.name)
        return query.all()

    @classmethod
    def by_name(cls, session, name):
        return session.query(cls).filter_by(name=name).first()

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
    __tablename__ = 'projects'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(200), nullable=False, index=True)
    homepage = sa.Column(sa.String(200), nullable=False)

    backend = sa.Column(
        sa.String(200),
        sa.ForeignKey(
            "backends.name",
            ondelete="cascade",
            onupdate="cascade"),
        default='custom',
    )
    version_url = sa.Column(sa.String(200), nullable=True)
    regex = sa.Column(sa.String(200), nullable=True)

    latest_version = sa.Column(sa.String(50))
    logs = sa.Column(sa.Text)

    updated_on = sa.Column(sa.DateTime, server_default=sa.func.now(),
                           onupdate=sa.func.current_timestamp())
    created_on = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    packages = sa.orm.relation('Packages')

    __table_args__ = (
        sa.UniqueConstraint('name', 'homepage'),
    )

    @property
    def versions(self):
        ''' Return the list of all versions stored. '''
        return sorted([version.version for version in self.versions_obj])

    def __repr__(self):
        return '<Project(%s, %s)>' % (self.name, self.homepage)

    def __json__(self):
        return dict(
            name=self.name,
            homepage=self.homepage,
            regex=self.regex,
            backend=self.backend,
            version_url=self.version_url,
            version=self.latest_version,
            created_on=time.mktime(self.created_on.timetuple()),
            updated_on=time.mktime(self.updated_on.timetuple()),
        )

    @classmethod
    def get_or_create(cls, session, name, homepage, backend='custom'):
        project = cls.by_name_and_homepage(session, name, homepage)
        if not project:
            #print "Creating %s/%s(%s)" % (name, homepage, backend)

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
        return session.query(cls)\
            .filter_by(name=name)\
            .filter_by(homepage=homepage).first()

    @classmethod
    def all(cls, session, page=None, count=False):
        query = session.query(
            Project
        ).order_by(
            sa.func.lower(Project.name)
        )

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


class ProjectVersion(BASE):
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

    project = sa.orm.relation('Project', backref='versions_obj')
