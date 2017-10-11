from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    relationship,
    Unicode,
)

from pyramid_todo.models.meta import Base


class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    username = Column(Unicode)
    email = Column(Unicode)
    password = Column(Unicode)
    date_joined = Column(DateTime)
    tasks = relationship("Task", backref='profile')


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode)
    note = Column(Unicode)
    creation_date = Column(DateTime)
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    profile = relationship("Profile", backref='tasks')
