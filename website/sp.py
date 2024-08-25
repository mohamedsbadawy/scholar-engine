from flask import Blueprint, request, render_template, Response, redirect, jsonify, session, flash, url_for
from . import db
import requests
import re
import time
from fake_useragent import UserAgent
import os
import re
import certifi
from .API import APIFun
from .NetG import NetWorkGrap, find_word_in_list
import pandas as pd
from .models import User, Review
from flask_login import login_user, login_required, logout_user, current_user



HeaderRel = ['Original Paper','Related Paper' ,'abstract' ,'Authors','Link','PDF','Journal','Note']
HeaderOrg = ['Original Paper','abstract' ,'Authors','Link','PDF','Journal']
current_directory = os.getcwd()
ua = UserAgent()

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
# references in tha page
def clean_author_name(author_name):
    return re.sub(r'\xa0', ' ', author_name)

def grapCitations(link,numofPages):
     rsp = requests.get(link,
            headers={'X-API-KEY': APIFun()},
            #    references.title,references.authors
            params={'query': link, 'limit': numofPages, 'fields': f'citations.abstract,citations.title,citations.authors,citations.openAccessPdf,citations.venue'})
     if rsp.status_code == 200:
        result = rsp.json()
        if result:
            return result
        else:
            return None

def grapRefrences(link,numofPages):
     refDets = 'references.title,references.authors,references.abstract,references.openAccessPdf,references.venue'
     rsp = requests.get(link,
            headers={'X-API-KEY': APIFun()},
            #    references.title,references.authors
            params={'query': link, 'limit': numofPages, 'fields': refDets})
     if rsp.status_code == 200:
        result = rsp.json()
        if result:
            return result
        else:
             return None
     

def getLinks(papersN,secPaper, keyword):
    delay = 1/100
    mainlin = []
    refLinks = []
    if papersN:     
        rsp = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/{papersN.get('paperId')}?fields=externalIds",
        headers={'X-API-KEY': APIFun()})
        mainlin.append(("https://doi.org/" + rsp.json().get('externalIds').get('DOI')) if rsp.json().get('externalIds').get('DOI') else "NA")
        time.sleep(delay)
    for n, ref in enumerate(secPaper[keyword]):
        rsp = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/{ref.get('paperId')}?fields=externalIds",
        headers={'X-API-KEY': APIFun()})
        if rsp.json().get('externalIds'):
            refLinks.append(("https://doi.org/" + rsp.json().get('externalIds').get('DOI')) if rsp.json().get('externalIds').get('DOI') else "NA")
            time.sleep(delay)
        else:
            refLinks.append('NA')
    return {'MainLink':mainlin, 'refLinks':refLinks}


def EmptyLinks(papersN,secPaper, keyword):
    delay = 1/100
    mainlin = []
    refLinks = []
    if papersN:     
        rsp = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/{papersN.get('paperId')}?fields=externalIds",
        headers={'X-API-KEY': APIFun()})
        mainlin.append(("https://doi.org/" + rsp.json().get('externalIds').get('DOI')) if rsp.json().get('externalIds').get('DOI') else "NA")
        time.sleep(delay)
    for n, ref in enumerate(secPaper[keyword]):
        refLinks.append('Exceeded Number Of Requests')
    return {'MainLink':mainlin, 'refLinks':refLinks}
# extract formatted details 
def parseResults(MainP,SPaper,InpLinks,keyword):
    references = []
    data = []
    delimiter = ", "  # You can specify a delimiter (e.g., space)
    if keyword == 'data':
        note = 'Recommendations'
    else:
        note = keyword
    if MainP:
        data.append({
                    'OriginalPaper' : MainP.get("title","No title Available"),
                    'abstract' : MainP.get("abstract","No abstract Available"),
                    'Authors' : delimiter.join([clean_author_name(entry['name']) for entry in MainP['authors']]),
                    'Link' : InpLinks.get('MainLink')[0],
                    'PDF': MainP.get('openAccessPdf').get('url','NA') if MainP.get('openAccessPdf') else "NA",
                    'Journal': MainP.get('venue') if MainP.get('venue') else 'NA', }),
        # second paper 
    for n, ref in enumerate(SPaper[keyword]):
        references.append({
                        'Original Paper': MainP.get('title') if MainP else 'NA',
                        'Related Paper' : ref.get("title","No title Available"),
                        'abstract' : ref.get("abstract","No abstract Available"),
                        'Authors' : delimiter.join([clean_author_name(entry['name']) for entry in ref['authors']]),
                        'Link' : InpLinks.get('refLinks')[n],
                        'PDF': ref.get('openAccessPdf','NA').get("url",'NA') if ref.get('openAccessPdf') else "NA" ,
                        'Journal': ref.get('venue') if ref.get('venue') else 'NA',
                        'Note' : note
                    })
    return {'DATA': data, 'Ref': references}

