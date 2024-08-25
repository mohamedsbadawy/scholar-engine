from flask import Flask, render_template
import os
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from urllib.parse import quote_plus
from datetime import timedelta,datetime
db = SQLAlchemy()
from flask_login import LoginManager
from .mail import mail

from flask_sitemap import Sitemap 


sitemap = Sitemap()
# title="Related Engine Sitemap",  # Set the title here
# description="Explore the world of scholarly research articles an journals impact factors with reviews effortlessly with related Engine "  # Set the description here
# Your actual password
password = 'your DB password here'

# URL-encode the password
encoded_password = quote_plus(password)

def create_app():
    app = Flask(__name__)
    # Generate a random 24-byte (192-bit) secret key
    secret_key = os.urandom(24)
    # Convert the binary key to a hexadecimal string
    secret_key_hex = secret_key.hex()
    app.config['SECRET_KEY'] = secret_key_hex
    # Configure SQLAlchemy to use 'pymysql'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://SQLName:{encoded_password}@localhost:3306/SQLUserName'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable Flask-SQLAlchemy modification tracking
    
    # Configure Flask-Mail
    app.config['MAIL_SERVER'] = 'relengine.com'  # Replace with your SMTP server address
    app.config['MAIL_PORT'] = 465  # Replace with your SMTP server port
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'info@relengine.com'  # Replace with your email address
    app.config['MAIL_PASSWORD'] = '.!DRggB$~fA%'  # Replace with your email password
    mail.init_app(app)

    # Configure Flask-Session
    db.init_app(app)
    app.config['SESSION_TYPE'] = 'filesystem'  # You can choose other storage options as well
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'myapp_'
    # Configure the upload folder and allowed file extensions
    app.config['UPLOAD_FOLDER'] = 'static/assets/'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
    Session(app)
    
    # import modules
    from .pubmed import pubMed
    from .gs import gs 
    from .sp import sp
    from .views import views 
    from .contact import contact
    from .images import images
    from .jobs import jobs
    from .auth import auth
    from .models import User, Review
    from .lib import lib
    from .scijournals import jour
    from .factcheck import factcheck


    app.register_blueprint(gs, url_prefix='/')
    app.register_blueprint(sp, url_prefix='/')
    app.register_blueprint(pubMed, url_prefix='/')
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(contact, url_prefix='/')
    app.register_blueprint(images, url_prefix='/')
    app.register_blueprint(jobs, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(lib, url_prefix='/')
    app.register_blueprint(jour, url_prefix='/')
    app.register_blueprint(factcheck, url_prefix='/')


    # db initiation
    with app.app_context():
        db.create_all()
    
    # Error handling for 404
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html")
        #Handling error 500 and displaying relevant web page
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'),500
    # login manager for auth
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    # sitemap !!
    sitemap.init_app(app)
    @app.route('/sitemap')
    @app.route('/sitemap.xml')
    def ep_sitemap():                            # endpoint for sitemap
        return sitemap.sitemap(), 200, {'Content-Type': 'text/xml', }

    return app
    

