"""View functions."""
from datetime import datetime

from passlib.hash import pbkdf2_sha256 as hasher
from pyramid.security import NO_PERMISSION_REQUIRED, remember, forget
from pyramid.view import view_config

from pyramid_todo.models import Task, Profile
from pyramid_todo import security


def get_profile(request, username):
    """Check if the requested profile exists."""
    return request.dbsession.query(Profile).filter(
        Profile.username == username
    ).first()


def get_json_response(request):
    """Retrieve the response object with content_type of json."""
    response = request.response
    response.headers.extend({'Content-Type': 'application/json'})
    return response


@view_config(
    route_name='info', renderer='json', permission=NO_PERMISSION_REQUIRED, request_method="GET"
)
def info_view(request):
    """List of routes for this API."""
    return {
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
        "delete task": 'DELETE /api/v1/accounts/<username>/tasks/<id>'
    }


@view_config(route_name='tasks', renderer='json', request_method='GET')
def tasks_list(request):
    """List tasks for one user."""
    response = get_json_response(request)
    profile = get_profile(request, request.matchdict['username'])
    if profile:
        if security.is_user(request):
            username = request.matchdict['username']
            tasks = request.dbsession.query(Task).filter(
                Task.profile == profile
            ).all()
            return {
                'username': username,
                'tasks': [task.to_dict() for task in tasks],
            }
        response.status_code = 403
        return {'error': 'You do not have permission to access this data.'}

    response.status_code = 404
    return {'error': 'The profile does not exist'}


@view_config(route_name='tasks', renderer='json', request_method='POST')
def task_create(request):
    """Create a new task for this user."""
    response = get_json_response(request)
    profile = get_profile(request, request.matchdict['username'])
    if profile:
        if security.is_user(request):
            due_date = request.POST['due_date']
            try:
                task = Task(
                    name=request.POST['name'],
                    note=request.POST['note'],
                    creation_date=datetime.now(),
                    due_date=datetime.strptime(due_date, '%d/%m/%Y %H:%M:%S') if due_date else None,
                    completed=request.POST['completed'],
                    profile_id=profile.id,
                    profile=profile
                )
                request.dbsession.add(task)
                response.status_code = 201
                return {'msg': 'posted'}
            except KeyError:
                response.status_code = 400
                return {'error': 'Some fields are missing'}

        response.status_code = 403
        return {'error': 'You do not have permission to access this data.'}

    response.status_code = 404
    return {'error': 'The profile does not exist'}


@view_config(route_name='one_task', renderer='json', request_method='GET')
def task_detail(request):
    """Get task detail for one user given a task ID."""
    response = get_json_response(request)
    if security.is_user(request):
        username = request.matchdict['username']
        profile = get_profile(request, username)
        task = request.dbsession.query(Task).get(request.matchdict['id'])
        if task in profile.tasks:
            return {'username': username, 'task': task.to_dict()}

        response.status_code = 404
        return {'username': username, 'task': None}

    response.status_code = 403
    return {'error': 'You do not have permission to access this data.'}


@view_config(route_name='one_task', renderer='json', request_method='PUT')
def task_update(request):
    """Update task information for one user's task."""
    response = get_json_response(request)
    if security.is_user(request):
        username = request.matchdict['username']
        profile = get_profile(request, username)
        task = request.dbsession.query(Task).get(request.matchdict['id'])
        if task in profile.tasks:
            if 'name' in request.POST and request.POST['name']:
                task.name = request.POST['name']
            if 'note' in request.POST:
                task.note = request.POST['note']
            if 'due_date' in request.POST:
                due_date = request.POST['due_date']
                task.due_date = datetime.strptime(due_date, '%d/%m/%Y %H:%M:%S') if due_date else None
            if 'completed' in request.POST:
                task.due_date = request.POST['completed']
            request.dbsession.add(task)
            request.dbsession.flush()
            return {'username': username, 'task': task.to_dict()}

        response.status_code = 404
        return {'username': username, 'task': None}

    response.status_code = 403
    return {'error': 'You do not have permission to access this data.'}


