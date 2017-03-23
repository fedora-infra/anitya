# -*- coding: utf-8 -*-

"""
 (c) 2014-2016 - Copyright Red Hat Inc

 Authors:
   Pierre-Yves Chibon <pingou@pingoured.fr>

anitya mapping of python classes to Database Tables.
"""

import datetime
import logging
import time

__requires__ = ['SQLAlchemy >= 0.7']  # NOQA
import pkg_resources  # NOQA

import sqlalchemy as sa
from sqlalchemy.orm import validates
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound

import anitya


BASE = declarative_base()


_log = logging.getLogger(__name__)


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
    __tablename__ = 'projects'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(200), nullable=False, index=True)
    homepage = sa.Column(sa.String(200), nullable=False)

    backend = sa.Column(sa.String(200), default='custom')
    ecosystem_name = sa.Column(sa.String(200), nullable=True, index=True)
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

    @validates('backend')
    def validate_backend(self, key, value):
        # At the moment I have to stash this here because there's a circular
        # import. It can be resolved after the config is decoupled from Flask:
        # https://github.com/release-monitoring/anitya/pull/450
        from .plugins import BACKEND_PLUGINS
        if value not in BACKEND_PLUGINS.get_plugin_names():
            raise ValueError('Backend "{}" is not supported.'.format(value))
        return value

    @validates('ecosystem_name')
    def validate_ecosystem_name(self, key, value):
        # At the moment I have to stash this here because there's a circular
        # import. It can be resolved after the config is decoupled from Flask:
        # https://github.com/release-monitoring/anitya/pull/450
        from .plugins import ECOSYSTEM_PLUGINS
        if value and value not in ECOSYSTEM_PLUGINS.get_plugin_names():
            raise ValueError('Ecosystem "{}" is not supported.'.format(value))
        return value

    @property
    def versions(self):
        ''' Return list of all versions stored, sorted from newest to oldest.
        '''
        return list(reversed(anitya.order_versions(
            [v.version for v in self.versions_obj])))

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
            query = session.query(cls)
            query = query.filter(cls.name == name, cls.ecosystem_name == ecosystem)
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
