from flask import Blueprint, render_template
from .models import User, Review
from flask_login import login_user, login_required, logout_user, current_user



contact = Blueprint('contact', __name__)
@contact.route('/contact', methods=['GET', 'POST'])
def home():
    return render_template("contact.html", user=current_user)

from datetime import datetime
# Create a datetime object with your date and time
date_time = datetime.now()
# Format the datetime object in XML Sitemap format
formatted_date_time = date_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
from . import sitemap
@sitemap.register_generator                                                      # +
def index():
    '''generate URLs using language codes

       Note. used by flask-sitemap
     '''
    yield 'contact.home', {}, formatted_date_time, 'monthly', 0.7