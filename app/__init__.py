import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask_bootstrap import Bootstrap

from werkzeug.contrib.fixers import ProxyFix

from config import config

mail = Mail()
moment = Moment()
bootstrap = Bootstrap()

db = SQLAlchemy()
lm = LoginManager()
lm.login_view = 'main.login'

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    mail.init_app(app)
    moment.init_app(app)
    bootstrap.init_app(app)

    db.init_app(app)
    lm.init_app(app)

    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    app.wsgi_app = ProxyFix(app.wsgi_app)

    if not app.debug:

        import logging
        import sys

        app.logger.addHandler(logging.StreamHandler(sys.stdout))

        app.logger.setLevel(logging.DEBUG)
        app.logger.info('healy startup')

    return app
