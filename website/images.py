from flask import Blueprint, render_template
from . import db  # Import the db object from your app
from .models import ImageData
from flask import current_app
from datetime import datetime, timedelta


images = Blueprint('images', __name__)

@images.route('/images')
def index():
    fetch_and_update_images()
    current_day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    daily_images = ImageData.query.filter(ImageData.timestamp >= current_day_start).all()
    return render_template('indextemp.html', images=daily_images)

def fetch_and_update_images():
    from . import db  # Import the db object from your app
    from .models import ImageData
    import requests
    from bs4 import BeautifulSoup
    from fake_useragent import UserAgent
    import uuid  # Import the uuid module
    ua = UserAgent()    
    import os
    headers = {
        "User-Agent": str(ua.googlechrome),
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://google.com/",
        # "X-Forwarded-For": str(proxy_load),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    SubUrl = f'https://www.nature.com/nature/articles'
    response = requests.get(SubUrl, headers=headers) 
    soup = BeautifulSoup(response.text, "html.parser")
    card_layouts = soup.find_all('div', class_='c-card__layout u-full-height')
    images = []
    # Loop through each "c-card__layout" div
    for card_layout in card_layouts:
        # Find the <h3> element within the current "c-card__layout" div
        h3_element = card_layout.find('h3', class_='c-card__title')   
        description_div = card_layout.find('div', class_='c-card__summary u-mb-16 u-hide-sm-max')
        if description_div:
            des = description_div.text.strip()
        else:
            des = ''
        if h3_element:
            # Extract the text within the <h3> element
            title = h3_element.text.strip()
            # Encode the text using UTF-8
            encoded_title = title.encode('utf-8')
            # Decode and display the encoded text
            title = encoded_title.decode('utf-8')
            # titles.append(title)        
            # Find the first <a> element within the <h3> element
            a_element = h3_element.find('a')        
            if a_element:
                # Extract the link (href) within the <a> element
                link = a_element.get('href')
        # Find the <img> element within the current "c-card__layout" div
        img_element = card_layout.find('img', itemprop='image')    
        if img_element and a_element and title and des:
            NewURL = 'https://www.nature.com' + link
            response2 = requests.get(NewURL, headers=headers) 
            soup2 = BeautifulSoup(response2.text, 'html.parser')
            img_element2 = soup2.find('img', attrs={'aria-describedby': 'Fig1'})
                # Check if the image element was found
            if img_element2:
                image_src = 'https:' + img_element2.get('src')
            else: 
                image_src = img_element.get('src')
            # Generate a safe filename by encoding the title to UTF-8 and quoting special characters
            unique_filename = str(uuid.uuid4()) + '.jpg'
            # Specify the directory where you want to save the images
            image_directory = os.path.join(current_app.root_path, 'static', 'images')  # Specify your image directory path
            # Combine the directory path and the safe filename to create the full image filename
            image_filename = os.path.join(image_directory, unique_filename)
            if not os.path.exists(image_filename):
                try:
                    # Send a GET request to download the image
                    image_response = requests.get(image_src, stream=True)
                    # Check if the request was successful (status code 200)
                    if image_response.status_code == 200:
                        # Create the directory if it doesn't exist
                        os.makedirs(image_directory, exist_ok=True)
                        # Save the image with the safe filename
                        with open(image_filename, 'wb') as image_file:
                            for chunk in image_response.iter_content(chunk_size=8192):
                                image_file.write(chunk)
                        # Add the image data to the database
                        new_image = ImageData(src="https://search.relengine.com/website/static/images/"+unique_filename, title=title, des=des, link='https://www.nature.com' + link)
                        db.session.add(new_image)
                except Exception as e:
                    print(f"Error downloading image: {str(e)}")
    db.session.commit()