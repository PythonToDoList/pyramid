from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    settings['sqlalchemy.url'] = 'postgres://localhost:5432/pyramid_todo'
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.include('pyramid_todo.models')
    config.include('pyramid_todo.routes')
    config.include('pyramid_todo.security')
    config.include('pyramid_todo.utils')
    config.scan()
    return config.make_wsgi_app()
