# инициализируем необходимые библиотеки
import datetime
import sqlalchemy
import flask_login
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash


class User(SqlAlchemyBase, flask_login.UserMixin):
    # Задаём имя модели
    __tablename__ = 'users'
    # Колонки модели
    id = sqlalchemy.Column(sqlalchemy.Integer, 
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, 
                              index=True, unique=True, nullable=True)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    was_progressed = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    # Настраиваем отношения моделей
    words = orm.relationship("Associate", back_populates="user")

    def __repr__(self):
        return f"{self.id};{self.name};{self.email}"
    # Функция задания пароля пользователю
    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)
    # Функция проверки пароля
    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)