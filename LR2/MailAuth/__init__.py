import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin



db = SQLAlchemy()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'THIS IS AN INSECURE SECRET')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.googlemail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'email@example.com') 
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', '"Flask" <noreply@example.com>')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'password')

db.init_app(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    login = db.Column(db.String(1000))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    tmp_pwd = db.Column(db.String(100))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# blueprint for auth routes in our app
from .auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

# blueprint for non-auth parts of app
from .main import main as main_blueprint
app.register_blueprint(main_blueprint)

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager


db = SQLAlchemy()
def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'THIS IS AN INSECURE SECRET')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite')
    # app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.googlemail.com')
    # app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
    # app.config['MAIL_USE_TLS'] = True
    # app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'email@example.com') 
    # app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', '"MyApp" <noreply@example.com>')
    # app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'password')

    db.init_app(app)
    # mail = Mail(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app

db.create_all(app=create_app())

