from flask import Flask, make_response, request
from dataf import db_session
from flask_wtf import FlaskForm
from dataf.users import User
from sqlalchemy.orm import joinedload
# from dataf.category import Category
import datetime
from dataf.associate import Associate
import random
from dataf.words import Words
from flask import jsonify
from wtforms import (
    StringField,
    TextAreaField,
    EmailField,
    PasswordField,
    BooleanField,
    SubmitField,
)
from wtforms.validators import DataRequired
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from flask import render_template, redirect
from sqlalchemy import func


app = Flask(__name__)
app.config["SECRET_KEY"] = "yandexlyceum_secret_key"

login_manager = LoginManager()
login_manager.init_app(app)


class RegisterForm(FlaskForm):
    email = EmailField("Почта", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    password_again = PasswordField("Повторите пароль", validators=[DataRequired()])
    name = StringField("Имя пользователя", validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField("Зарегестрироваться")


class LoginForm(FlaskForm):
    email = EmailField("Почта", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


def getWordsLearnToday(user_id):
    db_sess = db_session.create_session()
    words_learn_today = db_sess.query(Associate).filter(
        func.date(Associate.editing_date) == datetime.datetime.now().date(),
        Associate.user_id == user_id,
        Associate.state == 0,
    )

    wordsLearnToday = []
    for i in words_learn_today:
        wordsLearnToday.append(i)
    return wordsLearnToday


@app.route('/change_progress', methods=['POST'])
def change_progress():
        db_sess = db_session.create_session()
        current_user.was_progressed = 2 # --> 2
        db_sess.merge(current_user)
        db_sess.commit()
        # и нас перекидывает на /repeat_words где какимто хуем was_progressed = 0
        return jsonify({"result": "Данные успешно обработаны", "value": "2"}), 200


@app.route("/repeat_word", methods=["POST"])
def repeat_word():
    db_sess = db_session.create_session()
    data = request.get_json()
    mat = data.get("mat")

    if mat:
        associate_table = (
            db_sess.query(Associate)
            .filter(
                Associate.user_id == current_user.id,
                Associate.word_id == mat["word_id"],
            )
            .first()
        )

        state = associate_table.state
        if state == 3:
            associate_table.state = 0
            associate_table.editing_date = datetime.datetime.now()
        else:
            associate_table.state += 1
            associate_table.editing_date = datetime.datetime.now()

        db_sess.commit()

        return jsonify({"result": "Данные успешно обработаны", "mat": mat}), 200
    else:
        return jsonify({"error": "Неверные данные в запросе"}), 400


@app.route("/repeat_progress", methods=['GET'])
@login_required
def repeat_progress():
    db_sess = db_session.create_session()

    wordsLearnToday = getWordsLearnToday(current_user.id)
    words = []

    for i in wordsLearnToday[:10]:
        word_obj = db_sess.query(Words).get(i.word_id)

        data_words = [word_obj.word_in_english, word_obj.word_in_russian]

        words.append(data_words)

    return render_template(
        "cards_progress.html",
        progress={"numbers": len(wordsLearnToday), "words_with_translate": words},
    ) # --> там в шаблоне отправляется запрос на /change_progress


@app.route("/repeat_words")
@login_required
def repeat_words():
    db_sess = db_session.create_session()
    was_progressed = current_user.was_progressed # --> 0
    print(was_progressed)
    wordsLearnToday = getWordsLearnToday(current_user.id)
    
    do_if1 = (was_progressed == 0)
    do_if2 = not (len(wordsLearnToday) % 10)
    do_if3 = len(wordsLearnToday) != 0

    if do_if1 * do_if2 * do_if3:
        current_user.was_progressed = 1 # --> 1
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect("/repeat_progress")
    elif not do_if2:
        current_user.was_progressed = 0
        db_sess.merge(current_user)
        db_sess.commit()
    
    # Используем join для объединения таблиц и загружаем связанные объекты
    user_learned_words = (
        db_sess.query(Associate)
        .join(Associate.word)
        .filter(Associate.user_id == current_user.id, Associate.state != "0")
        .options(joinedload(Associate.word))
        .all()
    )
    print(user_learned_words)
    if len(user_learned_words) >= 4:
        user_learned_words_random_4_items = random.sample(user_learned_words, 4)
        # Выбираем случайное слово из списка
        word_associate = random.choice(user_learned_words_random_4_items)
        # Получаем объект слова напрямую из связи
        word_obj = word_associate.word
    elif not len(user_learned_words):
        return render_template('congratulates.html')
    else:
        # Выбираем случайное слово из списка
        word_associate = random.choice(user_learned_words)
        # Получаем объект слова напрямую из связи
        word_obj = word_associate.word
        user_learned_words_random_4_items = user_learned_words
        for i in range(4 - len(user_learned_words_random_4_items)):
            word = db_sess.query(Associate).order_by(func.random()).first()
            user_learned_words_random_4_items.append(word)

    

    mat_js = {
        "word_id": word_obj.id,
        "word": str(word_obj.word_in_english
                    ).strip().capitalize(),
        "category": word_obj.category.category,
        "word_translate": str(word_obj.word_in_russian
                              ).strip().capitalize(),
        "url_image": word_obj.url_for_img,
    }

    user_learned_words_random_4_words = {}
    for index in range(len(user_learned_words_random_4_items)):
        user_learned_words_random_4_words[str(index)] = str(user_learned_words_random_4_items[index].word.word_in_english).strip().capitalize()

    print(mat_js)
    return render_template("card_repeat.html",
                           mat=mat_js,
                           state=word_associate.state,
                           other_word=user_learned_words_random_4_words,
                           entrance=(len(wordsLearnToday) // 10) * 10,
                           exit=(len(wordsLearnToday) // 10 + 1) * 10,
                           value=(len(wordsLearnToday) % 10 * 10))


@app.route("/learn_word", methods=["POST"])
def learn_word():
    db_sess = db_session.create_session()
    data = request.get_json()
    mat = data.get("mat")

    if mat:
        if mat["value"] == "LEARN":
            associate_table = Associate()
            associate_table.user_id = current_user.id
            associate_table.word_id = mat["word_id"]
            associate_table.state = 1

            db_sess.add(associate_table)
            db_sess.commit()

        return jsonify({"result": "Данные успешно обработаны", "mat": mat}), 200
    else:
        return jsonify({"error": "Неверные данные в запросе"}), 400


@app.route("/learn_words")
@login_required
def learn_words():
    db_sess = db_session.create_session()
    user_learned_words = db_sess.query(Associate).filter(
        current_user.id == Associate.user_id, str(Associate.state) != "0"
    )

    words = db_sess.query(Words).all()
    mat = []

    for word_obj in words:
        bul = True
        for word_learned in user_learned_words:
            if word_learned.word_id == word_obj.id:
                bul = False
        if bul:
            mat_js = {
                "word_id": word_obj.id,
                "word": word_obj.word_in_english,
                "category": word_obj.category.category,
                "word_translate": word_obj.word_in_russian,
                "url_image": word_obj.url_for_img,
            }

            mat.append(mat_js)

    mat = random.choice(mat)
    return render_template("card.html", mat=mat)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()

    # words = db_sess.query(Associate).filter(Associate.user_id == current_user.id,
    #                                         Associate.state != 0).all()
    # print(words)
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template(
                "register.html",
                title="Регистрация",
                form=form,
                message="Пароли не совпадают",
            )
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template(
                "register.html",
                title="Регистрация",
                form=form,
                message="Такой пользователь уже есть",
            )

        user = User(
            name=form.name.data,
            email=form.email.data,
        )

        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        return redirect("/login")
    return render_template("register.html", title="Регистрация", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")

        return render_template(
            "login.html", message="Неправильный логин или пароль", form=form
        )
    return render_template("login.html", title="Авторизация", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/blogs.sqlite")
    app.run()


if __name__ == "__main__":
    main()