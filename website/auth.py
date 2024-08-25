from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify,session
from .models import User, Review
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
from .forms import PasswordResetRequestForm, PasswordResetForm, LoginForm, SignupForm  
import secrets
from flask_mail import Mail, Message
from .mail import mail
import time
import random
from flask_wtf.csrf import CSRFError
import json
from email_validator import validate_email, EmailNotValidError
from werkzeug.utils import secure_filename
import os
from flask import current_app



auth = Blueprint('auth', __name__)
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if not current_user.is_authenticated:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            remember_me = request.form.get('remember_me') == 'on'
            user = User.query.filter_by(email=email.lower()).first()
            if user:
                if check_password_hash(user.password, password):
                    flash('Logged in successfully!', category='success')
                    login_user(user, remember=remember_me)
                    # Check if there is a stored URL in the session
                    next_url = session.get('next_url')
                    if next_url:
                        # Redirect the user to the stored URL
                        return redirect(next_url)
    
                    # If there's no stored URL, redirect to the default page
                    return redirect(url_for('lib.library_redirect'))
                else:
                    flash('Email or password is incorrect, try again.', category='error')
            else:
                flash('Email or password is incorrect, try again.', category='error')
    
        # Store the URL the user came from in the session
        session['next_url'] = request.referrer
    
        return render_template("login.html", user=current_user)
    else:
        return redirect(url_for('views.home'))


@auth.route('/login_popup/', methods=['POST'])
def login_popup():
    response_data = {'success': False, 'message': ''}
    request_data = json.loads(request.data)
    if request_data:
        email = request_data.get('email')
        password = request_data.get('password')
        
        user = User.query.filter_by(email=email.lower()).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                response_data['success'] = True
                response_data['message'] = 'Logged in successfully!'
            else:
                response_data['message'] = 'Email or password is incorrect, try again.'
        else:
            response_data['message'] = 'Email or password is incorrect, try again.'
    else:
        response_data['message'] = 'Invalid request data.'

    return jsonify(response_data)


@auth.route('/login_form', methods=['GET'])
def login_form():
   
    return render_template('login_register_modal.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.home'))

# User Profiles
@auth.route('/user_profile/', methods=['GET'])
@login_required
def myprofile_redirect():
    # Redirect the user to their own profile page
    return redirect(url_for('auth.profile', user_id=current_user.id))

