import datetime
import sqlalchemy
from sqlalchemy import ForeignKey
import flask_login
from googletrans import Translator
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


translater = Translator()


class Words(SqlAlchemyBase, flask_login.UserMixin):
    __tablename__ = 'words'

    id = sqlalchemy.Column(sqlalchemy.Integer, unique=True, primary_key=True, autoincrement=True)
    word_in_english = sqlalchemy.Column(sqlalchemy.String)
    word_in_russian = sqlalchemy.Column(sqlalchemy.String)
    url_for_img = sqlalchemy.Column(sqlalchemy.String)

    users = orm.relationship("Associate", back_populates="word")
    category_id = sqlalchemy.Column(ForeignKey("categories.id"))
    category = orm.relationship("Category", back_populates="words_list")