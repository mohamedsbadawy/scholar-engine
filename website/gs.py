from flask import Blueprint, request, render_template, Response, redirect, jsonify, session, flash, url_for
from . import db
from werkzeug.middleware.proxy_fix import ProxyFix  # Example middleware import
import requests
from bs4 import BeautifulSoup
import re
import time
from fake_useragent import UserAgent
from openpyxl import Workbook
import os
import re
import certifi
from .NetG import NetWorkGrap, find_word_in_list
import pandas as pd

from .models import User, Review
from flask_login import login_user, login_required, logout_user, current_user



headers = ['OriginalPaper', 'Related Paper Title', 'Related Paper Link', 'Authors', 'Number of Citations']
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
        
RequestLessFactor = 1.5
current_directory = os.getcwd()
def clean_author_name(author_name):
    return re.sub(r'\xa0', ' ', author_name)
# Create a new workbook
wb = Workbook()
ws = wb.active
ua = UserAgent()
# Home = Blueprint('Home',__name__)
def get_unique_dicts_preserve_order(list_of_dicts):
    seen_dicts = set()
    unique_dicts = []
    order_preserved = []
    for d in list_of_dicts:
        # Convert each dictionary to a frozenset to make it hashable
        frozenset_d = frozenset(d.items())
        # Check if we have seen this dictionary before
        if frozenset_d not in seen_dicts:
            seen_dicts.add(frozenset_d)
            unique_dicts.append(dict(frozenset_d))
            order_preserved.append(d)
    return order_preserved
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
    # 35ae873b1f8fb5fab545baccad6cc1ea (first API)
def loadURL(url):
     API ='c8e48cc8fe644f757d0a8136a978cb55' 
     URL = f'http://api.scraperapi.com?api_key={API}&url={url}'
     return URL
def get_Related_Work(search_keyword):
    data = []
 # page numbers for future
    #https://scholar.google.com/scholar?start=PageNumber* 10
    # Define the query parameters
    proxyLoad = get_user_ip()
    headers = {
        "User-Agent": str(ua.googlechrome),
        "Accept-Language": "en-US,en;q=0.5",  # Language preference
        "Accept-Encoding": "gzip, deflate, br",  # Encoding methods supported
        "Referer": "https://scholar.google.com/",  # The page that referred th request
        "X-Forwarded-For": str(proxyLoad),  # User's IP address (if needed)
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",  # Accepted content types
     }
    # user id the between parentheses in this example https://scholar.google.com/citations?hl=en&user=(yGBA604AAAAJ)&view_op=list_works&sortby=pubdate
    papertitle = [search_keyword]
    papertitle1 = [paper.replace(" ", "+") for paper in papertitle]
    query = f"{papertitle1[0]}"
    google_search_url = f'https://scholar.google.com/scholar?hl=en&as_sdt=0%2C31&q={query}'
    # trying to deceive google
    response = requests.get(loadURL(google_search_url),headers=headers) 
    soup = BeautifulSoup(response.text, "html.parser")
    search_results = [a['href'] for a in soup.select('.gs_fl a:nth-child(4)')]
    if search_results:
        # Extract PAPERSLINKS
        papers_links = [a['href'] for a in soup.select('.gs_r.gs_or.gs_scl .gs_rt a')]  # Extract titles
        titles = [a.get_text() for a in soup.select('.gs_rt a')]
        author_details = soup.select('.gs_a') # Extract Number of Citations
        num_of_citations = [a.get_text() for a in soup.select('.gs_fl a:nth-child(3)')]    # Initialize an empty list for PaperAuth
        paper_auth = [] # Extract authors and store in PaperAuth
        for individual_paper in author_details:
            paper_auth.append(clean_author_name(individual_paper.get_text().strip()))
            # Create the data dictionary
        for idx in range(len(titles)):
            data.append({
                'OriginalPaper': titles[0].strip().replace("/", ""),
                'Related Paper Title': titles[idx].strip().replace("/", ""),
                'Related Paper Link': papers_links[idx],
                # 'Authors': [re.sub(r'[^A-Za-z\s]', '', papAuth) for papAuth in paper_auth[idx]],
                'Authors': paper_auth[idx],
                'Number of Citations': num_of_citations[idx],
                        })
        time.sleep(1)
        if len(search_results) >3:
          search_results = search_results[0: len(set(search_results))- round(len(set(search_results))/RequestLessFactor)]
        # until I find a solution for proxies 
        for url in search_results:
            try:
                headers = {
                "User-Agent": str(ua.google),
                "Accept-Language": "en-US,en;q=0.5",  # Language preference
                "Accept-Encoding": "gzip, deflate, br",  # Encoding methods supported
                "Referer": google_search_url,  # The page that referred the request
                "X-Forwarded-For": str(proxyLoad),  # User's IP address (if needed)
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",  # Accepted content types
               }
                SubUrl = f'https://scholar.google.com/{url}'
                response = requests.get(loadURL(SubUrl), headers=headers) 
                soup = BeautifulSoup(response.text, "html.parser")
                    # Extract PAPERSLINKS
                papers_links = [a['href'] for a in soup.select('.gs_r.gs_or.gs_scl .gs_rt a')]
                    # Extract titles
                titles = [a.get_text() for a in soup.select('.gs_rt a')]
                    # Extract author details
                author_details = soup.select('.gs_a')
                    # Extract Number of Citations
                num_of_citations = [a.get_text() for a in soup.select('.gs_fl a:nth-child(3)')]
                    # Initialize an empty list for PaperAuth
                paper_auth = []
                    # Extract authors and store in PaperAuth
                for individual_paper in author_details:
                    paper_auth.append(clean_author_name(individual_paper.get_text().strip()))
                    # Create the data dictionary
                    # data = []
                for idx in range(len(titles)):
                        data.append({
                            'OriginalPaper': titles[0].strip().replace("/", ""),
                            'Related Paper Title': titles[idx].strip().replace("/", ""),
                            'Related Paper Link': papers_links[idx],
                            'Authors': paper_auth[idx],
                            'Number of Citations': num_of_citations[idx],
                        })
                time.sleep(0.5)
            except Exception as e:
                print({e})
                continue
    else:
        data.append({
                    'OriginalPaper': search_keyword.replace("/", ""),
                    'Related Paper Title': 'A server error has occured, related to IP block',
                    'Related Paper Link': '/',
                    'Authors': f'a server error has occured Please try again later',
                    'Number of Citations': f' a server error has occured Please try again later',
                })
    return get_unique_dicts_preserve_order(data)

