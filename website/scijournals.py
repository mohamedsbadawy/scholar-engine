from datetime import datetime
from flask import Blueprint, render_template, request, flash, jsonify, Response, abort, redirect, url_for, session
from flask_login import login_required, current_user
from .models import User, categories, journals, Journal_info, Review
from . import db
import json
import pandas as pd
import os
from urllib.parse import quote, unquote  # Import URL encoding/decoding functions
from . import sitemap
from sqlalchemy import func, or_,and_
from fuzzywuzzy import fuzz
from .mail import mail
from flask_mail import Mail, Message




jour = Blueprint('jour', __name__)

@jour.route('/add_review/', methods=['GET', 'POST'])
@login_required  # Assuming you are using Flask-Login for authentication
def add_review():
    
    # Fetch reviews for the same journal
    reviews = Review.query.filter_by(journal_id=journal_id).all()
    # Render the same page with updated reviews
    return render_template('your_template.html', journal_id=journal_id, reviews=reviews)


@jour.route('/categories/')
def list_categories():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    category_query = categories.query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('categories.html', categories=category_query,user=current_user)

@jour.route('/categories/<path:category_name>')
def list_journals(category_name):
    category_name = unquote(category_name)  # Decode the category name from the URL
    page = request.args.get('page', 1, type=int)
    per_page = 75
    category = categories.query.filter_by(name=category_name).first()
    if not category:
        abort(404)  # Return a 404 error if the category doesn't exist
    journals_query = journals.query.filter_by(category_id=category.id).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('journals.html', category=category, journals=journals_query,user=current_user)