# User Profiles
@auth.route('/user_profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    if user_id == current_user.id:
        if request.method == 'POST':
            recentBio = request.form.get('thoughts')
            if not recentBio:
                field_mapping = {
                    'first_name': 'first_name',
                    'email': 'email',
                    'education': 'education',
                    'f_of_Study': 'f_of_Study',
                }
                values = {}
                for form_field, db_field in field_mapping.items():
                    form_value = request.form.get(form_field)
                    if form_field == 'email':
                        if form_value:
                            try:
                                # Validate the email format
                                valid = validate_email(form_value)
                                form_value = valid["email"]
                            except EmailNotValidError as e:
                                flash('Invalid email format!', category='error')
                                return redirect(request.url)
                            # Check if the email already exists in the database
                            existing_user = User.query.filter_by(email=form_value).first()
                            if existing_user is not None and existing_user != current_user:
                                flash('Email already exists for another user!', category='error')
                                return redirect(request.url)
                        else:
                            flash('Email is required!', category='error')
                            return redirect(request.url)
                    if form_value:
                        values[db_field] = form_value
    
                if values:
                    # Update the user's information in the database
                    User.query.filter_by(id=current_user.id).update(values)
                    db.session.commit()
                    return redirect(url_for('auth.profile', user_id=current_user.id))
                    flash('User info updated!', category='success')
            if recentBio:
                new_review = Review(
                    date=datetime.now(),
                    bio=str(recentBio),
                    user_id=current_user.id
                )
                db.session.add(new_review)
                db.session.commit()
                return redirect(url_for('auth.profile', user_id=current_user.id))
                flash('Note added!', category='success')
        last_review = Review.query.filter_by(user_id=current_user.id).order_by(Review.date.desc()).first()
        reviews = Review.query.filter_by(user_id=current_user.id).all()
        num_of_reviews = sum(1 for review in reviews if review.data)
        return render_template("profile.html", User=current_user, LastReview=last_review,numofRev=num_of_reviews)
    else:
        flash('You do not have access to this profile!', category='error')
        return redirect(url_for('views.home'))
        
def allowed_file(filename):
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS')
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
@auth.route('/update_av/<int:user_id>', methods=['POST'])
@login_required
def upload_avatar(user_id):
    if 'avatar' not in request.files:
        return redirect(request.url)
    file = request.files['avatar']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Define the upload folder and ensure it exists
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        file.save(os.path.join(upload_folder, filename))
        photo_path = 'assets/' + filename
        # Get the user to update
        user = User.query.get(user_id)
        user.photo = photo_path
        db.session.commit()
        flash('Updated successfully', 'success')
        return redirect(url_for('auth.profile', user_id=current_user.id))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    # Generate random numbers for the math question
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    # Calculate the answer
    answer = num1 + num2
    # Generate a random string for the input field's id attribute
    random_id = ''.join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(10))
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        education = request.form.get('Education')
        f_of_Study = request.form.get('Acinterest')
        userAnswer = int(request.form.get('captcha-answer'))

        
        if not education:
            education = 'Edit in Profile'
        if not f_of_Study:
            f_of_Study = 'Edit in Profile'

        user = User.query.filter_by(email=email.lower()).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        elif userAnswer != answer:
            flash('Wrong Captcha Answer!', category='error')
        else:
            new_user = User(
                email=email.lower(),
                first_name=first_name,
                education=education,
                f_of_Study=f_of_Study,
                password=generate_password_hash(password1),
                reset_password_token=None, # Set reset_password_token to None
                reset_password_token_timestamp = None
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            # Send a welcome email
            sender = ('Related Engine', 'info@relengine.com')
            welcome_msg = Message('Welcome to Related Engine | Your academic resource Hub', sender=sender, recipients=[new_user.email])
            welcome_msg.html = """
                        <html>
                        <body style="font-family: Arial, sans-serif;">
                            <h1>Welcome to the Related Engine Community, {first_name}!</h1>
                            <p>Thank you for joining us on Related Engine, your go-to platform for scholarly research and job hunting.</p>
                            <p>Here's what you can do with your new account:</p>
                            <ul>
                                <li>Search scholarly articles</li>
                                <li>Export results to Excel or your online library</li>
                                <li>Generate network graphs of your research results</li>
                                <li>Empower your job search with access to 3 major job posting databases</li>
                            </ul>
                            <p>Get started now and explore all these features:</p>
                            <p><a href="https://relengine.com">Visit our Website</a></p>
                            <p><a href="https://search.relengine.com/ai/">Try our AI-based search engine</a></p>
                            <p><a href="https://search.relengine.com/JobHunt/">Use our Job Hunt search helper tool</a></p>
                            <p>Don't forget to check out our <a href="https://relengine.com/blog/">blog</a> for the latest updates and tips!</p>
                            <p> follow us on facebook <a href="https://www.facebook.com/relatedengine">Facebook</a> for the latest updates!</p>
                            <p>Happy exploring!</p>
                            <p>#scholarly_research #academic_articles #job_finder</p>
                        </body>
                        </html>
                        """.format(first_name=new_user.first_name)
            mail.send(welcome_msg)  # Send the welcome email
            not_msg = Message('A new user registered to Related Engine', sender=sender, recipients=['muhammad.badawi@hotmail.com'])
            not_msg.html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h1>A new Registration in RelEngine!</h1>
                <p>{new_user.first_name} has registered to Relengine</p>
                <p> with an email {new_user.email} </p>
            </body>
            </html>
            """
            mail.send(not_msg)  # Send the welcome email
            return redirect(url_for('views.home'))
    return render_template("signup.html", user=current_user, random_id=random_id,num1=num1,num2=num2 )

@auth.route('/request_password', methods=['GET', 'POST'])
def reset_password_request():
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate a secure token
            token = secrets.token_hex(16)
            timestamp = int(time.time())  # Get the current timestamp
            user.reset_password_token = token
            user.reset_password_token_timestamp = timestamp  # Store the timestamp
            db.session.commit()
            # Send a password reset email
            currentuser = User.query.filter_by(email=form.email.data).first()
            msg = Message('Password Reset Request from Related Engine', sender=('Related Engine', 'info@relengine.com'), recipients=[user.email])
            msg.body = f"Dear {user.first_name},\n\nYou have requested to reset your password for Related Engine.\n\nTo reset your password, please click the link below. This link is valid for 10 minutes from the time of your request.\n\n{url_for('auth.reset_password', token=token, _external=True)}\n\nIf you did not make this request, please discard this email and contact our support team at info@relengine.com.\n\nBest regards,\nThe Related Engine Team"
            mail.send(msg)
            flash('Check your email for a password reset link.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Email not found. Please check and try again.', 'error')
    return render_template('request_password.html', title='Request Password Reset', form=form)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_password_token=token).first()
    if not user:
        flash('Invalid or expired token', 'error')
        return redirect(url_for('auth.reset_password_request'))

    token_timestamp = user.reset_password_token_timestamp
    current_timestamp = int(time.time())

    if current_timestamp - token_timestamp > 600:
        flash('Token has expired', 'error')
        return redirect(url_for('auth.reset_password_request'))

    form = PasswordResetForm()
    if form.validate_on_submit() and form.password1.data == form.password2.data:
        # Reset the user's password
        user.set_password(generate_password_hash(form.password1.data))
        user.reset_password_token = None
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('Passwords don not match', 'error')
    
    return render_template('reset_password.html', title='Reset Password', form=form)




# Example route where you send an email
@auth.route('/testemail')
def send_email():
    # Create a message
    msg = Message('Subject', sender='info@relengine.com', recipients=['youremail'])
    msg.body = 'This is the body of the email.'

    # Send the email
    mail.send(msg)
    result_set = {'Email sent successfully'}
    result_list = list(result_set)
    return jsonify(result_list)

# ...


