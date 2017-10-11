from datetime import datetime
from passlib.hash import pbkdf2_sha256 as hasher
from pyramid.view import view_config
from pyramid_todo.models import Profile, Task


def get_profile(request, username):
    """Check if the requested profile exists."""
    return request.dbsession.query(Profile).filter(Profile.username == username).first()


@view_config(route_name='info', renderer='json')
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
    if get_profile(request, request.matchdict['username']):
        username = request.matchdict['username']
        matching_profile = get_profile(request, username)
        if request.method == "GET":
            tasks = request.dbsession.query(Task).filter(
                Task.profile == matching_profile
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
                profile_id=matching_profile.id,
                profile=matching_profile
            )
            request.dbsession.add(task)
            return {'msg': 'post'}
    return {
        'error': 'Invalid username'
    }


@view_config(route_name='one_task', renderer='json')
def task_detail(request):
    """Get task detail for one user given a task ID."""
    username = request.matchdict['username']
    matching_profile = get_profile(request, username)
    if matching_profile:
        task = request.dbsession.query(Task).get(request.matchdict['id'])
        if task in matching_profile.tasks:
            return {
                'username': username,
                'task': task.to_dict(),
            }
    return {
        'error': 'Invalid username'
    }


@view_config(route_name='profiles', renderer='json')
def profile_list(request):
    """List all profiles."""
    if request.method == "GET":
        profiles = request.dbsession.query(Profile).all()
        return {'profiles': profiles}

    elif request.method == "POST":
        if not get_profile(request, request.POST['username']):
            profile = Profile(
                username=request.POST['username'],
                email=request.POST['email'],
                password=hasher.hash(request.POST['password']),
                date_joined=datetime.now(),
            )
            request.dbsession.add(profile)

        else:
            return {'error': 'This user already has a profile.'}

    elif request.method == "DELETE":
        if get_profile(request, request.POST['username']):
            request.dbsession.query(Profile).filter(Profile.username == request.POST['username']).delete()

    else:
        return {'error': 'Method not supported for this route.'}


@view_config(route_name='one_profile', renderer='json')
def profile_detail(request):
    """Get detail for one profile."""
    profile = request.dbsession.query(Profile).filter(Profile.username == request.matchdict['username']).first()
    return profile.to_dict() if profile else {}


@view_config(route_name='login', renderer='json')
def login(request):
    return {}


@view_config(route_name='logout', renderer='json')
def logout(request):
    return {}
