from flask import Flask, render_template, request, redirect,url_for,session
import data_manager
import random
import datetime
import time
from flask_bootstrap import Bootstrap
from functools import wraps
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
import passhash as ph

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
Bootstrap(app)
app.secret_key = "secretkey"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER




class LoginForm(FlaskForm):
    username = StringField('Username:', validators=[InputRequired(),Length(min=4, max=15)])
    password = PasswordField('Password:', validators=[InputRequired(),Length(min=8, max=80)])
    remember = BooleanField('Remember Me')

class RegisterForm(FlaskForm):
    email = StringField('Email:', validators=[InputRequired(),Email(message='Invalid email'),Length(max=50)])
    first_name = StringField('First Name:', validators=[InputRequired(), Length(max=50)])
    last_name = StringField('Last Name:', validators=[InputRequired(), Length(max=50)])
    username = StringField('Username:', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password:', validators=[InputRequired(), Length(min=8, max=80)])

#check if user is logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap
# nu sunt sigur ca merge ( snippet luat de pe documentatia de flask)


def get_question_by_id(id):
    questions = data_manager.get_data('question')
    for question in questions:
        if question['id'] == id:
            return question


def key_generator():
    key = random.randint(1000000,   10000000)
    return key


def get_current_timestamp():
    timestamp = time.time()
    return round(timestamp)


def get_current_datetime():
    current_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return current_datetime


@app.route('/')
@app.route('/search')
def index():
    questions = data_manager.display_latest_five_questions()
    query = False
    if request.args:
        pattern = request.args.get('q')
        search_results = data_manager.search_question_pattern(pattern)
        query = True
        return render_template('index.html', search_results=search_results, query=query, pattern=pattern)
    return render_template('index.html', questions=questions, query=query)


@app.route('/list', methods=['GET', 'POST'])
@is_logged_in
def display_q():
    questions = data_manager.get_data('question')
    entries = questions
    sort_by = 'submission_time'
    if request.args.get('sort_by') == 'sorted_by' and request.args.get('asc_dsc') == 'asc' or request.args.get(
            'sort_by') == 'sorted_by' and request.args.get('asc_dsc') == 'desc':
        entries = sorted(questions, key=lambda questions: questions[sort_by])
    elif request.args.get('sort_by') is not None and request.args.get('asc_dsc') is not None:
        ascdsc = request.args.get('asc_dsc')
        sort_by = request.args.get('sort_by')
        if ascdsc == 'asc':
            entries = sorted(questions, key=lambda questions: questions[sort_by], reverse=False)
        elif ascdsc == 'desc':
            entries = sorted(questions, key=lambda questions: questions[sort_by], reverse=True)

    return render_template('list.html', questions=entries, sort_by=sort_by, asc_dsc=request.args.get('asc_dsc'))


@app.route('/question/<question_id>')
@is_logged_in
def display_one_question(question_id):
    question_id = int(question_id)
    question = get_question_by_id(question_id)
    answers = data_manager.get_answers_for_question(question_id)
    temp_count = data_manager.get_count_number(question_id)
    count = temp_count['view_number']
    data_manager.update_view_count(count,question_id)
    answer_id_list = []
    user_id = []
    for answer in answers:
        answer_id_list.append(str(answer['id']))
        user_id.append(str(answer['user_id']))
    while 'None' in user_id:
        user_id.remove('None')
    answer_comment = data_manager.get_comments_for_answers(question_id,answer_id_list)
    question_comments = data_manager.get_comments_for_question(question_id)
    tag = data_manager.get_tags(question_id)
    user = data_manager.get_user_for_question(question_id)
    answer_users = data_manager.user_for_answer(user_id)
    if user:
        user_name = user['user_name']
    else:
        user_name = 'No User Available'
    return render_template('questions.html',
                           question_id=question_id,
                           question=question,
                           answers=answers,
                           answer_comments=answer_comment,
                           question_comments=question_comments,
                           tags=tag,
                           username=user_name,
                           answer_users=answer_users)

@app.route('/add_question')
@is_logged_in
def add_question():
    return render_template('add_question.html')


@app.route('/add-question-todb', methods=['GET', 'POST'])
@is_logged_in
def add_question_todb():
    title = request.form['title']
    print(title)
    message = request.form['message']
    data = data_manager.get_user_id_from_username(session['username'])
    user_id = data['id']
    data_manager.add_questions(title, message,user_id)
    return redirect("/list")


@app.route('/question/<question_id>/edit', methods=['GET','POST'])
@is_logged_in
def edit_question(question_id):
    question_id = int(question_id)
    question = get_question_by_id(question_id)
    return render_template('edit_question.html', question=question)



@app.route('/edit-question-todb/<question_id>', methods=['GET', 'POST'])
@is_logged_in
def edit_question_to_csv(question_id):
    question_id = int(question_id)
    title = request.form['title']
    message = request.form['message']
    data_manager.update_question(question_id, title, message)
    return redirect('/question/' + str(question_id))


@app.route('/question/<question_id>/new_answer/', methods=['GET', 'POST'])
@is_logged_in
def question_new_answer(question_id):
    question_id = int(question_id)
    if request.method == 'POST':
        answer = request.form.get('text')
        data = data_manager.get_user_id_from_username(session['username'])
        user_id = data['id']
        data_manager.post_answer(question_id, answer,user_id)
        return redirect('/question/' + str(question_id))
    question = get_question_by_id(question_id)
    return render_template('add_answer.html', question=question)


@app.route('/answer/<answer_id>/edit')
@is_logged_in
def get_answer(answer_id):
    answer = data_manager.get_answer(answer_id)
    return render_template('edit_answer.html', answer=answer)


@app.route('/edit_answer_todb/<answer_id>', methods = ['GET', 'POST'])
@is_logged_in
def edit_answer(answer_id):
    message = request.form['message']
    data_manager.update_answer(answer_id, message)
    question_id = data_manager.get_question_id_from_answer_id(answer_id)[0]
    return redirect(url_for('display_one_question', question_id=question_id['id']))



@app.route('/answer/<answer_id>/delete')
@is_logged_in
def delete_answer_from_db(answer_id):
    question_id = data_manager.get_question_id(answer_id)
    data_manager.delete_answer(answer_id)
    return redirect(url_for('display_one_question', question_id=question_id))

@app.route('/question/<question_id>/delete')
@is_logged_in
def delete_from_db(question_id):
    data_manager.delete_from_table(question_id)
    return redirect('/list')

@app.route('/question/<question_id>/vote_up/', methods=['GET', 'POST'])
@is_logged_in
def vote_up(question_id):
    data_manager.vote_up_question(question_id)
    user_id = data_manager.get_question_owner(question_id)
    if user_id == None:
        return redirect(request.referrer)
    else:
        owner_user = data_manager.get_user_name_after_id(user_id)
        vote = 1
        data_manager.edit_reputation(vote, 'question', owner_user)
        return redirect(request.referrer)

@app.route('/question/<question_id>/vote_down/', methods=['GET', 'POST'])
@is_logged_in
def vote_down(question_id):
    data_manager.vote_down_question(question_id)
    user_id = data_manager.get_question_owner(question_id)
    if user_id == None:
        return redirect(request.referrer)
    else:
        owner_user = data_manager.get_user_name_after_id(user_id)
        vote = -1
        data_manager.edit_reputation(vote, 'question', owner_user)
        return redirect(request.referrer)

@app.route('/answer/<answer_id>/vote_up')
@is_logged_in
def vote_up_answer(answer_id):
    data_manager.vote_up_answer(answer_id)
    user_id = data_manager.get_answer_owner(answer_id)
    if user_id == None:
        return redirect(request.referrer)
    else:
        owner_user = data_manager.get_user_name_after_id(user_id)
        vote = 1
        data_manager.edit_reputation(vote, 'answer', owner_user)
        return redirect(request.referrer)

@app.route('/answer/<answer_id>/vote_down')
@is_logged_in
def vote_down_answer(answer_id):
    data_manager.vote_down_answer(answer_id)
    user_id = data_manager.get_answer_owner(answer_id)
    if user_id == None:
        return redirect(request.referrer)
    else:
        owner_user = data_manager.get_user_name_after_id(user_id)
        vote = -1
        data_manager.edit_reputation(vote, 'answer', owner_user)
        return redirect(request.referrer)


@app.route("/question/<question_id>/new-tag", methods=['GET', 'POST'])
@is_logged_in
def add_tag(question_id):
    if request.method =='POST':
        tag = request.form.get('tag')
        data_manager.add_new_tag(tag)
        data_manager.add_new_tag_id(question_id)
    return redirect(request.referrer)

@app.route('/question/<question_id>/new-comment', methods=['GET', 'POST'])
@is_logged_in
def new_question_comment(question_id=None):
    data = data_manager.get_user_id_from_username(session['username'])
    user_id = data['id']
    if request.method == 'POST':
        question_comment = {
            'id': key_generator(),
            'question_id': question_id,
            'message': request.form.get('message'),
            'submission_time': get_current_datetime(),
            'edited_count': '0',
            'user_id': user_id
             }
        data_manager.add_new_question_comment(question_comment)
        return redirect(url_for('display_one_question', question_id=question_id))

    return render_template('all_comment_functions.html',
                           page_title='Add comment to question',
                           button_title='Submit comment',
                           question_id=question_id)


@app.route('/answer/<answer_id>/new-comment', methods=['GET', 'POST'])
@is_logged_in
def new_answer_comment(answer_id=None):
    data = data_manager.get_user_id_from_username(session['username'])
    user_id = data['id']
    if request.method == 'POST':
        answer_comment = {
            'id': key_generator(),
            'answer_id': answer_id,
            'message': request.form.get('message'),
            'submission_time': get_current_datetime(),
            'edited_count': '0',
            'user_id':user_id
             }
        data_manager.add_new_answer_comment(answer_comment)
        question_id = data_manager.get_answer_data_by_answer_id(answer_id)[0]
        return redirect(url_for('display_one_question', question_id=question_id['question_id']))

    return render_template('all_comment_functions.html',
                           page_title='Add comment to answer',
                           button_title='Submit comment',
                           answer_id=answer_id)

@app.route('/comments/<comment_id>/delete', methods=['GET'])
@is_logged_in
def del_comment(comment_id):
    q_and_a_id = data_manager.get_q_and_a_id_from_comment(comment_id)
    data_manager.delete_comment(comment_id)
    if q_and_a_id[0]['answer_id']:
        answer_id = q_and_a_id[0]['answer_id']
        question_id = data_manager.get_question_id_from_answer_id(answer_id)
        question_id = question_id[0]['id']
    else:
        question_id = q_and_a_id[0]['question_id']
    return redirect(url_for('display_one_question', question_id=question_id))

@app.route('/<question_id>/comments/<comment_id>/edit', methods=['GET', 'POST'])
@is_logged_in
def edit_comment(question_id=None, comment_id=None):
    if request.method == 'POST':
        comment = data_manager.get_comment(comment_id)[0]
        comment['message'] = request.form.get('message')
        comment['edited_count'] += 1
        data_manager.edit_comment(comment)
        return redirect(url_for('display_one_question', question_id=question_id))

    comment = data_manager.get_comment(comment_id)[0]

    return render_template('all_comment_functions.html',
                           page_title='Edit comment',
                           button_title='Edit comment',
                           comment=comment,
                           question_id=question_id
                           )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if request.method == "POST":
        if form.validate_on_submit():
            hash_pass = ph.hash_password(form.password.data)
            last_name = form.last_name.data
            first_name = form.first_name.data
            email = form.email.data
            user_name = form.username.data
            existing_user = data_manager.existing_user(user_name,email)
            if len(existing_user) == 0:
                data_manager.add_user(user_name, first_name, last_name, email, hash_pass)
                return render_template('signup.html', form=form, status='user_created')
            else:
                return render_template('signup.html', form=form, status='user_exist')
    return render_template('signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        result = data_manager.get_user(request.form['username'])
        if result == None:
            return render_template('login.html', status='not_ok')
        elif len(result) > 0:
            password = result['password']
            username = result['user_name']
            check = ph.verify_password(request.form['password'], password)
            if check == True:
                session['logged_in'] = True
                session['username'] = username
                temp_dict = data_manager.get_user_id_from_username(username)
                session['user_id'] = temp_dict['id']
                return redirect(url_for('display_q'))
            elif check == False:
                return render_template('login.html', status='not_ok')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session['logged_in'] = False
    session.clear()
    return redirect(url_for('index'))

@app.route('/users')
@is_logged_in
def show_users():
    data = data_manager.get_all_users()
    return render_template('users.html', data=data)


@app.route('/user/<user_id>')
@is_logged_in
def route_user_activity(user_id):
    id_check = False
    questions_dict_list = []
    answers_dict_list = []
    comments_dict_list = []
    if int(user_id) == session['user_id']:
        id_check = True
        questions_dict_list = data_manager.get_questions_by_user_id(user_id)
        answers_dict_list = data_manager.get_answers_by_user_id(user_id)
        comments_dict_list = data_manager.get_comments_by_user_id(user_id)
        user_details = data_manager.get_user_after_id(user_id)
    return render_template('user_page.html', id_check=id_check, questions_dict_list=questions_dict_list,
                           answers_dict_list=answers_dict_list, comments_dict_list=comments_dict_list, user_details=user_details)


@app.route('/mark-accepted/<answer_id>/<question_id>')
def route_mark_accepted(answer_id, question_id):
    data_manager.mark_answer_as_accepted(answer_id)
    return redirect(url_for('display_one_question', question_id=question_id))


@app.route('/unmark/<answer_id>/<question_id>')
def route_unmark_answer(answer_id, question_id):
    data_manager.unmark_accepted_answer(answer_id)
    return redirect(url_for('display_one_question', question_id=question_id))

@app.route('/test_page')
@is_logged_in
def test_page():
    user_id = session['user_id']
    fav_questions = data_manager.fav_questions(user_id)
    return render_template('test_page.html', fav_questions = fav_questions)


@app.route('/tags')
@is_logged_in
def showtags():
    tags = data_manager.get_tagz()
    return render_template('tags.html', tags=tags)

if __name__ == "__main__":
    app.run(
        threaded=True,
        host='0.0.0.0',
        debug=True,
        port=5000
    )
