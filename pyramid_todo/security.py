import os
from passlib.hash import pbkdf2_sha256 as hasher
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated, Allow
from pyramid_todo.models import Profile


class MyRoot(object):

    def __init__(self, request):
        self.request = request

    __acl__ = [
        (Allow, Authenticated, 'authorized'),
    ]


def includeme(config):
    """Include this security configuration for the configurator."""
    auth_secret = os.environ.get('AUTH_SECRET', 's00persekret')
    authn_policy = AuthTktAuthenticationPolicy(
        secret=auth_secret,
        hashalg='sha512'
    )
    config.set_authentication_policy(authn_policy)

    authz_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(authz_policy)
    config.set_default_permission('authorized')
    config.set_root_factory(MyRoot)


def authenticate_user(request):
    """Check provided username and password for valid user credentials."""
    username = request.POST['username']
    passwd = request.POST['password']
    profile = request.dbsession.query(Profile).filter(
        Profile.username == username
    ).first()
    return profile and hasher.verify(passwd, profile.password)


def is_user(request):
    """Check if the incoming request is from the appropriate_user."""
    return request.authenticated_userid == request.matchdict['username']