@view_config(route_name='one_task', renderer='json', request_method='DELETE')
def task_delete(request):
    """Delete a task."""
    response = get_json_response(request)
    if security.is_user(request):
        username = request.matchdict['username']
        profile = get_profile(request, username)
        task = request.dbsession.query(Task).get(request.matchdict['id'])
        if task in profile.tasks:
            request.dbsession.delete(task)
        return {'username': username, 'msg': 'Deleted.'}

    response.status_code = 403
    return {'error': 'You do not have permission to access this profile.'}


@view_config(route_name='one_profile', renderer='json', request_method='GET')
def profile_detail(request):
    """Get detail for one profile."""
    response = get_json_response(request)
    if security.is_user(request):
        profile = get_profile(request, request.matchdict['username'])
        return profile.to_dict()

    response.status_code = 403
    return {'error': 'You do not have permission to access this profile.'}


@view_config(route_name='one_profile', renderer='json', request_method='PUT')
def profile_update(request):
    """Update an existing profile."""
    response = get_json_response(request)
    if security.is_user(request):
        profile = get_profile(request, request.matchdict['username'])
        if 'username' in request.POST and request.POST['username'] != '':
            profile.username = request.POST['username']
        if 'email' in request.POST and request.POST['email'] != '':
            profile.email = request.POST['email']
        if 'password' in request.POST and 'password2' in request.POST and request.POST['password'] == request.POST['password2'] and request.POST['password'] != '':
            profile.password = hasher.hash(request.POST['password'])
        request.dbsession.add(profile)
        request.dbsession.flush()
        response.status_code = 202
        return {
            'msg': 'Profile updated.',
            'profile': profile.to_dict(),
            'username': profile.username
        }

    response.status_code = 403
    return {'error': 'You do not have permission to access this profile.'}


@view_config(route_name='one_profile', renderer='json', request_method='DELETE')
def profile_delete(request):
    """Delete an existing profile."""
    response = get_json_response(request)
    if security.is_user(request):
        profile = get_profile(request, request.matchdict['username'])
        request.dbsession.delete(profile)
        response.status_code = 204
        response.headers = forget(request)
        return

    response.status_code = 403
    return {'error': 'You do not have permission to access this profile.'}


@view_config(
    route_name='login', renderer='json', request_method='POST',
    permission=NO_PERMISSION_REQUIRED
)
def login(request):
    """Authenticate a user."""
    needed = ['username', 'password']
    response = get_json_response(request)
    if all([key in request.POST for key in needed]):
        if security.authenticate_user(request):
            headers = remember(request, request.POST['username'])
            response.status_code = 202
            response.headers.extend(headers)
            return {
                'msg': 'Authenticated'
            }
        response.status_code = 400
        return {'error': 'Incorrect username/password combination.'}
    response.status_code = 400
    return {'error': 'Some fields are missing'}


@view_config(route_name='logout', renderer='json', request_method="GET")
def logout(request):
    """Remove user authentication from requests."""
    headers = forget(request)
    request.response.headers = headers
    request.response.headers.extend({'Content-Type': 'application/json'})
    return {'msg': 'Logged out.'}


@view_config(
    route_name='register', renderer='json', request_method='POST',
    permission=NO_PERMISSION_REQUIRED
)
def register(request):
    """Add a new user profile if it doesn't already exist."""
    needed = ['username', 'email', 'password', 'password2']
    response = get_json_response(request)
    if all([key in request.POST for key in needed]):
        username = request.POST['username']
        profile = get_profile(request, username)
        if not profile:
            if request.POST['password'] == request.POST['password2']:
                new_profile = Profile(
                    username=username,
                    email=request.POST['email'],
                    password=hasher.hash(request.POST['password']),
                    date_joined=datetime.now(),
                )
                request.dbsession.add(new_profile)
                headers = remember(request, username)
                response.status_code = 201
                response.headers.extend(headers)
                return {"msg": 'Profile created'}

            response.status_code = 400
            return {"error": "Passwords don't match"}

        response.status_code = 400
        return {'error': f'Username "{username}" is already taken'}

    response.status_code = 400
    return {'error': 'Some fields are missing'}