@jour.route('/categories/<path:category_name>/<path:journal_title>.html', methods=['GET', 'POST'])
def journal_detail(category_name, journal_title):
    category_name = unquote(category_name)  # Decode the category name from the URL
    journal_title = unquote(journal_title)  # Decode the journal title from the URL
    category = categories.query.filter_by(name=category_name).first()
    if not category:
        abort(404)  # Return a 404 error if the category doesn't exist
    journal = journals.query.filter_by(title=journal_title, category_id=category.id).first()
    journal_inf = Journal_info.query.filter_by(title=journal_title, journal_id=journal.id, category__id=category.id).first()
    # Check if the about string starts with the prefix
    prefix = 'About ' + journal_title
    if journal_inf.about.lower().startswith(prefix.lower()):
        # Remove the prefix using slicing
        journal_inf.about = journal_inf.about[len(prefix):].lstrip()
    # # paragraphs = journal_inf.about.split('.')
    # formatted_about = "<div style='margin-bottom: 10px;'>" + "</div><div style='margin-bottom: 10px;'>".join(paragraphs) + "</div>">"
    # journal_inf.about = formatted_about
    # journal_inf.about = journal_inf.about.replace('\n', '<br>')
    reviews = Review.query.filter_by(journal_id=journal_inf.id).all()
    if request.method == 'POST' and current_user.is_authenticated:
        review_content = request.form['review_content']
        if len(review_content)> 100:
            # Create a new review and add it to the database
            new_review = Review(data=review_content, user_id=current_user.id, journal_id=journal_inf.id)
            db.session.add(new_review)
            db.session.commit()
            flash('Review added successfully', 'success')
            # Redirect to the same page to display the updated reviews
            # Redirect to the same page to display the updated reviews
            sender = ('Related Engine', 'info@relengine.com')
            not_msg = Message('A new comment has been added', sender=sender, recipients=['muhammad.badawi@hotmail.com'])
            
            # Generate the URL for the journal detail page
            journal_url = 'https://search.relengine.com/' + url_for('jour.journal_detail', category_name=category_name, journal_title=journal_title)
            not_msg.html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h1>A new comment has been added to {new_review.data} by {User.query.filter_by(id=new_review.user_id).first().first_name}!</h1>
                <p> On <a href="{journal_url}">{journal.title}</a></p>
            </body>
            </html>
            """
            mail.send(not_msg)  # Send the welcome email
            return redirect(url_for('jour.journal_detail', category_name=category_name, journal_title=journal_title))
        else: 
            flash('Review can not be less than 100 characters', 'error')
    if not journal:
        abort(404)  # Return a 404 error if the journal doesn't exist
    return render_template('journal_detail.html', category=category, journal=journal, Journal_inf=journal_inf, user=current_user, reviews=reviews)
    
@jour.route('/delete_review', methods=['POST'])
def delete_review():
    note = json.loads(request.data)  # This function expects JSON from the INDEX.js file
    noteId = note['noteId']
    rev = Review.query.get(noteId)
    if rev:
        if rev.user_id == current_user.id or current_user.id ==2 :
            db.session.delete(rev)
            db.session.commit()
            flash('Review deleted!', 'success')
        else:
            flash('You do not have permission to delete this review', 'error')
    else:
        flash('Review not found!', 'error')

    return redirect(request.referrer)
    
#upvote
@jour.route('/upvote_rev', methods=['POST'])
def upvote_rev():
    idR = json.loads(request.data)
    noteId = idR['noteId']
    rev = Review.query.get(noteId)
    if rev:
        user_id = current_user.id if current_user.is_authenticated else None
        if user_id:
            # Initialize the 'upvoted_reviews' set in the session if it doesn't exist
            session.setdefault('upvoted_reviews', set())
            try:
                # Check if the user has already upvoted this review
                if rev.id in session['upvoted_reviews']:
                    return flash('You have already upvoted this review', 'error')
                # Increment the upvote_count for the review
                rev.upvote_count += 1
                # Add this review to the user's upvoted list
                session['upvoted_reviews'].add(rev.id)
                session.modified = True  # Mark the session as modified
                flash('Review upvoted!', 'success')
                # Commit the transaction
                db.session.commit()
            except Exception as e:
                db.session.rollback()  # Rollback changes in case of an error
                flash('An error occurred while upvoting the review.', 'error')
    else:
        flash('Review not found!', 'error')

    return redirect(request.referrer)






@jour.route('/search/', methods=['POST'])
def search_page():
    keyword = request.form['search_input_']  # 'keyword' should match the 'name' attribute in the form field
    if keyword:
        return redirect(url_for('jour.search_result', keyword=keyword))
    else:
        flash('No results found')
        return redirect(url_for('views.home'))

@jour.route('/search/<path:keyword>', methods=['POST', 'GET'])
def search_result(keyword):
    # Decode the keyword from the URL
    RESULTS_PER_PAGE = 25
    keyword = unquote(keyword)
    # Join the Journal_info table
    query = db.session.query(journals).join(categories, journals.category_id == categories.id).join(
        Journal_info, journals.id == Journal_info.journal_id
    )
    
    # Define filter conditions for the search
    filter_conditions = or_(
        journals.title.ilike(f"%{keyword}%"),
        Journal_info.title.ilike(f"%{keyword}%"),
        Journal_info.issn.ilike(f"%{keyword}%"),
        Journal_info.country.ilike(f"%{keyword}%"),
        Journal_info.about.ilike(f"%{keyword}%"),
        Journal_info.Q.ilike(f"%{keyword}%"),
        Journal_info.cat.ilike(f"%{keyword}%"),
        journals.impact.ilike(f"%{keyword}%"),
        journals.description.ilike(f"%{keyword}%"),
        Journal_info.publisher.ilike(f"%{keyword}%"),
    )
    
    # Apply the filter conditions to the query
    results = query.filter(filter_conditions).paginate(
        page=request.args.get('page', 1, type=int),
        per_page=RESULTS_PER_PAGE
    )
    # If there are no exact matches, perform a fuzzy search on all columns
    if results.total == 0:
        RESULTS_PER_PAGE = 25
        keyword = unquote(keyword)
        fuzzy_results = []
        for result in query:
            match = False
            for column in [
                journals.title,
                Journal_info.title,
                Journal_info.issn,
                Journal_info.country,
                Journal_info.about,
                Journal_info.Q,
                Journal_info.cat,
                journals.impact,
                journals.description,
                Journal_info.publisher,
            ]:
                if hasattr(result, column.key):
                    column_value = getattr(result, column.key)
                    ratio = fuzz.ratio(keyword.lower(), column_value.lower())
                    if ratio >= 45:  # Adjust the threshold as needed
                        fuzzy_results.append(result)
    
        # Create a list of IDs for the fuzzy search results
        fuzzy_result_ids = [result.id for result in fuzzy_results]
        # Create a new query for the fuzzy search results and paginate it
        results = db.session.query(journals).filter(journals.id.in_(fuzzy_result_ids)).paginate(page=request.args.get('page', 1, type=int), per_page=RESULTS_PER_PAGE)
        return render_template('search_results.html', results=results, keyword=keyword, user=current_user)
    return render_template('search_results.html', results=results, keyword=keyword, user=current_user)

    
    
# fuzzy_results_data = []
# Extract relevant data from fuzzy_results and create dictionaries
# for idx, result in enumerate(fuzzy_results):
#     fuzzy_result_data = {
#         'Column': 'Result ' + str(idx + 1),  # Adjust the column key as needed
#         'Value': str(result.title)  # Convert the result object to a string or extract specific attributes
#     }
#     fuzzy_results_data.append(fuzzy_result_data)    
# return jsonify(fuzzy_results_data)
    




# admin

@jour.route('/admin/', methods=['GET', 'POST'])
@login_required
def import_data():
    # Get the current user
    if current_user is None:
        flash('please log in')
        return redirect(url_for('views.home'))
        # Check if the user is authenticated as user ID 2
    elif current_user.id != 2:
        flash('You don not have access',category='error')
        return redirect(url_for('views.home'))
    return render_template('admin.html')




# import data
@jour.route('/admin/import', methods=['POST'])
def import_data_go():
    try:
        user = User.query.get(2)  # Assuming you want to authenticate user ID 2
        category_name = request.form['category']
        category = categories.query.filter_by(name=category_name).first()
        if user.id == 2:
            # main_journal = request.form['main_journal']
            # journal_details = request.form['journal_details']
            #Access uploaded files
            file1 = request.files['csv_file1']
            file2 = request.files['csv_file2']
            # Delete rows with category_id = 2 if requested 
            category_action_enabled = 'category_checkbox' in request.form
            if category_action_enabled and category:
                db.session.query(journals).filter_by(category_id=category.id).delete()
                db.session.query(Journal_info).filter_by(category__id=category.id).delete()
                # Commit the changes to the database
                db.session.commit()
                flash('entries deleted successfully', category='success')
            # Get the current working directory
            current_dir = os.getcwd()
            # Check if files were uploaded
            if file1 and file2:
                # Save the uploaded files to a temporary location
                file1.save(os.path.join(current_dir, 'mainj.csv'))
                file2.save(os.path.join(current_dir, 'jdets.csv'))
                mainjpath = os.path.join(current_dir, 'mainj.csv')
                jdetspath = os.path.join(current_dir, 'jdets.csv')
                # Read the CSV files and fill NaN values with 'Not Available'
                jour_det = pd.read_csv(jdetspath).fillna('Not Available')
                jour_name = pd.read_csv(mainjpath).fillna('Not Available')
                # Check if the category exists, and if not, create it
                if not category:
                    category = categories(name=category_name)
                    db.session.add(category)
                    db.session.commit()
                # Create a dictionary to store journal titles and their respective info
                journal_info_dict = {row['title']: row for _, row in jour_det.iterrows()}
                # Iterate through the journal names CSV and create main journal entries
                for _, row in jour_name.iterrows():
                    title = row['title']
                    description = row['description']
                    if not journals.query.filter_by(title=title).first():
                        # Create a new Journal
                        journal = journals(
                            title=title,
                            description=description,
                            impact=row['impact'],
                            h_index=row['h-Index'],
                            SJR=row['SJR'],
                            ranking=row['ranking'],
                            category_id=category.id,
                        )
                        # Add the journal to the session
                        db.session.add(journal)
                
                # Commit the changes for main journals to the database (outside the loop)
                db.session.commit()
                # Iterate through the journal details CSV to create Journal_info entries
                for _, row in jour_det.iterrows():
                    title = row['title']
                    # Check if the journal title exists in the journal info dictionary
                    if title in journal_info_dict and not Journal_info.query.filter_by(title=title).first():
                        journal_info_data = journal_info_dict[title]
                        # Create a new Journal_info and associate it with the journal
                        journal_info = Journal_info(
                            title=journal_info_data['title'],
                            type=journal_info_data['type'],
                            cat=journal_info_data['cat'],
                            publisher=journal_info_data['Publisher'],
                            country=journal_info_data['Country'],
                            issn=journal_info_data['ISSN'],
                            Q=journal_info_data['Q'],
                            history=journal_info_data['History'],
                            about=journal_info_data[' about'].strip(),  # Note the space in the column name
                            website='----',
                            journal_id=journals.query.filter_by(title=title).first().id,
                            category__id=category.id,
                        )
                        # Add the journal_info to the session
                        db.session.add(journal_info)
                
                # Commit the changes for Journal_info entries to the database
                db.session.commit()
                os.remove(mainjpath)
                os.remove(jdetspath)
                flash('upload successful', category='success')
            return redirect(url_for('jour.import_data'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Handle exceptions and return an error response

            


# Create a datetime object with your date and time
date_time = datetime.now()
# Format the datetime object in XML Sitemap format
formatted_date_time = date_time.strftime("%Y-%m-%dT%H:%M:%S+00:00")
@sitemap.register_generator
def index():
    '''generate URLs dynamically from database records'''
    # Generate URLs for list_categories (no variables required)
    yield 'jour.list_categories', {}, formatted_date_time, 'monthly', 0.9
    # Generate URLs for list_journals dynamically from database records
    category_ = categories.query.all()  # Fetch all categories from your database
    for category in category_:
        # Encode the category name for the URL
        encoded_category_name = unquote(quote(category.name, safe=''))
        yield 'jour.list_journals', {'category_name': encoded_category_name}, formatted_date_time, 'monthly', 0.9
        category = categories.query.filter_by(name=category.name).first()
        # Generate URLs for journal_detail dynamically from database records
        journal_ = journals.query.filter_by(category_id=category.id)  # Fetch all journals from your database
        for journal in journal_:
            # Encode both category name and journal title for the URL
            encoded_journal_title = unquote(quote(journal.title, safe=''))
            yield 'jour.journal_detail', {'category_name': encoded_category_name, 'journal_title': encoded_journal_title}, formatted_date_time, 'monthly', 0.9


