from pyramid_todo.models.meta import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Unicode,
    ForeignKey
)
from sqlalchemy.orm import relationship


DATE_FMT = '%d/%m/%Y %H:%M:%S'


class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    username = Column(Unicode, nullable=False)
    email = Column(Unicode, nullable=False)
    password = Column(Unicode, nullable=False)
    date_joined = Column(DateTime, nullable=False)
    tasks = relationship("Task", back_populates='profile')

    def to_dict(self):
        """Get the object's properties as a dictionary."""

        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "date_joined": self.date_joined.strftime(DATE_FMT),
            "tasks": self.tasks
        }


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode, nullable=False)
    note = Column(Unicode)
    creation_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime)
    completed = Column(Boolean, default=False)
    profile_id = Column(Integer, ForeignKey('profiles.id'), nullable=False)
    profile = relationship("Profile", back_populates='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'note': self.note,
            'creation_date': self.creation_date.strftime(DATE_FMT),
            'due_date': self.due_date.strftime(DATE_FMT) if self.due_date else None,
            'completed': self.completed,
            'profile_id': self.profile_id
        }
