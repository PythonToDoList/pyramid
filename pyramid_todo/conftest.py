"""Test Configuration of the Pyramid To Do List."""
from datetime import datetime
from faker import Faker
import os
from pyramid import testing
import pytest
import random
import transaction

from pyramid_todo.models import (
    Task, Profile, get_tm_session
)
from pyramid_todo.models.meta import Base
from pyramid_todo.security import hasher


DATE_FMT = '%d/%m/%Y %H:%M:%S'
FAKE = Faker()


@pytest.fixture(scope="session")
def configuration(request):
    """Set up a Configurator instance."""
    config = testing.setUp(settings={
        'sqlalchemy.url': os.environ.get('TEST_DB', '')
    })
    config.include("pyramid_todo.models")
    config.include("pyramid_todo.routes")

    def teardown():
        testing.tearDown()

    request.addfinalizer(teardown)
    return config


@pytest.fixture
def db_session(configuration, request):
    """Create a session for interacting with the test database."""
    SessionFactory = configuration.registry["dbsession_factory"]
    session = SessionFactory()
    engine = session.bind
    Base.metadata.create_all(engine)

    def teardown():
        session.transaction.rollback()
        Base.metadata.drop_all(engine)

    request.addfinalizer(teardown)
    return session


@pytest.fixture
def dummy_request(db_session):
    """Instantiate a fake HTTP Request, complete with a database session.

    This is a function-level fixture, so every new request will have a
    new database session.
    """
    return testing.DummyRequest(dbsession=db_session)


@pytest.fixture
def profile(db_session):
    """Instantiate a new profile, add it to the database, and return it."""
    profile = Profile(
        username='some_person',
        email=FAKE.email(),
        password=hasher.hash(FAKE.password()),
        date_joined=datetime.strptime('01/01/2010', '%m/%d/%Y')
    )
    db_session.add(profile)
    db_session.commit()
    return profile


@pytest.fixture(scope="session")
def several_profiles():
    """Instantiate a bunch of profiles and return them."""
    profiles = []
    for i in range(20):
        profiles.append(Profile(
            username=FAKE.first_name(),
            email=FAKE.email(),
            password=hasher.hash('potato'),
            date_joined=datetime.strptime('01/01/2010', '%m/%d/%Y')
        ))
    profiles.append(Profile(
        username='nhuntwalker',
        email=FAKE.email(),
        password=hasher.hash('potato'),
        date_joined=datetime.strptime('01/01/2010', '%m/%d/%Y')
    ))
    return profiles


def main(global_config, **settings):
    """Set up configuration for the test application."""
    from pyramid.config import Configurator
    settings['sqlalchemy.url'] = os.environ.get('TEST_DB', '')
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.include('pyramid_todo.routes')
    config.include('pyramid_todo.models')
    config.include('pyramid_todo.security')
    config.include('pyramid_todo.utils')
    config.scan()
    return config.make_wsgi_app()


@pytest.fixture(scope='session')
def testapp(request):
    """Create an instance of webtests TestApp for testing routes.

    With the alchemy scaffold we need to add to our test application the
    setting for a database to be used for the models.

    We have to then set up the database by starting a database session.
    Finally we have to create all of the necessary tables that our app
    normally uses to function.

    The scope of the fixture is session-level, so every test session will use
    the same testapp instance.
    """
    from webtest import TestApp
    app = main({}, **{})

    SessionFactory = app.registry["dbsession_factory"]
    engine = SessionFactory().bind
    Base.metadata.create_all(bind=engine)

    def tearDown():
        Base.metadata.drop_all(bind=engine)

    request.addfinalizer(tearDown)

    return TestApp(app)


@pytest.fixture(scope='session')
def fill_db(testapp, several_profiles):
    """Fill the database with model instances."""
    SessionFactory = testapp.app.registry["dbsession_factory"]
    with transaction.manager:
        dbsession = get_tm_session(SessionFactory, transaction.manager)
        dbsession.add_all(several_profiles)

    with transaction.manager:
        dbsession = get_tm_session(SessionFactory, transaction.manager)
        many_tasks = []
        for i in range(200):
            profile = random.choice(dbsession.query(Profile).all())
            many_tasks.append(Task(
                name=FAKE.words(3),
                note=FAKE.words(100),
                creation_date=FAKE.date_time(),
                due_date=FAKE.date_time(),
                profile_id=profile.id,
                profile=profile
            ))
        dbsession.add_all(many_tasks)


@pytest.fixture
def empty_db(testapp):
    """Drop existing database tables and create fresh empty ones."""
    SessionFactory = testapp.app.registry["dbsession_factory"]
    engine = SessionFactory().bind
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
