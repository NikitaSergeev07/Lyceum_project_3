import pymorphy2
from flask import Flask
from flask import render_template, redirect, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_restful import abort, Api
from werkzeug.exceptions import abort

from data import db_session
from data.contact_forms import Contact_form
from data.object import Objects
from data.users import User
from forms.object import ObjectForm
from forms.user import LoginForm
from forms.user import RegisterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
api = Api(app)


def main():
    db_session.global_init("db/web-project.db")
    app.run()
    db_sess = db_session.create_session()


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        events = db_sess.query(Objects).filter(
            (Objects.user == current_user))
    else:
        events = db_sess.query(Objects)
    return render_template("index.html", objects=events)


# Функция поиска
@app.route("/search", methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        db_sess = db_session.create_session()
        mess = request.form['mess']
        # Если что сократить все до первого запроса
        result = db_sess.query(Objects).filter(
            Objects.title.like(f'%{mess}%') | (Objects.title.like(f'{mess}%%')) | (Objects.title.like(f'%%{mess}')) | (
                Objects.title.like(f'{mess}%{mess}')) | (Objects.title.like(f'%{mess}{mess}')) | (
                Objects.title.like(f'{mess}{mess}%')))
        count = 0
        for i in result:
            if i.title:
                count += 1
        # print(count)
        morph = pymorphy2.MorphAnalyzer()
        comment = morph.parse('объявление')[0]
        word = comment.make_agree_with_number(count).word  # => 'объявлений'
        if count > 0:
            flash(f'По вашему запросу найдено {count} {word}')
        elif count == 0:
            flash(f"Ничего не найдено по запросу {mess}")
        return render_template('search.html', objects=result)


def abort_if_news_not_found(objects_id):
    session = db_session.create_session()
    objects = session.query(Objects).get(objects_id)
    if not objects:
        abort(404, message=f"Objects {objects_id} not found")


@app.route('/contact', methods=["POST", "GET"])
def contact():
    if request.method == 'GET':
        return render_template('contact.html')
    if request.method == 'POST':
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
            if request.form['username'] and request.form['email'] and request.form['message']:
                db_sess = db_session.create_session()
                contact = Contact_form(
                    username=request.form['username'],
                    email=request.form['email'],
                    message=request.form['message']
                )
                db_sess.add(contact)
                db_sess.commit()
        else:
            flash("Ошибка отправки", category='error')
    return render_template('contact.html')


# TODO /account/<int:id> и пихнуть это в account.html обработку /account/{{current_user.id}}
@app.route('/account')
@login_required
def account():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        objects = db_sess.query(Objects).filter(
            (Objects.user == current_user))
    else:
        objects = db_sess.query(Objects)
    return render_template("account.html", objects=objects)


@app.route('/event/<int:id>', methods=["GET", "POST"])
def event(id):
    if request.method == "GET" or request.method == "POST":
        db_sess = db_session.create_session()
        events = db_sess.query(Objects).filter(Objects.id == id,
                                               Objects.user == current_user
                                               ).first()
        if events:
            return render_template('event.html', objects=events)
        else:
            abort(404)


@app.route('/log_out')
@login_required
def log_out():
    logout_user()
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/add_objects', methods=['GET', 'POST'])
@login_required
def add_objects():
    form = ObjectForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        objects = Objects()
        objects.title = form.title.data
        objects.content = form.content.data
        objects.price = form.price.data
        objects.category = form.category.data
        objects.city = form.city.data
        current_user.objects.append(objects)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('object.html', title='Добавление новости',
                           form=form)


@app.route('/edit_objects/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_objects(id):
    form = ObjectForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        events = db_sess.query(Objects).filter(Objects.id == id,
                                               Objects.user == current_user
                                               ).first()
        if events:
            form.title.data = events.title
            form.content.data = events.content
            form.price.data = events.price
            form.category.data = events.category
            form.city.data = events.city

        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        events = db_sess.query(Objects).filter(Objects.id == id,
                                               Objects.user == current_user
                                               ).first()
        if events:
            events.title = form.title.data
            events.content = form.content.data
            events.price = form.price.data
            events.category = form.category.data
            events.city = form.city.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('object.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/objects_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def objects_delete(id):
    db_sess = db_session.create_session()
    events = db_sess.query(Objects).filter(Objects.id == id,
                                           Objects.user == current_user
                                           ).first()
    if events:
        db_sess.delete(events)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/account')


@app.route('/api')
def api():
    return render_template('Api.html')


@app.route('/donate')
def donate():
    return render_template('donate.html')


@app.route('/editing')
def editing():
    return render_template('editing.html')


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    main()
