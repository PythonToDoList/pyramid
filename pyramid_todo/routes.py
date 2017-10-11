username = '{username:[\w\-\.]+}'


def includeme(config):
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('info', '/api/v1')
    config.add_route('profiles', '/api/v1/accounts')
    config.add_route('login', '/api/v1/accounts/login')
    config.add_route('logout', '/api/v1/accounts/logout')
    config.add_route('one_profile', '/api/v1/accounts/{username}')
    config.add_route('tasks', '/api/v1/accounts/{username}/tasks')
    config.add_route('one_task', '/api/v1/accounts/{username}/tasks/{id:\d+}')
