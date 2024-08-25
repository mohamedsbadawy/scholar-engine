from flask import Blueprint, request, render_template, Response, redirect, jsonify, session, flash, url_for
from . import db
from .models import User, Review
from flask_login import login_user, login_required, logout_user, current_user
import requests
from bs4 import BeautifulSoup
import re
import time
from fake_useragent import UserAgent
import os
import re
import difflib
import certifi
import random, string
import pandas as pd
from .NetG import NetWorkGrap, find_word_in_list


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

current_directory = os.getcwd()
# Create a new workbook
ua = UserAgent()
HeadersCont = ['Paper Title' ,'PubMed Link','Authors','Journal','Note']
# user ID 
# function for generation of random string
def generate_random_string(stringLength=10):
  letters = string.ascii_lowercase
  return ''.join(random.choice(letters) for i in range(stringLength))
# IP
# Function to get the user's IP address
def get_user_ip():
    user_ip = request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote_addr
    return user_ip

# references in tha page
def clean_author_name(author_name):
    return re.sub(r'\xa0', ' ', author_name)
# strcmpi
def strcmpi(str1, str2):
    similarity_ratio = []
    str1 = str1.split()
    str2 = str2.split()
    matcher = difflib.SequenceMatcher(None, str1, str2)
    similarity_ratio = matcher.ratio()
    return similarity_ratio
# page details
def extractDetails(soup,tag):
    datalist = []    
    # Links of the search page
    elements = soup.find_all('a', class_='docsum-title')    
    # Titles
    text = [re.sub('\n', '', element.get_text(strip=False)) for element in elements]
    titles = [re.sub(r'\s+', ' ', re.sub(r'\n', '', text.strip())) for text in text]    
    # Links
    links = ['https://pubmed.ncbi.nlm.nih.gov' + element.get('href') for element in elements]    
    # For Journal details and authors
    results = soup.find_all('div', class_='docsum-content')    
    for idx, result in enumerate(results):
        authors = result.find('span', class_='docsum-authors full-authors').get_text()
        journal = result.find('span', class_='docsum-journal-citation short-journal-citation').get_text()        
        datalist.append({
            'Paper Title': titles[idx],
            'PubMed Link': links[idx],
            'Authors': authors,
            'Journal': journal,
            'Note': tag + ' article'
        })    
    return datalist

# CitedBY
def CitedBY(soup):
        datalist = []
        # '//*[@id="citedby-articles-list"]//*[@class="full-docsum"]'
        elements = soup.select('#citedby-articles-list .full-docsum')
        links = [link.find_all('a') for link in elements]
        # citations part 
            # title 
        titles = [titTemp[0].get_text(strip=True) for titTemp in links]
        # links 
        pLinks = ['https://pubmed.ncbi.nlm.nih.gov' + linkTemp[0].get('href') for linkTemp in links]
        author_elements = soup.select('#citedby-articles-list .docsum-authors.full-authors')
        Authors = [author_e.get_text(strip=True) for author_e in author_elements]
        JournalElem = soup.select('#citedby-articles-list .short-journal-citation')
        JournalElem = [journal.get_text(strip=True) for journal in JournalElem]
        for idx in range(len(JournalElem)):             
            datalist.append({
                'Paper Title': titles[idx],
                'PubMed Link': pLinks[idx],
                'Authors': Authors[idx],
                'Journal': JournalElem[idx],
                'Note': 'Citing article'
            })    
        return datalist

