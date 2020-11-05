from flask import Blueprint, render_template, redirect, url_for, request, flash
from . import User
from flask_mail import Mail, Message
from . import db, mail
import random as r
import string
from flask_login import login_user, logout_user, login_required
import re

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/confirm')
def confirm():
    id = request.args.get('key')
    return render_template('confirm.html', key=id)

@auth.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    login = request.form.get('login')
    password = request.form.get('password')

    user_email = User.query.filter_by(email=email).first()
    user_login = User.query.filter_by(login=login).first()
    
    if user_email:
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))
    
    if user_login:
        flash('This login already exists')
        return redirect(url_for('auth.signup'))
    
    r_p = re.compile('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[^\w\s]).{8,}')
    if not bool(r_p.findall(password)):
        flash('Password must be at least 8 characters long.\
            Must contain digits, lowercase and uppervase characters and special characters.')
        return redirect(url_for('auth.signup'))

    new_user = User(email=email, login=login, password=password, tmp_pwd = '')

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['POST'])
def login_post():
    login = request.form.get('login')
    password = request.form.get('password')

    user = User.query.filter_by(login=login).first()

    if not user or password != user.password:
        flash('Please check your login and password')
        return redirect(url_for('auth.login'))
        
    tmp = ''
    for i in range(10):
        tmp += (r.choice(string.ascii_letters + string.digits))
    user.tmp_pwd = tmp
    db.session.commit()

    msg = Message("Confirmation password", recipients=[user.email])
    msg.body = "Use this temper password: " + tmp
    
    try:
        mail.send(msg)
    except:
        flash("Unfortunately, our mail server doesn't work! It'll work \
            when the correct email and password are set(((")
        return redirect(url_for('auth.login'))            

    return redirect(url_for('auth.confirm', key=user.id))

@auth.route('/confirm', methods=['POST'])
def confirm_post():
    tmp = request.form.get('tmp_pwd')
    id = request.form.get('id')
    user = User.query.filter_by(id=int(id)).first()
    if tmp == user.tmp_pwd:
        login_user(user)
        return redirect(url_for('main.profile'))
    else:
        flash('The confirmation code is incorrect!')
        return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