gs = Blueprint('gs', __name__)
@gs.route('/gs/')
def index():
    if 'KW' in session:
        session.pop('KW')  # Remove 'KW' from the session
    if 'Html' in session:
        session.pop('Html')
    if 'dfTemp' in session:
        session.pop('dfTemp')
    return render_template('gs.html', user=current_user)

@gs.route('/gs/result/', methods=['POST'])
def result():
    global search_keyword
    search_keyword = str(request.form['check'])
    df = get_Related_Work(search_keyword)  # Update the global variable
    dfTemp = df
    session['dfTemp'] = dfTemp
    newdf = pd.DataFrame(df)  
    # change links 
    newdf['Related Paper Link'] = newdf['Related Paper Link'].apply(create_links_with_custom_keyword)
    # Convert the DataFrame to an HTML table with links
    table_html = RenderHtml(newdf)
    session['KW'] = search_keyword
    session['Html'] = table_html
    return render_template('result.html', table=table_html, classes='table table-striped container', search_keyword=search_keyword, user=current_user)


@gs.route('/gs/graph/', methods=['POST'])
def gen_graph():
    try:
        headers = ['OriginalPaper', 'Related Paper Title', 'Related Paper Link', 'Authors', 'Number of Citations']
        NewList = find_word_in_list(['OriginalPaper','Related Paper Title','Authors','Number of Citations'],headers)
        NewList = [headers[i] for i in NewList]
        graph_html = NetWorkGrap(session.get('dfTemp'), session.get('KW'),NewList,'gs')
        session['gen_graph'] = {
            'success': True,
            'message': 'Done Successfully'
        }
    except Exception as e:       
        graph_html =  f'Error Occurred: ' + str(e)  # Include the error message
    # Pass 'search_keyword' to the template if it's defined
    search_keyword = session.get('KW', '')  # Use a default value if not defined
    return render_template('graph.html', table=graph_html, classes='table table-striped container', search_keyword=search_keyword, user=current_user)

# Define the route for saving search results
@gs.route('/gs/saveResults', methods=['POST'])
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


@gs.route('/gs/download_excel', methods=['POST'])
def download_excel():
    try:
        import io    
        headers = ['OriginalPaper', 'Related Paper Title', 'Related Paper Link', 'Authors', 'Number of Citations']
        search_keyword = session.get('KW')
        df = pd.DataFrame(session.get('dfTemp'))    
        # Specify the order of columns
        column_order = headers
        df = df[column_order]    
        # Create an Excel writer object
        excel_output = io.BytesIO()    
        # Use the search keyword as the file name
        excel_filename = f"{search_keyword}.xlsx"    
        with pd.ExcelWriter(excel_output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1', columns=column_order)    
        excel_output.seek(0)    
        # Create a Flask Response with the Excel data
        response = Response(excel_output.read(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response.headers["Content-Disposition"] = f"attachment; filename={excel_filename}"    
        return response
    except Exception as e:
        # Handle the exception gracefully, e.g., redirect to an error page
        return redirect('https://search.relengine.com/gs')

