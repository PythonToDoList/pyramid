"""Tests of the Pyramid To Do List."""
from datetime import datetime
from faker import Faker
from pyramid.httpexceptions import (
    HTTPNotFound
)
from pyramid_todo.models import (
    Task, Profile
)


DATE_FMT = '%d/%m/%Y %H:%M:%S'
FAKE = Faker()
def parse_cookies(cookies_list):
    """Parse response cookies into individual key-value pairs."""
    return dict(map(lambda x: x.split('='), cookies_list.split('; ')))    


def test_profile_to_dict_is_dict_of_profile_attributes(profile):
    """to_dict method of Profile object returns dict of profile attributes."""
    as_dict = profile.to_dict()
    assert 'id' in as_dict and as_dict['id'] == profile.id
    assert 'username' in as_dict and as_dict['username'] == profile.username
    assert 'email' in as_dict and as_dict['email'] == profile.email
    assert 'date_joined' in as_dict and as_dict['date_joined'] == profile.date_joined.strftime(DATE_FMT)
    assert 'tasks' in as_dict and as_dict['tasks'] == []


def test_task_to_dict_is_dict_of_task_attributes(db_session, profile):
    """to_dict method of Task object returns dict of task attributes."""
    task = Task(
        name=FAKE.words(3),
        note=FAKE.words(100),
        creation_date=datetime.strptime('01/01/2010', '%m/%d/%Y'),
        due_date=None,
        profile_id=profile.id,
        profile=profile
    )
    db_session.add(task)
    db_session.commit()
    as_dict = task.to_dict()
    assert 'id' in as_dict and as_dict['id'] == task.id
    assert 'name' in as_dict and as_dict['name'] == task.name
    assert 'note' in as_dict and as_dict['note'] == task.note
    assert 'creation_date' in as_dict and as_dict['creation_date'] == task.creation_date.strftime(DATE_FMT)
    assert 'due_date' in as_dict and as_dict['due_date'] == task.due_date
    assert 'completed' in as_dict and as_dict['completed'] == task.completed
    assert 'profile_id' in as_dict and as_dict['profile_id'] == task.profile_id


def test_task_assigned_to_profile_in_profile_task_list(db_session, profile):
    """When a Task has been assigned to a Profile, that Profile contains the Task."""
    task = Task(
        name=FAKE.words(3),
        note=FAKE.words(100),
        creation_date=datetime.strptime('01/01/2010', '%m/%d/%Y'),
        due_date=None,
        profile_id=profile.id,
        profile=profile
    )
    db_session.add(task)
    db_session.commit()
    assert task in profile.tasks


def test_get_profile_returns_none_with_no_profiles(dummy_request):
    """get_profile will attempt to find the given profile but finds none if none exist."""
    from pyramid_todo.views.main import get_profile
    assert get_profile(dummy_request, 'nhuntwalker') is None


def test_get_profile_returns_none_with_wrong_profile(db_session, dummy_request, profile):
    """get_profile will attempt to find the profile to match the given username but return None if no profile exists."""
    from pyramid_todo.views.main import get_profile
    assert get_profile(dummy_request, 'nhuntwalker') is None


def test_get_profile_returns_correct_profile(db_session, dummy_request):
    """get_profile will return the profile matching the given username."""
    from pyramid_todo.views.main import get_profile
    db_session.add(Profile(
        username='nhuntwalker',
        email=FAKE.email(),
        password=FAKE.password(),
        date_joined=FAKE.date_time()
    ))
    db_session.commit()
    profile = get_profile(dummy_request, 'nhuntwalker')
    assert profile is not None
    assert isinstance(profile, Profile)
    assert profile.username == 'nhuntwalker'


def test_info_view_returns_dict_of_routes_and_methods(dummy_request):
    """The info_view should show information about available routes and allowed HTTP methods."""
    from pyramid_todo.views.main import info_view
    response = info_view(dummy_request)
    assert response == {
        'info': 'GET /api/v1',
        'register': 'POST /api/v1/accounts',
        'single profile detail': 'GET /api/v1/accounts/<username>',
        'edit profile': 'PUT /api/v1/accounts/<username>',
        'delete profile': 'DELETE /api/v1/accounts/<username>',
        'login': 'POST /api/v1/accounts/login',
        'logout': 'GET /api/v1/accounts/logout',
        "user's tasks": 'GET /api/v1/accounts/<username>/tasks',
        "create task": 'POST /api/v1/accounts/<username>/tasks',
        "task detail": 'GET /api/v1/accounts/<username>/tasks/<id>',
        "task update": 'PUT /api/v1/accounts/<username>/tasks/<id>',
        "delete task": 'DELETE /api/v1/accounts/<username>/tasks</id>'
    }


def test_tasks_list_with_no_users_returns_notfound(dummy_request):
    """Cannot get tasks from user when no users exist."""
    from pyramid_todo.views.main import tasks_list
    dummy_request.matchdict['username'] = 'nhuntwalker'
    response = tasks_list(dummy_request)
    assert isinstance(response, dict)
    assert response == {'error': 'The profile does not exist'}


