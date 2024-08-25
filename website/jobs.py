from flask import Blueprint, request, render_template, Response, redirect, jsonify, session, flash, url_for
from . import db
from .models import User, Review
import requests
import pandas as pd
from .src.jobspy import scrape_jobs
import pandas as pd
from bs4 import BeautifulSoup
from flask_login import login_user, login_required, logout_user, current_user
import re
# IP
def get_user_ip():
    # First, try to get the IP address from the 'X-Real-IP' header if it exists.
    user_ip = request.headers.get('X-Real-IP')
    # If 'X-Real-IP' is not present, fall back to 'X-Forwarded-For'.
    if not user_ip:
       user_ip = request.headers.get('X-Forwarded-For')
      # If neither header is available, fall back to the remote address.
    if not user_ip:
        user_ip = request.remote_addr    
    return user_ip
    
def RenderHtml(df):
    table_html = "<table class='table table-striped container'><thead><tr>"
    for col in df.columns:
        table_html += f"<th style='text-align: center;'>{col}</th>"
    table_html += "</tr></thead><tbody>"
    for _, row in df.iterrows():
        table_html += "<tr>"
        for col in df.columns:
            table_html += f"<td style='text-align: center;'>{row[col]}</td>"
        table_html += "</tr>"
    table_html += "</tbody></table>" 
    return table_html
# Function to create HTML anchor tags with the custom keyword for valid links
def create_links_with_custom_keyword(link):
    custom_keyword = 'Click Here'
    if link:
        # Use a regular expression to check if the content resembles a URL
        if re.match(r'https?://\S+', link):
            return f'<a href="{link}" target="_blank">{custom_keyword}</a>'
        else:
            return link
    else:
        return ''
def truncate_and_generate_html(original_text, max_length=150):
    # Truncate the text to the specified length
    truncated_text = original_text[:max_length]
    
    # Generate the HTML code with a tooltip
    html_code = f'<div id="text-container"><p id="original-text" title="{original_text}">{truncated_text}</p></div>'
    
    return html_code

# Define your list of country tuples
countries = [
    ("USA", "www"),
    ("USA/CA", "www"),  # US_CANADA
    ("WORLDWIDE", "www"),
    ("ARGENTINA", "ar"),
    ("AUSTRALIA", "au"),
    ("AUSTRIA", "at"),
    ("BAHRAIN", "bh"),
    ("BELGIUM", "be"),
    ("BRAZIL", "br"),
    ("CANADA", "ca"),
    ("CHILE", "cl"),
    ("CHINA", "cn"),
    ("COLOMBIA", "co"),
    ("COSTA RICA", "cr"),
    ("CZECH REPUBLIC", "cz"),
    ("DENMARK", "dk"),
    ("ECUADOR", "ec"),
    ("EGYPT", "eg"),
    ("FINLAND", "fi"),
    ("FRANCE", "fr"),
    ("GERMANY", "de"),
    ("GREECE", "gr"),
    ("HONG KONG", "hk"),
    ("HUNGARY", "hu"),
    ("INDIA", "in"),
    ("INDONESIA", "id"),
    ("IRELAND", "ie"),
    ("ITALY", "it"),
    ("JAPAN", "jp"),
    ("KUWAIT", "kw"),
    ("LUXEMBOURG", "lu"),
    ("MALAYSIA", "my"),
    ("MEXICO", "mx"),
    ("MOROCCO", "ma"),
    ("NETHERLANDS", "nl"),
    ("NEW ZEALAND", "nz"),
    ("NIGERIA", "ng"),
    ("NORWAY", "no"),
    ("OMAN", "om"),
    ("PAKISTAN", "pk"),
    ("PANAMA", "pa"),
    ("PERU", "pe"),
    ("PHILIPPINES", "ph"),
    ("POLAND", "pl"),
    ("PORTUGAL", "pt"),
    ("QATAR", "qa"),
    ("ROMANIA", "ro"),
    ("SAUDI ARABIA", "sa"),
    ("SINGAPORE", "sg"),
    ("SOUTH AFRICA", "za"),
    ("SOUTH KOREA", "kr"),
    ("SPAIN", "es"),
    ("SWEDEN", "se"),
    ("SWITZERLAND", "ch"),
    ("TAIWAN", "tw"),
    ("THAILAND", "th"),
    ("TURKEY", "tr"),
    ("UKRAINE", "ua"),
    ("UNITED ARAB EMIRATES", "ae"),
    ("UK", "uk"),
    ("URUGUAY", "uy"),
    ("VENEZUELA", "ve"),
    ("VIETNAM", "vn"),
]
jobs = Blueprint('jobs', __name__)
@jobs.route('/JobHunt/')
def index():
    return render_template('jobs.html',countries=countries, user=current_user)

