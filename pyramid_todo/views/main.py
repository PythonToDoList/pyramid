"""View functions."""
from datetime import datetime
import json
from passlib.hash import pbkdf2_sha256 as hasher
from pyramid.httpexceptions import (
    HTTPOk, HTTPAccepted, HTTPCreated, HTTPNoContent,
    HTTPBadRequest, HTTPForbidden, HTTPNotFound
)
from pyramid.security import NO_PERMISSION_REQUIRED, remember, forget
from pyramid.view import view_config

from pyramid_todo.models import Profile, Task
from pyramid_todo import security


def get_profile(request, username):
    """Check if the requested profile exists."""
    return request.dbsession.query(Profile).filter(
        Profile.username == username
    ).first()


@view_config(
    route_name='info', renderer='json', permission=NO_PERMISSION_REQUIRED
)
def info_view(request):
    """List of routes for this API."""
    return {
        'info': '/api/v1',
        'list profiles': '/api/v1/accounts/',
        'one profile': '/api/v1/accounts/<username>',
        'tasks': '/api/v1/accounts/<username>/tasks',
        'one task': '/api/v1/accounts/<username>/tasks/<task_id>',
        'login': '/api/v1/accounts/login',
        'logout': '/api/v1/accounts/logout',
    }


@view_config(route_name='tasks', renderer='json')
def tasks_list(request):
    """List tasks for one user."""
    profile = get_profile(request, request.matchdict['username'])
    if profile:
        username = request.matchdict['username']
        if request.method == "GET":
            tasks = request.dbsession.query(Task).filter(
                Task.profile == profile
            ).all()
            return {
                'username': username,
                'tasks': [task.to_dict() for task in tasks],
            }

        elif request.method == "POST":
            due_date = f'{request.POST["due_date"]} {request.POST["due_time"]}'
            task = Task(
                name=request.POST['name'],
                note=request.POST['note'],
                creation_date=datetime.now(),
                due_date=datetime.strptime(due_date, '%d/%m/%Y %H:%M:%S') if request.POST['due_date'] else None,
                completed=request.POST['completed'],
                profile_id=profile.id,
                profile=profile
            )
            request.dbsession.add(task)
            return {'msg': 'post'}
    return {
        'error': 'Invalid username'
    }


@view_config(route_name='one_task', renderer='json', request_method='GET')
def task_detail(request):
    """Get task detail for one user given a task ID."""
    if is_user(request):
        username = request.matchdict['username']
        profile = get_profile(request, username)
        task = request.dbsession.query(Task).get(request.matchdict['id'])
        if task in profile.tasks:
            return HTTPOk(
                body=json.dumps({'username': username, 'task': task.to_dict()}),
                headers=request.headers
            )
        return HTTPNotFound(
            body=json.dumps({'username': username, 'task': {}}),
            headers=request.headers
        )
    return HTTPForbidden(
        body=json.dumps({'error': 'You do not have permission to access this data.'})
    )


@view_config(route_name='one_task', renderer='json', request_method='PUT')
def task_update(request):
    """Update task information for one user's task."""
    if is_user(request):
        username = request.matchdict['username']
        profile = get_profile(request, username)
        task = request.dbsession.query(Task).get(request.matchdict['id'])
        if task in profile.tasks:
            if 'name' in request.POST and request.POST['name']:
                task.name = request.POST['name']
            if 'note' in request.POST:
                task.note = request.POST['note']
            if 'due_date' in request.POST:
                task.due_date = datetime.strptime(due_date, '%d/%m/%Y %H:%M:%S') if request.POST['due_date'] else None
            if 'completed' in request.POST:
                task.due_date = request.POST['completed']
            request.dbsession.add(task)
            request.dbsession.flush()
            return HTTPOk(
                body=json.dumps({'username': username, 'task': task.to_dict()}),
                headers=request.headers
            )
        return HTTPNotFound(
            body=json.dumps({'username': username, 'task': {}}),
            headers=request.headers
        )
    return HTTPForbidden(
        body=json.dumps({'error': 'You do not have permission to access this data.'})
    )


@view_config(route_name='one_task', renderer='json', request_method='DELETE')
def task_delete(request):
    """Delete a task."""
    if is_user(request):
        username = request.matchdict['username']
        profile = get_profile(request, username)
        task = request.dbsession.query(Task).get(request.matchdict['id'])
        if task in profile.tasks:
            request.dbsession.delete(task)
        return HTTPOk(
            body=json.dumps({'username': username, 'msg': 'Deleted.'}),
            headers=request.headers
        )
    return HTTPForbidden(
        body=json.dumps({'error': 'You do not have permission to access this data.'})
    )


@view_config(route_name='one_profile', renderer='json', request_method='GET')
def profile_detail(request):
    """Get detail for one profile."""
    if security.is_user(request):
        profile = get_profile(request, request.matchdict['username'])
        return profile.to_dict() if profile else {}
    return HTTPForbidden(
        body=json.dumps({'error': 'You do not have permission to access this profile.'})
    )


@view_config(route_name='one_profile', renderer='json', request_method='PUT')
def profile_update(request):
    """Update an existing profile."""
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
        return HTTPAccepted(
            body=json.dumps({
                'msg': 'Profile updated.',
                'profile': profile.to_dict(),
                'username': profile.username
            }),
            headers=request.headers
        )

    return HTTPForbidden(
        body=json.dumps({'error': 'You do not have permission to access this profile.'}),
        headers=request.headers
    )


@view_config(route_name='one_profile', renderer='json', request_method='DELETE')
def profile_delete(request):
    """Delete an existing profile."""
    if security.is_user(request):
        profile = get_profile(request, request.matchdict['username'])
        if profile:
            request.dbsession.delete(profile)
        return HTTPNoContent(
            body=json.dumps({'msg': 'Profile deleted'})
        )
    return HTTPForbidden(
        body=json.dumps({'error': 'You do not have permission to access this profile.'})
    )


@view_config(
    route_name='login', renderer='json', request_method='POST',
    permission=NO_PERMISSION_REQUIRED
)
def login(request):
    """Authenticate a user."""
    needed = ['username', 'password']
    if all([key in request.POST for key in needed]):
        if security.authenticate_user(request):
            headers = remember(request, request.POST['username'])
            return HTTPAccepted(
                body=json.dumps({
                    'msg': 'Authenticated'
                }),
                headers=headers
            )
        return HTTPBadRequest(
            body=json.dumps(
                {'error': 'Incorrect username/password combination.'}
            )
        )
    return HTTPBadRequest(
        body=json.dumps(
            {'error': 'Some fields are missing'}
        )
    )


@view_config(route_name='logout', renderer='json')
def logout(request):
    """Remove user authentication from requests."""
    headers = forget(request)
    return HTTPOk(
        body=json.dumps({'msg': 'Logged out.'}),
        headers=headers
    )


@view_config(
    route_name='register', renderer='json', request_method='POST',
    permission=NO_PERMISSION_REQUIRED
)
def register(request):
    """Add a new user profile if it doesn't already exist."""
    needed = ['username', 'email', 'password', 'password2']
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
                return HTTPCreated(
                    body=json.dumps(
                        {"msg": 'Profile created'}
                    ),
                    headers=headers
                )
            return HTTPBadRequest(
                body=json.dumps(
                    {"error": "Passwords don't match"}
                )
            )

        return HTTPBadRequest(
            body=json.dumps(
                {'error': f'Username {username} is already taken'}
            )
        )

    return HTTPBadRequest(
        body=json.dumps(
            {'error': 'Some fields are missing'}
        )
    )