def test_tasks_list_with_bad_username_returns_notfound(dummy_request, profile):
    """Cannot get tasks if the nonexistent user is entered."""
    from pyramid_todo.views.main import tasks_list
    dummy_request.matchdict['username'] = 'nhuntwalker'
    response = tasks_list(dummy_request)
    assert isinstance(response, dict)
    assert response == {'error': 'The profile does not exist'}


def test_successful_login_adds_auth_tkt_cookie(testapp, fill_db):
    data_dict = {
        'username': 'nhuntwalker',
        'password': 'potato'
    }
    response = testapp.post('/api/v1/accounts/login', data_dict)
    cookies = parse_cookies(response.headers['Set-Cookie'])
    assert response.status_code == 202
    assert not (cookies['auth_tkt'] == '')


def test_bad_username_prevents_login(testapp, fill_db):
    data_dict = {
        'username': 'flergtheblerg',
        'password': 'potato'
    }
    response = testapp.post('/api/v1/accounts/login', data_dict, status=400)
    assert response.status_code == 400


def test_missing_fields_prevents_login(testapp, fill_db):
    data_dict = {
        'username': 'flergtheblerg'
    }
    response = testapp.post('/api/v1/accounts/login', data_dict, status=400)
    assert response.status_code == 400


def test_logging_out_removes_auth_tks_from_headers(testapp, fill_db):
    data_dict = {
        'username': 'nhuntwalker',
        'password': 'potato'
    }
    response = testapp.post('/api/v1/accounts/login', data_dict)
    cookies = parse_cookies(response.headers['Set-Cookie'])
    assert not (cookies['auth_tkt'] == '')

    response = testapp.get('/api/v1/accounts/logout')
    cookies = parse_cookies(response.headers['Set-Cookie'])
    assert cookies['auth_tkt'] == ''


def test_successful_creates_profile(testapp):
    data_dict = {
        'username': 'nicholas',
        'password': 'potato',
        'password2': 'potato',
        'email': 'nicholas@huntwalker.com',
    }
    testapp.post('/api/v1/accounts', data_dict)
    response = testapp.get('/api/v1/accounts/nicholas')
    assert response.status_code == 200
    assert 'nicholas@huntwalker.com' in response.ubody


def test_cant_register_same_username_twice(testapp, fill_db):
    data_dict = {
        'username': 'nhuntwalker',
        'password': 'potato',
        'password2': 'potato',
        'email': FAKE.email(),
    }
    response = testapp.post('/api/v1/accounts', data_dict, status=400)
    assert response.status_code == 400
    assert response.json == {'error': 'Username "nhuntwalker" is already taken'}


def test_cant_register_mismatched_passwords(testapp):
    data_dict = {
        'username': 'meeseeks',
        'password': 'potato',
        'password2': 'potahto',
        'email': FAKE.email(),
    }
    response = testapp.post('/api/v1/accounts', data_dict, status=400)
    assert response.status_code == 400
    assert response.json == {'error': "Passwords don't match"}


def test_cant_register_missing_fields(testapp):
    data_dict = {
        'username': 'meeseeks',
        'password': 'potato',
        'password2': 'potahto',
    }
    response = testapp.post('/api/v1/accounts', data_dict, status=400)
    assert response.status_code == 400
    assert response.json == {'error': 'Some fields are missing'}


def test_unauthenticated_user_cant_delete_existing_profile(testapp):
    response = testapp.delete('/api/v1/accounts/nhuntwalker', status=403)
    assert response.json == {'error': 'You do not have permission to access this profile.'}


def test_authenticated_user_can_delete_existing_profile(testapp):
    data_dict = {
        'username': 'meeseeks',
        'password': 'potato',
        'password2': 'potato',
        'email': 'mr@meeseeks.com'
    }
    testapp.post('/api/v1/accounts', data_dict)
    response = testapp.delete('/api/v1/accounts/meeseeks', status=204)
    assert response.json_body is None


def test_authenticated_user_can_edit_existing_profile(testapp):
    data_dict = {
        'username': 'meeseeks',
        'password': 'potato',
        'password2': 'potato',
        'email': 'mr@meeseeks.com'
    }
    testapp.post('/api/v1/accounts', data_dict)
    response = testapp.put('/api/v1/accounts/meeseeks', {'email': 'mee@seeks.com'})
    assert response.json['profile']['email'] == 'mee@seeks.com'


def test_user1_cannot_edit_user2_profile(testapp):
    user1 = {'username': 'foobar', 'password': 'potato', 'password2': 'potato', 'email': 'foo@bar.com'}
    user2 = {'username': 'barfoo', 'password': 'potato', 'password2': 'potato', 'email': 'bar@foo.com'}

    testapp.post('/api/v1/accounts', user1)
    testapp.post('/api/v1/accounts', user2)

    response = testapp.put('/api/v1/accounts/foobar', {'username': 'tugboat'}, status=403)
    assert response.json == {'error': 'You do not have permission to access this profile.'}
