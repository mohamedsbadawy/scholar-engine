from flask import Blueprint, render_template
from . import db  # Import the db object from your app
from datetime import datetime, timedelta
from .models import User, Review, ImageData
from flask_login import login_user, login_required, logout_user, current_user
from . import sitemap

views = Blueprint('views', __name__)
@views.route('/index.php', methods=['GET', 'POST'])
@views.route('/index.html', methods=['GET', 'POST'])
@views.route('/index', methods=['GET', 'POST'])
@views.route('/', methods=['GET', 'POST'])
def home():
    # current_day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # daily_images = ImageData.query.filter(ImageData.timestamp >= current_day_start).all()
    daily_images = []
    new_image1 = {
        'src': 'https://search.relengine.com/website/static/images/search-engine.webp',
        'title': 'Unlocking the Potential of Academic Search Engines for Effective Research – feat Related Engine',
        'des': 'Discover how to optimize your Academic searches and what Related Engine has to offer',
        'link': 'https://relengine.com/blog/2023/09/19/unlocking-the-potential-of-academic-search-engines/'
    }
    new_image2 = {
        'src': 'https://nba.uth.tmc.edu/neuroscience/m/s1/images/html5/2023_Figure%207-1.gif',
        'title': 'The Memory Game: How Synaptic Potentiation Keeps Your Brain Sharp',
        'des': 'Memory and synaptic transmission',
        'link': 'https://relengine.com/blog/2023/09/25/the-memory-game-how-synaptic-potentiation-keeps-your-brain-sharp/'
    }
    daily_images.insert(0, new_image1)
    daily_images.insert(1, new_image2)
    

    return render_template('index.html', images=daily_images, user=current_user)




# Create a datetime object with your date and time
date_time = datetime.now()
# Format the datetime object in XML Sitemap format
formatted_date_time = date_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
@sitemap.register_generator                                                      # +
def index():
    '''generate URLs using language codes

       Note. used by flask-sitemap
     '''
    yield 'views.home', {}, formatted_date_time, 'monthly', 0.7