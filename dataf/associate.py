import datetime
import sqlalchemy
import flask_login
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Associate(SqlAlchemyBase, flask_login.UserMixin):
    __tablename__ = 'associate'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.ForeignKey("users.id"))
    word_id = sqlalchemy.Column(sqlalchemy.ForeignKey("words.id"))
    state = sqlalchemy.Column(sqlalchemy.Integer)
    editing_date = sqlalchemy.Column(sqlalchemy.DateTime, 
                                     default=datetime.datetime.now)

    user = orm.relationship("User", back_populates="words")
    word = orm.relationship("Words", back_populates='users')