__author__ = 'sikho'

import hashlib
import json
import md5
import os
from flask import Flask, session, request, flash, url_for, redirect, render_template, abort, g, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required
from models import *
from app import app, db, login_manager, migrate, mail
from forms import CommentForm, SigninForm, SignupForm, PortoForm, AddTask
from flask.ext.sqlalchemy import get_debug_queries
from config import DATABASE_QUERY_TIMEOUT, ALLOWED_EXTENSIONS
from flask.ext.mail import Message
from werkzeug.utils import secure_filename

@app.after_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= DATABASE_QUERY_TIMEOUT:
            app.logger.warning("SLOW QUERY: %s\nParameters: %s\nDuration: %fs\nContext: %s\n" % (query.statement,
                                                                                                 query.parameters,
                                                                                                 query.duration,
                                                                                                 query.context))
    return response

@app.before_request
def before_request():
    g.user = current_user



@app.route('/')
@login_required
def index():
    return render_template('index.html')




@app.route('/dashboard_list')
@login_required
def dashboard_list():
    projects = Project.query.filter_by(user_id=g.user.id).order_by(Project.start_date.desc()).all()
    tasks = Task.query.filter_by(user_id=g.user.id, status='1').order_by(Task.due_date.desc()).all()
    closed_tasks = Task.query.filter_by(user_id=g.user.id, status='0').order_by(Task.due_date.desc()).all()
    contacts=Contact.query.filter_by(user_id=g.user.id).all()
    comments=Comment.query.filter_by(user_id=g.user.id).order_by(Comment.timestamp.desc()).all()
    return render_template('dashboard_list.html', projects=projects, tasks=tasks, closed_tasks=closed_tasks,
                           contacts=contacts, comments=comments)




@app.route('/project_list')
@login_required
def project_list():
    return render_template('project_list.html', projects=Project.query.filter_by(user_id=g.user.id).order_by(
       Project.start_date.desc()).all())


@app.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        if not request.form['name']:
            flash('Name is required', 'error')
        elif not request.form['desc']:
            flash('Description is required', 'error')
        else:
            project = Project(request.form['name'], request.form['desc'])
            project.user = g.user
            db.session.add(project)
            db.session.commit()
            flash("Project item added successfully")
            return redirect(url_for('project_list'))
    return render_template('new_project.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/delete/<int:project_id>')
@login_required
def delete(project_id):
    project = Project.query.get(project_id)
    if project is None:
        flash('Project not found.')
        return redirect(url_for('index'))
    if project.user.id != g.user.id:
        flash('You cannot delete this project.')
        return redirect(url_for('project_list'))
    db.session.delete(project)
    db.session.commit()
    flash('Your project has been deleted.')
    return redirect(url_for('project_list'))