@jobs.route('/JobHunt/result/', methods=['POST'])
def findJobs():
    search_term = request.form['search_job']
    location = request.form['country']
    site_name = request.form['site']
    remote = request.form.get('remote', 'No')  # Check if the remote checkbox is checked
    
    try:
        if location == 'USA' or not location:
            # Example 2 - remote USA & hyperlinks
            jobs = scrape_jobs(
                site_name=site_name,
                location="USA",
                search_term=search_term,
                country_indeed="USA",
                hyperlinks=False,
                is_remote=remote,
                results_wanted=25,
            )
            # Use if hyperlinks=True
            jobs2 = jobs
            jobs2['job_url'] = jobs2['job_url'].apply(create_links_with_custom_keyword)
            jobs2['description'] = jobs2['description'].apply(truncate_and_generate_html)
            html = RenderHtml(jobs2)
            # Change max-width: 200px to show more or less of the content
            truncate_width = f'<style>.dataframe td {{ max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}</style>{html}'
        else:
            # Example 3 - with hyperlinks, international - LinkedIn (no zip_recruiter)
            jobs = scrape_jobs(
                site_name=site_name,
                location=location,
                search_term=search_term,
                country_indeed=location,
                hyperlinks=False,
                is_remote=remote,
                results_wanted=25,
            )
            # Use if hyperlinks=True
            jobs2 = jobs
            jobs2['job_url'] = jobs2['job_url'].apply(create_links_with_custom_keyword)
            jobs2['description'] = jobs2['description'].apply(truncate_and_generate_html)
            html = RenderHtml(jobs2)
            # Change max-width: 200px to show more or less of the content
            truncate_width = f'<style>.dataframe td {{ max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}</style>{html}'
        
        session['KW'] = search_term
        session['Html'] = html
        session['dfTemp'] = jobs
        return render_template('results.html', table=truncate_width, search_keyword=search_term, user=current_user)
    
    except requests.exceptions.RequestException as e:
        # Handle HTTP request errors
        errormessage = f'Error making an HTTP request: {e}'
        flash(errormessage, 'error')
        return redirect(url_for('jobs.index'))
    except Exception as e:
        # Handle other exceptions
        errormessage = f'Search is not successful: {e}'
        flash(errormessage, 'error')
        return redirect(url_for('jobs.index'))

            
    


# Define the route for saving search results
@jobs.route('/JobHunt/saveResults', methods=['POST'])
@login_required
def send_table_webhook():
    from .models import Library
    from datetime import datetime
    datasent = session.get('Html')
    
    new_note = Library(
        data=datasent,
        date=datetime.now(),  # Add the current date and time
        user_id=current_user.id,
    )
    
    # Add the note to the database 
    db.session.add(new_note)
    db.session.commit()
    
    flash('Data saved!', category='success')
    return redirect(url_for('lib.home', user_id=current_user.id))

@jobs.route('/JobHunt/download_excel', methods=['POST'])
def download_excel():
    try:
        import io    
        search_keyword = session.get('KW')
        df = pd.DataFrame(session.get('dfTemp'))    
        # Iterate through the DataFrame and extract links
        # Initialize an empty list to store the extracted links
        links = []
        for html_snippet in df['job_url']:
            soup = BeautifulSoup(html_snippet, 'html.parser')
            link = soup.a['href']
            links.append(link)
        # Create a new DataFrame with the extracted links
        df['job_url'] = links
        # Specify the order of columns
        excel_output = io.BytesIO()    
        # Use the search keyword as the file name
        excel_filename = f"{search_keyword}.xlsx"    
        with pd.ExcelWriter(excel_output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1', columns=df.columns)    
        excel_output.seek(0)    
        # Create a Flask Response with the Excel data
        response = Response(excel_output.read(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response.headers["Content-Disposition"] = f"attachment; filename={excel_filename}"    
        return response
    except Exception as e:
        error_message = str(e)  # Convert the exception to a string
        error_response = {
            'error_code': '500',  # Use an appropriate error code
            'error_message': error_message
        }
        return jsonify(error_response), 500
        
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
    yield 'jobs.index', {}, formatted_date_time, 'monthly', 0.7

