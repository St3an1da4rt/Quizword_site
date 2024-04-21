# инициализируем необходимые библиотеки
from flask import Flask, request
from dataf import db_session
from flask_wtf import FlaskForm
from dataf.users import User
from sqlalchemy.orm import joinedload
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

# активируем ключ яндекса
app = Flask(__name__)
app.config["SECRET_KEY"] = "yandexlyceum_secret_key"
# создаём Login_mananger и инициализируем приложение
login_manager = LoginManager()
login_manager.init_app(app)

# создём форму регистрации
class RegisterForm(FlaskForm):
    email = EmailField("Почта",
                       validators=[DataRequired()])
    password = PasswordField("Пароль",
                             validators=[DataRequired()])
    password_again = PasswordField(
        "Повторите пароль", validators=[
            DataRequired()])
    name = StringField("Имя пользователя",
                        validators=[DataRequired()])
    about = TextAreaField("Немного о себе")
    submit = SubmitField("Зарегистрироваться")

# Создаём форму входа в аккаунт
class LoginForm(FlaskForm):
    email = EmailField("Почта",
                       validators=[DataRequired()])
    password = PasswordField("Пароль",
                             validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")

# Создаём функции получения количество выученных слов пользователем за день
def getWordsLearnToday(user_id):
    # Получаем запрос слов выученных слов ползователем в день
    db_sess = db_session.create_session()
    words_learn_today = db_sess.query(Associate).filter(
        func.date(Associate.editing_date) == datetime.datetime.now().date(),
        Associate.user_id == user_id,
        Associate.state == 0,
    )
    # Переводим запрос в список
    wordsLearnToday = []
    for i in words_learn_today:
        wordsLearnToday.append(i)
    # Отправляем список слов    
    return wordsLearnToday

# Функция-обработчик, которая изменяет состояние прогресса пользователя
@app.route('/change_progress', methods=['POST'])
def change_progress():
    # Меняем состояние прогресса на промежуточное, в котором нельзя открыть окно прогресса
    db_sess = db_session.create_session()
    current_user.was_progressed = 2 # --> 2
    db_sess.merge(current_user)
    db_sess.commit()
    # Отправляет запрос в шаблон об успешной обработке запроса
    return jsonify(
        {"result": "Данные успешно обработаны", "value": "2"}
        ), 200

# Endpoint отправленного обьекта слова, которое пользователь выучил
@app.route("/repeat_word", methods=["POST"])
def repeat_word():
    db_sess = db_session.create_session()
    data = request.get_json()
    mat = data.get("mat") # Получаем json запроса

    if mat:
        # Получаем обьект слова 
        associate_table = (
            db_sess.query(Associate)
            .filter(
                Associate.user_id == current_user.id,
                Associate.word_id == mat["word_id"],
            )
            .first()
        )

        state = associate_table.state
        # Изменение состояние прогресса слова
        if state == 3:
            associate_table.state = 0
            associate_table.editing_date = datetime.datetime.now()
        else:
            associate_table.state += 1
            associate_table.editing_date = datetime.datetime.now()
        # Применяем изменение
        db_sess.commit()
        # Отправляем запрос подтверждения
        return jsonify(
            {"result": "Данные успешно обработаны", "mat": mat}), 200
    else:
        return jsonify({"error": "Неверные данные в запросе"}), 400

# Обработчик страницы прогресса
@app.route("/repeat_progress", methods=['GET'])
@login_required
def repeat_progress():
    db_sess = db_session.create_session()
    # Получаем список выученных слов
    wordsLearnToday = getWordsLearnToday(current_user.id)
    # Выбираем 10 первых из них
    words = []
    for i in wordsLearnToday[:10]:
        word_obj = db_sess.query(Words).get(i.word_id) # Выполняем запрос на получение слова из 10 первых
        # Делим запрос на список из слова и его перевода
        data_words = [word_obj.word_in_english, word_obj.word_in_russian]
        # Добавляем этот список в список 10 таких же слов
        words.append(data_words)
    # Показываем страницу проогресса
    return render_template(
        "cards_progress.html",
        progress={
            "numbers": len(wordsLearnToday),
            "words_with_translate": words},
    )

# Страница повторения слов
@app.route("/repeat_words")
@login_required
def repeat_words():
    # Получаем исходный прогресс пользователя и список выученных слов
    db_sess = db_session.create_session()
    was_progressed = current_user.was_progressed  # --> 0
    wordsLearnToday = getWordsLearnToday(current_user.id)
    # Условия при которых будет открываться страница прогресса
    do_if1 = (was_progressed == 0)
    do_if2 = not (len(wordsLearnToday) % 10)
    do_if3 = len(wordsLearnToday) != 0
    # Условный оператор при котором будет открываться страница прогресса
    if do_if1 * do_if2 * do_if3:
        # Меняем состояние прогресса пользователя, применяем изменение
        current_user.was_progressed = 1  # --> 1
        db_sess.merge(current_user)
        db_sess.commit()
        # Открываем страницу прогресса
        return redirect("/repeat_progress")
    # Если условия не верны
    elif not do_if2:
        # Меняем состояние прогресса пользователя, применяем изменение
        current_user.was_progressed = 0 # --> 0
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

    if len(user_learned_words) >= 4:
        user_learned_words_random_4_items = random.sample(
            user_learned_words, 4)
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
        # Заполняем список другими словами если длина списка меньше 4
        user_learned_words_random_4_items = user_learned_words
        for _ in range(4 - len(user_learned_words_random_4_items)):
            word = (
                db_sess.query(Associate)
                    .order_by(func.random())
                    .first()
                    )
            user_learned_words_random_4_items.append(word)

    # Создаём json запроса на шаблон
    mat_js = {
        "word_id": word_obj.id,
        "word": str(word_obj.word_in_english
                    ).strip().capitalize(),
        "category": word_obj.category.category,
        "word_translate": str(word_obj.word_in_russian
                              ).strip().capitalize(),
        "url_image": word_obj.url_for_img,
    }
    # Создаём json рандомных 4 слов
    user_learned_words_random_4_words = {}
    for index in range(len(user_learned_words_random_4_items)):
        user_learned_words_random_4_words[str(index)] = str(
            user_learned_words_random_4_items[index].word.word_in_english
            ).strip().capitalize()

    entrance = (len(wordsLearnToday) // 10) * 10
    exit = (len(wordsLearnToday) // 10 + 1) * 10
    value = (len(wordsLearnToday) % 10 * 10)

    # Отправляем запросы на шеблон
    return render_template(
            "card_repeat.html",
            mat=mat_js,
            state=word_associate.state,
            other_word=user_learned_words_random_4_words,
            entrance=entrance,
            exit=exit,
            value=value
        )

# Endpoint изучения слова
@app.route("/learn_word", methods=["POST"])
def learn_word():
    # Получаем необходимые данные
    db_sess = db_session.create_session()
    data = request.get_json()
    mat = data.get("mat")

    if mat:
        # Изменяем состояние слова
        if mat["value"] == "LEARN":
            associate_table = Associate()
            associate_table.user_id = current_user.id
            associate_table.word_id = mat["word_id"]
            associate_table.state = 1
            # Применяем изменения
            db_sess.add(associate_table)
            db_sess.commit()
        # Отправляем запрос
        return jsonify(
            {"result": "Данные успешно обработаны", "mat": mat}
            ), 200
    else:
        return jsonify(
            {"error": "Неверные данные в запросе"}
            ), 400

# Страница выбора слова
@app.route("/learn_words")
@login_required
def learn_words():
    db_sess = db_session.create_session()
    # Слова уже отправленные на повторение
    user_learned_words = db_sess.query(Associate).filter(
        current_user.id == Associate.user_id,
        str(Associate.state) != "0"
    )
    # Все слова
    words = db_sess.query(Words).all()
    mat = []
    # цикл в кором собираем слова ещё не выбраынные пользователем
    for word_obj in words:
        bul = True
        # Проверям есть ли слово в списке изученных слов
        for word_learned in user_learned_words:
            if word_learned.word_id == word_obj.id:
                bul = False
        
        if bul:
            # Если слово не в том списке значит создаём запрос
            mat_js = {
                "word_id": word_obj.id,
                "word": word_obj.word_in_english,
                "category": word_obj.category.category,
                "word_translate": word_obj.word_in_russian,
                "url_image": word_obj.url_for_img,
            }
            # Добавляем слово в список слов ещё не выбраынных пользователем
            mat.append(mat_js)
    # Выбираем рандомное их них
    mat = random.choice(mat)
    return render_template(
            "card.html",
            mat=mat
        )

# Функция для current_user 
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)

# Главная страница
@app.route("/")
def index():
    return render_template("index.html")

# Страница регистрации
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
        if db_sess.query(User).filter(
            User.email == form.email.data
            ).first():
            return render_template(
                "register.html",
                title="Регистрация",
                form=form,
                message="Такой пользователь уже есть",
            )
        # Получаем пользователя
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        # Устанавливаем пароль для пользователя и применяем изменения
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        return redirect("/login")
    return render_template(
            "register.html",
            title="Регистрация",
            form=form
        )

# Страница входа в аккаунт
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.email == form.email.data).first()
        # Входим в аккаунт
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")

        return render_template(
            "login.html", message="Неправильный логин или пароль", form=form
        )
    return render_template("login.html", title="Авторизация", form=form)

# При нажатии на name пользователя выходим из аккаунта
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")

# Главная функция
def main():
    db_session.global_init("db/blogs.sqlite")
    app.run()


if __name__ == "__main__":
    main()