@app.route('/todos/<int:project_id>', methods=['GET', 'POST'])
@login_required
def show_or_update(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == 'GET':
        return render_template('edit_project.html', todo=project)
    if project.user.id == g.user.id:
        project.name = request.form['name']
        project.desc = request.form['desc']
        db.session.add(project)
        db.session.commit()
        flash('Updated successfully')
        return redirect(url_for('index'))
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/task_list')
@login_required
def task_list():

    tasks=Task.query.filter_by(user_id=g.user.id, status='1').order_by(Task.due_date.desc()).all()
    closed_tasks=Task.query.filter_by(user_id=g.user.id, status='0').order_by(Task.due_date.desc()).all()

    return render_template('task_list.html', tasks=tasks, closed_tasks=closed_tasks)

    #return render_template('task_list.html',
    #                        tasks=Task.query.filter_by(user_id=g.user.id).order_by(Task.start_date.desc()).all())


@app.route('/post/<int:id>', methods=['GET', 'POST'])
@login_required
def post(id):
    comment = None
    task = Task.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, task=task, author=current_user._get_current_object())
        comment.task = g.user
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.')
        #return redirect(url_for('task_list'))
        return redirect(url_for('post', id=task.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (task.comments.count() - 1)
        app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = task.comments.order_by(Comment.timestamp.asc()).paginate(page,
                                    per_page=app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('post.html', task=task, form=form, comments=comments, pagination=pagination)
    #return render_template('comment_add.html', task=task, form=form)

@app.route('/new_contact', methods=['GET', 'POST'])
@login_required
def new_contact():
    if request.method == 'POST':
        if not request.form['first_name']:
            flash('Name is required', 'error')
        elif not request.form['email']:
            flash('Email is required', 'error')
        else:
            contact = Contact(request.form['first_name'], request.form['last_name'], request.form['email'],
                              request.form['home_number'], request.form['work_number'],request.form['cell_number'],
                              )
            contact.contact = g.user
            db.session.add(contact)
            db.session.commit()
            flash("Contacts added successfully")
            return redirect(url_for('contact_list'))
    return render_template('new_contact.html')


@app.route('/edit_contact/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_contact(id):
    contact = Contact.query.get_or_404(id)
    if request.method == 'GET':
        return render_template("edit_contact.html",  contact=contact)
    if contact.contact.id == g.user.id:
        contact.first_name = request.form['first_name']
        contact.last_name = request.form['last_name']
        contact.email = request.form['email']
        contact.cell_number = request.form['cell_number']
        contact.contact = g.user
        db.session.add(contact)
        db.session.commit()
        flash("Contacts updated successfully")
        return redirect(url_for('contact_list'))
    return redirect(request.args.get('next') or url_for('index'))



@app.route('/delete/<int:contact_id>')
@login_required
def delete_contact(contact_id):
    contact = Contact.query.get(contact_id)
    if contact is None:
        flash('Contact not found.')
        return redirect(url_for('contact_list'))
    if contact.contact.id != g.user.id:
        flash('You cannot delete this contact.')
        return redirect(url_for('contact_list'))
    db.session.delete(contact)
    db.session.commit()
    flash('Your contact has been deleted.')
    return redirect(url_for('contact_list'))


@app.route('/contact_list')
@login_required
def contact_list():
    return render_template('contact_list.html',
                           contacts=Contact.query.filter_by(user_id=g.user.id).all())



@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'GET':
        return render_template('edit_task.html', mytask=task)
    if task.poster.id == g.user.id:

        task.name = request.form['name']
        task.desc = request.form['desc']

        task.done = ('done.%d' % task_id) in request.form

        db.session.add(task)
        db.session.commit()
        flash('Updated successfully')
        return redirect(url_for('task_list'))
    return redirect(request.args.get('next') or url_for('task_list'))


@app.route('/delete_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task is None:
        flash("Task not found")
        return redirect(url_for('task_list'))
    if task.poster.id != g.user.id:
        flash('You cannot delete this task.')
        return redirect(url_for('index'))
    db.session.delete(task)
    db.session.commit()
    flash('Task Deleted successfully')
    return redirect(url_for('task_list'))


@app.route('/')
@app.route('/<username>')
def username(username=None):
    if username is None:
        return render_template('index.html', page_title='Biography just for you!', signin_form=SigninForm(), portoform=PortoForm())

    user = User.query.filter_by(username=username).first()
    if user is None:
        user = User()
        user.username = username
        user.fullname = 'Batman, is that you?'
        user.tagline = 'Tagline of how special you are'
        user.bio = 'Explain to the rest of the world, why you are the very most unique person to look at'
        user.avatar = '/static/batman.jpeg'
        return render_template('themes/water/bio.html', page_title='Claim this name : ' + username, user=user, signin_form=SigninForm())
    else:
        return render_template('themes/water/bio.html', page_title=user.fullname, user=user, signin_form=SigninForm(), portoform=PortoForm())


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        form = SignupForm(request.form)
        if form.validate():
            user = User()
            form.populate_obj(user)

            user_exist = User.query.filter_by(username=form.username.data).first()
            email_exist = User.query.filter_by(email=form.email.data).first()

            if user_exist:
                form.username.errors.append('Username already taken')

            if email_exist:
                form.email.errors.append('Email already use')

            if user_exist or email_exist:
                return render_template('signup.html',
                                       signin_form=SigninForm(),
                                       form=form,
                                       page_title='Signup to Bio Application')

            else:
                user.fullname = "Your fullname"
                user.password = hash_string(user.password)
                user.tagline = "Tagline of how special you are"
                user.bio = "Explain to the rest of the world why you are the very most unique person to have a look at"
                user.avatar = '/static/batman.jpeg'

                db.session.add(user)
                db.session.commit()
                return render_template('signup-success.html',
                                       user=user,
                                       signin_form=SigninForm(),
                                       page_title='Sign Up Success!')

        else:
            return render_template('signup.html',
                                   form=form,
                                   signin_form=SigninForm(),
                                   page_title='Signup to Bio Application')
    return render_template('signup.html',
                           form=SignupForm(),
                           signin_form=SigninForm(),
                           page_title='Signup to Bio Application')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        if current_user is not None and current_user.is_authenticated():
            return redirect(url_for('index'))

        form = SigninForm(request.form)
        if form.validate():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None:
                form.username.errors.append('Username not found')
                return render_template('signinpage.html',  signinpage_form=form, page_title='Sign In to Bio Application')
            if user.password != hash_string(form.password.data):
                form.password.errors.append('Passwod did not match')
                return render_template('signinpage.html',  signinpage_form=form, page_title='Sign In to Bio Application')

            login_user(user, remember=form.remember_me.data)

            session['signed'] = True
            session['username']= user.username

            if session.get('next'):
                next_page = session.get('next')
                session.pop('next')
                return redirect(next_page)
            else:
                return redirect(url_for('index'))
        return render_template('signinpage.html',  signinpage_form=form, page_title='Sign In to Bio Application')
    else:
        session['next'] = request.args.get('next')
        return render_template('signinpage.html', signinpage_form=SigninForm())


@app.route('/signout')
@login_required
def signout():
    logout_user()
    session.pop('signed')
    session.pop('username')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', page_title='Customize your profile')


def hash_string(string):
     """
     Return the md5 hash of a (string+salt)
     """
     salted_hash = string + app.config['SECRET_KEY']
     return md5.new(salted_hash).hexdigest()


@app.route('/portfolio_add_update', methods = ['POST'])
@login_required
def portfolio_add_update():

    form = PortoForm(request.form)
    if form.validate():
        result={}
        result['iserror'] = False

        if not form.portfolio_id.data:
            user = User.query.filter_by(username=session['username']).first()
            if user is not None:
                user.portfolio.append(Portfolio(title=form.title.data, description=form.description.data, tags=form.tags.data))
                print 'id ', form.portfolio_id
                db.session.commit()
                result['savedsuccess'] = True
            else:
                result['savedsuccess'] = False
        else:
            portfolio = Portfolio.query.get(form.portfolio_id.data)
            form.populate_obj(portfolio)
            db.session.commit()
            result['savedsuccess'] = True

        return json.dumps(result)

    form.errors['iserror'] = True
    print form.errors
    return json.dumps(form.errors)


@app.route('/portfolio_get/<id>')
@login_required
def portfolio_get(id):
    portfolio = Portfolio.query.get(id)
    return json.dumps(portfolio._asdict())


@app.route('/portfolio_delete/<id>')
@login_required
def portfolio_delete(id):
    portfolio = Portfolio.query.get(id)
    db.session.delete(portfolio)
    db.session.commit()
    result={}
    result['result'] = 'success'
    return json.dumps(result)


@app.route('/user_edit_fullname', methods=['GET', 'POST'])
def user_edit_fullname():
    id = request.form["pk"]
    user = User.query.get(id)
    user.fullname = request.form["value"]
    result = {}
    db.session.commit()
    return json.dumps(result)


@app.route('/user_edit_tagline', methods=['GET', 'POST'])
def user_edit_tagline():
    id = request.form["pk"]
    user = User.query.get(id)
    user.tagline = request.form["value"]
    result = {}
    db.session.commit()
    return json.dumps(result)


@app.route('/user_edit_biography', methods=['GET', 'POST'])
def user_edit_biography():
    id = request.form["pk"]
    user = User.query.get(id)
    user.bio = request.form["value"]
    result = {}
    db.session.commit()
    return json.dumps(result)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/user_upload_avatar', methods=['POST'])
def user_upload_avatar():
    if request.method == 'POST':
        id = request.form["avatar_user_id"]
        file = request.files['file']
        if file and allowed_file(file.filename):
            user = User.query.get(id)
            filename = user.username + "_" + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img = "/static/upload/" + filename

            user.avatar = img
            db.session.commit()
            return img


@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
        form = AddTask(request.form, csrf_enabled=False)
        if form.validate():
            new_task = Task(form.name.data, form.due_date.data, form.priority.data,form.start_date.data,
                            form.task_type.data, form.state.data,'1','1',)

            new_task.poster = g.user
            db.session.add(new_task)
            db.session.commit()
            flash('New entry was successfully posted. Thanks.')
            return redirect(url_for('task_list'))
        else:
            return render_template('tasks.html')


@app.route('/complete/<int:task_id>/')
@login_required
def complete(task_id):
        new_id = task_id
        db.session.query(Task).filter_by(id=new_id).update({"status": "0"})
        db.session.commit()
        flash('The task was marked as complete. Nice.')
        return redirect(url_for('tasks'))

@app.route('/delete/<int:task_id>/',)
@login_required
def delete_entry(task_id):
    new_id = task_id
    db.session.query(Task).filter_by(id=new_id).delete()
    db.session.commit()
    flash('The task was deleted. Why not add a new one?')
    return redirect(url_for('tasks'))


@app.route('/tasks')
@login_required
def tasks():
    tasks = Task.query.filter_by(user_id=g.user.id, status='1').order_by(Task.start_date.asc())
    closed_tasks = Task.query.filter_by(user_id=g.user.id, status='2').order_by(Task.start_date.asc())
    work = Task.query.filter(user_id=g.user.id, state='1',task_type=2).order_by(Task.start_date.asc())
    customer = Task.query.filter_by(user_id=g.user.id, state='2', task_type=2).order_by(Task.start_date.asc())
    personal = Task.query.filter_by(user_id=g.user.id, state='3', task_type=3).order_by(Task.start_date.asc())
    return render_template('tasks.html', form=AddTask(request.form), tasks=tasks, closed_tasks=closed_tasks,
                           work=work, customer=customer, personal=personal)


#@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
##@login_required
#def edit_task(task_id):
#    task = Task.query.get_or_404(task_id)
#    if request.method == 'GET':
#        return render_template('edit_task.html', mytask=task)
#    if task.poster.id == g.user.id:

#        task.name = request.form['name']
#        task.desc = request.form['desc']

#        task.done = ('done.%d' % task_id) in request.form

#        db.session.add(task)
#        db.session.commit()
#        flash('Updated successfully')
#        return redirect(url_for('task_list'))task.poster.id == g.user.id:
    #else:
    #    comment = Comment(request.form['body'])

            # Add it to the SQLAlchemy session and commit it to
            # save it to the database
    #    db.session.add(comment)
    #    db.session.commit()
#    return redirect(request.args.get('next') or url_for('task_list'))


@app.route('/edit_post/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_post(task_id):
    task = Task.query.get_or_404(task_id)
    if request.method == 'GET':
        return render_template('test_edit.html', task=task)

    #form = AddTask(request.form, csrf_enabled=False)

    if task.poster.id == g.user.id:
        task.name = request.form['name']
        task.due_date = request.form['due_date']
        task.priority = request.form['priority']
        task.status = 1
        task.start_date = request.form['start_date']
        task.done = ('done.%d' % task_id) in request.form
        db.session.add(task)
        db.session.commit()
        flash('Task updated successfully')
        return redirect(url_for('task_list'))
    return redirect(url_for('task_list'))
    #else:
    #    form.name.data = task.name
    #    form.due_date.data = task.due_date
    #    form.priority.data = task.priority
    #   form.status.data = task.status
    #    form.start_date.data = task.start_date
    #return render_template('test_edit.html', task=task)

@app.route('/show_all')
@login_required
def show_all():
    return render_template('comments_all.html',
                         comments=Comment.query.filter_by(user_id=g.user.id).order_by(Comment.timestamp.desc()).all())


# This view method responds to the URL /new for the methods GET and POST
@app.route('/comment_add', methods=['GET', 'POST'])
@login_required
def comment_add():

    form = CommentForm()
    if request.method == "POST":
        if form.validate():
            return render_template('comment_add.html', form=form)
        else:
            comment = Comment(form.body.data)
            comment.author = g.user
            db.session.add(comment)
            db.session.commit()
            flash('Comment created successfully')
            return redirect(url_for('show_all'))
    return render_template("comment_add.html", form=form)

@app.route('/comment/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_comment(id):
    if request.method == 'POST':
        form = CommentForm()
        if form.validate():
            comment = Comment.query.filter_by(id=id).first()
            comment.body = form.body.data
            db.session.merge(comment)
            db.session.commit()
            flash('Comment updated successfully')
            return render_template('comments_all.html', comments=Comment.query.order_by(Comment.timestamp.desc()).all())

    elif request.method == 'GET':
        comment = Comment.query.get_or_404(id)
        form = CommentForm(id=comment.id, comment= comment.body)
        return render_template('edittag.html', tag_id=comment.id, form=form)

@app.route('/delete_comment/<int:id>')
@login_required
def delete_comment(id):
    comment = Comment.query.filter_by(id=id).first()
    db.session.delete(comment)
    db.session.commit()
    return render_template('comments_all.html', comment=Comment.query.all())

#look at pypress important
@app.route("/<int:task_id>/addcomment/", methods=("GET", "POST"))
@app.route('/<int:task_id><int:id>/reply', methods=['GET', 'POST'])
#@app.route("/<int:comment_id>/", methods=("GET", "POST"))
def add_comment(task_id):
    task = Task.query.get_or_404(task_id)
    form = CommentForm()
    if request.method == "POST":
        if form.validate():
            return render_template('comment_add.html', form=form)
        else:
            comment = Comment(form.body.data)
            comment.author = g.user
            db.session.add(comment)
            db.session.commit()
            flash('Comment created successfully')
            return redirect(url_for('show_all'))
    return render_template("comment_add.html", form=form)