# Unique Values
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
# main fun
def get_Related_Work(search_keyword,NumofPage):
    data = []
    proxy_load = get_user_ip()
    headers = {
        "User-Agent": str(ua.googlechrome),
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://google.com/",
        "X-Forwarded-For": str(proxy_load),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    papertitle = [search_keyword]
    papertitle1 = [paper.replace(" ", "+") for paper in papertitle]
    query = f"{papertitle1[0]}"
    pubmedURL = f'https://pubmed.ncbi.nlm.nih.gov/?term={query}'
    # pages = f'https://pubmed.ncbi.nlm.nih.gov/?term={query}&page='
    response = requests.get(pubmedURL,headers=headers) 
    # cited by
    soup = BeautifulSoup(response.text, "html.parser")    
    # Find the <a> element by its class
    link_element1 = soup.find(id='citedby') # usa-button ')
    if link_element1:
        link_element = link_element1.find(class_='show-all-linked-articles')
        if link_element1 and link_element:
            link_element = link_element['data-href']        
            Continuuuu = True
        elements = soup.select('#citedby-articles-list .full-docsum')
        links = [link.find_all('a') for link in elements]
        if links: 
            data.extend(CitedBY(soup))
    else:
        elements = soup.select(".docsum-title")
        hrefs = [element['href'] for element in elements]
        text = [element.get_text() for element in elements]    
        ratios = [strcmpi(Ti,papertitle[0]) for Ti in text]  
        if ratios:
            # getting the correct paper link and redirect to the proper request
            ratiosMax = ratios.index(max(ratios))
            if ratios[ratiosMax] >= 0.7:
                link =  'https://pubmed.ncbi.nlm.nih.gov' + hrefs[ratiosMax]
                time.sleep(1)
                response = requests.get(link,headers=headers)
                soup = BeautifulSoup(response.text, "html.parser")
                link_element = soup.find(class_='citedby-articles') # usa-button ')
                if link_element:
                    link_element = link_element.find(class_='show-all-linked-articles')
                    if link_element:
                                link_element = link_element['data-href']        
                                Continuuuu = True                                
                elements = soup.select('#citedby-articles-list .full-docsum')
                links = [link.find_all('a') for link in elements]
                if links: 
                    data.extend(CitedBY(soup))
            else: 
                data.extend(extractDetails(soup,'Related'))
                link_element = False
                
        else: 
            link_element = False
    # Extract the 'data-href' attribute, which contains the link
    time.sleep(0.5)
    if link_element and Continuuuu:
        link = 'https://pubmed.ncbi.nlm.nih.gov' + link_element
        newRespons = requests.get(link,headers=headers)
        soup = BeautifulSoup(newRespons.text, "html.parser")
        data.extend(extractDetails(soup,'Citing'))
        TotalPages = int(re.search(r'\d+',soup.find(class_ = 'of-total-pages').get_text(strip=True)).group())
        pgcnt = 2
        while NumofPage > 1 and TotalPages >= pgcnt and pgcnt < 7:
            pages = f'{link}&page={pgcnt}'
            # second page
            time.sleep(2)
            newRespons = requests.get(pages,headers=headers)
            soup = BeautifulSoup(newRespons.text, "html.parser")
            data.extend(extractDetails(soup,'Citing'))
            pgcnt+= 1
    else:
        # get similar articles instead of refrenced 
        link_element = soup.find(class_='similar-articles') # usa-button ')
        if link_element:
            link_element = link_element.find(class_='show-all-linked-articles')
            link_element = 'https://pubmed.ncbi.nlm.nih.gov' +link_element['data-href']
            time.sleep(1)
            response = requests.get(link_element,headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            data.extend(extractDetails(soup,'Related'))
            # second page
            pgcnt = 2
            TotalPages = int(re.search(r'\d+',soup.find(class_ = 'of-total-pages').get_text(strip=True)).group())
            while NumofPage > 1 and TotalPages >= pgcnt and pgcnt < 7:
                pages = f'{link_element}&page={pgcnt}'
                # second page
                time.sleep(2)
                response = requests.get(pages,headers=headers)
                soup = BeautifulSoup(response.text, "html.parser")
                data.extend(extractDetails(soup,'Related'))
                pgcnt+= 1
        else:
            """" in progress
            duckDuckGo = f'https://duckduckgo.com/?t=h_&q={query}&ia=web'
            newResponse = requests.get(duckDuckGo, headers=headers)  # Replace 'utf-8' with the desired encoding
            soup = BeautifulSoup(newResponse.text, "html.parser")
            search_results = soup.find_all("div", class_="tF2Cxc")
            """
            data.append({
                'Paper Title': search_keyword,
                'PubMed Link': '/',
                'Authors': 'NA',
                'Journal': 'NA',
                'Note': 'Related work is above, if any'
            })  
    return get_unique_dicts_preserve_order(data)

pubMed = Blueprint('pubMed', __name__)
@pubMed.route('/pm/')
def index():
    if 'KW' in session:
        session.pop('KW')  # Remove 'KW' from the session
    if 'Html' in session:
        session.pop('Html')
    if 'dfTemp' in session:
        session.pop('dfTemp')
    return render_template('pm.html',user=current_user)
# Helper functions

@pubMed.route('/pm/result/', methods=['POST'])
def result():
    NumofPage = None
    global search_keyword
    search_keyword = request.form['check']
    NumofPage = int(request.form['check2'])
    df = get_Related_Work(search_keyword,NumofPage)  # Update the global variable
    dfTemp = df
    # Iterate through the list of dictionaries and add rows to the table
    session['dfTemp'] = dfTemp

    df = pd.DataFrame(df)  
    # change links 
    df['PubMed Link'] = df['PubMed Link'].apply(create_links_with_custom_keyword)
    # Convert the DataFrame to an HTML table with links
    table_html = RenderHtml(df)
    session['KW'] = search_keyword
    session['Html'] = table_html
    # generate_random_string(stringLength=10)
    return render_template('result.html', table=table_html, classes='table table-striped container', search_keyword=search_keyword, user=current_user)

@pubMed.route('/pm/graph/', methods=['POST'])
def gen_graph():
    try:
        NewList = find_word_in_list(['Paper','Authors','Journal'],HeadersCont)
        NewList = [HeadersCont[i] for i in NewList]
        graph_html = NetWorkGrap(session.get('dfTemp'), session.get('KW'),NewList,'pm')
        session['gen_graph'] = {
            'success': True,
            'message': 'Done Successfully'
        }
    except Exception as e:       
        graph_html =  f'Error Occurred: ' + str(e)  # Include the error message
    # Pass 'search_keyword' to the template if it's defined
    search_keyword = session.get('KW', '')  # Use a default value if not defined
    return render_template('graph.html', table=graph_html, classes='table table-striped container', search_keyword=search_keyword, user=current_user)

# Helper functions


# Define the route for saving search results
@pubMed.route('/pm/saveResults', methods=['POST'])
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

@pubMed.route('/pm/download_excel', methods=['POST'])
def download_excel():
    try:
        import io    
        search_keyword = session.get('KW')
        df = pd.DataFrame(session.get('dfTemp'))    
        # Specify the order of columns
        column_order = HeadersCont
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
        return redirect('https://search.relengine.com/pm')
        
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
    yield 'pubMed.index', {}, formatted_date_time, 'monthly', 0.7