from datetime import datetime
import json
import os
import sys
import transaction

from pyramid.paster import (
    get_appsettings,
    setup_logging,
)

from pyramid.scripts.common import parse_vars

from pyramid_todo.models.meta import Base
from pyramid_todo.security import hasher
from pyramid_todo.models import (
    get_engine,
    get_session_factory,
    get_tm_session,
    Profile,
    Task
)


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri> [var=value]\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) < 2:
        usage(argv)
    config_uri = argv[1]
    options = parse_vars(argv[2:])
    setup_logging(config_uri)
    settings = get_appsettings(config_uri, options=options)
    settings['sqlalchemy.url'] = os.environ.get('DATABASE_URL', '')

    engine = get_engine(settings)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    session_factory = get_session_factory(engine)

    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)

        person = Profile(
            username='nhuntwalker',
            email='nhuntwalker@gmail.com',
            password=hasher.hash('password'),
            date_joined=datetime.now(),
        )
        dbsession.add(person)

    with transaction.manager:
        dbsession = get_tm_session(session_factory, transaction.manager)

        file_path = os.path.join(os.path.dirname(__file__), 'tasks.json')
        fmt = '%m/%d/%Y %H:%M:%S %p'

        for task in json.loads(open(file_path).read()):
            task = Task(
                name=task['title'],
                note=task['note'],
                creation_date=datetime.strptime(task['creation_date'], fmt) if task['creation_date'] else None,
                due_date=datetime.strptime(task['due_date'], fmt) if task['due_date'] else None,
                completed=task['completed'],
                profile_id=dbsession.query(Profile).first().id,
                profile=dbsession.query(Profile).first(),
            )
            dbsession.add(task)
