# инициализируем необходимые библиотеки
import datetime
import sqlalchemy
import flask_login
from .db_session import SqlAlchemyBase
from sqlalchemy import orm

# Модель соединяющая модель слов и пользователя
class Associate(SqlAlchemyBase, flask_login.UserMixin):
    # Задаём имя модели
    __tablename__ = 'associate'

    # Колонки модели
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.ForeignKey("users.id"))
    word_id = sqlalchemy.Column(sqlalchemy.ForeignKey("words.id"))
    state = sqlalchemy.Column(sqlalchemy.Integer)
    editing_date = sqlalchemy.Column(sqlalchemy.DateTime, 
                                     default=datetime.datetime.now)
    
    # Настраиваем отношения моделей
    user = orm.relationship("User", back_populates="words")
    word = orm.relationship("Words", back_populates='users')