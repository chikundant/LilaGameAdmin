import config
from project import app
from flask import render_template, flash, redirect, url_for, request, render_template_string, send_file
from werkzeug.urls import url_parse
from project.forms import LoginForm, RegistrationForm, SearchForm, AddUserForm, AddGameForm, ChangeGameForm, CellForm, \
    TypeForm, TemplateForm, ReportForm
from flask_login import current_user, login_user, logout_user, login_required
from project.models import Admin, User, Game, Type, Cell, Template
from project import db
import datetime
from collections import Counter

from docx import Document
from htmldocx import HtmlToDocx


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required
def index(page=1):
    search_form = SearchForm()
    add_form = AddUserForm()

    users = User.query.order_by(User.id.desc()).paginate(page=page, per_page=config.USERS_PER_PAGE, error_out=False)

    if add_form.validate_on_submit():
        user = User(name=add_form.name.data, email=add_form.email.data or None, phone=add_form.phone.data or None,
                    additional_comment=add_form.comment.data, date=datetime.date.today(),
                    birthday=add_form.birthday.data or None, city=add_form.city.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('index'))

    if search_form.is_submitted():
        search = '%{}%'
        if search_form.input.data == '':
            users = User.query.order_by(User.id.desc()).paginate(page=page, per_page=config.USERS_PER_PAGE,
                                                                 error_out=False)
        if search_form.type.data == '1':
            users = User.query.filter(User.name.like(search.format(search_form.input.data))).paginate(page=page, per_page=config.USERS_PER_PAGE, error_out=False)

        elif search_form.type.data == '2':
            users = User.query.filter(User.email.like(search.format(search_form.input.data))).paginate(page=page, per_page=config.USERS_PER_PAGE, error_out=False)

        elif search_form.type.data == '3':
            users = User.query.filter(User.phone.like(search.format(search_form.input.data))).paginate(page=page, per_page=config.USERS_PER_PAGE, error_out=False)


    return render_template('index.html', search_form=search_form, add_form=add_form, users=users)


@app.route('/user/<id>', methods=['GET', 'POST'])
@login_required
async def user(id):
    user = User.query.filter_by(id=id).first()

    add_user_form = AddUserForm()
    if add_user_form.is_submitted() and not (add_user_form.name.data is None):
        user.name = add_user_form.name.data
        user.email = add_user_form.email.data
        user.phone = add_user_form.phone.data
        user.birthday = add_user_form.birthday.data
        user.city = add_user_form.city.data
        user.additional_comment = add_user_form.comment.data

        db.session.commit()
        return redirect(url_for('user', id=id))

    add_game_form = AddGameForm()
    if add_game_form.is_submitted():
        cell = Cell.query.filter_by(id=add_game_form.cell_id.data).first()
        if cell is not None:
            game = Game(cell_id=add_game_form.cell_id.data, personal_comment=add_game_form.my_comment.data.replace('\r\n', '<br>'),
                        user_comment=add_game_form.user_comment.data.replace('\r\n', '<br>'))
            game.user_id = user.id
            db.session.add(game)
            db.session.commit()
        return redirect(url_for('user', id=id))

    games = Game.query.filter_by(user_id=user.id).order_by(Game.id.desc()).all()
    users_block = User.query.filter_by(date=datetime.date.today()).all()

    return render_template('user.html', user=user, add_game_form=add_game_form, add_user_form=add_user_form,
                           games=games, users_block=users_block)


@app.route('/change_cell', methods=['GET', 'POST'])
@login_required
def change_cell():
    cell_form = CellForm()
    cell_form.type.choices = [(type.id, type.name) for type in Type.query.all()]
    cell_form.type.choices.append((0, None))

    if cell_form.is_submitted() and request.form['submit'] == 'search':
        cell = Cell.query.filter_by(id=cell_form.id.data).first()
        if cell:
            cell_form.type.default = cell.type_id
            cell_form.process()
            cell_form.description.data = cell.description
            cell_form.id.data = cell.id
            cell_form.title.data = cell.title

    elif cell_form.is_submitted() and request.form['submit'] == 'save':
        cell = Cell.query.filter_by(id=cell_form.id.data).first()
        if cell is None:
            cell = Cell()
        cell.id = cell_form.id.data
        cell.title = cell_form.title.data
        cell.description = cell_form.description.data
        cell.type_id = cell_form.type.data
        db.session.add(cell)
        db.session.commit()
        return redirect('change_cell')
    return render_template('change_cell.html', cell_form=cell_form)


