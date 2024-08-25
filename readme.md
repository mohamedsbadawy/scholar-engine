# Research Engine

Research Engine is a Python-based web application designed to help users easily find and organize academic articles, journals, and related research. It leverages the Scrapy framework for web scraping and Flask for the web interface. This tool allows users to search for scholarly articles, view related references and citations, and save results into a personal library. Users can also download their saved search results and explore connected maps of their research findings.

## live view.

You can also access the live application at [Related Engine](https://relengine.com).
![live preview](https://search.relengine.com/testimage/liveimage.png)

## Features

- **Scholarly Search**: Search for articles, journals, and papers related to specific keywords.
- **Related References and Citations**: Automatically fetch related references and citations for the searched articles.
- **User Accounts**: Users can create accounts to save their search results, manage their personal library, and download saved data.
- **Connected Maps**: Visualize the relationships between articles and references through interactive connected maps.
- **Review Section**: A modifiable section where users can input reviews for articles, journals, or any other related content.
- **SQL database integrations**: to use user registration, and Journals listings, you need to connect your SQL database according to the instructions below.


## Installation

To install and run the Research Engine on your local machine, follow these steps:

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/mohamedsbadawy/research-engine.git
    cd research-engine
    ```

2. **Create a Virtual Environment** (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install the Required Packages**:
    Install all dependencies using the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

4. **Change SQL DB name and username**:
    Change SQL DB name and username:
    in /website/__init__.py
    you need to input your DB username and passwords to use the SQL functinality. 
    You can disable these features by commenting out the lines that controls DB, and User functionality.
    ```bash
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://SQLName:{encoded_password}@localhost:3306/SQLUserName'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable Flask-SQLAlchemy modification tracking
    
    ```
5. **Rudimentary admin page to add Journal enteries**:
    admin page to add Journal enteries:
    in /website/scijournals.py
    change userid here to whatever userid you choose to be the admin
    ```bash
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
    ```
    
6. **To allow the app to send notification emails**:
    To allow the app to send notification emails:
     in /website/__init__.py
    ```bash
    # Configure Flask-Mail
    app.config['MAIL_SERVER'] = 'relengine.com'  # Replace with your SMTP server address
    app.config['MAIL_PORT'] = 465  # Replace with your SMTP server port
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'email username'  # Replace with your email address
    app.config['MAIL_PASSWORD'] = 'Password'  # Replace with your email password
    mail.init_app(app)
    ```

7. **Sematic Scholars API**:
    To use "AI-Search Engine": obtain an API from sematicscholars, and add it to API.Py.
8. **Run the Web Application**:
    Start the Flask application by running:
    ```bash
    flask run
    ```
    By default, the application will be accessible at `http://127.0.0.1:5000`.

9. **Access the Application**:
    Open your web browser and navigate to `http://127.0.0.1:5000` to start using the Research Engine.

## Usage

1. **Search**: Enter a keyword or phrase into the search bar to find relevant scholarly articles.
2. **View Results**: Browse through the search results, which include related references and citations.
3. **Save to Library**: Logged-in users can save articles to their personal library for future reference.
4. **Download Results**: Users can download their saved search results in a convenient format.
5. **Connected Maps**: Explore the relationships between articles and references using the interactive map feature.
6. **Review Journals**: Contribute by reviewing articles or journals, enhancing the collaborative academic environment.
7. **Job hub**: Contribute by reviewing articles or journals, enhancing the collaborative academic environment.
7. **SQL integration**: Contribute by reviewing articles or journals, enhancing the collaborative academic environment.
## Reused codes
Some of the code in the project was open source and was repurposed to the current use case. 

## Contributing

Contributions are welcome! If you would like to contribute to this project, please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


