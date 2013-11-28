#-*- coding: utf-8 -*-

""" Cnucnu mapping of python classes to Database Tables. """

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import datetime
import logging

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

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

    # This... "causes problems"
    #if db_url.startswith('sqlite:'):
    #    def _fk_pragma_on_connect(dbapi_con, con_record):
    #        dbapi_con.execute('pragma foreign_keys=ON')
    #    sa.event.listen(engine, 'connect', _fk_pragma_on_connect)

    if alembic_ini is not None:  # pragma: no cover
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession



class Project(BASE):
    __tablename__ = 'projects'

    name = sa.Column(sa.String(200), primary_key=True)
    homepage = sa.Column(sa.String(200), unique=True, nullable=False)
    version_url = sa.Column(sa.String(200), nullable=False)
    regex = sa.Column(sa.String(200), nullable=False)
    fedora_name = sa.Column(sa.String(200))
    debian_name = sa.Column(sa.String(200))

    version = sa.Column(sa.String(50))
    logs = sa.Column(sa.Text)

    updated_on = sa.Column(sa.DateTime, server_default=sa.func.now(),
                           onupdate=sa.func.current_timestamp())
    created_on = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)

    @classmethod
    def by_name(cls, session, name):
        return session.query(cls).filter_by(name=name).first()

    get = by_name

    @classmethod
    def all(cls, session, page=None, count=False):
        query = session.query(cls).order_by(cls.name)

        if page:
            try: page = int(page)
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
    def get_or_create(cls, session, name, homepage, version_url, regex,
                      fedora_name=None, debian_name=None):
        project = cls.by_name(session, name)
        if not project:
            project = cls(
                name=name,
                homepage=homepage,
                version_url=version_url,
                regex=regex,
                fedora_name=fedora_name,
                debian_name=debian_name
            )
            session.add(project)
            session.flush()
        return project
