import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'plaster_pastedeploy',
    'pyramid >= 1.9a',
    'pyramid_debugtoolbar',
    'pyramid_jinja2',
    'pyramid_retry',
    'pyramid_tm',
    'SQLAlchemy',
    'transaction',
    'zope.sqlalchemy',
    'waitress',
]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest',
    'pytest-cov',
]

dev_requires = [
    'ipython',
    'pyramid_ipython'
]

setup(
    name='pyramid',
    version='1.0.0',
    description='Pyramid To Do List',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='Nicholas Hunt-Walker',
    author_email='nhuntwalker@gmail.com',
    url='https://github.com/PythonToDoList/pyramid',
    keywords='web pyramid pylons',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
        'dev': dev_requires
    },
    install_requires=requires,
    entry_points={
        'paste.app_factory': [
            'main = pyramid:main',
        ],
        'console_scripts': [
            'initialize_pyramid_db = pyramid.scripts.initializedb:main',
        ],
    },
)