# for in cases where there's no details extracted
def parseEmpty():
    data = []
    references = []
    data.append({
                    'OriginalPaper' : "No Available Results",
                    'abstract' : "No Available Results",
                    'Authors' : "No Available Results",
                    'Link' : "No Available Results",
                    'PDF': "No Available Results",
                    'Journal': "No Available Results",
                    })
    references.append({
                        'Original Paper': "No Available Results",
                        'Related Paper' : "No Available Results",
                        'abstract' : "No Available Results",
                        'Authors' : "No Available Results",
                        'Link' : "No Available Results",
                        'PDF': "No Available Results" ,
                        'Journal': "No Available Results",
                        'Note' : "No Available Results"
                    })
    return {'DATA': data, 'Ref': references}


def QueryInfo(query,numofPages,cite,ref,relatedPapers):       
    data = []
    rsp = requests.get('https://api.semanticscholar.org/graph/v1/paper/search',
            headers={'X-API-KEY': APIFun()},
            #    references.title,references.authors
            params={'query': query, 'limit': numofPages, 'fields': f'abstract,title,authors,openAccessPdf,venue'})
    if rsp.status_code == 200:
        results = rsp.json()
        total = results["total"]
        if total:
            papers = results['data']
            Cpapers = []
            links = []
            data = []
            if not relatedPapers:  
                if cite:
                    for idx , pep in enumerate(papers):
                        Cpapers.append(grapCitations(f"https://api.semanticscholar.org/graph/v1/paper/{pep.get('paperId')}",numofPages))
                        if len(Cpapers[0]['citations'])<= 30 and len(Cpapers[0]['citations'])> 0:
                            links.append(getLinks(pep,Cpapers[idx],'citations'))
                        else:
                            new_links = []
                            fragment1 = {'citations': Cpapers[idx]['citations'][0:21]}
                            fragment2 = {'citations': Cpapers[idx]['citations'][21:]}
                            new_links = getLinks(pep, fragment1, 'citations')
                            # Iterate through new_links and extend refLinks for each element
                            new_links['refLinks'].extend(EmptyLinks(pep, fragment2, 'citations').get('refLinks'))
                            data.append(parseResults(pep,Cpapers[idx],new_links,'citations'))
                elif ref:
                    Cpapers.append(grapRefrences(f"https://api.semanticscholar.org/graph/v1/paper/{papers[0]['paperId']}",numofPages))
                    if len(Cpapers[0]['references'])<= 30 and len(Cpapers[0]['references'])> 0:
                        links.append(getLinks(papers[0],Cpapers[0],'references'))
                        data.append(parseResults(papers[0],Cpapers[0],links[0],'references'))
                    else:
                        new_links = []
                        fragment1 = {'references': Cpapers[0]['references'][0:21]}
                        fragment2 = {'references': Cpapers[0]['references'][21:]}
                        new_links = getLinks(papers[0], fragment1, 'references')
                        # Iterate through new_links and extend refLinks for each element
                        new_links['refLinks'].extend(EmptyLinks(papers[0], fragment2, 'references').get('refLinks'))
                        data.append(parseResults(papers[0],Cpapers[0],new_links,'references'))
            else:
                links.append(getLinks([],results,'data'))
                data.append(parseResults([],results,links[0],'data'))
        else:
            data = [parseEmpty()]
    else: 
         data = [parseEmpty()]
    return data



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

# recommendations 
def recomendations(query,numofPages):
    links = []
    data = []
    rsp = requests.get('https://api.semanticscholar.org/graph/v1/paper/search',
            headers={'X-API-KEY': APIFun()},
            #    references.title,references.authors
            params={'query': query, 'limit': numofPages, 'fields': f'abstract,title,authors,openAccessPdf,venue'})
    if rsp.status_code == 200:
        paper = rsp.json() 
        if paper['total']> 0:
            links.append(getLinks([],paper,'data'))
            data.append(parseResults([],paper,links[0], 'data'))
        else:
            data.append(parseEmpty())
    return data


