from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from datetime import datetime

db = SQLAlchemy()

# Association table for many-to-many relationship between Users and Roles
roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                       db.Column('role_id', db.Integer, db.ForeignKey('roles.id'))
                       )


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    fs_uniquifier = db.Column(db.String(255))
    user_type = db.Column(db.String(50))
    last_login = db.Column(db.DateTime)
    API_token = db.Column(db.String, default=None)
    roles = db.relationship('Role', secondary=roles_users,backref=db.backref('users', lazy='dynamic'))
 

class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)



class Section(db.Model):
    __tablename__ = 'section'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.String(255))
    books = db.relationship('Book', backref='section', lazy=True,cascade='all, delete-orphan')

    
class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    authors = db.Column(db.String(255), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    rating = db.Column(db.Float, nullable=True) 

    
class BookStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_allocated = db.Column(db.Integer)
    is_requested = db.Column(db.Integer)
    date_of_issue = db.Column(db.DateTime,nullable=True)
    return_date = db.Column(db.DateTime,nullable=True)
    status = db.Column(db.String(255), nullable=False)
    user = db.relationship('User', backref=db.backref('borrowed'))
    book = db.relationship('Book', backref=db.backref('borrowed'))

class BookIssued(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    rating=db.Column(db.Integer)
    feedback = db.Column(db.Text)
    returned = db.Column(db.Integer)
    date_of_issue = db.Column(db.DateTime)
    return_date = db.Column(db.DateTime)
    user = db.relationship('User', backref=db.backref('books'))
    book = db.relationship('Book', backref=db.backref('users'))
