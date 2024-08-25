from datetime import datetime
from flask import Blueprint, render_template, request, flash, jsonify, Response, abort, redirect, url_for
from flask_login import login_required, current_user
from .models import User, Library
from . import db
import json



lib = Blueprint('lib', __name__)

# User Profiles
@lib.route('/lib/', methods=['GET', 'POST'])
@login_required
def library_redirect():
    # Redirect the user to their own profile page
    return redirect(url_for('lib.home', user_id=current_user.id))


@lib.route('/lib/dochub_<int:user_id>', methods=['GET', 'POST'])
@login_required
def home(user_id):
    if user_id == current_user.id:
        return render_template("lib.html", user=current_user)
    else:
        flash('Please Login to access your library','error')
        return redirect(url_for('auth.login', user_id=current_user.id))
    
@lib.route('/lib/dochub_<int:user_id>/delete-note', methods=['POST'])
def delete_note(user_id):
    note = json.loads(request.data)  # This function expects JSON from the INDEX.js file
    noteId = note['noteId']
    note = Library.query.get(noteId)

    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
            return  flash('Data deleted!', category='success')
        else:
            return flash('Something went wrong!', category='error')
    else:
        return flash('Data not found!', category='error') # Return a 404 Not Found status
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
    yield 'lib.library_redirect', {}, formatted_date_time, 'monthly', 0.7