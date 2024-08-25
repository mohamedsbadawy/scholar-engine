from flask import Blueprint, request, jsonify, current_app, flash, redirect, url_for,render_template
from . import db
from .models import User, Review
from flask_login import login_required, current_user
import requests
from urllib.parse import quote
from fake_useragent import UserAgent

factcheck = Blueprint('factcheck', __name__)

@factcheck.route('/factcheck/')
def index():
    return render_template('factcheckmain.html', user=current_user)

# Helper functions
@factcheck.route('/factcheck/result/', methods=['POST'])
def result():
    word_to_be_checked = request.form.get('search_job')

    if not word_to_be_checked:
        flash('Please provide a word to check.', 'error')
        return redirect(url_for('factcheck.index'))

    # Set up headers with a fake User-Agent and custom IP
    headers = {
        'User-Agent': UserAgent().random,
        'X-Forwarded-For': 'your_custom_ip',  # Replace 'your_custom_ip' with the desired IP
    }

    # Make the request with custom headers
    response = requests.get(f'https://nli.wmcloud.org/fact_checking_model/?claim={quote(word_to_be_checked)}', headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the JSON content
        data = response.json()
       # Extract information and create a dictionary with numbering
        details_dict = {}
        supports_count = 0  # Count of results with label "SUPPORTS"
        total_results = 0
        for index, result in enumerate(data["results"], start=0):
            details_dict[index] = {
                "Claim": result["claim"],
                "Article": result["article"],
                "text": result["text"],
                "Label": result["label"],
                "Contradiction Probability": result["contradiction_prob"],
                "Entailment Probability": result["entailment_prob"],
                "Neutral Probability": result["neutral_prob"]
            }
            if result["label"] == "SUPPORTS" or result["label"] == "REFUTES":
                total_results +=1
            # Count results with label "SUPPORTS"
            if result["label"] == "SUPPORTS":
                supports_count += 1
    
        # Calculate the percentage of results with label "SUPPORTS"
        supports_percentage = (supports_count / total_results) * 100 if total_results > 0 else 0
        # Return the JSON response directly
        return render_template('resultsfacts.html', results=details_dict,
                               search_keyword=word_to_be_checked, user=current_user, support = round(supports_percentage, 2))
    else:
        current_app.logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
        flash('Failed to retrieve data. Please try again later.', 'error')
        return redirect(url_for('factcheck.index'))
