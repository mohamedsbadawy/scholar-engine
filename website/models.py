from . import db  # Import 'db' from your package
from datetime import datetime
from sqlalchemy import func  # Import func for database functions
from flask_login import UserMixin


class ImageData(db.Model):
    __tablename__ = 'image_data'  # Explicitly set the table name
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    src = db.Column(db.String(255))
    title = db.Column(db.String(255))
    des = db.Column(db.String(255))
    link = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Define the timestamp field

class categories(db.Model):
    __tablename__ = 'categories'  # Explicitly set the table name
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    journals_under = db.relationship('journals', backref='categories', lazy=True)
    journal_det_under = db.relationship('Journal_info', backref='categories', lazy=True)


class journals(db.Model):
    __tablename__ = 'journals'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    impactfactor = db.Column(db.Text)
    description = db.Column(db.Text,nullable=True)
    impact = db.Column(db.Text,nullable=True)
    h_index = db.Column(db.Text,nullable=True)  # Changed the column name to h_index (removed hyphen)
    SJR = db.Column(db.Text,nullable=True)
    ranking = db.Column(db.Text,nullable=True)
    
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    # Define a relationship with Journal_info
    journal_info = db.relationship('Journal_info', backref='journals', lazy=True)

class Journal_info(db.Model):
    __tablename__ = 'Journal_info'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text)
    cat = db.Column(db.Text)
    publisher = db.Column(db.Text)
    country = db.Column(db.Text)
    issn = db.Column(db.Text)
    Q = db.Column(db.Text)
    history = db.Column(db.Text)
    about = db.Column(db.Text)
    website = db.Column(db.Text)
    
    journal_id = db.Column(db.Integer, db.ForeignKey('journals.id'), nullable=False)
    category__id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    bio = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    journal_id = db.Column(db.Integer, db.ForeignKey('Journal_info.id'))
    journal_rev = db.relationship('Journal_info', backref='reviews')
    upvote_count = db.Column(db.Integer, default=0)
    user = db.relationship('User', back_populates='reviews', overlaps="user_reviews,user")


    
class Library(db.Model):  # Corrected the model name to singular form
    __tablename__ = 'library'  # Explicitly set the table name
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model, UserMixin):
    __tablename__ = 'user'  # Explicitly set the table name
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    photo = db.Column(db.Text,nullable=False)
    # salt = db.Column(db.LargeBinary(16), nullable=False)  # Salt column as BINARY(16)
    first_name = db.Column(db.String(150))
    reviews = db.relationship('Review')  # Use the corrected model name 'Review'
    Library = db.relationship('Library')  # Use the corrected model name 'Review'
    reset_password_token = db.Column(db.String(255), nullable=True)
    reset_password_token_timestamp = db.Column(db.Integer, nullable=True)
    education = db.Column(db.String(500))
    f_of_Study = db.Column(db.String(600))
    def set_password(self, password):
        self.password = password
