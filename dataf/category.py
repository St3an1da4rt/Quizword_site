# инициализируем необходимые библиотеки
import sqlalchemy
import flask_login
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Category(SqlAlchemyBase, flask_login.UserMixin):
    # Задаём имя модели
    __tablename__ = 'categories'

    # Колонки модели
    id = sqlalchemy.Column(sqlalchemy.Integer, unique=True, primary_key=True, autoincrement=True)
    category = sqlalchemy.Column(sqlalchemy.String)
    # Настраиваем отношения моделей
    words_list = orm.relationship("Words", back_populates='category')