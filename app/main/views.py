from flask import render_template, session, redirect, url_for, current_app, flash, request, Markup, abort
from flask_login import login_required, current_user
from .. import db
from ..models import User, Post, Group
from ..email import send_email
from . import main
from .forms import EditorForm, UpdateAccountForm
from ..decorators import admin_required, owner_required
from datetime import datetime
import os
from PIL import Image


time_format = '%Y-%m-%d-%H:%M'

@main.route('/')
def index():
    posts = Post.query.filter_by(is_approved=1).order_by(Post.last_modified.desc()).all()
    posts = posts[0:9]
    return render_template('index.html', posts=posts)

@main.route('/editor', methods=['GET', 'POST'])
@login_required
@owner_required
def post_editor():

    if request.method == 'POST':
        if not request.form['content'] or not request.form['title'] or not request.form['datetime_from'] or not request.form['datetime_to']:
            flash('Please fill in all forms!')
            return redirect(url_for('.post_editor'))

        post = Post(author=current_user.my_group,
                    title=request.form['title'],
                    location=request.form['location'],
                    tag=request.form['tag'],
                    datetime_from = datetime.strptime(request.form['datetime_from'], time_format),
                    datetime_to = datetime.strptime(request.form['datetime_to'], time_format),
                    post_html=request.form['content'].replace('\r\n', '')
        )
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('event.post', id=post.id))
    _post = Post(title='', location='', post_html='')
    return render_template('editor.html', old_post=_post, old_time_from='', old_time_to='')

@main.route('/creater', methods=['GET', 'POST'])
@login_required
def group_creater():

    if current_user.my_group:
        flash('You already have a group!')
        return redirect(url_for('main.index')) 

    if request.method == 'POST':
        if not request.form['groupname']:
            flash('Please fill in the name!')
            return redirect(url_for('.group_creater'))

        group = Group(groupname=request.form['groupname'],
                      tag=request.form['tag'],
                      about_us=request.form['aboutus'])

        current_user.my_group = group
        db.session.add(group)
        db.session.commit()
        return redirect(url_for('group.group_profile',id=group.id))
    _group = Group()
    return render_template('creater.html', old_group=_group)

@main.route('/moments')
@login_required
def moments():
    #TODO
    return render_template('moments.html')

@main.route('/approve', methods=['GET', 'POST'])
@login_required
@admin_required
def approve():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(is_approved=0).order_by(Post.last_modified.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out = False)
    posts = pagination.items
    return render_template('approve.html', posts=posts, pagination=pagination)

@main.route('/<tag>')
@login_required
def tag_events(tag):

    tag = str(tag).capitalize()
    if not tag in current_app.config['TAGS'].keys():
        abort(404)

    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(tag=tag, is_approved=1).order_by(Post.last_modified.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out = False)
    posts = pagination.items
    tag = tag.lower()
    return render_template('tag.html', posts=posts, pagination=pagination, title=tag)

# @main.route('/my_post/<int:id>')
# @login_required
# def my_post(id):
#     page = request.args.get('page', 1, type=int)
#     user = User.query.get_or_404(id)
#     pagination = user.posts.order_by(Post.last_modified.desc()).paginate(
#         page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
#         error_out = False)
#     posts = pagination.items
#     return render_template('approve.html', posts=posts, pagination=pagination, title='My Events')


@main.route('/account/<int:user_id>', methods=['GET', 'POST'])
@login_required
def account(user_id):
    
    page = request.args.get('page', 1, type=int)
    user = User.query.get_or_404(user_id)
    pagination = user.followings.order_by(Post.datetime_from).paginate(
        page, per_page=9,
        error_out = False)
    posts = pagination.items

    profile_pic = url_for('static', filename='profile_pic/' + user.profile_pic)

    return render_template('account.html', user=user, profile_pic=profile_pic, user_id=user_id, posts=posts, pagination=pagination)


@main.route('/account/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def account_edit(user_id):

    if user_id != current_user.id:
        abort(403)

    user = User.query.get(user_id)
    form = UpdateAccountForm()

    if form.validate_on_submit():

        if form.profile_pic.data:
            file_name = save_profile_pic(form.profile_pic.data, user)
            user.profile_pic = file_name

        user.name = form.name.data
        user.username = form.username.data
        user.location = form.location.data
        user.about_me = form.about_me.data

        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.account', user_id=user.id))

    form.name.data = user.name
    form.username.data = user.username
    form.location.data = user.location
    form.about_me.data = user.about_me

    return render_template('edit_account.html', form=form)


def save_profile_pic(form_picture, user):

    random_hex = user.user_hex
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
