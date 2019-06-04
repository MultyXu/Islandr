from flask import render_template, session, redirect, url_for, current_app, flash, request, Markup, abort
from flask_login import login_required, current_user
from .. import db
from ..models import User, Post
from ..email import send_email
from . import main
from .forms import EditorForm, UpdateAccountForm
from ..decorators import admin_required
from datetime import datetime
import secrets
import os
from PIL import Image


time_format = '%Y-%m-%d-%H:%M'

@main.route('/', methods=['GET', 'POST'])
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

@main.route('/editor', methods=['GET', 'POST'])
@login_required
def editor():

    if request.method == 'POST':
        if not request.form['content'] or not request.form['title'] or not request.form['datetime_from'] or not request.form['datetime_to']:
            flash('Please fill in all forms!')
            return redirect(url_for('.editor'))

        post = Post(title=request.form['title'],
                    location=request.form['location'],
                    tag=request.form['tag'],
                    datetime_from = datetime.strptime(request.form['datetime_from'], time_format),
                    datetime_to = datetime.strptime(request.form['datetime_to'], time_format),
                    author=current_user,
                    post_html=request.form['content'].replace('\r\n', '')
        )
        print(request.form['tag'])
        print(type(request.form['tag']))
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('event.post', id=post.id))
    _post = Post(title='', location='', post_html='')
    return render_template('editor.html', old_post=_post, old_time_from='', old_time_to='')


@main.route('/approve', methods=['GET', 'POST'])
@login_required
@admin_required
def approve():
    posts = Post.query.all()
    return render_template('approve.html', posts=posts)


@main.route('/account/<int:user_id>', methods=['GET', 'POST'])
@login_required
def account(user_id):

    user = User.query.get(user_id)
    profile_pic = url_for('static', filename='profile_pic/' + user.profile_pic)

    return render_template('account.html', user=user, profile_pic=profile_pic)


@main.route('/account/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def account_edit(user_id):

    user = User.query.get(user_id)
    form = UpdateAccountForm()

    if form.validate_on_submit():

        if form.profile_pic.data:
            file_name = save_profile_pic(form.profile_pic.data)
            user.profile_pic = file_name

        user.name = form.name.data
        user.username = form.username.data
        user.location = form.location.data

        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account', user_id=user.id))

    form.name.data = user.name
    form.username.data = user.username
    form.location.data = user.location

    return render_template('edit_account.html', form=form)


def save_profile_pic(form_picture):

    # generate a random file name at standard length
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(form_picture.filename)
    picture_file_name = random_hex + file_extension

    # crop to square and resize the picutre
    i = Image.open(form_picture)

    width, height = i.size
    new_size = min(width, height)

    left = (width - new_size)/2
    top = (height - new_size)/2
    right = (width + new_size)/2
    bottom = (height + new_size)/2

    i = i.crop((left, top, right, bottom))
    i.thumbnail([100, 100])

    # save it to static folder
    picture_path = os.path.join(current_app.root_path, 'static/profile_pic', picture_file_name)
    i.save(picture_path)

    return picture_file_name