sp = Blueprint('sp', __name__)
@sp.route('/ai/')
def index():
    if 'KW' in session:
        session.pop('KW')  # Remove 'KW' from the session
    if 'Html' in session:
        session.pop('Html')
    if 'dfTemp' in session:
        session.pop('dfTemp')
    return render_template('ai.html', user=current_user)

@sp.route('/ai/result/', methods=['POST'])
def result():
    OriginalPapers = []
    df2 = []
    cit = False
    ref = False
    relatedPapers = False
    numofPages = None
    global search_keyword
    search_keyword = request.form['check']
    numofPages = int(request.form['check2'])
    search_type = request.form.get('search-type')
    # flash(' Processing, Please Wait! ', 'info')
    if search_type =='cit':
        cit = True
        df = QueryInfo(search_keyword,numofPages,cit,ref,relatedPapers)  # Update the global variable
    elif search_type == 'ref':
        ref = True    
        df = QueryInfo(search_keyword,numofPages,cit,ref,relatedPapers)  # Update the global variable
    elif search_type =='rec':
       df = recomendations(search_keyword,numofPages=numofPages)
    elif search_type =='RelW':
        relatedPapers = True
        df = QueryInfo(search_keyword,numofPages,cit,ref,relatedPapers)

    dfTemp = []
    for idx in range(len(df)):
        dfTemp.extend(get_unique_dicts_preserve_order(df[idx]['Ref']))   
        #flash('Invalid search type selected!', 'error')
    for idx in range(len(df)):
        OriginalPapers.extend(df[idx]['DATA'])
        df2.extend(get_unique_dicts_preserve_order(df[idx]['Ref']))
        for data_dict in df2:
            if data_dict['abstract']:
                if len(data_dict['abstract']) > 220:
                    data_dict['abstract'] = data_dict['abstract'][0:220]
            # Define the table headers
    newdf = pd.DataFrame(df2)  
    # change links 
    try:
        newdf[HeaderRel[4]] = newdf[HeaderRel[4]].apply(create_links_with_custom_keyword)
        newdf[HeaderRel[5]] = newdf[HeaderRel[5]].apply(create_links_with_custom_keyword)
    except Exception as e:
        flash('Something went wrong!', 'info')

    # Convert the DataFrame to an HTML table with links
    # Create the HTML for the table
    table_html = RenderHtml(newdf)
    session['KW'] = search_keyword
    session['Html'] = table_html
    session['dfTemp'] = dfTemp
    return render_template('result.html', table=table_html, classes='table table-striped container', search_keyword=search_keyword, user=current_user)

@sp.route('/ai/graph/', methods=['POST'])
def gen_graph():
    try:
        HeaderRel = ['Original Paper','Related Paper' ,'abstract' ,'Authors','Link','PDF','Journal','Note']
        NewList = find_word_in_list(['Original Paper','Related Paper','Authors','Journal'],HeaderRel)
        NewList = [HeaderRel[i] for i in NewList]
        graph_html = NetWorkGrap(session.get('dfTemp'), session.get('KW'),NewList,'ai')
        session['gen_graph'] = {
            'success': True,
            'message': 'Done Successfully'
        }
    except Exception as e:       
        graph_html =  f'An error has occurred: {e}'  # Include the error message
    # Pass 'search_keyword' to the template if it's defined
    search_keyword = session.get('KW', '')  # Use a default value if not defined
    return render_template('graph.html', table=graph_html, classes='table table-striped container', search_keyword=search_keyword, user=current_user)

# Define the route for saving search results
@sp.route('/ai/saveResults', methods=['POST'])
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

@sp.route('/ai/download_excel', methods=['POST'])
def download_excel():
    try:
        import io    
        search_keyword = session.get('KW')
        df = pd.DataFrame(session.get('dfTemp'))    
        # Specify the order of columns
        column_order = HeaderRel
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
        return redirect('https://search.relengine.com/ai')
        

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
    yield 'sp.index', {}, formatted_date_time, 'monthly', 0.7