@app.route('/change_type', methods=['GET', 'POST'])
@login_required
def change_type():
    type_form = TypeForm()

    types = Type.query.all()

    for i in range(len(types)):
        type_form.name_select.choices.append((types[i].id, types[i].name))

    if type_form.is_submitted() and request.form['submit'] == 'search':
        type = Type.query.filter_by(id=type_form.name_select.data).first()
        if type:
            type_form.name.data = type.name
            type_form.description.data = type.description
        else:
            return redirect('change_type')

    elif type_form.is_submitted() and request.form['submit'] == 'save':
        print(type_form.name.data)
        type = Type.query.filter_by(id=type_form.name_select.data).first()
        if type is None:
            type = Type()
        type.name = type_form.name.data
        type.description = type_form.description.data
        db.session.add(type)
        db.session.commit()
        return redirect('change_type')

    return render_template('change_type.html', type_form=type_form)


@app.route('/change_template', methods=['GET', 'POST'])
@login_required
def change_template():
    template_form = TemplateForm()

    templates = Template.query.all()
    for i in range(len(templates)):
        template_form.name_select.choices.append((templates[i].id, templates[i].name))

    if template_form.is_submitted() and request.form['submit'] == 'search':
        template = Template.query.filter_by(id=template_form.name_select.data).first()
        if template:
            template_form.name.data = template.name
            template_form.description.data = template.description
        else:
            return redirect('change_template')

    elif template_form.is_submitted() and request.form['submit'] == 'save':

        template = Template.query.filter_by(id=template_form.name_select.data).first()
        if template is None:
            template = Template()
        # template.name = template_form.name.data
        # template.name = template_form.name_select.data
        template.description = template_form.description.data
        db.session.add(template)
        db.session.commit()
        return redirect('change_template')

    return render_template('change_template.html', type_form=template_form)


@app.route('/game/<id>', methods=['GET', 'POST'])
def edit_game(id):
    change_game_form = ChangeGameForm()
    game = Game.query.filter_by(id=id).first()

    if change_game_form.is_submitted():
        game.cell_id = change_game_form.cell_id.data
        game.user_comment = change_game_form.user_comment.data.replace('\r\n', '<br>')
        game.personal_comment = change_game_form.my_comment.data.replace('\r\n', '<br>')
        db.session.commit()
        return redirect(url_for('user', id=game.user_id))

    change_game_form.my_comment.data = game.personal_comment
    change_game_form.user_comment.data = game.user_comment

    return render_template('edit_game.html', game=game, change_game_form=change_game_form)


@app.route('/delete_game/<id>', methods=['GET', 'POST'])
def delete_game(id):
    game = Game.query.filter_by(id=id).first()
    db.session.delete(game)
    db.session.commit()
    return redirect(url_for('user', id=game.user_id))


@app.route('/delete/user/<id>')
@login_required
def delete(id):
    user = User.query.filter_by(id=id).first()
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = Admin.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')

        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        return redirect(next_page)

    return render_template('login.html', form=form)


# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#
#     form = RegistrationForm()
#
#     if form.validate_on_submit():
#         user = Admin(username=form.username.data)
#         user.set_password(form.password.data)
#         db.session.add(user)
#         db.session.commit()
#         flash('Congratulations, you are now a registered user!')
#         return redirect(url_for('login'))
#     return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<id>/report', methods=['GET', 'POST'])
@login_required
def report(id):
    user = User.query.filter_by(id=id).first()
    games = Game.query.filter_by(user_id=id).all()

    form = ReportForm()
    if request.method == 'POST':
        document = Document()
        new_parser = HtmlToDocx()
        html = (str(form.text.data))

        new_parser.add_html_to_document(html, document)
        document.save('project/report.docx')
        file = 'ЛИЛА-{}-{}.docx'.format(user.name, user.date)
        return send_file('report.docx', as_attachment=True, download_name=file)


    # Creating a template
    newline = '</br>'
    bold = lambda str: f'<b>{str}</b>'
    i = lambda str: f'<i>{str}</i>'
    h1 = lambda str: f'<h1>{str}</h1>'
    h2 = lambda str: f'<h2>{str}</h2>'
    p = lambda str: f'<p>{str}</p>'
    d = str(user.date.strftime("%d.%m.%Y"))

    dbir = ''
    if user.birthday:
        dbir = str(user.birthday.strftime("%d.%m.%Y"))

    form.text.data = p(h1(user.name + ' ' + d))
    form.text.data += newline
    form.text.data += p(bold('Запрос: ')) + p(i(user.additional_comment)) + newline

    form.text.data += p(bold('Город: ') + user.city)
    form.text.data += p(bold('Дата рождения: ') + dbir + newline)

    form.text.data += p('_____________________________________________________________')

    printed_games = []

    for game in games:
        if game.cell:
            if game.cell.title in printed_games:
                form.text.data += p(h2(Template.query.filter_by(name='emoji_cell_title').first().description + str(game.cell.id) + ' ' + game.cell.title) + newline)
                if game.user_comment:
                    form.text.data += p(bold('Твой комментарий: ') + p(game.user_comment + newline + newline))

                if game.personal_comment:
                        form.text.data += bold('Сообщение от Ксении: ') + p(game.personal_comment + newline + newline)

                form.text.data += p('_____________________________________________________________')
            else:

                form.text.data += p(h2(Template.query.filter_by(name='emoji_cell_title').first().description + str(game.cell.id) +  ' ' + game.cell.title) + newline)
                if game.user_comment:
                    form.text.data += p(bold('Твой комментарий: ')) + p(game.user_comment + newline + newline)

                if game.personal_comment:
                        form.text.data += bold('Сообщение от Ксении: ') + p(game.personal_comment + newline + newline)
                form.text.data += p(bold('О клетке: '))

                form.text.data += game.cell.description
                form.text.data += p('_____________________________________________________________')

            printed_games.append(game.cell.title)
    form.text.data += newline


    cells = []
    for game in games:
        cells.append(game.cell)

    printed_games = dict(Counter(cells))

    # Финалочка
    form.text.data += p(Template.query.filter_by(name='snake').first().description)
    snake = {
        12: 'Зависть - Неудовлетворенность',
        16: 'Ревность - Хотение',
        24: 'Плохая Компания - Тщеславие',
        52: 'Насилие - Чистилище',
        63: 'Инерция - Обнуление',
        55: 'Эгоизм - Гнев',
        61: 'Неверно направленное сознание - Ничтожност',
        29: 'Отрицание своей природы - Заблуждение',
        44: 'Неведение - Чувственный план',
        72: 'Энергия инерции - Земля'
    }
    arrow = {
        10: 'Очищение - Уверенность',
        17: 'Сопереживание - Созидание',
        20: 'Отдавание - Равновесие',
        22: 'Жизнь в согласии с природой - Верно направленное сознание',
        27: 'Высшая Цель - Реализация',
        28: 'Принятие и раскрытие своей природы - Преодоление',
        45: 'Правильное знание - Оставление концепций и отождествлений',
        46: 'Различение - Счастье',
        37: 'Мудрость - План блаженства',
        54: 'Выражение Бога через себя - Высшее сознание'
    }
    condition = {
        1: 'Рождение',
        3: 'Гнев',
        5: 'Род',
        11: 'Развлечение',
        14: 'Астральный план, связь',
        15: 'План фантазии',
        18: 'План радости',
        19: 'План кармы, действия',
        21: 'Искуплнение, исправление',
        23: 'Уверенность',
        25: 'Хорошая компания',
        26: 'Печаль',
        30: 'Хорошие тенденции',
        31: 'Встреча с учителем',
        33: 'План ароматов',
        34: 'План вкуса',
        36: 'Ясность осознания',
        38: 'Энергия',
        39: 'Отпускание',
        40: 'Восстановления энергетической целостности',
        42: 'Огонь',
        43: 'Рождение человека',
        47: 'План нейтральности',
        48: 'Солнечный план',
        49: 'Лунный план',
        53: 'Вода',
        56: 'Звук',
        57: 'Воздух',
        58: 'Расширение сознания',
        59: 'Реальность',
        64: 'Феноменальный план',
        65: 'План внутреннего пространства',
        2: 'Обнуление',
        4: 'Хотение',
        6: 'Заблуждение',
        7: 'Тщеславие',
        8: 'Неудовлетворенность',
        9: 'Чувственный план',
        13: 'Ничтожность',
        35: 'Чистилище',
        51: 'Земля',
        23: 'Уверенность',
        32: 'План равновесия',
        41: 'Реализация',
        50: 'Преодоление',
        60: 'Верно направленное сознание',
        62: 'Счастье',
        66: 'План блаженства',
        67: 'Оставление концепций и отождествлений',
        68: 'Высшее сознание',
        69: 'Созидание'

    }
    # for cell in printed_games:
    #     if cell.id in snake.keys():
    #         form.text.data += Template.query.filter_by(name='emoji_cell_type').first().description + bold(snake[cell.id])
    #         if printed_games[cell] > 1:
    #             form.text.data += bold(f' ({printed_games[cell]} р.)')
    #         form.text.data += newline

    for game in games:
        if game.cell.id in snake:
            form.text.data += p(Template.query.filter_by(name='snake_emoji').first().description + " " + bold(snake[game.cell.id]))

    form.text.data += p('_____________________________________________________________')

    form.text.data += p(Template.query.filter_by(name='arrow').first().description)

    for game in games:
        if game.cell.id in arrow:
            form.text.data += p(Template.query.filter_by(name='arrow_emoji').first().description + " " + bold(arrow[game.cell.id]))

    form.text.data += p('_____________________________________________________________')

    form.text.data += p(Template.query.filter_by(name='condition').first().description)

    for game in games:
        if game.cell.id in condition:
            form.text.data += p(Template.query.filter_by(name='condition_emoji').first().description + " " + bold(condition[game.cell.id]))

    form.text.data += p('_____________________________________________________________')

    form.text.data += p(bold('ОТЧЕТ: ')) + p(i('Здесь вписывается финальный  комментарий'))
    return render_template('report.html', user=user, form=form)
